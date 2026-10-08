from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models import models as M
from app.models.models import Observation, PointTransaction, Reward, RewardRedemption, User
from app.schemas.schemas import (
    LoginResponse,
    ObservationEnvelope,
    PointsSnapshot,
    RewardItem,
    RewardRedemptionOut,
    SpeciesProfile,
    TokenOut,
    UserPublic,
)
from app.services.environment import (
    POINTS_PER_VALID_SIGHTING,
    POINTS_ACCURATE_TIMESTAMP,
    POINTS_DETAILED_NOTES,
    POINTS_PHOTO,
    POINTS_VERIFIED,
    REPEAT_MULTIPLIER,
    REPEAT_CONTRIBUTOR_THRESHOLD,
    _level_for_reputation,
    _now_iso,
    _now_utc,
    award_points_for_observation as svc_award_points,
    build_user_public as svc_build_user_public,
    compute_quality_score as svc_compute_quality_score,
    enrichment_for_sighting as svc_enrichment_for_sighting,
    sandbox_reward_catalog,
    validate_observation as svc_validate_observation,
)

POINT_PER_OBSERVATION = 10
REPUTATION_PER_VERIFIED = 20


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email, User.is_active.is_(True))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, password: str, display_name: str) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        display_name=display_name,
        role="fisherman",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def issue_token_for_user(user: User) -> TokenOut:
    payload: dict[str, Any] = {"role": user.role, "user_id": str(user.id)}
    token = create_access_token(subject=user.email, data=payload)
    return TokenOut(access_token=token, token_type="bearer")


async def decode_token(token: str) -> dict[str, Any] | None:
    return decode_access_token(token)


async def get_current_user(
    session: AsyncSession,
    token: str,
) -> User | None:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    email = payload["sub"]
    user = await get_user_by_email(session, email)
    if not user:
        return None
    # verify the user_id in token matches
    if str(user.id) != payload.get("user_id", ""):
        return None
    return user


async def get_user_public(
    session: AsyncSession,
    user: User,
) -> UserPublic:
    # Aggregate observation stats. created_by is stored as a UUID column, so
    # compare against the UUID object itself (str() breaks sqlite binding).
    total_stmt = select(func.count(Observation.id)).where(Observation.created_by == user.id)
    verified_stmt = select(func.count(Observation.id)).where(
        Observation.created_by == user.id, Observation.status == "validated"
    )
    quality_stmt = select(func.avg(Observation.quality_score)).where(Observation.created_by == user.id)

    total_result = await session.execute(total_stmt)
    verified_result = await session.execute(verified_stmt)
    quality_result = await session.execute(quality_stmt)

    total = int(total_result.scalar_one() or 0)
    verified = int(verified_result.scalar_one() or 0)
    avg_quality = float(quality_result.scalar_one() or 0.0)

    return svc_build_user_public(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        reputation=user.reputation,
        points_balance=user.points_balance,
        observations_count=total,
        verified_count=verified,
        last_quality_avg=avg_quality,
    )


