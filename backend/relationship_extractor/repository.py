import logging
from typing import List, Optional
from backend.database.db import supabase
from backend.relationship_extractor.schemas import MedicalRelationship

logger = logging.getLogger(__name__)

class RelationshipRepository:
    @staticmethod
    def create(relationship: MedicalRelationship) -> Optional[str]:
        if not supabase:
            return "mock-rel-id"
            
        data = relationship.model_dump(exclude={"id"}, exclude_none=True)
        if hasattr(data.get('relationship_type'), 'value'):
            data['relationship_type'] = data['relationship_type'].value
            
        try:
            response = supabase.table("medical_relationships").insert(data).execute()
            if response.data:
                return response.data[0].get("id")
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
        return None

    @staticmethod
    def create_batch(relationships: List[MedicalRelationship]) -> int:
        if not supabase or not relationships:
            return len(relationships) if not supabase else 0
            
        batch_data = []
        for r in relationships:
            d = r.model_dump(exclude={"id"}, exclude_none=True)
            if hasattr(d.get('relationship_type'), 'value'):
                d['relationship_type'] = d['relationship_type'].value
            batch_data.append(d)
            
        try:
            response = supabase.table("medical_relationships").insert(batch_data).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Failed to bulk insert relationships: {e}")
            return 0

    @staticmethod
    def get_by_patient(patient_id: str, relationship_type: Optional[str] = None, limit: int = 100) -> List[MedicalRelationship]:
        if not supabase:
            return []
            
        try:
            query = supabase.table("medical_relationships").select("*").eq("patient_id", patient_id)
            if relationship_type:
                query = query.eq("relationship_type", relationship_type)
                
            response = query.order("created_at", desc=True).limit(limit).execute()
            return [MedicalRelationship(**row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to fetch relationships for patient {patient_id}: {e}")
            return []

    @staticmethod
    def get_by_entity(entity_id: str) -> List[MedicalRelationship]:
        if not supabase:
            return []
            
        try:
            # Query relationships where entity is source
            src_resp = supabase.table("medical_relationships").select("*").eq("source_entity_id", entity_id).execute()
            # Query relationships where entity is target
            tgt_resp = supabase.table("medical_relationships").select("*").eq("target_entity_id", entity_id).execute()
            
            combined = src_resp.data + tgt_resp.data
            # Deduplicate by id
            unique = {row["id"]: row for row in combined}.values()
            
            return [MedicalRelationship(**row) for row in unique]
        except Exception as e:
            logger.error(f"Failed to fetch relationships for entity {entity_id}: {e}")
            return []

    @staticmethod
    def get_by_conversation(conversation_id: str) -> List[MedicalRelationship]:
        if not supabase:
            return []
            
        try:
            response = supabase.table("medical_relationships").select("*").eq("source_conversation_id", conversation_id).execute()
            return [MedicalRelationship(**row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to fetch relationships for conversation {conversation_id}: {e}")
            return []

    @staticmethod
    def delete(relationship_id: str) -> bool:
        if not supabase:
            return False
            
        try:
            supabase.table("medical_relationships").delete().eq("id", relationship_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete relationship {relationship_id}: {e}")
            return False
