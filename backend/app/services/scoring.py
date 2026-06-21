from __future__ import annotations
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import settings
from app.database import get_supabase

BINGO_WIN_LINES = [
    [0, 1, 2, 3, 4],
    [5, 6, 7, 8, 9],
    [10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19],
    [20, 21, 22, 23, 24],
    [0, 5, 10, 15, 20],
    [1, 6, 11, 16, 21],
    [2, 7, 12, 17, 22],
    [3, 8, 13, 18, 23],
    [4, 9, 14, 19, 24],
    [0, 6, 12, 18, 24],
    [4, 8, 12, 16, 20],
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def get_session_expiry() -> datetime:
    return utcnow() + timedelta(hours=settings.session_expire_hours)


def is_game_locked(kickoff_at: str) -> bool:
    from app.services.game_schedule import is_game_locked as _is_game_locked

    return _is_game_locked(kickoff_at, utcnow())


def generate_bingo_board(event_ids: list[int]) -> list[int]:
    """Generate 25-cell board: index 12 is free space (-1)."""
    chosen = random.sample(event_ids, 24)
    board = chosen[:12] + [-1] + chosen[12:]
    return board


def check_bingo(marks: set[int]) -> bool:
    return any(all(i in marks for i in line) for line in BINGO_WIN_LINES)


def add_score_event(
    user_email: str,
    source: str,
    description: str,
    points: int,
    game_id: Optional[str] = None,
) -> None:
    db = get_supabase()
    db.table("score_events").insert(
        {
            "user_email": user_email,
            "source": source,
            "description": description,
            "points": points,
            "game_id": game_id,
        }
    ).execute()


def score_pick_em(user_email: str, game: dict, prediction: dict) -> None:
    home_pred = prediction["home_score"]
    away_pred = prediction["away_score"]
    home_actual = game["home_score"]
    away_actual = game["away_score"]
    game_id = game["id"]
    label = f"{game['home_team']} vs {game['away_team']}"

    pred_winner = "home" if home_pred > away_pred else ("away" if away_pred > home_pred else "draw")
    actual_winner = "home" if home_actual > away_actual else ("away" if away_actual > home_actual else "draw")

    if pred_winner == actual_winner:
        add_score_event(user_email, "Pick'ems", f"{label}: Correct winner", 5, game_id)

    sides = 0
    if home_pred == home_actual:
        sides += 1
    if away_pred == away_actual:
        sides += 1
    if sides:
        add_score_event(user_email, "Pick'ems", f"{label}: {sides} correct score side(s)", sides * 3, game_id)

    if home_pred == home_actual and away_pred == away_actual:
        add_score_event(user_email, "Pick'ems", f"{label}: Exact score!", 4, game_id)


def score_captain_for_game(game_id: str) -> None:
    db = get_supabase()
    game = db.table("games").select("*").eq("id", game_id).single().execute().data
    players = db.table("players").select("*").eq("game_id", game_id).execute().data
    player_map = {p["id"]: p for p in players}

    selections = db.table("captain_selections").select("*").execute().data
    for sel in selections:
        player = player_map.get(sel["player_id"])
        if not player:
            continue
        email = sel["user_email"]
        name = player["name"]
        if player["goals"] > 0:
            add_score_event(email, "Captain", f"{name}: {player['goals']} goal(s)", player["goals"] * 10, game_id)
        if player["assists"] > 0:
            add_score_event(email, "Captain", f"{name}: {player['assists']} assist(s)", player["assists"] * 5, game_id)
        if player["clean_sheet"] and player["position"] in ("GK", "DEF"):
            add_score_event(email, "Captain", f"{name}: Clean sheet", 8, game_id)


def score_all_pick_ems_for_game(game_id: str, *, replace: bool = False) -> None:
    db = get_supabase()
    game = db.table("games").select("*").eq("id", game_id).single().execute().data
    if game.get("status") != "finished":
        return

    predictions = db.table("pick_em_predictions").select("*").eq("game_id", game_id).execute().data

    existing = (
        db.table("score_events")
        .select("id")
        .eq("game_id", game_id)
        .eq("source", "Pick'ems")
        .limit(1)
        .execute()
        .data
    )
    if existing and not replace:
        return
    if existing and replace:
        db.table("score_events").delete().eq("game_id", game_id).eq("source", "Pick'ems").execute()

    for pred in predictions:
        score_pick_em(pred["user_email"], game, pred)


def rescore_pick_ems_for_game(game_id: str) -> None:
    """Re-award pick'em points from current final scores (fixes bad first-pass scoring)."""
    score_all_pick_ems_for_game(game_id, replace=True)


def process_game_finished(game_id: str) -> None:
    score_all_pick_ems_for_game(game_id)
    score_captain_for_game(game_id)


def award_bingo(user_email: str, is_first: bool) -> None:
    points = 20 if is_first else 10
    label = "First bingo!" if is_first else "Bingo completed"
    add_score_event(user_email, "Bingo", label, points)


def award_trivia_perfect_bonus(user_email: str, game_id: str) -> None:
    add_score_event(user_email, "Trivia", "Perfect 5 bonus", 5, game_id)
