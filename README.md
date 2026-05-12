# Nistula — Guest Messaging AI Platform

AI-powered guest message handler for hospitality operations. Receives guest messages from multiple channels, classifies them using Claude, drafts professional replies, and routes based on confidence scoring.

## Tech Stack

- Python
- FastAPI
- Anthropic Claude API
- Pydantic
- PostgreSQL (schema design)

## Architecture Flow

```
Incoming Message
      ↓
Normalize Payload
      ↓
Claude Classification + Reply Drafting
      ↓
Confidence Scoring
      ↓
Action Routing (auto_send / agent_review / escalate)
```

## Design Decision

LLM-based classification was used instead of keyword matching to better handle ambiguous and multi-intent guest queries. A rule-based approach would fail on messages like "Is the villa free next week and how much for 5 people?" — which combines availability and pricing in natural language. Claude handles this reliably without brittle regex or keyword lists.

## Project Structure

```
nistula-technical-assessment/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and webhook endpoint
│   ├── config.py            # Environment configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models and enums
│   └── services/
│       ├── __init__.py
│       ├── classifier.py    # Claude API integration
│       ├── confidence.py    # Confidence scoring and action routing
│       └── property_context.py
├── schema.sql               # PostgreSQL database schema
├── thinking.md              # System design thinking questions
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
LOG_LEVEL=INFO
```

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `ANTHROPIC_MODEL` | No | Claude model to use (default: `claude-sonnet-4-20250514`) |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

Health check: `GET http://localhost:8000/health`

API docs: `http://localhost:8000/docs`

## API Usage

### POST /webhook/message

**Sample Request:**

```bash
curl -X POST http://localhost:8000/webhook/message \
  -H "Content-Type: application/json" \
  -d '{
    "source": "whatsapp",
    "guest_name": "Rahul Sharma",
    "message": "Is the villa available from April 20 to 24? What is the rate for 2 adults?",
    "timestamp": "2026-05-05T10:30:00Z",
    "booking_ref": "NIS-2024-0891",
    "property_id": "villa-b1"
  }'
```

**Sample Response:**

```json
{
  "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "query_type": "pre_sales_availability",
  "drafted_reply": "Hi Rahul! I'm happy to confirm Villa B1 is available from April 20–24. The rate for 2 adults is INR 18,000 per night, so the total for your 4-night stay would be INR 72,000. The villa includes 3 bedrooms and a private pool in Assagao, North Goa. Would you like to proceed with the booking?",
  "confidence_score": 0.92,
  "action": "auto_send"
}
```

**Supported Sources:** `whatsapp`, `booking_com`, `airbnb`, `instagram`, `direct`

**Query Types:** `pre_sales_availability`, `pre_sales_pricing`, `post_sales_checkin`, `special_request`, `complaint`, `general_enquiry`

## Confidence Scoring

Confidence scores determine how each message is routed. The scoring is programmatic (not from the LLM) and based on two factors:

### Base Confidence by Query Type

| Query Type | Base Score | Rationale |
|---|---|---|
| `pre_sales_availability` | 0.92 | Factual, property data is known |
| `pre_sales_pricing` | 0.90 | Factual, rate card is fixed |
| `post_sales_checkin` | 0.88 | Standard info, minor variability |
| `general_enquiry` | 0.85 | Usually straightforward |
| `special_request` | 0.72 | Requires operational verification |
| `complaint` | 0.45 | Needs human empathy and judgment |

### Modifiers

- **Ambiguity penalty:** Messages containing uncertain language ("maybe", "not sure", "confused") receive a -0.08 penalty per keyword (capped at -0.25).
- **Short message penalty:** Messages under 4 words receive -0.05 (too little context).
- **Long message penalty:** Messages over 50 words receive -0.03 (possible complexity).
- **Complaint cap:** Complaints are hard-capped at 0.55 maximum confidence.

### Action Routing

| Condition | Action | Meaning |
|---|---|---|
| Confidence > 0.85 | `auto_send` | Reply sent to guest automatically |
| Confidence 0.60 – 0.85 | `agent_review` | Draft queued for human review |
| Confidence < 0.60 OR complaint | `escalate` | Flagged for immediate staff attention |

## Assumptions

- Property context is hardcoded for this single-property assessment. In production, this would be fetched from a database per `property_id`.
- No database persistence is implemented in the API layer. The `schema.sql` represents the production schema design; the API returns responses without writing to a database.
- No authentication is implemented on the webhook endpoint. In production, each channel integration would have its own webhook signature verification.
- The Claude API is called synchronously per request. In production, a message queue (e.g., Redis + Celery) would decouple ingestion from processing.
- `booking_ref` and `property_id` are optional fields since pre-sales inquiries may not have them.
- Confidence scoring is fully programmatic and deterministic. The LLM is used only for classification and reply drafting, never for confidence estimation.
