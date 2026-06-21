from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=50)


class RegisterResponse(BaseModel):
    email: str
    display_name: str
    session_token: str
    expires_at: datetime


class UserResponse(BaseModel):
    email: str
    display_name: str
    has_seen_game_rules: bool


class GameResponse(BaseModel):
    id: str
    home_team: str
    away_team: str
    home_flag: str
    away_flag: str
    kickoff_at: datetime
    status: str
    home_score: int
    away_score: int
    current_half: int
    is_locked: bool


class PickEmRequest(BaseModel):
    home_score: int = Field(ge=0, le=20)
    away_score: int = Field(ge=0, le=20)


class PickEmResponse(BaseModel):
    game_id: str
    home_score: int
    away_score: int
    is_locked: bool


class PlayerResponse(BaseModel):
    id: str
    name: str
    country: str
    position: str
    game_id: str
    previous_opponent: Optional[str]
    previous_points: int
    goals: int
    assists: int
    clean_sheet: bool
    unavailable: bool
    match_started: bool = False
    is_selectable: bool


class CaptainSelectRequest(BaseModel):
    player_id: str


class CaptainResponse(BaseModel):
    player: Optional[PlayerResponse]
    score_events: list["ScoreEventResponse"]
    is_locked: bool


class BingoBoardResponse(BaseModel):
    squares: list["BingoSquare"]
    marks: list[int]
    has_bingo: bool
    is_first_winner: bool


class BingoSquare(BaseModel):
    index: int
    description: str
    is_free: bool
    marked: bool


class BingoMarkRequest(BaseModel):
    square_index: int = Field(ge=0, le=24)


class TriviaQuestionResponse(BaseModel):
    id: int
    question: str
    options: list[str]
    sort_order: int
    answered: bool
    selected_index: Optional[int]
    is_correct: Optional[bool]


class TriviaSessionResponse(BaseModel):
    is_active: bool
    game_id: str
    game_label: str = ""
    half_number: int
    message: str
    questions: list[TriviaQuestionResponse]


class TriviaAnswerRequest(BaseModel):
    question_id: int
    selected_index: int = Field(ge=0, le=3)


class LeaderboardEntry(BaseModel):
    email: str
    display_name: str
    total_points: int
    rank: int


class ScoreEventResponse(BaseModel):
    id: int
    source: str
    description: str
    points: int
    game_id: Optional[str]
    created_at: datetime


class ScoringResponse(BaseModel):
    total_points: int
    events: list[ScoreEventResponse]
    rules: list["ScoringRule"]


class ScoringRule(BaseModel):
    category: str
    outcome: str
    points: str


class AttendanceScanRequest(BaseModel):
    qr_payload: str


class AttendanceScanResponse(BaseModel):
    game_id: str
    game_name: str
    points_awarded: int
    already_scanned: bool


class AdminUpdateScoreRequest(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    status: str = Field(pattern="^(scheduled|live|halftime|finished)$")
    current_half: int = Field(ge=0, le=2)


class AdminPlayerStatsRequest(BaseModel):
    goals: int = Field(ge=0)
    assists: int = Field(ge=0)
    clean_sheet: bool = False


class AdminResetUserRequest(BaseModel):
    email: EmailStr


class AdminResetUserResponse(BaseModel):
    email: str
    display_name: str
    unregistered: bool
    deleted: dict[str, int]


class AdminLinkFixtureRequest(BaseModel):
    match_id: str = Field(min_length=1)


class AdminRescorePickEmRequest(BaseModel):
    home_score: Optional[int] = Field(default=None, ge=0, le=20)
    away_score: Optional[int] = Field(default=None, ge=0, le=20)
    refresh_from_api: bool = True


CaptainResponse.model_rebuild()
BingoBoardResponse.model_rebuild()

SCORING_RULES = [
    ScoringRule(category="Pick'ems", outcome="Correct Match Winner", points="5"),
    ScoringRule(category="Pick'ems", outcome="Each Correct Side of Score", points="3 (per side)"),
    ScoringRule(category="Pick'ems", outcome="Exact Score Match", points="4"),
    ScoringRule(category="Captain", outcome="Player Goal", points="10"),
    ScoringRule(category="Captain", outcome="Player Assist", points="5"),
    ScoringRule(category="Captain", outcome="Clean Sheet (Goalie/Defender)", points="8"),
    ScoringRule(category="Bingo", outcome="5 in a Row (First to finish)", points="20"),
    ScoringRule(category="Bingo", outcome="5 in a Row (Everyone else)", points="10"),
    ScoringRule(category="Trivia", outcome="Correct Answer", points="2"),
    ScoringRule(category="Trivia", outcome='"Perfect 5" Bonus', points="5"),
    ScoringRule(category="Attendance", outcome="In-person scan per game", points="4"),
]
