from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_supabase
from app.deps import get_current_user
from app.models import GameResponse
from app.services.scoring import is_game_locked

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=list[GameResponse])
def list_games(user: dict = Depends(get_current_user)):
    db = get_supabase()
    games = db.table("games").select("*").order("sort_order").execute().data
    return [
        GameResponse(
            id=g["id"],
            home_team=g["home_team"],
            away_team=g["away_team"],
            home_flag=g["home_flag"],
            away_flag=g["away_flag"],
            kickoff_at=g["kickoff_at"],
            status=g["status"],
            home_score=g["home_score"],
            away_score=g["away_score"],
            current_half=g["current_half"],
            is_locked=is_game_locked(g["kickoff_at"]),
        )
        for g in games
    ]


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: str, user: dict = Depends(get_current_user)):
    db = get_supabase()
    result = db.table("games").select("*").eq("id", game_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Game not found")
    g = result.data[0]
    return GameResponse(
        id=g["id"],
        home_team=g["home_team"],
        away_team=g["away_team"],
        home_flag=g["home_flag"],
        away_flag=g["away_flag"],
        kickoff_at=g["kickoff_at"],
        status=g["status"],
        home_score=g["home_score"],
        away_score=g["away_score"],
        current_half=g["current_half"],
        is_locked=is_game_locked(g["kickoff_at"]),
    )
