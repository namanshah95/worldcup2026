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


def match_player_name(roster_name: str, api_name: str) -> bool:
    """Match roster short names (e.g. Yamal) to API display names (e.g. Lamine Yamal)."""
    roster = normalize_name(roster_name)
    api = normalize_name(api_name)
    if not roster or not api:
        return False
    if roster == api or roster in api or api.endswith(f" {roster}"):
        return True
    roster_last = roster.split()[-1]
    api_last = api.split()[-1]
    return len(roster_last) >= 3 and roster_last == api_last


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
    ) -> tuple[list[dict], Optional[str]]:
        payload = await self._get(
            client,
            f"fixtures/date/{day.isoformat()}",
            include=include,
            filters=f"fixtureLeagues:{self.league_id}",
        )
        return payload.get("data") or [], payload.get("message")

    async def list_fixtures_for_date(
        self, client: httpx.AsyncClient, day: date, include: str = "participants;state"
    ) -> dict:
        """Fetch fixtures with or without league filter (broader search for debugging)."""
        with_filter, msg_filtered = await self.get_fixtures_by_date(client, day, include=include)
        if with_filter:
            return {"fixtures": with_filter, "api_message": msg_filtered, "league_id": self.league_id}

        without_filter_payload = await self._get(
            client,
            f"fixtures/date/{day.isoformat()}",
            include=include,
        )
        all_fixtures = without_filter_payload.get("data") or []
        return {
            "fixtures": all_fixtures,
            "api_message": without_filter_payload.get("message") or msg_filtered,
            "league_id": self.league_id,
            "filtered_count": 0,
            "unfiltered_count": len(all_fixtures),
        }

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


def parse_scores(fixture: dict) -> Optional[tuple[int, int]]:
    home, away = extract_participants(fixture)
    if not home or not away:
        return None

    home_id = str(home["id"])
    away_id = str(away["id"])
    preferred = ("CURRENT", "2ND_HALF", "2ND HALF")

    def normalize_desc(value: str) -> str:
        return (value or "").upper().replace(" ", "_")

    def parse_description(target_desc: str) -> Optional[tuple[int, int]]:
        target = normalize_desc(target_desc)
        home_score: Optional[int] = None
        away_score: Optional[int] = None
        for entry in fixture.get("scores") or []:
            if normalize_desc(entry.get("description") or "") != target:
                continue
            score_obj = entry.get("score") or {}
            goals = score_obj.get("goals")
            if goals is None:
                continue
            goals = int(goals)
            participant = (score_obj.get("participant") or "").lower()
            participant_id = entry.get("participant_id")
            pid = str(participant_id) if participant_id is not None else None

            if participant == "home" or pid == home_id:
                home_score = goals
            elif participant == "away" or pid == away_id:
                away_score = goals

        if home_score is None or away_score is None:
            return None
        return home_score, away_score

    for desc in preferred:
        parsed = parse_description(desc)
        if parsed is not None:
            return parsed
    return None


def map_state(state_id: int) -> str:
    return STATE_TO_STATUS.get(state_id, "live")


def build_player_stats(fixture: dict, player_rows: list[dict]) -> dict[str, dict]:
    """Return stats keyed by internal player id."""
    home, away = extract_participants(fixture)
    if not home or not away:
        return {}

    home_id = home["id"]
    away_id = away["id"]
    parsed = parse_scores(fixture)
    home_score, away_score = parsed if parsed is not None else (0, 0)

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
            for row in player_rows:
                if match_player_name(row["name"], event["player_name"]):
                    stats[row["id"]]["goals"] += 1
                    break
        if assist_sm and int(assist_sm) in sm_to_internal:
            stats[sm_to_internal[int(assist_sm)]]["assists"] += 1
        elif event.get("related_player_name"):
            for row in player_rows:
                if match_player_name(row["name"], event["related_player_name"]):
                    stats[row["id"]]["assists"] += 1
                    break

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


def fixture_summary(fixture: dict) -> dict:
    home, away = extract_participants(fixture)
    return {
        "id": fixture.get("id"),
        "name": fixture.get("name"),
        "home": (home or {}).get("name"),
        "away": (away or {}).get("name"),
        "state_id": fixture.get("state_id") or (fixture.get("state") or {}).get("id"),
    }
