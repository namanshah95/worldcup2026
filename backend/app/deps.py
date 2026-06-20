from __future__ import annotations
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException

from app.database import get_supabase
from app.services.scoring import utcnow


async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    db = get_supabase()
    result = db.table("users").select("*").eq("session_token", token).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user = result.data[0]
    expires = user.get("session_expires_at")
    if expires:
        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        if utcnow() > exp_dt:
            raise HTTPException(status_code=401, detail="Session expired")
    return user
