import * as maplibregl from 'maplibre-gl';
// MapLibre resolves its web worker against `import.meta.url`, guessing the filename at
// runtime — something no bundler can follow. Left alone it breaks in BOTH modes, and it
// breaks *silently*: the style never loads, zero sources or layers appear, no tiles are
// requested, and the canvas just stays blank. Measured behaviour:
//
//   dev   - MapLibre resolves to node_modules/.vite/deps/maplibre-gl-worker.mjs, which
//           the optimizer never emits (it only writes maplibre-gl.js). Constructing a
//           Worker against that path raises "Worker failed to load".
//   build - the worker is emitted as a hashed asset, so the unhashed guess 404s.
//
// `?worker&url` is Vite's dedicated primitive for "give me a URL I can hand to
// `new Worker(...)`". It matters here: a plain `?url` import returns the raw file,
// which Vite then serves through its normal module pipeline — complete with an
// injected `import { injectQuery } from "/@vite/client"` HMR preamble. That preamble
// needs a DOM and a WebSocket, so inside a worker it breaks the module and MapLibre's
// worker silently never answers a single message (measured: no reply in 2500 ms, style
// never loads, zero tiles requested). `?worker&url` builds the file as a worker instead,
// emitting a real standalone asset in both dev and production.
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type { PredictionZone } from '../contracts';
import { PALETTE, SUITABILITY_RAMP } from '../lib/palette';

// Must run before any Map is constructed.
maplibregl.setWorkerUrl(maplibreWorkerUrl);

export const GRID_FILL_ID = 'aq-grid-fill';
export const GRID_OUTLINE_ID = 'aq-grid-outline';
export const GRID_SOURCE_ID = 'aq-zones';

export const SIGHTINGS_SOURCE_ID = 'aq-sightings';
export const SIGHTINGS_LAYER_ID = 'aq-sightings-fish';
export const HOTSPOT_SOURCE_ID = 'aq-hotspots';
export const HOTSPOT_GLOW_ID = 'aq-hotspot-glow';
export const HOTSPOT_LAYER_ID = 'aq-hotspot-fish';

const FISH_SIGHTING_ICON = 'aq-fish-sighting';
const FISH_HOTSPOT_ICON = 'aq-fish-hotspot';

const BASEMAP_TILES =
  'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
const BASEMAP_ATTRIBUTION =
  'Tiles &copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

/** Public sighting marker payload pushed onto the map as a fish symbol. */
export interface SightingPoint {
  id: string;
  species_id: number;
  species_name: string | null;
  observed_at: string;
  latitude: number;
  longitude: number;
  quality_score: number;
  status: string;
  notes?: string | null;
}

type Feature = {
  type: 'Feature';
  geometry:
    | { type: 'Polygon'; coordinates: number[][][] }
    | { type: 'LineString'; coordinates: number[][] }
    | { type: 'Point'; coordinates: number[] };
  properties?: Record<string, unknown>;
};

/** Warm graticule so the dark basemap keeps its "fishing chart" read. */
function graticuleFeatures(): Feature[] {
  const features: Feature[] = [];
  for (let lon = 60; lon <= 90; lon += 1) {
    features.push({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: [[lon, 5], [lon, 30]] },
    });
  }
  for (let lat = 5; lat <= 30; lat += 1) {
    features.push({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: [[60, lat], [90, lat]] },
    });
  }
  return features;
}

export function cyberMarineStyle(): maplibregl.StyleSpecification {
  return {
    version: 8,
    sources: {
      'aq-basemap': {
        type: 'raster',
        tiles: [BASEMAP_TILES],
        tileSize: 256,
        maxzoom: 19,
        attribution: BASEMAP_ATTRIBUTION,
      },
      'aq-graticule': {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: graticuleFeatures() },
      },
    },
    layers: [
      // Ground colour shows while raster tiles are still in flight.
      { id: 'ocean', type: 'background', paint: { 'background-color': PALETTE.inkDeep } },
      { id: 'basemap', type: 'raster', source: 'aq-basemap', paint: { 'raster-opacity': 1 } },
      {
        id: 'graticule',
        type: 'line',
        source: 'aq-graticule',
        paint: {
          'line-color': 'rgba(219,195,156,0.11)',
          'line-width': 0.6,
        },
      },
    ],
  };
}

/**
 * Draw a fish silhouette on a canvas and hand MapLibre the raw RGBA pixels.
 *
 * Drawn with canvas primitives rather than an SVG data URL on purpose: some browsers
 * refuse to rasterise SVG `<img>` sources into a canvas (or taint it), which would make
 * `addImage` fail silently and leave every symbol layer invisible.
 */
