from __future__ import annotations
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_supabase
from app.deps import get_current_user
from app.models import TriviaAnswerRequest, TriviaQuestionResponse, TriviaSessionResponse
from app.services.scoring import add_score_event, award_trivia_perfect_bonus

router = APIRouter(prefix="/trivia", tags=["trivia"])


def _game_label(game: dict) -> str:
    return f"{game['home_team']} vs {game['away_team']}"


def _format_kickoff(kickoff_at: str) -> str:
    dt = datetime.fromisoformat(kickoff_at.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%I:%M %p").lstrip("0")


def _build_session(game: dict, user: dict, is_active: bool, message: str) -> TriviaSessionResponse:
    half = game.get("current_half") or 1
    questions_data = (
        get_supabase()
        .table("trivia_questions")
        .select("*")
        .eq("game_id", game["id"])
        .eq("half_number", half)
        .order("sort_order")
        .execute()
        .data
        if is_active
        else []
    )

    answers = (
        get_supabase()
        .table("trivia_answers")
        .select("*")
        .eq("user_email", user["email"])
        .in_("question_id", [q["id"] for q in questions_data] if questions_data else [-1])
        .execute()
        .data
    )
    answer_map = {a["question_id"]: a for a in answers}

    return TriviaSessionResponse(
        is_active=is_active,
        game_id=game["id"],
        game_label=_game_label(game),
        half_number=half,
        message=message,
        questions=[
            TriviaQuestionResponse(
                id=q["id"],
                question=q["question"],
                options=q["options"],
                sort_order=q["sort_order"],
                answered=q["id"] in answer_map,
                selected_index=answer_map[q["id"]]["selected_index"] if q["id"] in answer_map else None,
                is_correct=answer_map[q["id"]]["is_correct"] if q["id"] in answer_map else None,
            )
            for q in questions_data
        ],
    )


def _waiting_message(games: list[dict]) -> tuple[dict, str]:
    """Pick a reference game and message for the trivia splash screen."""
    halftime = [g for g in games if g["status"] == "halftime"]
    if halftime:
        game = halftime[0]
        return game, f"Half-time trivia for {_game_label(game)} is live! Head to the trivia screen now."

    live = [g for g in games if g["status"] == "live"]
    if live:
        game = live[0]
        return game, f"Trivia unlocks at half-time of {_game_label(game)}. Check back during the break!"

    upcoming = [g for g in games if g["status"] == "scheduled"]
    if upcoming:
        game = upcoming[0]
        time_str = _format_kickoff(game["kickoff_at"])
        return (
            game,
            f"Next trivia opens at half-time of {_game_label(game)} (kickoff {time_str}).",
        )

    finished = [g for g in games if g["status"] == "finished"]
    if finished and len(finished) == len(games):
        return finished[-1], "All matches are complete. Thanks for playing!"

    return games[0] if games else {"id": "", "home_team": "", "away_team": "", "current_half": 1}, "Trivia unlocks at the next half-time break."


@router.get("/session", response_model=TriviaSessionResponse)
def get_trivia_session(user: dict = Depends(get_current_user)):
    db = get_supabase()
    games = db.table("games").select("*").order("sort_order").execute().data

    halftime = [g for g in games if g["status"] == "halftime"]
    if halftime:
        game = halftime[0]
        return _build_session(
            game,
            user,
            True,
            f"Half-time trivia is live for {_game_label(game)}! Answer before the 2nd half kicks off.",
        )

    ref_game, message = _waiting_message(games)
    return _build_session(ref_game, user, False, message)


@router.get("/{game_id}", response_model=TriviaSessionResponse)
def get_trivia(game_id: str, user: dict = Depends(get_current_user)):
    db = get_supabase()
    game = db.table("games").select("*").eq("id", game_id).execute().data
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    game = game[0]

    is_active = game["status"] == "halftime"
    if not is_active:
        next_label = "1st half-time" if game["status"] in ("scheduled", "live") else "next half-time"
        return _build_session(
            game,
            user,
            False,
            f"Trivia unlocks at {next_label}. Check back during the break!",
        )

    return _build_session(
        game,
        user,
        True,
        "Half-time trivia is live! You have until the 2nd half kicks off.",
    )


@router.post("/{game_id}/answer")
def submit_answer(game_id: str, body: TriviaAnswerRequest, user: dict = Depends(get_current_user)):
    db = get_supabase()
    game = db.table("games").select("*").eq("id", game_id).single().execute().data
    if game["status"] != "halftime":
        raise HTTPException(status_code=403, detail="Trivia is only available during half-time")

    question = db.table("trivia_questions").select("*").eq("id", body.question_id).single().execute().data
    if question["game_id"] != game_id:
        raise HTTPException(status_code=400, detail="Question does not belong to this game")

    existing = (
        db.table("trivia_answers")
        .select("*")
        .eq("user_email", user["email"])
        .eq("question_id", body.question_id)
        .execute()
        .data
    )
    if existing:
        raise HTTPException(status_code=403, detail="Already answered")

    is_correct = body.selected_index == question["correct_index"]
    db.table("trivia_answers").insert(
        {
            "user_email": user["email"],
            "question_id": body.question_id,
            "selected_index": body.selected_index,
            "is_correct": is_correct,
        }
    ).execute()

    if is_correct:
        add_score_event(
            user["email"],
            "Trivia",
            f"Q{question['sort_order']}: Correct",
            2,
            game_id,
        )

    half = game["current_half"] or 1
    all_q = (
        db.table("trivia_questions")
        .select("id, correct_index")
        .eq("game_id", game_id)
        .eq("half_number", half)
        .execute()
        .data
    )
    all_a = (
        db.table("trivia_answers")
        .select("*")
        .eq("user_email", user["email"])
        .in_("question_id", [q["id"] for q in all_q])
        .execute()
        .data
    )
    if len(all_a) == len(all_q) and all(a["is_correct"] for a in all_a):
        bonus_exists = (
            db.table("score_events")
            .select("id")
            .eq("user_email", user["email"])
            .eq("source", "Trivia")
            .eq("description", "Perfect 5 bonus")
            .eq("game_id", game_id)
            .execute()
            .data
        )
        if not bonus_exists:
            award_trivia_perfect_bonus(user["email"], game_id)

    return {"is_correct": is_correct}
