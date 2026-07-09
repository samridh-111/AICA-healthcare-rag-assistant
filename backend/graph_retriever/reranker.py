import re
import os
import logging
import asyncio
import requests
from typing import List, Optional
from backend.graph_retriever.schemas import ContextChunk
from backend.config import RERANKER_TOP_K

logger = logging.getLogger(__name__)

class ContextReranker:
    async def _rerank_with_hf(self, chunks: List[ContextChunk], query: str) -> Optional[List[float]]:
        token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        model_id = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        
        # Format for Sequence Classification API
        payload = {
            "inputs": [
                {"text": query, "text_pair": chunk.content}
                for chunk in chunks
            ]
        }
        
        def call_api():
            # Set a small timeout (5s) to prevent blocking the thread pool for long
            response = requests.post(api_url, headers=headers, json=payload, timeout=5)
            response.raise_for_status()
            return response.json()
            
        try:
            response_data = await asyncio.to_thread(call_api)
            scores = []
            if isinstance(response_data, list):
                for item in response_data:
                    if isinstance(item, (int, float)):
                        scores.append(float(item))
                    elif isinstance(item, list) and len(item) > 0:
                        first_elem = item[0]
                        if isinstance(first_elem, dict) and "score" in first_elem:
                            scores.append(float(first_elem["score"]))
                        else:
                            scores.append(0.0)
                    elif isinstance(item, dict):
                        if "score" in item:
                            scores.append(float(item["score"]))
                        else:
                            scores.append(0.0)
                    else:
                        scores.append(0.0)
                if len(scores) == len(chunks):
                    return scores
            logger.warning(f"HF API returned unexpected format or count: {response_data}")
            return None
        except Exception as e:
            logger.warning(f"HF Inference API reranking failed/timed out: {e}")
            return None

    async def _rerank_with_llm(self, chunks: List[ContextChunk], query: str) -> Optional[List[float]]:
        from backend.groq.provider import get_llm_provider
        import json
        
        provider = get_llm_provider()
        system_prompt = (
            "You are a clinical reasoning assistant. Rate the relevance of each of the following candidate context chunks to answering the user's medical query on a scale of 0 to 10 (higher means more relevant).\n"
            "You MUST respond with a JSON object containing a key 'scores' which is a list of floats, matching the exact order of the chunks."
        )
        
        chunks_str = ""
        for i, c in enumerate(chunks):
            chunks_str += f"--- Chunk {i+1} ---\n{c.content}\n\n"
            
        prompt = f"Patient Query: {query}\n\nCandidate Chunks:\n{chunks_str}\nRate their relevance on a scale of 0 to 10 in JSON format."
        
        try:
            response_str = await provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                response_format={"type": "json_object"}
            )
            data = json.loads(response_str)
            scores = [float(s) for s in data.get("scores", [])]
            if len(scores) == len(chunks):
                return scores
            logger.warning(f"LLM reranker returned unexpected number of scores: {len(scores)}")
            return None
        except Exception as e:
            logger.warning(f"LLM reranking failed: {e}")
            return None

    def _fallback_rerank(self, chunks: List[ContextChunk], query: str) -> List[float]:
        query_words = set(re.findall(r'\w+', query.lower()))
        scores = []
        for chunk in chunks:
            # 1. Base score (weight 0.4)
            base_score = chunk.relevance_score * 0.4
            
            # 2. Keyword overlap (weight 0.3)
            chunk_words = set(re.findall(r'\w+', chunk.content.lower()))
            overlap = len(query_words.intersection(chunk_words))
            overlap_score = min((overlap / max(len(query_words), 1)) * 0.3, 0.3)
            
            # 3. Source bonus (weight 0.1)
            source_score = 0.1 if chunk.source.startswith("graph") else 0.05
            
            # 4. Recency (weight 0.2)
            recency_score = 0.1
            
            scores.append(base_score + overlap_score + source_score + recency_score)
        return scores

    async def rerank(self, vector_chunks: List[ContextChunk], graph_chunks: List[ContextChunk], query: str, top_k: int = RERANKER_TOP_K) -> List[ContextChunk]:
        all_chunks = vector_chunks + graph_chunks
        if not all_chunks:
            return []
            
        # 1. Attempt HF Cross-Encoder
        scores = await self._rerank_with_hf(all_chunks, query)
        
        # 2. Attempt LLM Cross-Encoder fallback
        if scores is None:
            logger.info("Falling back to LLM relevance reranking...")
            scores = await self._rerank_with_llm(all_chunks, query)
            
        # 3. Attempt keyword heuristic fallback
        if scores is None:
            logger.info("Falling back to keyword overlap reranking...")
            scores = self._fallback_rerank(all_chunks, query)
            
        # Pair chunks with scores
        scored_chunks = []
        for chunk, score in zip(all_chunks, scores):
            scored_chunks.append((score, chunk))
            
        # Sort descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Deduplicate
        seen_content = set()
        final_list = []
        for score, chunk in scored_chunks:
            sig = chunk.content[:100].lower()
            if sig not in seen_content:
                seen_content.add(sig)
                # Save the new rerank score
                chunk.relevance_score = score
                final_list.append(chunk)
                if len(final_list) >= top_k:
                    break
                    
        return final_list
