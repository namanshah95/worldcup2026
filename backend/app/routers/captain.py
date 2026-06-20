from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_supabase
from app.deps import get_current_user
from app.models import CaptainResponse, CaptainSelectRequest, PlayerResponse, ScoreEventResponse
from app.services.scoring import is_game_locked

router = APIRouter(prefix="/captain", tags=["captain"])


def _player_response(p: dict) -> PlayerResponse:
    locked = is_game_locked(
        get_supabase().table("games").select("kickoff_at").eq("id", p["game_id"]).single().execute().data["kickoff_at"]
    )
    return PlayerResponse(
        id=p["id"],
        name=p["name"],
        country=p["country"],
        position=p["position"],
        game_id=p["game_id"],
        previous_opponent=p.get("previous_opponent"),
        previous_points=p.get("previous_points", 0),
        goals=p.get("goals", 0),
        assists=p.get("assists", 0),
        clean_sheet=p.get("clean_sheet", False),
        unavailable=p.get("unavailable", False),
        is_selectable=not locked and not p.get("unavailable", False),
    )


@router.get("/players", response_model=list[PlayerResponse])
def list_players(
    user: dict = Depends(get_current_user),
    country: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
):
    db = get_supabase()
    query = db.table("players").select("*")
    if country:
        query = query.eq("country", country)
    if position:
        query = query.eq("position", position)
    players = query.execute().data

    if search:
        search_lower = search.lower()
        players = [p for p in players if p["name"].lower().startswith(search_lower)]

    games = {g["id"]: g for g in db.table("games").select("*").execute().data}

    def sort_key(p):
        if sort_by == "country":
            return p["country"]
        if sort_by == "position":
            return p["position"]
        if sort_by == "previous_points":
            return -p.get("previous_points", 0)
        return p["name"]

    players.sort(key=sort_key)
    result = []
    for p in players:
        game = games.get(p["game_id"], {})
        kickoff = game.get("kickoff_at", "2099-01-01")
        locked = is_game_locked(kickoff)
        result.append(
            PlayerResponse(
                id=p["id"],
                name=p["name"],
                country=p["country"],
                position=p["position"],
                game_id=p["game_id"],
                previous_opponent=p.get("previous_opponent"),
                previous_points=p.get("previous_points", 0),
                goals=p.get("goals", 0),
                assists=p.get("assists", 0),
                clean_sheet=p.get("clean_sheet", False),
                unavailable=p.get("unavailable", False) or locked,
                is_selectable=not locked and not p.get("unavailable", False),
            )
        )
    return result


@router.get("/selection", response_model=CaptainResponse)
def get_selection(user: dict = Depends(get_current_user)):
    db = get_supabase()
    sel = db.table("captain_selections").select("*").eq("user_email", user["email"]).execute().data
    if not sel:
        return CaptainResponse(player=None, score_events=[], is_locked=False)

    player_data = db.table("players").select("*").eq("id", sel[0]["player_id"]).single().execute().data
    game = db.table("games").select("kickoff_at").eq("id", player_data["game_id"]).single().execute().data

    events = (
        db.table("score_events")
        .select("*")
        .eq("user_email", user["email"])
        .eq("source", "Captain")
        .order("created_at")
        .execute()
        .data
    )

    return CaptainResponse(
        player=PlayerResponse(
            id=player_data["id"],
            name=player_data["name"],
            country=player_data["country"],
            position=player_data["position"],
            game_id=player_data["game_id"],
            previous_opponent=player_data.get("previous_opponent"),
            previous_points=player_data.get("previous_points", 0),
            goals=player_data.get("goals", 0),
            assists=player_data.get("assists", 0),
            clean_sheet=player_data.get("clean_sheet", False),
            unavailable=False,
            is_selectable=False,
        ),
        score_events=[ScoreEventResponse(**e) for e in events],
        is_locked=True,
    )


@router.post("/select", response_model=CaptainResponse)
def select_captain(body: CaptainSelectRequest, user: dict = Depends(get_current_user)):
    db = get_supabase()
    existing = db.table("captain_selections").select("*").eq("user_email", user["email"]).execute().data
    if existing:
        raise HTTPException(status_code=403, detail="Captain already selected — cannot change")

    player = db.table("players").select("*").eq("id", body.player_id).execute().data
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    p = player[0]

    game = db.table("games").select("kickoff_at").eq("id", p["game_id"]).single().execute().data
    if is_game_locked(game["kickoff_at"]):
        raise HTTPException(status_code=403, detail="Cannot select — player's game has started")
    if p.get("unavailable"):
        raise HTTPException(status_code=403, detail="Player unavailable")

    db.table("captain_selections").insert(
        {"user_email": user["email"], "player_id": body.player_id}
    ).execute()

    return CaptainResponse(
        player=PlayerResponse(
            id=p["id"],
            name=p["name"],
            country=p["country"],
            position=p["position"],
            game_id=p["game_id"],
            previous_opponent=p.get("previous_opponent"),
            previous_points=p.get("previous_points", 0),
            goals=p.get("goals", 0),
            assists=p.get("assists", 0),
            clean_sheet=p.get("clean_sheet", False),
            unavailable=False,
            is_selectable=False,
        ),
        score_events=[],
        is_locked=True,
    )
