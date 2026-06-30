import logging
import uuid
from typing import List, Dict, Optional
from datetime import datetime

from backend.summarizer.service import SummarizerService
from backend.rag.embeddings import get_embedding_model
from backend.rag.vector_store import get_vector_store
from backend.patient_memory.repository import PatientMemoryRepository
from backend.patient_memory.schemas import PatientMemoryRecord, PatientMemoryResponse

logger = logging.getLogger(__name__)

class PatientMemoryService:
    def __init__(self):
        self.summarizer = SummarizerService()
        self.embedding_model = get_embedding_model()
        self.repository = PatientMemoryRepository()
        self.vector_store = get_vector_store()
        
    def _generate_human_readable_summary(self, summary) -> str:
        """Converts structured ConversationSummary into readable text."""
        parts = []
        if summary.chief_complaint:
            parts.append(f"Chief Complaint: {summary.chief_complaint}")
        if summary.summary:
            parts.append(f"Summary: {summary.summary}")
        if summary.symptoms:
            parts.append(f"Active Symptoms: {', '.join(summary.symptoms)}")
        if summary.conditions:
            parts.append(f"Conditions: {', '.join(summary.conditions)}")
        if summary.medications:
            parts.append(f"Medications: {', '.join(summary.medications)}")
        if summary.doctor_recommendations:
            parts.append(f"Recommendations: {', '.join(summary.doctor_recommendations)}")
            
        return "\n".join(parts) if parts else "No detailed summary available."

    async def create_memory(self, patient_id: str, conversation_id: str, conversation_history: List[Dict[str, str]]) -> Optional[PatientMemoryRecord]:
        """Creates a patient memory from a conversation history."""
        # 1. Summarize conversation
        summary_obj = await self.summarizer.summarize_conversation(conversation_history)
        
        # 2. Generate text summary
        summary_text = self._generate_human_readable_summary(summary_obj)
        
        # 3. Generate embedding for the summary text
        embedding = self.embedding_model.encode_single(summary_text)
        
        # 4. Create record
        record = PatientMemoryRecord(
            patient_id=patient_id,
            conversation_id=conversation_id,
            summary_json=summary_obj.model_dump(),
            summary_text=summary_text
        )
        
        # 5. Persist to Postgres
        memory_id = self.repository.create(record, embedding)
        if memory_id:
            record.id = memory_id
            
        # 6. Also add to Chroma/pgvector for standard RAG retrieval
        metadata = {
            "patient_id": patient_id,
            "conversation_id": conversation_id,
            "source_type": "patient_memory",
            "timestamp": record.created_at
        }
        
        # Generate a unique ID for the vector store
        vec_id = f"mem_{memory_id or uuid.uuid4().hex[:8]}"
        self.vector_store.add_raw_texts(
            texts=[summary_text],
            metadatas=[metadata],
            ids=[vec_id]
        )
        
        return record

    def get_patient_memories(self, patient_id: str, limit: int = 50) -> PatientMemoryResponse:
        """Retrieve paginated patient memories."""
        memories = self.repository.get_by_patient(patient_id, limit)
        return PatientMemoryResponse(
            memories=memories,
            total_count=len(memories),
            patient_id=patient_id
        )

    def get_memory_by_conversation(self, conversation_id: str) -> Optional[PatientMemoryRecord]:
        """Retrieve a specific memory."""
        return self.repository.get_by_conversation(conversation_id)
