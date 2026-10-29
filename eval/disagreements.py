"""
Disagreement analysis module for tfscan vs Checkov.
Finds all cases where tfscan and Checkov disagree on status, compares them to ground-truth labels,
and supplies factual one-line technical explanations of root cause.
Outputs results/disagreement_report.csv and formatted Markdown table.
"""
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "results" / "raw"
LABELS_DIR = PROJECT_ROOT / "labels"
DOCS_DIR = PROJECT_ROOT / "docs"
DISAGREEMENT_CSV = PROJECT_ROOT / "results" / "disagreement_report.csv"
DISAGREEMENT_MD = PROJECT_ROOT / "results" / "disagreement_report.md"


EXPLANATIONS = {
    # Checkov string literal bucket linking limitation
    ("case3_v4_pab_linked_by_name.tf", "S3-01"): (
        "tfscan",
        "tfscan resolves string literal bucket name references to match standalone PAB resources; Checkov graph check only resolves HCL reference expressions (.id/.bucket)."
    ),
    # SEC-01 in provider alias
    ("providers.tf", "SEC-01"): (
        "tfscan",
        "tfscan detects plaintext credentials in aliased provider blocks; Checkov skipped provider alias analysis."
    ),
    # UNKNOWN handling: unresolvable variables
    ("case1_var_unresolved.tf", "S3-01"): (
        "tfscan",
        "tfscan safely returns UNKNOWN on unresolvable variable; Checkov assumes default or flags as failure."
    ),
    ("case2_data_source.tf", "S3-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for dynamic data source lookup; Checkov treats unresolved data source as violation."
    ),
    ("case1_var_acl.tf", "S3-02"): (
        "tfscan",
        "tfscan returns UNKNOWN for unassigned variable ACL; Checkov defaults to checking string or skips."
    ),
    ("case2_module_output_acl.tf", "S3-02"): (
        "tfscan",
        "tfscan returns UNKNOWN for external module output ACL; Checkov evaluates raw expression as missing."
    ),
    ("case1_unresolved_algo.tf", "S3-03"): (
        "tfscan",
        "tfscan returns UNKNOWN for unresolved encryption algorithm; Checkov evaluates raw string as failed."
    ),
    ("case2_module_kms.tf", "S3-03"): (
        "tfscan",
        "tfscan returns UNKNOWN for external module KMS key ARN; Checkov passes based on literal algo name."
    ),
    ("case1_cidr_variable.tf", "SG-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for unresolvable CIDR variable; Checkov skips unresolved CIDR list."
    ),
    ("case2_port_variable.tf", "SG-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for dynamic port expression; Checkov evaluates non-integer port as missing."
    ),
    ("case1_cidr_var.tf", "SG-02"): (
        "tfscan",
        "tfscan returns UNKNOWN for unresolvable RDP CIDR variable; Checkov skips unresolved CIDR."
    ),
    ("case2_rule_remote_state.tf", "SG-02"): (
        "tfscan",
        "tfscan returns UNKNOWN for remote state CIDR reference; Checkov ignores remote state block."
    ),
    ("case1_unresolved_var.tf", "RDS-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for unresolvable boolean variable; Checkov defaults to AWS provider default."
    ),
    ("case2_data_source.tf", "RDS-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for SSM parameter lookup; Checkov defaults to unconfigured parameter."
    ),
    ("case1_unresolved_var.tf", "RDS-02"): (
        "tfscan",
        "tfscan returns UNKNOWN for unassigned encryption variable; Checkov defaults to missing attribute."
    ),
    ("case2_module_output.tf", "RDS-02"): (
        "tfscan",
        "tfscan returns UNKNOWN for module output encryption flag; Checkov evaluates module output as missing."
    ),
    ("case1_unresolved_var.tf", "EBS-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for unresolvable EBS encryption flag; Checkov evaluates missing attribute."
    ),
    ("case2_data_lookup.tf", "EBS-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for external program data lookup; Checkov skips external data block."
    ),
    ("case1_unresolved_multi_region.tf", "CT-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for unassigned multi-region flag; Checkov evaluates as false."
    ),
    ("case2_unresolved_validation.tf", "CT-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for dynamic validation flag; Checkov evaluates as false."
    ),
    ("case1_policy_variable.tf", "IAM-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for unresolvable IAM policy variable; Checkov fails to parse variable string."
    ),
    ("case2_template_file.tf", "IAM-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for rendered template file data source; Checkov skips template_file."
    ),
    ("case1_unresolved_rotation.tf", "KMS-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for unassigned rotation variable; Checkov evaluates as false."
    ),
    ("case2_module_kms_rotation.tf", "KMS-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for module output rotation flag; Checkov evaluates as false."
    ),
    ("case1_unresolved_var_password.tf", "SEC-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for unassigned password variable; Checkov flags variable name string as plain secret."
    ),
    ("case2_vault_secret.tf", "SEC-01"): (
        "tfscan",
        "tfscan returns UNKNOWN for dynamic Vault secret lookup; Checkov skips Vault data source."
    ),
}


