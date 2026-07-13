from datetime import datetime

async def preprocess_and_update_state(patient_id: str, text: str, source_file: str) -> dict:
    from backend.clinical.extraction import extract_clinical_data
    from backend.clinical.patient_state import update_patient_state
    from backend.clinical.scorer import score_patient
    from backend.clinical.alert_engine import AlertEngine
    from backend.clinical.trend_analysis import TrendAnalyzer
    from backend.clinical.emergency_rules import EmergencyDetector
    from backend.database.db import DatabaseManager
    from backend.database.models import RiskRecord
    
    extracted_data = await extract_clinical_data(text)
    state = update_patient_state(patient_id, extracted_data)
    
    trend_result = TrendAnalyzer.analyze(state.vitals_history)
    emergency_result = EmergencyDetector.detect(text, state.symptoms_history)
    score_result = score_patient(state, trend_result["score_modifier"], emergency_result["score_modifier"])
    
    all_alerts = list(set(score_result["reasons"] + trend_result["details"] + emergency_result["matched_symptoms"]))
    AlertEngine.process_alerts(patient_id, score_result["severity"], score_result["risk_score"], all_alerts)
    
    DatabaseManager.insert_risk(RiskRecord(
        patient_id=patient_id,
        timestamp=datetime.utcnow().isoformat(),
        risk_score=score_result["risk_score"],
        reasons=score_result["reasons"],
        severity=score_result["severity"]
    ))
    
    return {
        "symptoms": extracted_data.symptoms,
        "vitals": extracted_data.vitals.model_dump(),
        "risk_score": score_result["risk_score"],
        "severity": score_result["severity"]
    }

def log_interaction(patient_id: str, interaction_text: str, symptoms: list, source_file: str):
    from backend.database.db import DatabaseManager
    from backend.database.models import PatientHistoryRecord
    from backend.clinical.patient_state import get_patient_state
    from backend.clinical.scorer import score_patient
    
    state = get_patient_state(patient_id)
    score_result = score_patient(state)
    
    history_record = PatientHistoryRecord(
        patient_id=patient_id,
        timestamp=datetime.utcnow().isoformat(),
        interaction_text=f"{interaction_text} (File: {source_file})",
        extracted_symptoms=symptoms,
        risk_score=score_result["risk_score"],
        severity=score_result["severity"]
    )
    DatabaseManager.insert_history(history_record)
