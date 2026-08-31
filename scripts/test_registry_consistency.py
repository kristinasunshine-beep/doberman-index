#!/usr/bin/env python3
"""Regression tests for empty, first-record and ongoing production registries."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from validate_targeted_production_patch import registry_consistency_errors


class RegistryConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def canonical(self, record_id="DI-M-000123", folder="dobermans", entity="doberman", status="published", nested=""):
        path = self.root / "data" / folder / nested / f"{record_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"record_id": record_id, "entity_type": entity, "status": status}), encoding="utf-8")

    def errors(self, *ids):
        return registry_consistency_errors(self.root, {"records": [{"record_id": value, "status": "published"} for value in ids]})

    def test_empty(self):
        self.assertEqual(self.errors(), [])

    def test_first_record(self):
        self.canonical()
        self.assertEqual(self.errors("DI-M-000123"), [])

    def test_multiple_entities(self):
        self.canonical()
        self.canonical("DI-F-000456")
        self.canonical("DI-K-000789", "kennels", "kennel")
        self.canonical("DI-L-000321", "litters", "litter")
        self.assertEqual(self.errors("DI-M-000123", "DI-F-000456", "DI-K-000789", "DI-L-000321"), [])

    def test_stale_registry_entry(self):
        self.assertTrue(self.errors("DI-M-000123"))

    def test_missing_registry_entry(self):
        self.canonical()
        self.assertTrue(self.errors())

    def test_duplicate_registry_id(self):
        self.canonical()
        self.assertTrue(any("duplicate registry" in error for error in self.errors("DI-M-000123", "DI-M-000123")))

    def test_duplicate_canonical_id(self):
        self.canonical()
        self.canonical(nested="accidental-copy")
        self.assertTrue(any("duplicate canonical" in error for error in self.errors("DI-M-000123")))

    def test_nonpublished_canonical_excluded(self):
        self.canonical(status="draft")
        self.assertEqual(self.errors(), [])
        self.assertTrue(self.errors("DI-M-000123"))

    def test_invalid_registry_shape(self):
        self.assertTrue(registry_consistency_errors(self.root, {"records": {}}))
        self.assertTrue(registry_consistency_errors(self.root, {"records": [None]}))

    def test_wrong_folder_or_filename(self):
        self.canonical("DI-K-000789")
        self.assertTrue(self.errors("DI-K-000789"))

    def test_registry_must_be_published(self):
        self.canonical()
        self.assertTrue(registry_consistency_errors(self.root, {"records": [{"record_id": "DI-M-000123", "status": "draft"}]}))


if __name__ == "__main__":
    unittest.main()
