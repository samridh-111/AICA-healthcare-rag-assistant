def get_entity_extraction_system_prompt() -> str:
    return """You are a clinical entity extraction specialist.
Given a JSON clinical summary, your task is to extract supplementary medical entities that might not be explicitly structured but are important.
The output MUST be a JSON array of entity objects.

Each entity object MUST have the following structure:
{
  "type": "string (one of: PATIENT, CONDITION, SYMPTOM, MEDICATION, ALLERGY, DIAGNOSIS, LAB_TEST, VITAL, DOCTOR, RECOMMENDATION, MEDICAL_DEVICE, PROCEDURE)",
  "value": "string (the actual entity name or value)",
  "confidence": float (between 0.0 and 1.0),
  "source": "string (where it was found, typically 'conversation')"
}

Only extract entities that fit the types provided. Ensure high confidence before extracting.
Output ONLY a valid JSON array."""

def get_entity_extraction_user_prompt(summary_json: str) -> str:
    return f"""Extract medical entities from the following clinical summary JSON:

<summary>
{summary_json}
</summary>
"""
