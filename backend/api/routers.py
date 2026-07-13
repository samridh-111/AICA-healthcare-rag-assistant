import os
import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from backend.rag.chat import chat_pipeline
from backend.database.db import DatabaseManager
from backend.database.models import UploadRecord
from backend.clinical.patient_state import get_patient_state
from backend.rules.sos_rules import check_sos
from backend.utils.workflows import preprocess_and_update_state, log_interaction

router = APIRouter()

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "patient_001")

def resolve_patient_id(patient_id: str | None = None) -> str:
    return patient_id or DEFAULT_PATIENT_ID

async def save_upload_file(upload_file: UploadFile) -> str:
    """Helper to save uploaded file to workspace scratch folder."""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scratch", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, upload_file.filename)
    await upload_file.seek(0)
    content = await upload_file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    return file_path

class ChatRequest(BaseModel):
    query: str
    patient_id: str = DEFAULT_PATIENT_ID

# --- Background Task Handlers ---

async def process_document_task(upload_id: str, pid: str, file_path: str, filename: str):
    try:
        from backend.ingestion.documents.ingest_doc import ingest_document
        doc_data = ingest_document(file_path)
        
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type="document",
            clinical_content=doc_data["cleaned_text"],
            metadata={"source_file": filename}
        )
        add_to_knowledge_base(record)
        
        await preprocess_and_update_state(pid, doc_data["cleaned_text"][:8000], filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        DatabaseManager.update_upload_status(upload_id, "indexed")
    except Exception as e:
        DatabaseManager.update_upload_status(upload_id, "failed", str(e))

async def process_prescription_task(upload_id: str, pid: str, file_path: str, filename: str):
    try:
        from backend.ingestion.prescription_parser import parse_prescription_image
        meds = await parse_prescription_image(file_path, patient_id=pid)
        
        meds_summary = f"Prescription uploaded: {filename}.\nMedications extracted:\n"
        if meds:
            for m in meds:
                meds_summary += f"- {m.get('medicine')} {m.get('dosage')} {m.get('frequency')}\n"
        else:
            meds_summary += "No medications could be extracted."
            
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type="prescription",
            clinical_content=meds_summary,
            metadata={"source_file": filename}
        )
        add_to_knowledge_base(record)
        log_interaction(pid, f"Uploaded prescription: {filename}", ["medication_update"], filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        DatabaseManager.update_upload_status(upload_id, "indexed")
    except Exception as e:
        DatabaseManager.update_upload_status(upload_id, "failed", str(e))

async def process_lab_task(upload_id: str, pid: str, file_path: str, filename: str):
    try:
        from backend.ingestion.lab_parser import parse_lab_report
        lab_data = await parse_lab_report(file_path, patient_id=pid)
        
        if lab_data["interpretation"]:
            from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
            record = create_unified_record(
                patient_id=pid,
                source_type="lab_report",
                clinical_content=lab_data["interpretation"],
                metadata={"source_file": filename}
            )
            add_to_knowledge_base(record)
            
        symptoms = [val["test"] for val in lab_data["values"]]
        log_interaction(pid, f"Uploaded lab report: {filename}", symptoms, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        DatabaseManager.update_upload_status(upload_id, "indexed")
    except Exception as e:
        DatabaseManager.update_upload_status(upload_id, "failed", str(e))

async def process_image_task(upload_id: str, pid: str, file_path: str, filename: str, image_type: str):
    try:
        from backend.ingestion.image_parser import parse_medical_image
        image_data = await parse_medical_image(file_path, image_type=image_type, patient_id=pid)
        
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type=image_type,
            clinical_content=image_data["observation"],
            metadata={"source_file": filename, "image_path": file_path}
        )
        add_to_knowledge_base(record)
        log_interaction(pid, f"Analyzed {image_type} image: {filename}", ["imaging_finding"], filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        DatabaseManager.update_upload_status(upload_id, "indexed")
    except Exception as e:
        DatabaseManager.update_upload_status(upload_id, "failed", str(e))

async def process_audio_task(upload_id: str, pid: str, file_path: str, filename: str, source_type: str):
    try:
        from backend.ingestion.audio_parser import parse_audio_recording
        audio_data = await parse_audio_recording(file_path, source_type=source_type, patient_id=pid)
        
        if audio_data["transcript"]:
            from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
            record = create_unified_record(
                patient_id=pid,
                source_type=source_type,
                clinical_content=f"Voice Recording Transcript ({source_type}):\n{audio_data['transcript']}",
                metadata={"source_file": filename}
            )
            add_to_knowledge_base(record)
            
        if audio_data["symptoms"]:
            from backend.clinical.patient_state import update_patient_state
            from backend.clinical.schemas import ExtractedClinicalData, ExtractedVitals
            extracted = ExtractedClinicalData(symptoms=audio_data["symptoms"], vitals=ExtractedVitals(), medications=[])
            update_patient_state(pid, extracted)
            
        log_interaction(pid, f"Voice dictation processed: {audio_data['transcript'][:100]}...", audio_data["symptoms"], filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        DatabaseManager.update_upload_status(upload_id, "indexed")
    except Exception as e:
        DatabaseManager.update_upload_status(upload_id, "failed", str(e))

async def process_video_task(upload_id: str, pid: str, file_path: str, filename: str):
    try:
        from backend.ingestion.video_parser import parse_video_observations
        video_data = await parse_video_observations(file_path, patient_id=pid)
        
        from backend.knowledge.builder import create_unified_record, add_to_knowledge_base
        record = create_unified_record(
            patient_id=pid,
            source_type="video_observations",
            clinical_content=f"Video Summary: {video_data['summary']}\n\nFrame observations:\n{video_data['observations']}",
            metadata={"source_file": filename, "video_path": file_path}
        )
        add_to_knowledge_base(record)
        log_interaction(pid, f"Analyzed gait/movement video: {filename}", ["movement_finding"], filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        DatabaseManager.update_upload_status(upload_id, "indexed")
    except Exception as e:
        DatabaseManager.update_upload_status(upload_id, "failed", str(e))

# --- API Endpoints ---

@router.post("/upload/document")
async def upload_clinical_document(background_tasks: BackgroundTasks, patient_id: str | None = None, file: UploadFile = File(...)):
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        record = UploadRecord(patient_id=pid, filename=file.filename, status="processing")
        upload_id = DatabaseManager.insert_upload(record)
        
        background_tasks.add_task(process_document_task, upload_id, pid, file_path, file.filename)
        return {"status": "success", "message": f"Upload started for document {file.filename}", "upload_id": upload_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/prescription")
async def upload_prescription(background_tasks: BackgroundTasks, patient_id: str | None = None, file: UploadFile = File(...)):
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        record = UploadRecord(patient_id=pid, filename=file.filename, status="processing")
        upload_id = DatabaseManager.insert_upload(record)
        
        background_tasks.add_task(process_prescription_task, upload_id, pid, file_path, file.filename)
        return {"status": "success", "message": f"Upload started for prescription {file.filename}", "upload_id": upload_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/lab-report")
async def upload_lab_report(background_tasks: BackgroundTasks, patient_id: str | None = None, file: UploadFile = File(...)):
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        record = UploadRecord(patient_id=pid, filename=file.filename, status="processing")
        upload_id = DatabaseManager.insert_upload(record)
        
        background_tasks.add_task(process_lab_task, upload_id, pid, file_path, file.filename)
        return {"status": "success", "message": f"Upload started for lab report {file.filename}", "upload_id": upload_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/image")
async def upload_medical_image(background_tasks: BackgroundTasks, patient_id: str | None = None, image_type: str = "general", file: UploadFile = File(...)):
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        record = UploadRecord(patient_id=pid, filename=file.filename, status="processing")
        upload_id = DatabaseManager.insert_upload(record)
        
        background_tasks.add_task(process_image_task, upload_id, pid, file_path, file.filename, image_type)
        return {"status": "success", "message": f"Upload started for medical image {file.filename}", "upload_id": upload_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/audio")
async def upload_audio_recording(background_tasks: BackgroundTasks, patient_id: str | None = None, source_type: str = "audio_dictation", file: UploadFile = File(...)):
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        record = UploadRecord(patient_id=pid, filename=file.filename, status="processing")
        upload_id = DatabaseManager.insert_upload(record)
        
        background_tasks.add_task(process_audio_task, upload_id, pid, file_path, file.filename, source_type)
        return {"status": "success", "message": f"Upload started for audio {file.filename}", "upload_id": upload_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/video")
async def upload_video_recording(background_tasks: BackgroundTasks, patient_id: str | None = None, file: UploadFile = File(...)):
    try:
        pid = resolve_patient_id(patient_id)
        file_path = await save_upload_file(file)
        
        record = UploadRecord(patient_id=pid, filename=file.filename, status="processing")
        upload_id = DatabaseManager.insert_upload(record)
        
        background_tasks.add_task(process_video_task, upload_id, pid, file_path, file.filename)
        return {"status": "success", "message": f"Upload started for video {file.filename}", "upload_id": upload_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/patient/uploads")
def get_patient_uploads(patient_id: str | None = None):
    try:
        pid = resolve_patient_id(patient_id)
        uploads = DatabaseManager.get_uploads(pid)
        return {"uploads": [u.dict() for u in uploads]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch uploads: {str(e)}")

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        pid = resolve_patient_id(request.patient_id)
        chat_result = await chat_pipeline(request.query, patient_id=pid)
        sos_result = await check_sos(request.query)

        return {
            "response": chat_result["response"],
            "retrieved_context": chat_result["retrieved_context"],
            "sos_detected": chat_result["is_emergency"] or sos_result["is_sos"],
            "sos_details": sos_result if (chat_result["is_emergency"] or sos_result["is_sos"]) else None,
            "risk_score": chat_result["risk_score"],
            "severity": chat_result["severity"],
            "alerts": chat_result["alerts"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/summary")
async def get_patient_summary(patient_id: str | None = None):
    pid = resolve_patient_id(patient_id)
    state = get_patient_state(pid)
    risks = DatabaseManager.get_risk_history(pid, limit=1)
    latest_risk = risks[-1] if risks else None
    history = DatabaseManager.get_patient_history(pid, limit=100)
    alert_records = DatabaseManager.get_alerts(pid, limit=5)

    priority_alerts = []
    for record in alert_records:
        for alert in record.alerts:
            priority_alerts.append({"type": "critical", "title": record.severity, "detail": alert})
    if latest_risk:
        for reason in latest_risk.reasons[:5]:
            alert_type = "critical" if latest_risk.severity in ("HIGH", "CRITICAL") else "positive"
            priority_alerts.append({"type": alert_type, "title": "Risk Signal", "detail": reason})

    vitals = state.current_vitals
    last_updated = history[-1].timestamp if history else (latest_risk.timestamp if latest_risk else None)

    meds = DatabaseManager.get_medications(pid)
    labs = DatabaseManager.get_lab_results(pid)
    
    clinical_summary = "No clinical data available yet to generate a health overview."
    
    if vitals or meds or labs or history:
        from backend.groq.provider import get_llm_provider
        
        vitals_str = f"SpO2: {vitals.spo2}%, HR: {vitals.heart_rate} bpm, Temp: {vitals.temperature}°F, BP: {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg" if vitals else "None"
        meds_str = ", ".join([m.medicine for m in meds]) if meds else "None"
        labs_str = ", ".join([f"{l.test}: {l.value} {l.unit}" for l in labs]) if labs else "None"
        symptoms_str = ", ".join(state.symptoms_history) if state.symptoms_history else "None"
        risk_str = f"Risk Score: {latest_risk.risk_score}, Severity: {latest_risk.severity}" if latest_risk else "None"
        
        prompt = f"""You are a clinical reasoning assistant. Generate a concise (2-3 sentences), highly objective, and professional clinical summary of the patient's current health status based on the following patient data. Do not make diagnostic claims, do not use generalities, and do not add placeholders.
        
Patient ID: {pid}
Risk Profile: {risk_str}
Recent Vitals: {vitals_str}
Extracted Symptoms: {symptoms_str}
Medications: {meds_str}
Recent Lab Results: {labs_str}

Clinical Narrative Summary:"""
        
        try:
            provider = get_llm_provider()
            clinical_summary = await provider.generate(prompt)
            clinical_summary = clinical_summary.strip()
        except Exception as e:
            clinical_summary = f"Unable to generate clinical overview: {str(e)}"

    return {
        "patient_id": pid,
        "severity": latest_risk.severity if latest_risk else "LOW",
        "risk_score": latest_risk.risk_score if latest_risk else 0,
        "vitals": vitals.dict() if vitals else None,
        "medications_count": len(meds),
        "labs_count": len(labs),
        "timeline_count": len(history),
        "priority_alerts": priority_alerts[:8],
        "last_updated": last_updated,
        "clinical_summary": clinical_summary
    }

@router.get("/patient/alerts")
def get_patient_alerts(patient_id: str | None = None, limit: int = 10):
    pid = resolve_patient_id(patient_id)
    return {"alerts": [r.dict() for r in DatabaseManager.get_alerts(pid, limit=limit)]}

@router.get("/patient/timeline")
def get_patient_timeline(patient_id: str | None = None):
    pid = resolve_patient_id(patient_id)
    history = DatabaseManager.get_patient_history(pid)
    risks = DatabaseManager.get_risk_history(pid)
    
    events = []
    for h in history:
        events.append({"type": "interaction", "timestamp": h.timestamp, "description": h.interaction_text, "symptoms": h.extracted_symptoms, "risk_score": h.risk_score, "severity": h.severity})
    for r in risks:
        events.append({"type": "risk_assessment", "timestamp": r.timestamp, "description": f"Risk assessment: score {r.risk_score} ({r.severity})", "reasons": r.reasons, "risk_score": r.risk_score, "severity": r.severity})
        
    events.sort(key=lambda x: x["timestamp"])
    return {"timeline": events}

@router.get("/patient/medications")
def get_patient_medications(patient_id: str | None = None):
    pid = resolve_patient_id(patient_id)
    return {"medications": [m.dict() for m in DatabaseManager.get_medications(pid)]}

@router.get("/patient/labs")
def get_patient_labs(patient_id: str | None = None):
    pid = resolve_patient_id(patient_id)
    return {"labs": [l.dict() for l in DatabaseManager.get_lab_results(pid)]}

@router.get("/patient/vitals")
def get_patient_vitals_history(patient_id: str | None = None):
    pid = resolve_patient_id(patient_id)
    return {"vitals": [v.dict() for v in DatabaseManager.get_vitals_history(pid, limit=30)]}

@router.get("/patient/images")
def get_patient_images(patient_id: str | None = None):
    pid = resolve_patient_id(patient_id)
    return {"images": [img.dict() for img in DatabaseManager.get_images(pid)]}

@router.get("/patient/videos")
def get_patient_videos(patient_id: str | None = None):
    pid = resolve_patient_id(patient_id)
    return {"videos": [vid.dict() for vid in DatabaseManager.get_videos(pid)]}
