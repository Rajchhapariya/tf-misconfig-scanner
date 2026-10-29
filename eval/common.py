"""Shared helpers for scoring: label loading, result indexing, per-item status lookup.

Fixture results are keyed by their full relative path (fixtures/<rule>/<status>/<name>.tf),
never by bare file name, because the same file name appears under several rules.
TerraGoat results are keyed by bare file name, which is unique in terraform/aws.
"""
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "results" / "raw"
LABELS_DIR = PROJECT_ROOT / "labels"
DOCS_DIR = PROJECT_ROOT / "docs"

FIXTURES = "Fixtures"
TERRAGOAT = "TerraGoat"


def load_checkov_mapping() -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    with open(DOCS_DIR / "checkov_mapping.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mapping[row["rule_id"].strip()] = [c.strip() for c in row["checkov_check_ids"].split(",") if c.strip()]
    return mapping


def load_aliases() -> Dict[tuple, Dict[str, str]]:
    """Label address -> the address each tool uses for the same object (docs/address_aliases.csv)."""
    out: Dict[tuple, Dict[str, str]] = {}
    path = DOCS_DIR / "address_aliases.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                out[(r["dataset"], r["file"], r["label_address"])] = r
    return out


def load_labels(dataset: str) -> List[Dict[str, str]]:
    name = "fixture_labels.csv" if dataset == FIXTURES else "terragoat_labels.csv"
    rows = []
    with open(LABELS_DIR / name, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["expected"] in ("FAIL", "PASS", "UNKNOWN"):
                row = dict(row)
                row["dataset"] = dataset
                row["key"] = file_key(dataset, row["file"])
                rows.append(row)
    return rows


def file_key(dataset: str, path_str: str) -> str:
    """Fixtures: posix path starting at 'fixtures/'. TerraGoat: bare file name."""
    p = Path(path_str.replace("\\", "/"))
    if dataset == FIXTURES:
        parts = p.parts
        if "fixtures" in parts:
            parts = parts[parts.index("fixtures"):]
        return "/".join(parts)
    return p.name


class ToolIndex:
    """Indexes one dataset's raw tfscan and Checkov output."""

    def __init__(self, dataset: str, tf_data: Dict[str, Any], ckv_data: Dict[str, Any]):
        self.dataset = dataset
        self.aliases = load_aliases()
        self.tf: Dict[Tuple, List[str]] = {}
        for f in tf_data.get("findings", []):
            key = file_key(dataset, f["file_path"])
            self.tf.setdefault((key, f["rule_id"]), []).append(f["status"])
            self.tf.setdefault((key, f["resource_address"], f["rule_id"]), []).append(f["status"])
        self.ckv: Dict[Tuple, List[str]] = {}
        res = ckv_data.get("results", {})
        for label, checks in (("FAIL", res.get("failed_checks") or []), ("PASS", res.get("passed_checks") or [])):
            for c in checks:
                key = file_key(dataset, c.get("file_path", ""))
                cid = c.get("check_id")
                self.ckv.setdefault((key, cid), []).append(label)
                if c.get("resource"):
                    self.ckv.setdefault((key, c["resource"], cid), []).append(label)

    def tfscan_status(self, key: str, raddr: Optional[str], rid: str) -> str:
        alias = self.aliases.get((self.dataset, key, raddr)) if raddr else None
        if alias:
            raddr = alias["tfscan_address"]
        statuses = self.tf.get((key, raddr, rid)) if raddr else None
        if not statuses:
            statuses = self.tf.get((key, rid))
        if not statuses:
            return "NO_FINDING"
        if "FAIL" in statuses:
            return "FAIL"
        if "UNKNOWN" in statuses:
            return "UNKNOWN"
        return "PASS"

    def checkov_status(self, key: str, raddr: Optional[str], rid: str, mapping: Dict[str, List[str]]) -> str:
        seen = []
        alias = self.aliases.get((self.dataset, key, raddr)) if raddr else None
        if alias:
            raddr = alias["checkov_address"]
        for cid in mapping.get(rid, []):
            s = self.ckv.get((key, raddr, cid)) if raddr else None
            if not s:
                s = self.ckv.get((key, cid))
            if s:
                seen.extend(s)
        if not seen:
            return "NO_CHECK"
        return "FAIL" if "FAIL" in seen else "PASS"


def load_index(dataset: str) -> ToolIndex:
    tag = "fixtures" if dataset == FIXTURES else "terragoat"
    with open(RAW_DIR / f"tfscan_{tag}.json", "r", encoding="utf-8") as f:
        tf = json.load(f)
    with open(RAW_DIR / f"checkov_{tag}.json", "r", encoding="utf-8") as f:
        ckv = json.load(f)
    return ToolIndex(dataset, tf, ckv)
