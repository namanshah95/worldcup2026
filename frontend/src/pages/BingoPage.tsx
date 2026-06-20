import { useEffect, useState } from 'react';
import { PageShell } from '../components/UI';
import { api, type BingoSquare } from '../lib/api';

export default function BingoPage() {
  const [squares, setSquares] = useState<BingoSquare[]>([]);
  const [hasBingo, setHasBingo] = useState(false);
  const [isFirst, setIsFirst] = useState(false);

  const load = () => api.getBingo().then((b) => {
    setSquares(b.squares);
    setHasBingo(b.has_bingo);
    setIsFirst(b.is_first_winner);
  });

  useEffect(() => { load(); }, []);

  const toggle = async (idx: number, sq: BingoSquare) => {
    if (sq.is_free || sq.marked || hasBingo) return;
    try {
      const b = await api.markBingo(idx);
      setSquares(b.squares);
      setHasBingo(b.has_bingo);
      setIsFirst(b.is_first_winner);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <PageShell title="Bingo" backTo="/">
      {hasBingo && (
        <div className={`text-center rounded-xl p-4 mb-4 font-bold ${isFirst ? 'bg-gold text-pitch-dark' : 'bg-pitch-light'}`}>
          🎉 BINGO! {isFirst ? 'First winner — 20 pts!' : '10 pts!'}
        </div>
      )}

      <div className="grid grid-cols-5 gap-1.5 max-w-md mx-auto">
        {squares.map((sq) => (
          <button
            key={sq.index}
            onClick={() => toggle(sq.index, sq)}
            disabled={sq.is_free || hasBingo}
            className={`aspect-square rounded-lg text-[9px] leading-tight p-1 flex items-center justify-center text-center font-medium transition active:scale-95 ${
              sq.marked
                ? 'bg-gold text-pitch-dark line-through opacity-80'
                : sq.is_free
                ? 'bg-pitch-light text-gold font-bold'
                : 'bg-card border border-pitch-light/30'
            }`}
          >
            {sq.is_free ? 'FREE' : sq.description}
          </button>
        ))}
      </div>

      <p className="text-center text-gray-400 text-sm mt-6">
        Tap squares when you spot the event. First to 5 in a row wins 20 pts!
      </p>
    </PageShell>
  );
}
