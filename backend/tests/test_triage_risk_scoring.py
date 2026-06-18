"""Tests for triage risk scoring."""

from backend.service.triage_risk_scoring_service import TriageRiskScoringService


class TestTriageRiskScoring:
    def test_emergency_chest_pain(self) -> None:
        scorer = TriageRiskScoringService()
        result = scorer.score("I have severe chest pain and cannot breathe")
        assert result["risk_level"] == "emergency"
        assert result["escalation_required"] is True

    def test_low_mild_symptoms(self) -> None:
        scorer = TriageRiskScoringService()
        result = scorer.score("mild headache since morning")
        assert result["risk_level"] in {"low", "moderate"}

    def test_conversation_takes_highest_risk(self) -> None:
        scorer = TriageRiskScoringService()
        messages = [
            {"role": "patient", "message_text": "I have a cough"},
            {"role": "patient", "message_text": "now I have crushing chest pain"},
        ]
        result = scorer.score_conversation(messages)
        assert result["risk_level"] == "emergency"
