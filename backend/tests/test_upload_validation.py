"""Tests for upload document type inference."""

from __future__ import annotations

import pytest

from backend.utils.exceptions import ValidationException
from backend.utils.upload_validation import (
    normalize_file_type,
    resolve_document_type,
    suggest_file_type,
    validate_image_content,
    validate_type_selection,
)
from backend.utils.image_content_classifier import classify_clinical_image


class TestUploadValidation:
  def test_pneumonia_xray_filename_suggests_xray(self) -> None:
    assert suggest_file_type("pnue.jpeg", "image/jpeg") == "xray"

  def test_chest_xray_filename_suggests_xray(self) -> None:
    assert suggest_file_type("patient_chest_xray.png", "image/png") == "xray"

  def test_lab_photo_filename_suggests_lab_report(self) -> None:
    assert suggest_file_type("blood_panel_report.jpg", "image/jpeg") == "lab_report"

  def test_pdf_suggests_lab_report(self) -> None:
    assert suggest_file_type("results.pdf", "application/pdf") == "lab_report"

  def test_resolve_does_not_auto_change_selection(self) -> None:
    resolved = resolve_document_type("pnue.jpeg", "image/jpeg", "lab_report")
    assert resolved == "lab_report"

  def test_resolve_keeps_explicit_xray(self) -> None:
    resolved = resolve_document_type("scan.jpeg", "image/jpeg", "xray")
    assert resolved == "xray"

  def test_validate_rejects_xray_in_lab_report_section(self) -> None:
    with pytest.raises(ValidationException):
      validate_type_selection("chest_xray.png", "image/png", "lab_report")

  def test_validate_rejects_lab_in_xray_section(self) -> None:
    with pytest.raises(ValidationException):
      validate_type_selection("blood_report.jpg", "image/jpeg", "xray")

  def test_normalize_rejects_missing_type(self) -> None:
    with pytest.raises(ValidationException):
      normalize_file_type("")

  def test_validate_image_content_rejects_lab_in_xray_section(self, tmp_path) -> None:
    from PIL import Image

    path = tmp_path / "lab_like.png"
    img = Image.new("RGB", (400, 500), (255, 255, 255))
    for x in range(40, 360):
      for y in range(80, 120):
        img.putpixel((x, y), (200, 40, 40))
    img.save(path)

    assert classify_clinical_image(str(path)) == "lab_report"
    with pytest.raises(ValidationException):
      validate_image_content(str(path), "xray")

  def test_validate_image_content_rejects_xray_in_lab_section(self, tmp_path) -> None:
    from PIL import Image

    path = tmp_path / "xray_like.png"
    img = Image.new("L", (512, 512), 90)
    for x in range(100, 400):
      for y in range(120, 380):
        img.putpixel((x, y), 140 + ((x * y) % 40))
    img.convert("RGB").save(path)

    with pytest.raises(ValidationException):
      validate_image_content(str(path), "lab_report")
