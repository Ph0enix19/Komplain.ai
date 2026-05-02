from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class Decision(str, Enum):
    REFUND = "REFUND"
    RESHIP = "RESHIP"
    CLARIFY = "CLARIFY"
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
    language: str = "EN"


class ContextResult(BaseModel):
    order_found: bool = False
    order_data: Optional[dict[str, Any]] = None
    notes: str = "No order context"


class ImageAnalysisResult(BaseModel):
    image_provided: bool = False
    image_analyzed: bool = False
    item_visible: Optional[bool] = None
    package_visible: Optional[bool] = None
    damage_detected: Optional[bool] = None
    damage_level: str = "unknown"
    damage_type: Optional[str] = None
    matches_order_item: Optional[bool] = None
    matched_order_item: Optional[str] = None
    confidence: float = Field(0, ge=0, le=1)
    evidence: str = "No image evidence provided."
    human_review_required: bool = False

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0, min(1, float(value or 0)))


class ReasoningResult(BaseModel):
    decision: Decision
    confidence: float = Field(..., ge=0, le=1)
    rationale: str
    requires_human_review: bool = False
    clarification_needed: bool = False
    clarification_message: Optional[str] = None

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0, min(1, float(value)))


class ResponseResult(BaseModel):
    english: str
    bahasa_malaysia: str


class ComplaintRecord(BaseModel):
    id: str
    complaint_text: str
    created_at: datetime
    status: str = "COMPLETED"
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    image_analysis: Optional[ImageAnalysisResult] = None
    visual_evidence_used: bool = False
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
    provider_used: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
