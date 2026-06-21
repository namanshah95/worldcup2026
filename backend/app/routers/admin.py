from __future__ import annotations
from datetime import date

import httpx
from fastapi import APIRouter, Header, HTTPException, Query

from app.config import settings
from app.database import get_supabase
from app.models import (
    AdminLinkFixtureRequest,
    AdminPlayerStatsRequest,
    AdminResetUserRequest,
    AdminResetUserResponse,
    AdminUpdateScoreRequest,
)
from app.services.scoring import process_game_finished
from app.services.sportmonks import SportmonksClient, fixture_summary
from app.services.sports_sync import link_fixture_manual, link_fixtures, sync_match_statuses
from app.services.thestatsapi import TheStatsApiClient, match_summary
from app.services.user_admin import reset_user_by_email

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin(x_admin_secret: str = Header(...)):
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Unauthorized")


def _require_sports_sync():
    if not settings.sports_sync_enabled:
        raise HTTPException(
            status_code=400,
            detail="Sports sync not configured — set SPORTS_API_KEY and SPORTS_API_PROVIDER",
        )


@router.patch("/games/{game_id}")
def update_game(game_id: str, body: AdminUpdateScoreRequest, x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    db = get_supabase()
    prev = db.table("games").select("status").eq("id", game_id).single().execute().data

    db.table("games").update(
        {
            "home_score": body.home_score,
            "away_score": body.away_score,
            "status": body.status,
            "current_half": body.current_half,
        }
    ).eq("id", game_id).execute()

    if body.status == "finished" and prev.get("status") != "finished":
        process_game_finished(game_id)

    return {"ok": True}


@router.patch("/players/{player_id}")
def update_player_stats(player_id: str, body: AdminPlayerStatsRequest, x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    db = get_supabase()
    db.table("players").update(
        {"goals": body.goals, "assists": body.assists, "clean_sheet": body.clean_sheet}
    ).eq("id", player_id).execute()
    return {"ok": True}


@router.get("/attendance-qr/{game_id}")
def get_attendance_qr_payload(game_id: str, x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    db = get_supabase()
    game = db.table("games").select("id, attendance_qr_secret, home_team, away_team").eq("id", game_id).single().execute().data
    payload = f"wc26-attendance:{game['id']}:{game['attendance_qr_secret']}"
    return {"payload": payload, "game": f"{game['home_team']} vs {game['away_team']}"}


# ── Sports sync (TheStatsAPI / Sportmonks) ────────────────────────────────────


@router.post("/sports/link")
async def sports_link(x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    _require_sports_sync()
    return await link_fixtures()


@router.post("/sports/link/{game_id}")
async def sports_link_game(
    game_id: str,
    body: AdminLinkFixtureRequest,
    x_admin_secret: str = Header(...),
):
    verify_admin(x_admin_secret)
    try:
        return link_fixture_manual(game_id, body.match_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sports/fixtures")
async def sports_browse_fixtures(
    date: date = Query(..., description="Kickoff date (YYYY-MM-DD)"),
    x_admin_secret: str = Header(...),
):
    verify_admin(x_admin_secret)
    _require_sports_sync()

    async with httpx.AsyncClient() as http:
        if settings.thestatsapi_enabled:
            client = TheStatsApiClient()
            competition_id = await client.search_competition(http)
            matches, api_message = await client.get_matches_by_date(http, date, competition_id)
            return {
                "provider": "thestatsapi",
                "date": date.isoformat(),
                "competition_id": competition_id,
                "fixtures": [match_summary(m) for m in matches],
                "api_message": api_message,
            }

        client = SportmonksClient()
        result = await client.list_fixtures_for_date(http, date)
        return {
            "provider": "sportmonks",
            "date": date.isoformat(),
            "league_id": settings.sportmonks_league_id,
            "fixtures": [fixture_summary(f) for f in result["fixtures"]],
            "api_message": result.get("api_message"),
            "unfiltered_count": result.get("unfiltered_count"),
        }


@router.post("/sports/sync")
async def sports_sync(x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    _require_sports_sync()
    await sync_match_statuses()
    db = get_supabase()
    games = (
        db.table("games")
        .select("id, home_team, away_team, status, home_score, away_score, external_match_id, sportmonks_fixture_id")
        .execute()
        .data
    )
    return {"provider": settings.sports_api_provider, "games": games}


# Legacy Sportmonks routes (aliases)
@router.post("/sportmonks/link")
async def sportmonks_link(x_admin_secret: str = Header(...)):
    return await sports_link(x_admin_secret)


@router.post("/sportmonks/link/{game_id}")
async def sportmonks_link_game(
    game_id: str,
    body: AdminLinkFixtureRequest,
    x_admin_secret: str = Header(...),
):
    return await sports_link_game(game_id, body, x_admin_secret)


@router.get("/sportmonks/fixtures")
async def sportmonks_browse_fixtures(
    date: date = Query(..., description="Kickoff date (YYYY-MM-DD)"),
    x_admin_secret: str = Header(...),
):
    return await sports_browse_fixtures(date, x_admin_secret)


@router.post("/sportmonks/sync")
async def sportmonks_sync(x_admin_secret: str = Header(...)):
    return await sports_sync(x_admin_secret)


@router.post("/users/reset", response_model=AdminResetUserResponse)
def reset_user(body: AdminResetUserRequest, x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    result = reset_user_by_email(body.email)
    return AdminResetUserResponse(**result)
