from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class GraphNode(BaseModel):
    id: str
    label: str  # entity type
    properties: dict = Field(default_factory=dict)  # entity value, confidence, etc.
    
class GraphEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    properties: dict = Field(default_factory=dict)  # confidence, metadata

class PatientGraph(BaseModel):
    patient_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
