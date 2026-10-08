from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import (
    ConservationStatus,
    DataSourceStatus,
    LegalRestriction,
    Observation,
    Species,
    SpeciesHabitatProfile,
    User,
)
from app.schemas.schemas import SpeciesProfile

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def _admin_from_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await session.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


@router.get("/admin/species")
async def admin_list_species(session: AsyncSession = Depends(get_db), admin=Depends(_admin_from_token)):
    result = await session.execute(select(Species))
    species = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "scientific_name": s.scientific_name,
            "conservation_status": s.conservation_status,
            "legal_catch_status": s.legal_catch_status,
            "typical_habitat": s.typical_habitat,
            "seasonal_behavior": s.seasonal_behavior,
            "current_sensitivity": s.current_sensitivity,
            "known_regions": s.known_regions,
            "regional_restriction": s.regional_restriction,
            "seasonal_restriction": s.seasonal_restriction,
            "description": s.description,
            "thumbnail_hint": s.thumbnail_hint,
            "weight_kg_min": s.weight_kg_min,
            "weight_kg_max": s.weight_kg_max,
            "preferred_temperature_min_c": s.preferred_temperature_min_c,
            "preferred_temperature_max_c": s.preferred_temperature_max_c,
            "preferred_depth_min_m": s.preferred_depth_min_m,
            "preferred_depth_max_m": s.preferred_depth_max_m,
            "preferred_current_min_ms": s.preferred_current_min_ms,
            "preferred_current_max_ms": s.preferred_current_max_ms,
        }
        for s in species
    ]


@router.put("/admin/species/{species_id}")
async def admin_update_species(
    species_id: int,
    body: SpeciesProfile,
    session: AsyncSession = Depends(get_db),
    admin=Depends(_admin_from_token),
):
    species = await session.get(Species, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    # Update scalar fields
    for field in (
        "name", "scientific_name", "conservation_status", "legal_catch_status",
        "typical_habitat", "seasonal_behavior", "current_sensitivity",
        "regional_restriction", "seasonal_restriction", "description", "thumbnail_hint",
        "weight_kg_min", "weight_kg_max",
        "preferred_temperature_min_c", "preferred_temperature_max_c",
        "preferred_depth_min_m", "preferred_depth_max_m",
        "preferred_current_min_ms", "preferred_current_max_ms",
    ):
        if hasattr(body, field):
            setattr(species, field, getattr(body, field))
    # known_regions as JSON string
    species.known_regions = str(list(body.known_regions)).replace("'", '"')
    await session.commit()
    await session.refresh(species)
    return {"ok": True, "species_id": species.id}


@router.get("/admin/observations")
async def admin_list_observations(
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
    admin=Depends(_admin_from_token),
):
    stmt = select(Observation).order_by(Observation.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Observation.status == status)
    result = await session.execute(stmt)
    obs = result.scalars().all()
    return [
        {
            "id": str(o.id),
            "species_id": o.species_id,
            "observed_at": o.observed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latitude": o.latitude,
            "longitude": o.longitude,
            "observation_type": o.observation_type,
            "quantity_kg": o.quantity_kg,
            "photo_url": o.photo_url,
            "notes": o.notes,
            "status": o.status,
            "flagged_reason": o.flagged_reason,
            "quality_score": o.quality_score,
            "created_by": o.created_by,
            "created_at": o.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for o in obs
    ]


@router.post("/admin/observations/{observation_id}/approve")
async def admin_approve_observation(
    observation_id: str,
    session: AsyncSession = Depends(get_db),
    admin=Depends(_admin_from_token),
):
    from uuid import UUID as _UUID
    try:
        oid = _UUID(observation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid observation id")
    obs = await session.get(Observation, oid)
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")
    obs.status = "validated"
    obs.flagged_reason = None
    await session.commit()
    return {"ok": True}


@router.post("/admin/observations/{observation_id}/flag")
async def admin_flag_observation(
    observation_id: str,
    reason: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_db),
    admin=Depends(_admin_from_token),
):
    from uuid import UUID as _UUID
    try:
        oid = _UUID(observation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid observation id")
    obs = await session.get(Observation, oid)
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")
    obs.status = "flagged"
    obs.flagged_reason = reason
    await session.commit()
    return {"ok": True}


@router.get("/admin/users")
async def admin_list_users(
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    admin=Depends(_admin_from_token),
):
    result = await session.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "display_name": u.display_name,
            "role": u.role,
            "reputation": u.reputation,
            "points_balance": u.points_balance,
            "is_active": u.is_active,
            "created_at": u.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for u in users
    ]


@router.post("/admin/users/{user_id}/toggle_active")
async def admin_toggle_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
    admin=Depends(_admin_from_token),
):
    from uuid import UUID
    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user id")
    user = await session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    await session.commit()
    return {"ok": True, "is_active": user.is_active}


@router.get("/admin/data-sources")
async def admin_data_sources(session: AsyncSession = Depends(get_db), admin=Depends(_admin_from_token)):
    result = await session.execute(select(DataSourceStatus))
    rows = result.scalars().all()
    return [{"id": r.id, "source": r.source, "status": r.status, "last_checked": r.last_checked.strftime("%Y-%m-%dT%H:%M:%SZ"), "detail": r.detail} for r in rows]
