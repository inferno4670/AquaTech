// Shared type contracts between frontend and backend (MVP).
// Kept in sync manually for the MVP; in a larger project these would live in a shared package.

export interface SpeciesShort {
  id: number;
  name: string;
  scientific_name: string;
  conservation_status: ConservationStatus;
  legal_catch_status: LegalCatchStatus;
  thumbnail_hint?: string;
}

export type ConservationStatus =
  | "least_concern"
  | "near_threatened"
  | "vulnerable"
  | "endangered"
  | "critically_endangered"
  | "data_deficient"
  | "not_evaluated";

export type LegalCatchStatus =
  | "unrestricted"
  | "regulated"
  | "restricted"
  | "protected"
  | "unknown";

export interface SpeciesProfile extends SpeciesShort {
  preferred_temperature_min_c: number;
  preferred_temperature_max_c: number;
  preferred_depth_min_m: number;
  preferred_depth_max_m: number;
  preferred_current_min_ms: number;
  preferred_current_max_ms: number;
  typical_habitat: string;
  seasonal_behavior: string;
  current_sensitivity: string;
  known_regions: string[];
  regional_restriction?: string;
  seasonal_restriction?: string;
  weight_kg_min?: number;
  weight_kg_max?: number;
  description: string;
  natural_lat_min: number;
  natural_lat_max: number;
  natural_lng_min: number;
  natural_lng_max: number;
  monsoon_peak: string;
  monsoon_off: string;
  prefers_rain: boolean;
  storm_tolerance: string;
  hot_behavior: string;
  cold_behavior: string;
  tide_affinity: string;
  night_activity: string;
  surface_feed_behavior: string;
}

export interface MarineRegion {
  id: number;
  name: string;
  label: string;
  bounds: GeoBounds;
  centroid_lat: number;
  centroid_lng: number;
  default_search_radius_km: number;
}

export interface GeoBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface MarineConditions {
  lat: number;
  lng: number;
  timestamp: string;
  sea_surface_temperature_c: number;
  current_velocity_ms: number;
  current_direction_deg: number;
  wave_height_m: number;
  wave_direction_deg: number;
  wind_speed_kmh: number;
  wind_direction_deg: number;
  weather_code: number;
  water_depth_m?: number;
}

export interface PredictionZone {
  grid_id: string;
  lat: number;
  lng: number;
  suitability: number;     // 0..1
  confidence: number;      // 0..1
  sea_surface_temperature_c: number;
  current_velocity_ms: number;
  current_direction_deg: number;
  wave_height_m: number;
  water_depth_m: number;
  distance_from_coast_km: number;
  historical_match: "high" | "moderate" | "low" | "none";
  seasonal_match: "high" | "moderate" | "low" | "none";
  basis: PredictionBasis;
}

export interface PredictionBasis {
  temperature: boolean;
  current: boolean;
  depth: boolean;
  seasonality: boolean;
  historical_sightings: boolean;
  wave: boolean;
  notes: string;
}

export interface PredictionRun {
  id: string;
  species_id: number;
  species_name: string;
  region_id: number;
  region_name: string;
  prediction_date: string;
  model_version: string;
  generated_at: string;
  data_freshness_sec: number;
  observation_count: number;
  zones: PredictionZone[];
}

export interface ObservationDraft {
  species_id: number;
  observed_at: string;       // ISO datetime
  latitude: number;
  longitude: number;
  quantity_kg?: number;
  observation_type: "caught" | "observed";
  photo_url?: string;
  notes?: string;
}

export interface Observation extends ObservationDraft {
  id: string;
  created_by: string;
  created_at: string;
  status: ObservationStatus;
  quality_score: number;
  flagged_reason?: string;
}

export type ObservationStatus = "pending" | "validated" | "flagged";

export interface ObservationEnvelope {
  observation: Observation;
  environment: MarineConditions;
  points_awarded: number;
}

/** A validated sighting from any contributor, as plotted on the shared map. */
export interface PublicSighting {
  id: string;
  species_id: number;
  species_name: string | null;
  observed_at: string;
  latitude: number;
  longitude: number;
  observation_type: "caught" | "observed";
  quantity_kg: number | null;
  quality_score: number;
  status: ObservationStatus;
  notes: string | null;
  // Colour hint for the map marker: the species' status colour, or a neutral
  // cyan when the frontend has not yet loaded the species profile.
  marker_color?: string;
}

export interface PublicSightingsResponse {
  count: number;
  sightings: PublicSighting[];
}

export interface UserPublic {
  id: string;
  display_name: string;
  level: number;
  reputation: number;
  observations_count: number;
  verified_count: number;
  data_quality_percent: number;
  is_admin: boolean;
}

export interface PointsSnapshot {
  balance: number;
  level: number;
  reputation: number;
  transactions: PointTransaction[];
}

export interface PointTransaction {
  id: string;
  delta: number;
  balance_after: number;
  reason: string;
  created_at: string;
}

export interface RewardItem {
  id: string;
  title: string;
  description: string;
  value_label: string;   // e.g. "₹100 Voucher"
  points_cost: number;
  available: boolean;
  provider: "sandbox" | "funded";
}

export interface RewardRedemptionOut {
  id: string;
  reward_id: string;
  title: string;
  status: string;
  created_at: string;
  completed_at?: string | null;
}

export interface LoginResponse {
  user: UserPublic;
  token: TokenOut;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
}

export interface SpeciesCollection {
  species: SpeciesShort[];
  profiles: SpeciesProfile[];
  regions: MarineRegion[];
}
