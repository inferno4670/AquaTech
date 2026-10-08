import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import * as maplibregl from 'maplibre-gl';
import type { SpeciesProfile, MarineRegion, PredictionZone, PredictionRun, PublicSighting } from '../contracts';
import { createPrediction, getSpeciesCollection, getMarineConditions, getPublicSightings } from '../api';
import {
  applyZoneGrid,
  applySightings,
  applyHotspotFish,
  cyberMarineStyle,
  ensureFishIcons,
  GRID_FILL_ID,
  HOTSPOT_LAYER_ID,
  SIGHTINGS_LAYER_ID,
} from '../components/mapStyle';
import { bandColor, bandLabel, suitabilityBand, suitabilityColor } from '../components/suitability';
import { statusColorForSpecies } from '../lib/ui';
import MarineConditionsPanel from '../components/MarineConditionsPanel';

import { PALETTE } from '../lib/palette';

const MAHARASHTRA = { lat: 19.0, lng: 72.5, zoom: 6.4 };

export default function FindFish() {
  // A species page sends the reader here to predict zones for one fish. Read that intent
  // before choosing a default, or the first species in the catalogue always wins.
  const location = useLocation();
  const requestedSpeciesId = useMemo(() => {
    const raw = (location.state as { speciesId?: unknown } | null)?.speciesId;
    return typeof raw === 'number' && Number.isFinite(raw) ? raw : null;
  }, [location.state]);

  const [collection, setCollection] = useState<{ species: SpeciesProfile[]; regions: MarineRegion[] } | null>(null);
  const [speciesId, setSpeciesId] = useState<number | null>(requestedSpeciesId);
  const [regionId, setRegionId] = useState<number | null>(null);
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [hour, setHour] = useState(6);
  const [radius, setRadius] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [run, setRun] = useState<PredictionRun | null>(null);
  const [selectedZone, setSelectedZone] = useState<PredictionZone | null>(null);
  const [pointConditions, setPointConditions] = useState<Awaited<ReturnType<typeof getMarineConditions>> | null>(null);
  const [sightings, setSightings] = useState<PublicSighting[]>([]);
  const [mapReady, setMapReady] = useState(false);

  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);

  const species = useMemo(() => collection?.species.find(s => s.id === speciesId) ?? null, [collection, speciesId]);
  const region = useMemo(() => collection?.regions.find(r => r.id === regionId) ?? null, [collection, regionId]);

  // Stable colour for this species' sighting markers, so the live fish layer
  // reads as "this species' reported sightings" rather than one generic blue fish.
  const sightingMarkerColor = useMemo(() => {
    if (!species) return PALETTE.cyanSlate;
    return statusColorForSpecies(species.legal_catch_status, species.conservation_status).color;
  }, [species]);

  // Compute the next species id to fetch before we render the effects, so the
  // sightings effect can depend on a stable nominated id rather than re-fetching
  // on every render whenever species changes under us.
  const nominatedSpeciesId = useMemo(() => speciesId, [speciesId]);

  // Load catalog once
  useEffect(() => {
    getSpeciesCollection()
      .then(c => {
        setCollection({ species: c.profiles, regions: c.regions });
        // Keep the requested species when it is really in the catalogue; otherwise fall back
        // to the first one, so a stale link can never leave the select empty.
        const keepsRequest =
          requestedSpeciesId !== null && c.species.some(s => s.id === requestedSpeciesId);
        const wanted = keepsRequest ? requestedSpeciesId : (c.species[0]?.id ?? null);
        if (wanted !== null) setSpeciesId(wanted);
        if (c.regions.length > 0) setRegionId(c.regions[0].id);
      })
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load species'));
  }, [requestedSpeciesId]);

  // Community sightings for the map's fish layer.
  // Re-fetch filtered by species whenever the selected species changes, so the
  // map's fish markers actually reflect the species the user is looking at instead
  // of showing the same static cloud of every sighting every time.
  useEffect(() => {
    getPublicSightings(nominatedSpeciesId ?? null)
      .then(r => setSightings(r.sightings))
      .catch(() => setSightings([]));
  }, [nominatedSpeciesId]);

  // Init map
  useEffect(() => {
    if (!mapDivRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: mapDivRef.current,
      style: cyberMarineStyle(),
      center: [MAHARASHTRA.lng, MAHARASHTRA.lat],
      zoom: MAHARASHTRA.zoom,
      attributionControl: false,
    });
    mapRef.current = map;
    // Surface style/source/tile failures instead of leaving a silently blank canvas.
    map.on('error', (e) => {
      // MapLibre surfaces failures (bad style, unreachable tile source, dead worker) as
      // an `error` event; without this they are invisible and the map just stays blank.
      const err = (e as unknown as { error?: { message?: string } }).error;
      console.error('[AquaTrack map]', err?.message ?? String(e));
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    // The basemap raster tiles are OSM-derived; both the ODbL licence and CARTO's
    // terms require visible attribution.
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');

    map.on('load', () => {
      ensureFishIcons(map);
      setMapReady(true);
    });

    // One handler with explicit priority: fish symbols sit above the zone grid, so
    // they must be hit-tested first or a marker on top of a cell would select the cell.
    map.on('click', (e) => {
      const fishLayers = [SIGHTINGS_LAYER_ID, HOTSPOT_LAYER_ID].filter(id => map.getLayer(id));
      if (fishLayers.length > 0) {
        const fishHit = map.queryRenderedFeatures(e.point, { layers: fishLayers })[0];
        if (fishHit) {
          const props = (fishHit.properties ?? {}) as Record<string, unknown>;
          if (fishHit.layer.id === SIGHTINGS_LAYER_ID) {
            const geom = fishHit.geometry as { type: string; coordinates?: number[] };
            const coords = geom?.coordinates ?? [Number(props.longitude), Number(props.latitude)];
            popupRef.current?.remove();
            popupRef.current = new maplibregl.Popup({ closeButton: true, maxWidth: '270px' })
              .setLngLat([coords[0], coords[1]])
              .setHTML(sightingPopupHtml(props))
              .addTo(map);
          } else {
            // Hotspot fish marker: resolve it back to the full zone record.
            const gridId = props.grid_id;
            const z = runRef.current?.zones.find(x => x.grid_id === gridId);
            if (z) setSelectedZone(z);
          }
          return;
        }
      }

      if (!map.getLayer(GRID_FILL_ID)) return;
      const gridHit = map.queryRenderedFeatures(e.point, { layers: [GRID_FILL_ID] })[0];
      if (!gridHit) return;
      const gridId = (gridHit.properties as Record<string, unknown> | undefined)?.grid_id;
      if (typeof gridId !== 'string') return;
      const z = runRef.current?.zones.find(x => x.grid_id === gridId);
      if (z) setSelectedZone(z);
    });

    map.on('mousemove', (e) => {
      const fishLayers = [SIGHTINGS_LAYER_ID, HOTSPOT_LAYER_ID].filter(id => map.getLayer(id));
      const overFish = fishLayers.length > 0 && map.queryRenderedFeatures(e.point, { layers: fishLayers }).length > 0;
      const overGrid = !overFish && map.getLayer(GRID_FILL_ID) !== undefined
        && map.queryRenderedFeatures(e.point, { layers: [GRID_FILL_ID] }).length > 0;
      map.getCanvas().style.cursor = overFish ? 'pointer' : overGrid ? 'crosshair' : '';
    });

    return () => {
      popupRef.current?.remove();
      popupRef.current = null;
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Push community sightings onto the map as fish symbols once the style is ready.
  // The marker colour follows the currently selected species so the live fish layer
  // reads as "reported sightings for this species" instead of one static blue cloud.
  useEffect(() => {
    if (!mapReady || !mapRef.current) return;
    applySightings(mapRef.current, sightings, sightingMarkerColor);
  }, [mapReady, sightingMarkerColor, sightings]);

  const runRef = useRef<PredictionRun | null>(null);
  useEffect(() => {
    runRef.current = run;
  }, [run]);

  // Push zones onto map after each run
  useEffect(() => {
    if (!run || !mapRef.current) return;
    const map = mapRef.current;
    // Fit to zones
    const lngs = run.zones.map(z => z.lng);
    const lats = run.zones.map(z => z.lat);
    if (lngs.length && lats.length) {
      map.fitBounds(
        [
          [Math.min(...lngs), Math.min(...lats)],
          [Math.max(...lngs), Math.max(...lats)],
        ],
        { padding: 40, maxZoom: 9, duration: 800 },
      );
    }
    applyZoneGrid(map, run.zones);
    applyHotspotFish(map, run.zones);
  }, [run]);

  // Probe marine conditions at region centroid for sidebar (independent of run)
  useEffect(() => {
    if (!region) return;
    getMarineConditions(region.centroid_lat, region.centroid_lng)
      .then(setPointConditions)
      .catch(() => setPointConditions(null));
  }, [region]);

  const analyze = useCallback(async () => {
    if (!speciesId || !regionId) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await createPrediction({
        species_id: speciesId,
        region_id: regionId,
        date,
        time_hour: hour,
        search_radius_km: radius,
      });
      setRun(resp.prediction);
      void resp.protected_species;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  }, [speciesId, regionId, date, hour, radius]);

  const speciesGuard = species ? statusColorForSpecies(species.legal_catch_status, species.conservation_status) : null;

  return (
    <div className="flex h-full min-h-0">
      {/* Left control bar */}
      <aside className="aq-panel z-20 flex w-72 shrink-0 flex-col gap-3 overflow-y-auto p-4">
        <h1 className="aq-glow-text text-xs tracking-[0.3em] text-cyan-300">MARINE INTELLIGENCE // FIND FISH</h1>

        <label className="block">
          <span className="aq-label">Species</span>
          <select className="aq-select w-full" value={speciesId ?? ''} onChange={e => setSpeciesId(Number(e.target.value))}>
            {collection?.species.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="aq-label">Region</span>
          <select className="aq-select w-full" value={regionId ?? ''} onChange={e => setRegionId(Number(e.target.value))}>
            {collection?.regions.map(r => (
              <option key={r.id} value={r.id}>{r.label}</option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-2">
          <label className="block">
            <span className="aq-label">Date</span>
            <input className="aq-input w-full" type="date" value={date} onChange={e => setDate(e.target.value)} />
          </label>
          <label className="block">
            <span className="aq-label">Time (h)</span>
            <input className="aq-input w-full" type="number" min={0} max={23} value={hour} onChange={e => setHour(Number(e.target.value))} />
          </label>
        </div>

        <label className="block">
          <span className="aq-label">Search radius: {radius} km</span>
          <input type="range" min={10} max={150} step={5} value={radius} onChange={e => setRadius(Number(e.target.value))} className="w-full accent-cyan-400" />
        </label>

        <button onClick={analyze} disabled={loading || !speciesId || loading} className="aq-btn-primary py-2 text-xs">
          {loading ? 'ANALYZING…' : '⚡ ANALYZE'}
        </button>

        {error && <p className="text-xs text-red-400">{error}</p>}

        {/* Species conservation guard */}
        {species && speciesGuard && (
          <div className="rounded p-2 text-[11px]" style={{ border: `1px solid ${speciesGuard.color}55`, background: `${speciesGuard.color}11` }}>
            <span style={{ color: speciesGuard.color }}>{speciesGuard.label}</span>
            {species.regional_restriction && <p className="mt-1 text-slate-400">{species.regional_restriction}</p>}
          </div>
        )}

        {/* Live marine snapshot at region centroid */}
        <MarineConditionsPanel conditions={pointConditions} title="REGION CONDITIONS" />

        {/* Run summary */}
        {run && (
          <div className="text-[11px] text-slate-400">
            <div className="flex justify-between"><span>Model</span><span className="text-cyan-300">{run.model_version}</span></div>
            <div className="flex justify-between"><span>Data updated</span><span className="text-cyan-300">{freshnessLabel(run.data_freshness_sec)}</span></div>
            <div className="flex justify-between"><span>Zones</span><span className="text-cyan-300">{run.zones.length}</span></div>
            <div className="flex justify-between"><span>Historical samples</span><span className="text-cyan-300">{run.observation_count}</span></div>
          </div>
        )}

        {/* Legend */}
        <div className="mt-auto grid grid-cols-4 gap-1 text-[9px] tracking-wider">
          {(['very_high', 'high', 'moderate', 'low'] as const).map(b => (
            <div key={b} className="flex items-center gap-1">
              <span className="inline-block h-2 w-2" style={{ background: legendColor(b) }} />
              <span className="text-slate-400">{bandLabel(b).toUpperCase()}</span>
            </div>
          ))}
        </div>
      </aside>

      {/* Map */}
      <div className="relative min-w-0 flex-1">
        <div ref={mapDivRef} className="h-full w-full" />
        <div className="aq-scanline" />
        {run && !selectedZone && (
          <div className="aq-panel pointer-events-none absolute left-4 top-4 rounded p-2 text-[10px] tracking-widest text-cyan-300">
            {run.species_name.toUpperCase()} · {run.region_name.toUpperCase()} · CLICK A CELL FOR DETAILS
          </div>
        )}
      </div>

      {/* Zone inspector */}
      {selectedZone && (
        <ZoneInspector
          zone={selectedZone}
          onClose={() => setSelectedZone(null)}
        />
      )}
    </div>
  );
}

function legendColor(b: 'very_high' | 'high' | 'moderate' | 'low'): string {
  return bandColor(b);
}

function freshnessLabel(seconds: number): string {
  if (seconds < 60) return '<1m ago';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

function ZoneInspector({ zone, onClose }: { zone: PredictionZone; onClose: () => void }) {
  const band = suitabilityBand(zone.suitability);
  const confBand = suitabilityBand(zone.confidence);
  return (
    <aside className="aq-panel z-20 flex w-80 shrink-0 flex-col gap-2 overflow-y-auto p-4">
      <div className="flex items-start justify-between">
        <h2 className="aq-glow-text text-xs tracking-[0.25em] text-cyan-200">PREDICTED ZONE</h2>
        <button type="button" onClick={onClose} className="text-slate-500 hover:text-cyan-300">✕</button>
      </div>
      <p className="text-[10px] text-slate-500">{zone.grid_id} · {zone.lat.toFixed(3)}, {zone.lng.toFixed(3)}</p>

      <div className="grid grid-cols-2 gap-2">
        <SuitBox label="Suitability" value={zone.suitability} sub={bandLabel(band)} />
        <SuitBox label="Confidence" value={zone.confidence} sub={bandLabel(confBand)} />
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
        <Row label="SST" value={`${zone.sea_surface_temperature_c}°C`} />
        <Row label="Current" value={`${zone.current_velocity_ms} m/s`} />
        <Row label="Wave" value={`${zone.wave_height_m} m`} />
        <Row label="Depth" value={`${zone.water_depth_m} m`} />
        <Row label="From coast" value={`${zone.distance_from_coast_km} km`} />
        <Row label="Hist. match" value={zone.historical_match.toUpperCase()} />
        <Row label="Season" value={zone.seasonal_match.toUpperCase()} />
      </div>

      <div className="border-t border-cyan-500/20 pt-2">
        <p className="aq-label mb-1">Prediction basis</p>
        <ul className="space-y-0.5 text-[11px]">
          {(['temperature', 'current', 'depth', 'seasonality', 'historical_sightings', 'wave'] as const).map(k => (
            <li key={k} className={zone.basis[k as keyof typeof zone.basis] ? 'text-emerald-300' : 'text-slate-500'}>
              {zone.basis[k as keyof typeof zone.basis] ? '✓' : '○'} {prettyKey(k)}
            </li>
          ))}
        </ul>
      </div>

      <p className="text-[10px] leading-relaxed text-slate-400">{zone.basis.notes}</p>
      <p className="text-[9px] text-slate-600">Suitability describes conditions; confidence describes data support — they can differ.</p>
    </aside>
  );
}

function SuitBox({ label, value, sub }: { label: string; value: number; sub: string }) {
  const color = suitabilityColor(value);
  return (
    <div className="rounded aq-neon-border p-2 text-center">
      <p className="aq-label">{label}</p>
      <p className="text-xl font-bold aq-glow-text" style={{ color }}>{Math.round(value * 100)}%</p>
      <p className="text-[9px] text-slate-500">{sub.toUpperCase()}</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className="text-cyan-200">{value}</span>
    </div>
  );
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Popup for a fish marker. `notes` is contributor-supplied free text, so it is
 * escaped before it reaches `setHTML`.
 */
function sightingPopupHtml(props: Record<string, unknown>): string {
  const name = escapeHtml(String(props.species_name ?? 'Unknown species'));
  const status = escapeHtml(String(props.status ?? 'validated'));
  const observed = escapeHtml(String(props.observed_at ?? '').slice(0, 10) || 'unknown date');
  // quality_score is already on a 0-100 scale (see compute_quality_score); scaling it
  // again would render 75 as "7500%".
  const quality = typeof props.quality_score === 'number' ? Math.round(props.quality_score) : null;
  const lat = Number(props.latitude);
  const lng = Number(props.longitude);
  const notes = String(props.notes ?? '').trim();
  const isSample = notes.toUpperCase().startsWith('SAMPLE DATA');
  return `
    <div class="aq-popup">
      <p class="aq-popup-title">${name}</p>
      ${isSample ? '<p class="aq-popup-sample">SAMPLE DATA — not a real report</p>' : ''}
      <p class="aq-popup-row">Observed<span>${observed}</span></p>
      <p class="aq-popup-row">Record<span>${status}</span></p>
      ${quality != null ? `<p class="aq-popup-row">Quality<span>${quality}%</span></p>` : ''}
      <p class="aq-popup-row">Position<span>${lat.toFixed(3)}, ${lng.toFixed(3)}</span></p>
    </div>`;
}

const BASIS_LABELS: Record<string, string> = {
  temperature: 'Temperature',
  current: 'Current',
  depth: 'Depth',
  seasonality: 'Seasonality',
  historical_sightings: 'Historical sightings',
  wave: 'Wave',
};

function prettyKey(k: string): string {
  return BASIS_LABELS[k] ?? k;
}
