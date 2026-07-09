# GraphRAG Engine: Sam Trial Documentation

This document explains exactly how the GraphRAG (Knowledge Graph + Retrieval-Augmented Generation) engine works in the healthcare assistant. It breaks down every logical step, showing which file is being called and how the engine processes information from a user chat to graph construction and hybrid retrieval.

---

## 1. Triggering the Engine (API Entry Point)
**File:** `backend/api/router_v2.py`
**Step Logic:**
1. A user sends a message via the `/chat` endpoint.
2. The system executes the standard chat pipeline (V1 RAG) to get an immediate response.
3. Crucially, it triggers `background_post_chat_processing(patient_id, conversation_id)` as a FastAPI background task so the user isn't kept waiting.
4. The background task fetches the recent conversation history from the database.
5. If the conversation length exceeds the `SUMMARIZATION_MESSAGE_THRESHOLD` (defined in `backend/config.py`), it begins the GraphRAG extraction pipeline.

---

## 2. Conversation Summarization (Patient Memory)
**File:** `backend/patient_memory/service.py` -> `backend/summarizer/service.py`
**Step Logic:**
1. The `PatientMemoryService` calls `SummarizerService.summarize_conversation()`.
2. The summarizer uses an LLM (Groq) with a strict JSON schema prompt (from `backend/prompts/summary_prompt.py`).
3. It extracts a structured clinical summary containing: chief complaint, active/resolved symptoms, conditions, medications, allergies, labs, doctor recommendations, and vitals.
4. A human-readable text summary is generated and embedded using `sentence-transformers` via a HuggingFace API (`backend/rag/embeddings.py`).
5. This memory is persisted to the Postgres database via `PatientMemoryRepository` and vectorized into Chroma/pgvector so it can be retrieved in standard V1 RAG.

---

## 3. Entity Extraction (Building Graph Nodes)
**File:** `backend/entity_extractor/service.py`
**Step Logic:**
1. Now that a structured summary exists, `EntityExtractorService.extract_entities()` is called.
2. **Phase 1 (Deterministic):** It iterates through the structured summary fields (symptoms, conditions, medications, vitals, etc.) and explicitly creates `MedicalEntity` objects for them. 
3. **Phase 2 (LLM Extraction):** It asks the LLM (using `backend/prompts/entity_prompt.py`) to extract any supplementary medical entities that might have been missed, assigning a confidence score to each.
4. Deduplication occurs by checking if the entity values already exist.
5. Entities are bulk-inserted into the Postgres database (`medical_entities` table) via `EntityRepository`. These act as the **Nodes** in our Knowledge Graph.

---

## 4. Relationship Extraction (Building Graph Edges)
**File:** `backend/relationship_extractor/service.py`
**Step Logic:**
1. With entities created, `RelationshipExtractorService.extract_relationships()` is executed.
2. **Phase 1 (Deterministic):** It logically maps known entities to the patient. For example, if a symptom entity exists, it creates a `PATIENT_HAS_SYMPTOM` relationship between the Patient node and the Symptom node.
3. **Phase 2 (LLM Extraction):** The LLM (using `backend/prompts/relationship_prompt.py`) analyzes the text summary and the list of extracted entities to deduce complex relationships, such as `MEDICATION_TREATS_CONDITION` or `CONDITION_CAUSES_SYMPTOM`.
4. Extracted relationships are filtered by a `CONFIDENCE_THRESHOLD`.
5. The relationships are bulk-inserted into the Postgres database (`medical_relationships` table) via `RelationshipRepository`. These act as the **Edges** in our Knowledge Graph.

---

## 5. The Graph Provider (Relational Adapter)
**File:** `backend/graph/relational_adapter.py`
**Step Logic:**
1. Because we are using Postgres instead of a dedicated graph DB like Neo4j, the `RelationalGraphRepository` acts as a graph adapter.
2. It dynamically translates Postgres records from the `medical_entities` and `medical_relationships` tables into `GraphNode` and `GraphEdge` objects.
3. The `get_neighbors(node_id, max_depth)` function simulates graph traversal using Breadth-First Search (BFS) over the SQL relationship tables, allowing us to find connected entities up to `GRAPH_MAX_DEPTH`.

---

## 6. Hybrid Retrieval Engine (Answering Questions)
When a user asks a new question on the `/retrieve` or via future chat versions, the `HybridRetrievalService` takes over to combine vector search and graph search.

**File:** `backend/graph_retriever/service.py`

### Step A: Intent Detection
**File:** `backend/graph_retriever/intent_detector.py`
- Analyzes the user's query to detect the primary intent (e.g., `MEDICATION_RELATED`, `VITAL_RELATED`, `HISTORY`).
- Uses simple keyword and regex rules to classify the query and extract basic medical keywords.

### Step B: Vector Retrieval
**File:** `backend/rag/retriever.py`
- Performs standard semantic search using the query embedding against the vector database (fetching the top-K chunks).

### Step C: Graph Context Building
**File:** `backend/graph_retriever/context_builder.py`
- Based on the detected intent, it queries specific nodes from the Knowledge Graph.
- For example, if intent is `CONDITION_RELATED`, it finds all `CONDITION` entities for the patient, traverses the graph to find their neighbors (like medications treating the condition, or symptoms caused by it), and builds structured text chunks (e.g., `"Condition: Diabetes\nConnected: - Medication: Metformin"`).
- If the intent is `HISTORY`, it fetches recent memories from the `PatientMemoryRepository`.

### Step D: Reranking and Merging
**File:** `backend/graph_retriever/reranker.py`
- Combines the chunks from the Vector Search and the Graph Search.
- Scores each chunk based on relevance, keyword overlap with the query, and a source bonus (graph structured data is given a slight boost).
- Sorts the chunks by score and deduplicates them.
- Finally, it formats the top chunks into a single `merged_context` string, which is then fed to the LLM to generate the final, highly accurate, and deeply contextualized clinical answer.
