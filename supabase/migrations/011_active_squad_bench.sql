-- Add active squad members who did not play MD1 (0 pts) alongside MD1 starters.

INSERT INTO players (id, name, country, position, game_id, previous_opponent, previous_points) VALUES
  ('esp-yamal', 'Yamal', 'Spain', 'FWD', 'esp-sau', 'Cabo Verde', 0),
  ('esp-nwilliams', 'N. Williams', 'Spain', 'FWD', 'esp-sau', 'Cabo Verde', 0),
  ('esp-gavi', 'Gavi', 'Spain', 'MID', 'esp-sau', 'Cabo Verde', 0),
  ('esp-ferran', 'Ferran Torres', 'Spain', 'FWD', 'esp-sau', 'Cabo Verde', 0),
  ('esp-olmo', 'Dani Olmo', 'Spain', 'FWD', 'esp-sau', 'Cabo Verde', 0),
  ('esp-merino', 'Merino', 'Spain', 'MID', 'esp-sau', 'Cabo Verde', 0),
  ('sau-shehri', 'Al-Shehri', 'Saudi Arabia', 'FWD', 'esp-sau', 'Uruguay', 0),
  ('bel-lukaku', 'Lukaku', 'Belgium', 'FWD', 'bel-irn', 'Egypt', 0),
  ('bel-deketelaere', 'De Ketelaere', 'Belgium', 'FWD', 'bel-irn', 'Egypt', 0),
  ('bel-witsel', 'Witsel', 'Belgium', 'MID', 'bel-irn', 'Egypt', 0),
  ('irn-jahanbakhsh', 'Jahanbakhsh', 'Iran', 'MID', 'bel-irn', 'New Zealand', 0),
  ('uru-gimenez', 'Giménez', 'Uruguay', 'DEF', 'uru-cpv', 'Saudi Arabia', 0),
  ('uru-arrascaeta', 'De Arrascaeta', 'Uruguay', 'MID', 'uru-cpv', 'Saudi Arabia', 0),
  ('uru-rajo', 'Ronald Araújo', 'Uruguay', 'DEF', 'uru-cpv', 'Saudi Arabia', 0),
  ('cpv-rodrigues', 'Garry Rodrigues', 'Cabo Verde', 'MID', 'uru-cpv', 'Spain', 0),
  ('nzl-rogerson', 'Rogerson', 'New Zealand', 'FWD', 'nzl-egy', 'Iran', 0),
  ('egy-trezeguet', 'Trézéguet', 'Egypt', 'FWD', 'nzl-egy', 'Belgium', 0)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  country = EXCLUDED.country,
  position = EXCLUDED.position,
  game_id = EXCLUDED.game_id,
  previous_opponent = EXCLUDED.previous_opponent,
  previous_points = EXCLUDED.previous_points;

UPDATE players AS p
SET
  previous_goals = v.goals,
  previous_assists = v.assists,
  previous_clean_sheet = v.clean_sheet,
  previous_points = v.goals * 10 + v.assists * 5 + CASE
    WHEN v.clean_sheet AND p.position IN ('GK', 'DEF') THEN 8
    ELSE 0
  END
FROM (
  VALUES
    ('esp-yamal', 0, 0, FALSE),
    ('esp-nwilliams', 0, 0, FALSE),
    ('esp-gavi', 0, 0, FALSE),
    ('esp-ferran', 0, 0, FALSE),
    ('esp-olmo', 0, 0, FALSE),
    ('esp-merino', 0, 0, FALSE),
    ('sau-shehri', 0, 0, FALSE),
    ('bel-lukaku', 0, 0, FALSE),
    ('bel-deketelaere', 0, 0, FALSE),
    ('bel-witsel', 0, 0, FALSE),
    ('irn-jahanbakhsh', 0, 0, FALSE),
    ('uru-gimenez', 0, 0, FALSE),
    ('uru-arrascaeta', 0, 0, FALSE),
    ('uru-rajo', 0, 0, FALSE),
    ('cpv-rodrigues', 0, 0, FALSE),
    ('nzl-rogerson', 0, 0, FALSE),
    ('egy-trezeguet', 0, 0, FALSE)
) AS v(id, goals, assists, clean_sheet)
WHERE p.id = v.id;
