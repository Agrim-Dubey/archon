"""Pydantic schemas for quiz decks, questions, and submissions."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import ConfigDict, BaseModel


class QuizOption(BaseModel):
    id: str
    text: str
    is_correct: Optional[bool] = None
    explanation: Optional[str] = None


class QuizQuestionResponse(BaseModel):
    id: str
    deck_id: str
    question: str
    scenario: Optional[str] = None
    topic_tag: str
    options: List[QuizOption]
    is_daily: bool = False

    model_config = ConfigDict(from_attributes=True)


class QuizDeckResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    question_count: int
    est_minutes: int
    category: str
    icon_name: str

    model_config = ConfigDict(from_attributes=True)


class QuizSubmitRequest(BaseModel):
    answers: Dict[str, str]  # question_id -> option_id


class QuizSubmitResponse(BaseModel):
    score: int
    total_questions: int
    percentage: float
    results: List[Dict[str, Any]]


class DailyChallengeVerifyRequest(BaseModel):
    question_id: str
    selected_option_id: str


class DailyChallengeVerifyResponse(BaseModel):
    is_correct: bool
    explanation: str
    correct_option_id: str
