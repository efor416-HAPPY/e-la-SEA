-- src/database/schema.sql

-- 에이전트 자가진단 및 토큰 무결성 검증용 구조
CREATE TABLE IF NOT EXISTS AgentRegistry (
    agent_name TEXT PRIMARY KEY,
    auth_token TEXT NOT NULL,
    status TEXT DEFAULT 'IDLE',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 가벼운 대화 히스토리 및 컨텍스트 요약본 캐싱 (LLM 토큰 절약용)
CREATE TABLE IF NOT EXISTS MemoryContext (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_text TEXT NOT NULL,
    importance_score REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
