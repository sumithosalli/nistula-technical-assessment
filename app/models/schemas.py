from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageSource(str, Enum):
    WHATSAPP = "whatsapp"
    BOOKING_COM = "booking_com"
    AIRBNB = "airbnb"
    INSTAGRAM = "instagram"
    DIRECT = "direct"


class QueryType(str, Enum):
    PRE_SALES_AVAILABILITY = "pre_sales_availability"
    PRE_SALES_PRICING = "pre_sales_pricing"
    POST_SALES_CHECKIN = "post_sales_checkin"
    SPECIAL_REQUEST = "special_request"
    COMPLAINT = "complaint"
    GENERAL_ENQUIRY = "general_enquiry"


class ActionType(str, Enum):
    AUTO_SEND = "auto_send"
    AGENT_REVIEW = "agent_review"
    ESCALATE = "escalate"


class IncomingMessage(BaseModel):
    source: MessageSource
    guest_name: str
    message: str
    timestamp: datetime
    booking_ref: Optional[str] = None
    property_id: Optional[str] = None


class NormalizedMessage(BaseModel):
    message_id: UUID = Field(default_factory=uuid4)
    source: MessageSource
    guest_name: str
    message_text: str
    timestamp: datetime
    booking_ref: Optional[str] = None
    property_id: Optional[str] = None
    query_type: QueryType


class LLMClassificationResult(BaseModel):
    query_type: QueryType
    drafted_reply: str


class WebhookResponse(BaseModel):
    message_id: UUID
    query_type: QueryType
    drafted_reply: str
    confidence_score: float
    action: ActionType
