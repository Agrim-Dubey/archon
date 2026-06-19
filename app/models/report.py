"""Interview evaluation scorecard and report model."""

from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requirements_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimation_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    architecture_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_modeling_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scalability_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strengths: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    anti_patterns: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    scorecard_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="report")
