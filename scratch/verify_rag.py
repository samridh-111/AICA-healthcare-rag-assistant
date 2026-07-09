import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Ensure backend imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyRAG")

# Load environment variables
load_dotenv()

async def test_intent_and_entity():
    print("\n--- Testing Intent Detection & Entity Extraction ---")
    from backend.graph_retriever.intent_detector import IntentDetector
    detector = IntentDetector()
    
    queries = [
        "What dosage of lisinopril should I take for my blood pressure?",
        "Why does the patient have chronic chest pain and dyspnea?",
        "Retrieve the blood panel lab results from last month.",
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        intent = await detector.detect_intent(q)
        print(f"Intent Type: {intent.intent_type.value}")
        print(f"Confidence: {intent.confidence}")
        print(f"Extracted Entities: {intent.extracted_entities}")

async def test_weighted_bfs():
    print("\n--- Testing Dijkstra-style Weighted BFS ---")
    from backend.graph.relational_adapter import RelationalGraphRepository
    from backend.entity_extractor.repository import EntityRepository
    
    repo = RelationalGraphRepository()
    # Find any entity for patient_001
    patient_id = "patient_001"
    entities = EntityRepository.get_by_patient(patient_id, limit=5)
    
    if not entities:
        print("No patient entities found in database. Skipping BFS traversal test.")
        return
        
    start_entity = entities[0]
    print(f"Starting traversal from entity: ID={start_entity.id}, Value='{start_entity.value}', Type={start_entity.entity_type.value}")
    
    neighbors = await repo.get_neighbors(start_entity.id, max_depth=2)
    print(f"Retrieved {len(neighbors)} neighbors:")
    for n in neighbors:
        print(f"- Node: Value='{n.properties.get('value')}', Label={n.label}, Traversal Path Score={n.properties.get('path_score'):.4f}")

async def test_context_builder():
    print("\n--- Testing Dynamic Context Builder ---")
    from backend.graph_retriever.context_builder import GraphContextBuilder
    from backend.graph_retriever.schemas import QueryIntent, IntentType
    
    builder = GraphContextBuilder()
    intent = QueryIntent(
        intent_type=IntentType.MEDICATION_RELATED,
        confidence=0.9,
        extracted_entities=["lisinopril", "metformin", "blood pressure"]
    )
    
    chunks = await builder.build_context("patient_001", intent)
    print(f"Retrieved {len(chunks)} dynamic context chunks:")
    for i, c in enumerate(chunks):
        print(f"\nChunk {i+1} [Source: {c.source}, Score: {c.relevance_score:.2f}]:")
        print(c.content)

async def test_reranker():
    print("\n--- Testing Hybrid Reranker ---")
    from backend.graph_retriever.reranker import ContextReranker
    from backend.graph_retriever.schemas import ContextChunk
    
    reranker = ContextReranker()
    vector_chunks = [
        ContextChunk(content="The patient is prescribed lisinopril 10mg daily for hypertension.", source="vector", relevance_score=0.8),
        ContextChunk(content="Metformin 500mg was added to manage type 2 diabetes.", source="vector", relevance_score=0.7)
    ]
    graph_chunks = [
        ContextChunk(content="Entity: lisinopril. Connected to hypertension.", source="graph_dynamic", relevance_score=0.9)
    ]
    
    query = "What is the patient taking for their blood pressure?"
    reranked = await reranker.rerank(vector_chunks, graph_chunks, query)
    print(f"Reranked {len(reranked)} chunks:")
    for i, chunk in enumerate(reranked):
        print(f"- Rank {i+1} [Source: {chunk.source}, Final Score: {chunk.relevance_score:.4f}]: {chunk.content}")

async def test_hybrid_retrieval_service():
    print("\n--- Testing Hybrid Retrieval Service ---")
    from backend.graph_retriever.service import HybridRetrievalService
    
    service = HybridRetrievalService()
    query = "Is the patient taking any medications for hypertension or high blood pressure?"
    
    context = await service.retrieve(query, "patient_001")
    print(f"Intent: {context.intent.intent_type.value}")
    print(f"Total Chunks: {context.total_chunks}")
    print("\nMerged Context Output:")
    print(context.merged_context[:500] + "...")

async def main():
    try:
        await test_intent_and_entity()
        await test_weighted_bfs()
        await test_context_builder()
        await test_reranker()
        await test_hybrid_retrieval_service()
        print("\nAll tests completed successfully!")
    except Exception as e:
        logger.exception(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
