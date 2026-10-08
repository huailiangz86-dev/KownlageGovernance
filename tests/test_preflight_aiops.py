import unittest

from scripts.migration.preflight_aiops import preflight_aiops


class AIOpsPreflightTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {"mappings": [
            {"tenant_id": "acme", "organization_id": 10,
             "target_organization_id": "org-acme", "target_project_id": "project-a"},
            {"tenant_id": "acme", "organization_id": 11,
             "target_organization_id": "org-acme", "target_project_id": "project-b"},
        ]}

    def test_active_tenant_matches_code_without_leaking_key(self):
        report = preflight_aiops({"tenants": [{
            "id": 1, "code": "acme", "organization_id": 99,
            "status": "active", "is_deleted": False,
            "api_key": "secret-value", "contact_email": "person@example.com",
        }]}, self.mapping)
        row = report["records"][0]
        self.assertEqual(row["status"], "ready")
        self.assertEqual(row["target_organization_id"], "org-acme")
        self.assertNotIn("secret-value", str(report))
        self.assertNotIn("person@example.com", str(report))

    def test_shared_kh_root_quarantines_both_tenants(self):
        mapping = {"mappings": self.mapping["mappings"] + [{
            "tenant_id": "other", "organization_id": 20,
            "target_organization_id": "org-other", "target_project_id": "project-other",
        }]}
        tenants = {"tenants": [
            {"id": 1, "code": "acme", "organization_id": 99,
             "status": "active", "is_deleted": False},
            {"id": 2, "code": "other", "organization_id": 99,
             "status": "active", "is_deleted": False},
        ]}
        report = preflight_aiops(tenants, mapping)
        self.assertEqual(report["counts"], {"quarantined": 2})

    def test_conflicting_target_orgs_fail(self):
        mapping = {"mappings": self.mapping["mappings"] + [{
            "tenant_id": "acme", "organization_id": 12,
            "target_organization_id": "another-org", "target_project_id": "project-c",
        }]}
        report = preflight_aiops({"tenants": [{
            "id": 1, "code": "acme", "organization_id": 99,
            "status": "active", "is_deleted": False,
        }]}, mapping)
        self.assertEqual(report["records"][0]["status"], "failed")

    def test_pending_tenant_not_ready(self):
        report = preflight_aiops({"tenants": [{
            "id": 1, "code": "acme", "organization_id": 99,
            "status": "pending", "is_deleted": False,
        }]}, self.mapping)
        self.assertEqual(report["records"][0]["status"], "quarantined")


if __name__ == "__main__":
    unittest.main()
