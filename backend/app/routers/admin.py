from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from app.config import settings
from app.database import get_supabase
from app.models import (
    AdminPlayerStatsRequest,
    AdminResetUserRequest,
    AdminResetUserResponse,
    AdminUpdateScoreRequest,
)
from app.services.scoring import process_game_finished
from app.services.sports_sync import link_fixtures, sync_match_statuses
from app.services.user_admin import reset_user_by_email

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin(x_admin_secret: str = Header(...)):
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Unauthorized")


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


@router.post("/sportmonks/link")
async def sportmonks_link(x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    if not settings.sportmonks_enabled:
        raise HTTPException(status_code=400, detail="Sportmonks not configured — set SPORTS_API_KEY")
    linked = await link_fixtures()
    return {"linked": linked}


@router.post("/sportmonks/sync")
async def sportmonks_sync(x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    if not settings.sportmonks_enabled:
        raise HTTPException(status_code=400, detail="Sportmonks not configured — set SPORTS_API_KEY")
    await sync_match_statuses()
    db = get_supabase()
    games = db.table("games").select("id, home_team, away_team, status, home_score, away_score, sportmonks_fixture_id").execute().data
    return {"games": games}


@router.post("/users/reset", response_model=AdminResetUserResponse)
def reset_user(body: AdminResetUserRequest, x_admin_secret: str = Header(...)):
    verify_admin(x_admin_secret)
    result = reset_user_by_email(body.email)
    return AdminResetUserResponse(**result)
