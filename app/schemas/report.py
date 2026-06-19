"""Pydantic schemas for reports and scorecards."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ScorecardDimension(BaseModel):
    score: int
    weight: float
    feedback: str


class ReportDetailResponse(BaseModel):
    id: str
    interview_id: str
    question_title: Optional[str] = None
    difficulty: Optional[str] = None
    overall_score: int
    requirements_score: int
    estimation_score: int
    architecture_score: int
    data_modeling_score: int
    scalability_score: int
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    anti_patterns: List[str]
    scorecard_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    id: str
    interview_id: str
    question_title: str
    difficulty: str
    overall_score: int
    created_at: datetime

    class Config:
        from_attributes = True
