"""Candidate Analytics & Radar Chart domain."""

import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.interview import Interview
from app.models.report import InterviewReport
from app.models.user import User
from app.schemas.analytics import AnalyticsOverviewResponse, PerformanceHistory, RadarMetric

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Candidate Analytics"])


@router.get("", response_model=AnalyticsOverviewResponse)
async def get_analytics(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    # Fetch user reports
    res = await db.execute(
        select(InterviewReport)
        .join(Interview, InterviewReport.interview_id == Interview.id)
        .where(Interview.user_id == user.id)
    )
    reports = list(res.scalars().all())

    count = len(reports)
    if count == 0:
        return AnalyticsOverviewResponse(
            radar_metrics=[
                RadarMetric(category="Requirements Gathering", score=75.0, benchmark=80.0),
                RadarMetric(category="Capacity Estimation", score=70.0, benchmark=78.0),
                RadarMetric(category="System Architecture", score=80.0, benchmark=82.0),
                RadarMetric(category="Data Modeling & Storage", score=72.0, benchmark=76.0),
                RadarMetric(category="Scalability & Reliability", score=78.0, benchmark=84.0),
            ],
            overall_readiness_score=75.0,
            total_interviews_completed=0,
            estimated_level="Senior Software Engineer",
            history=[],
        )

    avg_req = sum(r.requirements_score for r in reports) / count
    avg_est = sum(r.estimation_score for r in reports) / count
    avg_arch = sum(r.architecture_score for r in reports) / count
    avg_data = sum(r.data_modeling_score for r in reports) / count
    avg_scale = sum(r.scalability_score for r in reports) / count
    avg_overall = sum(r.overall_score for r in reports) / count

    metrics = [
        RadarMetric(category="Requirements Gathering", score=round(avg_req, 1), benchmark=80.0),
        RadarMetric(category="Capacity Estimation", score=round(avg_est, 1), benchmark=78.0),
        RadarMetric(category="System Architecture", score=round(avg_arch, 1), benchmark=82.0),
        RadarMetric(category="Data Modeling & Storage", score=round(avg_data, 1), benchmark=76.0),
        RadarMetric(category="Scalability & Reliability", score=round(avg_scale, 1), benchmark=84.0),
    ]

    history = [
        PerformanceHistory(
            date=r.created_at.strftime("%Y-%m-%d"),
            score=r.overall_score,
            topic="System Design",
        )
        for r in reports[:10]
    ]

    return AnalyticsOverviewResponse(
        radar_metrics=metrics,
        overall_readiness_score=round(avg_overall, 1),
        total_interviews_completed=count,
        estimated_level="Senior / Staff Engineer" if avg_overall >= 80 else "Intermediate Engineer",
        history=history,
    )
