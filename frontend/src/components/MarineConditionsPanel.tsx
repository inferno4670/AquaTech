import type { MarineConditions } from '../contracts';

export default function MarineConditionsPanel({
  conditions,
  title = 'LIVE CONDITIONS',
}: {
  conditions: MarineConditions | null;
  title?: string;
}) {
  if (!conditions) {
    return (
      <div className="text-[10px] text-slate-500">{title} · acquiring…</div>
    );
  }
  return (
    <div className="aq-neon-border rounded p-2">
      <p className="aq-label mb-1">{title}</p>
      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px]">
        <Row label="SST" value={`${conditions.sea_surface_temperature_c.toFixed(1)}°C`} />
        <Row label="Current" value={`${conditions.current_velocity_ms.toFixed(2)} m/s`} />
        <Row label="Wave" value={`${conditions.wave_height_m.toFixed(1)} m`} />
        <Row label="Wind" value={`${conditions.wind_speed_kmh.toFixed(0)} km/h`} />
      </div>
      <p className="mt-1 text-[8px] text-slate-600">
        src: open-meteo marine · {new Date(conditions.timestamp).toLocaleTimeString()}
      </p>
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