function drawFish(
  size: number,
  fill: string,
  stroke: string,
  eye = PALETTE.onLight,
): maplibregl.StyleImageInterface | null {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;

  // Design grid is 48x48; scale to the requested bitmap size.
  ctx.scale(size / 48, size / 48);
  ctx.lineJoin = 'round';
  ctx.lineWidth = 2;
  ctx.strokeStyle = stroke;
  ctx.fillStyle = fill;

  // Body, facing right.
  ctx.beginPath();
  ctx.ellipse(26, 24, 13, 8.5, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Tail fin.
  ctx.beginPath();
  ctx.moveTo(14, 24);
  ctx.lineTo(3, 12);
  ctx.lineTo(6.5, 24);
  ctx.lineTo(3, 36);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Dorsal fin.
  ctx.beginPath();
  ctx.moveTo(20, 17);
  ctx.lineTo(26, 8);
  ctx.lineTo(32, 16.5);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Eye.
  ctx.beginPath();
  ctx.arc(33, 21.5, 2.6, 0, Math.PI * 2);
  ctx.fillStyle = eye;
  ctx.fill();

  const data = ctx.getImageData(0, 0, size, size);
  return { width: size, height: size, data: new Uint8Array(data.data.buffer) };
}

/**
 * Register the fish bitmaps once. Rendered at 2x and declared with pixelRatio 2 so
 * they stay crisp on HiDPI displays.
 */
export function ensureFishIcons(map: maplibregl.Map): void {
  if (!map.hasImage(FISH_SIGHTING_ICON)) {
    const img = drawFish(96, PALETTE.pale, PALETTE.onLight);
    if (img) map.addImage(FISH_SIGHTING_ICON, img, { pixelRatio: 2 });
  }
  if (!map.hasImage(FISH_HOTSPOT_ICON)) {
    const img = drawFish(96, PALETTE.amber, PALETTE.onLight);
    if (img) map.addImage(FISH_HOTSPOT_ICON, img, { pixelRatio: 2 });
  }
}

/**
 * Id of the lowest fish layer currently on the map, or undefined when there is none.
 * Zone-grid layers are inserted *before* it so the heatmap never paints over the fish
 * symbols, and so clicking a fish still hits its symbol layer rather than a grid cell.
 */
function firstFishLayerId(map: maplibregl.Map): string | undefined {
  for (const id of [HOTSPOT_GLOW_ID, SIGHTINGS_LAYER_ID, HOTSPOT_LAYER_ID]) {
    if (map.getLayer(id)) return id;
  }
  return undefined;
}

/** Add/refresh predicted-zone grid fill+outline layers. */
export function applyZoneGrid(map: maplibregl.Map, zones: PredictionZone[], cellKm = 10) {
  if (zones.length === 0) return;
  const dLat = cellKm / 111.0 / 2;
  const dLng = cellKm / (111.0 * Math.cos((zones[0].lat * Math.PI) / 180)) / 2;

  const features: Feature[] = zones.map((z) => ({
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [z.lng - dLng, z.lat - dLat],
          [z.lng - dLng, z.lat + dLat],
          [z.lng + dLng, z.lat + dLat],
          [z.lng + dLng, z.lat - dLat],
          [z.lng - dLng, z.lat - dLat],
        ],
      ],
    },
    properties: {
      grid_id: z.grid_id,
      suitability: z.suitability,
      confidence: z.confidence,
      lat: z.lat,
      lng: z.lng,
    },
  }));

  const fillColor: maplibregl.ExpressionSpecification = [
    'interpolate', ['linear'], ['get', 'suitability'],
    0, SUITABILITY_RAMP.low,
    0.31, SUITABILITY_RAMP.moderate,
    0.61, SUITABILITY_RAMP.high,
    0.81, SUITABILITY_RAMP.very_high,
    1, SUITABILITY_RAMP.very_high,
  ];

  if (!map.getSource(GRID_SOURCE_ID)) {
    const beforeId = firstFishLayerId(map);
    map.addSource(GRID_SOURCE_ID, { type: 'geojson', data: { type: 'FeatureCollection', features } });
    map.addLayer({
      id: GRID_FILL_ID,
      type: 'fill',
      source: GRID_SOURCE_ID,
      paint: {
        'fill-color': fillColor,
        'fill-opacity': 0.34,
      },
    }, beforeId);
    map.addLayer({
      id: GRID_OUTLINE_ID,
      type: 'line',
      source: GRID_SOURCE_ID,
      paint: {
        'line-color': fillColor,
        'line-width': 0.8,
        'line-opacity': 0.6,
      },
    }, beforeId);
  } else {
    const src = map.getSource(GRID_SOURCE_ID);
    if (src) (src as maplibregl.GeoJSONSource).setData({ type: 'FeatureCollection', features });
  }
}

