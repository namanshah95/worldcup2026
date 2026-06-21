from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

FIRST_HALF_MINUTES = 45
HALFTIME_BREAK_MINUTES = 15
SECOND_HALF_MINUTES = 45


def parse_kickoff(kickoff_at: str | datetime) -> datetime:
    if isinstance(kickoff_at, datetime):
        kickoff = kickoff_at
    else:
        normalized = kickoff_at.replace("Z", "+00:00")
        if len(normalized) >= 3 and normalized[-3] in "+-" and normalized[-2:].isdigit():
            normalized = f"{normalized}:00"
        kickoff = datetime.fromisoformat(normalized)
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    return kickoff


def kickoff_date(kickoff_at: str | datetime) -> date:
    return parse_kickoff(kickoff_at).date()


def link_search_dates(kickoff_at: str | datetime) -> list[date]:
    """Dates to query when linking — covers fixtures listed on adjacent UTC days."""
    day = kickoff_date(kickoff_at)
    return [day - timedelta(days=1), day, day + timedelta(days=1)]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def is_game_locked(kickoff_at: str | datetime, now: datetime | None = None) -> bool:
    """Pick'em and captain lock once kickoff time is reached."""
    reference = now or utcnow()
    return reference >= parse_kickoff(kickoff_at)


def estimate_status_from_kickoff(kickoff_at: str | datetime, now: datetime | None = None) -> tuple[str, int]:
    """Fallback match phase from kickoff clock (no Sportmonks required)."""
    reference = now or utcnow()
    kickoff = parse_kickoff(kickoff_at)
    if reference < kickoff:
        return "scheduled", 1

    first_half_end = kickoff + timedelta(minutes=FIRST_HALF_MINUTES)
    halftime_end = first_half_end + timedelta(minutes=HALFTIME_BREAK_MINUTES)
    match_end = halftime_end + timedelta(minutes=SECOND_HALF_MINUTES)

    if reference < first_half_end:
        return "live", 1
    if reference < halftime_end:
        return "halftime", 1
    if reference < match_end:
        return "live", 2
    return "finished", 2


def effective_game_state(game: dict, now: datetime | None = None) -> tuple[str, int]:
    """
    Resolve status for trivia and splash messaging.

    Sportmonks DB status wins when a fixture is linked and has left 'scheduled'.
    Otherwise use kickoff-based estimates so trivia still opens at half-time
    without manual admin updates.
    """
    reference = now or utcnow()
    db_status = game.get("status") or "scheduled"
    db_half = game.get("current_half") or 1

    if (game.get("external_match_id") or game.get("sportmonks_fixture_id")) and db_status in (
        "live",
        "halftime",
        "finished",
    ):
        return db_status, db_half

    return estimate_status_from_kickoff(game["kickoff_at"], reference)
