"""Pydantic schemas for interview sessions and questions."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import ConfigDict, BaseModel, Field


class QuestionResponse(BaseModel):
    id: str
    title: str
    difficulty: str
    expected_topics: List[str]
    time_limit_minutes: int
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    architectural_tips: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class StartInterviewRequest(BaseModel):
    question_id: str


class InterviewResponse(BaseModel):
    id: str
    user_id: int
    question_id: str
    question_title: Optional[str] = None
    difficulty: Optional[str] = None
    status: str
    current_phase: str
    score: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubmitInterviewRequest(BaseModel):
    notes: Optional[str] = None


class SubmitInterviewResponse(BaseModel):
    success: bool
    interview_id: str
    status: str
    message: str
