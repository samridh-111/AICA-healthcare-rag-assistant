import os
import json
from datetime import datetime
from backend.rag.retriever import retrieve_context
from backend.clinical.extraction import extract_clinical_data
from backend.clinical.patient_state import update_patient_state, get_patient_state
from backend.clinical.emergency_rules import EmergencyDetector
from backend.clinical.trend_analysis import TrendAnalyzer
from backend.clinical.scorer import score_patient
from backend.clinical.alert_engine import AlertEngine
from backend.database.models import PatientHistoryRecord, RiskRecord
from backend.database.db import DatabaseManager
from backend.groq.provider import get_llm_provider

async def generate_chat_response(query: str, context_string: str, patient_context: str = "") -> str:
    """
    Generates a response using Groq.
    """
    system_prompt = """You are a highly cautious and expert AI clinical reasoning assistant.
Your goal is to answer the user's queries based on the provided retrieved medical context and specific patient data.

You MUST strictly follow these safety and operational rules:
1. Ground your response SOLELY in the provided medical context and structured patient details.
2. NEVER hallucinate or fabricate medical facts, drug details, or lab results.
3. If the context does not contain the answer, explicitly state that you cannot answer based on the available information.
4. Internally cite your sources by referencing them (e.g. "[Source 1]", "[Medication History]", "[Lab Results]").
5. Do NOT make a definitive medical diagnosis. Offer observations and differential possibilities only.
6. Always include a disclaimer advising the patient to consult a qualified physician or healthcare professional.
7. If the patient context indicates HIGH or CRITICAL risk severity, or if active alert emergency symptoms (SOS) are triggered, you MUST highlight this severity to the user and strongly recommend immediate medical escalation (like visiting the ER or calling 911).

RETRIEVED MEDICAL CONTEXT:
{context}

PATIENT STRUCTURED DATA:
{patient_context}
"""
    prompt = f"Patient Query: {query}\n\nClinical Response:"
    
    provider = get_llm_provider()
    return await provider.generate(
        prompt=prompt,
        system_prompt=system_prompt.format(context=context_string, patient_context=patient_context)
    )

async def chat_pipeline(query: str, patient_id: str = "patient_001", uploaded_sources: list = None):
    # 1. Retrieve RAG Context
    retrieval_data = await retrieve_context(query, patient_id=patient_id)
    context_str = retrieval_data["context_string"]
    
    # 2. Extract structured data
    extracted_data = await extract_clinical_data(query)
    
    # 3. Update patient state
    state = update_patient_state(patient_id, extracted_data)
    
    # 4. Run emergency detection
    emergency_result = EmergencyDetector.detect(query, state.symptoms_history)
    
    # 5. Run trend analysis
    trend_result = TrendAnalyzer.analyze(state.vitals_history)
    
    # 6. Run deterioration scoring
    score_result = score_patient(
        state, 
        trend_score_modifier=trend_result["score_modifier"], 
        emergency_score_modifier=emergency_result["score_modifier"]
    )
    
    # Save risk score record
    timestamp = datetime.utcnow().isoformat()
    risk_record = RiskRecord(
        patient_id=patient_id,
        timestamp=timestamp,
        risk_score=score_result["risk_score"],
        reasons=score_result["reasons"],
        severity=score_result["severity"]
    )
    DatabaseManager.insert_risk(risk_record)
    
    all_alerts = list(set(score_result["reasons"] + trend_result["details"] + emergency_result["matched_symptoms"]))
    AlertEngine.process_alerts(patient_id, score_result["severity"], score_result["risk_score"], all_alerts)
    
    # Log patient history to DB
    history_record = PatientHistoryRecord(
        patient_id=patient_id,
        timestamp=timestamp,
        interaction_text=query,
        extracted_symptoms=extracted_data.symptoms,
        risk_score=score_result["risk_score"],
        severity=score_result["severity"]
    )
    DatabaseManager.insert_history(history_record)
    
    # Compile patient details
    cv = state.current_vitals
    vitals_str = f"SpO2: {cv.spo2}%, Heart Rate: {cv.heart_rate} bpm, Temp: {cv.temperature}°F, Resp: {cv.respiratory_rate}/min, BP: {cv.systolic_bp}/{cv.diastolic_bp} mmHg" if cv else "No vitals recorded"
        
    meds = DatabaseManager.get_medications(patient_id)
    meds_str = ", ".join([f"{m.medicine} ({m.dosage}, {m.frequency})" for m in meds]) if meds else "No medications recorded"
    
    labs = DatabaseManager.get_lab_results(patient_id)
    labs_str = ", ".join([f"{l.test}: {l.value} {l.unit} (Ref: {l.reference_range or 'N/A'})" for l in labs]) if labs else "No lab values recorded"
    
    imgs = DatabaseManager.get_images(patient_id)
    imgs_str = "\n".join([f"- {img.image_type.upper()}: {img.observation}" for img in imgs]) if imgs else "No medical images analyzed"
    
    vids = DatabaseManager.get_videos(patient_id)
    vids_str = "\n".join([f"- Video: {vid.summary}" for vid in vids]) if vids else "No video gait observations"
    
    history = DatabaseManager.get_patient_history(patient_id, limit=10)
    history_str = "\n".join([f"Date: {h.timestamp.split('T')[0]} | Symptoms: {', '.join(h.extracted_symptoms) if h.extracted_symptoms else 'none'} | Risk: {h.risk_score} ({h.severity})" for h in history]) if history else "No history timeline"

    patient_context_string = f"""Patient ID: {patient_id}
Current Calculated Risk Score: {score_result['risk_score']}/100 ({score_result['severity']})
Triggers & Warnings: {', '.join(score_result['reasons'])}
Current Vitals: {vitals_str}
Current Symptoms History: {', '.join(state.symptoms_history) if state.symptoms_history else 'None recorded'}
Active Medications: {meds_str}
Lab Results: {labs_str}
Medical Image Findings:
{imgs_str}
Video Findings:
{vids_str}
Historical Timeline:
{history_str}"""

    try:
        response_text = await generate_chat_response(query, context_str, patient_context_string)
    except Exception as e:
        response_text = f"Error generating reasoning response: {str(e)}"
        
    return {
        "response": response_text,
        "retrieved_context": retrieval_data["metadata"],
        "is_emergency": emergency_result["is_emergency"],
        "emergency_symptoms": emergency_result["matched_symptoms"],
        "risk_score": score_result["risk_score"],
        "severity": score_result["severity"],
        "alerts": all_alerts,
        "trend": trend_result
    }
