from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from math import cos, radians, sin
from typing import Any

from app.data.species_db import (
    depth_suitability,
    historical_similarity,
    needs_protection,
    seasonality_score,
    seasonal_match_label,
    temperature_suitability,
    triangular_weight,
    wave_suitability,
)
from app.schemas.schemas import MarineConditions, PredictionBasis, PredictionRunResponse, PredictionZone
from app.services.marine import marine_service

NO_DATA_VALUE = -9999.0


def _num(value: Any, default: float) -> float:
    """Coerce potentially-None/str marine values to a finite float default."""
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return f if f == f and f not in (float("inf"), float("-inf")) else default


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1r, lon1r = radians(lat1), radians(lon1)
    lat2r, lon2r = radians(lat2), radians(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = sin(dlat / 2) ** 2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2) ** 2
    c = 2 * (a ** 0.5)
    return R * _degrees_to_radians(c)


def _degrees_to_radians(x: float) -> float:
    return x * 3.141592653589793 / 180.0


def _estimate_depth_m(latitude: float, longitude: float, region_center_lat: float) -> float:
    """Very rough MVP bathymetry proxy: depth increases with distance from a simple
    near-coast assumption. Not a substitute for GEBCO.

    For Maharashtra west coast, a crude model:
      - within ~25 km offshore => shallow shelf
      - beyond that => deeper
    """
    dist_km = _haversine_km(latitude, longitude, region_center_lat, 72.5)
    # crude shelf slope proxy
    depth = min(200.0, max(5.0, dist_km * 2.2))
    return round(depth, 1)


def _distance_from_coast_km(latitude: float, longitude: float, region_center_lat: float, region_center_lng: float) -> float:
    return _haversine_km(latitude, longitude, region_center_lat, region_center_lng)


def _is_on_land(latitude: float, longitude: float) -> bool:
    """Crude Maharashtra west-coast land mask.

    The Maharashtra coastline runs roughly north-south along ~72.5-73.5°E between
    ~17.5°N and ~20.5°N. For the MVP we treat any cell at-or-east of the nearest
    west-coast latitude-dependent meridian as "land" and skip it, so the hotspot
    layer never paints synthetic fish on the peninsula.

    This is intentionally a coarse guardrail. A production deployment would swap it
    for a real coastline/land-sea mask (for example GSHHG or a raster mask from
    GEBCO/Open-Meteo land-sea fraction).
    """
    if not (17.5 <= latitude <= 20.5 and 71.6 <= longitude <= 73.6):
        # Outside the Maharashtra study box entirely — not our problem to adjudicate.
        return False
    # Approximate west-coast meridian as a function of latitude along the Maharashtra
    # shore. Farther north, the coast sits a little farther east; farther south a bit
    # farther west. Anything at-or-east of this meridian is inland for the MVP.
    coast_lng = 72.50 + (latitude - 19.0) * 0.18
    return longitude >= coast_lng


def _grid_cells_for_region(
    region: dict[str, Any],
    resolution_km: float,
    center_lat: float,
    center_lng: float,
) -> list[dict[str, Any]]:
    """Create a lat/lon grid covering the radius band around the region centroid.

    The old implementation generated the full region bounding box and then trimmed by
    radius only during scoring. That made the km-radius slider feel broken: the map
    still lit up the whole coast. Now the grid itself is bounded to a square band of
    side 2*radius around the centroid, so smaller radii produce visibly smaller grids.

    We still keep the marine-only guardrail inside the scoring loop (via _is_on_land)
    so no inland cell can ever become a zone.
    """
    radius_km = region.get("search_radius_km", 50.0)
    half = radius_km + resolution_km  # small overshoot so the band edge is covered

    dlat = half / 111.0
    dlng = half / (111.0 * cos(radians(center_lat)))

    south = center_lat - dlat
    north = center_lat + dlat
    west = center_lng - dlng
    east = center_lng + dlng

    lat_step = resolution_km / 111.0
    lon_step = resolution_km / (111.0 * cos(radians(center_lat)))

    cells: list[dict[str, Any]] = []
    lat = south
    while lat <= north:
        lon = west
        while lon <= east:
            cells.append({"latitude": round(lat, 4), "longitude": round(lon, 4)})
            lon += lon_step
        lat += lat_step
    return cells


