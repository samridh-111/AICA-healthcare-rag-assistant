import os
import asyncio
import uuid
import logging
from typing import List, Dict
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.rag.chat import chat_pipeline
from backend.database.db import DatabaseManager

from backend.patient_memory.router import router as memory_router
from backend.overview.router import router as overview_router
from backend.timeline.router import router as timeline_router
from backend.analytics.router import router as analytics_router
from backend.graph.router import router as graph_router

from backend.summarizer.service import SummarizerService
from backend.entity_extractor.service import EntityExtractorService
from backend.relationship_extractor.service import RelationshipExtractorService
from backend.patient_memory.service import PatientMemoryService
from backend.graph_retriever.service import HybridRetrievalService

logger = logging.getLogger(__name__)

router = APIRouter()

# Include all the sub-routers from V2 modules
router.include_router(memory_router)
router.include_router(overview_router)
router.include_router(timeline_router)
router.include_router(analytics_router)
router.include_router(graph_router)

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

class ChatRequestV2(BaseModel):
    query: str
    patient_id: str = DEFAULT_PATIENT_ID
    conversation_id: str = None  # Frontend should pass this to group messages

class RetrieveRequestV2(BaseModel):
    query: str
    patient_id: str = DEFAULT_PATIENT_ID

# Initialize services
summarizer_svc = SummarizerService()
entity_svc = EntityExtractorService()
relationship_svc = RelationshipExtractorService()
memory_svc = PatientMemoryService()
hybrid_retriever_svc = HybridRetrievalService()

async def background_post_chat_processing(patient_id: str, conversation_id: str):
    """
    Runs asynchronously after the chat response is returned to the user.
    Handles the summarization, extraction, and graph building pipeline.
    """
    logger.info(f"Starting background post-chat processing for {conversation_id}")
    
    # 1. Fetch recent conversation history from PatientHistoryRecord (approximation)
    # Ideally, we should have a dedicated conversation table, but we use history for now.
    history_records = DatabaseManager.get_patient_history(patient_id, limit=20)
    
    # If not enough messages based on config, skip
    if not summarizer_svc.should_summarize(len(history_records)):
        logger.info(f"Message count {len(history_records)} < threshold. Skipping summarization.")
        return
        
    # Reconstruct a simple conversation list for summarizer
    # Assuming user queries are what is logged in PatientHistoryRecord
    conversation_history = []
    for h in reversed(history_records):
        conversation_history.append({"role": "user", "content": h.interaction_text})
        # Assistant response is not logged in history currently, so we use a mock or partial history.
        # In a fully fleshed out system, we would log assistant responses too.
        
    try:
        # 2. Create Patient Memory (Summarization)
        memory_record = await memory_svc.create_memory(patient_id, conversation_id, conversation_history)
        if not memory_record:
            return
            
        summary_obj = memory_record.summary_json
        from backend.summarizer.schemas import ConversationSummary
        summary = ConversationSummary(**summary_obj)
        
        # 3. Entity Extraction
        entities = await entity_svc.extract_entities(patient_id, conversation_id, summary)
        
        # 4. Relationship Extraction
        relationships = await relationship_svc.extract_relationships(patient_id, conversation_id, summary, entities)
        
        # Invalidate overview cache since new memory/entities exist
        from backend.overview.router import overview_service
        overview_service.invalidate_cache(patient_id)
        
        logger.info(f"Background processing complete. Extracted {len(entities)} entities, {len(relationships)} relationships.")
    except Exception as e:
        logger.error(f"Error in background post-chat processing: {e}")

@router.post("/chat")
async def chat_v2(request: ChatRequestV2, background_tasks: BackgroundTasks):
    """
    V2 Chat endpoint. Uses V1 Chat Pipeline but adds async intelligence extraction.
    """
    try:
        pid = request.patient_id or DEFAULT_PATIENT_ID
        conv_id = request.conversation_id or str(uuid.uuid4())
        
        # V1 core logic
        chat_result = await chat_pipeline(request.query, patient_id=pid)
        from backend.rules.sos_rules import check_sos
        sos_result = check_sos(request.query)
        
        # Trigger async post-processing pipeline
        background_tasks.add_task(background_post_chat_processing, pid, conv_id)
        
        return {
            "response": chat_result["response"],
            "retrieved_context": chat_result["retrieved_context"],
            "sos_detected": chat_result["is_emergency"] or sos_result["is_sos"],
            "sos_details": sos_result if (chat_result["is_emergency"] or sos_result["is_sos"]) else None,
            "risk_score": chat_result["risk_score"],
            "severity": chat_result["severity"],
            "alerts": chat_result["alerts"],
            "conversation_id": conv_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrieve")
async def retrieve_v2(request: RetrieveRequestV2):
    """
    V2 Hybrid Retrieval endpoint using both Vector DB and Knowledge Graph.
    """
    try:
        pid = request.patient_id or DEFAULT_PATIENT_ID
        hybrid_context = await hybrid_retriever_svc.retrieve(request.query, pid)
        
        return {
            "intent": hybrid_context.intent.model_dump(),
            "merged_context": hybrid_context.merged_context,
            "total_chunks": hybrid_context.total_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
