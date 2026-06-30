from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from backend.summarizer.schemas import ConversationSummary

class PatientMemoryCreate(BaseModel):
    patient_id: str
    conversation_id: str
    summary: ConversationSummary

class PatientMemoryRecord(BaseModel):
    id: Optional[str] = None
    patient_id: str
    conversation_id: str
    summary_json: dict  # The full ConversationSummary as dict
    summary_text: str   # Human-readable summary text
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class PatientMemoryResponse(BaseModel):
    memories: List[PatientMemoryRecord]
    total_count: int
    patient_id: str
