"""Base test case for agile sprint-aligned unit tests."""

from __future__ import annotations

import unittest


class BaseTestCase(unittest.TestCase):
    """Shared assertions and helpers for MedVision tests."""

    def assert_success_response(self, payload: dict) -> None:
        """Assert API success envelope."""
        self.assertTrue(payload.get("success"))
        self.assertIn("data", payload)
