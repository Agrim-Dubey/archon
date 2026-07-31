"""Pydantic schemas for user platform settings."""

from typing import List, Optional
from pydantic import ConfigDict, BaseModel


class UserSettingsSchema(BaseModel):
    target_level: str
    years_of_experience: int
    primary_stack: str
    target_companies: List[str]
    interviewer_strictness: str
    feedback_style: str
    enable_proactive_hints: bool
    enable_voice_interview: bool
    canvas_grid_type: str
    snap_to_grid: bool
    auto_save_interval_seconds: int
    export_format: str
    weekly_interview_target: int
    email_notifications: bool
    weekly_report_digest: bool

    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdate(BaseModel):
    target_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    primary_stack: Optional[str] = None
    target_companies: Optional[List[str]] = None
    interviewer_strictness: Optional[str] = None
    feedback_style: Optional[str] = None
    enable_proactive_hints: Optional[bool] = None
    enable_voice_interview: Optional[bool] = None
    canvas_grid_type: Optional[str] = None
    snap_to_grid: Optional[bool] = None
    auto_save_interval_seconds: Optional[int] = None
    export_format: Optional[str] = None
    weekly_interview_target: Optional[int] = None
    email_notifications: Optional[bool] = None
    weekly_report_digest: Optional[bool] = None
