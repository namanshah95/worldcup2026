from __future__ import annotations
import random

from app.database import get_supabase
from app.services.scoring import generate_bingo_board


def ensure_bingo_board(user_email: str) -> list[int]:
    db = get_supabase()
    existing = db.table("bingo_boards").select("event_ids").eq("user_email", user_email).execute().data
    if existing:
        return existing[0]["event_ids"]

    events = db.table("bingo_events").select("id").execute().data
    event_ids = [e["id"] for e in events]
    board = generate_bingo_board(event_ids)

    db.table("bingo_boards").insert({"user_email": user_email, "event_ids": board}).execute()
    return board
