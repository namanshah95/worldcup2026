-- Recalculate previous_points using captain scoring:
--   goals × 10 + assists × 5 + clean sheet × 8 (GK/DEF only)
-- Stats reflect each player's prior match vs previous_opponent (seed form guide).

ALTER TABLE players
  ADD COLUMN IF NOT EXISTS previous_goals INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS previous_assists INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS previous_clean_sheet BOOLEAN NOT NULL DEFAULT FALSE;

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
    -- Spain vs Brazil
    ('esp-alvarez', 1, 0, FALSE),
    ('esp-morata', 0, 1, FALSE),
    ('esp-pedri', 0, 1, FALSE),
    ('esp-rodri', 1, 0, FALSE),
    ('esp-laporte', 0, 0, TRUE),
    ('esp-simon', 0, 0, TRUE),
    ('esp-carvajal', 0, 0, TRUE),
    ('esp-oyarzabal', 0, 1, FALSE),
    ('esp-yamal', 1, 1, FALSE),
    ('esp-nwilliams', 1, 0, FALSE),
    ('esp-cucurella', 0, 0, TRUE),
    -- Saudi Arabia vs Argentina
    ('sau-salem', 0, 1, FALSE),
    ('sau-alshehri', 1, 0, FALSE),
    ('sau-owais', 0, 0, FALSE),
    ('sau-breik', 0, 0, FALSE),
    ('sau-faraj', 0, 1, FALSE),
    ('sau-marison', 0, 0, FALSE),
    ('sau-buraijk', 0, 0, FALSE),
    ('sau-amri', 0, 0, FALSE),
    ('sau-kanno', 0, 0, FALSE),
    ('sau-albishi', 0, 0, FALSE),
    ('sau-alhassoun', 0, 0, FALSE),
    -- Belgium vs Canada
    ('bel-lukaku', 1, 0, FALSE),
    ('bel-debruyne', 1, 1, FALSE),
    ('bel-witsel', 0, 1, FALSE),
    ('bel-vertonghen', 0, 0, TRUE),
    ('bel-courtois', 0, 0, TRUE),
    ('bel-carrasco', 1, 0, FALSE),
    ('bel-casteels', 0, 0, FALSE),
    ('bel-meunier', 0, 1, FALSE),
    ('bel-trossard', 1, 0, FALSE),
    ('bel-tielemans', 0, 1, FALSE),
    ('bel-doku', 1, 0, FALSE),
    -- Iran vs USA
    ('irn-taremi', 1, 0, FALSE),
    ('irn-azmoun', 1, 1, FALSE),
    ('irn-ezatolahi', 0, 0, FALSE),
    ('irn-beiranvand', 0, 0, TRUE),
    ('irn-hajsafi', 0, 0, TRUE),
    ('irn-ghoddos', 0, 1, FALSE),
    ('irn-jahan', 0, 1, FALSE),
    ('irn-moharrami', 0, 0, TRUE),
    ('irn-pouraliganji', 0, 0, TRUE),
    ('irn-shojaei', 0, 1, FALSE),
    ('irn-gouey', 0, 0, FALSE),
    -- Uruguay vs Portugal
    ('uru-nunez', 1, 0, FALSE),
    ('uru-valverde', 0, 1, FALSE),
    ('uru-araujo', 0, 0, TRUE),
    ('uru-rochet', 0, 0, TRUE),
    ('uru-suarez', 1, 0, FALSE),
    ('uru-olivera', 0, 0, TRUE),
    ('uru-bentancur', 0, 1, FALSE),
    ('uru-gimenez', 0, 0, TRUE),
    ('uru-vina', 0, 0, TRUE),
    ('uru-ugarte', 0, 0, FALSE),
    ('uru-cavani', 0, 1, FALSE),
    -- Cabo Verde vs Morocco
    ('cpv-tairu', 0, 1, FALSE),
    ('cpv-platini', 0, 1, FALSE),
    ('cpv-dias', 0, 0, TRUE),
    ('cpv-bandeira', 0, 0, TRUE),
    ('cpv-monteiro', 0, 0, FALSE),
    ('cpv-leal', 0, 0, FALSE),
    ('cpv-ponck', 0, 0, TRUE),
    ('cpv-lopes', 0, 0, FALSE),
    ('cpv-semedo', 0, 0, FALSE),
    ('cpv-cabral', 0, 1, FALSE),
    ('cpv-moreira', 0, 0, FALSE),
    -- New Zealand vs France
    ('nzl-wood', 0, 1, FALSE),
    ('nzl-rutter', 0, 0, FALSE),
    ('nzl-ryan', 0, 0, FALSE),
    ('nzl-boxall', 0, 0, FALSE),
    ('nzl-singh', 0, 0, FALSE),
    ('nzl-garbett', 0, 0, FALSE),
    ('nzl-moss', 0, 0, FALSE),
    ('nzl-smith', 0, 0, FALSE),
    ('nzl-kilkolly', 0, 0, FALSE),
    ('nzl-payne', 0, 0, FALSE),
    ('nzl-just', 0, 0, FALSE),
    -- Egypt vs England
    ('egy-salah', 1, 1, FALSE),
    ('egy-elneny', 0, 0, FALSE),
    ('egy-hegazi', 0, 0, TRUE),
    ('egy-elhenawy', 0, 0, TRUE),
    ('egy-fathy', 0, 0, TRUE),
    ('egy-trezeguet', 1, 0, FALSE),
    ('egy-marmoush', 1, 0, FALSE),
    ('egy-abdelmonem', 0, 0, TRUE),
    ('egy-zizo', 0, 1, FALSE),
    ('egy-kouka', 0, 0, FALSE),
    ('egy-gabaski', 0, 0, FALSE)
) AS v(id, goals, assists, clean_sheet)
WHERE p.id = v.id;
