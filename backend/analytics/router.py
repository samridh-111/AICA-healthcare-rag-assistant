import os
from fastapi import APIRouter, Query
from backend.analytics.service import AnalyticsService
from backend.analytics.schemas import AnalyticsResponse

router = APIRouter(tags=["Analytics"])
analytics_service = AnalyticsService()

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(patient_id: str = Query(DEFAULT_PATIENT_ID)):
    """Retrieve Chart.js compatible analytics for a patient."""
    return analytics_service.get_analytics(patient_id)
