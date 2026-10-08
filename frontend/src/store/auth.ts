import { create } from 'zustand';
import * as api from '../api';
import type { UserPublic } from '../contracts';

const TOKEN_KEY = 'aquatrack.token';

interface AuthState {
  user: UserPublic | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  init: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, displayName: string) => Promise<void>;
  signOut: () => void;
  refreshUser: () => Promise<void>;
}

function persist(token: string | null) {
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
    api.setToken(token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
    api.setToken(null);
  }
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: false,
  error: null,

  init: async () => {
    const saved = window.localStorage.getItem(TOKEN_KEY);
    if (!saved) return;
    api.setToken(saved);
    set({ token: saved, loading: true });
    try {
      const user = await api.getMe();
      set({ user, loading: false });
    } catch {
      persist(null);
      set({ token: null, user: null, loading: false });
    }
  },

  signIn: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const resp = await api.login(email, password);
      persist(resp.token.access_token);
      let user = resp.user;
      try {
        user = await api.getMe();
      } catch {
        /* fall back to login payload user */
      }
      set({ user, token: resp.token.access_token, loading: false });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : 'Login failed' });
      throw e;
    }
  },

  signUp: async (email, password, displayName) => {
    set({ loading: true, error: null });
    try {
      const resp = await api.register(email, password, displayName);
      persist(resp.token.access_token);
      let user = resp.user;
      try {
        user = await api.getMe();
      } catch {
        /* fall back */
      }
      set({ user, token: resp.token.access_token, loading: false });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : 'Registration failed' });
      throw e;
    }
  },

  signOut: () => {
    persist(null);
    set({ user: null, token: null, error: null });
    void get();
  },

  refreshUser: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const user = await api.getMe();
      set({ user });
    } catch {
      /* keep stale user */
    }
  },
}));
