from __future__ import annotations
"""Sportmonks Football API v3 client (World Cup 2026)."""

import logging
import unicodedata
from datetime import date, datetime
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.sportmonks.com/v3/football"

# state_id -> internal match status
STATE_TO_STATUS: dict[int, str] = {
    1: "scheduled",
    2: "live",
    3: "halftime",
    4: "live",
    5: "finished",
    6: "live",
    7: "finished",
    8: "finished",
    9: "live",
    21: "halftime",
    22: "live",
}

LIVE_STATE_IDS = {2, 4, 6, 9, 22}
HALFTIME_STATE_IDS = {3, 21}
FINISHED_STATE_IDS = {5, 7, 8}

GOAL_EVENT_TYPES = {14, 16}  # goal, penalty

TEAM_ALIASES: dict[str, list[str]] = {
    "spain": ["spain"],
    "saudi arabia": ["saudi arabia", "saudi", "ksa"],
    "belgium": ["belgium"],
    "iran": ["iran", "ir iran", "team melli"],
    "uruguay": ["uruguay"],
    "cabo verde": ["cabo verde", "cape verde"],
    "new zealand": ["new zealand", "all whites"],
    "egypt": ["egypt"],
}

FIXTURE_INCLUDES = "scores;state;events;participants;lineups.player"


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.lower())
    return "".join(c for c in text if not unicodedata.combining(c)).strip()


def team_matches(expected: str, actual: str) -> bool:
    expected_key = normalize_name(expected)
    actual_norm = normalize_name(actual)
    aliases = TEAM_ALIASES.get(expected_key, [expected_key])
    return any(alias in actual_norm or actual_norm in alias for alias in aliases)


class SportmonksClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.sports_api_key
        self.league_id = settings.sportmonks_league_id

    async def _get(self, client: httpx.AsyncClient, path: str, **params: Any) -> dict:
        params["api_token"] = self.api_key
        url = f"{BASE_URL}/{path.lstrip('/')}"
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    async def get_fixtures_by_date(
        self, client: httpx.AsyncClient, day: date, include: str = "participants;state"
    ) -> list[dict]:
        payload = await self._get(
            client,
            f"fixtures/date/{day.isoformat()}",
            include=include,
            filters=f"fixtureLeagues:{self.league_id}",
        )
        return payload.get("data") or []

    async def get_fixture(self, client: httpx.AsyncClient, fixture_id: int, include: str = FIXTURE_INCLUDES) -> dict:
        payload = await self._get(client, f"fixtures/{fixture_id}", include=include)
        return payload.get("data") or {}

    async def get_inplay_fixtures(self, client: httpx.AsyncClient, include: str = "scores;state;participants") -> list[dict]:
        payload = await self._get(
            client,
            "livescores/inplay",
            include=include,
            filters=f"fixtureLeagues:{self.league_id}",
        )
        return payload.get("data") or []


def extract_participants(fixture: dict) -> tuple[Optional[dict], Optional[dict]]:
    home, away = None, None
    for participant in fixture.get("participants") or []:
        location = (participant.get("meta") or {}).get("location")
        if location == "home":
            home = participant
        elif location == "away":
            away = participant
    return home, away


def fixture_matches_game(fixture: dict, home_team: str, away_team: str) -> bool:
    home, away = extract_participants(fixture)
    if not home or not away:
        name = fixture.get("name") or ""
        return team_matches(home_team, name) and team_matches(away_team, name)
    return team_matches(home_team, home.get("name", "")) and team_matches(away_team, away.get("name", ""))


def parse_scores(fixture: dict) -> tuple[int, int]:
    home, away = extract_participants(fixture)
    if not home or not away:
        return 0, 0

    home_id = home["id"]
    away_id = away["id"]
    home_score, away_score = 0, 0

    for entry in fixture.get("scores") or []:
        if entry.get("description") != "CURRENT":
            continue
        participant_id = entry.get("participant_id")
        goals = (entry.get("score") or {}).get("goals", 0)
        if participant_id == home_id:
            home_score = goals
        elif participant_id == away_id:
            away_score = goals

    return home_score, away_score


def map_state(state_id: int) -> str:
    return STATE_TO_STATUS.get(state_id, "live")


def build_player_stats(fixture: dict, player_rows: list[dict]) -> dict[str, dict]:
    """Return stats keyed by internal player id."""
    home, away = extract_participants(fixture)
    if not home or not away:
        return {}

    home_id = home["id"]
    away_id = away["id"]
    home_score, away_score = parse_scores(fixture)

    # Map sportmonks player id -> internal player id
    sm_to_internal: dict[int, str] = {}
    name_to_internal: dict[str, str] = {}
    for row in player_rows:
        if row.get("sportmonks_player_id"):
            sm_to_internal[int(row["sportmonks_player_id"])] = row["id"]
        name_to_internal[normalize_name(row["name"])] = row["id"]

    for lineup in fixture.get("lineups") or []:
        sm_player = (lineup.get("player") or {}).get("id") or lineup.get("player_id")
        if not sm_player:
            continue
        sm_player = int(sm_player)
        display = lineup.get("player_name") or (lineup.get("player") or {}).get("display_name") or (lineup.get("player") or {}).get("name") or ""
        for row in player_rows:
            if row.get("sportmonks_player_id"):
                continue
            if normalize_name(row["name"]) in normalize_name(display) or normalize_name(display).endswith(normalize_name(row["name"])):
                sm_to_internal[sm_player] = row["id"]

    stats: dict[str, dict] = {
        pid: {"goals": 0, "assists": 0, "clean_sheet": False, "sportmonks_player_id": None}
        for pid in {r["id"] for r in player_rows}
    }

    for row in player_rows:
        sm_id = row.get("sportmonks_player_id")
        if sm_id:
            stats[row["id"]]["sportmonks_player_id"] = int(sm_id)

    for event in fixture.get("events") or []:
        if event.get("type_id") not in GOAL_EVENT_TYPES:
            continue
        scorer_sm = event.get("player_id")
        assist_sm = event.get("related_player_id")
        if scorer_sm and int(scorer_sm) in sm_to_internal:
            stats[sm_to_internal[int(scorer_sm)]]["goals"] += 1
        elif event.get("player_name"):
            key = normalize_name(event["player_name"].split()[-1])
            if key in name_to_internal:
                stats[name_to_internal[key]]["goals"] += 1
        if assist_sm and int(assist_sm) in sm_to_internal:
            stats[sm_to_internal[int(assist_sm)]]["assists"] += 1
        elif event.get("related_player_name"):
            key = normalize_name(event["related_player_name"].split()[-1])
            if key in name_to_internal:
                stats[name_to_internal[key]]["assists"] += 1

    state_id = fixture.get("state_id") or (fixture.get("state") or {}).get("id")
    if state_id in FINISHED_STATE_IDS:
        for row in player_rows:
            pid = row["id"]
            if row["position"] not in ("GK", "DEF"):
                continue
            if team_matches(row["country"], home.get("name", "")):
                conceded = away_score
            elif team_matches(row["country"], away.get("name", "")):
                conceded = home_score
            else:
                continue
            if conceded == 0:
                stats[pid]["clean_sheet"] = True

    for sm_id, internal_id in sm_to_internal.items():
        if not stats[internal_id]["sportmonks_player_id"]:
            stats[internal_id]["sportmonks_player_id"] = sm_id

    return stats


def kickoff_date(kickoff_at: str) -> date:
    dt = datetime.fromisoformat(kickoff_at.replace("Z", "+00:00"))
    return dt.date()
