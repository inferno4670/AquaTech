import type {
  LoginResponse,
  MarineConditions,
  Observation,
  ObservationDraft,
  ObservationEnvelope,
  PredictionRun,
  PublicSightingsResponse,
  PointsSnapshot,
  RewardItem,
  RewardRedemptionOut,
  SpeciesCollection,
  SpeciesProfile,
} from './contracts';

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://127.0.0.1:8000';

let accessToken: string | null = null;

export function setToken(token: string | null) {
  accessToken = token;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((init.headers as Record<string, string>) ?? {}),
  };
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  const resp = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await resp.json()) as T;
}

// ---- health + catalog ----
export function getHealth() {
  return request<{ status: string; service: string }>('/health');
}

export function getSpeciesCollection() {
  return request<SpeciesCollection>('/api/species/all');
}

export function getSpeciesProfile(id: number) {
  return request<SpeciesProfile>(`/api/species/${id}`);
}

// ---- predictions ----
export interface PredictionRequestPayload {
  species_id: number;
  region_id: number;
  date: string; // YYYY-MM-DD
  time_hour?: number | null;
  search_radius_km?: number | null;
}

export interface PredictionApiResponse {
  prediction: PredictionRun;
  species_id: number;
  region_id: number;
  protected_species: boolean;
  requested_at: string;
}

export function createPrediction(payload: PredictionRequestPayload) {
  return request<PredictionApiResponse>('/api/predictions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ---- marine conditions (point probe) ----
export function getMarineConditions(lat: number, lng: number, forecastHours = 0) {
  const q = new URLSearchParams({
    latitude: String(lat),
    longitude: String(lng),
    forecast_hours: String(forecastHours),
  });
  return request<MarineConditions>(`/api/marine/conditions?${q.toString()}`);
}

// ---- observations ----
export function submitObservation(draft: ObservationDraft) {
  return request<ObservationEnvelope>('/api/observations', { method: 'POST', body: JSON.stringify(draft) });
}

export function listObservations(status?: 'pending' | 'validated' | 'flagged', limit = 50) {
  const q = status ? `?status=${status}&limit=${limit}` : `?limit=${limit}`;
  return request<Observation[]>(`/api/observations${q}`);
}

/** Validated sightings from all contributors — powers the map's fish symbols. */
export function getPublicSightings(speciesId?: number | null, limit = 200) {
  const q = new URLSearchParams({ limit: String(limit) });
  if (speciesId != null) q.set('species_id', String(speciesId));
  return request<PublicSightingsResponse>(`/api/observations/public?${q.toString()}`);
}

// ---- auth + user ----
export function register(email: string, password: string, displayName: string) {
  return request<LoginResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

export function login(email: string, password: string) {
  return request<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function getMe() {
  return request<LoginResponse['user']>('/api/users/me');
}

export function getPointsSnapshot() {
  return request<PointsSnapshot>('/api/users/me/points');
}

// ---- rewards ----
export function listRewards() {
  return request<{ rewards: RewardItem[] }>('/api/rewards');
}

export function redeemReward(rewardId: string) {
  return request<RewardRedemptionOut>(`/api/rewards/redeem?reward_id=${encodeURIComponent(rewardId)}`, {
    method: 'POST',
  });
}

// ---- admin ----
export interface AdminUserRow {
  id: string;
  email: string;
  display_name: string;
  role: string;
  reputation: number;
  points_balance: number;
  is_active: boolean;
  created_at: string;
}

export function adminListUsers() {
  return request<AdminUserRow[]>('/api/admin/users');
}

export function adminToggleUser(userId: string) {
  return request<{ ok: boolean; is_active: boolean }>(`/api/admin/users/${userId}/toggle_active`, { method: 'POST' });
}

export function adminListObservations(status?: string) {
  return request<Observation[]>(`/api/admin/observations${status ? `?status=${status}` : ''}`);
}

export function adminApproveObservation(observationId: string) {
  return request<{ ok: boolean }>(`/api/admin/observations/${observationId}/approve`, { method: 'POST' });
}

export function adminFlagObservation(observationId: string, reason: string) {
  return request<{ ok: boolean }>(
    `/api/admin/observations/${observationId}/flag?reason=${encodeURIComponent(reason)}`,
    { method: 'POST' },
  );
}

export function adminListSpecies() {
  return request<SpeciesProfile[]>('/api/admin/species');
}

export function adminUpdateSpecies(speciesId: number, body: SpeciesProfile) {
  return request<{ ok: boolean; species_id: number }>(`/api/admin/species/${speciesId}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export function adminDataSources() {
  return request<{ id: string; source: string; status: string; last_checked: string; detail: string | null }[]>(
    '/api/admin/data-sources',
  );
}
