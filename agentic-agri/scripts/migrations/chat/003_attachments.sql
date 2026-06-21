-- Phase 5: attachments
CREATE TABLE IF NOT EXISTS chat.chat_attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id      VARCHAR(64) NOT NULL REFERENCES chat.chat_channels(id) ON DELETE CASCADE,
    thread_id       UUID REFERENCES chat.chat_threads(id) ON DELETE SET NULL,
    uploader_id     VARCHAR(128) NOT NULL,
    file_name       VARCHAR(512) NOT NULL,
    mime_type       VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream',
    size_bytes      BIGINT NOT NULL DEFAULT 0,
    storage_path    TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_attachments_channel
    ON chat.chat_attachments (channel_id, created_at DESC);

CREATE TABLE IF NOT EXISTS chat.chat_message_attachments (
    message_id      UUID NOT NULL REFERENCES chat.chat_messages(id) ON DELETE CASCADE,
    attachment_id   UUID NOT NULL REFERENCES chat.chat_attachments(id) ON DELETE CASCADE,
    CONSTRAINT pk_message_attachment PRIMARY KEY (message_id, attachment_id)
);
