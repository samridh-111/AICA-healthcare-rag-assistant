import os
from fastapi import APIRouter, Query
from backend.patient_memory.service import PatientMemoryService
from backend.patient_memory.schemas import PatientMemoryResponse

router = APIRouter(tags=["Patient Memory"])
memory_service = PatientMemoryService()

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

@router.get("/memory", response_model=PatientMemoryResponse)
def get_memories(patient_id: str = Query(DEFAULT_PATIENT_ID), limit: int = Query(50)):
    """Retrieve all memory summaries for a patient."""
    return memory_service.get_patient_memories(patient_id, limit=limit)
