from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import get_settings

# Open-Meteo Marine variables we request in one call:
# - sea_surface_temperature
# - ocean_current_velocity (u/v decomposition)
# - ocean_current_direction
# - wave_height
# - wave_direction
# - wind_speed_10m, wind_direction_10m
#
# This service only fetches CURRENT/NEAR-FUTURE marine conditions from Open-Meteo.
# Historical/enriched sighting data is handled separately (see environment.py).


def _iso_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finite(value: Any, default: float) -> float:
    """Coerce a possibly-missing Open-Meteo value to a finite float.

    Open-Meteo omits variables for cells/model runs where it has no data, which
    yields ``None``. The API schema types these fields as floats, so returning
    ``None`` used to raise a validation error and surface as a 500.
    """
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return f if f == f and f not in (float("inf"), float("-inf")) else default


class MarineService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def _http(self) -> httpx.AsyncClient:
        timeout = httpx.Timeout(20.0, connect=5.0)
        transport: Any = httpx.AsyncHTTPTransport(retries=2)
        return httpx.AsyncClient(base_url=self._settings.openmeteo_marine_url, timeout=timeout, transport=transport)

    async def marine_conditions(
        self,
        latitude: float,
        longitude: float,
        forecast_hours_ahead: int = 0,
    ) -> dict[str, Any]:
        """Fetch current marine conditions for a point from Open-Meteo Marine API.

        Returns a dict mirroring MarineConditions fields (CamelCase keys) plus raw.
        """
        cache_key = f"{latitude:.4f},{longitude:.4f}"
        now = datetime.now(timezone.utc)
        ttl = timedelta(seconds=self._settings.openmeteo_cache_ttl_seconds)

        async with self._lock:
            if cache_key in self._cache:
                ts, payload = self._cache[cache_key]
                if now - datetime.fromtimestamp(ts, tz=timezone.utc) < ttl:
                    return payload

        url = self._settings.openmeteo_marine_url
        params: dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "sea_surface_temperature",
                "ocean_current_velocity",
                "ocean_current_direction",
                "wave_height",
                "wave_direction",
            ],
            "timezone": "UTC",
        }
        # The Marine API is ocean-only: it serves no wind variables, so requesting
        # wind_speed_10m/wind_direction_10m here just returns nulls. Wind and
        # weather_code are fetched from the weather API in _wind_conditions().
        # Hourly is kept as a fallback for marine variables missing from `current`
        # on some model runs.
        params["hourly"] = [
            "sea_surface_temperature",
            "ocean_current_velocity",
            "wave_height",
        ]
        if forecast_hours_ahead and forecast_hours_ahead > 0:
            params["forecast_hours"] = forecast_hours_ahead

        async with await self._http() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        marine = data.get("current", {})
        marine_values: dict[str, Any] = {
            "lat": latitude,
            "lng": longitude,
            "timestamp": marine.get("time", _iso_now_z()),
            "sea_surface_temperature_c": marine.get("sea_surface_temperature", 27.0),
            "current_velocity_ms": marine.get("ocean_current_velocity", 0.0),
            "current_direction_deg": marine.get("ocean_current_direction", 0.0),
            "wave_height_m": marine.get("wave_height", 0.0),
            "wave_direction_deg": marine.get("wave_direction", 0.0),
            "wind_speed_kmh": None,
            "wind_direction_deg": None,
            "weather_code": 0,
            "water_depth_m": None,
            "_raw": data,
            "_source": "open_meteo_marine",
        }

        hourly = data.get("hourly", {})
        if hourly:
            for var in ("sea_surface_temperature", "ocean_current_velocity", "wave_height"):
                cur_key = {
                    "sea_surface_temperature": "sea_surface_temperature_c",
                    "ocean_current_velocity": "current_velocity_ms",
                    "wave_height": "wave_height_m",
                }[var]
                cur = marine_values.get(cur_key)
                vals = hourly.get(var, [])
                if cur is None and vals and vals[0] is not None:
                    marine_values[cur_key] = float(vals[0])
        # Wind + weather code are not marine variables; they come from the weather API.
        wind = await self._wind_conditions(latitude, longitude)
        marine_values["wind_speed_kmh"] = wind["wind_speed_kmh"]
        marine_values["wind_direction_deg"] = wind["wind_direction_deg"]
        marine_values["weather_code"] = wind["weather_code"]

        # Guarantee every numeric field is a real number before it reaches the
        # response schema (see _finite).
        for key, default in (
            ("sea_surface_temperature_c", 27.0),
            ("current_velocity_ms", 0.0),
            ("current_direction_deg", 0.0),
            ("wave_height_m", 0.0),
            ("wave_direction_deg", 0.0),
            ("wind_speed_kmh", 0.0),
            ("wind_direction_deg", 0.0),
        ):
            marine_values[key] = _finite(marine_values.get(key), default)
        marine_values["weather_code"] = int(_finite(marine_values.get("weather_code"), 0.0))

        marine_values["timestamp"] = marine.get("time") or marine_values["timestamp"]

        async with self._lock:
            self._cache[cache_key] = (datetime.now(timezone.utc).timestamp(), marine_values)

        return marine_values

    async def _wind_conditions(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, float | int]:
        """Fetch wind speed/direction and weather code from the Open-Meteo weather API.

        Wind is a first-class input to the habitat model but is not served by the
        Marine API, so it is requested separately. This call is best-effort: if the
        weather API is unreachable we return neutral values rather than failing the
        whole marine request.
        """
        fallback: dict[str, float | int] = {
            "wind_speed_kmh": 0.0,
            "wind_direction_deg": 0.0,
            "weather_code": 0,
        }
        params: dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["wind_speed_10m", "wind_direction_10m", "weather_code"],
            "timezone": "UTC",
            "wind_speed_unit": "kmh",
        }
        try:
            timeout = httpx.Timeout(12.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(self._settings.openmeteo_weather_url, params=params)
                resp.raise_for_status()
                data = resp.json()
            current = data.get("current", {}) or {}
            return {
                "wind_speed_kmh": _finite(current.get("wind_speed_10m"), 0.0),
                "wind_direction_deg": _finite(current.get("wind_direction_10m"), 0.0),
                "weather_code": int(_finite(current.get("weather_code"), 0.0)),
            }
        except Exception:
            return fallback

    async def marine_conditions_playback(
        self,
        latitude: float,
        longitude: float,
        observed_at: datetime,
    ) -> dict[str, Any]:
        """Best-effort historical marine conditions for a sighting.

        Open-Meteo marine API is primarily current/forecast-oriented. For the MVP we
        therefore fall back to a transparent "enriched estimate" built from recent
        nearby marine conditions plus reasonable defaults, and we clearly label the
        source so sightings are never silently treated as hard measurements.

        A production deployment would swap this for NOAA/ERDDAP or a pre-downloaded
        historical dataset.
        """
        # Try to retrieve recent nearby marine conditions live from Open-Meteo (current),
        # then annotate with the fact that this is a recent estimate for a past time.
        try:
            recent = await self.marine_conditions(latitude, longitude)
        except Exception:
            recent = self._blank_marine(latitude, longitude)

        ts = observed_at.astimezone(timezone.utc)
        out = dict(recent)
        out["lat"] = latitude
        out["lng"] = longitude
        out["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        out["observed_at"] = ts.isoformat()
        out["_source"] = "open_meteo_marine_recent_estimate"
        out["_note"] = (
            "Open-Meteo marine API primarily serves current/forecast conditions. "
            "This sighting is enriched with the most recent available marine conditions "
            "for this location and timestamped accordingly, not a historical reanalysis."
        )
        return out

    def _blank_marine(self, latitude: float, longitude: float) -> dict[str, Any]:
        return {
            "lat": latitude,
            "lng": longitude,
            "timestamp": _iso_now_z(),
            "sea_surface_temperature_c": 27.0,
            "current_velocity_ms": 0.0,
            "current_direction_deg": 0.0,
            "wave_height_m": 0.0,
            "wave_direction_deg": 0.0,
            "wind_speed_kmh": 0.0,
            "wind_direction_deg": 0.0,
            "weather_code": 0,
            "water_depth_m": None,
            "_raw": {},
            "_source": "blank",
            "_note": "Fallback marine estimate; no live Open-Meteo data available.",
        }


marine_service = MarineService()
