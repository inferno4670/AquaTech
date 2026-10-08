from __future__ import annotations

from fastapi import APIRouter

from app.schemas.schemas import MarineRegion
from app.data.species_db import _regions, region_by_id, species_by_id

router = APIRouter()


@router.get("/map/layers")
async def available_layers():
    return {
        "layers": [
            {"id": "suitability", "name": "Habitat Suitability", "type": "heatmap", "default_on": True},
            {"id": "temperature", "name": "Sea Surface Temperature", "type": "heatmap", "default_on": False},
            {"id": "current", "name": "Ocean Current", "type": "animated_vectors", "default_on": False},
            {"id": "wave", "name": "Wave Conditions", "type": "intensity", "default_on": False},
            {"id": "sightings", "name": "Historical Sightings", "type": "point_clusters", "default_on": False},
            {"id": "fishing_activity", "name": "Fishing Activity", "type": "raster", "default_on": False, "note": "GFW datasets, registration required"},
            {"id": "bathymetry", "name": "Bathymetry", "type": "raster", "default_on": False, "note": "GEBCO 2026 grid"},
        ]
    }


@router.get("/map/grid")
async def prediction_grid(
    species_id: int,
    region_id: int,
    date: str,
    radius_km: float | None = None,
):
    from app.services.prediction import _haversine_km

    species = species_by_id(species_id)
    if not species:
        return {"zones": []}

    region = region_by_id(region_id)
    if not region:
        return {"zones": []}

    bounds = {
        "north": region.bounds["north"],
        "south": region.bounds["south"],
        "east": region.bounds["east"],
        "west": region.bounds["west"],
        "centroid_lat": region.centroid_lat,
        "centroid_lng": region.centroid_lng,
        "default_search_radius_km": region.default_search_radius_km,
        "label": region.label,
    }

    radius = radius_km or region.default_search_radius_km

    # Build a lightweight grid response (no full marine fetch per cell; MVP uses regional sample)
    # For responsiveness, we cap cell count.
    res = 0.25  # degrees approx ~25km near equator; we keep coarse for MVP
    cells = []
    lat = bounds["south"]
    while lat <= bounds["north"]:
        lon = bounds["west"]
        while lon <= bounds["east"]:
            cells.append((round(lat, 4), round(lon, 4)))
            lon += res
        lat += res

    zones = []
    center_lat = bounds["centroid_lat"]
    center_lng = bounds["centroid_lng"]
    for idx, (lat, lon) in enumerate(cells):
        dist = _haversine_km(lat, lon, center_lat, center_lng)
        if radius and dist > radius:
            continue
        zones.append({
            "grid_id": f"cell_{idx:04d}",
            "lat": lat,
            "lng": lon,
            "distance_km": round(dist, 1),
        })
        if len(zones) >= 2000:
            break

    return {"zones": zones, "species_id": species_id, "region_id": region_id, "date": date}
