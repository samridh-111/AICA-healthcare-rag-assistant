import os
from fastapi import APIRouter, Query
from typing import Optional
from backend.timeline.service import TimelineService
from backend.timeline.schemas import TimelineResponse

router = APIRouter(tags=["Timeline"])
timeline_service = TimelineService()

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    patient_id: str = Query(DEFAULT_PATIENT_ID),
    limit: int = Query(100),
    event_type: Optional[str] = Query(None)
):
    """Retrieve an enriched timeline of all patient events."""
    return timeline_service.get_timeline(patient_id, limit, event_type)
