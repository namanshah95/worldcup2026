-- Sportmonks integration columns
ALTER TABLE games ADD COLUMN IF NOT EXISTS sportmonks_fixture_id BIGINT;
ALTER TABLE games ADD COLUMN IF NOT EXISTS sportmonks_last_state_id INT;

ALTER TABLE players ADD COLUMN IF NOT EXISTS sportmonks_player_id BIGINT;

CREATE INDEX IF NOT EXISTS idx_games_sportmonks_fixture ON games(sportmonks_fixture_id);
CREATE INDEX IF NOT EXISTS idx_players_sportmonks_player ON players(sportmonks_player_id);
