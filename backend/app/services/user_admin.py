from __future__ import annotations

from fastapi import HTTPException

from app.database import get_supabase

USER_DATA_TABLES = (
    "score_events",
    "bingo_marks",
    "trivia_answers",
    "attendance_scans",
    "pick_em_predictions",
    "captain_selections",
    "bingo_boards",
)


def reset_user_by_email(email: str) -> dict:
    """Remove a user and all associated game data."""
    db = get_supabase()
    normalized = email.strip().lower()

    existing = db.table("users").select("email, display_name").eq("email", normalized).execute().data
    if not existing:
        raise HTTPException(status_code=404, detail=f"User not found: {normalized}")

    user = existing[0]
    deleted: dict[str, int] = {}

    for table in USER_DATA_TABLES:
        rows = db.table(table).select("*").eq("user_email", normalized).execute().data
        deleted[table] = len(rows)
        if rows:
            db.table(table).delete().eq("user_email", normalized).execute()

    db.table("users").delete().eq("email", normalized).execute()

    return {
        "email": normalized,
        "display_name": user["display_name"],
        "unregistered": True,
        "deleted": deleted,
    }
