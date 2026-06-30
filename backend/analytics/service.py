import logging
from collections import Counter
from datetime import datetime
from backend.database.db import DatabaseManager
from backend.patient_memory.repository import PatientMemoryRepository
from backend.analytics.schemas import AnalyticsResponse, ChartData, ChartDataset, FrequencyItem, VitalTrends

logger = logging.getLogger(__name__)

def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime("%b %d")
    except:
        return iso_str[:10]

class AnalyticsService:
    def get_analytics(self, patient_id: str) -> AnalyticsResponse:
        response = AnalyticsResponse(patient_id=patient_id)
        
        # 1. Risk over time
        risk_history = DatabaseManager.get_risk_history(patient_id)
        if risk_history:
            labels = [format_date(r.timestamp) for r in risk_history]
            scores = [r.risk_score for r in risk_history]
            response.risk_over_time = ChartData(
                labels=labels,
                datasets=[ChartDataset(label="Risk Score", data=scores, border_color="#e74c3c", background_color="rgba(231, 76, 60, 0.1)")]
            )
            
        # 2. Symptom Frequency
        patient_history = DatabaseManager.get_patient_history(patient_id)
        symptom_counter = Counter()
        for h in patient_history:
            if h.extracted_symptoms:
                symptom_counter.update(h.extracted_symptoms)
        
        response.symptom_frequency = [FrequencyItem(name=k, count=v) for k, v in symptom_counter.most_common(10)]
        
        # 3. Medication Frequency
        medications = DatabaseManager.get_medications(patient_id)
        med_counter = Counter(m.medicine for m in medications)
        response.medication_frequency = [FrequencyItem(name=k, count=v) for k, v in med_counter.most_common(10)]
        
        # 4. Conditions & Memories (Consultation Count)
        memories = PatientMemoryRepository.get_all_for_patient(patient_id)
        condition_counter = Counter()
        for mem in memories:
            conds = mem.summary_json.get("conditions", [])
            if conds:
                condition_counter.update(conds)
        
        response.condition_frequency = [FrequencyItem(name=k, count=v) for k, v in condition_counter.most_common(10)]
        response.consultation_count = len(patient_history) + len(memories) # Approx
        
        # 5. Vital Trends
        vitals = DatabaseManager.get_vitals_history(patient_id, limit=30)
        if vitals:
            dates = [format_date(v.timestamp) for v in vitals]
            
            # Blood Pressure
            sys_data = [v.systolic_bp for v in vitals]
            dia_data = [v.diastolic_bp for v in vitals]
            response.vital_trends.blood_pressure = ChartData(
                labels=dates,
                datasets=[
                    ChartDataset(label="Systolic", data=sys_data, border_color="#3498db", background_color="transparent"),
                    ChartDataset(label="Diastolic", data=dia_data, border_color="#2ecc71", background_color="transparent")
                ]
            )
            
            # Heart Rate
            hr_data = [v.heart_rate for v in vitals]
            response.vital_trends.heart_rate = ChartData(
                labels=dates,
                datasets=[ChartDataset(label="Heart Rate", data=hr_data, border_color="#e67e22")]
            )
            
            # Temperature
            temp_data = [v.temperature for v in vitals]
            response.vital_trends.temperature = ChartData(
                labels=dates,
                datasets=[ChartDataset(label="Temperature", data=temp_data, border_color="#f1c40f")]
            )
            
            # SpO2
            spo2_data = [v.spo2 for v in vitals]
            response.vital_trends.spo2 = ChartData(
                labels=dates,
                datasets=[ChartDataset(label="SpO2", data=spo2_data, border_color="#9b59b6")]
            )
            
        # Blood Sugar & Weight from Memories (Fallback)
        bs_dates = []
        bs_data = []
        wt_dates = []
        wt_data = []
        
        for mem in reversed(memories): # Oldest first
            vitals_sum = mem.summary_json.get("vitals", {})
            d = format_date(mem.created_at)
            
            bs = vitals_sum.get("blood_glucose")
            if bs and bs != "":
                try:
                    bs_data.append(float(bs.split()[0])) # Parse out numbers roughly
                    bs_dates.append(d)
                except: pass
                
            wt = vitals_sum.get("weight")
            if wt and wt != "":
                try:
                    wt_data.append(float(wt.split()[0]))
                    wt_dates.append(d)
                except: pass
                
        if bs_data:
            response.vital_trends.blood_sugar = ChartData(
                labels=bs_dates,
                datasets=[ChartDataset(label="Blood Glucose", data=bs_data, border_color="#1abc9c")]
            )
            
        if wt_data:
            response.vital_trends.weight = ChartData(
                labels=wt_dates,
                datasets=[ChartDataset(label="Weight", data=wt_data, border_color="#34495e")]
            )
            
        return response