async def record_observation_and_award_points(
    session: AsyncSession,
    user: User,
    species: SpeciesProfile,
    region_bounds: dict[str, Any] | None,
    observation_in: Any,  # ObservationDraft-like
) -> tuple[Observation, dict[str, Any], int]:
    """Create observation, enrich environment, validate, score, award points, persist.

    Returns (observation, environment_dict, points_awarded).
    """
    observed_at = observation_in.observed_at
    lat = float(observation_in.latitude)
    lng = float(observation_in.longitude)

    # Validate
    # fetch prior observations for duplicate detection
    prior_stmt = (
        select(Observation)
        .where(Observation.created_by == user.id)
        .order_by(Observation.created_at.desc())
        .limit(8)
    )
    prior_result = await session.execute(prior_stmt)
    prior_obs = []
    for o in prior_result.scalars().all():
        prior_obs.append({
            "species_id": o.species_id,
            "latitude": o.latitude,
            "longitude": o.longitude,
            "observed_at": o.observed_at,
            "id": str(o.id),
        })
    flags = svc_validate_observation(
        species_id=species.id,
        latitude=lat,
        longitude=lng,
        observed_at=observed_at,
        region_bounds=region_bounds,
        existing_observations=prior_obs,
    )

    # Env enrichment (Open-Meteo recent estimate + annotation)
    env = await svc_enrichment_for_sighting(lat, lng, observed_at)

    # Enrichment returns a validated MarineConditions model; keep a dict view
    # for legacy dict-style consumers below.
    env_obj: MarineConditions = env
    env = {
        "lat": env_obj.lat,
        "lng": env_obj.lng,
        "timestamp": env_obj.timestamp,
        "sea_surface_temperature_c": env_obj.sea_surface_temperature_c,
        "current_velocity_ms": env_obj.current_velocity_ms,
        "current_direction_deg": env_obj.current_direction_deg,
        "wave_height_m": env_obj.wave_height_m,
        "wave_direction_deg": env_obj.wave_direction_deg,
        "wind_speed_kmh": env_obj.wind_speed_kmh,
        "wind_direction_deg": env_obj.wind_direction_deg,
        "weather_code": env_obj.weather_code,
        "water_depth_m": env_obj.water_depth_m,
    }

    # Quality score
    obs_dict = {
        "species_id": species.id,
        "latitude": lat,
        "longitude": lng,
        "observed_at": observed_at,
        "observation_type": observation_in.observation_type,
        "quantity_kg": observation_in.quantity_kg,
        "photo_url": observation_in.photo_url,
        "notes": observation_in.notes,
    }
    quality = svc_compute_quality_score(obs_dict, env_obj, species)

    is_verified = (len(flags) == 0)
    points, new_balance = svc_award_points(
        user_id=user.id,
        observation=obs_dict,
        environment=env_obj,
        species=species,
        is_verified=is_verified,
        existing_balance=user.points_balance,
    )

    # Persist observation + environment
    obs = Observation(
        created_by=user.id,
        species_id=species.id,
        latitude=lat,
        longitude=lng,
        observed_at=observed_at,
        observation_type=observation_in.observation_type,
        quantity_kg=observation_in.quantity_kg,
        photo_url=observation_in.photo_url,
        notes=observation_in.notes,
        status="validated" if is_verified else "pending",
        flagged_reason="; ".join(flags) if flags else None,
        quality_score=quality,
        is_public=True,
    )
    session.add(obs)
    await session.flush()

    env_record = M.ObservationEnvironment(
        observation_id=obs.id,
        sea_surface_temperature_c=env_obj.sea_surface_temperature_c,
        current_velocity_ms=env_obj.current_velocity_ms,
        current_direction_deg=env_obj.current_direction_deg,
        wave_height_m=env_obj.wave_height_m,
        wave_direction_deg=env_obj.wave_direction_deg,
        wind_speed_kmh=env_obj.wind_speed_kmh,
        wind_direction_deg=env_obj.wind_direction_deg,
        weather_code=env_obj.weather_code,
        water_depth_m=env_obj.water_depth_m,
        source="open_meteo_marine_recent_estimate",
    )
    session.add(env_record)

    # points transaction
    tx = PointTransaction(
        user_id=user.id,
        delta=points,
        balance_after=new_balance,
        reason="observation_contribution",
    )
    session.add(tx)

    # update user points + reputation
    user.points_balance = new_balance
    if is_verified:
        user.reputation += REPUTATION_PER_VERIFIED
    await session.commit()
    await session.refresh(obs)
    await session.refresh(user)

    return obs, env_obj, points


async def get_points_snapshot(session: AsyncSession, user: User) -> PointsSnapshot:
    stmt = (
        select(PointTransaction)
        .where(PointTransaction.user_id == user.id)
        .order_by(PointTransaction.created_at.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    txs = result.scalars().all()

    def _serialize(tx: PointTransaction) -> dict[str, Any]:
        return {
            "id": str(tx.id),
            "delta": int(tx.delta),
            "balance_after": int(tx.balance_after),
            "reason": tx.reason,
            "created_at": tx.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    return PointsSnapshot(
        balance=int(user.points_balance),
        level=_level_for_reputation(int(user.reputation)),
        reputation=int(user.reputation),
        transactions=[_serialize(tx) for tx in txs],
    )


async def list_rewards(session: AsyncSession) -> list[RewardItem]:
    return sandbox_reward_catalog()


async def redeem_reward(session: AsyncSession, user: User, reward_id: str) -> RewardRedemptionOut:
    reward = await session.get(Reward, reward_id)
    if not reward:
        from app.schemas.schemas import RewardItem
        catalog = sandbox_reward_catalog()
        for item in catalog:
            if item.id == reward_id:
                reward = Reward(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    value_label=item.value_label,
                    points_cost=item.points_cost,
                    provider="sandbox",
                    available=True,
                    metadata_json=None,
                )
                session.add(reward)
                await session.commit()
                await session.refresh(reward)
                break
        else:
            raise ValueError(f"Unknown reward_id={reward_id}")

    if reward.points_cost > user.points_balance:
        raise ValueError("Insufficient points")

    # deduct points
    user.points_balance -= int(reward.points_cost)
    redemption = RewardRedemption(
        user_id=user.id,
        reward_id=reward.id,
        status="fulfilled" if reward.provider == "sandbox" else "pending",
        notes=_redemption_note(reward),
    )
    session.add(redemption)
    # transaction record
    tx = PointTransaction(
        user_id=user.id,
        delta=-int(reward.points_cost),
        balance_after=int(user.points_balance),
        reason=f"reward_redemption:{reward.id}",
    )
    session.add(tx)
    await session.commit()
    await session.refresh(redemption)
    return RewardRedemptionOut(
        id=str(redemption.id),
        reward_id=redemption.reward_id,
        title=redemption.reward.title if redemption.reward else reward.title,
        status=redemption.status,
        created_at=redemption.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        completed_at=(redemption.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if redemption.completed_at else None),
    )


def _redemption_note(reward: Reward) -> str:
    return f"Redeemed {reward.value_label} (sandbox)" if reward.provider == "sandbox" else f"Redeemed {reward.value_label}"
