import re
from backend.graph_retriever.schemas import QueryIntent, IntentType

class IntentDetector:
    def detect_intent(self, query: str) -> QueryIntent:
        text = query.lower()
        
        # Simple rule-based intent detection
        if any(w in text for w in ["medication", "medicine", "drug", "dosage", "prescription", "taking"]):
            intent = IntentType.MEDICATION_RELATED
            conf = 0.9
        elif any(w in text for w in ["condition", "disease", "diagnosis", "diagnosed", "symptom"]):
            intent = IntentType.CONDITION_RELATED
            conf = 0.9
        elif any(w in text for w in ["lab", "test", "result", "blood work", "panel"]):
            intent = IntentType.LAB_RELATED
            conf = 0.9
        elif any(w in text for w in ["recommend", "advice", "should i", "doctor said"]):
            intent = IntentType.RECOMMENDATION
            conf = 0.8
        elif any(w in text for w in ["blood pressure", "heart rate", "temperature", "oxygen", "spo2", "vitals", "weight"]):
            intent = IntentType.VITAL_RELATED
            conf = 0.9
        elif any(w in text for w in ["history", "previous", "past", "last visit", "before"]):
            intent = IntentType.HISTORY
            conf = 0.8
        elif any(w in text for w in ["my", "patient", "i have", "i am", "i feel"]):
            intent = IntentType.PATIENT_SPECIFIC
            conf = 0.7
        else:
            intent = IntentType.GENERAL_MEDICAL
            conf = 0.5
            
        # Extract basic medical terms (crude approximation without NLP library)
        words = re.findall(r'\b[a-z]{4,}\b', text)
        stop_words = {"what", "when", "where", "how", "why", "can", "you", "tell", "about", "this", "that", "have", "been", "with"}
        entities = [w for w in words if w not in stop_words]
        
        return QueryIntent(
            intent_type=intent,
            confidence=conf,
            extracted_entities=list(set(entities))
        )
