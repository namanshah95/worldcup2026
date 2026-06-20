import { useEffect, useState } from 'react';
import { PageShell } from '../components/UI';
import { api, type LeaderboardEntry } from '../lib/api';
import { useAuth } from '../lib/auth';
import { subscribeToScoreUpdates } from '../lib/supabase';

export default function LeaderboardPage() {
  const { user } = useAuth();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);

  const load = () => api.getLeaderboard().then(setEntries);

  useEffect(() => {
    load();
    const unsub = subscribeToScoreUpdates(load);
    const interval = setInterval(load, 30000);
    return () => { unsub(); clearInterval(interval); };
  }, []);

  return (
    <PageShell title="Leaderboard" backTo="/">
      <ul className="space-y-2">
        {entries.map((e) => {
          const isMe = e.email === user?.email;
          return (
            <li
              key={e.email}
              className={`flex items-center gap-4 rounded-xl px-4 py-4 ${
                isMe ? 'bg-gold/20 border-2 border-gold' : 'bg-card'
              }`}
            >
              <span className={`text-2xl font-black w-8 text-center ${e.rank <= 3 ? 'text-gold' : 'text-gray-500'}`}>
                {e.rank <= 3 ? ['🥇', '🥈', '🥉'][e.rank - 1] : e.rank}
              </span>
              <span className={`flex-1 text-lg ${isMe ? 'font-black' : 'font-medium'}`}>
                {e.display_name}
                {isMe && <span className="text-gold text-sm ml-2">(you)</span>}
              </span>
              <span className="text-xl font-bold text-gold tabular-nums">{e.total_points}</span>
            </li>
          );
        })}
      </ul>
      {entries.length === 0 && (
        <p className="text-center text-gray-400 mt-8">No players yet. Be the first to join!</p>
      )}
    </PageShell>
  );
}
