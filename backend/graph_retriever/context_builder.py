from typing import List, Optional
from backend.graph_retriever.schemas import QueryIntent, IntentType, ContextChunk
from backend.graph.service import GraphService
from backend.entity_extractor.repository import EntityRepository
from backend.entity_extractor.schemas import EntityType
from backend.patient_memory.repository import PatientMemoryRepository

class GraphContextBuilder:
    def __init__(self, graph_service: Optional[GraphService] = None):
        self.graph = graph_service or GraphService()
        
    async def build_context(self, patient_id: str, intent: QueryIntent) -> List[ContextChunk]:
        chunks = []
        
        # Determine which entities to fetch based on intent
        if intent.intent_type == IntentType.MEDICATION_RELATED:
            entities = EntityRepository.get_by_patient(patient_id, EntityType.MEDICATION.value)
            for e in entities:
                rels = await self.graph.get_entity_neighbors(e.id)
                rel_strs = [f"- {r.label}: {r.properties.get('value')}" for r in rels]
                content = f"Medication: {e.value}\nConnected:\n" + "\n".join(rel_strs)
                chunks.append(ContextChunk(content=content, source="graph", relevance_score=e.confidence))
                
        elif intent.intent_type == IntentType.CONDITION_RELATED:
            entities = EntityRepository.get_by_patient(patient_id, EntityType.CONDITION.value)
            for e in entities:
                rels = await self.graph.get_entity_neighbors(e.id)
                rel_strs = [f"- {r.label}: {r.properties.get('value')}" for r in rels]
                content = f"Condition: {e.value}\nConnected:\n" + "\n".join(rel_strs)
                chunks.append(ContextChunk(content=content, source="graph", relevance_score=e.confidence))
                
        elif intent.intent_type == IntentType.LAB_RELATED:
            entities = EntityRepository.get_by_patient(patient_id, EntityType.LAB_TEST.value)
            for e in entities:
                rels = await self.graph.get_entity_neighbors(e.id)
                rel_strs = [f"- {r.label}: {r.properties.get('value')}" for r in rels]
                content = f"Lab Test: {e.value}\nConnected:\n" + "\n".join(rel_strs)
                chunks.append(ContextChunk(content=content, source="graph", relevance_score=e.confidence))
                
        elif intent.intent_type == IntentType.RECOMMENDATION:
            entities = EntityRepository.get_by_patient(patient_id, EntityType.RECOMMENDATION.value)
            for e in entities:
                chunks.append(ContextChunk(content=f"Doctor Recommendation: {e.value}", source="graph", relevance_score=e.confidence))
                
        elif intent.intent_type == IntentType.HISTORY:
            memories = PatientMemoryRepository.get_all_for_patient(patient_id)[:5] # get recent 5
            for mem in memories:
                chunks.append(ContextChunk(
                    content=f"Past Consultation ({mem.created_at[:10]}): {mem.summary_text}", 
                    source="graph_memory", 
                    relevance_score=0.9
                ))
                
        elif intent.intent_type == IntentType.PATIENT_SPECIFIC or intent.intent_type == IntentType.GENERAL_MEDICAL:
            # Get a broad overview
            conds = EntityRepository.get_by_patient(patient_id, EntityType.CONDITION.value)[:5]
            meds = EntityRepository.get_by_patient(patient_id, EntityType.MEDICATION.value)[:5]
            
            c_str = ", ".join(e.value for e in conds)
            m_str = ", ".join(e.value for e in meds)
            
            content = f"Patient Overview Profile:\nKnown Conditions: {c_str}\nCurrent Medications: {m_str}"
            chunks.append(ContextChunk(content=content, source="graph_overview", relevance_score=0.8))
            
        return chunks
