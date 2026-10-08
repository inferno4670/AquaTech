from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.schemas.schemas import MarineRegion as RegionSchema, SpeciesProfile as SpeciesSchema


# Editorial environment-behavior dataset for each species.
# These fields are the source of truth for SPECIES_DATASET.md and for the species
# detail page's "environmental triggers" section. They are intentionally human-readable
# and are not currently consumed directly by the v1 prediction model (which uses the
# numeric ranges instead); they exist so the dataset has the "when it rains / storms /
# hot / cold" semantics the user asked for.

EnvBehavior = dict[str, Any]


@dataclass(frozen=True)
class GeoBounds:
    north: float
    south: float
    east: float
    west: float


REGIONS: list[RegionSchema] = [
    RegionSchema(
        id=1,
        name="maharashtra_coast",
        label="Maharashtra Coast",
        centroid_lat=19.0,
        centroid_lng=72.5,
        default_search_radius_km=50.0,
        bounds={"north": 20.5, "south": 17.5, "east": 73.6, "west": 71.6},
        is_active=True,
    ),
]

DEFAULT_REGION_ID = 1
DEFAULT_SPECIES_ID = 1


def _regions() -> list[RegionSchema]:
    return REGIONS


def region_by_id(region_id: int) -> RegionSchema | None:
    for r in REGIONS:
        if r.id == region_id:
            return r
    return None


