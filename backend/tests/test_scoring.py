"""Tests for pick'em scoring."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.services.scoring import score_pick_em


class PickEmScoringTests(unittest.TestCase):
    def test_correct_winner_and_one_score_side(self):
        game = {
            "id": "esp-sau",
            "home_team": "Spain",
            "away_team": "Saudi Arabia",
            "home_score": 4,
            "away_score": 0,
        }
        prediction = {"home_score": 2, "away_score": 0}
        events: list[tuple] = []

        with patch("app.services.scoring.add_score_event", side_effect=lambda *args: events.append(args)):
            score_pick_em("user@example.com", game, prediction)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][3], 5)
        self.assertIn("Correct winner", events[0][2])
        self.assertEqual(events[1][3], 3)
        self.assertIn("1 correct score side", events[1][2])

    def test_zero_zero_actual_does_not_award_winner_for_home_win_prediction(self):
        """Documents the bad first-pass case when final sync wiped scores to 0-0."""
        game = {
            "id": "esp-sau",
            "home_team": "Spain",
            "away_team": "Saudi Arabia",
            "home_score": 0,
            "away_score": 0,
        }
        prediction = {"home_score": 2, "away_score": 0}
        events: list[tuple] = []

        with patch("app.services.scoring.add_score_event", side_effect=lambda *args: events.append(args)):
            score_pick_em("user@example.com", game, prediction)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][3], 3)
        self.assertIn("correct score side", events[0][2])
