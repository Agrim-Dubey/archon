"""Candidate Dashboard domain."""

import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.interview import Interview, Question
from app.models.quiz import QuizDeck
from app.models.settings import UserSettings
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewResponse, RecentInterviewSummary, StreakInfo
from app.schemas.quiz import QuizDeckResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    # Fetch user settings
    settings_res = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    user_settings = settings_res.scalar_one_or_none()
    target_lvl = user_settings.target_level if user_settings else "senior"
    weekly_target = user_settings.weekly_interview_target if user_settings else 3

    # Fetch recent interviews
    it_res = await db.execute(
        select(Interview).where(Interview.user_id == user.id).order_by(Interview.started_at.desc()).limit(5)
    )
    interviews = list(it_res.scalars().all())

    recent_summaries = []
    scores = []
    completed_count = 0
    for it in interviews:
        q = await db.get(Question, it.question_id)
        if it.score:
            scores.append(it.score)
        if it.status == "COMPLETED":
            completed_count += 1

        recent_summaries.append(
            RecentInterviewSummary(
                id=it.id,
                title=q.title if q else "System Design",
                difficulty=q.difficulty if q else "Senior",
                score=it.score,
                status=it.status,
                date=it.started_at.strftime("%b %d, %Y"),
            )
        )

    avg_score = sum(scores) / len(scores) if scores else 82.5

    # Fetch recommended quiz decks
    deck_res = await db.execute(select(QuizDeck).limit(3))
    recommended_decks = [QuizDeckResponse.from_orm(d) for d in deck_res.scalars().all()]

    return DashboardOverviewResponse(
        candidate_name=user.name,
        target_level=target_lvl.capitalize(),
        total_completed=completed_count,
        average_score=round(avg_score, 1),
        streak=StreakInfo(
            current_streak_days=4,
            weekly_progress=min(completed_count, weekly_target),
            weekly_target=weekly_target,
        ),
        recent_interviews=recent_summaries,
        recommended_decks=recommended_decks,
    )
