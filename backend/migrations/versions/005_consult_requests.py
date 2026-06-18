"""Add consult_requests table."""

from __future__ import annotations

from alembic import op

revision = "005_consult_requests"
down_revision = "004_triage_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS consult_requests (
            id UUID PRIMARY KEY,
            encounter_id UUID NOT NULL REFERENCES encounters(id),
            patient_id UUID NOT NULL REFERENCES patients(id),
            requested_by_user_id UUID NOT NULL REFERENCES users(id),
            urgency VARCHAR(30) NOT NULL DEFAULT 'within_24h',
            reason TEXT,
            status VARCHAR(30) NOT NULL DEFAULT 'pending',
            external_link_used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_consult_requests_encounter_id "
        "ON consult_requests (encounter_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_consult_requests_status "
        "ON consult_requests (status)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS consult_requests")
