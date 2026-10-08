from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="fisherman")  # fisherman | admin
    reputation: Mapped[int] = mapped_column(Integer, default=0)
    points_balance: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )

    observations = relationship("Observation", back_populates="user", lazy="selectin")


class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    scientific_name: Mapped[str] = mapped_column(String(255), nullable=False)
    conservation_status: Mapped[str] = mapped_column(String(40), nullable=False)
    legal_catch_status: Mapped[str] = mapped_column(String(40), nullable=False)
    typical_habitat: Mapped[str] = mapped_column(String(255), nullable=False)
    seasonal_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    current_sensitivity: Mapped[str] = mapped_column(String(255), nullable=False)
    known_regions: Mapped[str] = mapped_column(String(1024), nullable=False, default="[]")
    regional_restriction: Mapped[str | None] = mapped_column(Text, nullable=True)
    seasonal_restriction: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_hint: Mapped[str | None] = mapped_column(String(60), nullable=True)
    weight_kg_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_temperature_min_c: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_temperature_max_c: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_depth_min_m: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_depth_max_m: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_current_min_ms: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_current_max_ms: Mapped[float] = mapped_column(Float, nullable=False)
    # Editorial env-behavior dataset fields (source of truth for SPECIES_DATASET.md).
    natural_lat_min: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    natural_lat_max: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    natural_lng_min: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    natural_lng_max: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    monsoon_peak: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    monsoon_off: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    prefers_rain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    storm_tolerance: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    hot_behavior: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    cold_behavior: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    tide_affinity: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    night_activity: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    surface_feed_behavior: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )

    habitat_profile = relationship("SpeciesHabitatProfile", back_populates="species", uselist=False, cascade="all, delete-orphan")
    conservation_status_row = relationship("ConservationStatus", back_populates="species", uselist=False, cascade="all, delete-orphan")
    legal_restrictions = relationship("LegalRestriction", back_populates="species", cascade="all, delete-orphan")


class SpeciesHabitatProfile(Base):
    __tablename__ = "species_habitat_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id", ondelete="cascade"), nullable=False)
    preferred_temperature_min_c: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_temperature_max_c: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_depth_min_m: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_depth_max_m: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_current_min_ms: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_current_max_ms: Mapped[float] = mapped_column(Float, nullable=False)
    typical_habitat: Mapped[str] = mapped_column(String(255), nullable=False)
    seasonal_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    current_sensitivity: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    species = relationship("Species", back_populates="habitat_profile")


class ConservationStatus(Base):
    __tablename__ = "conservation_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id", ondelete="cascade"), nullable=False)
    iucn_status: Mapped[str] = mapped_column(String(40), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    species = relationship("Species", back_populates="conservation_status_row")


class LegalRestriction(Base):
    __tablename__ = "legal_restrictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id", ondelete="cascade"), nullable=False)
    legal_catch_status: Mapped[str] = mapped_column(String(40), nullable=False)
    regional_restriction: Mapped[str | None] = mapped_column(Text, nullable=True)
    seasonal_restriction: Mapped[str | None] = mapped_column(Text, nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(80), nullable=False, default="maharashtra")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    species = relationship("Species", back_populates="legal_restrictions")


class MarineRegion(Base):
    __tablename__ = "marine_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lng: Mapped[float] = mapped_column(Float, nullable=False)
    default_search_radius_km: Mapped[float] = mapped_column(Float, nullable=False)
    bounds_north: Mapped[float] = mapped_column(Float, nullable=False)
    bounds_south: Mapped[float] = mapped_column(Float, nullable=False)
    bounds_east: Mapped[float] = mapped_column(Float, nullable=False)
    bounds_west: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    prediction_runs = relationship("PredictionRun", back_populates="region")


class PredictionRun(Base):
    __tablename__ = "prediction_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("marine_regions.id"), nullable=False)
    prediction_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    model_version: Mapped[str] = mapped_column(String(40), nullable=False, default="v1")
    status: Mapped[str] = mapped_column(String(20), default="ready")
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    data_freshness_sec: Mapped[int] = mapped_column(Integer, default=0)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    params_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    species = relationship("Species", back_populates=None)
    region = relationship("MarineRegion", back_populates="prediction_runs")
    cells = relationship("PredictionGridCell", back_populates="prediction_run", cascade="all, delete-orphan")


class PredictionGridCell(Base):
    __tablename__ = "prediction_grid_cells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prediction_runs.id", ondelete="cascade"), nullable=False)
    grid_id: Mapped[str] = mapped_column(String(60), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    suitability: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sea_surface_temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    current_velocity_ms: Mapped[float] = mapped_column(Float, nullable=False)
    current_direction_deg: Mapped[float] = mapped_column(Float, nullable=False)
    wave_height_m: Mapped[float] = mapped_column(Float, nullable=False)
    water_depth_m: Mapped[float] = mapped_column(Float, nullable=False)
    distance_from_coast_km: Mapped[float] = mapped_column(Float, nullable=False)
    historical_match: Mapped[str] = mapped_column(String(20), nullable=False)
    seasonal_match: Mapped[str] = mapped_column(String(20), nullable=False)
    basis_temperature: Mapped[bool] = mapped_column(Boolean, default=False)
    basis_current: Mapped[bool] = mapped_column(Boolean, default=False)
    basis_depth: Mapped[bool] = mapped_column(Boolean, default=False)
    basis_seasonality: Mapped[bool] = mapped_column(Boolean, default=False)
    basis_historical_sightings: Mapped[bool] = mapped_column(Boolean, default=False)
    basis_wave: Mapped[bool] = mapped_column(Boolean, default=False)
    basis_notes: Mapped[str] = mapped_column(Text, nullable=True)

    prediction_run = relationship("PredictionRun", back_populates="cells")


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # caught | observed
    quantity_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | validated | flagged
    flagged_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    species = relationship("Species", back_populates=None, lazy="selectin")
    user = relationship("User", back_populates="observations", lazy="selectin")
    environment = relationship("ObservationEnvironment", uselist=False, cascade="all, delete-orphan", back_populates="observation")


class ObservationEnvironment(Base):
    __tablename__ = "observation_environment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("observations.id", ondelete="cascade"), nullable=False)
    observation = relationship("Observation", back_populates="environment")
    sea_surface_temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    current_velocity_ms: Mapped[float] = mapped_column(Float, nullable=False)
    current_direction_deg: Mapped[float] = mapped_column(Float, nullable=False)
    wave_height_m: Mapped[float] = mapped_column(Float, nullable=False)
    wave_direction_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    wind_direction_deg: Mapped[float] = mapped_column(Float, nullable=False)
    weather_code: Mapped[int] = mapped_column(Integer, nullable=False)
    water_depth_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(60), nullable=False)  # open_meteo | historical_cache
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    delta: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    user = relationship("User", back_populates=None)


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    value_label: Mapped[str] = mapped_column(String(80), nullable=False)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)  # sandbox | funded
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    reward_id: Mapped[str] = mapped_column(ForeignKey("rewards.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | fulfilled | failed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates=None)
    reward = relationship("Reward", back_populates=None)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)  # rule_based | random_forest | xgboost | spatiotemporal
    species_count: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DataSourceStatus(Base):
    __tablename__ = "data_source_status"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    source: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # healthy | degraded | down
    last_checked: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
