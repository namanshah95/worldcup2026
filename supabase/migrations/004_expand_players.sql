-- Expand captain pool: at least 1 GK per team (8 total) and fuller squads
INSERT INTO players (id, name, country, position, game_id, previous_opponent, previous_points) VALUES
  -- Spain
  ('esp-carvajal', 'Carvajal', 'Spain', 'DEF', 'esp-sau', 'Brazil', 6),
  ('esp-oyarzabal', 'Oyarzabal', 'Spain', 'FWD', 'esp-sau', 'Brazil', 4),
  -- Saudi Arabia
  ('sau-owais', 'Al-Owais', 'Saudi Arabia', 'GK', 'esp-sau', 'Argentina', 8),
  ('sau-breik', 'Al-Breik', 'Saudi Arabia', 'DEF', 'esp-sau', 'Argentina', 4),
  ('sau-faraj', 'Al-Faraj', 'Saudi Arabia', 'MID', 'esp-sau', 'Argentina', 2),
  ('sau-marison', 'Al-Muwallad', 'Saudi Arabia', 'FWD', 'esp-sau', 'Argentina', 2),
  -- Belgium
  ('bel-carrasco', 'Carrasco', 'Belgium', 'MID', 'bel-irn', 'Canada', 6),
  ('bel-casteels', 'Casteels', 'Belgium', 'GK', 'bel-irn', 'Canada', 0),
  ('bel-meunier', 'Meunier', 'Belgium', 'DEF', 'bel-irn', 'Canada', 4),
  ('bel-trossard', 'Trossard', 'Belgium', 'FWD', 'bel-irn', 'Canada', 6),
  -- Iran
  ('irn-beiranvand', 'Beiranvand', 'Iran', 'GK', 'bel-irn', 'USA', 8),
  ('irn-hajsafi', 'Hajsafi', 'Iran', 'DEF', 'bel-irn', 'USA', 4),
  ('irn-ghoddos', 'Ghoddos', 'Iran', 'MID', 'bel-irn', 'USA', 2),
  ('irn-jahan', 'Jahanbakhsh', 'Iran', 'FWD', 'bel-irn', 'USA', 4),
  -- Uruguay
  ('uru-suarez', 'Suárez', 'Uruguay', 'FWD', 'uru-cpv', 'Portugal', 8),
  ('uru-olivera', 'Olivera', 'Uruguay', 'DEF', 'uru-cpv', 'Portugal', 4),
  ('uru-bentancur', 'Bentancur', 'Uruguay', 'MID', 'uru-cpv', 'Portugal', 4),
  -- Cabo Verde
  ('cpv-dias', 'Vozinha', 'Cabo Verde', 'GK', 'uru-cpv', 'Morocco', 8),
  ('cpv-bandeira', 'Stopira', 'Cabo Verde', 'DEF', 'uru-cpv', 'Morocco', 4),
  ('cpv-monteiro', 'Monteiro', 'Cabo Verde', 'MID', 'uru-cpv', 'Morocco', 2),
  ('cpv-leal', 'Leal', 'Cabo Verde', 'FWD', 'uru-cpv', 'Morocco', 2),
  -- New Zealand
  ('nzl-ryan', 'Ryan', 'New Zealand', 'GK', 'nzl-egy', 'France', 8),
  ('nzl-boxall', 'Boxall', 'New Zealand', 'DEF', 'nzl-egy', 'France', 2),
  ('nzl-singh', 'Singh', 'New Zealand', 'MID', 'nzl-egy', 'France', 2),
  ('nzl-garbett', 'Garbett', 'New Zealand', 'FWD', 'nzl-egy', 'France', 2),
  -- Egypt
  ('egy-elhenawy', 'El Shenawy', 'Egypt', 'GK', 'nzl-egy', 'England', 8),
  ('egy-fathy', 'Fathy', 'Egypt', 'DEF', 'nzl-egy', 'England', 4),
  ('egy-trezeguet', 'Trezeguet', 'Egypt', 'MID', 'nzl-egy', 'England', 4),
  ('egy-marmoush', 'Marmoush', 'Egypt', 'FWD', 'nzl-egy', 'England', 6)
ON CONFLICT (id) DO NOTHING;
