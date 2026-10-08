from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.data.species_db import REGIONS, SPECIES
from app.models.models import (
    ConservationStatus,
    LegalRestriction,
    MarineRegion,
    ModelVersion,
    Observation,
    ObservationEnvironment,
    Reward,
    Species,
    SpeciesHabitatProfile,
    User,
    DataSourceStatus,
)

DEMO_SOURCE_TAG = "SAMPLE DATA - synthetic example sighting for map demonstration, not a real report"

# Offshore positions west of the Maharashtra coast, so every demo marker lands in
# water rather than on land when plotted on the real basemap.
# (latitude, longitude, species_id, days_ago)
DEMO_SIGHTINGS: list[tuple[float, float, int, int]] = [
    (19.20, 72.55, 1, 1),
    (19.05, 72.70, 1, 2),
    (18.85, 72.80, 2, 2),
    (18.60, 72.85, 6, 3),
    (18.30, 72.95, 1, 4),
    (18.00, 73.00, 4, 5),
    (19.40, 72.50, 7, 6),
    (17.75, 73.05, 2, 7),
    (19.60, 72.45, 1, 9),
    (18.45, 72.75, 5, 11),
    (19.15, 72.40, 6, 13),
    (18.95, 72.60, 3, 16),
]


async def seed_if_empty(session: AsyncSession) -> None:
    from sqlalchemy import select

    region_exists = await session.execute(select(MarineRegion.id).limit(1))
    if region_exists.scalar_one_or_none() is None:
        for r in REGIONS:
            region = MarineRegion(
                id=r.id,
                name=r.name,
                label=r.label,
                centroid_lat=r.centroid_lat,
                centroid_lng=r.centroid_lng,
                default_search_radius_km=r.default_search_radius_km,
                bounds_north=r.bounds["north"],
                bounds_south=r.bounds["south"],
                bounds_east=r.bounds["east"],
                bounds_west=r.bounds["west"],
                is_active=True,
            )
            session.add(region)

        # Species + profiles + conservation + legal
        for s in SPECIES:
            species = Species(
                id=s.id,
                name=s.name,
                scientific_name=s.scientific_name,
                conservation_status=s.conservation_status,
                legal_catch_status=s.legal_catch_status,
                typical_habitat=s.typical_habitat,
                seasonal_behavior=s.seasonal_behavior,
                current_sensitivity=s.current_sensitivity,
                known_regions=str(s.known_regions).replace("'", '"'),
                regional_restriction=s.regional_restriction,
                seasonal_restriction=s.seasonal_restriction,
                description=s.description,
                thumbnail_hint=s.thumbnail_hint,
                weight_kg_min=s.weight_kg_min,
                weight_kg_max=s.weight_kg_max,
                preferred_temperature_min_c=s.preferred_temperature_min_c,
                preferred_temperature_max_c=s.preferred_temperature_max_c,
                preferred_depth_min_m=s.preferred_depth_min_m,
                preferred_depth_max_m=s.preferred_depth_max_m,
                preferred_current_min_ms=s.preferred_current_min_ms,
                preferred_current_max_ms=s.preferred_current_max_ms,
            )
            session.add(species)

            profile = SpeciesHabitatProfile(
                species_id=s.id,
                preferred_temperature_min_c=s.preferred_temperature_min_c,
                preferred_temperature_max_c=s.preferred_temperature_max_c,
                preferred_depth_min_m=s.preferred_depth_min_m,
                preferred_depth_max_m=s.preferred_depth_max_m,
                preferred_current_min_ms=s.preferred_current_min_ms,
                preferred_current_max_ms=s.preferred_current_max_ms,
                typical_habitat=s.typical_habitat,
                seasonal_behavior=s.seasonal_behavior,
                current_sensitivity=s.current_sensitivity,
            )
            session.add(profile)

            conserv = ConservationStatus(
                species_id=s.id,
                iucn_status=s.conservation_status,
                notes=None,
            )
            session.add(conserv)

            legal = LegalRestriction(
                species_id=s.id,
                legal_catch_status=s.legal_catch_status,
                regional_restriction=s.regional_restriction,
                seasonal_restriction=s.seasonal_restriction,
                jurisdiction="maharashtra",
            )
            session.add(legal)

        # Default model version (MVP rule-based)
        v1 = ModelVersion(
            version="v1.0-rule-based",
            kind="rule_based",
            species_count=len(SPECIES),
            observation_count=0,
            metrics_json=None,
            is_active=True,
        )
        session.add(v1)

        # Data source status
        session.add(DataSourceStatus(id="open_meteo_marine", source="open_meteo_marine", status="healthy", detail=None))

        # Default admin account (demo credentials for the MVP) so the admin console is reachable out of the box.
        session.add(User(
            email="admin@aquatrack.dev",
            hashed_password=hash_password("admin123"),
            display_name="AquaTrack Admin",
            role="admin",
        ))

        # Sandbox rewards
        sandbox_rewards = [
            ("reward_100_voucher", "₹100 Voucher", "Test voucher credit for MVP contributors (sandbox provider).", "₹100 Voucher", 250, "sandbox", True),
            ("reward_250_voucher", "₹250 Voucher", "Higher-value test voucher for top contributors (sandbox provider).", "₹250 Voucher", 600, "sandbox", True),
            ("reward_500_voucher", "₹500 Voucher", "Premium test voucher for the most active contributors (sandbox provider).", "₹500 Voucher", 1200, "sandbox", True),
        ]
        for rid, title, desc, val, cost, provider, avail in sandbox_rewards:
            session.add(Reward(
                id=rid,
                title=title,
                description=desc,
                value_label=val,
                points_cost=cost,
                provider=provider,
                available=avail,
                metadata_json=None,
            ))

        await session.commit()

    # --- Demo sightings -------------------------------------------------------
    # A brand-new database has no observations at all, which leaves the map's fish
    # layer empty and the feature impossible to see or verify. These rows are
    # synthetic and labelled as such in `notes`, so nothing on screen can be
    # mistaken for a genuine report. Guarded by its own check because the block
    # above only runs on a database that has no regions yet.
    obs_exists = await session.execute(select(Observation.id).limit(1))
    if obs_exists.scalar_one_or_none() is None:
        admin = (
            await session.execute(select(User).where(User.role == "admin"))
        ).scalars().first()
        if admin is not None:
            species_ids = {s.id for s in SPECIES}
            now_utc = datetime.now(timezone.utc)
            for lat, lng, species_id, days_ago in DEMO_SIGHTINGS:
                if species_id not in species_ids:
                    continue
                observed_at = now_utc - timedelta(days=days_ago)
                obs = Observation(
                    created_by=admin.id,
                    species_id=species_id,
                    latitude=lat,
                    longitude=lng,
                    observed_at=observed_at,
                    observation_type="observed",
                    quantity_kg=None,
                    photo_url=None,
                    notes=DEMO_SOURCE_TAG,
                    status="validated",
                    flagged_reason=None,
                    # 0-100 scale, matching compute_quality_score(). A 0-1 value here
                    # would render as "1%" in the map's sighting popup.
                    quality_score=75.0,
                    is_public=True,
                )
                session.add(obs)
                await session.flush()
                session.add(
                    ObservationEnvironment(
                        observation_id=obs.id,
                        # Plausible October values for the eastern Arabian Sea; these
                        # are illustrative, not a retrieval from a data source.
                        sea_surface_temperature_c=28.6,
                        current_velocity_ms=0.35,
                        current_direction_deg=210.0,
                        wave_height_m=0.9,
                        wave_direction_deg=225.0,
                        wind_speed_kmh=14.0,
                        wind_direction_deg=240.0,
                        weather_code=2,
                        water_depth_m=55.0,
                        source="synthetic_demo_seed",
                    )
                )
            await session.commit()
