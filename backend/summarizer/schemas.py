from pydantic import BaseModel, Field
from typing import List

class VitalsSummary(BaseModel):
    blood_pressure: str = ""
    heart_rate: str = ""
    temperature: str = ""
    spo2: str = ""
    blood_glucose: str = ""
    weight: str = ""

class ConversationSummary(BaseModel):
    summary: str = ""
    chief_complaint: str = ""
    symptoms: List[str] = Field(default_factory=list)
    resolved_symptoms: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    resolved_conditions: List[str] = Field(default_factory=list)
    diagnoses: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    lab_tests: List[str] = Field(default_factory=list)
    doctor_recommendations: List[str] = Field(default_factory=list)
    follow_up: str = ""
    risk_level: str = ""  # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    vitals: VitalsSummary = Field(default_factory=VitalsSummary)
