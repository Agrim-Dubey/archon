"""Interview Evaluation Reports domain repository, service, and router."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.interview import Interview, Question
from app.models.report import InterviewReport
from app.models.user import User
from app.schemas.report import ReportDetailResponse, ReportListItem

logger = logging.getLogger(__name__)


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_interview_id(self, interview_id: str) -> Optional[InterviewReport]:
        result = await self.db.execute(
            select(InterviewReport).where(InterviewReport.interview_id == interview_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, report_id: str) -> Optional[InterviewReport]:
        result = await self.db.execute(
            select(InterviewReport).where(InterviewReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_user_reports(self, user_id: int) -> List[InterviewReport]:
        result = await self.db.execute(
            select(InterviewReport)
            .join(Interview, InterviewReport.interview_id == Interview.id)
            .where(Interview.user_id == user_id)
            .order_by(InterviewReport.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_default_report(self, interview_id: str) -> InterviewReport:
        rep = InterviewReport(
            interview_id=interview_id,
            overall_score=84,
            requirements_score=88,
            estimation_score=80,
            architecture_score=85,
            data_modeling_score=82,
            scalability_score=86,
            strengths=[
                "Thorough functional requirements gathering with explicit scope bounding",
                "Accurate calculation of read/write bandwidth and storage requirements",
                "Clear separation of concerns between ingress gateways and stateful databases",
            ],
            weaknesses=[
                "Could elaborate further on database replication lag mitigations",
                "Did not initially specify rate-limiting sliding window algorithms",
            ],
            recommendations=[
                "Adopt Consistent Hashing with virtual nodes for distributed cache tiers",
                "Implement Transactional Outbox pattern to avoid dual-write inconsistencies with Kafka",
            ],
            anti_patterns=[
                "Direct dual-write to PostgreSQL and message broker without atomic transactions"
            ],
            scorecard_json={
                "requirements": {"score": 88, "weight": 0.2, "feedback": "Exemplary scoping."},
                "estimation": {"score": 80, "weight": 0.15, "feedback": "Solid QPS math."},
                "architecture": {"score": 85, "weight": 0.35, "feedback": "Robust distributed topology."},
                "data_modeling": {"score": 82, "weight": 0.15, "feedback": "Sensible indexing strategy."},
                "scalability": {"score": 86, "weight": 0.15, "feedback": "Appropriate caching layers."},
            },
        )
        self.db.add(rep)
        await self.db.commit()
        await self.db.refresh(rep)
        return rep


router = APIRouter(prefix="/api/v1/reports", tags=["Reports & Feedback"])


@router.get("", response_model=List[ReportListItem])
async def list_reports(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    repo = ReportRepository(db)
    reports = await repo.list_user_reports(user.id)
    items = []
    for r in reports:
        it = await db.get(Interview, r.interview_id)
        q = await db.get(Question, it.question_id) if it else None
        items.append(
            ReportListItem(
                id=r.id,
                interview_id=r.interview_id,
                question_title=q.title if q else "System Design",
                difficulty=q.difficulty if q else "Senior",
                overall_score=r.overall_score,
                created_at=r.created_at,
            )
        )
    return items


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report_detail(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    repo = ReportRepository(db)
    r = await repo.get_by_id(report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found.")

    it = await db.get(Interview, r.interview_id)
    if not it or it.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    q = await db.get(Question, it.question_id) if it else None

    return ReportDetailResponse(
        id=r.id,
        interview_id=r.interview_id,
        question_title=q.title if q else "System Design",
        difficulty=q.difficulty if q else "Senior",
        overall_score=r.overall_score,
        requirements_score=r.requirements_score,
        estimation_score=r.estimation_score,
        architecture_score=r.architecture_score,
        data_modeling_score=r.data_modeling_score,
        scalability_score=r.scalability_score,
        strengths=r.strengths,
        weaknesses=r.weaknesses,
        recommendations=r.recommendations,
        anti_patterns=r.anti_patterns,
        scorecard_json=r.scorecard_json,
        created_at=r.created_at,
    )
