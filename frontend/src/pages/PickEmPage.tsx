import { useEffect, useState } from 'react';
import { PageShell, ScoreInput } from '../components/UI';
import { api, type Game } from '../lib/api';

interface Prediction {
  home_score: number;
  away_score: number;
  is_locked: boolean;
}

export default function PickEmPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [predictions, setPredictions] = useState<Record<string, Prediction>>({});
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getGames().then(async (g) => {
      setGames(g);
      const preds: Record<string, Prediction> = {};
      await Promise.all(
        g.map(async (game) => {
          const pred = await api.getPickEm(game.id);
          preds[game.id] = {
            home_score: pred?.home_score ?? 0,
            away_score: pred?.away_score ?? 0,
            is_locked: game.is_locked || pred?.is_locked || false,
          };
        })
      );
      setPredictions(preds);
      setLoading(false);
    });
  }, []);

  const updateScore = (gameId: string, side: 'home' | 'away', value: number) => {
    setPredictions((prev) => ({
      ...prev,
      [gameId]: { ...prev[gameId], [`${side}_score`]: value },
    }));
  };

  const saveAll = async () => {
    setError('');
    try {
      const unlocked = games.filter((g) => !predictions[g.id]?.is_locked);
      await Promise.all(
        unlocked.map((g) => {
          const p = predictions[g.id];
          return api.savePickEm(g.id, p.home_score, p.away_score);
        })
      );
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    }
  };

  const allLocked = games.length > 0 && games.every((g) => predictions[g.id]?.is_locked);
  const anyUnlocked = games.some((g) => !predictions[g.id]?.is_locked);

  if (loading) {
    return (
      <PageShell title="Pick'em" backTo="/">
        <p className="text-center text-gray-400">Loading...</p>
      </PageShell>
    );
  }

  return (
    <PageShell title="Pick'em" backTo="/">
      <p className="text-gray-400 text-sm text-center mb-6">
        Set your score predictions for all 4 matches. Locked once each kickoff begins.
      </p>

      <div className="space-y-6 mb-8">
        {games.map((game) => {
          const pred = predictions[game.id];
          if (!pred) return null;
          return (
            <div
              key={game.id}
              className={`rounded-2xl bg-card p-4 border ${pred.is_locked ? 'border-gray-700 opacity-75' : 'border-pitch-light/30'}`}
            >
              <div className="text-center mb-4">
                <div className="text-3xl mb-1">{game.home_flag} vs {game.away_flag}</div>
                <h2 className="font-bold">{game.home_team} vs {game.away_team}</h2>
                {pred.is_locked && (
                  <p className="text-amber-400 text-xs mt-1">🔒 Locked — match started</p>
                )}
              </div>
              <div className="flex justify-around items-center">
                <ScoreInput
                  value={pred.home_score}
                  onChange={(v) => updateScore(game.id, 'home', v)}
                  label={game.home_team}
                  disabled={pred.is_locked}
                />
                <span className="text-2xl font-light text-gray-500">:</span>
                <ScoreInput
                  value={pred.away_score}
                  onChange={(v) => updateScore(game.id, 'away', v)}
                  label={game.away_team}
                  disabled={pred.is_locked}
                />
              </div>
            </div>
          );
        })}
      </div>

      {anyUnlocked && (
        <button
          onClick={saveAll}
          className="w-full touch-target rounded-xl bg-gold text-pitch-dark py-4 text-lg font-bold active:scale-98 transition"
        >
          {saved ? '✓ All Saved!' : 'Save All Predictions'}
        </button>
      )}
      {allLocked && (
        <p className="text-center text-gray-400 text-sm">All predictions are locked.</p>
      )}
      {error && <p className="text-red-400 text-center mt-4">{error}</p>}

      <div className="mt-8 p-4 rounded-xl bg-card/50 text-sm text-gray-400">
        <p className="font-semibold text-gold mb-2">Scoring (per match)</p>
        <p>Correct winner: 5 pts · Each correct score side: 3 pts · Exact score bonus: 4 pts</p>
      </div>
    </PageShell>
  );
}
