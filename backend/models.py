from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Decision(str, Enum):
    REFUND = "REFUND"
    RESHIP = "RESHIP"
    ESCALATE = "ESCALATE"
    DISMISS = "DISMISS"


class ComplaintCreate(BaseModel):
    complaint_text: str = Field(..., min_length=5)
    order_id: Optional[str] = None


class IntakeResult(BaseModel):
    customer_name: Optional[str] = None
    order_id: Optional[str] = None
    issue_type: str = "unknown"
    sentiment: str = "neutral"


class ContextResult(BaseModel):
    order_found: bool = False
    order_data: Optional[dict[str, Any]] = None
    notes: str = "No order context"


class ReasoningResult(BaseModel):
    decision: Decision
    confidence: float = Field(..., ge=0, le=1)
    rationale: str
    requires_human_review: bool = False


class ResponseResult(BaseModel):
    english: str
    bahasa_malaysia: str


class ComplaintRecord(BaseModel):
    id: str
    complaint_text: str
    created_at: datetime
    status: str = "COMPLETED"
    intake: IntakeResult
    context: ContextResult
    reasoning: ReasoningResult
    response: ResponseResult


class AgentEvent(BaseModel):
    id: str
    complaint_id: str
    step: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TestLLMRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


class TestLLMResponse(BaseModel):
    model: str
    output: str
