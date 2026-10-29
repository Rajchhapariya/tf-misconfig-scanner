"""List every labelled item where tfscan and Checkov reach different verdicts.

Verdicts are collapsed to FAIL / PASS / OTHER (UNKNOWN, NO_FINDING, NO_CHECK) and compared.
The generated columns come from saved results. The one-line explanation is the only
hand-written column; it is read from docs/disagreement_notes.csv (key: dataset,file,resource_address,rule_id)
and left blank where no note has been written. Nothing is auto-explained.
"""
import csv
from typing import Dict, List

from eval.common import (
    DOCS_DIR, FIXTURES, TERRAGOAT, PROJECT_ROOT,
    load_checkov_mapping, load_index, load_labels,
)

OUT_CSV = PROJECT_ROOT / "results" / "disagreement_report.csv"
OUT_MD = PROJECT_ROOT / "results" / "disagreement_report.md"
NOTES = DOCS_DIR / "disagreement_notes.csv"


def _verdict(s: str) -> str:
    return s if s in ("FAIL", "PASS") else "OTHER"


def _load_notes() -> Dict[tuple, str]:
    notes = {}
    if NOTES.exists():
        with open(NOTES, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                notes[(r["dataset"], r["file"], r["resource_address"], r["rule_id"])] = r["explanation"]
    return notes


def _right(expected: str, tf: str, ck: str) -> str:
    if expected == "UNKNOWN":
        return "n/a (unknowable)"
    tfv, ckv = _verdict(tf), _verdict(ck)
    tf_ok = tfv == expected
    ck_ok = ckv == expected
    return "both" if tf_ok and ck_ok else "tfscan" if tf_ok else "checkov" if ck_ok else "neither"


def build() -> List[Dict[str, str]]:
    mapping = load_checkov_mapping()
    notes = _load_notes()
    rows = []
    for dataset in (FIXTURES, TERRAGOAT):
        index = load_index(dataset)
        for item in load_labels(dataset):
            rid = item["rule_id"]
            if rid not in mapping:
                continue
            raddr = item.get("resource_address") or None
            tf = index.tfscan_status(item["key"], raddr, rid)
            ck = index.checkov_status(item["key"], raddr, rid, mapping)
            if _verdict(tf) == _verdict(ck):
                continue
            k = (dataset, item["key"], raddr or "", rid)
            rows.append({
                "dataset": dataset, "file": item["key"], "resource_address": raddr or "",
                "rule_id": rid, "expected": item["expected"], "tfscan": tf, "checkov": ck,
                "who_was_right": _right(item["expected"], tf, ck),
                "explanation": notes.get(k, ""),
            })
    return rows


def main() -> None:
    rows = build()
    cols = ["dataset", "file", "resource_address", "rule_id", "expected", "tfscan", "checkov", "who_was_right", "explanation"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(f"`{r[c]}`" if c in ("file", "resource_address") and r[c] else r[c] for c in cols) + " |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    from collections import Counter
    print(len(rows), "disagreements;", dict(Counter(r["who_was_right"] for r in rows)))


if __name__ == "__main__":
    main()
