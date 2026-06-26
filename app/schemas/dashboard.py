"""Pydantic schemas for dashboard overview."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas.interview import InterviewResponse
from app.schemas.quiz import QuizDeckResponse


class RecentInterviewSummary(BaseModel):
    id: str
    title: str
    difficulty: str
    score: Optional[int]
    status: str
    date: str


class StreakInfo(BaseModel):
    current_streak_days: int
    weekly_progress: int
    weekly_target: int


class DashboardOverviewResponse(BaseModel):
    candidate_name: str
    target_level: str
    total_completed: int
    average_score: float
    streak: StreakInfo
    recent_interviews: List[RecentInterviewSummary]
    recommended_decks: List[QuizDeckResponse]