SPECIES: list[SpeciesSchema] = [
    SpeciesSchema(
        id=1,
        name="Indian Mackerel",
        scientific_name="Rastrelliger kanagurta",
        conservation_status="least_concern",
        legal_catch_status="regulated",
        thumbnail_hint="mackerel",
        preferred_temperature_min_c=22.0,
        preferred_temperature_max_c=28.0,
        preferred_depth_min_m=20.0,
        preferred_depth_max_m=100.0,
        preferred_current_min_ms=0.2,
        preferred_current_max_ms=0.8,
        typical_habitat="Coastal / Continental Shelf",
        seasonal_behavior="Peaks during pre-monsoon and post-monsoon; forms near-shore schools.",
        current_sensitivity="Moderate — schools track moderate coastal currents.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Permitted with standard license; observe closed seasons per MFD norms.",
        seasonal_restriction="Peak-season aggregations warrant conservative effort.",
        weight_kg_min=0.15,
        weight_kg_max=0.5,
        description="Small, fast, schooling pelagic fish common along the west coast. A staple for small-scale fishermen and a strong candidate for habitat-based prediction.",
        natural_lat_min=14.0,
        natural_lat_max=21.0,
        natural_lng_min=68.0,
        natural_lng_max=75.5,
        monsoon_peak="Post-monsoon (Oct-Dec) — strongest near-shore feeding runs.",
        monsoon_off="Pre-monsoon (Mar-May): warm, clear water, active surface feeders.",
        prefers_rain=True,
        storm_tolerance="Moderate — schools scatter in heavy chop, regroup after the front passes.",
        hot_behavior="Above 30°C moves slightly deeper and slows surface feeding.",
        cold_behavior="Below 21°C activity drops; schools compress toward warmer shelf water.",
        tide_affinity="Active on rising tide and tide changes near shore.",
        night_activity="Moderate — schools stay near surface at night in calm weather.",
        surface_feed_behavior="Strong — readily feeds on the surface when bait is present.",
    ),
    SpeciesSchema(
        id=2,
        name="Sardine",
        scientific_name="Sardinella longiceps",
        conservation_status="least_concern",
        legal_catch_status="regulated",
        thumbnail_hint="sardine",
        preferred_temperature_min_c=23.0,
        preferred_temperature_max_c=30.0,
        preferred_depth_min_m=10.0,
        preferred_depth_max_m=80.0,
        preferred_current_min_ms=0.1,
        preferred_current_max_ms=0.6,
        typical_habitat="Coastal / Pelagic",
        seasonal_behavior="Abundant in warmer months; nearshore shoals.",
        current_sensitivity="Low to moderate.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Standard license applies.",
        weight_kg_min=0.05,
        weight_kg_max=0.2,
        description="Silver sardine with large nearshore shoals. Sensitive to temperature shifts and often appears with other small pelagics.",
        natural_lat_min=12.0,
        natural_lat_max=20.5,
        natural_lng_min=68.0,
        natural_lng_max=74.5,
        monsoon_peak="Southwest monsoon onset (Jun-Jul): plankton bloom drives nearshore abundance.",
        monsoon_off="Winter (Dec-Feb): still present but more dispersed.",
        prefers_rain=True,
        storm_tolerance="High in shoals — tolerates rough surface water; avoids the strongest breakers.",
        hot_behavior="Tolerates warm water well; blooms during hot months.",
        cold_behavior="Below 22°C shoals thin out and drift offshore deeper.",
        tide_affinity="Loose — more driven by plankton drift than tide.",
        night_activity="Low to moderate — mostly daylight shoaling.",
        surface_feed_behavior="Moderate — filter-feeder; surface only when baitfish are present.",
    ),
    SpeciesSchema(
        id=3,
        name="Shrimp (Penaeid)",
        scientific_name="Penaeus spp.",
        conservation_status="least_concern",
        legal_catch_status="regulated",
        thumbnail_hint="shrimp",
        preferred_temperature_min_c=24.0,
        preferred_temperature_max_c=31.0,
        preferred_depth_min_m=5.0,
        preferred_depth_max_m=60.0,
        preferred_current_min_ms=0.05,
        preferred_current_max_ms=0.4,
        typical_habitat="Inshore / Estuarine / Muddy bottom",
        seasonal_behavior="Tied to monsoon-driven productivity cycles.",
        current_sensitivity="Low; prefers sheltered nearshore grounds.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Permitted with license; some estuarine zones have seasonal restrictions.",
        weight_kg_min=0.01,
        weight_kg_max=0.05,
        description="Penaeid shrimp support important inshore fisheries. Ground-truth observations are especially valuable because suitable habitat is patchy and tide-influenced.",
        natural_lat_min=13.0,
        natural_lat_max=20.5,
        natural_lng_min=68.5,
        natural_lng_max=74.0,
        monsoon_peak="Southwest monsoon (Jun-Sep): estuarine flushing and productivity peak.",
        monsoon_off="Winter (Nov-Feb): still active near river mouths and sheltered bays.",
        prefers_rain=True,
        storm_tolerance="High in sheltered water; avoids open-bay chop during storms.",
        hot_behavior="Warm water suits growth; extreme heat spikes can push them deeper in the water column.",
        cold_behavior="Below 23°C activity slows; estuary-fed grounds remain best.",
        tide_affinity="Strong — moving tides concentrate shrimp in channels and edges.",
        night_activity="High — many penaeid species move up in the water column at night.",
        surface_feed_behavior="Low — bottom and mid-water feeder, not a surface species.",
    ),
    SpeciesSchema(
        id=4,
        name="Kingfish",
        scientific_name="Scomberomorus guttatus",
        conservation_status="near_threatened",
        legal_catch_status="regulated",
        thumbnail_hint="kingfish",
        preferred_temperature_min_c=22.0,
        preferred_temperature_max_c=29.0,
        preferred_depth_min_m=10.0,
        preferred_depth_max_m=120.0,
        preferred_current_min_ms=0.2,
        preferred_current_max_ms=0.9,
        typical_habitat="Coastal / Shelf edge",
        seasonal_behavior="Seasonal migratory aggregations along the coast.",
        current_sensitivity="Moderate to high; follows prey movements.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Regulated catch; respect size/season limits.",
        seasonal_restriction="Seasonal aggregations may warrant reduced effort.",
        weight_kg_min=1.5,
        weight_kg_max=8.0,
        description="Fast predator of the scombrid family. Near-threatened status means this species should surface conservation context prominently.",
        natural_lat_min=12.0,
        natural_lat_max=21.0,
        natural_lng_min=68.0,
        natural_lng_max=75.0,
        monsoon_peak="Pre-monsoon and post-monsoon — strong feeding runs along the coast.",
        monsoon_off="Mid-monsoon: may move farther offshore or hold on current edges.",
        prefers_rain=False,
        storm_tolerance="Moderate — avoids the worst surface storm chop; holds deeper or on edges.",
        hot_behavior="Above 28°C may shift slightly deeper and hunt current edges.",
        cold_behavior="Below 21°C feeding slows and aggregations loosen.",
        tide_affinity="Moderate — often near structure and current changes at tide turns.",
        night_activity="Moderate to high — predator that can feed after dark in clear water.",
        surface_feed_behavior="Strong — explosive surface strikes when chasing bait.",
    ),
    SpeciesSchema(
        id=5,
        name="Anchovy",
        scientific_name="Stolephorus spp.",
        conservation_status="least_concern",
        legal_catch_status="unrestricted",
        thumbnail_hint="anchovy",
        preferred_temperature_min_c=22.0,
        preferred_temperature_max_c=30.0,
        preferred_depth_min_m=5.0,
        preferred_depth_max_m=50.0,
        preferred_current_min_ms=0.05,
        preferred_current_max_ms=0.5,
        typical_habitat="Coastal / Pelagic",
        seasonal_behavior="Abundant in productive coastal waters year-round.",
        current_sensitivity="Low.",
        known_regions=["maharashtra_coast"],
        weight_kg_min=0.01,
        weight_kg_max=0.03,
        description="Small, abundant forage fish. Useful baseline observations because anchovies respond strongly to seasonal productivity.",
        natural_lat_min=12.0,
        natural_lat_max=20.5,
        natural_lng_min=68.0,
        natural_lng_max=74.5,
        monsoon_peak="Southwest monsoon and post-monsoon — plankton-driven abundance peaks.",
        monsoon_off="Winter: still present but scattered near productive zones.",
        prefers_rain=True,
        storm_tolerance="High in large, tight shoals; dispersed by extreme surface turbulence.",
        hot_behavior="Tolerates warm water; blooms during hot productive months.",
        cold_behavior="Below 21°C shoals thin out near shore.",
        tide_affinity="Weak — more driven by plankton and currents than tide.",
        night_activity="Low to moderate — mostly daytime schooling.",
        surface_feed_behavior="Moderate — surface and mid-water filter-feeder.",
    ),
    SpeciesSchema(
        id=6,
        name="Silver Pomfret",
        scientific_name="Pampus argenteus",
        conservation_status="vulnerable",
        legal_catch_status="restricted",
        thumbnail_hint="pomfret",
        preferred_temperature_min_c=22.0,
        preferred_temperature_max_c=28.0,
        preferred_depth_min_m=30.0,
        preferred_depth_max_m=100.0,
        preferred_current_min_ms=0.15,
        preferred_current_max_ms=0.6,
        typical_habitat="Shelf / Soft bottom",
        seasonal_behavior="Seasonally variable; valued commercial species.",
        current_sensitivity="Low to moderate.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Restricted — treat as conservation-sensitive in UI.",
        seasonal_restriction="Avoid targeting during known spawning peaks.",
        weight_kg_min=0.8,
        weight_kg_max=2.5,
        description="High-value silver pomfret with vulnerable status. The platform should show clear conservation context rather than an unqualified 'go here' signal.",
        natural_lat_min=12.0,
        natural_lat_max=21.0,
        natural_lng_min=68.0,
        natural_lng_max=75.0,
        monsoon_peak="Post-monsoon to winter — common in market landings.",
        monsoon_off="Mid-monsoon: availability patchy; often holds on cleaner shelf water.",
        prefers_rain=False,
        storm_tolerance="Moderate — holds slightly deeper in heavy weather.",
        hot_behavior="Above 28°C may shift to deeper shelf water.",
        cold_behavior="Below 21°C feeding activity declines.",
        tide_affinity="Moderate — often near soft-bottom edges and current changes.",
        night_activity="Low to moderate — more of a daytime/evening feeder.",
        surface_feed_behavior="Low to moderate — mid-water and bottom feeder.",
    ),
    SpeciesSchema(
        id=7,
        name="Tuna (Skipjack)",
        scientific_name="Katsuwonus pelamis",
        conservation_status="least_concern",
        legal_catch_status="regulated",
        thumbnail_hint="tuna",
        preferred_temperature_min_c=18.0,
        preferred_temperature_max_c=30.0,
        preferred_depth_min_m=10.0,
        preferred_depth_max_m=250.0,
        preferred_current_min_ms=0.3,
        preferred_current_max_ms=1.2,
        typical_habitat="Offshore / Pelagic",
        seasonal_behavior="Present offshore; movements tied to currents and temperature fronts.",
        current_sensitivity="High.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Regulated; offshore licenses may apply.",
        weight_kg_min=2.0,
        weight_kg_max=15.0,
        description="Offshore skipjack tuna. Observations here are especially useful for understanding current-driven habitat, though the nearshore focus of the MVP makes sightings less common.",
        natural_lat_min=10.0,
        natural_lat_max=22.0,
        natural_lng_min=65.0,
        natural_lng_max=78.0,
        monsoon_peak="Southwest monsoon: offshore current fronts and upwelling attract schools.",
        monsoon_off="Post-monsoon: still present offshore on current edges.",
        prefers_rain=False,
        storm_tolerance="High — pelagic and offshore; tolerates rough open water.",
        hot_behavior="Tolerates warm water; very hot surface layers can push them deeper.",
        cold_behavior="Active across a wide range; below 18°C feeding still possible but weaker.",
        tide_affinity="Weak — oceanic species; tide is not a strong driver offshore.",
        night_activity="High — strong night feeder and known to aggregate around light.",
        surface_feed_behavior="Strong — surface and subsurface strikes on bait balls.",
    ),
    SpeciesSchema(
        id=8,
        name="Octopus",
        scientific_name="Octopus spp.",
        conservation_status="data_deficient",
        legal_catch_status="regulated",
        thumbnail_hint="octopus",
        preferred_temperature_min_c=22.0,
        preferred_temperature_max_c=30.0,
        preferred_depth_min_m=5.0,
        preferred_depth_max_m=60.0,
        preferred_current_min_ms=0.05,
        preferred_current_max_ms=0.4,
        typical_habitat="Inshore / Rocky & sandy bottom",
        seasonal_behavior="Seasonal; tied to bottom-type and productivity.",
        current_sensitivity="Low.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Standard license applies; check local norms.",
        weight_kg_min=0.5,
        weight_kg_max=3.0,
        description="Benthic invertebrate predator. Presence is strongly habitat-driven (bottom type, depth, shelter), so location-specific observations are especially informative.",
        natural_lat_min=12.0,
        natural_lat_max=21.0,
        natural_lng_min=68.0,
        natural_lng_max=74.5,
        monsoon_peak="Post-monsoon to winter — active on structure and sheltered grounds.",
        monsoon_off="Mid-monsoon: may hold in sheltered rocky/crevice habitat.",
        prefers_rain=False,
        storm_tolerance="High in sheltered structure; avoids open-bay surge.",
        hot_behavior="Warm water suits activity; extreme heat can push them deeper into shade.",
        cold_behavior="Below 21°C activity tends to slow.",
        tide_affinity="Moderate — often forages on tide changes near structure.",
        night_activity="High — many octopus species are more active after dark.",
        surface_feed_behavior="Low — benthic predator; not a surface feeder.",
    ),
    SpeciesSchema(
        id=9,
        name="Sea Bass",
        scientific_name="Lates calcarifer",
        conservation_status="least_concern",
        legal_catch_status="regulated",
        thumbnail_hint="seabass",
        preferred_temperature_min_c=24.0,
        preferred_temperature_max_c=32.0,
        preferred_depth_min_m=2.0,
        preferred_depth_max_m=50.0,
        preferred_current_min_ms=0.05,
        preferred_current_max_ms=0.5,
        typical_habitat="Estuarine / Coastal",
        seasonal_behavior="Moves between estuary and coastal waters with season.",
        current_sensitivity="Low to moderate.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Standard license applies.",
        weight_kg_min=0.5,
        weight_kg_max=4.0,
        description="Indo-Pacific seabass, a valued estuarine species. Observations near river mouths and estuaries are particularly useful.",
        natural_lat_min=12.0,
        natural_lat_max=21.0,
        natural_lng_min=68.0,
        natural_lng_max=75.0,
        monsoon_peak="Pre-monsoon and post-monsoon — strong estuarine and nearshore feeding.",
        monsoon_off="Mid-monsoon: fish may move between estuaries and coastal holes with the rain and freshwater flow.",
        prefers_rain=True,
        storm_tolerance="Moderate — holds in sheltered estuary channels during heavy weather.",
        hot_behavior="Tolerates very warm water; thrives in hot estuarine conditions.",
        cold_behavior="Below 23°C feeding tends to slow.",
        tide_affinity="Strong — moves with tide into estuaries, creeks and coastal shallows.",
        night_activity="High — strong night and low-light feeder.",
        surface_feed_behavior="Moderate to strong — known to take surface lures in estuaries.",
    ),
    SpeciesSchema(
        id=10,
        name="Tiger Prawn",
        scientific_name="Penaeus monodon",
        conservation_status="least_concern",
        legal_catch_status="regulated",
        thumbnail_hint="tigerprawn",
        preferred_temperature_min_c=24.0,
        preferred_temperature_max_c=31.0,
        preferred_depth_min_m=5.0,
        preferred_depth_max_m=70.0,
        preferred_current_min_ms=0.05,
        preferred_current_max_ms=0.4,
        typical_habitat="Inshore / Estuarine / Muddy bottom",
        seasonal_behavior="Monsoon-influenced cycles; high-value commercial species.",
        current_sensitivity="Low.",
        known_regions=["maharashtra_coast"],
        regional_restriction="Permitted with license; observe seasonal norms.",
        weight_kg_min=0.02,
        weight_kg_max=0.15,
        description="Large penaeid prawn with strong monsoon-driven cycles. Key commercial species; observations help capture patchy, tide- and season-influenced habitat.",
        natural_lat_min=13.0,
        natural_lat_max=20.5,
        natural_lng_min=68.5,
        natural_lng_max=74.0,
        monsoon_peak="Southwest monsoon to post-monsoon — peak estuarine and mudflat productivity.",
        monsoon_off="Winter: still present in sheltered estuarine and mudflat grounds.",
        prefers_rain=True,
        storm_tolerance="High in sheltered water; avoids open-bay surge during storms.",
        hot_behavior="Warm water suits growth; extreme heat can push deeper in the water column in shallow bays.",
        cold_behavior="Below 23°C activity slows; estuary-fed grounds remain best.",
        tide_affinity="Strong — moving tides and tide changes concentrate prawns in channels and edges.",
        night_activity="High — many penaeid prawns are more active and move up at night.",
        surface_feed_behavior="Low — bottom and mid-water feeder.",
    ),
]