export function clearZoneGrid(map: maplibregl.Map) {
  for (const id of [GRID_FILL_ID, GRID_OUTLINE_ID]) {
    if (map.getLayer(id)) map.removeLayer(id);
  }
  if (map.getSource(GRID_SOURCE_ID)) map.removeSource(GRID_SOURCE_ID);
}

/**
 * Plot real community sightings as fish symbols at their recorded coordinates.
 * These are the only markers on the map that represent an actual fish observation.
 *
 * The marker colour is driven by the currently selected species so the map reads as
 * "reported sightings for this species" instead of one static blue cloud.
 */
export function applySightings(map: maplibregl.Map, sightings: SightingPoint[], markerColor = PALETTE.pale) {
  ensureFishIcons(map);

  const cachedIcon = `aq-fish-sighting-${markerColor.replace(/[^a-z0-9]/gi, '-')}`;

  // One icon per colour so we can tint the sighting markers by species without
  // rebuilding the whole palette each render. If the fresh colour already exists
  // (re-render with the same species), reuse it.
  if (!map.hasImage(cachedIcon)) {
    const img = drawFish(96, markerColor, PALETTE.onLight);
    if (img) map.addImage(cachedIcon, img, { pixelRatio: 2 });
  }

  const features: Feature[] = sightings.map((s) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [s.longitude, s.latitude] },
    properties: {
      id: s.id,
      species_id: s.species_id,
      species_name: s.species_name ?? 'Unknown species',
      observed_at: s.observed_at,
      latitude: s.latitude,
      longitude: s.longitude,
      quality_score: s.quality_score,
      status: s.status,
      notes: s.notes ?? '',
    },
  }));

  const data = { type: 'FeatureCollection' as const, features };

  if (!map.getSource(SIGHTINGS_SOURCE_ID)) {
    map.addSource(SIGHTINGS_SOURCE_ID, { type: 'geojson', data });
    map.addLayer({
      id: SIGHTINGS_LAYER_ID,
      type: 'symbol',
      source: SIGHTINGS_SOURCE_ID,
      layout: {
        'icon-image': cachedIcon,
        'icon-size': ['interpolate', ['linear'], ['zoom'], 4, 0.5, 8, 0.8, 12, 1.15],
        'icon-allow-overlap': true,
        'icon-ignore-placement': true,
        'icon-anchor': 'center',
      },
      paint: { 'icon-opacity': 0.95 },
    });
  } else {
    const src = map.getSource(SIGHTINGS_SOURCE_ID);
    if (src) (src as maplibregl.GeoJSONSource).setData(data);
  }
}

/**
 * Mark the strongest predicted cells with a larger amber fish so the answer to
 * "where should I look?" is readable at a glance. These are predictions, not sightings.
 */
export function applyHotspotFish(map: maplibregl.Map, zones: PredictionZone[], topN = 5) {
  if (zones.length === 0) return;
  ensureFishIcons(map);

  const best = [...zones]
    .sort((a, b) => b.suitability * b.confidence - a.suitability * a.confidence)
    .slice(0, topN);

  const features: Feature[] = best.map((z, i) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [z.lng, z.lat] },
    properties: {
      rank: i + 1,
      grid_id: z.grid_id,
      suitability: z.suitability,
      confidence: z.confidence,
    },
  }));

  const data = { type: 'FeatureCollection' as const, features };

  if (!map.getSource(HOTSPOT_SOURCE_ID)) {
    map.addSource(HOTSPOT_SOURCE_ID, { type: 'geojson', data });
    map.addLayer({
      id: HOTSPOT_GLOW_ID,
      type: 'circle',
      source: HOTSPOT_SOURCE_ID,
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 9, 9, 18],
        'circle-color': PALETTE.amber,
        'circle-opacity': 0.18,
        'circle-blur': 0.8,
      },
    });
    map.addLayer({
      id: HOTSPOT_LAYER_ID,
      type: 'symbol',
      source: HOTSPOT_SOURCE_ID,
      layout: {
        'icon-image': FISH_HOTSPOT_ICON,
        'icon-size': ['interpolate', ['linear'], ['zoom'], 4, 0.75, 8, 1.1, 12, 1.5],
        'icon-allow-overlap': true,
        'icon-ignore-placement': true,
      },
    });
  } else {
    const src = map.getSource(HOTSPOT_SOURCE_ID);
    if (src) (src as maplibregl.GeoJSONSource).setData(data);
  }
}

export function clearHotspots(map: maplibregl.Map) {
  for (const id of [HOTSPOT_LAYER_ID, HOTSPOT_GLOW_ID]) {
    if (map.getLayer(id)) map.removeLayer(id);
  }
  if (map.getSource(HOTSPOT_SOURCE_ID)) map.removeSource(HOTSPOT_SOURCE_ID);
}
