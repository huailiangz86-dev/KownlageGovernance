"""Read-only reconciliation of AIOps tenants against approved KH mappings."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from scripts.migration.preflight_knowledgehub import load_json, validate_mapping


def preflight_aiops(tenants_export: Any, mapping_export: Any) -> dict[str, Any]:
    if not isinstance(tenants_export, dict) or not isinstance(tenants_export.get("tenants"), list):
        raise ValueError("AIOps export must contain a tenants array")
    mapping = validate_mapping(mapping_export)
    target_orgs: dict[str, set[str]] = defaultdict(set)
    for (tenant_code, _department), target in mapping.items():
        target_orgs[tenant_code].add(target["target_organization_id"])

    rows = tenants_export["tenants"]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("each tenant must be an object")
    id_counts = Counter(str(row.get("id")) for row in rows if row.get("id") is not None)
    code_counts = Counter(str(row.get("code") or "").strip() for row in rows if row.get("code"))
    root_codes: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.get("organization_id") is not None and row.get("code"):
            root_codes[str(row["organization_id"])].add(str(row["code"]).strip())
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"tenants[{index}] is not an object")
        legacy_id = str(row.get("id")) if row.get("id") is not None else ""
        code = str(row.get("code") or "").strip()
        kh_root = str(row.get("organization_id")) if row.get("organization_id") is not None else ""
        reasons: list[str] = []
        status = "ready"

        if not legacy_id or not code:
            reasons.append("missing_tenant_identity")
            status = "failed"
        if legacy_id and id_counts[legacy_id] > 1:
            reasons.append("duplicate_aiops_tenant_id")
            status = "failed"
        if code and code_counts[code] > 1:
            reasons.append("duplicate_tenant_code")
            status = "failed"

        if row.get("is_deleted") or row.get("status") != "active":
            reasons.append("tenant_not_active")
            if status != "failed":
                status = "quarantined"
        if not kh_root:
            reasons.append("kh_root_organization_missing")
            if status != "failed":
                status = "quarantined"
        elif len(root_codes[kh_root]) > 1:
            reasons.append("kh_root_shared_by_multiple_tenants")
            if status != "failed":
                status = "quarantined"

        orgs = target_orgs.get(code, set())
        if not orgs:
            reasons.append("approved_mapping_missing")
            if status == "ready":
                status = "needs_mapping"
        elif len(orgs) != 1:
            reasons.append("conflicting_target_organizations")
            status = "failed"

        records.append({
            "legacy_aiops_tenant_id": legacy_id or None,
            "tenant_code": code or None,
            "kh_root_organization_id": kh_root or None,
            "target_organization_id": next(iter(orgs)) if len(orgs) == 1 and status == "ready" else None,
            "status": status,
            "reason_codes": reasons,
        })

    counts = dict(sorted(Counter(row["status"] for row in records).items()))
    return {
        "schema_version": 1,
        "mode": "metadata_only_no_writes",
        "counts": counts,
        "records": records,
        "limitations": [
            "AIOps organization_id is the KH tenant root; KH row organization_id may be a department",
            "No credentials, object bytes, or live permissions are verified",
            "Ready is only eligible for a later trial import",
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
    report = preflight_aiops(load_json(args.export), load_json(args.mapping))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report["counts"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
