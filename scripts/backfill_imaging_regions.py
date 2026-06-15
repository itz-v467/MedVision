#!/usr/bin/env python3
"""Backfill imaging anomaly regions for existing encounters."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import get_database_manager
from backend.dao.document_dao import DocumentDao
from backend.logger import get_logger
from backend.model.document_model import ImagingStudyModel, InferenceResultModel
from backend.utils.imaging_regions import derive_anomaly_regions
from backend.utils.storage_paths import resolve_storage_file_optional

logger = get_logger()


def backfill(dry_run: bool = False) -> int:
    """Recompute and persist regions for encounters missing bounding boxes."""
    db = get_database_manager()
    updated = 0
    skipped = 0

    with db.session_scope() as session:
        dao = DocumentDao(session)
        rows = (
            session.query(ImagingStudyModel, InferenceResultModel)
            .join(
                InferenceResultModel,
                InferenceResultModel.imaging_study_id == ImagingStudyModel.id,
            )
            .all()
        )

        for study, inference in rows:
            boxes = inference.bounding_boxes if isinstance(inference.bounding_boxes, dict) else {}
            regions = boxes.get("regions") or []
            if regions:
                skipped += 1
                continue

            resolved = resolve_storage_file_optional(study.storage_path)
            if not resolved:
                logger.warning("Skip study %s — file not found", study.id)
                skipped += 1
                continue

            new_regions = derive_anomaly_regions(str(resolved), inference.findings or {})
            if not new_regions:
                logger.warning("No regions derived for study %s", study.id)
                skipped += 1
                continue

            if dry_run:
                logger.info("Would update study %s with %d region(s)", study.id, len(new_regions))
                updated += 1
                continue

            if not isinstance(inference.bounding_boxes, dict):
                inference.bounding_boxes = {}
            inference.bounding_boxes["regions"] = new_regions
            proof = inference.bounding_boxes.get("analysis_proof")
            if isinstance(proof, dict):
                proof["regions"] = new_regions
            dao.save_inference(inference)
            updated += 1
            logger.info("Updated study %s | regions=%d", study.id, len(new_regions))

    logger.info("Backfill complete | updated=%d skipped=%d", updated, skipped)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Log actions without writing")
    args = parser.parse_args()
    count = backfill(dry_run=args.dry_run)
    print(f"Regions backfilled for {count} study/studies.")


if __name__ == "__main__":
    main()
