from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SpeciesShort(BaseModel):
    id: int
    name: str
    scientific_name: str
    conservation_status: str
    legal_catch_status: str
    thumbnail_hint: str | None = None


class SpeciesProfile(SpeciesShort):
    preferred_temperature_min_c: float
    preferred_temperature_max_c: float
    preferred_depth_min_m: float
    preferred_depth_max_m: float
    preferred_current_min_ms: float
    preferred_current_max_ms: float
    typical_habitat: str
    seasonal_behavior: str
    current_sensitivity: str
    known_regions: list[str]
    regional_restriction: str | None = None
    seasonal_restriction: str | None = None
    weight_kg_min: float | None = None
    weight_kg_max: float | None = None
    description: str
    # Natural range centroid + env-behavior dataset fields.
    # These are editorial content for the species database .md and the species detail
    # page; they do not yet drive the prediction model directly (MVP v1 uses the
    # numeric ranges above for that), but they are the source of truth for the
    # documented triggers in SPECIES_DATASET.md.
    natural_lat_min: float
    natural_lat_max: float
    natural_lng_min: float
    natural_lng_max: float
    monsoon_peak: str
    monsoon_off: str
    prefers_rain: bool
    storm_tolerance: str
    hot_behavior: str
    cold_behavior: str
    tide_affinity: str
    night_activity: str
    surface_feed_behavior: str


class MarineRegion(BaseModel):
    id: int
    name: str
    label: str
    centroid_lat: float
    centroid_lng: float
    default_search_radius_km: float
    bounds: dict[str, float]
    is_active: bool = True


class MarineConditions(BaseModel):
    lat: float
    lng: float
    timestamp: str
    sea_surface_temperature_c: float
    current_velocity_ms: float
    current_direction_deg: float
    wave_height_m: float
    wave_direction_deg: float
    wind_speed_kmh: float
    wind_direction_deg: float
    weather_code: int
    water_depth_m: float | None = None


class PredictionBasis(BaseModel):
    temperature: bool
    current: bool
    depth: bool
    seasonality: bool
    historical_sightings: bool
    wave: bool
    notes: str = ""


class PredictionZone(BaseModel):
    grid_id: str
    lat: float
    lng: float
    suitability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    sea_surface_temperature_c: float
    current_velocity_ms: float
    current_direction_deg: float
    wave_height_m: float
    water_depth_m: float
    distance_from_coast_km: float
    historical_match: str
    seasonal_match: str
    basis: PredictionBasis


class PredictionRunResponse(BaseModel):
    id: str
    species_id: int
    species_name: str
    region_id: int
    region_name: str
    prediction_date: str
    model_version: str
    generated_at: str
    data_freshness_sec: int
    observation_count: int
    zones: list[PredictionZone]


class ObservationDraft(BaseModel):
    species_id: int
    observed_at: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    quantity_kg: float | None = None
    observation_type: str = "observed"
    photo_url: str | None = None
    notes: str | None = None

    @field_validator("observation_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower()
        if v not in ("caught", "observed"):
            raise ValueError("observation_type must be 'caught' or 'observed'")
        return v


class ObservationOut(ObservationDraft):
    id: str
    created_by: str
    created_at: str
    status: str
    quality_score: float
    flagged_reason: str | None = None
    species_id: int
    species_name: str | None = None
    observation_type: str
    quantity_kg: float | None = None
    notes: str | None = None


class Observation(ObservationOut):
    pass


class ObservationShort(ObservationOut):
    id: str
    species_id: int
    status: str
    quality_score: float
    flagged_reason: str | None = None


class ObservationEnvelope(BaseModel):
    observation: Observation
    environment: MarineConditions
    points_awarded: int


class UserPublic(BaseModel):
    id: str
    display_name: str
    level: int
    reputation: int
    observations_count: int
    verified_count: int
    data_quality_percent: float
    # Drives the admin console nav entry; the server still authorises every
    # /api/admin route on its own.
    is_admin: bool = False


class PointTransaction(BaseModel):
    id: str
    delta: int
    balance_after: int
    reason: str
    created_at: str


class PointsSnapshot(BaseModel):
    balance: int
    level: int
    reputation: int
    transactions: list[PointTransaction]


class RewardItem(BaseModel):
    id: str
    title: str
    description: str
    value_label: str
    points_cost: int
    available: bool
    provider: str


class RewardRedemptionOut(BaseModel):
    id: str
    reward_id: str
    title: str
    status: str
    created_at: str
    completed_at: str | None = None


class SpeciesCollection(BaseModel):
    species: list[SpeciesShort]
    profiles: list[SpeciesProfile]
    regions: list[MarineRegion]


# Auth
class Credentials(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    display_name: str = Field(min_length=1, max_length=120)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictionRequest(BaseModel):
    species_id: int = Field(ge=1)
    region_id: int = Field(ge=1)
    date: str = Field(min_length=10, max_length=10)
    time_hour: int | None = Field(default=None, ge=0, le=23)
    search_radius_km: float | None = Field(default=None, ge=1, le=200)


class LoginResponse(BaseModel):
    user: UserPublic
    token: TokenOut
