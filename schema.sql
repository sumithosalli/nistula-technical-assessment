CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE guests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       VARCHAR(255) NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(50),
    whatsapp_id     VARCHAR(100),
    booking_com_id  VARCHAR(100),
    airbnb_id       VARCHAR(100),
    instagram_id    VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_guest_email UNIQUE (email)
);

CREATE INDEX idx_guests_phone ON guests (phone);
CREATE INDEX idx_guests_whatsapp ON guests (whatsapp_id);

CREATE TABLE reservations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id        UUID NOT NULL REFERENCES guests(id) ON DELETE CASCADE,
    booking_ref     VARCHAR(50) NOT NULL UNIQUE,
    property_id     VARCHAR(50) NOT NULL,
    check_in_date   DATE NOT NULL,
    check_out_date  DATE NOT NULL,
    guest_count     INT NOT NULL DEFAULT 1,
    total_amount    DECIMAL(12, 2),
    status          VARCHAR(20) NOT NULL DEFAULT 'confirmed'
                    CHECK (status IN ('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled')),
    source_channel  VARCHAR(20) NOT NULL
                    CHECK (source_channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reservations_guest ON reservations (guest_id);
CREATE INDEX idx_reservations_property ON reservations (property_id);
CREATE INDEX idx_reservations_dates ON reservations (check_in_date, check_out_date);

CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id        UUID NOT NULL REFERENCES guests(id) ON DELETE CASCADE,
    reservation_id  UUID REFERENCES reservations(id) ON DELETE SET NULL,
    source_channel  VARCHAR(20) NOT NULL
                    CHECK (source_channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')),
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'resolved', 'escalated')),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_guest ON conversations (guest_id);
CREATE INDEX idx_conversations_reservation ON conversations (reservation_id);
CREATE INDEX idx_conversations_status ON conversations (status);

CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    direction       VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    sender_type     VARCHAR(10) NOT NULL CHECK (sender_type IN ('guest', 'ai', 'agent')),
    content         TEXT NOT NULL,
    source_channel  VARCHAR(20) NOT NULL
                    CHECK (source_channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')),
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages (conversation_id);
CREATE INDEX idx_messages_sent_at ON messages (sent_at);

CREATE TABLE ai_processing (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id          UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    query_type          VARCHAR(30) NOT NULL
                        CHECK (query_type IN (
                            'pre_sales_availability', 'pre_sales_pricing',
                            'post_sales_checkin', 'special_request',
                            'complaint', 'general_enquiry'
                        )),
    drafted_reply       TEXT NOT NULL,
    final_reply         TEXT,
    confidence_score    DECIMAL(4, 2) NOT NULL,
    action_taken        VARCHAR(20) NOT NULL
                        CHECK (action_taken IN ('auto_sent', 'agent_reviewed', 'escalated')),
    agent_edited        BOOLEAN NOT NULL DEFAULT FALSE,
    agent_id            UUID,
    llm_model           VARCHAR(100),
    llm_latency_ms      INT,
    processed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_processing_message ON ai_processing (message_id);
CREATE INDEX idx_ai_processing_query_type ON ai_processing (query_type);
CREATE INDEX idx_ai_processing_action ON ai_processing (action_taken);

/*
DESIGN NOTES

Table Relationships:
- guests is the unified profile table. A single guest can have identifiers across all channels
  (WhatsApp, Booking.com, Airbnb, Instagram, direct). This avoids duplicate profiles when the
  same person contacts via different platforms.
- reservations links to guests via guest_id. One guest can have multiple reservations.
- conversations links to both guests and optionally to reservations. Pre-sales conversations
  exist without a reservation; post-booking conversations are tied to one.
- messages belongs to a conversation. All inbound and outbound messages from every channel are
  stored in this single table, distinguished by direction and sender_type.
- ai_processing stores AI metadata associated with an inbound message. It stores the AI draft,
  the final reply (which may differ if an agent edited it), confidence score, query
  classification, and whether the reply was auto-sent, agent-reviewed, or escalated.

Hardest Schema Decision:
Whether to separate messages by channel into different tables or unify them. Unification was
chosen because the core message structure is identical across channels, queries and analytics
need to span all channels, and the source_channel column provides filtering when needed.
The tradeoff is that channel-specific metadata (e.g., WhatsApp message IDs, Booking.com
thread references) would need a separate key-value extension table if required later, but for
the current scope a single messages table keeps the schema simple and queryable.
*/
