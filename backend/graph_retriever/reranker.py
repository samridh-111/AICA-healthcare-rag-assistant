import re
from typing import List
from backend.graph_retriever.schemas import ContextChunk
from backend.config import RERANKER_TOP_K

class ContextReranker:
    def rerank(self, vector_chunks: List[ContextChunk], graph_chunks: List[ContextChunk], query: str, top_k: int = RERANKER_TOP_K) -> List[ContextChunk]:
        all_chunks = vector_chunks + graph_chunks
        query_words = set(re.findall(r'\w+', query.lower()))
        
        scored_chunks = []
        for chunk in all_chunks:
            # 1. Base score (weight 0.4)
            base_score = chunk.relevance_score * 0.4
            
            # 2. Keyword overlap (weight 0.3)
            chunk_words = set(re.findall(r'\w+', chunk.content.lower()))
            overlap = len(query_words.intersection(chunk_words))
            overlap_score = min((overlap / max(len(query_words), 1)) * 0.3, 0.3)
            
            # 3. Source bonus (weight 0.1)
            # Rough heuristic: graph is structured and reliable
            source_score = 0.1 if chunk.source.startswith("graph") else 0.05
            
            # 4. Recency (weight 0.2)
            # Not fully implemented - assuming 0.1 as average
            recency_score = 0.1
            
            final_score = base_score + overlap_score + source_score + recency_score
            scored_chunks.append((final_score, chunk))
            
        # Sort by score desc
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Simple deduplication (prevent exact same content)
        seen_content = set()
        final_list = []
        for score, chunk in scored_chunks:
            # use first 100 chars as signature
            sig = chunk.content[:100].lower()
            if sig not in seen_content:
                seen_content.add(sig)
                final_list.append(chunk)
                if len(final_list) >= top_k:
                    break
                    
        return final_list
