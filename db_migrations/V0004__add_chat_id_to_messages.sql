ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS chat_id BIGINT;

CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id ON chat_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);