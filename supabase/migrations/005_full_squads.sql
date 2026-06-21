-- Full starting XIs: 11 players per team (88 total across 8 nations)
INSERT INTO players (id, name, country, position, game_id, previous_opponent, previous_points) VALUES
  -- Spain (8 existing → 11)
  ('esp-yamal', 'Yamal', 'Spain', 'FWD', 'esp-sau', 'Brazil', 14),
  ('esp-nwilliams', 'N. Williams', 'Spain', 'FWD', 'esp-sau', 'Brazil', 10),
  ('esp-cucurella', 'Cucurella', 'Spain', 'DEF', 'esp-sau', 'Brazil', 6),

  -- Saudi Arabia (6 → 11)
  ('sau-buraijk', 'Al-Buraijk', 'Saudi Arabia', 'DEF', 'esp-sau', 'Argentina', 4),
  ('sau-amri', 'Al-Amri', 'Saudi Arabia', 'DEF', 'esp-sau', 'Argentina', 4),
  ('sau-kanno', 'Al-Kanno', 'Saudi Arabia', 'MID', 'esp-sau', 'Argentina', 2),
  ('sau-albishi', 'Al-Abdullah', 'Saudi Arabia', 'MID', 'esp-sau', 'Argentina', 2),
  ('sau-alhassoun', 'Al-Hassoun', 'Saudi Arabia', 'FWD', 'esp-sau', 'Argentina', 4),

  -- Belgium (9 → 11)
  ('bel-tielemans', 'Tielemans', 'Belgium', 'MID', 'bel-irn', 'Canada', 6),
  ('bel-doku', 'Doku', 'Belgium', 'FWD', 'bel-irn', 'Canada', 8),

  -- Iran (7 → 11)
  ('irn-moharrami', 'Moharrami', 'Iran', 'DEF', 'bel-irn', 'USA', 4),
  ('irn-pouraliganji', 'Pouraliganji', 'Iran', 'DEF', 'bel-irn', 'USA', 4),
  ('irn-shojaei', 'Shojaei', 'Iran', 'MID', 'bel-irn', 'USA', 2),
  ('irn-gouey', 'Gouey', 'Iran', 'MID', 'bel-irn', 'USA', 2),

  -- Uruguay (7 → 11)
  ('uru-gimenez', 'Giménez', 'Uruguay', 'DEF', 'uru-cpv', 'Portugal', 8),
  ('uru-vina', 'Viña', 'Uruguay', 'DEF', 'uru-cpv', 'Portugal', 4),
  ('uru-ugarte', 'Ugarte', 'Uruguay', 'MID', 'uru-cpv', 'Portugal', 4),
  ('uru-cavani', 'Cavani', 'Uruguay', 'FWD', 'uru-cpv', 'Portugal', 6),

  -- Cabo Verde (6 → 11)
  ('cpv-ponck', 'Ponck', 'Cabo Verde', 'DEF', 'uru-cpv', 'Morocco', 4),
  ('cpv-lopes', 'Lopes', 'Cabo Verde', 'DEF', 'uru-cpv', 'Morocco', 2),
  ('cpv-semedo', 'Semedo', 'Cabo Verde', 'MID', 'uru-cpv', 'Morocco', 2),
  ('cpv-cabral', 'Cabral', 'Cabo Verde', 'FWD', 'uru-cpv', 'Morocco', 4),
  ('cpv-moreira', 'Moreira', 'Cabo Verde', 'GK', 'uru-cpv', 'Morocco', 0),

  -- New Zealand (6 → 11)
  ('nzl-moss', 'Moss', 'New Zealand', 'GK', 'nzl-egy', 'France', 0),
  ('nzl-smith', 'Smith', 'New Zealand', 'DEF', 'nzl-egy', 'France', 2),
  ('nzl-kilkolly', 'Kilkolly', 'New Zealand', 'DEF', 'nzl-egy', 'France', 2),
  ('nzl-payne', 'Payne', 'New Zealand', 'MID', 'nzl-egy', 'France', 2),
  ('nzl-just', 'Just', 'New Zealand', 'FWD', 'nzl-egy', 'France', 2),

  -- Egypt (7 → 11)
  ('egy-abdelmonem', 'Abdelmonem', 'Egypt', 'DEF', 'nzl-egy', 'England', 4),
  ('egy-zizo', 'Zizo', 'Egypt', 'MID', 'nzl-egy', 'England', 4),
  ('egy-kouka', 'Kouka', 'Egypt', 'FWD', 'nzl-egy', 'England', 2),
  ('egy-gabaski', 'Gabaski', 'Egypt', 'GK', 'nzl-egy', 'England', 0)
ON CONFLICT (id) DO NOTHING;
