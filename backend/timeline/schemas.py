from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class EventType(str, Enum):
    CONVERSATION = "conversation"
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    MEDICAL_SCAN = "medical_scan"
    DOCTOR_RECOMMENDATION = "doctor_recommendation"
    MEDICATION_CHANGE = "medication_change"
    FOLLOW_UP = "follow_up"
    RISK_ASSESSMENT = "risk_assessment"
    VITAL_RECORDING = "vital_recording"
    VIDEO_ANALYSIS = "video_analysis"

class TimelineEvent(BaseModel):
    date: str
    event_type: EventType
    title: str
    summary: str
    source: str = "system"  # conversation, upload, system
    metadata: dict = Field(default_factory=dict)

class TimelineResponse(BaseModel):
    patient_id: str
    events: List[TimelineEvent]
    total_count: int
