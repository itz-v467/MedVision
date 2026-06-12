"""Add pgvector extension and document_embeddings table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002_pgvector_embeddings"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable pgvector and create embeddings table."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )
    op.execute(
        "ALTER TABLE document_embeddings " "ADD COLUMN embedding vector(384) NOT NULL"
    )
    op.create_index(
        "ix_document_embeddings_encounter_id",
        "document_embeddings",
        ["encounter_id"],
    )


def downgrade() -> None:
    """Drop embeddings table."""
    op.drop_table("document_embeddings")
