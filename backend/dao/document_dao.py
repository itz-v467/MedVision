"""Document and AI result data access object."""

from __future__ import annotations

import uuid

from backend.core.base_dao import BaseDao
from backend.model.document_model import (
    AlertModel,
    ClinicalSummaryModel,
    DocumentModel,
    ImagingStudyModel,
    InferenceResultModel,
    NlpExtractionModel,
    OcrResultModel,
)


class DocumentDao(BaseDao):
    """Database operations for documents and AI artifacts."""

    def create_document(self, document: DocumentModel) -> DocumentModel:
        """Persist document metadata."""
        self._session.add(document)
        self._session.flush()
        return document

    def find_document(self, document_id: uuid.UUID) -> DocumentModel | None:
        """Return document by ID."""
        return (
            self._session.query(DocumentModel)
            .filter(DocumentModel.id == document_id)
            .first()
        )

    def save_ocr_result(self, result: OcrResultModel) -> OcrResultModel:
        """Persist OCR output."""
        self._session.add(result)
        self._session.flush()
        return result

    def save_nlp_extraction(self, extraction: NlpExtractionModel) -> NlpExtractionModel:
        """Persist NLP output."""
        self._session.add(extraction)
        self._session.flush()
        return extraction

    def create_imaging_study(self, study: ImagingStudyModel) -> ImagingStudyModel:
        """Persist imaging study."""
        self._session.add(study)
        self._session.flush()
        return study

    def save_inference(self, inference: InferenceResultModel) -> InferenceResultModel:
        """Persist imaging inference."""
        self._session.add(inference)
        self._session.flush()
        return inference

    def save_summary(self, summary: ClinicalSummaryModel) -> ClinicalSummaryModel:
        """Persist clinical summary."""
        self._session.add(summary)
        self._session.flush()
        return summary

    def find_summary_by_encounter(
        self, encounter_id: uuid.UUID
    ) -> ClinicalSummaryModel | None:
        """Return latest summary for encounter."""
        return (
            self._session.query(ClinicalSummaryModel)
            .filter(ClinicalSummaryModel.encounter_id == encounter_id)
            .order_by(ClinicalSummaryModel.created_at.desc())
            .first()
        )

    def find_summary_by_id(self, summary_id: uuid.UUID) -> ClinicalSummaryModel | None:
        """Return summary by ID."""
        return (
            self._session.query(ClinicalSummaryModel)
            .filter(ClinicalSummaryModel.id == summary_id)
            .first()
        )

    def find_ocr_by_document(self, document_id: uuid.UUID) -> OcrResultModel | None:
        """Return OCR result for a document."""
        return (
            self._session.query(OcrResultModel)
            .filter(OcrResultModel.document_id == document_id)
            .order_by(OcrResultModel.created_at.desc())
            .first()
        )

    def find_ocr_by_encounter(self, encounter_id: uuid.UUID) -> OcrResultModel | None:
        """Return latest OCR result for an encounter."""
        return (
            self._session.query(OcrResultModel)
            .join(DocumentModel, OcrResultModel.document_id == DocumentModel.id)
            .filter(DocumentModel.encounter_id == encounter_id)
            .order_by(OcrResultModel.created_at.desc())
            .first()
        )

    def find_nlp_by_encounter(
        self, encounter_id: uuid.UUID
    ) -> NlpExtractionModel | None:
        """Return latest NLP extraction for an encounter."""
        return (
            self._session.query(NlpExtractionModel)
            .filter(NlpExtractionModel.encounter_id == encounter_id)
            .order_by(NlpExtractionModel.created_at.desc())
            .first()
        )

    def find_imaging_by_encounter(
        self, encounter_id: uuid.UUID
    ) -> tuple[ImagingStudyModel | None, InferenceResultModel | None]:
        """Return latest imaging study and inference for an encounter."""
        study = (
            self._session.query(ImagingStudyModel)
            .filter(ImagingStudyModel.encounter_id == encounter_id)
            .order_by(ImagingStudyModel.created_at.desc())
            .first()
        )
        if study is None:
            return None, None
        inference = (
            self._session.query(InferenceResultModel)
            .filter(InferenceResultModel.imaging_study_id == study.id)
            .order_by(InferenceResultModel.created_at.desc())
            .first()
        )
        return study, inference

    def find_alert_by_id(self, alert_id: uuid.UUID) -> AlertModel | None:
        """Return alert by ID."""
        return self._session.query(AlertModel).filter(AlertModel.id == alert_id).first()

    def find_alerts_by_encounter(self, encounter_id: uuid.UUID) -> list[AlertModel]:
        """Return alerts for an encounter."""
        return (
            self._session.query(AlertModel)
            .filter(AlertModel.encounter_id == encounter_id)
            .order_by(AlertModel.created_at.desc())
            .all()
        )

    def find_documents_by_encounter(
        self, encounter_id: uuid.UUID
    ) -> list[DocumentModel]:
        """Return documents linked to an encounter."""
        return (
            self._session.query(DocumentModel)
            .filter(DocumentModel.encounter_id == encounter_id)
            .order_by(DocumentModel.created_at.desc())
            .all()
        )
