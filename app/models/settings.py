"""User profile and platform settings model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    target_level: Mapped[str] = mapped_column(String(50), default="senior", nullable=False)
    years_of_experience: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    primary_stack: Mapped[str] = mapped_column(String(50), default="Python", nullable=False)
    target_companies: Mapped[list] = mapped_column(JSON, default=lambda: ["Google", "Meta", "Stripe"], nullable=False)
    interviewer_strictness: Mapped[str] = mapped_column(String(50), default="standard", nullable=False)
    feedback_style: Mapped[str] = mapped_column(String(50), default="socratic", nullable=False)
    enable_proactive_hints: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_voice_interview: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canvas_grid_type: Mapped[str] = mapped_column(String(20), default="dots", nullable=False)
    snap_to_grid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_save_interval_seconds: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    export_format: Mapped[str] = mapped_column(String(10), default="svg", nullable=False)
    weekly_interview_target: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_report_digest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="settings")
