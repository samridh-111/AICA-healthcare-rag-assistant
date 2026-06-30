CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS patient_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    summary_json JSONB NOT NULL,
    summary_text TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_memories_patient_id ON patient_memories(patient_id);
