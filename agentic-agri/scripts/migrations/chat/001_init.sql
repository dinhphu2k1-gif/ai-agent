-- Chat persistence schema (PostgreSQL 16+)
-- See docs/chat-sse-implementation-plan.md §4.3.12

CREATE SCHEMA IF NOT EXISTS chat;

CREATE TABLE chat.chat_channels (
    id              VARCHAR(64) PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    icon            VARCHAR(64) NOT NULL DEFAULT 'chat',
    category        VARCHAR(128),
    sort_order      INT NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chat.chat_threads (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id                  VARCHAR(64) NOT NULL REFERENCES chat.chat_channels(id),
    user_id                     VARCHAR(128) NOT NULL,
    langgraph_thread_id         VARCHAR(256) NOT NULL,
    pending_prompt_message_id   UUID,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_thread_user_channel UNIQUE (channel_id, user_id),
    CONSTRAINT uq_langgraph_thread UNIQUE (langgraph_thread_id)
);

CREATE TABLE chat.chat_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id           UUID NOT NULL REFERENCES chat.chat_threads(id) ON DELETE CASCADE,
    status              VARCHAR(32) NOT NULL,
    trigger_type        VARCHAR(16) NOT NULL,
    request_payload     JSONB NOT NULL DEFAULT '{}',
    user_message_id     UUID,
    agent_message_id    UUID,
    last_event_id       VARCHAR(64),
    idempotency_key     VARCHAR(128),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    error_code          VARCHAR(64),
    error_message       TEXT,
    CONSTRAINT chk_run_status CHECK (
        status IN ('queued','running','completed','failed','cancelled')
    )
);

CREATE UNIQUE INDEX uq_run_active_per_thread
    ON chat.chat_runs (thread_id)
    WHERE status IN ('queued', 'running');

CREATE UNIQUE INDEX uq_run_idempotency
    ON chat.chat_runs (thread_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE chat.chat_messages (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id               UUID NOT NULL REFERENCES chat.chat_threads(id) ON DELETE CASCADE,
    run_id                  UUID REFERENCES chat.chat_runs(id) ON DELETE SET NULL,
    sender                  VARCHAR(32) NOT NULL,
    content                 TEXT,
    agent_data              JSONB,
    prompt_data             JSONB,
    status                  VARCHAR(32) NOT NULL DEFAULT 'final',
    reply_to_message_id     UUID REFERENCES chat.chat_messages(id) ON DELETE SET NULL,
    client_request_id       VARCHAR(64),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ,
    CONSTRAINT chk_sender CHECK (
        sender IN ('user','agent','system','action_prompt')
    ),
    CONSTRAINT chk_message_status CHECK (
        status IN ('final','pending','resolved','streaming','failed')
    ),
    CONSTRAINT chk_payload_shape CHECK (
        (sender IN ('user','system') AND agent_data IS NULL AND prompt_data IS NULL)
        OR (sender = 'agent' AND agent_data IS NOT NULL)
        OR (sender = 'action_prompt' AND prompt_data IS NOT NULL)
        OR (sender = 'user')
    )
);

CREATE INDEX idx_messages_thread_created
    ON chat.chat_messages (thread_id, created_at DESC);

CREATE INDEX idx_messages_pending_prompt
    ON chat.chat_messages (thread_id)
    WHERE sender = 'action_prompt' AND status = 'pending';

ALTER TABLE chat.chat_threads
    ADD CONSTRAINT fk_pending_prompt
    FOREIGN KEY (pending_prompt_message_id)
    REFERENCES chat.chat_messages(id) ON DELETE SET NULL;

ALTER TABLE chat.chat_runs
    ADD CONSTRAINT fk_run_user_message
    FOREIGN KEY (user_message_id) REFERENCES chat.chat_messages(id) ON DELETE SET NULL;

ALTER TABLE chat.chat_runs
    ADD CONSTRAINT fk_run_agent_message
    FOREIGN KEY (agent_message_id) REFERENCES chat.chat_messages(id) ON DELETE SET NULL;

CREATE TABLE chat.chat_run_events (
    id              BIGSERIAL PRIMARY KEY,
    run_id          UUID NOT NULL REFERENCES chat.chat_runs(id) ON DELETE CASCADE,
    event_name      VARCHAR(64) NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_run_events_run_id ON chat.chat_run_events (run_id, id);

INSERT INTO chat.chat_channels (id, title, icon, category, sort_order) VALUES
    ('threat-intel', 'threat-intel-global', 'shield', 'Active Channels', 10),
    ('network-anomaly', 'network-anomaly-detect', 'hub', 'Active Channels', 20),
    ('insider-risk', 'insider-risk-alerts', 'person_alert', 'Active Channels', 30),
    ('market-trends', 'Market Trends', 'trending_up', NULL, 0)
ON CONFLICT (id) DO NOTHING;
