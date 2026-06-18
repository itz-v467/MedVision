"""Staged advanced capabilities for the symptom triage chatbot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TriageCapability:
    """A planned or active triage feature."""

    id: str
    title: str
    phase: str
    status: str  # planned | beta | active
    description: str


TRIAGE_ROADMAP: tuple[TriageCapability, ...] = (
    TriageCapability(
        id="pre_consult_handoff",
        title="Smart pre-consult triage + clinician handoff",
        phase="mvp",
        status="active",
        description="Conversational symptom intake with structured handoff note for physicians.",
    ),
    TriageCapability(
        id="multimodal_fusion",
        title="Multimodal symptom + lab/imaging fusion",
        phase="phase_2",
        status="planned",
        description="Cross-check chatbot symptoms against uploaded labs and chest X-ray findings.",
    ),
    TriageCapability(
        id="longitudinal_deterioration",
        title="Longitudinal deterioration detection",
        phase="phase_2",
        status="planned",
        description="Compare symptom trends across prior encounters and flag worsening trajectories.",
    ),
    TriageCapability(
        id="care_plan_coaching",
        title="Personalized care-plan coaching",
        phase="phase_3",
        status="planned",
        description="Age/comorbidity-aware follow-up plans with adherence nudges.",
    ),
    TriageCapability(
        id="medication_safety",
        title="Medication & contraindication prompts",
        phase="phase_3",
        status="planned",
        description="Allergy and drug-interaction clarifying questions for physician review.",
    ),
    TriageCapability(
        id="post_discharge_monitoring",
        title="Post-discharge monitoring assistant",
        phase="phase_4",
        status="planned",
        description="Daily structured check-ins with auto-escalation on worsening symptoms.",
    ),
    TriageCapability(
        id="multilingual_low_literacy",
        title="Multilingual low-literacy mode",
        phase="phase_4",
        status="planned",
        description="Plain-language and culturally adaptive symptom questioning.",
    ),
)


def roadmap_as_dict() -> list[dict[str, str]]:
    """Serialize roadmap for API responses."""
    return [
        {
            "id": item.id,
            "title": item.title,
            "phase": item.phase,
            "status": item.status,
            "description": item.description,
        }
        for item in TRIAGE_ROADMAP
    ]
