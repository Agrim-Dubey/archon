"""System design quiz decks, questions, and attempts models."""

from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class QuizDeck(Base):
    __tablename__ = "quiz_decks"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)  # beginner, intermediate, senior, staff
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    est_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_name: Mapped[str] = mapped_column(String(50), default="Layers", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    questions = relationship("QuizQuestion", back_populates="deck", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deck_id: Mapped[str] = mapped_column(String(50), ForeignKey("quiz_decks.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topic_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)  # list of {id, text, is_correct, explanation}
    is_daily: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    deck = relationship("QuizDeck", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    deck_id: Mapped[str] = mapped_column(String(50), ForeignKey("quiz_decks.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
