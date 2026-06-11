"""Whiteboard diagram nodes and edges models."""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class DiagramNode(Base, TimestampMixin):
    __tablename__ = "diagram_nodes"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    interview = relationship("Interview", back_populates="diagram_nodes")


class DiagramEdge(Base, TimestampMixin):
    __tablename__ = "diagram_edges"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=True, default="default")

    interview = relationship("Interview", back_populates="diagram_edges")
