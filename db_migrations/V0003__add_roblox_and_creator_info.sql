ALTER TABLE lua_knowledge_base ADD COLUMN IF NOT EXISTS is_roblox BOOLEAN DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_lua_kb_roblox ON lua_knowledge_base(is_roblox);

CREATE TABLE IF NOT EXISTS creator_info (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO creator_info (key, value) 
VALUES 
    ('creator_name', 'Мад Сатору'),
    ('creation_year', '2025'),
    ('creator_full', 'MadAI создал Мад Сатору в 2025 году')
ON CONFLICT (key) DO NOTHING;
