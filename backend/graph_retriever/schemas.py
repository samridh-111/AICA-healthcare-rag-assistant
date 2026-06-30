from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class IntentType(str, Enum):
    GENERAL_MEDICAL = "general_medical"
    PATIENT_SPECIFIC = "patient_specific"
    MEDICATION_RELATED = "medication_related"
    CONDITION_RELATED = "condition_related"
    LAB_RELATED = "lab_related"
    RECOMMENDATION = "recommendation"
    VITAL_RELATED = "vital_related"
    HISTORY = "history"

class QueryIntent(BaseModel):
    intent_type: IntentType
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extracted_entities: List[str] = Field(default_factory=list)  # key terms extracted from query

class ContextChunk(BaseModel):
    content: str
    source: str  # "vector" or "graph"
    relevance_score: float = 0.0
    metadata: dict = Field(default_factory=dict)

class HybridContext(BaseModel):
    query: str
    intent: QueryIntent
    vector_chunks: List[ContextChunk] = Field(default_factory=list)
    graph_chunks: List[ContextChunk] = Field(default_factory=list)
    merged_context: str = ""
    total_chunks: int = 0
