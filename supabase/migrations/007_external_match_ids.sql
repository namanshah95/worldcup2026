-- Provider-agnostic external IDs (TheStatsAPI match_id strings like mt_123, etc.)
ALTER TABLE games ADD COLUMN IF NOT EXISTS external_match_id TEXT;
ALTER TABLE players ADD COLUMN IF NOT EXISTS external_player_id TEXT;

CREATE INDEX IF NOT EXISTS idx_games_external_match ON games(external_match_id);
CREATE INDEX IF NOT EXISTS idx_players_external_player ON players(external_player_id);
