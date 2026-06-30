import logging
from typing import List, Optional
from backend.database.db import supabase
from backend.patient_memory.schemas import PatientMemoryRecord

logger = logging.getLogger(__name__)

class PatientMemoryRepository:
    @staticmethod
    def create(record: PatientMemoryRecord, embedding: List[float]) -> Optional[str]:
        """Insert a patient memory record with its vector embedding."""
        if not supabase:
            logger.warning("Supabase not configured. Mocking create patient memory.")
            return "mock-memory-id"
            
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        data["embedding"] = embedding
        
        try:
            response = supabase.table("patient_memories").insert(data).execute()
            if response.data:
                return response.data[0].get("id")
        except Exception as e:
            logger.error(f"Failed to insert patient memory: {e}")
        return None

    @staticmethod
    def get_by_patient(patient_id: str, limit: int = 50) -> List[PatientMemoryRecord]:
        """Get recent patient memories."""
        if not supabase:
            return []
            
        try:
            response = supabase.table("patient_memories").select("*") \
                .eq("patient_id", patient_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            return [PatientMemoryRecord(**row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to fetch memories for patient {patient_id}: {e}")
            return []

    @staticmethod
    def get_by_conversation(conversation_id: str) -> Optional[PatientMemoryRecord]:
        """Get a specific memory by its conversation ID."""
        if not supabase:
            return None
            
        try:
            response = supabase.table("patient_memories").select("*") \
                .eq("conversation_id", conversation_id) \
                .execute()
                
            if response.data:
                return PatientMemoryRecord(**response.data[0])
        except Exception as e:
            logger.error(f"Failed to fetch memory for conversation {conversation_id}: {e}")
        return None

    @staticmethod
    def get_all_for_patient(patient_id: str) -> List[PatientMemoryRecord]:
        """Get all memories for a patient without a limit."""
        if not supabase:
            return []
            
        try:
            # Note: For large datasets, pagination should be used.
            response = supabase.table("patient_memories").select("*") \
                .eq("patient_id", patient_id) \
                .order("created_at", desc=True) \
                .execute()
            
            return [PatientMemoryRecord(**row) for row in response.data]
        except Exception as e:
            logger.error(f"Failed to fetch all memories for patient {patient_id}: {e}")
            return []

    @staticmethod
    def delete(memory_id: str) -> bool:
        """Delete a memory by its ID."""
        if not supabase:
            return False
            
        try:
            supabase.table("patient_memories").delete().eq("id", memory_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
