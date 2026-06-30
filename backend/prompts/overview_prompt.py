def get_overview_system_prompt() -> str:
    return """You are a highly skilled clinical AI generating a comprehensive patient overview.
Given a collection of past consultation summaries for a patient, synthesize a single, cohesive overview.
The output MUST be a strict JSON object matching this schema:

{
  "overall_health_summary": "string (2-4 sentences summarizing the patient's general health trajectory)",
  "active_conditions": ["string", "string"],
  "resolved_conditions": ["string"],
  "medication_history": ["string"],
  "current_medications": ["string"],
  "allergies": ["string"],
  "recurring_symptoms": ["string"],
  "recent_recommendations": ["string"],
  "overall_risk": "string (LOW, MEDIUM, HIGH, CRITICAL)",
  "key_concerns": ["string"]
}

Guidelines:
- Consolidate information, avoid duplicates.
- Ensure the overall_risk reflects the most severe ongoing conditions or recent deteriorations.
- Ensure only active conditions are in active_conditions, and resolved ones in resolved_conditions.
Output ONLY a valid JSON object."""

def get_overview_user_prompt(memories_json: str) -> str:
    return f"""Generate a patient overview from the following collection of consultation summaries:

<consultation_summaries>
{memories_json}
</consultation_summaries>
"""
