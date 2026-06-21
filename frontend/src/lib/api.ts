const API_BASE = import.meta.env.VITE_API_URL || '';

export interface User {
  email: string;
  display_name: string;
  has_seen_game_rules: boolean;
}

export interface Game {
  id: string;
  home_team: string;
  away_team: string;
  home_flag: string;
  away_flag: string;
  kickoff_at: string;
  status: string;
  home_score: number;
  away_score: number;
  current_half: number;
  is_locked: boolean;
}

export interface LeaderboardEntry {
  email: string;
  display_name: string;
  total_points: number;
  rank: number;
}

export interface ScoreEvent {
  id: number;
  source: string;
  description: string;
  points: number;
  game_id: string | null;
  created_at: string;
}

export interface Player {
  id: string;
  name: string;
  country: string;
  position: string;
  game_id: string;
  previous_opponent: string | null;
  previous_points: number;
  goals: number;
  assists: number;
  clean_sheet: boolean;
  unavailable: boolean;
  is_selectable: boolean;
}

export interface BingoSquare {
  index: number;
  description: string;
  is_free: boolean;
  marked: boolean;
}

function getToken(): string | null {
  return localStorage.getItem('wc26_token');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem('wc26_token');
    localStorage.removeItem('wc26_user');
    window.location.href = '/register';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  register: (email: string, display_name: string) =>
    request<{ session_token: string; email: string; display_name: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, display_name }),
    }),

  me: () => request<User>('/api/auth/me'),
  endSession: () => request('/api/auth/end-session', { method: 'POST' }),
  markRulesSeen: () => request('/api/auth/mark-rules-seen', { method: 'POST' }),

  getGames: () => request<Game[]>('/api/games'),
  getGame: (id: string) => request<Game>(`/api/games/${id}`),

  getPickEm: (gameId: string) => request<{ home_score: number; away_score: number; is_locked: boolean } | null>(`/api/pick-em/${gameId}`),
  savePickEm: (gameId: string, home_score: number, away_score: number) =>
    request(`/api/pick-em/${gameId}`, { method: 'PUT', body: JSON.stringify({ home_score, away_score }) }),

  getPlayers: (params: Record<string, string>) => {
    const qs = new URLSearchParams(params).toString();
    return request<Player[]>(`/api/captain/players?${qs}`);
  },
  getCaptain: () => request<{ player: Player | null; score_events: ScoreEvent[]; is_locked: boolean }>('/api/captain/selection'),
  selectCaptain: (player_id: string) =>
    request<{ player: Player; score_events: ScoreEvent[]; is_locked: boolean }>('/api/captain/select', { method: 'POST', body: JSON.stringify({ player_id }) }),

  getBingo: () => request<{ squares: BingoSquare[]; marks: number[]; has_bingo: boolean; is_first_winner: boolean }>('/api/bingo/board'),
  markBingo: (square_index: number) =>
    request<{ squares: BingoSquare[]; marks: number[]; has_bingo: boolean; is_first_winner: boolean }>('/api/bingo/mark', { method: 'POST', body: JSON.stringify({ square_index }) }),

  getTriviaSession: () => request<{
    is_active: boolean;
    game_id: string;
    game_label: string;
    half_number: number;
    message: string;
    questions: Array<{
      id: number;
      question: string;
      options: string[];
      sort_order: number;
      answered: boolean;
      selected_index: number | null;
      is_correct: boolean | null;
    }>;
  }>('/api/trivia/session'),
  getTrivia: (gameId: string) => request<{
    is_active: boolean;
    game_id: string;
    game_label: string;
    half_number: number;
    message: string;
    questions: Array<{
      id: number;
      question: string;
      options: string[];
      sort_order: number;
      answered: boolean;
      selected_index: number | null;
      is_correct: boolean | null;
    }>;
  }>(`/api/trivia/${gameId}`),
  answerTrivia: (gameId: string, question_id: number, selected_index: number) =>
    request(`/api/trivia/${gameId}/answer`, { method: 'POST', body: JSON.stringify({ question_id, selected_index }) }),

  getLeaderboard: () => request<LeaderboardEntry[]>('/api/leaderboard'),
  getScoring: () => request<{ total_points: number; events: ScoreEvent[]; rules: Array<{ category: string; outcome: string; points: string }> }>('/api/scoring'),

  scanAttendance: (qr_payload: string) =>
    request<{ game_id: string; game_name: string; points_awarded: number; already_scanned: boolean }>('/api/attendance/scan', {
      method: 'POST',
      body: JSON.stringify({ qr_payload }),
    }),
};
