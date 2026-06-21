from __future__ import annotations
"""Poll sports APIs and sync scores, match state, and player stats into Supabase."""

import asyncio
import logging
from typing import Optional

import httpx

from app.config import settings
from app.database import get_supabase
from app.services.game_schedule import kickoff_date
from app.services.scoring import process_game_finished
from app.services.sportmonks import (
    SportmonksClient,
    FINISHED_STATE_IDS,
    HALFTIME_STATE_IDS,
    build_player_stats as build_sportmonks_player_stats,
    fixture_matches_game,
    fixture_summary,
    map_state,
    parse_scores as parse_sportmonks_scores,
)
from app.services.thestatsapi import (
    TheStatsApiClient,
    build_player_stats as build_thestats_player_stats,
    map_match_status,
    match_matches_game,
    match_summary,
    parse_scores as parse_thestats_scores,
)

logger = logging.getLogger(__name__)


def game_external_match_id(game: dict) -> Optional[str]:
    if game.get("external_match_id"):
        return str(game["external_match_id"])
    if game.get("sportmonks_fixture_id"):
        return str(game["sportmonks_fixture_id"])
    return None


def _game_needs_link(game: dict) -> bool:
    return not game_external_match_id(game)


# ── Sportmonks ──────────────────────────────────────────────────────────────


def _sportmonks_current_half(state_id: int, prev_state_id: Optional[int]) -> int:
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


async def _sync_sportmonks_game(game: dict, fixture: dict) -> None:
    db = get_supabase()
    state_id = fixture.get("state_id") or (fixture.get("state") or {}).get("id", 1)
    prev_state = game.get("sportmonks_last_state_id")
    prev_status = game["status"]

    home_score, away_score = parse_sportmonks_scores(fixture)
    status = map_state(state_id)
    current_half = _sportmonks_current_half(state_id, prev_state)

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
        stats = build_sportmonks_player_stats(fixture, players)
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


async def link_fixtures_sportmonks() -> dict:
    if not settings.sportmonks_enabled:
        return {
            "linked": {},
            "unlinked": [],
            "fixtures_by_date": {},
            "warnings": ["Sportmonks not configured — set SPORTS_API_PROVIDER=sportmonks"],
        }

    db = get_supabase()
    client = SportmonksClient()
    games = [g for g in db.table("games").select("*").execute().data if _game_needs_link(g)]
    linked: dict[str, str] = {}
    unlinked: list[dict] = []
    fixtures_by_date: dict[str, list[dict]] = {}
    warnings: list[str] = []

    async with httpx.AsyncClient() as http:
        dates_seen: dict[str, list[dict]] = {}
        for game in games:
            day = kickoff_date(game["kickoff_at"]).isoformat()
            if day not in dates_seen:
                fixtures, api_message = await client.get_fixtures_by_date(http, kickoff_date(game["kickoff_at"]))
                dates_seen[day] = fixtures
                fixtures_by_date[day] = [fixture_summary(f) for f in fixtures]
                if not fixtures and api_message:
                    warnings.append(f"{day} (league {client.league_id}): {api_message}")

            matched = False
            for fixture in dates_seen[day]:
                if fixture_matches_game(fixture, game["home_team"], game["away_team"]):
                    fixture_id = int(fixture["id"])
                    db.table("games").update({"sportmonks_fixture_id": fixture_id}).eq("id", game["id"]).execute()
                    linked[game["id"]] = str(fixture_id)
                    logger.info("Linked %s -> Sportmonks fixture %s", game["id"], fixture_id)
                    matched = True
                    break

            if not matched:
                unlinked.append(
                    {
                        "game_id": game["id"],
                        "home_team": game["home_team"],
                        "away_team": game["away_team"],
                        "kickoff_date": day,
                        "fixtures_on_date": len(dates_seen[day]),
                    }
                )

    if unlinked and not warnings:
        warnings.append(
            "Fixtures were returned but no team-name match. "
            "Browse GET /api/admin/sports/fixtures?date=YYYY-MM-DD then "
            "POST /api/admin/sports/link/{game_id} with the match_id."
        )

    return {
        "provider": "sportmonks",
        "linked": linked,
        "unlinked": unlinked,
        "fixtures_by_date": fixtures_by_date,
        "warnings": warnings,
        "subscription_hint": (
            "World Cup (league 732) requires a paid Sportmonks plan."
            if any("No result" in w or "don't have access" in w for w in warnings)
            else None
        ),
    }


async def sync_sportmonks() -> None:
    db = get_supabase()
    if any(_game_needs_link(g) for g in db.table("games").select("*").execute().data):
        await link_fixtures_sportmonks()

    games = [
        g
        for g in db.table("games").select("*").execute().data
        if game_external_match_id(g) and g.get("status") != "finished" and g.get("sportmonks_fixture_id")
    ]
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
                    await _sync_sportmonks_game(game, fixture)
            except httpx.HTTPStatusError as exc:
                logger.warning("Sportmonks HTTP error for game %s: %s", game["id"], exc.response.status_code)
            except Exception as exc:
                logger.warning("Failed to sync game %s: %s", game["id"], exc)


# ── TheStatsAPI ─────────────────────────────────────────────────────────────


