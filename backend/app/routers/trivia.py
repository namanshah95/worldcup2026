from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.database import get_supabase
from app.deps import get_current_user
from app.models import TriviaAnswerRequest, TriviaQuestionResponse, TriviaSessionResponse
from app.services.scoring import add_score_event, award_trivia_perfect_bonus

router = APIRouter(prefix="/trivia", tags=["trivia"])


def _active_halftime_game():
    db = get_supabase()
    games = db.table("games").select("*").eq("status", "halftime").order("sort_order").execute().data
    return games[0] if games else None


@router.get("/{game_id}", response_model=TriviaSessionResponse)
def get_trivia(game_id: str, user: dict = Depends(get_current_user)):
    db = get_supabase()
    game = db.table("games").select("*").eq("id", game_id).single().execute().data
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    is_active = game["status"] == "halftime"
    half = game["current_half"] or 1

    if not is_active:
        next_label = "1st half-time" if game["status"] in ("scheduled", "live") else "next half-time"
        return TriviaSessionResponse(
            is_active=False,
            game_id=game_id,
            half_number=half,
            message=f"Trivia unlocks at {next_label}. Check back during the break!",
            questions=[],
        )

    questions = (
        db.table("trivia_questions")
        .select("*")
        .eq("game_id", game_id)
        .eq("half_number", half)
        .order("sort_order")
        .execute()
        .data
    )

    answers = (
        db.table("trivia_answers")
        .select("*")
        .eq("user_email", user["email"])
        .in_("question_id", [q["id"] for q in questions] if questions else [-1])
        .execute()
        .data
    )
    answer_map = {a["question_id"]: a for a in answers}

    return TriviaSessionResponse(
        is_active=True,
        game_id=game_id,
        half_number=half,
        message="Half-time trivia is live! You have until the 2nd half kicks off.",
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
            for q in questions
        ],
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