def species_by_id(species_id: int) -> SpeciesSchema | None:
    for s in SPECIES:
        if s.id == species_id:
            return s
    return None


def species_list() -> list[SpeciesSchema]:
    return list(SPECIES)


def species_env_behavior(species_id: int) -> dict[str, Any] | None:
    """Return the editorial env-behavior dataset for a species, for the .md and the
    species detail page. Returns None when the species id is unknown."""
    s = species_by_id(species_id)
    if s is None:
        return None
    return {
        "id": s.id,
        "name": s.name,
        "scientific_name": s.scientific_name,
        "natural_range_degrees": {
            "lat_min": s.natural_lat_min,
            "lat_max": s.natural_lat_max,
            "lng_min": s.natural_lng_min,
            "lng_max": s.natural_lng_max,
        },
        "monsoon_peak": s.monsoon_peak,
        "monsoon_off": s.monsoon_off,
        "prefers_rain": s.prefers_rain,
        "storm_tolerance": s.storm_tolerance,
        "hot_behavior": s.hot_behavior,
        "cold_behavior": s.cold_behavior,
        "tide_affinity": s.tide_affinity,
        "night_activity": s.night_activity,
        "surface_feed_behavior": s.surface_feed_behavior,
    }


# ---------------------------------------------------------------------------
# Transparent, expert-rule style habitat suitability helpers.
# These are intentionally editable from admin (they are the "model" for MVP v1).
# ---------------------------------------------------------------------------


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def triangular_center_half(min_val: float, max_val: float) -> tuple[float, float]:
    mid = (min_val + max_val) / 2.0
    half = (max_val - min_val) / 2.0
    return mid, half


