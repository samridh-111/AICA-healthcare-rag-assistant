import os
from fastapi import APIRouter, Query
from backend.overview.service import OverviewService
from backend.overview.schemas import PatientOverview

router = APIRouter(tags=["Patient Overview"])
overview_service = OverviewService()

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

@router.get("/overview", response_model=PatientOverview)
async def get_patient_overview(
    patient_id: str = Query(DEFAULT_PATIENT_ID),
    force_refresh: bool = Query(False)
):
    """Retrieve an aggregated overview of the patient's longitudinal health data."""
    return await overview_service.get_overview(patient_id, force_refresh)