async def predict(
    species_id: int,
    region_id: int,
    prediction_date: str,
    time_hour: int | None,
    search_radius_km: float | None,
    region_bounds: dict[str, Any],
    observation_density_nearby: float = 0.0,
) -> PredictionRunResponse:
    from app.data.species_db import species_by_id

    species = species_by_id(species_id)
    if species is None:
        raise ValueError(f"Unknown species_id={species_id}")

    region = _region_from_bounds(region_bounds)
    center_lat = region["centroid_lat"]
    center_lng = region["centroid_lng"]

    resolution = 10.0
    radius = search_radius_km or region.get("default_search_radius_km", 50.0) or 50.0

    region["search_radius_km"] = radius
    cells = _grid_cells_for_region(region, resolution, center_lat, center_lng)

    # Fetch a representative marine conditions sample from the region centroid to
    # use as the environmental baseline across the grid (MVP simplification).
    # In production, each cell would be sampled individually from a local cache of
    # Open-Meteo points or a regional marine reanalysis.
    marine = await marine_service.marine_conditions(center_lat, center_lng)
    base = MarineConditions(
        lat=marine["lat"],
        lng=marine["lng"],
        timestamp=marine["timestamp"],
        sea_surface_temperature_c=_num(marine.get("sea_surface_temperature_c"), 27.0),
        current_velocity_ms=_num(marine.get("current_velocity_ms"), 0.0),
        current_direction_deg=_num(marine.get("current_direction_deg"), 0.0),
        wave_height_m=_num(marine.get("wave_height_m"), 0.0),
        wave_direction_deg=_num(marine.get("wave_direction_deg"), 0.0),
        wind_speed_kmh=_num(marine.get("wind_speed_kmh"), 0.0),
        wind_direction_deg=_num(marine.get("wind_direction_deg"), 0.0),
        weather_code=marine.get("weather_code", 0),
        water_depth_m=marine.get("water_depth_m"),
    )

    # Seasonal / temporal context
    date_obj = datetime.strptime(prediction_date, "%Y-%m-%d")
    month = date_obj.month
    hour = time_hour if time_hour is not None else 6

    now_z = datetime.now(timezone.utc)
    generated_at = now_z.strftime("%Y-%m-%dT%H:%M:%SZ")

    zones: list[PredictionZone] = []

    for idx, cell in enumerate(cells):
        lat = cell["latitude"]
        lon = cell["longitude"]

        # Land guardrail: no inland cell may ever become a predicted zone or a
        # hotspot marker, regardless of how good its score would be.
        if _is_on_land(lat, lon):
            continue

        dist_km = _haversine_km(lat, lon, center_lat, center_lng)
        if radius and dist_km > radius:
            continue

        depth_m = _estimate_depth_m(lat, lon, center_lat)
        dist_coast_km = _distance_from_coast_km(lat, lon, center_lat, center_lng)

        # For the MVP we treat the regional marine sample as representative.
        sst = base.sea_surface_temperature_c
        current_vel = base.current_velocity_ms
        current_dir = base.current_direction_deg
        wave_height = base.wave_height_m

        temp_score = temperature_suitability(species, sst)
        depth_score = depth_suitability(species, depth_m)
        current_score = current_suitability_local(species, current_vel)
        wave_score = wave_suitability(species, wave_height)
        seasonal = seasonality_score(species, month)

        # Historical similarity: blend environmental closeness with observation density.
        presence = min(1.0, observation_density_nearby)
        hist_score = historical_similarity(species, {
            "sea_surface_temperature_c": sst,
            "current_velocity_ms": current_vel,
            "water_depth_m": depth_m,
        }, presence)

        # Weighted composite suitability
        weights = {
            "temperature": 0.30,
            "depth": 0.22,
            "current": 0.14,
            "wave": 0.08,
            "historical": 0.16,
            "seasonality": 0.10,
        }
        suitability = (
            temp_score * weights["temperature"]
            + depth_score * weights["depth"]
            + current_score * weights["current"]
            + wave_score * weights["wave"]
            + hist_score * weights["historical"]
            + seasonal * weights["seasonality"]
        )

        # Confidence: combines data freshness, observation support, and model clarity.
        # - Freshness: we always use live Open-Meteo data in MVP, so freshness is high.
        freshness_factor = 0.9
        # - Observation support: scaled by nearby historical sightings.
        obs_factor = 0.4 + 0.6 * presence
        # - Model clarity: rule-based model is deterministic, but we lower confidence
        #   when suitability sits in a borderline band where small env changes flip the result.
        clarity = 1.0 - abs(suitability - 0.5) * 0.6
        confidence = clamp(0.55 * freshness_factor + 0.30 * obs_factor + 0.15 * clarity, 0.0, 1.0)

        hist_label = _hist_label_from_score(hist_score)
        season_label = seasonal_match_label(species, month, hist_label)

        basis = PredictionBasis(
            temperature=temp_score > 0.5,
            current=current_score > 0.5,
            depth=depth_score > 0.5,
            seasonality=seasonal > 0.5,
            historical_sightings=presence > 0.2,
            wave=wave_score > 0.5,
            notes=_basis_notes(species, temp_score, depth_score, current_score, wave_score, seasonal, hist_score, presence),
        )

        zones.append(
            PredictionZone(
                grid_id=f"cell_{idx:04d}",
                lat=lat,
                lng=lon,
                suitability=round(suitability, 3),
                confidence=round(confidence, 3),
                sea_surface_temperature_c=round(sst, 2),
                current_velocity_ms=round(current_vel, 3),
                current_direction_deg=round(current_dir, 1),
                wave_height_m=round(wave_height, 2),
                water_depth_m=depth_m,
                distance_from_coast_km=round(dist_coast_km, 1),
                historical_match=hist_label,
                seasonal_match=season_label,
                basis=basis,
            )
        )

    # Sort descending by a combined utility = suitability * confidence
    zones.sort(key=lambda z: z.suitability * z.confidence, reverse=True)
    if len(zones) > 800:
        zones = zones[:800]

    data_freshness_sec = 0
    try:
        ts = datetime.fromisoformat(marine["timestamp"].replace("Z", "+00:00"))
        data_freshness_sec = int((now_z - ts).total_seconds())
    except Exception:
        pass

    params_hash = _params_hash(species_id, region_id, prediction_date, time_hour, search_radius_km, observation_density_nearby)

    return PredictionRunResponse(
        id="",  # filled by caller persistence layer
        species_id=species_id,
        species_name=species.name,
        region_id=region_id,
        region_name=region.get("label", "Maharashtra Coast"),
        prediction_date=prediction_date,
        model_version="v1.0-rule-based",
        generated_at=generated_at,
        data_freshness_sec=data_freshness_sec,
        observation_count=int(round(observation_density_nearby * 1000)),
        zones=zones,
    )


