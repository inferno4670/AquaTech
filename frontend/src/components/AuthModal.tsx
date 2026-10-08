import { useEffect, useState } from 'react';
import { useAuth } from '../store/auth';

export default function AuthModal() {
  const { signIn, signUp, loading, error } = useAuth();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');

  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener('aquatrack:open-auth', handler);
    return () => window.removeEventListener('aquatrack:open-auth', handler);
  }, []);

  if (!open) return null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (mode === 'signin') {
        await signIn(email, password);
      } else {
        await signUp(email, password, displayName || email.split('@')[0]);
      }
      setOpen(false);
    } catch {
      /* error rendered inline */
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <form onSubmit={submit} className="aq-panel w-80 rounded-lg p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="aq-glow-text text-sm tracking-[0.3em] text-cyan-200">
            {mode === 'signin' ? 'SIGN IN' : 'CREATE ACCOUNT'}
          </h2>
          <button type="button" onClick={() => setOpen(false)} className="text-slate-500 hover:text-cyan-300">
            ✕
          </button>
        </div>
        {mode === 'signup' && (
          <label className="mb-2 block">
            <span className="aq-label">Display name</span>
            <input className="aq-input w-full" value={displayName} onChange={e => setDisplayName(e.target.value)} />
          </label>
        )}
        <label className="mb-2 block">
          <span className="aq-label">Email</span>
          <input
            className="aq-input w-full"
            type="email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="fisher@example.com"
          />
        </label>
        <label className="mb-4 block">
          <span className="aq-label">Password</span>
          <input
            className="aq-input w-full"
            type="password"
            required
            minLength={6}
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="min 6 chars"
          />
        </label>
        {error && <p className="mb-2 text-xs text-red-400">{error}</p>}
        <button type="submit" disabled={loading} className="aq-btn-primary w-full py-2 text-xs">
          {loading ? '…' : mode === 'signin' ? 'SIGN IN' : 'REGISTER'}
        </button>
        <button
          type="button"
          className="mt-3 w-full text-[10px] tracking-widest text-slate-500 hover:text-cyan-300"
          onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
        >
          {mode === 'signin' ? 'NO ACCOUNT? REGISTER →' : 'HAVE AN ACCOUNT? SIGN IN →'}
        </button>
      </form>
    </div>
  );
}
