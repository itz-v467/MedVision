"""Patient search — keyword-first with optional semantic (pgvector) matching."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from backend.client.embedding_client import get_embedding_client
from backend.client.vector_store_client import get_vector_store_client
from backend.config import get_settings
from backend.core.base_service import BaseService
from backend.model.patient_embedding_model import PatientEmbeddingModel
from backend.model.patient_model import PatientModel


def build_patient_search_text(patient: PatientModel) -> str:
    """Canonical text indexed for vector and keyword search."""
    parts = [patient.external_id, patient.full_name]
    if patient.gender:
        parts.append(patient.gender)
    if patient.date_of_birth:
        parts.append(f"age {patient.date_of_birth}")
    return " | ".join(p for p in parts if p)


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[\s|,_-]+", value.lower()) if len(token) >= 2}


class PatientSearchService(BaseService):
    """Index and search patients by name, ID, or semantic similarity."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self._vector = get_vector_store_client()
        self._embedding = get_embedding_client()
        self._settings = get_settings()

    def index_patient(self, patient: PatientModel) -> None:
        """Upsert patient profile into vector index when real embeddings are available."""
        if not self._vector.is_enabled or not self._embedding.is_available:
            return

        self._vector.ensure_extension(self._session)
        search_text = build_patient_search_text(patient)
        embedding = self._embedding.embed(search_text)

        row = (
            self._session.query(PatientEmbeddingModel)
            .filter(PatientEmbeddingModel.patient_id == patient.id)
            .first()
        )
        if row is None:
            row = PatientEmbeddingModel(
                patient_id=patient.id,
                search_text=search_text,
                embedding=embedding,
            )
            self._session.add(row)
        else:
            row.search_text = search_text
            row.embedding = embedding
        self._session.flush()

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search patients by keyword match, with optional high-confidence vector matches."""
        query = (query or "").strip()
        if not query:
            return []

        limit = min(max(limit, 1), 25)
        merged: dict[str, dict[str, Any]] = {}

        text_hits = self._text_search(query, limit)
        for hit in text_hits:
            merged[hit["patient_id"]] = hit

        vector_enabled = (
            self._vector.is_enabled
            and self._embedding.is_available
            and len(query) >= 2
        )
        if vector_enabled:
            min_similarity = self._settings.patient_search_vector_min
            for hit in self._vector_search(query, limit):
                similarity = float(hit.get("similarity", 0))
                if similarity < min_similarity:
                    continue
                if not self._is_relevant_vector_hit(query, hit, similarity):
                    continue

                pid = hit["patient_id"]
                if pid in merged:
                    merged[pid]["similarity"] = max(
                        merged[pid].get("similarity", 0),
                        similarity,
                    )
                    if merged[pid]["match_type"] == "keyword":
                        merged[pid]["match_type"] = "hybrid"
                else:
                    if text_hits and similarity < 0.78:
                        continue
                    merged[pid] = hit

        results = list(merged.values())
        results.sort(
            key=lambda row: (
                0 if row.get("match_type") == "keyword" else 1,
                -row.get("similarity", 0),
            )
        )
        return results[:limit]

    def _is_relevant_vector_hit(
        self, query: str, hit: dict[str, Any], similarity: float
    ) -> bool:
        """Reject vector hits that do not relate to the query text."""
        q = query.lower().strip()
        name = (hit.get("full_name") or "").lower()
        external_id = (hit.get("external_id") or "").lower()

        if q in name or q in external_id or name.startswith(q) or external_id.startswith(q):
            return True

        query_tokens = _tokenize(q)
        patient_tokens = _tokenize(f"{name} {external_id}")
        if query_tokens & patient_tokens:
            return True

        return similarity >= 0.82

    def _text_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        rows = (
            self._session.query(PatientModel)
            .filter(
                or_(
                    PatientModel.full_name.ilike(pattern),
                    PatientModel.external_id.ilike(pattern),
                )
            )
            .order_by(PatientModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            self._patient_hit(p, similarity=0.95, match_type="keyword") for p in rows
        ]

    def _vector_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        self._vector.ensure_extension(self._session)
        query_embedding = self._embedding.embed(query)
        vector_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"

        sql = text(
            """
            SELECT p.id, p.external_id, p.full_name, p.date_of_birth, p.gender,
                   pe.search_text,
                   1 - (pe.embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM patient_embeddings pe
            JOIN patients p ON p.id = pe.patient_id
            ORDER BY pe.embedding <=> CAST(:query_vec AS vector)
            LIMIT :result_limit
            """
        )
        rows = self._session.execute(
            sql,
            {"query_vec": vector_literal, "result_limit": limit},
        ).fetchall()

        hits: list[dict[str, Any]] = []
        for row in rows:
            hits.append(
                {
                    "patient_id": str(row.id),
                    "external_id": row.external_id,
                    "full_name": row.full_name,
                    "age": row.date_of_birth,
                    "gender": row.gender,
                    "search_text": row.search_text,
                    "similarity": float(row.similarity),
                    "match_type": "vector",
                }
            )
        return hits

    def _patient_hit(
        self,
        patient: PatientModel,
        *,
        similarity: float,
        match_type: str,
    ) -> dict[str, Any]:
        return {
            "patient_id": str(patient.id),
            "external_id": patient.external_id,
            "full_name": patient.full_name,
            "age": patient.date_of_birth,
            "gender": patient.gender,
            "search_text": build_patient_search_text(patient),
            "similarity": similarity,
            "match_type": match_type,
        }

    def reindex_all(self) -> int:
        """Backfill vector index for all patients (admin/maintenance)."""
        if not self._vector.is_enabled or not self._embedding.is_available:
            return 0
        patients = self._session.query(PatientModel).all()
        for patient in patients:
            self.index_patient(patient)
        return len(patients)
