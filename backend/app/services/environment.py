from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.schemas.schemas import (
    MarineConditions,
    ObservationEnvelope,
    PointTransaction,
    PointsSnapshot,
    PredictionRunResponse,
    RewardItem,
    SpeciesProfile,
    UserPublic,
)
from app.services.marine import marine_service
from app.services.prediction import predict as run_prediction, _haversine_km

POINTS_PER_VALID_SIGHTING = 10
POINTS_ACCURATE_TIMESTAMP = 5
POINTS_PHOTO = 10
POINTS_DETAILED_NOTES = 5
POINTS_VERIFIED = 20
REPEAT_CONTRIBUTOR_THRESHOLD = 5
REPEAT_MULTIPLIER = 1.25


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def enrichment_for_sighting(
    latitude: float,
    longitude: float,
    observed_at: datetime,
) -> MarineConditions:
    env = await marine_service.marine_conditions_playback(latitude, longitude, observed_at)
    return MarineConditions(
        lat=env["lat"],
        lng=env["lng"],
        timestamp=env["timestamp"],
        sea_surface_temperature_c=env.get("sea_surface_temperature_c", 27.0),
        current_velocity_ms=env.get("current_velocity_ms", 0.0),
        current_direction_deg=env.get("current_direction_deg", 0.0),
        wave_height_m=env.get("wave_height_m", 0.0),
        wave_direction_deg=env.get("wave_direction_deg", 0.0),
        wind_speed_kmh=env.get("wind_speed_kmh") or 0.0,
        wind_direction_deg=env.get("wind_direction_deg") or 0.0,
        weather_code=env.get("weather_code", 0),
        water_depth_m=env.get("water_depth_m"),
    )


def compute_quality_score(
    observation: dict[str, Any],
    environment: MarineConditions,
    species: SpeciesProfile,
) -> float:
    """MVP quality score: higher is better.

    Factors:
    - timestamp precision (observed_at close to now = more reliable memory)
    - presence of photo
    - detailed notes
    - quantity provided
    - environmental clarity (non-blank marine conditions backfilled)
    """
    score = 50.0
    if observation.get("quantity_kg") is not None:
        score += 10.0
    if observation.get("notes"):
        score += POINTS_DETAILED_NOTES
    if observation.get("photo_url"):
        score += POINTS_PHOTO
    if environment.water_depth_m is not None:
        score += 5.0
    if environment.current_velocity_ms > 0:
        score += 5.0
    # Timestamp freshness: observed recently => bonus for accuracy.
    age_hours = (_now_utc() - observation["observed_at"]).total_seconds() / 3600.0
    if age_hours <= 2:
        score += POINTS_ACCURATE_TIMESTAMP
    elif age_hours <= 24:
        score += 3.0
    return min(100.0, score)


def award_points_for_observation(
    user_id: uuid.UUID,
    observation: dict[str, Any],
    environment: MarineConditions,
    species: SpeciesProfile,
    is_verified: bool = False,
    existing_balance: int = 0,
) -> tuple[int, int]:
    points = POINTS_PER_VALID_SIGHTING
    if observation.get("photo_url"):
        points += POINTS_PHOTO
    if observation.get("notes"):
        points += POINTS_DETAILED_NOTES
    if observation.get("quantity_kg") is not None:
        points += 5
    if is_verified:
        points += POINTS_VERIFIED
    # bonus multiplier capped
    points = int(points * REPEAT_MULTIPLIER) if observation.get("repeat_contributor") else points
    new_balance = max(0, existing_balance + points)
    return points, new_balance


def build_user_public(
    user_id: uuid.UUID,
    email: str,
    display_name: str,
    role: str,
    reputation: int,
    points_balance: int,
    observations_count: int,
    verified_count: int,
    last_quality_avg: float = 0.0,
) -> UserPublic:
    level = _level_for_reputation(reputation)
    return UserPublic(
        id=str(user_id),
        display_name=display_name,
        level=level,
        reputation=reputation,
        observations_count=observations_count,
        verified_count=verified_count,
        data_quality_percent=round(clamp(last_quality_avg, 0.0, 100.0), 1),
        is_admin=(role == "admin"),
    )


def _level_for_reputation(reputation: int) -> int:
    # Every 100 reputation = one level, minimum 1.
    return max(1, (reputation // 100) + 1)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def sandbox_reward_catalog() -> list[RewardItem]:
    return [
        RewardItem(
            id="reward_100_voucher",
            title="₹100 Voucher",
            description="Test voucher credit for MVP contributors (sandbox provider).",
            value_label="₹100 Voucher",
            points_cost=250,
            available=True,
            provider="sandbox",
        ),
        RewardItem(
            id="reward_250_voucher",
            title="₹250 Voucher",
            description="Higher-value test voucher for top contributors (sandbox provider).",
            value_label="₹250 Voucher",
            points_cost=600,
            available=True,
            provider="sandbox",
        ),
        RewardItem(
            id="reward_500_voucher",
            title="₹500 Voucher",
            description="Premium test voucher for the most active contributors (sandbox provider).",
            value_label="₹500 Voucher",
            points_cost=1200,
            available=True,
            provider="sandbox",
        ),
    ]


def validate_observation(
    species_id: int,
    latitude: float,
    longitude: float,
    observed_at: datetime,
    region_bounds: dict[str, Any] | None,
    existing_observations: list[dict[str, Any]],
) -> list[str]:
    flags: list[str] = []
    now = _now_utc()
    if observed_at > now:
        flags.append("Future timestamp")
    if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
        flags.append("Impossible coordinates")
    if region_bounds:
        b = region_bounds
        if not (b["south"] <= latitude <= b["north"] and b["west"] <= longitude <= b["east"]):
            flags.append("Location outside selected region")
    if existing_observations:
        for prev in existing_observations[-8:]:
            if prev["latitude"] == latitude and prev["longitude"] == longitude:
                flags.append("Repeated exact coordinates")
                break
    return flags


def _prediction_as_run_response(run: PredictionRunResponse, species_name: str, region_name: str) -> PredictionRunResponse:
    return run
