import { useEffect, useState } from 'react';
import { PageShell } from '../components/UI';
import { api, type ScoreEvent } from '../lib/api';

export default function ScoringPage() {
  const [total, setTotal] = useState(0);
  const [events, setEvents] = useState<ScoreEvent[]>([]);
  const [rules, setRules] = useState<Array<{ category: string; outcome: string; points: string }>>([]);

  useEffect(() => {
    api.getScoring().then((s) => {
      setTotal(s.total_points);
      setEvents(s.events);
      setRules(s.rules);
    });
  }, []);

  return (
    <PageShell title="My Scoring" backTo="/">
      <div className="text-center mb-8">
        <p className="text-gray-400 text-sm uppercase tracking-wide">Your Total</p>
        <p className="text-5xl font-black text-gold tabular-nums">{total}</p>
      </div>

      {events.length > 0 ? (
        <div className="mb-8">
          <h2 className="font-bold text-gold mb-3">Point Breakdown</h2>
          <ul className="space-y-2">
            {events.map((e) => (
              <li key={e.id} className="flex justify-between items-start bg-card rounded-lg px-4 py-3 gap-3">
                <div>
                  <span className="text-xs text-gray-500 uppercase">{e.source}</span>
                  <p className="text-sm">{e.description}</p>
                </div>
                <span className="font-bold text-gold shrink-0">+{e.points}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="text-center text-gray-400 mb-8">No points yet — start playing!</p>
      )}

      <div>
        <h2 className="font-bold text-gold mb-3">Scoring Rules</h2>
        <div className="rounded-xl bg-card/50 overflow-hidden">
          <table className="w-full text-sm">
            <tbody>
              {rules.map((r, i) => (
                <tr key={i} className="border-b border-pitch-light/20 last:border-0">
                  <td className="px-3 py-2 text-gray-400">{r.category}</td>
                  <td className="px-3 py-2">{r.outcome}</td>
                  <td className="px-3 py-2 text-right text-gold font-bold">{r.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </PageShell>
  );
}
