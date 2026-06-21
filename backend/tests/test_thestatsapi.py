"""Tests for TheStatsAPI status/score mapping."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.services.thestatsapi import (
    TheStatsApiClient,
    map_match_status,
    match_matches_game,
    parse_scores,
    team_matches,
)


class TheStatsApiTests(unittest.TestCase):
    def test_halftime_from_live_meta(self):
        match = {"status": "live"}
        live_meta = {"match_status": "halftime", "home_goals": 1, "away_goals": 0}
        self.assertEqual(map_match_status(match, live_meta), ("halftime", 1))

    def test_live_second_half(self):
        match = {"status": "live"}
        live_meta = {"match_status": "second_half", "period": "second_half"}
        self.assertEqual(map_match_status(match, live_meta), ("live", 2))

    def test_scores_from_live_meta(self):
        match = {"score": {"home": 0, "away": 0}}
        live_meta = {"home_goals": 2, "away_goals": 1}
        self.assertEqual(parse_scores(match, live_meta), (2, 1))

    def test_team_matching(self):
        self.assertTrue(team_matches("Cabo Verde", "Cape Verde"))
        self.assertTrue(match_matches_game(
            {"home_team": {"name": "Spain"}, "away_team": {"name": "Saudi Arabia"}},
            "Spain",
            "Saudi Arabia",
        ))


class TheStatsApiClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_live_stats_409_treated_as_unavailable(self):
        client = TheStatsApiClient(api_key="test-key")
        http = AsyncMock()
        response = MagicMock()
        response.status_code = 409
        response.text = '{"error":{"message":"Match not live"}}'
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "conflict", request=MagicMock(), response=response
        )

        with patch.object(client, "_get", side_effect=httpx.HTTPStatusError(
            "conflict", request=MagicMock(), response=response
        )):
            result = await client.get_live_stats(http, "mt_732525756")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
