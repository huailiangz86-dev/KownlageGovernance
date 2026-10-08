"""Read-only preflight for KnowledgeHub metadata exports.

Input is a JSON export of knowledge_files, knowledge_directories and
knowledge_cards plus an explicit tenant/department-to-project mapping.
This script never connects to a database or moves source objects.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any

TABLES = ("knowledge_directories", "knowledge_files", "knowledge_cards")
PUBLIC_TENANTS = {"000000"}
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def key_for(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("tenant_id")), str(row.get("organization_id"))


def validate_mapping(data: Any) -> dict[tuple[str, str], dict[str, str]]:
    if not isinstance(data, dict) or not isinstance(data.get("mappings"), list):
        raise ValueError("mapping must contain a mappings array")
    result: dict[tuple[str, str], dict[str, str]] = {}
    for index, item in enumerate(data["mappings"]):
        if not isinstance(item, dict):
            raise ValueError(f"mapping row {index} is not an object")
        key = key_for(item)
        if key in result:
            raise ValueError(f"duplicate mapping key at row {index}")
        target_org = item.get("target_organization_id")
        target_project = item.get("target_project_id")
        if not isinstance(target_org, str) or not target_org.strip():
            raise ValueError(f"mapping row {index} lacks target_organization_id")
        if not isinstance(target_project, str) or not target_project.strip():
            raise ValueError(f"mapping row {index} lacks target_project_id")
        result[key] = {
            "target_organization_id": target_org,
            "target_project_id": target_project,
        }
    return result


def preflight(
    export: Any, mapping: dict[tuple[str, str], dict[str, str]]
) -> dict[str, Any]:
    if not isinstance(export, dict):
        raise ValueError("export must be a JSON object")
    records: list[dict[str, Any]] = []
    for table in TABLES:
        rows = export.get(table, [])
        if not isinstance(rows, list):
            raise ValueError(f"{table} must be an array")
        seen: set[str] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{table}[{index}] is not an object")
            old_id = row.get("id")
            identity = str(old_id) if old_id is not None else ""
            reasons: list[str] = []
            status = "ready"
            if not identity:
                reasons.append("missing_legacy_id")
                status = "failed"
            elif identity in seen:
                reasons.append("duplicate_legacy_id")
                status = "failed"
            seen.add(identity)

            tenant = row.get("tenant_id")
            if tenant is None or str(tenant).strip() == "":
                reasons.append("unassigned_tenant")
                status = "quarantined" if status != "failed" else status
            elif str(tenant) in PUBLIC_TENANTS:
                reasons.append("public_tenant_requires_review")
                status = "quarantined" if status != "failed" else status

            target = mapping.get(key_for(row))
            if status == "ready" and target is None:
                reasons.append("project_mapping_missing")
                status = "needs_mapping"

            if table == "knowledge_files" and status != "failed":
                digest = row.get("sha256")
                if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
                    reasons.append("sha256_missing_or_invalid")
                    status = "quarantined" if status != "failed" else status
                if not row.get("oss_key") and not row.get("evidence_path"):
                    reasons.append("object_locator_missing")
                    status = "quarantined" if status != "failed" else status
            if table == "knowledge_cards" and status == "ready":
                reasons.append("draft_only_no_publication_evidence")

            records.append({
                "entity_type": table,
                "legacy_id": identity or None,
                "status": status,
                "reason_codes": reasons,
                "target_organization_id": target["target_organization_id"]
                if target and status == "ready" else None,
                "target_project_id": target["target_project_id"]
                if target and status == "ready" else None,
            })
    counts = dict(sorted(Counter(item["status"] for item in records).items()))
    return {
        "schema_version": 1,
        "mode": "metadata_only_no_writes",
        "counts": counts,
        "records": records,
        "limitations": [
            "Object existence and bytes are not verified",
            "Legacy permissions and card evidence are not verified",
            "Ready means eligible for a later test import, not published",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {args.export.resolve(), args.mapping.resolve()}:
        parser.error("output must differ from export and mapping inputs")
    report = preflight(load_json(args.export), validate_mapping(load_json(args.mapping)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report["counts"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
