import { type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  confirmLabel?: string;
  onConfirm?: () => void;
  cancelLabel?: string;
}

export function Modal({ open, onClose, title, children, confirmLabel, onConfirm, cancelLabel = 'Close' }: ModalProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-2xl bg-card p-6 shadow-2xl border border-pitch-light/30"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-gold mb-4">{title}</h2>
        <div className="text-gray-200 text-sm leading-relaxed mb-6">{children}</div>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 touch-target rounded-xl bg-gray-700 py-3 font-semibold active:scale-95 transition"
          >
            {cancelLabel}
          </button>
          {confirmLabel && onConfirm && (
            <button
              onClick={onConfirm}
              className="flex-1 touch-target rounded-xl bg-gold text-pitch-dark py-3 font-bold active:scale-95 transition"
            >
              {confirmLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function GameRulesModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Modal open={open} onClose={onClose} title="🏆 Watch Party Games" confirmLabel="Let's Go!" onConfirm={onClose}>
      <ul className="space-y-3 list-none">
        <li><strong className="text-gold">Pick'ems</strong> — Predict the score before kickoff. Earn points for winner, score sides, and exact score.</li>
        <li><strong className="text-gold">Captain</strong> — Pick one player for the day. Goals, assists, and clean sheets earn bonus points.</li>
        <li><strong className="text-gold">Bingo</strong> — Mark off events as you see them. First to 5 in a row wins big!</li>
        <li><strong className="text-gold">Trivia</strong> — Answer 5 questions during each half-time break.</li>
        <li><strong className="text-gold">Attendance</strong> — Scan the QR code in the room for a bonus each game.</li>
      </ul>
    </Modal>
  );
}

export function BottomNav() {
  const navigate = useNavigate();
  const links = [
    { label: 'Leaderboard', path: '/leaderboard' },
    { label: 'Scoring', path: '/scoring' },
    { label: 'Attendance', path: '/attendance' },
  ];
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-pitch-dark/95 backdrop-blur border-t border-pitch-light/30 safe-bottom z-40">
      <div className="flex justify-around py-2 px-2">
        {links.map((l) => (
          <button
            key={l.path}
            onClick={() => navigate(l.path)}
            className="flex-1 touch-target text-sm font-semibold text-gray-300 active:text-gold py-3 mx-1 rounded-lg active:bg-pitch-light/20 transition"
          >
            {l.label}
          </button>
        ))}
      </div>
    </nav>
  );
}

export function PageShell({ children, title, backTo }: { children: ReactNode; title?: string; backTo?: string }) {
  const navigate = useNavigate();
  return (
    <div className="min-h-full pb-24 safe-bottom">
      {title && (
        <header className="sticky top-0 z-30 bg-pitch-dark/90 backdrop-blur px-4 py-3 flex items-center gap-3 border-b border-pitch-light/20">
          {backTo && (
            <button onClick={() => navigate(backTo)} className="touch-target text-gold text-2xl leading-none">←</button>
          )}
          <h1 className="text-lg font-bold">{title}</h1>
        </header>
      )}
      <main className="px-4 py-4">{children}</main>
    </div>
  );
}

export function ScoreInput({ value, onChange, label, disabled }: { value: number; onChange: (v: number) => void; label: string; disabled?: boolean }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      <div className="flex items-center gap-4">
        <button
          disabled={disabled || value <= 0}
          onClick={() => onChange(Math.max(0, value - 1))}
          className="touch-target w-12 h-12 rounded-full bg-pitch-light text-xl font-bold disabled:opacity-30 active:scale-90 transition"
        >−</button>
        <span className="text-4xl font-bold w-12 text-center tabular-nums">{value}</span>
        <button
          disabled={disabled}
          onClick={() => onChange(Math.min(20, value + 1))}
          className="touch-target w-12 h-12 rounded-full bg-pitch-light text-xl font-bold disabled:opacity-30 active:scale-90 transition"
        >+</button>
      </div>
    </div>
  );
}
