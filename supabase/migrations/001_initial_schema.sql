-- World Cup Watch Party Schema

-- Users (email is the identifier)
CREATE TABLE users (
  email TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  session_token TEXT,
  session_expires_at TIMESTAMPTZ,
  has_seen_game_rules BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Games on match day
CREATE TABLE games (
  id TEXT PRIMARY KEY,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  home_flag TEXT NOT NULL,
  away_flag TEXT NOT NULL,
  kickoff_at TIMESTAMPTZ NOT NULL,
  status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'live', 'halftime', 'finished')),
  home_score INT DEFAULT 0,
  away_score INT DEFAULT 0,
  current_half INT DEFAULT 0,
  attendance_qr_secret TEXT NOT NULL,
  sort_order INT DEFAULT 0
);

-- Players available for captain selection
CREATE TABLE players (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  position TEXT NOT NULL CHECK (position IN ('GK', 'DEF', 'MID', 'FWD')),
  game_id TEXT REFERENCES games(id),
  previous_opponent TEXT,
  previous_points INT DEFAULT 0,
  goals INT DEFAULT 0,
  assists INT DEFAULT 0,
  clean_sheet BOOLEAN DEFAULT FALSE,
  unavailable BOOLEAN DEFAULT FALSE
);

-- Captain selections (one per user, immutable)
CREATE TABLE captain_selections (
  user_email TEXT PRIMARY KEY REFERENCES users(email),
  player_id TEXT NOT NULL REFERENCES players(id),
  selected_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pick'em predictions
CREATE TABLE pick_em_predictions (
  user_email TEXT REFERENCES users(email),
  game_id TEXT REFERENCES games(id),
  home_score INT NOT NULL,
  away_score INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_email, game_id)
);

-- Bingo event bank
CREATE TABLE bingo_events (
  id SERIAL PRIMARY KEY,
  description TEXT NOT NULL UNIQUE,
  category TEXT DEFAULT 'general'
);

-- User bingo boards (25 cells: indices 0-24, index 12 is free space)
CREATE TABLE bingo_boards (
  user_email TEXT PRIMARY KEY REFERENCES users(email),
  event_ids INT[] NOT NULL,
  completed_at TIMESTAMPTZ,
  is_first_winner BOOLEAN DEFAULT FALSE
);

-- Bingo square marks
CREATE TABLE bingo_marks (
  user_email TEXT REFERENCES users(email),
  square_index INT NOT NULL CHECK (square_index >= 0 AND square_index <= 24),
  marked_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_email, square_index)
);

-- Trivia questions (same for all users per game/half)
CREATE TABLE trivia_questions (
  id SERIAL PRIMARY KEY,
  game_id TEXT REFERENCES games(id),
  half_number INT NOT NULL CHECK (half_number IN (1, 2)),
  question TEXT NOT NULL,
  options JSONB NOT NULL,
  correct_index INT NOT NULL,
  sort_order INT NOT NULL,
  UNIQUE (game_id, half_number, sort_order)
);

-- Trivia answers
CREATE TABLE trivia_answers (
  user_email TEXT REFERENCES users(email),
  question_id INT REFERENCES trivia_questions(id),
  selected_index INT NOT NULL,
  is_correct BOOLEAN NOT NULL,
  answered_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_email, question_id)
);

-- Attendance bonus scans
CREATE TABLE attendance_scans (
  user_email TEXT REFERENCES users(email),
  game_id TEXT REFERENCES games(id),
  scanned_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_email, game_id)
);

-- Score ledger for breakdown display
CREATE TABLE score_events (
  id SERIAL PRIMARY KEY,
  user_email TEXT REFERENCES users(email),
  source TEXT NOT NULL,
  description TEXT NOT NULL,
  points INT NOT NULL,
  game_id TEXT REFERENCES games(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_score_events_user ON score_events(user_email);
CREATE INDEX idx_players_game ON players(game_id);
CREATE INDEX idx_trivia_game_half ON trivia_questions(game_id, half_number);

-- Enable realtime for leaderboard-related tables
ALTER PUBLICATION supabase_realtime ADD TABLE users;
ALTER PUBLICATION supabase_realtime ADD TABLE score_events;

-- Leaderboard view
CREATE OR REPLACE VIEW leaderboard AS
SELECT
  u.email,
  u.display_name,
  COALESCE(SUM(se.points), 0)::INT AS total_points
FROM users u
LEFT JOIN score_events se ON se.user_email = u.email
GROUP BY u.email, u.display_name
ORDER BY total_points DESC, u.display_name ASC;
