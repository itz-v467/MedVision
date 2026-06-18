"""Guided symptom-triage conversation when no LLM API key is configured."""

from __future__ import annotations

import re
from typing import Any

from backend.constants.triage_policy import TRIAGE_DISCLAIMER

_SYMPTOM_FOLLOW_UPS: dict[str, list[str]] = {
    "fever": [
        "What is the highest temperature you have measured, and for how many days?",
        "Have you had chills, body aches, or night sweats?",
    ],
    "cough": [
        "Is the cough dry or are you bringing up mucus?",
        "Any chest tightness, wheezing, or blood when you cough?",
    ],
    "headache": [
        "How severe is the pain on a scale of 1–10, and when did it start?",
        "Any vision changes, neck stiffness, or this is the worst headache of your life?",
    ],
    "pain": [
        "Where exactly is the pain, and does it spread anywhere?",
        "What makes it better or worse — movement, eating, breathing?",
    ],
    "chest": [
        "Does the chest discomfort worsen with exertion or deep breaths?",
        "Any shortness of breath, sweating, nausea, or pain radiating to arm or jaw?",
    ],
    "breath": [
        "Did the breathing difficulty start suddenly or gradually?",
        "Can you speak in full sentences, or do you feel you cannot get enough air?",
    ],
    "nausea": [
        "How many episodes of vomiting, and can you keep fluids down?",
        "Any abdominal pain, diarrhea, or recent new medications?",
    ],
    "rash": [
        "Where is the rash and is it itchy, painful, or spreading quickly?",
        "Any lip or tongue swelling, or trouble breathing?",
    ],
    "dizziness": [
        "Do you feel the room spinning, or lightheaded like you might faint?",
        "Any recent head injury, dehydration, or new medications?",
    ],
    "throat": [
        "Is swallowing painful and do you have a fever?",
        "Any muffled voice, drooling, or difficulty opening the mouth?",
    ],
}

_GENERAL_FOLLOW_UPS = [
    "When did these symptoms start, and have they been getting better, worse, or staying the same?",
    "Are you taking any medications or do you have known allergies we should note?",
    "Do you have any chronic conditions such as diabetes, heart disease, asthma, or pregnancy?",
]

_MISSING_FACTOR_QUESTIONS: dict[str, str] = {
    "age": "How old are you (in years)? This helps us assess risk.",
    "symptom_duration": "How many days have you had these symptoms?",
    "fever_duration_days": "How many days have you had fever?",
    "fever_temperature": "What is the highest temperature you measured (°F or °C)?",
    "symptoms": "What is your main symptom right now?",
}


def _missing_factor_questions(missing: list[str]) -> list[str]:
    questions: list[str] = []
    for key in missing:
        question = _MISSING_FACTOR_QUESTIONS.get(key)
        if question and question not in questions:
            questions.append(question)
        if len(questions) >= 2:
            break
    return questions


def _patient_turns(messages: list[dict[str, Any]]) -> list[str]:
    texts: list[str] = []
    for msg in messages:
        if (msg.get("role") or "").lower() in {"user", "patient"}:
            text = (msg.get("message_text") or msg.get("content") or "").strip()
            if text:
                texts.append(text)
    return texts


def _detect_topics(text: str) -> list[str]:
    lowered = text.lower()
    topics: list[str] = []
    mapping = {
        "fever": ["fever", "temperature", "temp"],
        "cough": ["cough", "coughing"],
        "headache": ["headache", "migraine"],
        "chest": ["chest pain", "chest tight", "chest pressure"],
        "breath": ["breath", "breathing", "shortness of breath", "sob"],
        "nausea": ["nausea", "vomit", "vomiting", "throwing up"],
        "rash": ["rash", "hives", "itchy skin"],
        "dizziness": ["dizzy", "dizziness", "lightheaded", "vertigo"],
        "throat": ["sore throat", "throat pain", "swallow"],
        "pain": ["pain", "ache", "hurts", "sore"],
    }
    for topic, keywords in mapping.items():
        if any(kw in lowered for kw in keywords):
            topics.append(topic)
    return topics or ["pain"]


def _pick_questions(topics: list[str], turn_index: int) -> list[str]:
    questions: list[str] = []
    for topic in topics[:2]:
        for question in _SYMPTOM_FOLLOW_UPS.get(topic, []):
            if question not in questions:
                questions.append(question)
            if len(questions) >= 2:
                break
        if len(questions) >= 2:
            break
    if len(questions) < 2:
        for question in _GENERAL_FOLLOW_UPS:
            if question not in questions:
                questions.append(question)
            if len(questions) >= 2:
                break
    if turn_index > 1:
        questions = [
            "Has anything changed since your last message — better, worse, or new symptoms?",
            "On a scale of 1–10, how much are these symptoms affecting your daily activities?",
        ]
    return questions[:2]


def _empathic_opening(last_message: str, patient_name: str | None) -> str:
    name = (patient_name or "").strip()
    greeting = f"Thank you for explaining that{', ' + name.split()[0] if name else ''}."
    snippet = last_message.strip()
    if len(snippet) > 160:
        snippet = f"{snippet[:157]}…"
    if snippet:
        return f"{greeting} I understand you are dealing with: \"{snippet}\"."
    return f"{greeting} I want to gather a few more details for your doctor."


def generate_guided_triage_reply(
    messages: list[dict[str, Any]],
    context: dict[str, Any],
    assessment: dict[str, Any],
) -> str:
    """Produce a contextual, question-driven triage reply without an external LLM."""
    turns = _patient_turns(messages)
    if not turns:
        return (
            "Please describe your main symptom, when it started, and how severe it feels. "
            f"{TRIAGE_DISCLAIMER}"
        )

    last_message = turns[-1]
    topics = _detect_topics(" ".join(turns))
    missing = assessment.get("missing_factors") or []
    missing_questions = _missing_factor_questions(missing)
    questions = missing_questions or _pick_questions(topics, len(turns))

    parts = [_empathic_opening(last_message, context.get("patient_name"))]

    risk = assessment.get("risk_level", "low")
    if risk == "emergency":
        parts.append(
            "Some of what you described may need emergency care. "
            "If you feel unsafe right now, call your local emergency number immediately."
        )
    elif risk == "high":
        parts.append(
            "Based on your symptoms, same-day medical evaluation would be prudent."
        )
    elif risk == "moderate":
        parts.append(
            "These symptoms may benefit from a clinic visit within the next day or two if they continue."
        )
    else:
        parts.append(
            "I do not see emergency red flags in what you shared so far, but we should still clarify a few details."
        )

    age = (context.get("patient_age") or "").strip()
    if age.isdigit() and int(age) >= 65:
        parts.append(
            "Because you are in an older age group, it is especially important to monitor for worsening symptoms."
        )

    parts.append("To help your clinician prepare, could you tell me:")
    for idx, question in enumerate(questions, start=1):
        parts.append(f"{idx}. {question}")

    disposition = assessment.get("recommended_disposition")
    if disposition and risk in {"moderate", "high", "emergency"}:
        parts.append(f"Preliminary guidance: {disposition}")

    parts.append(TRIAGE_DISCLAIMER)
    return " ".join(parts)
