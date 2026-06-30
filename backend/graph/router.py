import os
from fastapi import APIRouter, Query, Path
from typing import List
from backend.graph.service import GraphService
from backend.graph.schemas import PatientGraph, GraphNode

router = APIRouter(tags=["Knowledge Graph"])
graph_service = GraphService()

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

@router.get("/graph", response_model=PatientGraph)
async def get_graph(patient_id: str = Query(DEFAULT_PATIENT_ID)):
    """Retrieve the full patient knowledge graph."""
    return await graph_service.get_patient_graph(patient_id)

@router.get("/graph/neighbors/{entity_id}", response_model=List[GraphNode])
async def get_neighbors(
    entity_id: str = Path(...), 
    depth: int = Query(1)
):
    """Retrieve neighboring entities in the knowledge graph."""
    return await graph_service.get_entity_neighbors(entity_id, depth)
