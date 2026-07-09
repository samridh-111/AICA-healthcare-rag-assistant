import re
import asyncio
import logging
from backend.rag.vector_store import get_vector_store
from backend.database.db import supabase

logger = logging.getLogger(__name__)

async def retrieve_context(query: str, patient_id: str = None, top_k: int = 4, metadata_filters: dict = None):
    """
    Retrieves the most relevant chunks for a given query using hybrid search (semantic + keyword RRF) 
    and applies metadata filtering.
    """
    store = get_vector_store()
    
    # 1. Semantic (Vector) Search
    semantic_results = []
    try:
        if patient_id:
            # similarity_search is synchronous, run it in a thread to keep it non-blocking
            semantic_results = await asyncio.to_thread(
                store.similarity_search, query, patient_id=patient_id, k=top_k * 2
            )
        else:
            semantic_results = await asyncio.to_thread(
                store.similarity_search, query, k=top_k * 2
            )
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        semantic_results = []

    # 2. Keyword Search on clinical_knowledge table
    keyword_results = []
    if supabase and patient_id:
        try:
            # Tokenize query to extract key terms
            words = [w.strip() for w in re.findall(r'\b[a-zA-Z0-9_]{3,}\b', query.lower())]
            stop_words = {
                "what", "when", "where", "how", "why", "can", "you", "tell", "about", 
                "this", "that", "have", "been", "with", "from", "your", "were", "there", 
                "then", "them", "they", "please", "some", "more"
            }
            keywords = [w for w in words if w not in stop_words]
            
            # Fetch all documents for this patient to do keyword matching in memory
            def fetch_patient_docs():
                response = supabase.table("clinical_knowledge").select("*").eq("patient_id", patient_id).execute()
                return response.data
                
            all_docs = await asyncio.to_thread(fetch_patient_docs)
            
            scored_docs = []
            for doc in all_docs:
                content_lower = doc.get("content", "").lower()
                matches = sum(1 for kw in keywords if kw in content_lower)
                if matches > 0:
                    scored_docs.append((matches, doc))
                    
            # Sort by match count descending
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            keyword_results = [doc for matches, doc in scored_docs[:top_k * 2]]
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            keyword_results = []

    # 3. Reciprocal Rank Fusion (RRF) to merge semantic and keyword results
    rrf_constant = 60
    scores = {}  # doc_content -> (rrf_score, doc_obj)
    
    def get_content(doc):
        if isinstance(doc, dict):
            return doc.get("content") or doc.get("page_content") or ""
        return getattr(doc, "page_content", getattr(doc, "content", str(doc)))
        
    for rank, doc in enumerate(semantic_results):
        content = get_content(doc)
        scores[content] = (1.0 / (rrf_constant + rank + 1), doc)
        
    for rank, doc in enumerate(keyword_results):
        content = get_content(doc)
        curr_score, existing_doc = scores.get(content, (0.0, doc))
        scores[content] = (curr_score + (1.0 / (rrf_constant + rank + 1)), existing_doc)
        
    merged_results = sorted(scores.values(), key=lambda x: x[0], reverse=True)
    results = [doc for score, doc in merged_results]

    # 4. Metadata Filtering
    if metadata_filters:
        filtered_results = []
        for doc in results:
            meta = doc.get("metadata", {}) if isinstance(doc, dict) else getattr(doc, "metadata", {})
            match = True
            for k, v in metadata_filters.items():
                if meta.get(k) != v:
                    match = False
                    break
            if match:
                filtered_results.append(doc)
        results = filtered_results

    # 5. Format results
    context_chunks = []
    metadata_list = []

    # Take the top_k results
    for i, item in enumerate(results[:top_k]):
        if isinstance(item, dict):
            content = item.get("content") or item.get("page_content") or str(item)
            metadata = item.get("metadata", {})
        else:
            content = getattr(item, "page_content", None) or getattr(item, "content", str(item))
            metadata = getattr(item, "metadata", {}) if hasattr(item, "metadata") else {}

        context_chunks.append(f"[Document {i+1}]:\n{content}")
        metadata_list.append(metadata)

    context_string = "\n\n".join(context_chunks)

    return {
        "context_string": context_string,
        "metadata": metadata_list,
        "raw_results": results[:top_k]
    }
