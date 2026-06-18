"""Add triage_sessions and triage_messages tables."""

from __future__ import annotations

from alembic import op

revision = "004_triage_tables"
down_revision = "003_unified_case_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create symptom triage persistence tables."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS triage_sessions (
            id UUID PRIMARY KEY,
            encounter_id UUID NOT NULL REFERENCES encounters(id),
            patient_id UUID NOT NULL REFERENCES patients(id),
            status VARCHAR(30) NOT NULL DEFAULT 'active',
            risk_level VARCHAR(20) NOT NULL DEFAULT 'low',
            recommended_disposition TEXT,
            assessment JSONB NOT NULL DEFAULT '{}',
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finalized_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_triage_sessions_encounter_id "
        "ON triage_sessions (encounter_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_triage_sessions_patient_id "
        "ON triage_sessions (patient_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_triage_sessions_status "
        "ON triage_sessions (status)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS triage_messages (
            id UUID PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES triage_sessions(id),
            role VARCHAR(20) NOT NULL,
            message_text TEXT NOT NULL,
            structured_symptoms JSONB NOT NULL DEFAULT '{}',
            safety_flags JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_triage_messages_session_id "
        "ON triage_messages (session_id)"
    )


def downgrade() -> None:
    """Drop triage tables."""
    op.execute("DROP TABLE IF EXISTS triage_messages")
    op.execute("DROP TABLE IF EXISTS triage_sessions")
