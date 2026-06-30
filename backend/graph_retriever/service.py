import logging
from backend.graph_retriever.schemas import HybridContext, ContextChunk
from backend.graph_retriever.intent_detector import IntentDetector
from backend.graph_retriever.context_builder import GraphContextBuilder
from backend.graph_retriever.reranker import ContextReranker
from backend.rag.retriever import retrieve_context
from backend.config import DEFAULT_TOP_K

logger = logging.getLogger(__name__)

class HybridRetrievalService:
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.context_builder = GraphContextBuilder()
        self.reranker = ContextReranker()
        
    async def retrieve(self, query: str, patient_id: str, top_k: int = DEFAULT_TOP_K) -> HybridContext:
        # 1. Detect Intent
        intent = self.intent_detector.detect_intent(query)
        logger.info(f"Detected intent: {intent.intent_type.value} (conf: {intent.confidence})")
        
        # 2. Vector Retrieval (Existing RAG)
        vector_data = retrieve_context(query, patient_id=patient_id, top_k=top_k)
        vector_chunks = []
        
        # Vector store returns list of dicts or objects
        for i, res in enumerate(vector_data.get("raw_results", [])):
            if isinstance(res, dict):
                content = res.get("content", "")
                meta = res.get("metadata", {})
            else:
                content = getattr(res, "page_content", getattr(res, "content", str(res)))
                meta = getattr(res, "metadata", {})
                
            vector_chunks.append(ContextChunk(
                content=content,
                source="vector",
                relevance_score=0.8, # standard assumption
                metadata=meta
            ))
            
        # 3. Graph Retrieval
        graph_chunks = await self.context_builder.build_context(patient_id, intent)
        
        # 4. Merge & Rerank
        reranked_chunks = self.reranker.rerank(vector_chunks, graph_chunks, query)
        
        # 5. Build merged string
        merged_strs = []
        for i, c in enumerate(reranked_chunks):
            merged_strs.append(f"[{c.source.upper()} Context {i+1}]:\n{c.content}")
            
        merged_context_str = "\n\n".join(merged_strs)
        
        return HybridContext(
            query=query,
            intent=intent,
            vector_chunks=vector_chunks,
            graph_chunks=graph_chunks,
            merged_context=merged_context_str,
            total_chunks=len(reranked_chunks)
        )
