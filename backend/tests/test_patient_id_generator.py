"""Tests for MedVision patient number generation."""

from backend.db import get_database_manager
from backend.model.patient_model import PatientModel
from backend.utils.patient_id_generator import (
    generate_patient_external_id,
    resolve_patient_external_id,
    should_auto_generate_patient_id,
)


def test_should_auto_generate_sentinels():
    assert should_auto_generate_patient_id(None) is True
    assert should_auto_generate_patient_id("") is True
    assert should_auto_generate_patient_id("AUTO") is True
    assert should_auto_generate_patient_id("P-UNKNOWN") is True
    assert should_auto_generate_patient_id("MV-20260101-0001") is False


def test_generate_patient_external_id_sequential(app):
    with get_database_manager().session_scope() as session:
        first = generate_patient_external_id(session)
        session.add(PatientModel(external_id=first, full_name="Test Patient A"))
        session.flush()
        second = generate_patient_external_id(session)

    assert first.startswith("MV-")
    assert second.startswith("MV-")
    assert first.rsplit("-", 1)[0] == second.rsplit("-", 1)[0]
    assert int(second.rsplit("-", 1)[-1]) == int(first.rsplit("-", 1)[-1]) + 1


def test_resolve_patient_external_id_preserves_hospital_id(app):
    with get_database_manager().session_scope() as session:
        resolved = resolve_patient_external_id(session, "UHID-99881")
    assert resolved == "UHID-99881"
