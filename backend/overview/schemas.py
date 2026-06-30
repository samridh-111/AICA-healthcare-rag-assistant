from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PatientOverview(BaseModel):
    patient_id: str
    overall_health_summary: str = ""
    active_conditions: List[str] = Field(default_factory=list)
    resolved_conditions: List[str] = Field(default_factory=list)
    medication_history: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    recurring_symptoms: List[str] = Field(default_factory=list)
    recent_recommendations: List[str] = Field(default_factory=list)
    overall_risk: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    key_concerns: List[str] = Field(default_factory=list)
    most_recent_consultation: Optional[str] = None  # ISO timestamp
    consultation_count: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
