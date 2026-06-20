from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.database import get_supabase
from app.deps import get_current_user
from app.models import AttendanceScanRequest, AttendanceScanResponse
from app.services.scoring import add_score_event

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/scan", response_model=AttendanceScanResponse)
def scan_qr(body: AttendanceScanRequest, user: dict = Depends(get_current_user)):
    db = get_supabase()
    # QR payload format: wc26-attendance:{game_id}:{secret}
    payload = body.qr_payload.strip()
    if not payload.startswith("wc26-attendance:"):
        raise HTTPException(status_code=400, detail="Invalid QR code")

    parts = payload.split(":")
    if len(parts) != 3:
        raise HTTPException(status_code=400, detail="Invalid QR code format")

    _, game_id, secret = parts
    game = db.table("games").select("*").eq("id", game_id).execute().data
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    g = game[0]

    if g["attendance_qr_secret"] != secret:
        raise HTTPException(status_code=403, detail="Invalid attendance code")

    existing = (
        db.table("attendance_scans")
        .select("*")
        .eq("user_email", user["email"])
        .eq("game_id", game_id)
        .execute()
        .data
    )
    if existing:
        return AttendanceScanResponse(
            game_id=game_id,
            game_name=f"{g['home_team']} vs {g['away_team']}",
            points_awarded=0,
            already_scanned=True,
        )

    db.table("attendance_scans").insert({"user_email": user["email"], "game_id": game_id}).execute()
    points = settings.attendance_bonus_points
    add_score_event(
        user["email"],
        "Attendance",
        f"In-person: {g['home_team']} vs {g['away_team']}",
        points,
        game_id,
    )

    return AttendanceScanResponse(
        game_id=game_id,
        game_name=f"{g['home_team']} vs {g['away_team']}",
        points_awarded=points,
        already_scanned=False,
    )


@router.get("/scans")
def my_scans(user: dict = Depends(get_current_user)):
    db = get_supabase()
    scans = (
        db.table("attendance_scans")
        .select("game_id, scanned_at, games(home_team, away_team)")
        .eq("user_email", user["email"])
        .execute()
        .data
    )
    return scans
