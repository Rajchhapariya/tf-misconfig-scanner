"""
Scoring module for tfscan vs Checkov.
Computes Precision, Recall, F1, UNKNOWN rates, and scan performance per 100 resources.
Reads ground truth labels from labels/*.csv and raw scan results from results/raw/*.json.
"""
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "results" / "raw"
LABELS_DIR = PROJECT_ROOT / "labels"
DOCS_DIR = PROJECT_ROOT / "docs"
SUMMARY_SCORES_PATH = PROJECT_ROOT / "results" / "summary_scores.json"


def load_checkov_mapping() -> Dict[str, List[str]]:
    mapping = {}
    csv_path = DOCS_DIR / "checkov_mapping.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rule_id = row["rule_id"].strip()
            ckv_ids = [cid.strip() for cid in row["checkov_check_ids"].split(",") if cid.strip()]
            mapping[rule_id] = ckv_ids
    return mapping


def load_terragoat_labels() -> List[Dict[str, str]]:
    labels = []
    with open(LABELS_DIR / "terragoat_labels.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["expected"] in ["FAIL", "PASS", "UNKNOWN"]:
                labels.append(row)
    return labels


def load_fixture_labels() -> List[Dict[str, str]]:
    labels = []
    with open(LABELS_DIR / "fixture_labels.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels.append(row)
    return labels


def normalize_file_name(path_str: str) -> str:
    return Path(path_str).name


def evaluate_dataset(
    dataset_name: str,
    labels: List[Dict[str, str]],
    tfscan_data: Dict[str, Any],
    checkov_data: Dict[str, Any],
    checkov_mapping: Dict[str, List[str]],
) -> Dict[str, Any]:
    # Index tfscan findings by (file_name, resource_address, rule_id) and (file_name, rule_id)
    tfscan_findings_by_resource = {}
    tfscan_findings_by_file_rule = {}
    for f in tfscan_data.get("findings", []):
        fname = normalize_file_name(f["file_path"])
        raddr = f["resource_address"]
        rid = f["rule_id"]
        status = f["status"]
        tfscan_findings_by_resource[(fname, raddr, rid)] = status
        tfscan_findings_by_file_rule[(fname, rid)] = status

    # Index Checkov failed and passed checks
    # Checkov check: check_id, resource, file_path
    checkov_results = checkov_data.get("results", {})
    failed_checks = checkov_results.get("failed_checks", []) or []
    passed_checks = checkov_results.get("passed_checks", []) or []

    checkov_failed_set = set()
    checkov_passed_set = set()

    for c in failed_checks:
        cid = c.get("check_id")
        raddr = c.get("resource")
        fname = normalize_file_name(c.get("file_path", ""))
        checkov_failed_set.add((fname, raddr, cid))
        checkov_failed_set.add((fname, cid))

    for c in passed_checks:
        cid = c.get("check_id")
        raddr = c.get("resource")
        fname = normalize_file_name(c.get("file_path", ""))
        checkov_passed_set.add((fname, raddr, cid))
        checkov_passed_set.add((fname, cid))

    rule_stats: Dict[str, Dict[str, Any]] = {}
    all_rules = sorted(list(checkov_mapping.keys()))

    for rid in all_rules:
        rule_stats[rid] = {
            "tfscan": {"TP": 0, "FP": 0, "TN": 0, "FN": 0, "UNKNOWN": 0, "total": 0},
            "checkov": {"TP": 0, "FP": 0, "TN": 0, "FN": 0, "UNKNOWN": 0, "total": 0},
        }

    for item in labels:
        rid = item["rule_id"]
        if rid not in rule_stats:
            continue
        fname = normalize_file_name(item["file"])
        raddr = item.get("resource_address")
        expected = item["expected"]

        # 1. tfscan evaluation
        tf_status = None
        if raddr and (fname, raddr, rid) in tfscan_findings_by_resource:
            tf_status = tfscan_findings_by_resource[(fname, raddr, rid)]
        elif (fname, rid) in tfscan_findings_by_file_rule:
            tf_status = tfscan_findings_by_file_rule[(fname, rid)]
        else:
            tf_status = "PASS"

        t_stats = rule_stats[rid]["tfscan"]
        t_stats["total"] += 1

        if tf_status == "UNKNOWN":
            t_stats["UNKNOWN"] += 1
            if expected == "FAIL":
                t_stats["FN"] += 1
            elif expected == "PASS":
                t_stats["TN"] += 1
        elif tf_status == "FAIL":
            if expected == "FAIL":
                t_stats["TP"] += 1
            elif expected == "PASS":
                t_stats["FP"] += 1
        elif tf_status == "PASS":
            if expected == "PASS":
                t_stats["TN"] += 1
            elif expected == "FAIL":
                t_stats["FN"] += 1

        # 2. Checkov evaluation
        ckv_ids = checkov_mapping.get(rid, [])
        ckv_status = "PASS"

        is_failed = False
        is_passed = False
        for cid in ckv_ids:
            if raddr and (fname, raddr, cid) in checkov_failed_set:
                is_failed = True
                break
            if (fname, cid) in checkov_failed_set:
                is_failed = True
                break
            if raddr and (fname, raddr, cid) in checkov_passed_set:
                is_passed = True
            if (fname, cid) in checkov_passed_set:
                is_passed = True

        if is_failed:
            ckv_status = "FAIL"
        elif is_passed:
            ckv_status = "PASS"
        else:
            # If no check was triggered or mapped, defaults to not flagging (PASS)
            ckv_status = "PASS"

        c_stats = rule_stats[rid]["checkov"]
        c_stats["total"] += 1

        if ckv_status == "FAIL":
            if expected == "FAIL":
                c_stats["TP"] += 1
            elif expected == "PASS":
                c_stats["FP"] += 1
        elif ckv_status == "PASS":
            if expected == "PASS":
                c_stats["TN"] += 1
            elif expected == "FAIL":
                c_stats["FN"] += 1

    # Compute precision, recall, F1, unknown rate
    results = {}
    for rid, tools in rule_stats.items():
        results[rid] = {}
        for tool_name, counts in tools.items():
            tp = counts["TP"]
            fp = counts["FP"]
            tn = counts["TN"]
            fn = counts["FN"]
            unk = counts["UNKNOWN"]
            tot = counts["total"]

            precision = (tp / (tp + fp)) if (tp + fp) > 0 else (1.0 if tp == 0 and fp == 0 else 0.0)
            recall = (tp / (tp + fn)) if (tp + fn) > 0 else (1.0 if tp == 0 and fn == 0 else 0.0)
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
            unk_rate = (unk / tot) if tot > 0 else 0.0

            results[rid][tool_name] = {
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn,
                "UNKNOWN": unk,
                "total": tot,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "unknown_rate": round(unk_rate, 4),
            }

    return results


def compute_aggregate(rule_metrics: Dict[str, Any]) -> Dict[str, Any]:
    agg = {
        "tfscan": {"TP": 0, "FP": 0, "TN": 0, "FN": 0, "UNKNOWN": 0, "total": 0},
        "checkov": {"TP": 0, "FP": 0, "TN": 0, "FN": 0, "UNKNOWN": 0, "total": 0},
    }
    for rid, tools in rule_metrics.items():
        for tool, m in tools.items():
            agg[tool]["TP"] += m["TP"]
            agg[tool]["FP"] += m["FP"]
            agg[tool]["TN"] += m["TN"]
            agg[tool]["FN"] += m["FN"]
            agg[tool]["UNKNOWN"] += m["UNKNOWN"]
            agg[tool]["total"] += m["total"]

    summary = {}
    for tool, c in agg.items():
        tp, fp, tn, fn, unk, tot = c["TP"], c["FP"], c["TN"], c["FN"], c["UNKNOWN"], c["total"]
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        unk_rate = (unk / tot) if tot > 0 else 0.0
        summary[tool] = {
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "UNKNOWN": unk,
            "total": tot,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "unknown_rate": round(unk_rate, 4),
        }
    return summary


def run_scoring():
    checkov_mapping = load_checkov_mapping()
    terragoat_labels = load_terragoat_labels()
    fixture_labels = load_fixture_labels()

    with open(RAW_DIR / "tfscan_fixtures.json", "r", encoding="utf-8") as f:
        tf_fix_data = json.load(f)
    with open(RAW_DIR / "checkov_fixtures.json", "r", encoding="utf-8") as f:
        ckv_fix_data = json.load(f)
    with open(RAW_DIR / "tfscan_terragoat.json", "r", encoding="utf-8") as f:
        tf_tg_data = json.load(f)
    with open(RAW_DIR / "checkov_terragoat.json", "r", encoding="utf-8") as f:
        ckv_tg_data = json.load(f)

    fixture_scores = evaluate_dataset("fixtures", fixture_labels, tf_fix_data, ckv_fix_data, checkov_mapping)
    terragoat_scores = evaluate_dataset("terragoat", terragoat_labels, tf_tg_data, ckv_tg_data, checkov_mapping)

    combined_labels = fixture_labels + terragoat_labels
    # merge raw findings
    merged_tf_findings = tf_fix_data.get("findings", []) + tf_tg_data.get("findings", [])
    merged_ckv_failed = ckv_fix_data.get("results", {}).get("failed_checks", []) + ckv_tg_data.get("results", {}).get("failed_checks", [])
    merged_ckv_passed = ckv_fix_data.get("results", {}).get("passed_checks", []) + ckv_tg_data.get("results", {}).get("passed_checks", [])

    merged_tf_data = {"findings": merged_tf_findings}
    merged_ckv_data = {"results": {"failed_checks": merged_ckv_failed, "passed_checks": merged_ckv_passed}}

    combined_scores = evaluate_dataset("combined", combined_labels, merged_tf_data, merged_ckv_data, checkov_mapping)

    # Performance scan times
    # Scan time per 100 resources
    tf_fix_ms = tf_fix_data.get("scan_duration_ms", 100.0)
    tf_fix_res = tf_fix_data.get("resources_evaluated", 96)
    ckv_fix_ms = ckv_fix_data.get("execution_duration_ms", 9000.0)
    ckv_fix_res = ckv_fix_data.get("summary", {}).get("resource_count", 96) or 96

    tf_tg_ms = tf_tg_data.get("scan_duration_ms", 100.0)
    tf_tg_res = tf_tg_data.get("resources_evaluated", 35) or 35
    ckv_tg_ms = ckv_tg_data.get("execution_duration_ms", 9000.0)
    ckv_tg_res = ckv_tg_data.get("summary", {}).get("resource_count", 35) or 35

    perf = {
        "fixtures": {
            "tfscan_duration_ms": tf_fix_ms,
            "tfscan_resources": tf_fix_res,
            "tfscan_ms_per_100": round((tf_fix_ms / tf_fix_res) * 100, 2),
            "checkov_duration_ms": ckv_fix_ms,
            "checkov_resources": ckv_fix_res,
            "checkov_ms_per_100": round((ckv_fix_ms / ckv_fix_res) * 100, 2),
            "speedup_factor": round(ckv_fix_ms / max(1.0, tf_fix_ms), 1),
        },
        "terragoat": {
            "tfscan_duration_ms": tf_tg_ms,
            "tfscan_resources": tf_tg_res,
            "tfscan_ms_per_100": round((tf_tg_ms / tf_tg_res) * 100, 2),
            "checkov_duration_ms": ckv_tg_ms,
            "checkov_resources": ckv_tg_res,
            "checkov_ms_per_100": round((ckv_tg_ms / ckv_tg_res) * 100, 2),
            "speedup_factor": round(ckv_tg_ms / max(1.0, tf_tg_ms), 1),
        },
    }

    full_output = {
        "per_rule_scores": combined_scores,
        "aggregate": compute_aggregate(combined_scores),
        "dataset_aggregates": {
            "fixtures": compute_aggregate(fixture_scores),
            "terragoat": compute_aggregate(terragoat_scores),
        },
        "performance": perf,
    }

    SUMMARY_SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    print(f"Summary scores saved to {SUMMARY_SCORES_PATH}")
    agg = full_output["aggregate"]
    print(f"Combined Aggregate: tfscan F1={agg['tfscan']['f1']} | Checkov F1={agg['checkov']['f1']}")
    print(f"Unknown Rate (tfscan): {agg['tfscan']['unknown_rate'] * 100:.1f}%")
    return full_output


if __name__ == "__main__":
    run_scoring()
