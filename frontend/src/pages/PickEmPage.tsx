import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { PageShell, ScoreInput } from '../components/UI';
import { api, type Game } from '../lib/api';

export default function PickEmPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [homeScore, setHomeScore] = useState(0);
  const [awayScore, setAwayScore] = useState(0);
  const [locked, setLocked] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!gameId) return;
    Promise.all([api.getGame(gameId), api.getPickEm(gameId)]).then(([g, pred]) => {
      setGame(g);
      setLocked(g.is_locked || pred?.is_locked || false);
      if (pred) {
        setHomeScore(pred.home_score);
        setAwayScore(pred.away_score);
      }
    });
  }, [gameId]);

  const save = async () => {
    if (!gameId) return;
    setError('');
    try {
      await api.savePickEm(gameId, homeScore, awayScore);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    }
  };

  if (!game) return <PageShell title="Pick'em" backTo="/"><p className="text-center text-gray-400">Loading...</p></PageShell>;

  return (
    <PageShell title="Pick'em" backTo="/">
      <div className="text-center mb-8">
        <div className="text-5xl mb-3">{game.home_flag} vs {game.away_flag}</div>
        <h2 className="text-xl font-bold">{game.home_team} vs {game.away_team}</h2>
        {locked && <p className="text-amber-400 mt-2 text-sm">🔒 Locked — match has started</p>}
      </div>

      <div className="flex justify-around items-center mb-10">
        <ScoreInput value={homeScore} onChange={setHomeScore} label={game.home_team} disabled={locked} />
        <span className="text-3xl font-light text-gray-500">:</span>
        <ScoreInput value={awayScore} onChange={setAwayScore} label={game.away_team} disabled={locked} />
      </div>

      {!locked && (
        <button
          onClick={save}
          className="w-full touch-target rounded-xl bg-gold text-pitch-dark py-4 text-lg font-bold active:scale-98 transition"
        >
          {saved ? '✓ Saved!' : 'Save Prediction'}
        </button>
      )}
      {error && <p className="text-red-400 text-center mt-4">{error}</p>}

      <div className="mt-8 p-4 rounded-xl bg-card/50 text-sm text-gray-400">
        <p className="font-semibold text-gold mb-2">Scoring</p>
        <p>Correct winner: 5 pts · Each correct score side: 3 pts · Exact score bonus: 4 pts</p>
      </div>
    </PageShell>
  );
}
