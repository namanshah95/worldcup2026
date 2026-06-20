from __future__ import annotations
from fastapi import APIRouter, Depends

from app.database import get_supabase
from app.deps import get_current_user
from app.models import LeaderboardEntry, ScoreEventResponse, ScoringResponse, SCORING_RULES

router = APIRouter(tags=["scores"])


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(user: dict = Depends(get_current_user)):
    db = get_supabase()
    rows = db.rpc("get_leaderboard").execute().data if False else None

    users = db.table("users").select("email, display_name").execute().data
    entries = []
    for u in users:
        events = (
            db.table("score_events")
            .select("points")
            .eq("user_email", u["email"])
            .execute()
            .data
        )
        total = sum(e["points"] for e in events)
        entries.append({"email": u["email"], "display_name": u["display_name"], "total_points": total})

    entries.sort(key=lambda x: (-x["total_points"], x["display_name"]))
    return [
        LeaderboardEntry(
            email=e["email"],
            display_name=e["display_name"],
            total_points=e["total_points"],
            rank=i + 1,
        )
        for i, e in enumerate(entries)
    ]


@router.get("/scoring", response_model=ScoringResponse)
def my_scoring(user: dict = Depends(get_current_user)):
    db = get_supabase()
    events = (
        db.table("score_events")
        .select("*")
        .eq("user_email", user["email"])
        .order("created_at")
        .execute()
        .data
    )
    total = sum(e["points"] for e in events)
    return ScoringResponse(
        total_points=total,
        events=[ScoreEventResponse(**e) for e in events],
        rules=SCORING_RULES,
    )
