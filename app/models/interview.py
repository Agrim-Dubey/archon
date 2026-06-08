"""System design interview, question, and message models."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)  # Beginner, Intermediate, Senior, Staff
    expected_topics: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    constraints: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    architectural_tips: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    evaluation_rubric: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    interviews = relationship("Interview", back_populates="question")


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("questions.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, COMPLETED, ABANDONED
    current_phase: Mapped[str] = mapped_column(String(50), default="REQUIREMENTS", nullable=False)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="interviews")
    question = relationship("Question", back_populates="interviews")
    messages = relationship("InterviewMessage", back_populates="interview", cascade="all, delete-orphan")
    diagram_nodes = relationship("DiagramNode", back_populates="interview", cascade="all, delete-orphan")
    diagram_edges = relationship("DiagramEdge", back_populates="interview", cascade="all, delete-orphan")
    report = relationship("InterviewReport", back_populates="interview", uselist=False, cascade="all, delete-orphan")


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, ai, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    phase: Mapped[str] = mapped_column(String(50), default="REQUIREMENTS", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="messages")
