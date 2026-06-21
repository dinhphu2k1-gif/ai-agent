-- Channel RBAC (Phase 4)
CREATE TABLE IF NOT EXISTS chat.chat_channel_members (
    channel_id  VARCHAR(64) NOT NULL REFERENCES chat.chat_channels(id) ON DELETE CASCADE,
    user_id     VARCHAR(128) NOT NULL,
    role        VARCHAR(32) NOT NULL DEFAULT 'participant',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_channel_member PRIMARY KEY (channel_id, user_id),
    CONSTRAINT chk_member_role CHECK (role IN ('viewer', 'participant', 'admin'))
);

CREATE INDEX IF NOT EXISTS idx_channel_members_user
    ON chat.chat_channel_members (user_id);

-- Dev/staging: grant default test user access to all seeded channels
INSERT INTO chat.chat_channel_members (channel_id, user_id, role)
SELECT id, 'dev-user', 'participant'
FROM chat.chat_channels
WHERE is_active = TRUE
ON CONFLICT (channel_id, user_id) DO NOTHING;
