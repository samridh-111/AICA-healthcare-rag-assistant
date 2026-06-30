import json
import logging
from typing import List, Dict, Any, Optional
from backend.groq.provider import get_llm_provider
from backend.prompts.relationship_prompt import get_relationship_extraction_system_prompt, get_relationship_extraction_user_prompt
from backend.summarizer.schemas import ConversationSummary
from backend.entity_extractor.schemas import MedicalEntity, EntityType
from backend.relationship_extractor.schemas import MedicalRelationship, RelationshipType
from backend.relationship_extractor.repository import RelationshipRepository
from backend.config import CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

class RelationshipExtractorService:
    def __init__(self):
        self.provider = get_llm_provider()
        
    def _find_entity_id_by_value(self, entities: List[MedicalEntity], value: str) -> Optional[str]:
        val_lower = value.lower()
        for e in entities:
            if e.value.lower() == val_lower:
                return e.id
        return None

    def _get_patient_entity(self, entities: List[MedicalEntity]) -> Optional[MedicalEntity]:
        for e in entities:
            if e.entity_type == EntityType.PATIENT:
                return e
        return None

    async def extract_relationships(self, patient_id: str, conversation_id: str, summary: ConversationSummary, entities: List[MedicalEntity]) -> List[MedicalRelationship]:
        all_relationships: List[MedicalRelationship] = []
        existing_signatures = set()
        
        def get_signature(rel: MedicalRelationship):
            return f"{rel.source_entity_value.lower()}|{rel.target_entity_value.lower()}|{rel.relationship_type.value}"
            
        def add_relationships(rels: List[MedicalRelationship]):
            for r in rels:
                sig = get_signature(r)
                if sig not in existing_signatures:
                    existing_signatures.add(sig)
                    all_relationships.append(r)

        # 1. Phase 1 - Deterministic extraction
        patient_entity = self._get_patient_entity(entities)
        pat_id = patient_entity.id if patient_entity else None
        
        if patient_entity:
            for e in entities:
                if e.entity_type == EntityType.SYMPTOM:
                    add_relationships([MedicalRelationship(
                        patient_id=patient_id,
                        source_entity_id=pat_id, target_entity_id=e.id,
                        source_entity_value=patient_entity.value, target_entity_value=e.value,
                        relationship_type=RelationshipType.PATIENT_HAS_SYMPTOM,
                        confidence=1.0, source_conversation_id=conversation_id
                    )])
                elif e.entity_type == EntityType.CONDITION:
                    add_relationships([MedicalRelationship(
                        patient_id=patient_id,
                        source_entity_id=pat_id, target_entity_id=e.id,
                        source_entity_value=patient_entity.value, target_entity_value=e.value,
                        relationship_type=RelationshipType.PATIENT_HAS_CONDITION,
                        confidence=1.0, source_conversation_id=conversation_id
                    )])
                elif e.entity_type == EntityType.MEDICATION:
                    add_relationships([MedicalRelationship(
                        patient_id=patient_id,
                        source_entity_id=pat_id, target_entity_id=e.id,
                        source_entity_value=patient_entity.value, target_entity_value=e.value,
                        relationship_type=RelationshipType.PATIENT_TAKES_MEDICATION,
                        confidence=1.0, source_conversation_id=conversation_id
                    )])
                    
        # Simple deterministic rule for follow_up -> condition
        if summary.follow_up and summary.conditions:
            for c in summary.conditions:
                c_id = self._find_entity_id_by_value(entities, c)
                add_relationships([MedicalRelationship(
                    patient_id=patient_id,
                    source_entity_id=pat_id, target_entity_id=c_id,
                    source_entity_value=summary.follow_up, target_entity_value=c,
                    relationship_type=RelationshipType.FOLLOWUP_FOR_CONDITION,
                    confidence=0.8, source_conversation_id=conversation_id
                )])

        # 2. Phase 2 - LLM Extraction
        try:
            entities_json_str = json.dumps([e.model_dump() for e in entities], default=str)
            summary_json_str = summary.model_dump_json()
            
            response_str = await self.provider.generate(
                prompt=get_relationship_extraction_user_prompt(entities_json_str, summary_json_str),
                system_prompt=get_relationship_extraction_system_prompt(),
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response_str)
            llm_rels = data.get("relationships", []) if isinstance(data, dict) else data
            
            if isinstance(llm_rels, list):
                for r in llm_rels:
                    if isinstance(r, dict):
                        src_val = r.get("source_entity_value", "")
                        tgt_val = r.get("target_entity_value", "")
                        r_type = r.get("relationship_type", "")
                        r_conf = float(r.get("confidence", 0.5))
                        
                        if src_val and tgt_val and r_conf >= CONFIDENCE_THRESHOLD:
                            try:
                                valid_type = RelationshipType(r_type)
                                src_id = self._find_entity_id_by_value(entities, src_val)
                                tgt_id = self._find_entity_id_by_value(entities, tgt_val)
                                
                                add_relationships([MedicalRelationship(
                                    patient_id=patient_id,
                                    source_entity_id=src_id,
                                    target_entity_id=tgt_id,
                                    source_entity_value=src_val,
                                    target_entity_value=tgt_val,
                                    relationship_type=valid_type,
                                    confidence=r_conf,
                                    source_conversation_id=conversation_id
                                )])
                            except ValueError:
                                pass # Invalid enum type
        except Exception as e:
            logger.error(f"LLM Relationship extraction failed: {e}")
            
        # 3. Persist
        RelationshipRepository.create_batch(all_relationships)
        
        return all_relationships
