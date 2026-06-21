import { useEffect, useState } from 'react';
import { PageShell, Modal } from '../components/UI';
import { api, type Player, type ScoreEvent } from '../lib/api';

const POSITIONS = ['GK', 'DEF', 'MID', 'FWD'];

export default function CaptainPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [selected, setSelected] = useState<Player | null>(null);
  const [scoreEvents, setScoreEvents] = useState<ScoreEvent[]>([]);
  const [isLocked, setIsLocked] = useState(false);
  const [search, setSearch] = useState('');
  const [country, setCountry] = useState('');
  const [position, setPosition] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [confirmPlayer, setConfirmPlayer] = useState<Player | null>(null);
  const [error, setError] = useState('');

  const loadPlayers = () => {
    const params: Record<string, string> = { sort_by: sortBy };
    if (country) params.country = country;
    if (position) params.position = position;
    if (search) params.search = search;
    api.getPlayers(params).then(setPlayers);
  };

  useEffect(() => {
    api.getCaptain().then((res) => {
      if (res.player) {
        setSelected(res.player);
        setScoreEvents(res.score_events);
        setIsLocked(res.is_locked);
      }
    });
  }, []);

  useEffect(() => {
    if (!isLocked) loadPlayers();
  }, [search, country, position, sortBy, isLocked]);

  const countries = [...new Set(players.map((p) => p.country))].sort();

  const confirmSelect = async () => {
    if (!confirmPlayer) return;
    setError('');
    try {
      const res = await api.selectCaptain(confirmPlayer.id);
      setSelected(res.player);
      setIsLocked(true);
      setConfirmPlayer(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Selection failed');
      setConfirmPlayer(null);
    }
  };

  if (selected) {
    return (
      <PageShell title="Your Captain" backTo="/">
        <div className="flex flex-col items-center">
          <div className="w-32 h-32 rounded-full bg-pitch-light flex items-center justify-center text-5xl mb-4 border-4 border-gold">
            ⭐
          </div>
          <h2 className="text-2xl font-bold">{selected.name}</h2>
          <p className="text-gray-400">{selected.country} · {selected.position}</p>
          <p className="text-sm text-gray-500 mt-1">🔒 Selection locked</p>
        </div>

        {scoreEvents.length > 0 && (
          <div className="mt-8">
            <h3 className="font-bold text-gold mb-3">Points Earned</h3>
            <ul className="space-y-2">
              {scoreEvents.map((e) => (
                <li key={e.id} className="flex justify-between bg-card rounded-lg px-4 py-3">
                  <span className="text-sm">{e.description}</span>
                  <span className="font-bold text-gold">+{e.points}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {scoreEvents.length === 0 && (
          <p className="text-center text-gray-400 mt-8">Points will appear after your captain's game ends.</p>
        )}
      </PageShell>
    );
  }

  return (
    <PageShell title="Select Captain" backTo="/">
      <p className="text-sm text-gray-400 mb-4">
        Choose one player from any of the 8 teams playing today. This cannot be changed!
      </p>

      <input
        type="text"
        placeholder="Search player name..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full rounded-xl bg-card border border-pitch-light/40 px-4 py-3 mb-3 focus:outline-none focus:border-gold"
      />

      <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
        <select value={country} onChange={(e) => setCountry(e.target.value)} className="rounded-lg bg-card px-3 py-2 text-sm">
          <option value="">All Countries</option>
          {countries.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={position} onChange={(e) => setPosition(e.target.value)} className="rounded-lg bg-card px-3 py-2 text-sm">
          <option value="">All Positions</option>
          {POSITIONS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="rounded-lg bg-card px-3 py-2 text-sm">
          <option value="name">Name</option>
          <option value="country">Country</option>
          <option value="position">Position</option>
          <option value="previous_points">Prev Points</option>
        </select>
      </div>

      <ul className="space-y-2">
        {players.map((p) => (
          <li key={p.id}>
            <button
              disabled={!p.is_selectable}
              onClick={() => setConfirmPlayer(p)}
              className={`w-full text-left rounded-xl px-4 py-3 flex justify-between items-center transition active:scale-98 ${
                p.is_selectable ? 'bg-card active:bg-pitch-light/40' : 'bg-gray-800/50 opacity-50 cursor-not-allowed'
              }`}
            >
              <div>
                <span className="font-bold">{p.name}</span>
                <span className="text-gray-400 text-sm ml-2">{p.country} · {p.position}</span>
                {p.previous_opponent && (
                  <p className="text-xs text-gray-500">Prev vs {p.previous_opponent}: {p.previous_points} pts</p>
                )}
              </div>
              {!p.is_selectable && <span className="text-xs text-gray-500">Unavailable</span>}
            </button>
          </li>
        ))}
      </ul>

      {error && <p className="text-red-400 text-center mt-4">{error}</p>}

      <Modal
        open={!!confirmPlayer}
        onClose={() => setConfirmPlayer(null)}
        title="Confirm Captain"
        confirmLabel="Lock In Captain"
        onConfirm={confirmSelect}
        cancelLabel="Go Back"
      >
        {confirmPlayer && (
          <p>
            You are selecting <strong className="text-gold">{confirmPlayer.name}</strong> ({confirmPlayer.country}).
            <br /><br />
            ⚠️ This choice is <strong>permanent</strong> and cannot be changed!
          </p>
        )}
      </Modal>
    </PageShell>
  );
}
