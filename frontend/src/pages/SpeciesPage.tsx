import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { SpeciesProfile } from '../contracts';
import { getSpeciesCollection } from '../api';
import { statusColorForSpecies } from '../lib/ui';

export default function SpeciesPage() {
  const [species, setSpecies] = useState<SpeciesProfile[]>([]);
  const [selected, setSelected] = useState<SpeciesProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSpeciesCollection()
      .then(c => {
        setSpecies(c.profiles);
        if (c.profiles.length) setSelected(c.profiles[0]);
      })
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load species'));
  }, []);

  if (error) return <div className="p-6 text-sm text-red-400">{error}</div>;

  return (
    <div className="flex h-full min-h-0">
      {/* List column */}
      <aside className="aq-panel z-20 w-72 shrink-0 overflow-y-auto p-3">
        <h1 className="aq-glow-text mb-2 px-1 text-xs tracking-[0.3em] text-cyan-300">SPECIES DATABASE // {species.length} TAXA</h1>
        <div className="flex flex-col gap-1">
          {species.map(s => {
            const guard = statusColorForSpecies(s.legal_catch_status, s.conservation_status);
            const active = selected?.id === s.id;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => setSelected(s)}
                className={`rounded px-2 py-1.5 text-left transition-colors ${
                  active ? 'bg-cyan-400/15 aq-neon-border' : 'hover:bg-cyan-400/8 border border-transparent'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[12px] text-cyan-100">{s.name}</span>
                  <span className="h-2 w-2 rounded-full" style={{ background: guard.color }} title={guard.label} />
                </div>
                <span className="text-[9px] italic text-slate-500">{s.scientific_name}</span>
              </button>
            );
          })}
        </div>
      </aside>

      {/* Detail card */}
      <section className="min-w-0 flex-1 overflow-y-auto p-6">
        {selected && (
          <article className="aq-panel mx-auto max-w-2xl rounded-lg p-6">
            <header className="mb-4">
              <h2 className="aq-glow-text text-xl text-cyan-200">{selected.name}</h2>
              <p className="text-xs italic text-slate-500">{selected.scientific_name}</p>
              <ConservationBanner species={selected} />
            </header>

            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-[12px]">
              <Range label="Temperature range" min={selected.preferred_temperature_min_c} max={selected.preferred_temperature_max_c} unit="°C" />
              <Range label="Depth range" min={selected.preferred_depth_min_m} max={selected.preferred_depth_max_m} unit="m" />
              <Range label="Current range" min={selected.preferred_current_min_ms} max={selected.preferred_current_max_ms} unit="m/s" />
              <Range label="Typical weight" min={selected.weight_kg_min ?? 0} max={selected.weight_kg_max ?? 0} unit="kg" />
            </div>

            <div className="mt-4 space-y-2 text-[12px]">
              <InfoRow label="Typical habitat" value={selected.typical_habitat} />
              <InfoRow label="Seasonal behaviour" value={selected.seasonal_behavior} />
              <InfoRow label="Current sensitivity" value={selected.current_sensitivity} />
              {selected.regional_restriction && <InfoRow label="Regional restriction" value={selected.regional_restriction} accent />}
              {selected.seasonal_restriction && <InfoRow label="Seasonal restriction" value={selected.seasonal_restriction} accent />}
              <InfoRow label="Natural range (deg)" value={`lat ${selected.natural_lat_min}–${selected.natural_lat_max}, lng ${selected.natural_lng_min}–${selected.natural_lng_max}`} />
              <InfoRow label="Monsoon peak" value={selected.monsoon_peak} accent />
              <InfoRow label="Monsoon off-season" value={selected.monsoon_off} />
              <InfoRow label="Prefers rain" value={selected.prefers_rain ? 'Yes' : 'No'} />
              <InfoRow label="Storm tolerance" value={selected.storm_tolerance} />
              <InfoRow label="When hot" value={selected.hot_behavior} />
              <InfoRow label="When cold" value={selected.cold_behavior} />
              <InfoRow label="Tide affinity" value={selected.tide_affinity} />
              <InfoRow label="Night activity" value={selected.night_activity} />
              <InfoRow label="Surface feeding" value={selected.surface_feed_behavior} />
            </div>

            <p className="mt-4 border-t border-cyan-500/20 pt-3 text-[12px] leading-relaxed text-slate-300">
              {selected.description}
            </p>

            <Link
              to="/find"
              state={{ speciesId: selected.id }}
              className="aq-btn-primary mt-4 inline-block px-4 py-2 text-[11px]"
            >
              PREDICT ZONES FOR THIS SPECIES →
            </Link>
          </article>
        )}
      </section>
    </div>
  );
}

function ConservationBanner({ species }: { species: SpeciesProfile }) {
  const guard = statusColorForSpecies(species.legal_catch_status, species.conservation_status);
  const sensitive = guard.label !== 'OPEN';
  if (!sensitive) return null;
  return (
    <div
      className="mt-2 rounded border p-2 text-[11px]"
      style={{ borderColor: `${guard.color}66`, background: `${guard.color}12` }}
    >
      <span className="font-bold tracking-widest" style={{ color: guard.color }}>⚠ {guard.label}</span>
      <span className="ml-2 text-slate-400">conservation status: {species.conservation_status.replace(/_/g, ' ')}</span>
    </div>
  );
}

function Range({ label, min, max, unit }: { label: string; min: number; max: number; unit: string }) {
  return (
    <div className="flex justify-between border-b border-cyan-500/10 py-1">
      <span className="text-slate-500">{label}</span>
      <span className="text-cyan-200">{min}–{max} {unit}</span>
    </div>
  );
}

function InfoRow({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p className="aq-label">{label}</p>
      <p className={accent ? 'text-amber-300' : 'text-slate-300'}>{value}</p>
    </div>
  );
}
