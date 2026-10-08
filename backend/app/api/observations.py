from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.data.species_db import species_by_id
from app.models.models import Observation
from app.schemas.schemas import MarineConditions, ObservationDraft, ObservationEnvelope
from app.services.auth import (
    get_current_user,
    record_observation_and_award_points,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def _optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None
    user = await get_current_user(session, credentials.credentials)
    return user


@router.post("/observations")
async def submit_observation(
    draft: ObservationDraft,
    session: AsyncSession = Depends(get_db),
    user=Depends(_optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to submit observations")

# env_behavior is available from species_db for the dataset .md / species detail page
    # but is not currently injected into the observation envelope payload.
    from app.data.species_db import species_env_behavior
    _ = species_env_behavior(draft.species_id)

    # Region bounds for validation (hardcode MVP region)
    region_bounds = {
        "north": 20.5,
        "south": 17.5,
        "east": 73.6,
        "west": 71.6,
        "centroid_lat": 19.0,
        "centroid_lng": 72.5,
        "default_search_radius_km": 50.0,
        "label": "Maharashtra Coast",
    }

    try:
        obs, env_obj, points = await record_observation_and_award_points(
            session=session,
            user=user,
            species=species,
            region_bounds=region_bounds,
            observation_in=draft,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Observation rejected: {exc}") from exc

    envelope = ObservationEnvelope(
        observation={
            "id": str(obs.id),
            "species_id": obs.species_id,
            "species_name": species.name,
            "observed_at": obs.observed_at.isoformat(),
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "quantity_kg": obs.quantity_kg,
            "observation_type": obs.observation_type,
            "photo_url": obs.photo_url,
            "notes": obs.notes,
            "created_by": str(obs.created_by),
            "created_at": obs.created_at.isoformat(),
            "status": obs.status,
            "quality_score": obs.quality_score,
            "flagged_reason": obs.flagged_reason,
        },
        environment=MarineConditions(
            lat=env_obj.lat,
            lng=env_obj.lng,
            timestamp=env_obj.timestamp,
            sea_surface_temperature_c=env_obj.sea_surface_temperature_c,
            current_velocity_ms=env_obj.current_velocity_ms,
            current_direction_deg=env_obj.current_direction_deg,
            wave_height_m=env_obj.wave_height_m,
            wave_direction_deg=env_obj.wave_direction_deg,
            wind_speed_kmh=env_obj.wind_speed_kmh,
            wind_direction_deg=env_obj.wind_direction_deg,
            weather_code=env_obj.weather_code,
            water_depth_m=env_obj.water_depth_m,
        ),
        points_awarded=points,
    )
    return envelope


@router.get("/observations")
async def list_observations(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    user=Depends(_optional_user),
):
    stmt = select(Observation).order_by(Observation.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Observation.status == status)
    # If authenticated, default to user's observations
    if user:
        stmt = select(Observation).where(Observation.created_by == user.id).order_by(Observation.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(Observation.status == status)
    result = await session.execute(stmt)
    obs = result.scalars().all()
    return [
        {
            "id": str(o.id),
            "species_id": o.species_id,
            "species_name": o.species.name if o.species else None,
            "observed_at": o.observed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latitude": o.latitude,
            "longitude": o.longitude,
            "observation_type": o.observation_type,
            "quantity_kg": o.quantity_kg,
            "photo_url": o.photo_url,
            "notes": o.notes,
            "status": o.status,
            "quality_score": o.quality_score,
            "flagged_reason": o.flagged_reason,
            "created_by": str(o.created_by),
            "created_at": o.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for o in obs
    ]


@router.get("/observations/public")
async def list_public_sightings(
    species_id: int | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    """Validated public sightings from *every* user, for the map's fish layer.

    Deliberately separate from GET /observations, which scopes to the caller's own
    records once authenticated. Only `validated` + `is_public` rows are exposed, so a
    pending or flagged submission never appears on the shared map.

    Declared before /observations/{observation_id} on purpose: otherwise FastAPI would
    try to parse "public" as a UUID and always answer 404.
    """
    stmt = (
        select(Observation)
        .where(Observation.is_public.is_(True), Observation.status == "validated")
        .order_by(Observation.created_at.desc())
        .limit(limit)
    )
    if species_id is not None:
        stmt = stmt.where(Observation.species_id == species_id)

    result = await session.execute(stmt)
    rows = result.scalars().all()
    return {
        "count": len(rows),
        "sightings": [
            {
                "id": str(o.id),
                "species_id": o.species_id,
                "species_name": o.species.name if o.species else None,
                "observed_at": o.observed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "latitude": o.latitude,
                "longitude": o.longitude,
                "observation_type": o.observation_type,
                "quantity_kg": o.quantity_kg,
                "quality_score": o.quality_score,
                "status": o.status,
                "notes": o.notes,
            }
            for o in rows
        ],
    }


@router.get("/observations/{observation_id}")
async def get_observation(observation_id: str, session: AsyncSession = Depends(get_db)):
    try:
        obs_uuid = uuid.UUID(observation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Observation not found")

    # `environment` has no eager-load strategy, so it must be loaded explicitly:
    # touching it lazily on an async session raises MissingGreenlet (a 500).
    stmt = (
        select(Observation)
        .options(selectinload(Observation.environment))
        .where(Observation.id == obs_uuid)
    )
    result = await session.execute(stmt)
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Observation not found")
    env = o.environment
    return {
        "observation": {
            "id": str(o.id),
            "species_id": o.species_id,
            "species_name": o.species.name if o.species else None,
            "observed_at": o.observed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latitude": o.latitude,
            "longitude": o.longitude,
            "observation_type": o.observation_type,
            "quantity_kg": o.quantity_kg,
            "photo_url": o.photo_url,
            "notes": o.notes,
            "status": o.status,
            "quality_score": o.quality_score,
            "flagged_reason": o.flagged_reason,
            "created_by": str(o.created_by),
            "created_at": o.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "environment": {
            # The environment row stores no coordinates of its own; it is sampled at
            # the sighting's location, so it inherits the observation's lat/lng.
            "lat": o.latitude,
            "lng": o.longitude,
            "timestamp": env.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ") if env else None,
            "sea_surface_temperature_c": env.sea_surface_temperature_c if env else None,
            "current_velocity_ms": env.current_velocity_ms if env else None,
            "current_direction_deg": env.current_direction_deg if env else None,
            "wave_height_m": env.wave_height_m if env else None,
            "wave_direction_deg": env.wave_direction_deg if env else None,
            "wind_speed_kmh": env.wind_speed_kmh if env else None,
            "wind_direction_deg": env.wind_direction_deg if env else None,
            "weather_code": env.weather_code if env else None,
            "water_depth_m": env.water_depth_m if env else None,
        },
    }
