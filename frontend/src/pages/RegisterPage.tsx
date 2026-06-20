import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';

export default function RegisterPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), displayName.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full flex flex-col items-center justify-center px-6 py-12 safe-bottom">
      <div className="text-center mb-10">
        <div className="text-6xl mb-4">⚽</div>
        <h1 className="text-3xl font-black text-gold tracking-tight">World Cup '26</h1>
        <p className="text-gray-400 mt-2">Watch Party Games</p>
      </div>

      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
        <div>
          <label className="block text-sm text-gray-400 mb-2">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@email.com"
            className="w-full rounded-xl bg-card border border-pitch-light/40 px-4 py-4 text-lg focus:outline-none focus:border-gold"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-2">Display Name</label>
          <input
            type="text"
            required
            maxLength={50}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Your name on the leaderboard"
            className="w-full rounded-xl bg-card border border-pitch-light/40 px-4 py-4 text-lg focus:outline-none focus:border-gold"
          />
        </div>
        {error && <p className="text-red-400 text-sm text-center">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full touch-target rounded-xl bg-gold text-pitch-dark py-4 text-lg font-bold active:scale-98 transition disabled:opacity-50"
        >
          {loading ? 'Joining...' : 'Join the Party 🎉'}
        </button>
      </form>
    </div>
  );
}