def triangular_weight(value: float, mid: float, half: float) -> float:
    """1 at mid, linear decay to 0 at mid±half, 0 beyond."""
    dist = abs(value - mid)
    if dist <= half:
        return 1.0
    over = dist - half
    full_range = max((mid - half) - (mid - 2 * half), 0.0) + half  # == half + half
    # Simpler: define range as full width where value becomes 0 = 2*half.
    return max(0.0, 1.0 - over / max(2.0 * half, 1e-9))


def temperature_suitability(profile: SpeciesSchema, sst_c: float) -> float:
    mid, half = triangular_center_half(profile.preferred_temperature_min_c, profile.preferred_temperature_max_c)
    return triangular_weight(sst_c, mid, half)


def depth_suitability(profile: SpeciesSchema, depth_m: float) -> float:
    mid, half = triangular_center_half(profile.preferred_depth_min_m, profile.preferred_depth_max_m)
    return triangular_weight(depth_m, mid, half)


def current_suitability(profile: SpeciesSchema, velocity_ms: float) -> float:
    mid, half = triangular_center_half(profile.preferred_current_min_ms, profile.preferred_current_max_ms)
    return triangular_weight(velocity_ms, mid, half)


def wave_suitability(profile: SpeciesSchema, wave_height_m: float) -> float:
    # Heuristic: small-moderate waves fine; larger chop penalized.
    if wave_height_m <= 1.2:
        return 1.0
    if wave_height_m <= 2.5:
        return max(0.0, 1.0 - (wave_height_m - 1.2) / 1.3)
    return max(0.0, 1.0 - (wave_height_m - 1.2) / 2.0)


