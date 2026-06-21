"""Tests for captain scoring."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.services.scoring import score_captain_for_game


class CaptainScoringTests(unittest.TestCase):
    def test_awards_goal_points_for_captain(self):
        game = {
            "id": "esp-sau",
            "status": "finished",
            "home_team": "Spain",
            "away_team": "Saudi Arabia",
        }
        players = [
            {"id": "esp-yamal", "name": "Yamal", "country": "Spain", "position": "FWD", "goals": 1, "assists": 0, "clean_sheet": False},
        ]
        selections = [{"user_email": "fan@example.com", "player_id": "esp-yamal"}]
        events: list[tuple] = []

        db = MagicMock()
        db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = game
        db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = players
        db.table.return_value.select.return_value.execute.return_value.data = selections
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.services.scoring.get_supabase", return_value=db):
            with patch("app.services.scoring.add_score_event", side_effect=lambda *args: events.append(args)):
                report = score_captain_for_game("esp-sau")

        self.assertFalse(report["skipped"])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][3], 10)
        self.assertIn("Yamal", events[0][2])


if __name__ == "__main__":
    unittest.main()
