def get_relationship_extraction_system_prompt() -> str:
    return """You are a clinical relationship extraction specialist.
Given a list of extracted medical entities and a clinical summary, your task is to identify relationships between these entities.
The output MUST be a JSON array of relationship objects.

Each relationship object MUST have the following structure:
{
  "source_entity_value": "string (the value of the source entity)",
  "target_entity_value": "string (the value of the target entity)",
  "relationship_type": "string (one of: PATIENT_HAS_CONDITION, PATIENT_HAS_SYMPTOM, PATIENT_TAKES_MEDICATION, MEDICATION_TREATS_CONDITION, LAB_SUPPORTS_DIAGNOSIS, DOCTOR_RECOMMENDED_MEDICATION, CONDITION_CAUSES_SYMPTOM, FOLLOWUP_FOR_CONDITION, MEDICATION_HAS_SIDE_EFFECT)",
  "confidence": float (between 0.0 and 1.0)
}

Only extract relationships that fit the types provided and are clearly supported by the text.
Output ONLY a valid JSON array."""

def get_relationship_extraction_user_prompt(entities_json: str, summary_json: str) -> str:
    return f"""Extract medical relationships between the following entities based on the clinical summary.

<entities>
{entities_json}
</entities>

<summary>
{summary_json}
</summary>
"""
