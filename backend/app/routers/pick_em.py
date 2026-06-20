from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_supabase
from app.deps import get_current_user
from app.models import PickEmRequest, PickEmResponse
from app.services.scoring import is_game_locked

router = APIRouter(prefix="/pick-em", tags=["pick-em"])


@router.get("/{game_id}", response_model=Optional[PickEmResponse])
def get_prediction(game_id: str, user: dict = Depends(get_current_user)):
    db = get_supabase()
    game = db.table("games").select("kickoff_at").eq("id", game_id).execute()
    if not game.data:
        raise HTTPException(status_code=404, detail="Game not found")

    locked = is_game_locked(game.data[0]["kickoff_at"])
    pred = (
        db.table("pick_em_predictions")
        .select("*")
        .eq("user_email", user["email"])
        .eq("game_id", game_id)
        .execute()
        .data
    )
    if not pred:
        return None
    p = pred[0]
    return PickEmResponse(
        game_id=game_id,
        home_score=p["home_score"],
        away_score=p["away_score"],
        is_locked=locked,
    )


@router.put("/{game_id}", response_model=PickEmResponse)
def save_prediction(game_id: str, body: PickEmRequest, user: dict = Depends(get_current_user)):
    db = get_supabase()
    game = db.table("games").select("*").eq("id", game_id).execute()
    if not game.data:
        raise HTTPException(status_code=404, detail="Game not found")

    g = game.data[0]
    if is_game_locked(g["kickoff_at"]):
        raise HTTPException(status_code=403, detail="Predictions locked — match has started")

    db.table("pick_em_predictions").upsert(
        {
            "user_email": user["email"],
            "game_id": game_id,
            "home_score": body.home_score,
            "away_score": body.away_score,
        }
    ).execute()

    return PickEmResponse(
        game_id=game_id,
        home_score=body.home_score,
        away_score=body.away_score,
        is_locked=False,
    )
