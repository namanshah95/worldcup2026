from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_supabase
from app.deps import get_current_user
from app.models import BingoBoardResponse, BingoMarkRequest, BingoSquare
from app.services.bingo import ensure_bingo_board
from app.services.scoring import award_bingo, check_bingo

router = APIRouter(prefix="/bingo", tags=["bingo"])


@router.get("/board", response_model=BingoBoardResponse)
def get_board(user: dict = Depends(get_current_user)):
    db = get_supabase()
    event_ids = ensure_bingo_board(user["email"])

    events = db.table("bingo_events").select("id, description").execute().data
    event_map = {e["id"]: e["description"] for e in events}

    marks = db.table("bingo_marks").select("square_index").eq("user_email", user["email"]).execute().data
    mark_set = {m["square_index"] for m in marks}

    board_row = db.table("bingo_boards").select("*").eq("user_email", user["email"]).single().execute().data

    squares = []
    for i, eid in enumerate(event_ids):
        is_free = eid == -1
        squares.append(
            BingoSquare(
                index=i,
                description="FREE" if is_free else event_map.get(eid, "Unknown"),
                is_free=is_free,
                marked=i in mark_set or is_free,
            )
        )

    has_bingo = check_bingo(mark_set | {12})
    return BingoBoardResponse(
        squares=squares,
        marks=list(mark_set),
        has_bingo=has_bingo or board_row.get("completed_at") is not None,
        is_first_winner=board_row.get("is_first_winner", False),
    )


@router.post("/mark", response_model=BingoBoardResponse)
def mark_square(body: BingoMarkRequest, user: dict = Depends(get_current_user)):
    db = get_supabase()
    if body.square_index == 12:
        raise HTTPException(status_code=400, detail="Free space is always marked")

    board = db.table("bingo_boards").select("*").eq("user_email", user["email"]).single().execute().data
    if board.get("completed_at"):
        raise HTTPException(status_code=403, detail="Bingo already completed")

    existing = (
        db.table("bingo_marks")
        .select("*")
        .eq("user_email", user["email"])
        .eq("square_index", body.square_index)
        .execute()
        .data
    )
    if not existing:
        db.table("bingo_marks").insert(
            {"user_email": user["email"], "square_index": body.square_index}
        ).execute()

    marks = db.table("bingo_marks").select("square_index").eq("user_email", user["email"]).execute().data
    mark_set = {m["square_index"] for m in marks} | {12}

    if check_bingo(mark_set):
        winners = db.table("bingo_boards").select("*").not_.is_("completed_at", "null").execute().data
        is_first = len(winners) == 0

        db.table("bingo_boards").update(
            {"completed_at": "now()", "is_first_winner": is_first}
        ).eq("user_email", user["email"]).execute()

        award_bingo(user["email"], is_first)

    return get_board(user)


@router.post("/unmark", response_model=BingoBoardResponse)
def unmark_square(body: BingoMarkRequest, user: dict = Depends(get_current_user)):
    db = get_supabase()
    if body.square_index == 12:
        raise HTTPException(status_code=400, detail="Free space cannot be unmarked")

    board = db.table("bingo_boards").select("*").eq("user_email", user["email"]).single().execute().data
    if board.get("completed_at"):
        raise HTTPException(status_code=403, detail="Bingo already completed")

    existing = (
        db.table("bingo_marks")
        .select("*")
        .eq("user_email", user["email"])
        .eq("square_index", body.square_index)
        .execute()
        .data
    )
    if not existing:
        raise HTTPException(status_code=400, detail="Square is not marked")

    db.table("bingo_marks").delete().eq("user_email", user["email"]).eq(
        "square_index", body.square_index
    ).execute()

    return get_board(user)
