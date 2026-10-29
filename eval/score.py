"""Scoring for tfscan vs Checkov against hand-written labels.

Per label item the tool status is one of:
  tfscan : FAIL, PASS, UNKNOWN, NO_FINDING (no finding emitted for that file/resource and rule)
  Checkov: FAIL, PASS, NO_CHECK (none of the mapped checks fired for that file/resource)

Scoring rules:
  expected FAIL    : tool FAIL = TP; anything else = FN
  expected PASS    : tool FAIL = FP; anything else = TN
  expected UNKNOWN : not part of precision/recall. tfscan UNKNOWN = correct_unknown;
                     a confident FAIL/PASS = overconfident. Checkov has no UNKNOWN state, so a
                     FAIL/PASS = overconfident and NO_CHECK = abstained.
A missing finding is never silently counted as PASS: it is counted in no_finding / no_check
and, for expected FAIL, it is a missed detection (FN).
"""
import json
from pathlib import Path
from typing import Any, Dict, List

from eval.common import (
    FIXTURES,
    TERRAGOAT,
    PROJECT_ROOT,
    RAW_DIR,
    load_checkov_mapping,
    load_index,
    load_labels,
)

SUMMARY_SCORES_PATH = PROJECT_ROOT / "results" / "summary_scores.json"
EXCLUDED_FROM_HEADLINE = ["S3-03"]


def _blank() -> Dict[str, int]:
    return {
        "TP": 0, "FP": 0, "TN": 0, "FN": 0,
        "labelled": 0, "scored": 0,
        "unknown_returned": 0, "no_result": 0,
        "unknowable_items": 0, "correct_unknown": 0, "overconfident": 0, "abstained": 0,
    }


def _count(stats: Dict[str, int], expected: str, status: str, is_tfscan: bool) -> None:
    stats["labelled"] += 1
    if status == "UNKNOWN":
        stats["unknown_returned"] += 1
    if status in ("NO_FINDING", "NO_CHECK"):
        stats["no_result"] += 1
    if expected == "UNKNOWN":
        stats["unknowable_items"] += 1
        if is_tfscan and status == "UNKNOWN":
            stats["correct_unknown"] += 1
        elif status in ("NO_CHECK", "NO_FINDING"):
            stats["abstained"] += 1
        else:
            stats["overconfident"] += 1
        return
    stats["scored"] += 1
    if expected == "FAIL":
        stats["TP" if status == "FAIL" else "FN"] += 1
    else:
        stats["FP" if status == "FAIL" else "TN"] += 1


def _metrics(c: Dict[str, int]) -> Dict[str, Any]:
    tp, fp, fn = c["TP"], c["FP"], c["FN"]
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else (0.0 if precision is not None and recall is not None else None)
    out = dict(c)
    out["precision"] = None if precision is None else round(precision, 4)
    out["recall"] = None if recall is None else round(recall, 4)
    out["f1"] = None if f1 is None else round(f1, 4)
    out["unknown_rate"] = round(c["unknown_returned"] / c["labelled"], 4) if c["labelled"] else 0.0
    return out


def evaluate(dataset: str, mapping: Dict[str, List[str]]) -> Dict[str, Any]:
    index = load_index(dataset)
    labels = load_labels(dataset)
    stats = {rid: {"tfscan": _blank(), "checkov": _blank()} for rid in mapping}
    rows = []
    for item in labels:
        rid = item["rule_id"]
        if rid not in stats:
            continue
        raddr = item.get("resource_address") or None
        tf = index.tfscan_status(item["key"], raddr, rid)
        ck = index.checkov_status(item["key"], raddr, rid, mapping)
        _count(stats[rid]["tfscan"], item["expected"], tf, True)
        _count(stats[rid]["checkov"], item["expected"], ck, False)
        rows.append({
            "dataset": dataset, "file": item["key"], "resource_address": raddr or "",
            "rule_id": rid, "expected": item["expected"], "tfscan": tf, "checkov": ck,
        })
    return {"stats": stats, "rows": rows}


def _merge(*stat_maps: Dict[str, Any], exclude=()) -> Dict[str, Dict[str, int]]:
    agg = {"tfscan": _blank(), "checkov": _blank()}
    for sm in stat_maps:
        for rid, tools in sm.items():
            if rid in exclude:
                continue
            for tool, c in tools.items():
                for k, v in c.items():
                    agg[tool][k] += v
    return agg


def run_scoring() -> Dict[str, Any]:
    mapping = load_checkov_mapping()
    fx = evaluate(FIXTURES, mapping)
    tg = evaluate(TERRAGOAT, mapping)

    per_rule = {}
    for rid in sorted(mapping):
        merged = _merge({rid: fx["stats"][rid]}, {rid: tg["stats"][rid]})
        per_rule[rid] = {t: _metrics(c) for t, c in merged.items()}

    all_stats = _merge(fx["stats"], tg["stats"])
    headline = _merge(fx["stats"], tg["stats"], exclude=EXCLUDED_FROM_HEADLINE)
    aggregate = {t: _metrics(c) for t, c in all_stats.items()}
    aggregate_headline = {t: _metrics(c) for t, c in headline.items()}
    dataset_aggregates = {
        "fixtures": {t: _metrics(c) for t, c in _merge(fx["stats"]).items()},
        "terragoat": {t: _metrics(c) for t, c in _merge(tg["stats"]).items()},
    }

    with open(RAW_DIR / "tfscan_fixtures.json", encoding="utf-8") as f:
        tf_fix = json.load(f)
    with open(RAW_DIR / "checkov_fixtures.json", encoding="utf-8") as f:
        ck_fix = json.load(f)
    with open(RAW_DIR / "tfscan_terragoat.json", encoding="utf-8") as f:
        tf_tg = json.load(f)
    with open(RAW_DIR / "checkov_terragoat.json", encoding="utf-8") as f:
        ck_tg = json.load(f)

    def perf(tf, ck):
        res = max(tf.get("resources_evaluated", 0), 1)
        return {
            "resources": tf.get("resources_evaluated", 0),
            "tfscan_engine_ms": tf.get("scan_duration_ms"),
            "tfscan_cli_wall_ms": tf.get("cli_wall_ms"),
            "checkov_wall_ms": ck.get("execution_duration_ms"),
            "tfscan_cli_ms_per_100": round(tf.get("cli_wall_ms", 0) / res * 100, 1),
            "checkov_ms_per_100": round(ck.get("execution_duration_ms", 0) / res * 100, 1),
            "wall_ratio": round(ck.get("execution_duration_ms", 0) / max(tf.get("cli_wall_ms", 1), 1), 1),
        }

    out = {
        "per_rule_scores": per_rule,
        "aggregate": aggregate,
        "aggregate_headline": aggregate_headline,
        "headline_excludes": EXCLUDED_FROM_HEADLINE,
        "dataset_aggregates": dataset_aggregates,
        "performance": {"fixtures": perf(tf_fix, ck_fix), "terragoat": perf(tf_tg, ck_tg)},
        "item_rows": fx["rows"] + tg["rows"],
    }
    SUMMARY_SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_SCORES_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    for name, agg in (("all 12 rules", aggregate), ("headline", aggregate_headline)):
        t, c = agg["tfscan"], agg["checkov"]
        print(f"{name}: tfscan P={t['precision']} R={t['recall']} F1={t['f1']} | checkov P={c['precision']} R={c['recall']} F1={c['f1']}")
    return out


if __name__ == "__main__":
    run_scoring()
