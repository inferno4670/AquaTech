from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.data.species_db import needs_protection, region_by_id, species_by_id
from app.schemas.schemas import PredictionRequest, PredictionRunResponse
from app.services.prediction import predict as run_prediction

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def _optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None
    from app.core.security import decode_access_token
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    user_id = payload.get("user_id")
    email = payload["sub"]
    if not user_id:
        return None
    from app.models.models import User
    result = await session.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    return result.scalar_one_or_none()


async def _region_bounds_from_db(region_id: int, session: AsyncSession) -> dict[str, Any] | None:
    from app.models.models import MarineRegion
    row = await session.get(MarineRegion, region_id)
    if not row or not row.is_active:
        return None
    return {
        "north": row.bounds_north,
        "south": row.bounds_south,
        "east": row.bounds_east,
        "west": row.bounds_west,
        "centroid_lat": row.centroid_lat,
        "centroid_lng": row.centroid_lng,
        "default_search_radius_km": row.default_search_radius_km,
        "label": row.label,
    }


@router.post("/predict")
async def create_prediction_public(
    request: PredictionRequest,
    session: AsyncSession = Depends(get_db),
    user=Depends(_optional_user),
):
    """Stable public prediction endpoint.

    This is the endpoint the frontend's FindFish page uses. It is intentionally a
    thin wrapper around the same `app.services.prediction.predict` call the
    authenticated `/api/predictions` route uses, so both routes stay in sync as the
    model changes.
    """
    return await create_prediction(request, session, user=user)


@router.post("/predictions")
async def create_prediction(
    request: PredictionRequest,
    session: AsyncSession = Depends(get_db),
    user=Depends(_optional_user),
):
    species = species_by_id(request.species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")

    region_bounds = await _region_bounds_from_db(request.region_id, session)
    if not region_bounds:
        raise HTTPException(status_code=404, detail="Region not found or inactive")

    # Historical-density signal for this species, computed from stored observations.
    #
    # This is deliberately a real query over the database rather than a constant: the
    # density term is what should improve as the community logs more sightings, which is
    # the whole product loop. Two things changed here from the first draft:
    #   * it counts observations inside the requested region's bounding box instead of
    #     the whole table, so a busy coast no longer inflates an unrelated region;
    #   * it only counts `validated` rows, so pending or flagged submissions cannot
    #     steer a prediction, and it no longer requires a signed-in user.
    from app.models.models import Observation
    from sqlalchemy import func

    count_stmt = (
        select(func.count(Observation.id))
        .where(
            Observation.species_id == request.species_id,
            Observation.status == "validated",
            Observation.latitude.between(region_bounds["south"], region_bounds["north"]),
            Observation.longitude.between(region_bounds["west"], region_bounds["east"]),
        )
    )
    result = await session.execute(count_stmt)
    nearby_observations = int(result.scalar_one() or 0)

    # 40 validated sightings in one region is a strong signal at MVP scale; the cap keeps
    # the term bounded no matter how large the table grows.
    density_proxy = min(1.0, nearby_observations / 40.0)

    try:
        run = await run_prediction(
            species_id=request.species_id,
            region_id=request.region_id,
            prediction_date=request.date,
            time_hour=request.time_hour,
            search_radius_km=request.search_radius_km,
            region_bounds=region_bounds,
            observation_density_nearby=density_proxy,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    # If the species is protected/restricted, we still surface habitat info but
    # flag it clearly. The UI decision is made there; API returns the data either way.
    protected = needs_protection(species)

    run.id = ""  # placeholder; persistence not required for MVP read-only flow

    return {
        "prediction": run,
        "species_id": request.species_id,
        "region_id": request.region_id,
        "protected_species": protected,
        "nearby_observations": nearby_observations,
        "requested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@router.get("/predictions/{run_id}")
async def get_prediction(run_id: str):
    raise HTTPException(status_code=501, detail="Prediction lookup by id not implemented in MVP; use POST /predictions")
