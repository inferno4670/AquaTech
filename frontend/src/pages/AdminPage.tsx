import { useCallback, useEffect, useState } from 'react';
import type { Observation } from '../contracts';
import {
  adminApproveObservation,
  adminDataSources,
  adminFlagObservation,
  adminListObservations,
  adminListUsers,
  adminToggleUser,
  type AdminUserRow,
} from '../api';
import { useAuth } from '../store/auth';

type ObsRow = Observation & { created_by: string };

export default function AdminPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<'observations' | 'users' | 'sources'>('observations');
  const [observations, setObservations] = useState<ObsRow[]>([]);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [sources, setSources] = useState<{ id: string; source: string; status: string; last_checked: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const isAdmin = user?.is_admin === true;

  const loadAll = useCallback(async () => {
    setError(null);
    try {
      const [obs, us, src] = await Promise.all([
        adminListObservations(),
        adminListUsers(),
        adminDataSources(),
      ]);
      setObservations(obs as ObsRow[]);
      setUsers(us);
      setSources(src);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load admin data');
    }
  }, []);

  useEffect(() => {
    if (user) void loadAll();
  }, [user, loadAll]);

  if (!user) {
    return <CenterNote text="SIGN IN WITH AN ADMIN ACCOUNT TO VIEW THE CONSOLE" />;
  }

  return (
    <div className="flex h-full min-h-0">
      <aside className="aq-panel z-20 flex w-56 shrink-0 flex-col gap-2 p-4">
        <h1 className="aq-glow-text text-xs tracking-[0.3em] text-cyan-300">ADMIN CONSOLE</h1>
        {(['observations', 'users', 'sources'] as const).map(t => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1.5 text-left text-[11px] tracking-widest ${
              tab === t ? 'bg-cyan-400/15 aq-neon-border text-cyan-200' : 'text-slate-400 hover:text-cyan-300'
            }`}
          >
            {t.toUpperCase()}
          </button>
        ))}
        {error && <p className="mt-2 text-[10px] text-red-400">{error}</p>}
        <p className="mt-auto text-[9px] text-slate-600">
          {isAdmin ? 'Admin session ✓' : 'Your account is not an admin — API calls will fail with 403.'}
        </p>
      </aside>

      <section className="min-w-0 flex-1 overflow-y-auto p-4">
        {tab === 'observations' && <ObservationModeration rows={observations} onChanged={loadAll} />}
        {tab === 'users' && <UsersPanel rows={users} onChanged={loadAll} />}
        {tab === 'sources' && <SourcesPanel rows={sources} />}
      </section>
    </div>
  );
}

function ObservationModeration({ rows, onChanged }: { rows: ObsRow[]; onChanged: () => void }) {
  const [flagReason, setFlagReason] = useState('');

  const act = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      onChanged();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Action failed');
    }
  };

  if (rows.length === 0) return <CenterNote text="NO OBSERVATIONS YET — SUBMIT SOME VIA THE CONTRIBUTE PAGE" />;

  return (
    <div className="space-y-2">
      <div className="mb-3 flex items-center gap-2">
        <input className="aq-input w-72 text-[11px]" placeholder="flag reason…" value={flagReason} onChange={e => setFlagReason(e.target.value)} />
        <span className="text-[9px] text-slate-600">applies when FLAG is clicked</span>
      </div>
      {rows.map(o => (
        <div key={o.id} className="aq-panel rounded p-3 text-[11px]">
          <div className="flex items-center justify-between">
            <span className="text-cyan-100">
              #{o.id.slice(0, 8)} · species {o.species_id} · {o.observation_type}
            </span>
            <span
              className={
                o.status === 'validated' ? 'text-emerald-300' : o.status === 'flagged' ? 'text-red-400' : 'text-amber-300'
              }
            >
              {o.status.toUpperCase()}
            </span>
          </div>
          <div className="mt-1 grid grid-cols-4 gap-2 text-slate-400">
            <span>at {o.latitude.toFixed(2)}, {o.longitude.toFixed(2)}</span>
            <span>{new Date(o.observed_at).toLocaleString()}</span>
            <span>quality {o.quality_score.toFixed(0)}%</span>
            <span>by {o.created_by.slice(0, 8)}</span>
          </div>
          {o.flagged_reason && <p className="mt-1 text-red-400">reason: {o.flagged_reason}</p>}
          <div className="mt-2 flex gap-2">
            <button type="button" className="aq-btn px-2 py-1 text-[9px]" onClick={() => act(() => adminApproveObservation(o.id))}>
              ✓ APPROVE
            </button>
            <button
              type="button"
              className="aq-btn px-2 py-1 text-[9px]"
              disabled={flagReason.length === 0}
              onClick={() => act(() => adminFlagObservation(o.id, flagReason))}
            >
              ⚑ FLAG
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function UsersPanel({ rows, onChanged }: { rows: AdminUserRow[]; onChanged: () => void }) {
  return (
    <div className="aq-panel rounded p-3">
      <table className="w-full text-[11px]">
        <thead>
          <tr className="text-left text-slate-500">
            <th className="pb-2">EMAIL</th><th>ROLE</th><th>REPUTATION</th><th>POINTS</th><th>ACTIVE</th><th />
          </tr>
        </thead>
        <tbody>
          {rows.map(u => (
            <tr key={u.id} className="border-t border-cyan-500/10">
              <td className="py-1 text-cyan-100">{u.email}</td>
              <td>{u.role}</td>
              <td>{u.reputation}</td>
              <td>{u.points_balance}</td>
              <td className={u.is_active ? 'text-emerald-300' : 'text-red-400'}>{String(u.is_active)}</td>
              <td className="text-right">
                <button
                  type="button"
                  className="aq-btn px-2 py-0.5 text-[9px]"
                  onClick={async () => {
                    await adminToggleUser(u.id).catch(e => alert(e.message));
                    onChanged();
                  }}
                >
                  TOGGLE
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SourcesPanel({ rows }: { rows: { id: string; source: string; status: string; last_checked: string }[] }) {
  if (rows.length === 0) return <CenterNote text="NO DATA SOURCE RECORDS" />;
  return (
    <div className="space-y-2">
      {rows.map(r => (
        <div key={r.id} className="aq-panel flex items-center justify-between rounded p-3 text-[11px]">
          <span className="text-cyan-100">{r.source}</span>
          <span className={r.status === 'healthy' ? 'text-emerald-300' : 'text-red-400'}>{r.status}</span>
          <span className="text-slate-500">{new Date(r.last_checked).toLocaleString()}</span>
        </div>
      ))}
      <p className="text-[9px] text-slate-600">
        Elevation/bathymetry (GEBCO) and fishing-effort (GFW) layers are documentation-only in the MVP; predictions use
        the Open-Meteo marine API plus rule-based depth proxy.
      </p>
    </div>
  );
}

function CenterNote({ text }: { text: string }) {
  return (
    <div className="flex h-full items-center justify-center">
      <p className="text-[11px] tracking-[0.25em] text-slate-500">{text}</p>
    </div>
  );
}