async def _sync_thestats_game(game: dict, match: dict, live: dict, player_stats: list, timeline: list) -> None:
    db = get_supabase()
    prev_status = game["status"]
    live_meta = live.get("meta") if live else None
    status, current_half = map_match_status(match, live_meta)
    home_score, away_score = parse_thestats_scores(match, live_meta)

    db.table("games").update(
        {
            "home_score": home_score,
            "away_score": away_score,
            "status": status,
            "current_half": current_half,
        }
    ).eq("id", game["id"]).execute()

    players = db.table("players").select("*").eq("game_id", game["id"]).execute().data
    if players:
        stats = build_thestats_player_stats(match, players, player_stats, timeline, status)
        for pid, ps in stats.items():
            row_update = {
                "goals": ps["goals"],
                "assists": ps["assists"],
                "clean_sheet": ps["clean_sheet"],
            }
            if ps.get("external_player_id"):
                row_update["external_player_id"] = ps["external_player_id"]
            db.table("players").update(row_update).eq("id", pid).execute()

    if status == "finished" and prev_status != "finished":
        process_game_finished(game["id"])
        logger.info("Game %s finished — pick'em and captain points awarded", game["id"])


async def link_fixtures_thestatsapi() -> dict:
    if not settings.thestatsapi_enabled:
        return {
            "linked": {},
            "unlinked": [],
            "fixtures_by_date": {},
            "warnings": ["TheStatsAPI not configured — set SPORTS_API_PROVIDER=thestatsapi"],
        }

    db = get_supabase()
    client = TheStatsApiClient()
    games = [g for g in db.table("games").select("*").execute().data if _game_needs_link(g)]
    linked: dict[str, str] = {}
    unlinked: list[dict] = []
    fixtures_by_date: dict[str, list[dict]] = {}
    warnings: list[str] = []
    competition_id: Optional[str] = settings.thestatsapi_competition_id or None

    async with httpx.AsyncClient() as http:
        competition_id = await client.search_competition(http)
        if not competition_id:
            warnings.append("Could not find FIFA World Cup competition — set THESTATSAPI_COMPETITION_ID")

        dates_seen: dict[str, list[dict]] = {}
        for game in games:
            day = kickoff_date(game["kickoff_at"]).isoformat()
            if day not in dates_seen:
                matches, api_message = await client.get_matches_by_date(http, kickoff_date(game["kickoff_at"]), competition_id)
                dates_seen[day] = matches
                fixtures_by_date[day] = [match_summary(m) for m in matches]
                if api_message:
                    warnings.append(f"{day}: {api_message}")

            matched = False
            for match in dates_seen[day]:
                if match_matches_game(match, game["home_team"], game["away_team"]):
                    match_id = str(match["id"])
                    db.table("games").update({"external_match_id": match_id}).eq("id", game["id"]).execute()
                    linked[game["id"]] = match_id
                    logger.info("Linked %s -> TheStatsAPI match %s", game["id"], match_id)
                    matched = True
                    break

            if not matched:
                unlinked.append(
                    {
                        "game_id": game["id"],
                        "home_team": game["home_team"],
                        "away_team": game["away_team"],
                        "kickoff_date": day,
                        "fixtures_on_date": len(dates_seen[day]),
                    }
                )

    if unlinked and not warnings:
        warnings.append(
            "Matches were returned but no team-name match. "
            "Your watch-party fixtures may differ from the real World Cup schedule — "
            "link manually via POST /api/admin/sports/link/{game_id}."
        )

    return {
        "provider": "thestatsapi",
        "linked": linked,
        "unlinked": unlinked,
        "fixtures_by_date": fixtures_by_date,
        "warnings": warnings,
        "competition_id": competition_id,
    }


async def sync_thestatsapi() -> None:
    db = get_supabase()
    all_games = db.table("games").select("*").execute().data
    if any(_game_needs_link(g) for g in all_games):
        await link_fixtures_thestatsapi()

    games = [g for g in all_games if game_external_match_id(g) and g.get("status") != "finished"]
    if not games:
        return

    client = TheStatsApiClient()
    async with httpx.AsyncClient() as http:
        for game in games:
            match_id = game_external_match_id(game)
            if not match_id:
                continue
            try:
                match = await client.get_match(http, match_id)
                if not match:
                    continue
                live = await client.get_live_stats(http, match_id)
                player_stats = await client.get_player_stats(http, match_id)
                timeline = await client.get_timeline(http, match_id)
                await _sync_thestats_game(game, match, live, player_stats, timeline)
            except httpx.HTTPStatusError as exc:
                logger.warning("TheStatsAPI HTTP error for game %s: %s", game["id"], exc.response.status_code)
            except Exception as exc:
                logger.warning("Failed to sync game %s: %s", game["id"], exc)


# ── Public API ────────────────────────────────────────────────────────────────


async def link_fixtures() -> dict:
    if settings.thestatsapi_enabled:
        return await link_fixtures_thestatsapi()
    if settings.sportmonks_enabled:
        return await link_fixtures_sportmonks()
    return {
        "linked": {},
        "unlinked": [],
        "fixtures_by_date": {},
        "warnings": ["No sports provider configured — set SPORTS_API_KEY and SPORTS_API_PROVIDER"],
    }


def link_fixture_manual(game_id: str, match_id: str) -> dict:
    db = get_supabase()
    game = db.table("games").select("id").eq("id", game_id).execute().data
    if not game:
        raise ValueError(f"Game {game_id} not found")

    update: dict = {"external_match_id": match_id}
    if match_id.isdigit():
        update["sportmonks_fixture_id"] = int(match_id)

    db.table("games").update(update).eq("id", game_id).execute()
    return {"game_id": game_id, "external_match_id": match_id}


async def sync_match_statuses() -> None:
    if settings.thestatsapi_enabled:
        await sync_thestatsapi()
    elif settings.sportmonks_enabled:
        await sync_sportmonks()


async def run_sync_loop(interval_seconds: Optional[int] = None) -> None:
    interval = interval_seconds or settings.sports_sync_interval
    provider = settings.sports_api_provider
    logger.info("%s sync loop started (every %ss)", provider, interval)
    while True:
        try:
            await sync_match_statuses()
        except Exception as exc:
            logger.exception("%s sync loop error: %s", provider, exc)
        await asyncio.sleep(interval)
