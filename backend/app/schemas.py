"""Pydantic schemas: validate API input AND the LLM's output."""
from typing import Optional

from pydantic import BaseModel, Field

from .services.policy_engine import Reason


class RefundRequestIn(BaseModel):
    customer_id: str = Field(min_length=1, max_length=20)
    order_id: str = Field(min_length=1, max_length=20)   # chosen in the UI, not parsed from text
    message: str = Field(min_length=1, max_length=2000)


class ExtractedIntent(BaseModel):
    """Structured output the LLM must return. Anything else is rejected."""
    reason: Reason
    claimed_amount: Optional[float] = Field(default=None, ge=0)
    mentioned_order_id: Optional[str] = Field(default=None, max_length=20)
    summary: str = Field(default="", max_length=300)
