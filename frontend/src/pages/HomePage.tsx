import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BottomNav, GameRulesModal } from '../components/UI';
import { api, type Game } from '../lib/api';
import { useAuth } from '../lib/auth';

const GAME_ACTIVITIES = [
  { key: 'pick-em', label: "Pick'em", emoji: '🎯' },
  { key: 'captain', label: 'Captain', emoji: '⭐' },
  { key: 'bingo', label: 'Bingo', emoji: '🎱' },
  { key: 'trivia', label: 'Trivia', emoji: '🧠' },
];

export default function HomePage() {
  const { user, logout, refresh } = useAuth();
  const navigate = useNavigate();
  const [games, setGames] = useState<Game[]>([]);
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [showActivityPicker, setShowActivityPicker] = useState(false);

  useEffect(() => {
    api.getGames().then(setGames).catch(console.error);
  }, []);

  const openGame = (game: Game) => {
    setSelectedGame(game);
    if (!user?.has_seen_game_rules) {
      setShowRules(true);
    } else {
      setShowActivityPicker(true);
    }
  };

  const onRulesConfirmed = () => {
    setShowRules(false);
    api.markRulesSeen().then(refresh);
    setShowActivityPicker(true);
  };

  const goToActivity = (activity: string) => {
    if (!selectedGame) return;
    setShowActivityPicker(false);
    navigate(`/game/${selectedGame.id}/${activity}`);
  };

  const handleEndSession = async () => {
    await logout();
    navigate('/register');
  };

  return (
    <div className="min-h-full pb-28 safe-bottom">
      <header className="px-4 pt-6 pb-4 text-center">
        <p className="text-gold text-sm font-semibold uppercase tracking-widest">Welcome</p>
        <h1 className="text-2xl font-black">{user?.display_name}</h1>
      </header>

      <div className="px-4 grid grid-cols-2 gap-4">
        {games.map((g) => (
          <button
            key={g.id}
            onClick={() => openGame(g)}
            className="touch-target flex flex-col items-center justify-center rounded-2xl bg-card border-2 border-pitch-light/30 p-5 min-h-[140px] active:scale-95 active:border-gold transition shadow-lg"
          >
            <div className="text-4xl mb-2">{g.home_flag} vs {g.away_flag}</div>
            <div className="text-sm font-bold text-center leading-tight">
              {g.home_team}<br />vs<br />{g.away_team}
            </div>
            {g.status !== 'scheduled' && (
              <div className="mt-2 text-gold font-bold text-lg">{g.home_score} - {g.away_score}</div>
            )}
          </button>
        ))}
      </div>

      <BottomNav />

      <div className="fixed bottom-16 left-0 right-0 px-4 safe-bottom">
        <button
          onClick={handleEndSession}
          className="w-full text-center text-gray-500 text-sm py-2 underline"
        >
          End Session
        </button>
      </div>

      <GameRulesModal open={showRules} onClose={onRulesConfirmed} />

      {showActivityPicker && selectedGame && (
        <div className="fixed inset-0 z-50 flex items-end bg-black/70" onClick={() => setShowActivityPicker(false)}>
          <div className="w-full rounded-t-3xl bg-card p-6 safe-bottom" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-center text-lg font-bold mb-1">
              {selectedGame.home_flag} {selectedGame.home_team} vs {selectedGame.away_team} {selectedGame.away_flag}
            </h2>
            <p className="text-center text-gray-400 text-sm mb-6">Choose a game</p>
            <div className="grid grid-cols-2 gap-3">
              {GAME_ACTIVITIES.map((a) => (
                <button
                  key={a.key}
                  onClick={() => goToActivity(a.key)}
                  className="touch-target rounded-xl bg-pitch-light/30 py-5 font-bold text-lg active:bg-gold active:text-pitch-dark transition"
                >
                  <span className="text-2xl block mb-1">{a.emoji}</span>
                  {a.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
