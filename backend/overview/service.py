import json
import time
import logging
from typing import Dict, Tuple

from backend.groq.provider import get_llm_provider
from backend.prompts.overview_prompt import get_overview_system_prompt, get_overview_user_prompt
from backend.patient_memory.repository import PatientMemoryRepository
from backend.database.db import DatabaseManager
from backend.overview.schemas import PatientOverview
from backend.config import OVERVIEW_CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)

class OverviewService:
    def __init__(self):
        self.provider = get_llm_provider()
        self._cache: Dict[str, Tuple[PatientOverview, float]] = {}
        
    async def get_overview(self, patient_id: str, force_refresh: bool = False) -> PatientOverview:
        # Check cache
        if not force_refresh and patient_id in self._cache:
            overview, timestamp = self._cache[patient_id]
            if time.time() - timestamp < OVERVIEW_CACHE_TTL_SECONDS:
                return overview
                
        # Get memories
        memories = PatientMemoryRepository.get_all_for_patient(patient_id)
        
        # Get base data
        medications = DatabaseManager.get_medications(patient_id)
        current_meds = [m.medicine for m in medications]
        
        risk_history = DatabaseManager.get_risk_history(patient_id, limit=1)
        latest_risk = risk_history[0] if risk_history else None
        overall_risk = latest_risk.severity if latest_risk else "LOW"
        
        if not memories:
            # Basic overview if no conversational memory
            overview = PatientOverview(
                patient_id=patient_id,
                overall_health_summary="No conversational memories available.",
                current_medications=current_meds,
                overall_risk=overall_risk,
                consultation_count=0
            )
            self._cache[patient_id] = (overview, time.time())
            return overview
            
        # Combine memory summaries
        summaries_json = [m.summary_json for m in memories]
        memories_json_str = json.dumps(summaries_json, indent=2)
        
        # Ask LLM to generate overview
        try:
            response_str = await self.provider.generate(
                prompt=get_overview_user_prompt(memories_json_str),
                system_prompt=get_overview_system_prompt(),
                response_format={"type": "json_object"}
            )
            data = json.loads(response_str)
        except Exception as e:
            logger.error(f"Failed to generate overview: {e}")
            data = {}
            
        # Compile
        overview = PatientOverview(
            patient_id=patient_id,
            overall_health_summary=data.get("overall_health_summary", ""),
            active_conditions=data.get("active_conditions", []),
            resolved_conditions=data.get("resolved_conditions", []),
            medication_history=data.get("medication_history", []),
            current_medications=data.get("current_medications", current_meds),
            allergies=data.get("allergies", []),
            recurring_symptoms=data.get("recurring_symptoms", []),
            recent_recommendations=data.get("recent_recommendations", []),
            overall_risk=data.get("overall_risk", overall_risk),
            key_concerns=data.get("key_concerns", []),
            most_recent_consultation=memories[0].created_at if memories else None,
            consultation_count=len(memories)
        )
        
        # Update cache
        self._cache[patient_id] = (overview, time.time())
        return overview

    def invalidate_cache(self, patient_id: str) -> None:
        if patient_id in self._cache:
            del self._cache[patient_id]
