"""Pydantic schemas for candidate analytics and radar charts."""

from typing import List
from pydantic import BaseModel


class RadarMetric(BaseModel):
    category: str
    score: float
    benchmark: float


class PerformanceHistory(BaseModel):
    date: str
    score: int
    topic: str


class AnalyticsOverviewResponse(BaseModel):
    radar_metrics: List[RadarMetric]
    overall_readiness_score: float
    total_interviews_completed: int
    estimated_level: str
    history: List[PerformanceHistory]
