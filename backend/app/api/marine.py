from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas.schemas import MarineConditions
from app.services.marine import marine_service

router = APIRouter()


@router.get("/marine/conditions")
async def get_marine_conditions(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_hours: int = Query(0, ge=0, le=72),
):
    try:
        data = await marine_service.marine_conditions(latitude, longitude, forecast_hours_ahead=forecast_hours)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Marine data unavailable: {exc}") from exc

    return MarineConditions(
        lat=data["lat"],
        lng=data["lng"],
        timestamp=data.get("timestamp") or datetime.now().isoformat(),
        sea_surface_temperature_c=data.get("sea_surface_temperature_c", 27.0),
        current_velocity_ms=data.get("current_velocity_ms", 0.0),
        current_direction_deg=data.get("current_direction_deg", 0.0),
        wave_height_m=data.get("wave_height_m", 0.0),
        wave_direction_deg=data.get("wave_direction_deg", 0.0),
        wind_speed_kmh=data.get("wind_speed_kmh", 0.0),
        wind_direction_deg=data.get("wind_direction_deg", 0.0),
        weather_code=data.get("weather_code", 0),
        water_depth_m=(data["water_depth_m"] if data.get("water_depth_m") is not None else None),
    )
