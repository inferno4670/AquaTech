import { useCallback, useEffect, useState } from 'react';
import type { PointsSnapshot, RewardItem } from '../contracts';
import { getPointsSnapshot, listRewards, redeemReward } from '../api';
import { useAuth } from '../store/auth';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [points, setPoints] = useState<PointsSnapshot | null>(null);
  const [rewards, setRewards] = useState<RewardItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    getPointsSnapshot().then(setPoints).catch(e => setError(e instanceof Error ? e.message : 'Failed to load points'));
  }, []);

  useEffect(() => {
    listRewards()
      .then(r => setRewards(r.rewards))
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load rewards'));
  }, []);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  if (!user) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-xs tracking-[0.25em] text-slate-500">SIGN IN TO VIEW CONTRIBUTOR PROFILE</p>
      </div>
    );
  }

  const redeem = async (rewardId: string) => {
    setMessage(null);
    setError(null);
    try {
      const r = await redeemReward(rewardId);
      setMessage(`Redeemed: ${r.title} (${r.status}) — sandbox fulfillment.`);
      void refreshUser();
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Redemption failed');
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mx-auto grid max-w-4xl gap-4 md:grid-cols-2">
        {/* Identity + stats */}
        <section className="aq-panel rounded-lg p-5">
          <h1 className="aq-glow-text text-sm tracking-[0.3em] text-cyan-200">CONTRIBUTOR PROFILE</h1>
          <p className="mt-1 text-lg text-cyan-100">{user.display_name}</p>
          <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-[12px]">
            <Stat label="Reputation" value={user.reputation} />
            <Stat label="Contributor level" value={`L${user.level}`} />
            <Stat label="Observations" value={user.observations_count} />
            <Stat label="Verified" value={user.verified_count} />
            <Stat label="Data quality" value={`${user.data_quality_percent.toFixed(0)}%`} />
          </div>
        </section>

        {/* Points */}
        <section className="aq-panel rounded-lg p-5">
          <h2 className="aq-glow-text text-sm tracking-[0.3em] text-cyan-200">POINTS</h2>
          {points ? (
            <>
              <p className="mt-2 text-4xl font-bold text-lime-300 aq-glow-text">{points.balance}</p>
              <p className="text-[10px] text-slate-500">balance · level {points.level} · reputation {points.reputation}</p>
              <div className="mt-3 max-h-44 space-y-1 overflow-y-auto text-[10px]">
                {points.transactions.map(t => (
                  <div key={t.id} className="flex justify-between border-b border-cyan-500/10 py-0.5">
                    <span className={t.delta >= 0 ? 'text-emerald-400' : 'text-red-400'}>{t.delta >= 0 ? '+' : ''}{t.delta}</span>
                    <span className="text-slate-500">{t.reason.replace(/_/g, ' ')}</span>
                    <span className="text-slate-600">{new Date(t.created_at).toLocaleDateString()}</span>
                  </div>
                ))}
                {points.transactions.length === 0 && <p className="text-slate-600">No transactions yet — submit a sighting.</p>}
              </div>
            </>
          ) : (
            <p className="mt-3 text-[11px] text-slate-500">loading…</p>
          )}
        </section>

        {/* Rewards sandbox */}
        <section className="aq-panel rounded-lg p-5 md:col-span-2">
          <h2 className="aq-glow-text text-sm tracking-[0.3em] text-cyan-200">REWARD CATALOG · SANDBOX</h2>
          <p className="mb-3 text-[10px] text-slate-500">
            Redemptions are simulated (sandbox provider) — no real-world vouchers are issued.
          </p>
          <div className="grid gap-3 md:grid-cols-3">
            {rewards.map(r => (
              <div key={r.id} className="aq-neon-border rounded p-3">
                <p className="text-sm text-cyan-100">{r.title}</p>
                <p className="mt-1 text-[10px] text-slate-500">{r.description}</p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-xs font-bold text-lime-300">{r.points_cost} pts</span>
                  <button
                    type="button"
                    disabled={!r.available || (points?.balance ?? 0) < r.points_cost}
                    onClick={() => redeem(r.id)}
                    className="aq-btn px-2 py-1 text-[9px]"
                  >
                    REDEEM
                  </button>
                </div>
              </div>
            ))}
          </div>
          {message && <p className="mt-3 text-[11px] text-emerald-300">{message}</p>}
          {error && <p className="mt-3 text-[11px] text-red-400">{error}</p>}
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between border-b border-cyan-500/10 py-1">
      <span className="text-slate-500">{label}</span>
      <span className="text-cyan-200">{value}</span>
    </div>
  );
}
