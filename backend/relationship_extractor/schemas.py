from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class RelationshipType(str, Enum):
    PATIENT_HAS_CONDITION = "PATIENT_HAS_CONDITION"
    PATIENT_HAS_SYMPTOM = "PATIENT_HAS_SYMPTOM"
    PATIENT_TAKES_MEDICATION = "PATIENT_TAKES_MEDICATION"
    MEDICATION_TREATS_CONDITION = "MEDICATION_TREATS_CONDITION"
    LAB_SUPPORTS_DIAGNOSIS = "LAB_SUPPORTS_DIAGNOSIS"
    DOCTOR_RECOMMENDED_MEDICATION = "DOCTOR_RECOMMENDED_MEDICATION"
    CONDITION_CAUSES_SYMPTOM = "CONDITION_CAUSES_SYMPTOM"
    FOLLOWUP_FOR_CONDITION = "FOLLOWUP_FOR_CONDITION"
    MEDICATION_HAS_SIDE_EFFECT = "MEDICATION_HAS_SIDE_EFFECT"

class MedicalRelationship(BaseModel):
    id: Optional[str] = None
    patient_id: str
    source_entity_id: Optional[str] = None  # UUID of source entity
    target_entity_id: Optional[str] = None  # UUID of target entity
    source_entity_value: str  # Human-readable source
    target_entity_value: str  # Human-readable target
    relationship_type: RelationshipType
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_conversation_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class RelationshipResponse(BaseModel):
    relationships: List[MedicalRelationship]
    total_count: int
    patient_id: str
