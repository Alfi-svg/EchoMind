from __future__ import annotations

from pydantic import BaseModel, Field

class Phase1Result(BaseModel):
    language: str = Field(..., description="bn or en")
    transcript: str
    sentiment: str
    sentiment_score: float
    explanation: str

class Phase2Result(BaseModel):
    timeline_csv_path: str
    timeline_json_path: str
    stats: dict
    explanation: dict

class FullResult(BaseModel):
    phase1: Phase1Result
    phase2: Phase2Result
