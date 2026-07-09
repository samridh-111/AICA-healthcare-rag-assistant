import re
import json
import logging
from backend.graph_retriever.schemas import QueryIntent, IntentType
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

class IntentDetector:
    def _fallback_detect(self, query: str) -> QueryIntent:
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

    async def detect_intent(self, query: str) -> QueryIntent:
        try:
            provider = get_llm_provider()
            
            system_prompt = (
                "You are an expert AI clinical reasoning assistant. Analyze the patient query and classify it into exactly one of these intents:\n"
                "- general_medical: General medical questions not specific to this patient.\n"
                "- patient_specific: Queries about the patient's general health summary, state, profile, or details.\n"
                "- medication_related: Questions about medications, drugs, dosages, prescriptions, side effects, or drug interactions.\n"
                "- condition_related: Queries about illnesses, diseases, diagnoses, medical conditions, or symptoms.\n"
                "- lab_related: Queries about lab tests, results, blood panels, or pathology.\n"
                "- recommendation: Queries asking for advice, recommendations, next steps, or physician suggestions.\n"
                "- vital_related: Queries about blood pressure, heart rate, temperature, oxygen level (SpO2), vitals, or respiratory rate.\n"
                "- history: Queries about past visits, historical consultations, timelines, or prior medical events.\n\n"
                "Also, extract a list of medical entities/concepts mentioned in the query (like specific drug names, symptoms, conditions, vital types, lab test names).\n"
                "You MUST return a JSON object with: 'intent_type' (string matching one of the intents above exactly), 'confidence' (float between 0.0 and 1.0), and 'extracted_entities' (list of strings)."
            )
            
            prompt = f"Patient Query: {query}\n\nAnalyze and classify in JSON format."
            
            response_str = await provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response_str)
            intent_str = data.get("intent_type", "").lower()
            confidence = float(data.get("confidence", 0.5))
            extracted_entities = data.get("extracted_entities", [])
            
            # Map string to IntentType enum
            try:
                intent_type = IntentType(intent_str)
            except ValueError:
                # Fallback to general medical if output not matching enum values
                intent_type = IntentType.GENERAL_MEDICAL
                
            return QueryIntent(
                intent_type=intent_type,
                confidence=confidence,
                extracted_entities=extracted_entities
            )
            
        except Exception as e:
            logger.warning(f"LLM intent detection failed: {e}. Falling back to keyword rules.")
            return self._fallback_detect(query)
