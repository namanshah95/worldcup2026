from __future__ import annotations
from fastapi import APIRouter, Depends

from app.database import get_supabase
from app.deps import get_current_user
from app.models import RegisterRequest, RegisterResponse, UserResponse
from app.services.bingo import ensure_bingo_board
from app.services.scoring import create_session_token, get_session_expiry

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
def register(body: RegisterRequest):
    db = get_supabase()
    token = create_session_token()
    expires = get_session_expiry().isoformat()

    existing = db.table("users").select("email").eq("email", body.email).execute().data
    if existing:
        db.table("users").update(
            {
                "display_name": body.display_name,
                "session_token": token,
                "session_expires_at": expires,
            }
        ).eq("email", body.email).execute()
    else:
        db.table("users").insert(
            {
                "email": body.email,
                "display_name": body.display_name,
                "session_token": token,
                "session_expires_at": expires,
            }
        ).execute()

    ensure_bingo_board(body.email)

    return RegisterResponse(
        email=body.email,
        display_name=body.display_name,
        session_token=token,
        expires_at=expires,
    )


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)):
    return UserResponse(
        email=user["email"],
        display_name=user["display_name"],
        has_seen_game_rules=user.get("has_seen_game_rules", False),
    )


@router.post("/end-session")
def end_session(user: dict = Depends(get_current_user)):
    db = get_supabase()
    db.table("users").update({"session_token": None, "session_expires_at": None}).eq(
        "email", user["email"]
    ).execute()
    return {"ok": True}


@router.post("/mark-rules-seen")
def mark_rules_seen(user: dict = Depends(get_current_user)):
    db = get_supabase()
    db.table("users").update({"has_seen_game_rules": True}).eq("email", user["email"]).execute()
    return {"ok": True}
