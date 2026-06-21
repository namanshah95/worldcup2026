"""Tests for Sportmonks score parsing and player stat mapping."""

from __future__ import annotations

import unittest

from app.services.sportmonks import build_player_stats, match_player_name, parse_scores


class SportmonksScoreTests(unittest.TestCase):
    def test_parse_current_scores_by_participant_side(self):
        fixture = {
            "participants": [
                {"id": 1, "meta": {"location": "home"}},
                {"id": 2, "meta": {"location": "away"}},
            ],
            "scores": [
                {
                    "description": "CURRENT",
                    "participant_id": "1",
                    "score": {"goals": 4, "participant": "home"},
                },
                {
                    "description": "CURRENT",
                    "participant_id": "2",
                    "score": {"goals": 0, "participant": "away"},
                },
            ],
        }
        self.assertEqual(parse_scores(fixture), (4, 0))

    def test_parse_second_half_when_current_missing(self):
        fixture = {
            "participants": [
                {"id": 10, "meta": {"location": "home"}},
                {"id": 20, "meta": {"location": "away"}},
            ],
            "scores": [
                {
                    "description": "2ND_HALF",
                    "participant_id": 10,
                    "score": {"goals": 4, "participant": "home"},
                },
                {
                    "description": "2ND_HALF",
                    "participant_id": 20,
                    "score": {"goals": 0, "participant": "away"},
                },
            ],
        }
        self.assertEqual(parse_scores(fixture), (4, 0))

    def test_match_player_name_yamal(self):
        self.assertTrue(match_player_name("Yamal", "Lamine Yamal"))

    def test_goal_event_maps_yamal(self):
        fixture = {
            "state_id": 5,
            "participants": [
                {"id": 1, "name": "Spain", "meta": {"location": "home"}},
                {"id": 2, "name": "Saudi Arabia", "meta": {"location": "away"}},
            ],
            "scores": [
                {"description": "CURRENT", "participant_id": 1, "score": {"goals": 4, "participant": "home"}},
                {"description": "CURRENT", "participant_id": 2, "score": {"goals": 0, "participant": "away"}},
            ],
            "events": [
                {"type_id": 14, "player_id": 999, "player_name": "Lamine Yamal"},
            ],
            "lineups": [],
        }
        players = [{"id": "esp-yamal", "name": "Yamal", "country": "Spain", "position": "FWD"}]
        stats = build_player_stats(fixture, players)
        self.assertEqual(stats["esp-yamal"]["goals"], 1)


if __name__ == "__main__":
    unittest.main()