def _region_from_bounds(bounds: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounds_north": bounds.get("north", 20.5),
        "bounds_south": bounds.get("south", 17.5),
        "bounds_east": bounds.get("east", 73.6),
        "bounds_west": bounds.get("west", 71.6),
        "centroid_lat": bounds.get("centroid_lat", 19.0),
        "centroid_lng": bounds.get("centroid_lng", 72.5),
        "default_search_radius_km": bounds.get("default_search_radius_km", 50.0),
        "label": bounds.get("label", "Maharashtra Coast"),
    }


def current_suitability_local(species: Any, velocity_ms: float) -> float:
    from app.schemas.schemas import SpeciesProfile
    profile = SpeciesProfile(
        id=0,
        name="",
        scientific_name="",
        conservation_status="",
        legal_catch_status="",
        thumbnail_hint=None,
        preferred_temperature_min_c=species.preferred_temperature_min_c,
        preferred_temperature_max_c=species.preferred_temperature_max_c,
        preferred_depth_min_m=species.preferred_depth_min_m,
        preferred_depth_max_m=species.preferred_depth_max_m,
        preferred_current_min_ms=species.preferred_current_min_ms,
        preferred_current_max_ms=species.preferred_current_max_ms,
        typical_habitat=species.typical_habitat,
        seasonal_behavior=species.seasonal_behavior,
        current_sensitivity=species.current_sensitivity,
        known_regions=species.known_regions,
        regional_restriction=species.regional_restriction,
        seasonal_restriction=species.seasonal_restriction,
        weight_kg_min=species.weight_kg_min,
        weight_kg_max=species.weight_kg_max,
        description=species.description,
        natural_lat_min=species.natural_lat_min,
        natural_lat_max=species.natural_lat_max,
        natural_lng_min=species.natural_lng_min,
        natural_lng_max=species.natural_lng_max,
        monsoon_peak=species.monsoon_peak,
        monsoon_off=species.monsoon_off,
        prefers_rain=species.prefers_rain,
        storm_tolerance=species.storm_tolerance,
        hot_behavior=species.hot_behavior,
        cold_behavior=species.cold_behavior,
        tide_affinity=species.tide_affinity,
        night_activity=species.night_activity,
        surface_feed_behavior=species.surface_feed_behavior,
    )
    return current_suitability_from_profile(profile, velocity_ms)


def current_suitability_from_profile(profile: Any, velocity_ms: float) -> float:
    return triangular_weight(velocity_ms,
                             (profile.preferred_current_min_ms + profile.preferred_current_max_ms) / 2.0,
                             (profile.preferred_current_max_ms - profile.preferred_current_min_ms) / 2.0)


def _hist_label_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "moderate"
    if score >= 0.2:
        return "low"
    return "none"


def _basis_notes(
    species: Any,
    temp_score: float,
    depth_score: float,
    current_score: float,
    wave_score: float,
    seasonal: float,
    hist_score: float,
    presence: float,
) -> str:
    parts: list[str] = []
    if temp_score > 0.7:
        parts.append("Temperature closely matches preferred range")
    elif temp_score > 0.4:
        parts.append("Temperature within acceptable range")
    else:
        parts.append("Temperature outside preferred range")
    if depth_score > 0.7:
        parts.append("Depth closely matches preferred range")
    elif depth_score > 0.4:
        parts.append("Depth within acceptable range")
    else:
        parts.append("Depth outside preferred range")
    if current_score > 0.7:
        parts.append("Current within preferred range")
    elif current_score > 0.4:
        parts.append("Current near preferred range")
    else:
        parts.append("Current outside preferred range")
    if presence > 0.2:
        parts.append(f"Historical sightings nearby ({int(round(presence*100))}% density proxy)")
    else:
        parts.append("Limited historical sightings nearby")
    if seasonal < 0.5:
        parts.append("Season is less typical for this species")
    return ". ".join(parts) + "."


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _params_hash(species_id: int, region_id: int, date: str, hour: int | None, radius: float | None, density: float) -> str:
    s = f"{species_id}:{region_id}:{date}:{hour}:{radius}:{density}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]
