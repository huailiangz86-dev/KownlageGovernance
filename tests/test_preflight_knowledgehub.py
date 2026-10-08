import unittest

from scripts.migration.preflight_knowledgehub import preflight, validate_mapping


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.mapping = validate_mapping({
            "mappings": [{
                "tenant_id": "tenant-a",
                "organization_id": 7,
                "target_organization_id": "org-a",
                "target_project_id": "project-a",
            }]
        })

    def test_never_promotes_cards_or_public_tenant(self):
        export = {
            "knowledge_cards": [
                {"id": 1, "tenant_id": "tenant-a", "organization_id": 7,
                 "content": {"private": "do not copy into report"}},
                {"id": 2, "tenant_id": "000000", "organization_id": 7},
            ]
        }
        report = preflight(export, self.mapping)
        first, second = report["records"]
        self.assertEqual(first["status"], "ready")
        self.assertIn("draft_only_no_publication_evidence", first["reason_codes"])
        self.assertEqual(second["status"], "quarantined")
        self.assertNotIn("private", str(report))
        self.assertNotIn("do not copy", str(report))

    def test_duplicate_and_unmapped_file_stay_out_of_ready(self):
        export = {
            "knowledge_files": [
                {"id": 1, "tenant_id": "tenant-b", "organization_id": 8,
                 "sha256": "a" * 64, "oss_key": "k"},
                {"id": 1, "tenant_id": "tenant-a", "organization_id": 7,
                 "sha256": "a" * 64, "oss_key": "k"},
            ]
        }
        report = preflight(export, self.mapping)
        self.assertEqual(report["records"][0]["status"], "needs_mapping")
        self.assertEqual(report["records"][1]["status"], "failed")
        self.assertEqual(report["counts"], {"failed": 1, "needs_mapping": 1})

    def test_bad_hash_and_locator_quarantined(self):
        export = {
            "knowledge_files": [{
                "id": 3, "tenant_id": "tenant-a", "organization_id": 7,
                "sha256": "bad",
            }]
        }
        report = preflight(export, self.mapping)
        row = report["records"][0]
        self.assertEqual(row["status"], "quarantined")
        self.assertEqual(set(row["reason_codes"]),
                         {"sha256_missing_or_invalid", "object_locator_missing"})

    def test_duplicate_mapping_rejected(self):
        row = {
            "tenant_id": "tenant-a", "organization_id": 7,
            "target_organization_id": "org-a", "target_project_id": "project-a",
        }
        with self.assertRaisesRegex(ValueError, "duplicate mapping"):
            validate_mapping({"mappings": [row, row]})


if __name__ == "__main__":
    unittest.main()
