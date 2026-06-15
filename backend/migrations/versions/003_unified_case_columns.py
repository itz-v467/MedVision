"""Add unified-case columns: encounters.case_type, imaging_studies.source_document_id."""

from __future__ import annotations

from alembic import op

revision = "003_unified_case_columns"
down_revision = "002_pgvector_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add columns required for multimodal clinical cases."""
    op.execute(
        "ALTER TABLE encounters ADD COLUMN IF NOT EXISTS case_type VARCHAR(50)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_encounters_case_type ON encounters (case_type)"
    )
    op.execute(
        "ALTER TABLE imaging_studies "
        "ADD COLUMN IF NOT EXISTS source_document_id UUID"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_imaging_studies_source_document_id "
        "ON imaging_studies (source_document_id)"
    )
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TABLE imaging_studies
            ADD CONSTRAINT fk_imaging_studies_source_document_id
            FOREIGN KEY (source_document_id) REFERENCES documents(id);
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove unified-case columns."""
    op.execute(
        "ALTER TABLE imaging_studies "
        "DROP CONSTRAINT IF EXISTS fk_imaging_studies_source_document_id"
    )
    op.execute("DROP INDEX IF EXISTS ix_imaging_studies_source_document_id")
    op.execute(
        "ALTER TABLE imaging_studies DROP COLUMN IF EXISTS source_document_id"
    )
    op.execute("DROP INDEX IF EXISTS ix_encounters_case_type")
    op.execute("ALTER TABLE encounters DROP COLUMN IF EXISTS case_type")
