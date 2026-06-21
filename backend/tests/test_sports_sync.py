"""Tests for sports sync polling cadence."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.services.sports_sync import _should_poll_thestats_game, _thestats_poll_interval_seconds


class SportsSyncPollTests(unittest.TestCase):
    def test_scheduled_far_from_kickoff_not_polled(self):
        game = {
            "id": "bel-irn",
            "status": "scheduled",
            "kickoff_at": "2026-06-21T19:00:00+00:00",
        }
        now = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
        self.assertIsNone(_thestats_poll_interval_seconds(game, now))
        self.assertFalse(_should_poll_thestats_game(game, now))

    def test_scheduled_within_hour_polled_every_two_minutes(self):
        game = {
            "id": "bel-irn",
            "status": "scheduled",
            "kickoff_at": "2026-06-21T19:00:00+00:00",
        }
        now = datetime(2026, 6, 21, 18, 30, tzinfo=timezone.utc)
        self.assertEqual(_thestats_poll_interval_seconds(game, now), 120)
        self.assertTrue(_should_poll_thestats_game(game, now))

    def test_live_game_polled_every_thirty_seconds(self):
        game = {
            "id": "bel-irn",
            "status": "live",
            "kickoff_at": "2026-06-21T19:00:00+00:00",
        }
        now = datetime(2026, 6, 21, 19, 30, tzinfo=timezone.utc)
        self.assertEqual(_thestats_poll_interval_seconds(game, now), 30)


if __name__ == "__main__":
    unittest.main()
