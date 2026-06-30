import json
import logging
from typing import List, Dict, Any
from backend.groq.provider import get_llm_provider
from backend.prompts.entity_prompt import get_entity_extraction_system_prompt, get_entity_extraction_user_prompt
from backend.summarizer.schemas import ConversationSummary
from backend.entity_extractor.schemas import MedicalEntity, EntityType
from backend.entity_extractor.repository import EntityRepository
from backend.config import CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

class EntityExtractorService:
    def __init__(self):
        self.provider = get_llm_provider()
        
    def _create_entities_from_list(self, items: List[str], entity_type: EntityType, patient_id: str, conv_id: str, metadata: dict = None) -> List[MedicalEntity]:
        entities = []
        for item in items:
            if item.strip():
                entities.append(MedicalEntity(
                    patient_id=patient_id,
                    entity_type=entity_type,
                    value=item.strip(),
                    confidence=1.0,
                    source_conversation_id=conv_id,
                    metadata=metadata or {}
                ))
        return entities

    async def extract_entities(self, patient_id: str, conversation_id: str, summary: ConversationSummary) -> List[MedicalEntity]:
        all_entities: List[MedicalEntity] = []
        existing_values = set()
        
        # Helper to add entity and track value
        def add_entities(entities_list: List[MedicalEntity]):
            for e in entities_list:
                val = e.value.lower()
                if val not in existing_values:
                    existing_values.add(val)
                    all_entities.append(e)

        # 1. Phase 1 - Deterministic extraction from summary object
        
        # Patient
        add_entities([MedicalEntity(
            patient_id=patient_id, entity_type=EntityType.PATIENT, value=patient_id,
            confidence=1.0, source_conversation_id=conversation_id
        )])
        
        # Symptoms
        add_entities(self._create_entities_from_list(summary.symptoms, EntityType.SYMPTOM, patient_id, conversation_id))
        add_entities(self._create_entities_from_list(summary.resolved_symptoms, EntityType.SYMPTOM, patient_id, conversation_id, {"resolved": True}))
        
        # Conditions & Diagnoses
        add_entities(self._create_entities_from_list(summary.conditions, EntityType.CONDITION, patient_id, conversation_id))
        add_entities(self._create_entities_from_list(summary.resolved_conditions, EntityType.CONDITION, patient_id, conversation_id, {"resolved": True}))
        add_entities(self._create_entities_from_list(summary.diagnoses, EntityType.DIAGNOSIS, patient_id, conversation_id))
        
        # Meds, Allergies, Labs, Recommendations
        add_entities(self._create_entities_from_list(summary.medications, EntityType.MEDICATION, patient_id, conversation_id))
        add_entities(self._create_entities_from_list(summary.allergies, EntityType.ALLERGY, patient_id, conversation_id))
        add_entities(self._create_entities_from_list(summary.lab_tests, EntityType.LAB_TEST, patient_id, conversation_id))
        add_entities(self._create_entities_from_list(summary.doctor_recommendations, EntityType.RECOMMENDATION, patient_id, conversation_id))
        
        # Vitals
        vitals_dict = summary.vitals.model_dump()
        for k, v in vitals_dict.items():
            if v and v.strip():
                add_entities([MedicalEntity(
                    patient_id=patient_id, entity_type=EntityType.VITAL, value=f"{k}: {v}",
                    confidence=1.0, source_conversation_id=conversation_id
                )])

        # 2. Phase 2 - LLM Extraction for supplementary
        try:
            summary_json_str = summary.model_dump_json()
            response_str = await self.provider.generate(
                prompt=get_entity_extraction_user_prompt(summary_json_str),
                system_prompt=get_entity_extraction_system_prompt(),
                response_format={"type": "json_object"}
            )
            
            # The prompt asks for an array, but we forced JSON object.
            # Handle if LLM wraps it in a dict {"entities": [...]} or just returns list directly (if groq allows it with type:json_object)
            data = json.loads(response_str)
            llm_entities = data.get("entities", []) if isinstance(data, dict) else data
            
            if isinstance(llm_entities, list):
                for e in llm_entities:
                    if isinstance(e, dict):
                        e_type = e.get("type", "").lower()
                        e_val = e.get("value", "")
                        e_conf = float(e.get("confidence", 0.5))
                        
                        # Only add if we trust it and it's valid
                        if e_conf >= CONFIDENCE_THRESHOLD and e_val:
                            try:
                                valid_type = EntityType(e_type)
                                add_entities([MedicalEntity(
                                    patient_id=patient_id,
                                    entity_type=valid_type,
                                    value=e_val,
                                    confidence=e_conf,
                                    source_conversation_id=conversation_id,
                                    source_type="llm_extraction"
                                )])
                            except ValueError:
                                pass # Invalid enum type
        except Exception as e:
            logger.error(f"LLM Entity extraction failed: {e}")
            
        # 3. Persist
        EntityRepository.create_batch(all_entities)
        
        return all_entities
