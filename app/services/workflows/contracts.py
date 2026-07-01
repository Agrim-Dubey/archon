"""Temporal evaluation workflow contracts."""
from typing import Any, Dict, List
from pydantic import BaseModel

class EvaluationWorkflowInput(BaseModel):
    session_id: str
    notes: str = ""
