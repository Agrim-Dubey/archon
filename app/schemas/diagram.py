"""Pydantic schemas for whiteboard diagram state."""

from typing import List, Optional
from pydantic import BaseModel


class NodeSchema(BaseModel):
    id: str
    interview_id: Optional[str] = None
    type: str
    label: str
    x: float
    y: float

    class Config:
        from_attributes = True


class EdgeSchema(BaseModel):
    id: str
    interview_id: Optional[str] = None
    source: str
    target: str
    type: Optional[str] = "default"

    class Config:
        from_attributes = True


class DiagramStateResponse(BaseModel):
    interview_id: str
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]


class DiagramSyncRequest(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
