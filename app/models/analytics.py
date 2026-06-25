"""Candidate performance analytics model."""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class CandidatePerformance(Base, TimestampMixin):
    __tablename__ = "candidate_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentile: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    total_interviews: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
