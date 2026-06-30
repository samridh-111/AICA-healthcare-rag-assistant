import logging
from typing import List, Optional
from backend.database.db import supabase
from backend.entity_extractor.schemas import MedicalEntity

logger = logging.getLogger(__name__)

class EntityRepository:
    @staticmethod
    def create(entity: MedicalEntity) -> Optional[str]:
        if not supabase:
            logger.warning("Supabase not configured. Mocking create entity.")
            return "mock-entity-id"
            
        data = entity.model_dump(exclude={"id"}, exclude_none=True)
        # Ensure enum is stringified
        if hasattr(data.get('entity_type'), 'value'):
            data['entity_type'] = data['entity_type'].value
            
        try:
            response = supabase.table("medical_entities").insert(data).execute()
            if response.data:
                return response.data[0].get("id")
        except Exception as e:
            logger.error(f"Failed to create entity: {e}")
        return None

    @staticmethod
    def create_batch(entities: List[MedicalEntity]) -> int:
        if not supabase or not entities:
            return len(entities) if not supabase else 0
            
        batch_data = []
        for e in entities:
            d = e.model_dump(exclude={"id"}, exclude_none=True)
            if hasattr(d.get('entity_type'), 'value'):
                d['entity_type'] = d['entity_type'].value
            batch_data.append(d)
            
        try:
            response = supabase.table("medical_entities").insert(batch_data).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Failed to bulk insert entities: {e}")
            return 0

    @staticmethod
    def get_by_patient(patient_id: str, entity_type: Optional[str] = None, limit: int = 100) -> List[MedicalEntity]:
        if not supabase:
            return []
            
        try:
            query = supabase.table("medical_entities").select("*").eq("patient_id", patient_id)
            if entity_type:
                query = query.eq("entity_type", entity_type)
                
            response = query.order("created_at", desc=True).limit(limit).execute()
            return [MedicalEntity(**row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to fetch entities for patient {patient_id}: {e}")
            return []

    @staticmethod
    def get_by_id(entity_id: str) -> Optional[MedicalEntity]:
        if not supabase:
            return None
            
        try:
            response = supabase.table("medical_entities").select("*").eq("id", entity_id).execute()
            if response.data:
                return MedicalEntity(**response.data[0])
        except Exception as e:
            logger.error(f"Failed to fetch entity {entity_id}: {e}")
        return None

    @staticmethod
    def get_by_conversation(conversation_id: str) -> List[MedicalEntity]:
        if not supabase:
            return []
            
        try:
            response = supabase.table("medical_entities").select("*").eq("source_conversation_id", conversation_id).execute()
            return [MedicalEntity(**row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to fetch entities for conversation {conversation_id}: {e}")
            return []

    @staticmethod
    def delete(entity_id: str) -> bool:
        if not supabase:
            return False
            
        try:
            supabase.table("medical_entities").delete().eq("id", entity_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {e}")
            return False

    @staticmethod
    def search_by_value(patient_id: str, value: str) -> List[MedicalEntity]:
        if not supabase:
            return []
            
        try:
            response = supabase.table("medical_entities").select("*") \
                .eq("patient_id", patient_id) \
                .ilike("value", f"%{value}%") \
                .execute()
            return [MedicalEntity(**row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to search entities for {value}: {e}")
            return []
