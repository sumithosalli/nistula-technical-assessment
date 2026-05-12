import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import (
    ActionType,
    IncomingMessage,
    NormalizedMessage,
    WebhookResponse,
)
from app.services.classifier import classify_and_draft
from app.services.confidence import calculate_confidence, determine_action

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nistula Guest Messaging Platform",
    description="AI-powered guest message handler for hospitality operations",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/webhook/message", response_model=WebhookResponse)
async def handle_guest_message(payload: IncomingMessage):
    message_id = uuid4()

    try:
        llm_result = await classify_and_draft(
            guest_name=payload.guest_name,
            message_text=payload.message,
            source=payload.source.value,
        )
    except Exception as e:
        logger.error("LLM processing failed: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail="AI processing service temporarily unavailable",
        )

    normalized = NormalizedMessage(
        message_id=message_id,
        source=payload.source,
        guest_name=payload.guest_name,
        message_text=payload.message,
        timestamp=payload.timestamp,
        booking_ref=payload.booking_ref,
        property_id=payload.property_id,
        query_type=llm_result.query_type,
    )

    confidence = calculate_confidence(llm_result.query_type, payload.message)
    action = determine_action(confidence, llm_result.query_type)

    logger.info(
        "Processed message %s | type=%s | confidence=%.2f | action=%s",
        message_id,
        llm_result.query_type.value,
        confidence,
        action.value,
    )

    return WebhookResponse(
        message_id=message_id,
        query_type=llm_result.query_type,
        drafted_reply=llm_result.drafted_reply,
        confidence_score=confidence,
        action=action,
    )
