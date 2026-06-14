"""Pydantic schemas for WebSocket messages and AI payloads."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class WSMessage(BaseModel):
    type: str
    data: Any


class ChatMessageData(BaseModel):
    role: str
    content: str


class StatusMessageData(BaseModel):
    status: str
    role: str = "ai"


class ErrorMessageData(BaseModel):
    message: str
