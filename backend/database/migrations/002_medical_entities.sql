CREATE TABLE IF NOT EXISTS medical_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    source_conversation_id TEXT,
    source_type TEXT DEFAULT 'conversation',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medical_entities_patient_id ON medical_entities(patient_id);
CREATE INDEX IF NOT EXISTS idx_medical_entities_entity_type ON medical_entities(entity_type);
