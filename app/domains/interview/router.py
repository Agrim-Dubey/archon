"""Interview domain repository, service, and router."""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.interview import Interview, Question
from app.models.outbox import OutboxEvent
from app.models.user import User
from app.schemas.interview import (
    InterviewResponse,
    QuestionResponse,
    StartInterviewRequest,
    SubmitInterviewRequest,
    SubmitInterviewResponse,
)

logger = logging.getLogger(__name__)


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_question(self, question_id: str) -> Optional[Question]:
        result = await self.db.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def list_questions(self, difficulty: Optional[str] = None) -> List[Question]:
        query = select(Question)
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_interview(self, user_id: int, question_id: str) -> Interview:
        interview = Interview(user_id=user_id, question_id=question_id, status="IN_PROGRESS")
        self.db.add(interview)
        await self.db.flush()

        # Atomic Outbox event for interview creation
        outbox = OutboxEvent(
            aggregate_type="Interview",
            aggregate_id=interview.id,
            type="InterviewStarted",
            payload={"interview_id": interview.id, "user_id": user_id, "question_id": question_id},
        )
        self.db.add(outbox)
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def get_interview_by_id(self, interview_id: str, user_id: int) -> Optional[Interview]:
        result = await self.db.execute(
            select(Interview).where(Interview.id == interview_id, Interview.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_user_interviews(self, user_id: int) -> List[Interview]:
        result = await self.db.execute(
            select(Interview).where(Interview.user_id == user_id).order_by(Interview.started_at.desc())
        )
        return list(result.scalars().all())

    async def submit_interview(self, interview_id: str, user_id: int, notes: Optional[str] = None) -> Interview:
        interview = await self.get_interview_by_id(interview_id, user_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview session not found.")

        interview.status = "COMPLETED"
        interview.ended_at = datetime.now(timezone.utc)
        if not interview.score:
            interview.score = 85  # Initial baseline score prior to background evaluation

        outbox = OutboxEvent(
            aggregate_type="Interview",
            aggregate_id=interview.id,
            type="InterviewSubmitted",
            payload={"interview_id": interview.id, "user_id": user_id, "notes": notes},
        )
        self.db.add(outbox)
        await self.db.commit()
        await self.db.refresh(interview)
        return interview


router = APIRouter(prefix="/api/v1/interviews", tags=["Interviews"])


@router.get("/questions", response_model=List[QuestionResponse])
async def list_questions(difficulty: Optional[str] = None, db: AsyncSession = Depends(get_async_db)):
    repo = InterviewRepository(db)
    questions = await repo.list_questions(difficulty)
    return questions


@router.post("/start", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    req: StartInterviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    repo = InterviewRepository(db)
    q = await repo.get_question(req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found.")

    interview = await repo.create_interview(user.id, req.question_id)
    return InterviewResponse(
        id=interview.id,
        user_id=interview.user_id,
        question_id=interview.question_id,
        question_title=q.title,
        difficulty=q.difficulty,
        status=interview.status,
        current_phase=interview.current_phase,
        score=interview.score,
        started_at=interview.started_at,
        ended_at=interview.ended_at,
    )


@router.get("", response_model=List[InterviewResponse])
async def list_interviews(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    repo = InterviewRepository(db)
    interviews = await repo.list_user_interviews(user.id)
    result = []
    for it in interviews:
        q = await repo.get_question(it.question_id)
        result.append(
            InterviewResponse(
                id=it.id,
                user_id=it.user_id,
                question_id=it.question_id,
                question_title=q.title if q else "System Design",
                difficulty=q.difficulty if q else "Senior",
                status=it.status,
                current_phase=it.current_phase,
                score=it.score,
                started_at=it.started_at,
                ended_at=it.ended_at,
            )
        )
    return result


@router.post("/{interview_id}/submit", response_model=SubmitInterviewResponse)
async def submit_interview(
    interview_id: str,
    req: SubmitInterviewRequest = SubmitInterviewRequest(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    repo = InterviewRepository(db)
    it = await repo.submit_interview(interview_id, user.id, req.notes)
    return SubmitInterviewResponse(
        success=True,
        interview_id=it.id,
        status=it.status,
        message="Interview submitted successfully. Evaluation scorecard generated.",
    )


@router.get("/{interview_id}/report")
async def get_interview_report(
    interview_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    from app.domains.reports.router import ReportRepository
    repo = ReportRepository(db)
    rep = await repo.get_by_interview_id(interview_id)
    if not rep:
        # Generate default report if not yet evaluated
        rep = await repo.create_default_report(interview_id)
    return rep
