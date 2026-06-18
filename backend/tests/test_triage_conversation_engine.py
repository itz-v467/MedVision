"""Tests for guided triage conversation engine."""

from backend.service.triage_conversation_engine import generate_guided_triage_reply
from backend.service.triage_risk_scoring_service import TriageRiskScoringService


class TestTriageConversationEngine:
    def test_fever_reply_asks_follow_up_questions(self) -> None:
        messages = [
            {"role": "assistant", "message_text": "Welcome"},
            {"role": "patient", "message_text": "I have fever and cough for 3 days"},
        ]
        assessment = TriageRiskScoringService().score_conversation(messages)
        reply = generate_guided_triage_reply(
            messages,
            {"patient_name": "Alex", "patient_age": "32"},
            assessment,
        )
        assert "fever" in reply.lower() or "temperature" in reply.lower()
        assert "?" in reply
        assert "physician" in reply.lower() or "doctor" in reply.lower()

    def test_emergency_reply_mentions_urgent_care(self) -> None:
        messages = [
            {"role": "patient", "message_text": "crushing chest pain and cannot breathe"},
        ]
        assessment = TriageRiskScoringService().score_conversation(messages)
        reply = generate_guided_triage_reply(messages, {}, assessment)
        assert assessment["risk_level"] == "emergency"
        assert "emergency" in reply.lower()

    def test_second_turn_changes_questions(self) -> None:
        first_turn = [{"role": "patient", "message_text": "sore throat"}]
        second_turn = [
            {"role": "patient", "message_text": "sore throat"},
            {"role": "assistant", "message_text": "first reply"},
            {"role": "patient", "message_text": "started 2 days ago, pain when swallowing"},
        ]
        assessment = TriageRiskScoringService().score_conversation(second_turn)
        reply = generate_guided_triage_reply(second_turn, {}, assessment)
        assert "worse" in reply.lower() or "scale" in reply.lower()
