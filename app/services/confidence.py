from app.models.schemas import ActionType, QueryType

QUERY_TYPE_BASE_CONFIDENCE = {
    QueryType.PRE_SALES_AVAILABILITY: 0.92,
    QueryType.PRE_SALES_PRICING: 0.90,
    QueryType.POST_SALES_CHECKIN: 0.88,
    QueryType.GENERAL_ENQUIRY: 0.85,
    QueryType.SPECIAL_REQUEST: 0.72,
    QueryType.COMPLAINT: 0.45,
}

AMBIGUITY_KEYWORDS = [
    "maybe", "not sure", "i think", "possibly", "can you check",
    "confused", "don't know", "unclear", "help me understand",
]


def calculate_confidence(query_type: QueryType, message_text: str) -> float:
    base = QUERY_TYPE_BASE_CONFIDENCE.get(query_type, 0.75)

    message_lower = message_text.lower()
    ambiguity_hits = sum(1 for kw in AMBIGUITY_KEYWORDS if kw in message_lower)

    if ambiguity_hits > 0:
        penalty = min(ambiguity_hits * 0.08, 0.25)
        base -= penalty

    word_count = len(message_text.split())
    if word_count < 4:
        base -= 0.05
    elif word_count > 50:
        base -= 0.03

    if query_type == QueryType.COMPLAINT:
        base = min(base, 0.55)

    return round(max(0.0, min(1.0, base)), 2)


def determine_action(confidence: float, query_type: QueryType) -> ActionType:
    if query_type == QueryType.COMPLAINT:
        return ActionType.ESCALATE

    if confidence > 0.85:
        return ActionType.AUTO_SEND
    elif confidence >= 0.60:
        return ActionType.AGENT_REVIEW
    else:
        return ActionType.ESCALATE