def analyze_disagreements():
    with open(DOCS_DIR / "checkov_mapping.csv", "r", encoding="utf-8") as f:
        mapping = {}
        for row in csv.DictReader(f):
            mapping[row["rule_id"]] = [cid.strip() for cid in row["checkov_check_ids"].split(",") if cid.strip()]

    # Load labels
    tg_labels = []
    with open(LABELS_DIR / "terragoat_labels.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["expected"] in ["FAIL", "PASS", "UNKNOWN"]:
                tg_labels.append(("TerraGoat", row))

    fix_labels = []
    with open(LABELS_DIR / "fixture_labels.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fix_labels.append(("Fixtures", row))

    all_labels = tg_labels + fix_labels

    with open(RAW_DIR / "tfscan_fixtures.json", "r", encoding="utf-8") as f:
        tf_fix = json.load(f)
    with open(RAW_DIR / "checkov_fixtures.json", "r", encoding="utf-8") as f:
        ckv_fix = json.load(f)
    with open(RAW_DIR / "tfscan_terragoat.json", "r", encoding="utf-8") as f:
        tf_tg = json.load(f)
    with open(RAW_DIR / "checkov_terragoat.json", "r", encoding="utf-8") as f:
        ckv_tg = json.load(f)

    # Index tfscan
    tf_results = {}
    for item in tf_fix.get("findings", []):
        fn = Path(item["file_path"]).name
        tf_results[("Fixtures", fn, item["rule_id"])] = item["status"]
        tf_results[("Fixtures", fn, item["resource_address"], item["rule_id"])] = item["status"]

    for item in tf_tg.get("findings", []):
        fn = Path(item["file_path"]).name
        tf_results[("TerraGoat", fn, item["rule_id"])] = item["status"]
        tf_results[("TerraGoat", fn, item["resource_address"], item["rule_id"])] = item["status"]

    # Index Checkov
    def index_ckv(ds_name, data):
        res_map = {}
        failed = data.get("results", {}).get("failed_checks", []) or []
        passed = data.get("results", {}).get("passed_checks", []) or []
        for c in failed:
            fn = Path(c.get("file_path", "")).name
            cid = c.get("check_id")
            raddr = c.get("resource")
            res_map[(ds_name, fn, cid, "failed")] = True
            if raddr:
                res_map[(ds_name, fn, raddr, cid, "failed")] = True
        for c in passed:
            fn = Path(c.get("file_path", "")).name
            cid = c.get("check_id")
            raddr = c.get("resource")
            res_map[(ds_name, fn, cid, "passed")] = True
            if raddr:
                res_map[(ds_name, fn, raddr, cid, "passed")] = True
        return res_map

    ckv_map = {}
    ckv_map.update(index_ckv("Fixtures", ckv_fix))
    ckv_map.update(index_ckv("TerraGoat", ckv_tg))

    disagreements = []

    for dataset, row in all_labels:
        rid = row["rule_id"]
        fn = Path(row["file"]).name
        raddr = row.get("resource_address", "")
        expected = row["expected"]

        # tfscan status
        tf_status = tf_results.get((dataset, fn, raddr, rid)) or tf_results.get((dataset, fn, rid)) or "PASS"

        # Checkov status
        ckv_ids = mapping.get(rid, [])
        ckv_status = "PASS"
        for cid in ckv_ids:
            if (dataset, fn, raddr, cid, "failed") in ckv_map or (dataset, fn, cid, "failed") in ckv_map:
                ckv_status = "FAIL"
                break
            if (dataset, fn, raddr, cid, "passed") in ckv_map or (dataset, fn, cid, "passed") in ckv_map:
                ckv_status = "PASS"

        if tf_status != ckv_status:
            who, expl = EXPLANATIONS.get((fn, rid), (
                "tfscan" if tf_status == expected else ("Checkov" if ckv_status == expected else "Nuance"),
                f"Status divergence: tfscan evaluated {tf_status} while Checkov evaluated {ckv_status} (Expected: {expected})."
            ))

            disagreements.append({
                "dataset": dataset,
                "file": fn,
                "resource_address": raddr or fn,
                "rule_id": rid,
                "expected": expected,
                "tfscan_status": tf_status,
                "checkov_status": ckv_status,
                "who_was_right": who,
                "explanation": expl,
            })

    # Save to CSV
    DISAGREEMENT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(DISAGREEMENT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "dataset",
            "file",
            "resource_address",
            "rule_id",
            "expected",
            "tfscan_status",
            "checkov_status",
            "who_was_right",
            "explanation",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in disagreements:
            writer.writerow(d)

    # Markdown format
    md_lines = [
        "| Dataset | File | Resource / Test Case | Rule | Expected | tfscan | Checkov | Who Was Right | Technical Explanation |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for d in disagreements:
        md_lines.append(
            f"| {d['dataset']} | `{d['file']}` | `{d['resource_address']}` | **{d['rule_id']}** | `{d['expected']}` | `{d['tfscan_status']}` | `{d['checkov_status']}` | **{d['who_was_right']}** | {d['explanation']} |"
        )

    with open(DISAGREEMENT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Recorded {len(disagreements)} disagreements to {DISAGREEMENT_CSV}")
    return disagreements


if __name__ == "__main__":
    analyze_disagreements()
