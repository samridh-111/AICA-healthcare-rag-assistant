CREATE TABLE IF NOT EXISTS medical_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id TEXT NOT NULL,
    source_entity_id UUID REFERENCES medical_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES medical_entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    source_conversation_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medical_relationships_patient_id ON medical_relationships(patient_id);
CREATE INDEX IF NOT EXISTS idx_medical_relationships_type ON medical_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_medical_relationships_source_id ON medical_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_medical_relationships_target_id ON medical_relationships(target_entity_id);
