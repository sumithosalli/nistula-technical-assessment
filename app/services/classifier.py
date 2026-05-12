import json
import logging
import re

import httpx

from app.config import settings
from app.models.schemas import LLMClassificationResult, QueryType
from app.services.property_context import PROPERTY_CONTEXT

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

VALID_QUERY_TYPES = {qt.value for qt in QueryType}

SYSTEM_PROMPT = f"""You are a luxury hospitality concierge AI for a premium villa property in Goa, India.

PROPERTY INFORMATION:
{PROPERTY_CONTEXT}

CLASSIFICATION — classify the guest message into exactly one type:
- pre_sales_availability: asking about dates or availability
- pre_sales_pricing: asking about rates, costs, or pricing
- post_sales_checkin: existing booking — check-in details, directions, amenities
- special_request: specific requests like chef, decorations, early check-in
- complaint: dissatisfaction or reporting issues
- general_enquiry: anything else

REPLY GUIDELINES:
- Address the guest by first name
- Answer their specific question first, directly and clearly
- Confirm availability explicitly when applicable
- Provide exact pricing with accurate calculations when relevant
- Mention only property details that are directly relevant to the query
- Do NOT volunteer operational details (caretaker hours, WiFi password, cancellation policy) unless asked
- Keep replies under 120 words — concise and confident
- Use a warm, premium hospitality tone — friendly but not overly formal
- End with one natural call-to-action (e.g., "Shall I hold these dates?" or "Would you like to proceed?")
- Never use bullet points or lists in the reply — write in natural conversational paragraphs

TONE EXAMPLE:
"Hi Rahul! I'm happy to confirm Villa B1 is available from April 20–24. The rate for 2 adults is INR 18,000 per night, so the total for your 4-night stay would be INR 72,000. The villa includes 3 bedrooms and a private pool in Assagao, North Goa. Please let us know if you'd like to proceed with the booking or need any additional details."

RESPONSE FORMAT — respond with valid JSON only, no other text:
{{"query_type": "<one of the valid types>", "drafted_reply": "<your reply>"}}"""


async def classify_and_draft(
    guest_name: str, message_text: str, source: str
) -> LLMClassificationResult:
    user_prompt = (
        f"Guest Name: {guest_name}\n"
        f"Channel: {source}\n"
        f"Message: {message_text}"
    )

    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            ANTHROPIC_API_URL, headers=headers, json=payload
        )
        response.raise_for_status()

    response_data = response.json()
    raw_text = response_data["content"][0]["text"]

    return parse_llm_response(raw_text)


def parse_llm_response(raw_text: str) -> LLMClassificationResult:
    try:
        parsed = json.loads(raw_text)
        return _validate_parsed(parsed)
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    json_match = re.search(r"\{[^{}]*\}", raw_text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return _validate_parsed(parsed)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    logger.warning("Failed to parse LLM response, using fallback: %s", raw_text[:200])
    return LLMClassificationResult(
        query_type=QueryType.GENERAL_ENQUIRY,
        drafted_reply=(
            "Thank you for reaching out. I've noted your message and our team "
            "will get back to you shortly with the information you need."
        ),
    )


def _validate_parsed(parsed: dict) -> LLMClassificationResult:
    query_type = parsed["query_type"]
    drafted_reply = parsed["drafted_reply"]

    if query_type not in VALID_QUERY_TYPES:
        raise ValueError(f"Invalid query_type: {query_type}")

    if not drafted_reply or not isinstance(drafted_reply, str):
        raise ValueError("Missing or invalid drafted_reply")

    return LLMClassificationResult(
        query_type=QueryType(query_type),
        drafted_reply=drafted_reply.strip(),
    )
