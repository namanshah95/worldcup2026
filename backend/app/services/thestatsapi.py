from __future__ import annotations
"""TheStatsAPI client (https://api.thestatsapi.com)."""

import logging
import unicodedata
from datetime import date
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.thestatsapi.com/api"

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

GOAL_EVENT_TYPES = {"goal", "penalty_scored"}


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.lower())
    return "".join(c for c in text if not unicodedata.combining(c)).strip()


def team_matches(expected: str, actual: str) -> bool:
    expected_key = normalize_name(expected)
    actual_norm = normalize_name(actual)
    aliases = TEAM_ALIASES.get(expected_key, [expected_key])
    return any(alias in actual_norm or actual_norm in alias for alias in aliases)


def match_summary(match: dict) -> dict:
    home = match.get("home_team") or {}
    away = match.get("away_team") or {}
    return {
        "id": match.get("id"),
        "name": f"{home.get('name', '?')} vs {away.get('name', '?')}",
        "home": home.get("name"),
        "away": away.get("name"),
        "status": match.get("status"),
        "utc_date": match.get("utc_date"),
    }


def match_matches_game(match: dict, home_team: str, away_team: str) -> bool:
    home = (match.get("home_team") or {}).get("name", "")
    away = (match.get("away_team") or {}).get("name", "")
    if home and away:
        return team_matches(home_team, home) and team_matches(away_team, away)
    name = match.get("name") or ""
    return team_matches(home_team, name) and team_matches(away_team, name)


def parse_scores(match: dict, live_meta: Optional[dict] = None) -> tuple[int, int]:
    if live_meta:
        home = live_meta.get("home_goals")
        away = live_meta.get("away_goals")
        if home is not None and away is not None:
            return int(home), int(away)

    score = match.get("score") or {}
    home = score.get("home")
    away = score.get("away")
    if home is not None and away is not None:
        return int(home), int(away)

    final_score = score.get("final_score") or {}
    home = final_score.get("home")
    away = final_score.get("away")
    if home is not None and away is not None:
        return int(home), int(away)
    return 0, 0


def map_match_status(match: dict, live_meta: Optional[dict] = None) -> tuple[str, int]:
    """Return (internal status, current_half)."""
    if live_meta:
        match_status = (live_meta.get("match_status") or "").lower()
        period = (live_meta.get("period") or "").lower()
        if match_status == "halftime" or period == "halftime":
            return "halftime", 1
        if match_status in ("second_half", "extra_time", "penalties"):
            return "live", 2
        if match_status in ("first_half", "in_progress"):
            return "live", 1
        if match_status == "finished":
            return "finished", 2

    status = (match.get("status") or "scheduled").lower()
    if status == "finished":
        return "finished", 2
    if status == "live":
        return "live", 1
    return "scheduled", 1


class TheStatsApiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.sports_api_key

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _get(self, client: httpx.AsyncClient, path: str, **params: Any) -> dict:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        response = await client.get(url, headers=self._headers(), params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    async def search_competition(self, client: httpx.AsyncClient, query: str = "world cup") -> Optional[str]:
        if settings.thestatsapi_competition_id:
            return settings.thestatsapi_competition_id
        payload = await self._get(client, "/football/competitions", search=query, per_page=20)
        for comp in payload.get("data") or []:
            name = (comp.get("name") or "").lower()
            if "world cup" in name and "women" not in name:
                return comp.get("id")
        return None

    async def get_matches_by_date(
        self, client: httpx.AsyncClient, day: date, competition_id: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        comp_id = competition_id or settings.thestatsapi_competition_id
        params: dict[str, Any] = {
            "date_from": day.isoformat(),
            "date_to": day.isoformat(),
            "per_page": 100,
        }
        if comp_id:
            params["competition_id"] = comp_id
        if settings.thestatsapi_season_id:
            params["season_id"] = settings.thestatsapi_season_id

        try:
            payload = await self._get(client, "/football/matches", **params)
        except httpx.HTTPStatusError as exc:
            return [], exc.response.text

        return payload.get("data") or [], None

    async def get_matches_for_dates(
        self, client: httpx.AsyncClient, days: list[date], competition_id: Optional[str] = None
    ) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
        """Fetch matches for multiple days, deduped by match id."""
        merged: dict[str, dict] = {}
        by_date: dict[str, list[dict]] = {}
        warnings: list[str] = []

        for day in days:
            matches, api_message = await self.get_matches_by_date(client, day, competition_id)
            by_date[day.isoformat()] = matches
            if api_message:
                warnings.append(f"{day.isoformat()}: {api_message}")
            for match in matches:
                mid = str(match.get("id"))
                if mid:
                    merged[mid] = match

        return list(merged.values()), by_date, warnings

    async def get_match(self, client: httpx.AsyncClient, match_id: str) -> dict:
        payload = await self._get(client, f"/football/matches/{match_id}")
        return payload.get("data") or {}

    async def get_live_stats(self, client: httpx.AsyncClient, match_id: str) -> dict:
        try:
            payload = await self._get(client, f"/football/matches/{match_id}/live-stats")
            return payload.get("data") or {}
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (404, 409):
                return {}
            raise

    async def get_player_stats(self, client: httpx.AsyncClient, match_id: str) -> list[dict]:
        try:
            payload = await self._get(client, f"/football/matches/{match_id}/player-stats")
            return payload.get("data") or []
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (404, 409):
                return []
            raise

    async def get_timeline(self, client: httpx.AsyncClient, match_id: str) -> list[dict]:
        try:
            payload = await self._get(client, f"/football/matches/{match_id}/timeline")
            data = payload.get("data") or {}
            return data.get("events") or []
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (404, 409):
                return []
            raise


def build_player_stats(
    match: dict,
    player_rows: list[dict],
    player_stats: list[dict],
    timeline: list[dict],
    mapped_status: Optional[str] = None,
) -> dict[str, dict]:
    """Return captain stats keyed by internal player id."""
    home = (match.get("home_team") or {}).get("name", "")
    away = (match.get("away_team") or {}).get("name", "")
    home_score, away_score = parse_scores(match)

    id_to_internal: dict[str, str] = {}
    name_to_internal: dict[str, str] = {}
    for row in player_rows:
        ext_id = row.get("external_player_id")
        if ext_id:
            id_to_internal[str(ext_id)] = row["id"]
        name_to_internal[normalize_name(row["name"])] = row["id"]

    stats: dict[str, dict] = {
        pid: {"goals": 0, "assists": 0, "clean_sheet": False, "external_player_id": None}
        for pid in {r["id"] for r in player_rows}
    }

    for ps in player_stats:
        ext_id = ps.get("player_id")
        if not ext_id:
            continue
        internal = id_to_internal.get(str(ext_id))
        if not internal:
            player_name = ps.get("player_name") or ""
            key = normalize_name(player_name.split()[-1]) if player_name else ""
            internal = name_to_internal.get(key) or name_to_internal.get(normalize_name(player_name))
        if not internal:
            continue

        shooting = ps.get("shooting") or {}
        passing = ps.get("passing") or {}
        stats[internal]["goals"] = int(shooting.get("goals") or 0)
        stats[internal]["assists"] = int(passing.get("assists") or 0)
        stats[internal]["external_player_id"] = str(ext_id)

    # Fallback: timeline goals when player-stats not yet published
    if not player_stats and timeline:
        for event in timeline:
            if event.get("type") not in GOAL_EVENT_TYPES:
                continue
            player = event.get("player") or {}
            ext_id = player.get("id")
            name = player.get("name") or ""
            internal = None
            if ext_id and str(ext_id) in id_to_internal:
                internal = id_to_internal[str(ext_id)]
            elif name:
                key = normalize_name(name.split()[-1])
                internal = name_to_internal.get(key)
            if internal:
                stats[internal]["goals"] += 1
                if ext_id:
                    stats[internal]["external_player_id"] = str(ext_id)

    status = mapped_status or (match.get("status") or "").lower()
    if status == "finished":
        for row in player_rows:
            pid = row["id"]
            if row["position"] not in ("GK", "DEF"):
                continue
            if team_matches(row["country"], home):
                conceded = away_score
            elif team_matches(row["country"], away):
                conceded = home_score
            else:
                continue
            if conceded == 0:
                stats[pid]["clean_sheet"] = True

    return stats
