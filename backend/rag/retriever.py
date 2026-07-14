import logging
from backend.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# Lazy-loaded singleton — avoids downloading the ~400 MB model at import time
_cross_encoder = None

def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Loading CrossEncoder model (first use)...")
            _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("CrossEncoder loaded.")
        except Exception as e:
            logger.warning(f"CrossEncoder unavailable: {e}. Reranking disabled.")
            _cross_encoder = None
    return _cross_encoder

def retrieve_context(query: str, patient_id: str = None, top_k: int = 4):
    """
    Retrieves the most semantically relevant chunks for a given query using Hybrid Search
    and Reranks them using a CrossEncoder.
    """
    store = get_vector_store()
    results = []
    try:
        # Fetch initial K candidates
        fetch_k = max(top_k * 5, 20)
        if patient_id:
            # Try hybrid search first
            results = store.hybrid_search(query, patient_id=patient_id, k=fetch_k)
            # Fallback to similarity search if hybrid fails or returns empty
            if not results:
                results = store.similarity_search(query, patient_id=patient_id, k=fetch_k)
        else:
            results = store.similarity_search(query, k=fetch_k)
    except Exception:
        results = []

    if not results:
        return {
            "context_string": "",
            "metadata": [],
            "raw_results": []
        }

    texts = []
    for item in results:
        content = item.get("content") or item.get("page_content") or str(item)
        texts.append(content)

    # Rerank using CrossEncoder (lazy-loaded; skipped if unavailable)
    cross_encoder = _get_cross_encoder()
    if cross_encoder is not None:
        pairs = [[query, doc] for doc in texts]
        scores = cross_encoder.predict(pairs)
        scored_results = sorted(zip(scores, results, texts), key=lambda x: x[0], reverse=True)
    else:
        # No reranker available — use retrieval order as-is
        scored_results = list(zip([0.0] * len(results), results, texts))

    top_results = scored_results[:top_k]

    context_chunks = []
    metadata_list = []

    for i, (score, item, content) in enumerate(top_results):
        metadata = item.get("metadata", {})
        context_chunks.append(f"[Document {i+1}]:\n{content}")
        metadata_list.append(metadata)

    context_string = "\n\n".join(context_chunks)

    return {
        "context_string": context_string,
        "metadata": metadata_list,
        "raw_results": [res[1] for res in top_results]
    }
