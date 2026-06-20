import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, type User } from './api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    const token = localStorage.getItem('wc26_token');
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.me();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const login = async (email: string, displayName: string) => {
    const res = await api.register(email, displayName);
    localStorage.setItem('wc26_token', res.session_token);
    localStorage.setItem('wc26_user', JSON.stringify({ email: res.email, display_name: res.display_name }));
    setUser({ email: res.email, display_name: res.display_name, has_seen_game_rules: false });
  };

  const logout = async () => {
    try {
      await api.endSession();
    } catch {
      /* session may already be invalid */
    }
    localStorage.removeItem('wc26_token');
    localStorage.removeItem('wc26_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
