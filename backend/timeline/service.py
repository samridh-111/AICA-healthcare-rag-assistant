import logging
from typing import List, Optional
from backend.database.db import DatabaseManager
from backend.patient_memory.repository import PatientMemoryRepository
from backend.timeline.schemas import TimelineEvent, EventType, TimelineResponse

logger = logging.getLogger(__name__)

class TimelineService:
    def get_timeline(self, patient_id: str, limit: int = 100, event_type: Optional[str] = None) -> TimelineResponse:
        events: List[TimelineEvent] = []
        
        # 1. Patient Memories (Conversations)
        memories = PatientMemoryRepository.get_all_for_patient(patient_id)
        for mem in memories:
            title = mem.summary_json.get("chief_complaint") or "Consultation"
            events.append(TimelineEvent(
                date=mem.created_at,
                event_type=EventType.CONVERSATION,
                title=title,
                summary=mem.summary_text,
                source="conversation",
                metadata={"memory_id": mem.id}
            ))
            
        # 2. Medications
        medications = DatabaseManager.get_medications(patient_id)
        for med in medications:
            events.append(TimelineEvent(
                date=med.timestamp,
                event_type=EventType.MEDICATION_CHANGE,
                title=f"Prescribed {med.medicine}",
                summary=f"{med.medicine} {med.dosage} {med.frequency}",
                source="system",
                metadata={"medication_id": str(med.id)}
            ))
            
        # 3. Labs
        labs = DatabaseManager.get_lab_results(patient_id)
        for lab in labs:
            events.append(TimelineEvent(
                date=lab.timestamp,
                event_type=EventType.LAB_REPORT,
                title=f"Lab: {lab.test}",
                summary=f"{lab.test}: {lab.value} {lab.unit}",
                source="upload",
                metadata={"lab_id": str(lab.id)}
            ))
            
        # 4. Images
        images = DatabaseManager.get_images(patient_id)
        for img in images:
            events.append(TimelineEvent(
                date=img.timestamp,
                event_type=EventType.MEDICAL_SCAN,
                title=f"{img.image_type.upper()} Analysis",
                summary=img.observation,
                source="upload",
                metadata={"image_id": str(img.id)}
            ))
            
        # 5. Videos
        videos = DatabaseManager.get_videos(patient_id)
        for vid in videos:
            events.append(TimelineEvent(
                date=vid.timestamp,
                event_type=EventType.VIDEO_ANALYSIS,
                title="Video Analysis",
                summary=vid.summary,
                source="upload",
                metadata={"video_id": str(vid.id)}
            ))
            
        # 6. Risk Assessments
        risks = DatabaseManager.get_risk_history(patient_id)
        for risk in risks:
            events.append(TimelineEvent(
                date=risk.timestamp,
                event_type=EventType.RISK_ASSESSMENT,
                title=f"Risk: {risk.severity}",
                summary=", ".join(risk.reasons),
                source="system",
                metadata={"risk_score": risk.risk_score}
            ))
            
        # 7. Fallback Patient History (only if no corresponding memory)
        # Avoid duplicating conversational events if we have memories.
        history = DatabaseManager.get_patient_history(patient_id)
        memory_dates = set(m.created_at for m in memories) # Very rough approximation
        for h in history:
            # If timestamp matches a memory roughly, skip
            if h.timestamp not in memory_dates:
                events.append(TimelineEvent(
                    date=h.timestamp,
                    event_type=EventType.CONVERSATION,
                    title="Patient Interaction",
                    summary=h.interaction_text,
                    source="conversation",
                    metadata={"risk_score": h.risk_score}
                ))

        # Filter and Sort
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
            
        events.sort(key=lambda x: x.date, reverse=True)
        
        # Apply limit
        events = events[:limit]
        
        return TimelineResponse(
            patient_id=patient_id,
            events=events,
            total_count=len(events)
        )
