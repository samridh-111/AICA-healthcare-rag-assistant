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
        matched_any_entity = False
        
        # 1. Dynamic Graph Traversal based on extracted query entities
        for entity_val in intent.extracted_entities:
            entities = EntityRepository.search_by_value(patient_id, entity_val)
            for e in entities:
                matched_any_entity = True
                
                # Weighted BFS traversal from this matching entity
                neighbors = await self.graph.get_entity_neighbors(e.id, depth=1)
                
                if neighbors:
                    rel_strs = []
                    for n in neighbors:
                        path_score = n.properties.get("path_score", 1.0)
                        rel_strs.append(f"- {n.label}: {n.properties.get('value')} (score: {path_score:.2f})")
                    
                    content = f"Entity: {e.value} ({e.entity_type.value})\nConnected neighbors:\n" + "\n".join(rel_strs)
                    chunks.append(ContextChunk(
                        content=content, 
                        source="graph_dynamic", 
                        relevance_score=e.confidence
                    ))
                else:
                    # No neighbors, just add the entity itself
                    chunks.append(ContextChunk(
                        content=f"Entity: {e.value} ({e.entity_type.value})", 
                        source="graph_dynamic", 
                        relevance_score=e.confidence
                    ))
                    
        # 2. Dynamic Consultation Memory Search based on query terms
        memories = PatientMemoryRepository.get_all_for_patient(patient_id)
        if memories:
            query_words = {w.lower() for w in intent.extracted_entities}
            scored_memories = []
            
            for mem in memories:
                mem_text_lower = mem.summary_text.lower()
                # Count overlaps
                overlap_count = sum(1 for w in query_words if w in mem_text_lower)
                
                # Compute score: keyword overlap + base relevance
                score = overlap_count + 0.1
                scored_memories.append((score, mem))
                
            # Sort memories by relevance descending and retrieve top 3
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            for score, mem in scored_memories[:3]:
                # If there's keyword overlap or we have very few memories, include it
                if score > 0.1 or len(scored_memories) <= 3:
                    chunks.append(ContextChunk(
                        content=f"Past Consultation Summary ({mem.created_at[:10]}):\n{mem.summary_text}",
                        source="graph_memory_dynamic",
                        relevance_score=min(score / max(len(query_words), 1), 1.0) if query_words else 0.9
                    ))
                    
        # 3. Fallback / Overview context:
        # If no query entities were found in the database, or if it is a general/profile query,
        # fetch a dynamic summary of the patient overview profile.
        if not matched_any_entity or intent.intent_type == IntentType.PATIENT_SPECIFIC:
            conds = EntityRepository.get_by_patient(patient_id, EntityType.CONDITION.value, limit=5)
            meds = EntityRepository.get_by_patient(patient_id, EntityType.MEDICATION.value, limit=5)
            vitals = EntityRepository.get_by_patient(patient_id, EntityType.VITAL.value, limit=5)
            
            c_str = ", ".join(e.value for e in conds) if conds else "None"
            m_str = ", ".join(e.value for e in meds) if meds else "None"
            v_str = ", ".join(e.value for e in vitals) if vitals else "None"
            
            content = f"Patient Overview Profile:\nKnown Conditions: {c_str}\nCurrent Medications: {m_str}\nRecent Vitals: {v_str}"
            chunks.append(ContextChunk(content=content, source="graph_overview_dynamic", relevance_score=0.7))
            
        return chunks
