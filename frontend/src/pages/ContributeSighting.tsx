import { useEffect, useMemo, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { SpeciesProfile, ObservationEnvelope, MarineRegion } from '../contracts';
import { getSpeciesCollection, submitObservation } from '../api';
import { useAuth } from '../store/auth';
import { cyberMarineStyle } from '../components/mapStyle';
import { PALETTE } from '../lib/palette';
import MarineConditionsPanel from '../components/MarineConditionsPanel';

export default function ContributeSighting() {
  const { user, refreshUser } = useAuth();
  const [speciesList, setSpeciesList] = useState<SpeciesProfile[]>([]);
  const [regions, setRegions] = useState<MarineRegion[]>([]);
  const [speciesId, setSpeciesId] = useState<number | null>(null);
  const [observedAt, setObservedAt] = useState(() => {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  });
  const [observationType, setObservationType] = useState<'caught' | 'observed'>('observed');
  const [quantityKg, setQuantityKg] = useState<string>('');
  const [notes, setNotes] = useState('');
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ObservationEnvelope | null>(null);

  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  useEffect(() => {
    getSpeciesCollection()
      .then(c => {
        setSpeciesList(c.profiles);
        setRegions(c.regions);
        if (c.profiles.length) setSpeciesId(c.profiles[0].id);
      })
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load species'));
  }, []);

  useEffect(() => {
    if (!mapDivRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: mapDivRef.current,
      style: cyberMarineStyle(),
      center: [72.5, 19.0],
      zoom: 6.2,
      attributionControl: false,
    });
    mapRef.current = map;
    map.on('click', e => {
      setLat(Number(e.lngLat.lat.toFixed(4)));
      setLng(Number(e.lngLat.lng.toFixed(4)));
    });
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || lat === null || lng === null) return;
    const pos: [number, number] = [lng, lat];
    if (!markerRef.current) {
      markerRef.current = new maplibregl.Marker({ color: PALETTE.goldBright }).setLngLat(pos).addTo(mapRef.current);
    } else {
      markerRef.current.setLngLat(pos);
    }
    mapRef.current.easeTo({ center: pos, zoom: Math.max(mapRef.current.getZoom(), 7.5), duration: 500 });
  }, [lat, lng]);

  const region = useMemo(() => regions[0] ?? null, [regions]);
  void region;

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation not available');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      p => {
        setLat(Number(p.coords.latitude.toFixed(4)));
        setLng(Number(p.coords.longitude.toFixed(4)));
      },
      () => setError('Location permission denied — click the map to pick a spot manually.'),
    );
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setError('Sign in first — sightings are linked to contributor accounts.');
      return;
    }
    if (speciesId == null || lat == null || lng == null) {
      setError('Pick a species and a location (click the map).');
      return;
    }
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const envelope = await submitObservation({
        species_id: speciesId,
        observed_at: new Date(observedAt).toISOString(),
        latitude: lat,
        longitude: lng,
        quantity_kg: quantityKg ? Number(quantityKg) : undefined,
        observation_type: observationType,
        notes: notes || undefined,
      });
      setResult(envelope);
      void refreshUser();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex h-full min-h-0">
      {/* Form column */}
      <aside className="aq-panel z-20 flex w-96 shrink-0 flex-col gap-3 overflow-y-auto p-4">
        <h1 className="aq-glow-text text-xs tracking-[0.3em] text-cyan-300">CONTRIBUTE SIGHTING // LEARNING DATA</h1>
        <p className="text-[10px] leading-relaxed text-slate-500">
          Your sighting is enriched with marine conditions at that place and time, then scored and stored as a
          learning record that improves future predictions.
        </p>

        {!user && (
          <div className="rounded border border-amber-500/40 bg-amber-500/10 p-2 text-[11px] text-amber-300">
            Sign in to contribute. Use the SIGN IN button in the top bar.
          </div>
        )}

        <form onSubmit={submit} className="flex flex-col gap-3">
          <label className="block">
            <span className="aq-label">Species</span>
            <select className="aq-select w-full" value={speciesId ?? ''} onChange={e => setSpeciesId(Number(e.target.value))}>
              {speciesList.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </label>

          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="aq-label">When</span>
              <input className="aq-input w-full" type="datetime-local" value={observedAt} onChange={e => setObservedAt(e.target.value)} />
            </label>
            <label className="block">
              <span className="aq-label">Type</span>
              <select className="aq-select w-full" value={observationType} onChange={e => setObservationType(e.target.value as 'caught' | 'observed')}>
                <option value="observed">observed</option>
                <option value="caught">caught</option>
              </select>
            </label>
          </div>

          <div className="grid grid-cols-2 items-end gap-2">
            <button type="button" onClick={useMyLocation} className="aq-btn py-1.5 text-[10px]">
              ◎ USE MY LOCATION
            </button>
            <div className="text-[10px] leading-tight text-slate-500">
              {lat == null ? 'No location picked — click map.' : `picked: ${lat}, ${lng}`}
            </div>
          </div>

          <label className="block">
            <span className="aq-label">Quantity (kg, optional)</span>
            <input className="aq-input w-full" type="number" min={0} step={0.1} value={quantityKg} onChange={e => setQuantityKg(e.target.value)} />
          </label>

          <label className="block">
            <span className="aq-label">Notes</span>
            <textarea className="aq-input h-20 w-full" value={notes} onChange={e => setNotes(e.target.value)} placeholder="school size, behaviour, gear…" />
          </label>

          <button type="submit" disabled={busy} className="aq-btn-primary py-2 text-xs">
            {busy ? 'ENRICHING…' : 'SUBMIT SIGHTING → LEARNING LOOP'}
          </button>
          {error && <p className="text-xs text-red-400">{error}</p>}
        </form>

        <p className="mt-auto text-[9px] leading-relaxed text-slate-600">
          Privacy: your sighting is displayed aggregated at grid level. Your exact coordinates are not shared
          publicly with other users by default.
        </p>
      </aside>

      {/* Map + result */}
      <div className="relative min-w-0 flex-1">
        <div ref={mapDivRef} className="h-full w-full" />
        <div className="aq-scanline" />

        {result && (
          <div className="aq-panel absolute bottom-4 left-4 right-4 z-20 rounded p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="aq-glow-text text-xs tracking-[0.25em] text-cyan-200">OBSERVATION ENRICHED ✓</h2>
              <button type="button" className="text-slate-500 hover:text-cyan-300" onClick={() => setResult(null)}>✕</button>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="aq-label mb-1">Learning record</p>
                <ul className="text-[11px] text-slate-300">
                  <li>status <span className={result.observation.status === 'validated' ? 'text-emerald-300' : 'text-amber-300'}>{result.observation.status}</span></li>
                  <li>quality score <span className="text-cyan-200">{result.observation.quality_score.toFixed(0)}%</span></li>
                  {result.observation.flagged_reason && <li className="text-red-400">flagged: {result.observation.flagged_reason}</li>}
                </ul>
              </div>
              <div>
                <p className="aq-label mb-1">Points awarded</p>
                <p className="text-2xl font-bold text-lime-300 aq-glow-text">+{result.points_awarded}</p>
              </div>
              <MarineConditionsPanel conditions={result.environment} title="ENRICHED ENVIRONMENT" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
