from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    PATIENT = "patient"
    CONDITION = "condition"
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    DIAGNOSIS = "diagnosis"
    LAB_TEST = "lab_test"
    VITAL = "vital"
    DOCTOR = "doctor"
    RECOMMENDATION = "recommendation"
    MEDICAL_DEVICE = "medical_device"
    PROCEDURE = "procedure"

class MedicalEntity(BaseModel):
    id: Optional[str] = None
    patient_id: str
    entity_type: EntityType
    value: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_conversation_id: Optional[str] = None
    source_type: str = "conversation"  # conversation, upload, extraction
    metadata: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class EntityResponse(BaseModel):
    entities: List[MedicalEntity]
    total_count: int
    patient_id: str
