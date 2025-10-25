CREATE TABLE IF NOT EXISTS telegram_bots (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER REFERENCES api_keys(id),
    telegram_token VARCHAR(255) UNIQUE NOT NULL,
    bot_username VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    webhook_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lua_knowledge_base (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    description TEXT,
    code_example TEXT,
    explanation TEXT,
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telegram_bots_api_key ON telegram_bots(api_key_id);
CREATE INDEX idx_telegram_bots_active ON telegram_bots(is_active);
CREATE INDEX idx_lua_kb_category ON lua_knowledge_base(category);
CREATE INDEX idx_lua_kb_keywords ON lua_knowledge_base USING GIN(keywords);
