"""System Design Quiz Bank domain repository, service, and router."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.quiz import QuizAttempt, QuizDeck, QuizQuestion
from app.models.user import User
from app.schemas.quiz import (
    DailyChallengeVerifyRequest,
    DailyChallengeVerifyResponse,
    QuizDeckResponse,
    QuizQuestionResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)

logger = logging.getLogger(__name__)


class QuizRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_decks(self) -> List[QuizDeck]:
        result = await self.db.execute(select(QuizDeck))
        return list(result.scalars().all())

    async def get_deck_questions(self, deck_id: str) -> List[QuizQuestion]:
        result = await self.db.execute(
            select(QuizQuestion).where(QuizQuestion.deck_id == deck_id)
        )
        return list(result.scalars().all())

    async def get_daily_challenge(self) -> Optional[QuizQuestion]:
        result = await self.db.execute(
            select(QuizQuestion).where(QuizQuestion.is_daily == True)
        )
        return result.scalars().first()


router = APIRouter(prefix="/api/v1/quiz", tags=["Quiz Bank"])


@router.get("/decks", response_model=List[QuizDeckResponse])
async def list_decks(db: AsyncSession = Depends(get_async_db)):
    repo = QuizRepository(db)
    return await repo.list_decks()


@router.get("/decks/{deck_id}", response_model=List[QuizQuestionResponse])
async def get_deck_questions(deck_id: str, db: AsyncSession = Depends(get_async_db)):
    repo = QuizRepository(db)
    questions = await repo.get_deck_questions(deck_id)
    if not questions:
        raise HTTPException(status_code=404, detail="Deck not found or empty.")
    return questions


@router.post("/decks/{deck_id}/submit", response_model=QuizSubmitResponse)
async def submit_deck(
    deck_id: str,
    req: QuizSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    repo = QuizRepository(db)
    questions = await repo.get_deck_questions(deck_id)
    if not questions:
        raise HTTPException(status_code=404, detail="Deck not found.")

    correct_count = 0
    results = []
    for q in questions:
        user_choice = req.answers.get(str(q.id))
        is_correct = False
        correct_opt = ""
        expl = ""
        for opt in q.options:
            if opt.get("is_correct"):
                correct_opt = opt.get("id")
                expl = opt.get("explanation", "")
            if opt.get("id") == user_choice and opt.get("is_correct"):
                is_correct = True

        if is_correct:
            correct_count += 1

        results.append(
            {
                "question_id": q.id,
                "is_correct": is_correct,
                "user_choice": user_choice,
                "correct_option_id": correct_opt,
                "explanation": expl,
            }
        )

    score_pct = (correct_count / len(questions)) * 100 if questions else 0.0

    attempt = QuizAttempt(
        user_id=user.id,
        deck_id=deck_id,
        score=correct_count,
        total_questions=len(questions),
        answers=req.answers,
    )
    db.add(attempt)
    await db.commit()

    return QuizSubmitResponse(
        score=correct_count,
        total_questions=len(questions),
        percentage=round(score_pct, 1),
        results=results,
    )


@router.get("/daily-challenge", response_model=QuizQuestionResponse)
async def get_daily_challenge(db: AsyncSession = Depends(get_async_db)):
    repo = QuizRepository(db)
    q = await repo.get_daily_challenge()
    if not q:
        # Fallback to any first question
        res = await db.execute(select(QuizQuestion))
        q = res.scalars().first()
        if not q:
            raise HTTPException(status_code=404, detail="No daily challenge question found.")
    return q


@router.post("/daily-challenge/verify", response_model=DailyChallengeVerifyResponse)
async def verify_daily_challenge(
    req: DailyChallengeVerifyRequest, db: AsyncSession = Depends(get_async_db)
):
    q = await db.get(QuizQuestion, req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found.")

    correct_id = ""
    explanation = ""
    for opt in q.options:
        if opt.get("is_correct"):
            correct_id = opt.get("id")
            explanation = opt.get("explanation", "")

    return DailyChallengeVerifyResponse(
        is_correct=(req.selected_option_id == correct_id),
        explanation=explanation,
        correct_option_id=correct_id,
    )