def seasonality_score(profile: SpeciesSchema, month: int) -> float:
    # Broad bell centered on productive months for west-coast small pelagics (approx. October).
    center = 10
    half = 4
    dist = abs(month - center)
    if dist <= half:
        return 1.0
    over = dist - half
    range_val = half * 2 + 2
    return max(0.0, 1.0 - over / range_val)


def historical_similarity(
    profile: SpeciesSchema,
    environment: dict[str, Any],
    presence_density: float,  # 0..1 proxy for nearby historical observations
) -> float:
    env = (
        temperature_suitability(profile, environment["sea_surface_temperature_c"])
        + depth_suitability(profile, environment.get("water_depth_m", 50.0))
        + current_suitability(profile, environment["current_velocity_ms"])
    ) / 3.0
    return clamp(env * 0.6 + presence_density * 0.4, 0.0, 1.0)


def seasonal_match_label(profile: SpeciesSchema, month: int, historical_match: str) -> str:
    s = seasonality_score(profile, month)
    if s >= 0.7:
        return "high"
    if s >= 0.4:
        return "moderate"
    if s >= 0.2:
        return "low"
    return "none"


def needs_protection(species: SpeciesSchema) -> bool:
    status = species.legal_catch_status.lower()
    return status in {"protected", "restricted"}


def is_observation_plausible(species: SpeciesSchema, lat: float, lng: float, region: RegionSchema) -> bool:
    # Very crude species-by-region sanity check for MVP.
    if region is None:
        return True
    b = region.bounds
    return b["south"] <= lat <= b["north"] and b["west"] <= lng <= b["east"]
