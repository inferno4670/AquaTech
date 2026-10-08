import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../store/auth';
import { getHealth } from '../api';
import { DISCLAIMER } from '../lib/ui';

const NAV = [
  { to: '/find', label: 'FIND FISH', end: false },
  { to: '/contribute', label: 'CONTRIBUTE', end: false },
  { to: '/species', label: 'SPECIES', end: false },
  { to: '/profile', label: 'PROFILE', end: false },
];

// Admin-only entry, appended when the signed-in account has the admin role.
const ADMIN_NAV = { to: '/admin', label: 'ADMIN', end: false };

export default function AppShell() {
  const { user, init, signOut } = useAuth();
  const [health, setHealth] = useState<'ok' | 'down' | 'unknown'>('unknown');

  useEffect(() => {
    void init();
  }, [init]);

  useEffect(() => {
    getHealth()
      .then(() => setHealth('ok'))
      .catch(() => setHealth('down'));
  }, []);

  return (
    <div className="flex h-full flex-col">
      <header className="aq-panel z-30 flex items-center gap-4 px-4 py-2">
        {/* Brand mark + wordmark. */}
        <NavLink to="/" title="AquaTech" className="flex items-center gap-2">
          <img
            src="/aq-logo.svg"
            alt="AquaTech"
            width={22}
            height={22}
            className="shrink-0"
          />
          <span className="aq-glow-text font-bold tracking-[0.25em] text-cyan-200">AQUATECH</span>
        </NavLink>
        <nav className="ml-4 flex gap-1 text-xs">
          {(user?.is_admin ? [...NAV, ADMIN_NAV] : NAV).map(n => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `px-3 py-1 tracking-widest transition-colors ${
                  isActive ? 'bg-cyan-400/20 text-cyan-200 aq-neon-border' : 'text-slate-400 hover:text-cyan-300'
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-[10px] tracking-widest text-slate-400">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                health === 'ok' ? 'bg-emerald-400 aq-pulse' : health === 'down' ? 'bg-red-500' : 'bg-slate-500'
              }`}
            />
            {health === 'ok' ? 'API ONLINE' : health === 'down' ? 'API OFFLINE' : 'API …'}
          </span>
          {user ? (
            <button
              type="button"
              onClick={signOut}
              className="aq-btn px-3 py-1 text-[10px]"
              title={`${user.display_name} (lvl ${user.level})`}
            >
              {user.display_name} · SIGN OUT
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('aquatrack:open-auth'));
              }}
              className="aq-btn-primary px-3 py-1 text-[10px]"
            >
              SIGN IN
            </button>
          )}
        </div>
      </header>

      <main className="relative min-h-0 flex-1">
        <Outlet />
      </main>

      <footer className="aq-panel z-30 px-4 py-1.5 text-[10px] leading-snug text-slate-400">
        <span className="text-amber-400">⚠ DISCLAIMER:</span> {DISCLAIMER}
      </footer>
    </div>
  );
}
