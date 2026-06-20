from __future__ import annotations
"""Poll Sportmonks and sync scores, match state, and player stats into Supabase."""

import asyncio
import logging
from typing import Optional

import httpx

from app.config import settings
from app.database import get_supabase
from app.services.scoring import process_game_finished
from app.services.sportmonks import (
    SportmonksClient,
    FINISHED_STATE_IDS,
    HALFTIME_STATE_IDS,
    build_player_stats,
    fixture_matches_game,
    kickoff_date,
    map_state,
    parse_scores,
)

logger = logging.getLogger(__name__)


async def link_fixtures() -> dict[str, int]:
    """Match internal games to Sportmonks fixture IDs by date + team names."""
    if not settings.sportmonks_enabled:
        return {}

    db = get_supabase()
    client = SportmonksClient()
    games = db.table("games").select("*").is_("sportmonks_fixture_id", "null").execute().data
    linked: dict[str, int] = {}

    async with httpx.AsyncClient() as http:
        dates_seen: dict[str, list] = {}
        for game in games:
            day = kickoff_date(game["kickoff_at"]).isoformat()
            if day not in dates_seen:
                dates_seen[day] = await client.get_fixtures_by_date(http, kickoff_date(game["kickoff_at"]))

            for fixture in dates_seen[day]:
                if fixture_matches_game(fixture, game["home_team"], game["away_team"]):
                    fixture_id = int(fixture["id"])
                    db.table("games").update({"sportmonks_fixture_id": fixture_id}).eq("id", game["id"]).execute()
                    linked[game["id"]] = fixture_id
                    logger.info("Linked %s -> Sportmonks fixture %s", game["id"], fixture_id)
                    break

    return linked


def _current_half(state_id: int, prev_state_id: Optional[int]) -> int:
    if state_id == 21:
        return 2
    if state_id in HALFTIME_STATE_IDS:
        return 1
    if state_id == 22:
        return 2
    if state_id == 2:
        return 1
    if state_id in FINISHED_STATE_IDS:
        return 2
    return 1


async def sync_game(game: dict, fixture: dict) -> None:
    db = get_supabase()
    state_id = fixture.get("state_id") or (fixture.get("state") or {}).get("id", 1)
    prev_state = game.get("sportmonks_last_state_id")
    prev_status = game["status"]

    home_score, away_score = parse_scores(fixture)
    status = map_state(state_id)
    current_half = _current_half(state_id, prev_state)

    if state_id in HALFTIME_STATE_IDS:
        status = "halftime"

    db.table("games").update(
        {
            "home_score": home_score,
            "away_score": away_score,
            "status": status,
            "current_half": current_half,
            "sportmonks_last_state_id": state_id,
        }
    ).eq("id", game["id"]).execute()

    players = db.table("players").select("*").eq("game_id", game["id"]).execute().data
    if players:
        stats = build_player_stats(fixture, players)
        for pid, ps in stats.items():
            row_update = {
                "goals": ps["goals"],
                "assists": ps["assists"],
                "clean_sheet": ps["clean_sheet"],
            }
            if ps.get("sportmonks_player_id"):
                row_update["sportmonks_player_id"] = ps["sportmonks_player_id"]
            db.table("players").update(row_update).eq("id", pid).execute()

    if status == "finished" and prev_status != "finished":
        process_game_finished(game["id"])
        logger.info("Game %s finished — pick'em and captain points awarded", game["id"])


async def sync_match_statuses() -> None:
    if not settings.sportmonks_enabled:
        return

    db = get_supabase()
    if db.table("games").select("id").is_("sportmonks_fixture_id", "null").execute().data:
        await link_fixtures()

    games = (
        db.table("games")
        .select("*")
        .not_.is_("sportmonks_fixture_id", "null")
        .neq("status", "finished")
        .execute()
        .data
    )

    if not games:
        return

    sm = SportmonksClient()
    async with httpx.AsyncClient() as http:
        for game in games:
            fixture_id = game.get("sportmonks_fixture_id")
            if not fixture_id:
                continue
            try:
                fixture = await sm.get_fixture(http, int(fixture_id))
                if fixture:
                    await sync_game(game, fixture)
            except httpx.HTTPStatusError as exc:
                logger.warning("Sportmonks HTTP error for game %s: %s", game["id"], exc.response.status_code)
            except Exception as exc:
                logger.warning("Failed to sync game %s: %s", game["id"], exc)


async def run_sync_loop(interval_seconds: Optional[int] = None) -> None:
    interval = interval_seconds or settings.sports_sync_interval
    logger.info("Sportmonks sync loop started (every %ss)", interval)
    while True:
        try:
            await sync_match_statuses()
        except Exception as exc:
            logger.exception("Sportmonks sync loop error: %s", exc)
        await asyncio.sleep(interval)
