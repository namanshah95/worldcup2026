"""Tests for kickoff-based locking and trivia half-time windows."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from app.services.game_schedule import (
    estimate_status_from_kickoff,
    effective_game_state,
    is_game_locked,
    link_search_dates,
)


KICKOFF = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)


class GameScheduleTests(unittest.TestCase):
    def test_pick_em_locks_at_kickoff_not_before(self):
        before = KICKOFF - timedelta(minutes=1)
        at_kickoff = KICKOFF
        after = KICKOFF + timedelta(minutes=5)

        self.assertFalse(is_game_locked(KICKOFF, before))
        self.assertTrue(is_game_locked(KICKOFF, at_kickoff))
        self.assertTrue(is_game_locked(KICKOFF, after))

    def test_per_match_lock_is_independent(self):
        """esp-sau at 12:05 locked; bel-irn at 15:00 still open."""
        esp_kickoff = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
        bel_kickoff = datetime(2026, 6, 21, 15, 0, tzinfo=timezone.utc)
        now = datetime(2026, 6, 21, 12, 5, tzinfo=timezone.utc)

        self.assertTrue(is_game_locked(esp_kickoff, now))
        self.assertFalse(is_game_locked(bel_kickoff, now))

    def test_captain_player_lock_follows_their_game_kickoff(self):
        now = datetime(2026, 6, 21, 12, 5, tzinfo=timezone.utc)
        yamal_game = {"kickoff_at": "2026-06-21T12:00:00+00:00"}
        lukaku_game = {"kickoff_at": "2026-06-21T15:00:00+00:00"}

        self.assertTrue(is_game_locked(yamal_game["kickoff_at"], now))
        self.assertFalse(is_game_locked(lukaku_game["kickoff_at"], now))

    def test_trivia_halftime_window_from_kickoff(self):
        first_half = KICKOFF + timedelta(minutes=30)
        halftime = KICKOFF + timedelta(minutes=50)
        second_half = KICKOFF + timedelta(minutes=70)
        finished = KICKOFF + timedelta(minutes=110)

        self.assertEqual(estimate_status_from_kickoff(KICKOFF, first_half), ("live", 1))
        self.assertEqual(estimate_status_from_kickoff(KICKOFF, halftime), ("halftime", 1))
        self.assertEqual(estimate_status_from_kickoff(KICKOFF, second_half), ("live", 2))
        self.assertEqual(estimate_status_from_kickoff(KICKOFF, finished), ("finished", 2))

    def test_trivia_unlocks_only_during_halftime(self):
        halftime = KICKOFF + timedelta(minutes=50)
        second_half = KICKOFF + timedelta(minutes=70)

        self.assertEqual(estimate_status_from_kickoff(KICKOFF, halftime)[0], "halftime")
        self.assertNotEqual(estimate_status_from_kickoff(KICKOFF, second_half)[0], "halftime")

    def test_effective_state_prefers_sportmonks_when_linked(self):
        now = KICKOFF + timedelta(minutes=50)
        game = {
            "kickoff_at": "2026-06-21T12:00:00+00:00",
            "status": "live",
            "current_half": 1,
            "sportmonks_fixture_id": 12345,
        }
        # DB says live (Sportmonks synced) even though clock says halftime
        self.assertEqual(effective_game_state(game, now), ("live", 1))

    def test_effective_state_uses_kickoff_when_no_fixture(self):
        now = KICKOFF + timedelta(minutes=50)
        game = {
            "kickoff_at": "2026-06-21T12:00:00+00:00",
            "status": "scheduled",
            "current_half": 1,
            "sportmonks_fixture_id": None,
        }
        self.assertEqual(effective_game_state(game, now), ("halftime", 1))

    def test_waiting_message_next_match_after_first_finishes(self):
        now = datetime(2026, 6, 21, 14, 0, tzinfo=timezone.utc)
        games = [
            {
                "id": "esp-sau",
                "home_team": "Spain",
                "away_team": "Saudi Arabia",
                "kickoff_at": "2026-06-21T12:00:00+00:00",
                "status": "scheduled",
                "current_half": 1,
            },
            {
                "id": "bel-irn",
                "home_team": "Belgium",
                "away_team": "Iran",
                "kickoff_at": "2026-06-21T15:00:00+00:00",
                "status": "scheduled",
                "current_half": 1,
            },
        ]
        enriched = []
        for g in games:
            status, half = effective_game_state(g, now)
            enriched.append({**g, "status": status, "current_half": half})

        finished = [g for g in enriched if g["status"] == "finished"]
        upcoming = [g for g in enriched if g["status"] == "scheduled"]
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]["id"], "esp-sau")
        self.assertEqual(upcoming[0]["id"], "bel-irn")

    def test_link_search_dates_includes_adjacent_utc_days(self):
        """6pm Vancouver (June 21) = 01:00 UTC June 22 — search must include +1 day."""
        kickoff = "2026-06-22 01:00:00+00"
        dates = link_search_dates(kickoff)
        self.assertEqual(dates, [
            datetime(2026, 6, 21, tzinfo=timezone.utc).date(),
            datetime(2026, 6, 22, tzinfo=timezone.utc).date(),
            datetime(2026, 6, 23, tzinfo=timezone.utc).date(),
        ])


if __name__ == "__main__":
    unittest.main()
