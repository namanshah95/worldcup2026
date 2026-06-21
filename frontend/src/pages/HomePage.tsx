import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BottomNav, GameRulesModal } from '../components/UI';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';

const ACTIVITIES = [
  { path: '/pick-em', label: "Pick'em", emoji: '🎯', subtitle: 'Predict all 4 scores' },
  { path: '/captain', label: 'Captain', emoji: '⭐', subtitle: 'Pick 1 player all day' },
  { path: '/bingo', label: 'Bingo', emoji: '🎱', subtitle: 'Spot events all day' },
  { path: '/trivia', label: 'Trivia', emoji: '🧠', subtitle: 'Half-time questions' },
];

export default function HomePage() {
  const { user, logout, refresh } = useAuth();
  const navigate = useNavigate();
  const [showRules, setShowRules] = useState(false);
  const [pendingPath, setPendingPath] = useState<string | null>(null);

  const goTo = (path: string) => {
    if (!user?.has_seen_game_rules) {
      setPendingPath(path);
      setShowRules(true);
    } else {
      navigate(path);
    }
  };

  const onRulesConfirmed = () => {
    setShowRules(false);
    api.markRulesSeen().then(refresh);
    if (pendingPath) navigate(pendingPath);
    setPendingPath(null);
  };

  const handleEndSession = async () => {
    await logout();
    navigate('/register');
  };

  return (
    <div className="min-h-full pb-28 safe-bottom">
      <header className="px-4 pt-6 pb-6 text-center">
        <p className="text-gold text-sm font-semibold uppercase tracking-widest">Welcome</p>
        <h1 className="text-2xl font-black">{user?.display_name}</h1>
        <p className="text-gray-400 text-sm mt-1">World Cup Watch Party</p>
      </header>

      <div className="px-4 grid grid-cols-2 gap-4">
        {ACTIVITIES.map((a) => (
          <button
            key={a.path}
            onClick={() => goTo(a.path)}
            className="touch-target flex flex-col items-center justify-center rounded-2xl bg-card border-2 border-pitch-light/30 p-6 min-h-[160px] active:scale-95 active:border-gold transition shadow-lg"
          >
            <span className="text-5xl mb-3">{a.emoji}</span>
            <span className="text-lg font-bold">{a.label}</span>
            <span className="text-xs text-gray-400 mt-1 text-center">{a.subtitle}</span>
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
    </div>
  );
}
