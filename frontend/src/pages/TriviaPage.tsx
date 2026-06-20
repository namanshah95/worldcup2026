import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { PageShell } from '../components/UI';
import { api } from '../lib/api';

interface Question {
  id: number;
  question: string;
  options: string[];
  sort_order: number;
  answered: boolean;
  selected_index: number | null;
  is_correct: boolean | null;
}

export default function TriviaPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [isActive, setIsActive] = useState(false);
  const [message, setMessage] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);

  const load = () => {
    if (!gameId) return;
    api.getTrivia(gameId).then((t) => {
      setIsActive(t.is_active);
      setMessage(t.message);
      setQuestions(t.questions);
    });
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, [gameId]);

  const answer = async (q: Question, idx: number) => {
    if (!gameId || q.answered) return;
    try {
      await api.answerTrivia(gameId, q.id, idx);
      load();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isActive) {
    return (
      <PageShell title="Trivia" backTo="/">
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
          <div className="text-6xl mb-6">⏳</div>
          <h2 className="text-xl font-bold text-gold mb-3">Trivia Locked</h2>
          <p className="text-gray-300 leading-relaxed">{message}</p>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell title="Half-Time Trivia" backTo="/">
      <p className="text-center text-amber-400 text-sm mb-6 font-semibold">⏱ Live now — answer before 2nd half!</p>
      <div className="space-y-6">
        {questions.map((q) => (
          <div key={q.id} className="rounded-xl bg-card p-4">
            <p className="font-bold mb-3">
              <span className="text-gold mr-2">Q{q.sort_order}</span>
              {q.question}
            </p>
            <div className="space-y-2">
              {q.options.map((opt, idx) => {
                let cls = 'bg-pitch-light/20 active:bg-pitch-light/50';
                if (q.answered) {
                  if (idx === q.selected_index) {
                    cls = q.is_correct ? 'bg-green-700/60' : 'bg-red-700/60';
                  } else {
                    cls = 'bg-gray-800/40 opacity-50';
                  }
                }
                return (
                  <button
                    key={idx}
                    disabled={q.answered}
                    onClick={() => answer(q, idx)}
                    className={`w-full text-left rounded-lg px-4 py-3 touch-target text-sm font-medium transition ${cls}`}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
            {q.answered && (
              <p className={`text-sm mt-2 font-semibold ${q.is_correct ? 'text-green-400' : 'text-red-400'}`}>
                {q.is_correct ? '✓ Correct! +2 pts' : '✗ Incorrect'}
              </p>
            )}
          </div>
        ))}
      </div>
      <p className="text-center text-gray-400 text-sm mt-6">Perfect 5/5 earns a +5 bonus!</p>
    </PageShell>
  );
}
