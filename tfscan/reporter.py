"""
Output formatters for tfscan: Table, JSON, and SARIF v2.1.0.
"""
import json
from pathlib import Path
from typing import Any, Dict

from tfscan.models import ScanResult, Severity, Status


def format_table(result: ScanResult) -> str:
    lines = []
    lines.append("=" * 88)
    lines.append(f"TFSCAN STATIC MISCONFIGURATION REPORT: {result.target_path}")
    lines.append("=" * 88)
    lines.append(
        f"Files Scanned: {result.files_scanned} | Evaluated Resources: {result.resources_evaluated} | Duration: {result.scan_duration_ms:.2f} ms"
    )
    lines.append(
        f"Summary: FAIL={result.summary['FAIL']} | PASS={result.summary['PASS']} | UNKNOWN={result.summary['UNKNOWN']} | TOTAL={result.summary['TOTAL']}"
    )
    lines.append("-" * 88)

    col_fmt = "{:<8} {:<8} {:<9} {:<32} {:<26}"
    lines.append(col_fmt.format("RULE ID", "STATUS", "SEVERITY", "RESOURCE", "DETAILS"))
    lines.append("-" * 88)

    # Sort findings: FAIL first, then UNKNOWN, then PASS
    sort_order = {Status.FAIL: 0, Status.UNKNOWN: 1, Status.PASS: 2, Status.SKIPPED: 3}
    sorted_findings = sorted(result.findings, key=lambda f: (sort_order.get(f.status, 9), f.rule_id))

    for f in sorted_findings:
        res_addr = f.resource_address
        if len(res_addr) > 30:
            res_addr = res_addr[:27] + "..."
        msg = f.message
        if len(msg) > 60:
            msg = msg[:57] + "..."
        lines.append(col_fmt.format(f.rule_id, f.status.value, f.severity.value, res_addr, msg))

    lines.append("=" * 88)
    if result.has_failures:
        lines.append("SCAN RESULT: FAILED (Non-zero exit code gating CI/CD pipeline)")
    else:
        lines.append("SCAN RESULT: PASSED (Zero security policy violations found)")
    lines.append("=" * 88)
    return "\n".join(lines)


def format_json(result: ScanResult) -> str:
    return json.dumps(result.to_dict(), indent=2)


def format_sarif(result: ScanResult) -> str:
    """
    Formats the scan result into standard SARIF v2.1.0 JSON format for GitHub Code Scanning.
    """
    rule_defs = {}
    sarif_results = []

    level_map = {
        Severity.CRITICAL: "error",
        Severity.HIGH: "error",
        Severity.MEDIUM: "warning",
        Severity.LOW: "note",
        Severity.INFORMATIONAL: "note",
    }

    for f in result.findings:
        if f.rule_id not in rule_defs:
            rule_defs[f.rule_id] = {
                "id": f.rule_id,
                "name": f.rule_title,
                "shortDescription": {"text": f.rule_title},
                "fullDescription": {"text": f.rule_title},
                "defaultConfiguration": {"level": level_map.get(f.severity, "warning")},
                "properties": {
                    "severity": f.severity.value,
                    "cisControls": f.cis_controls,
                    "awsControls": f.aws_controls,
                },
            }

        # Include FAIL and UNKNOWN findings in SARIF
        if f.status == Status.FAIL or f.status == Status.UNKNOWN:
            sarif_level = "error" if f.status == Status.FAIL else "note"
            try:
                uri = Path(f.file_path).as_posix()
            except Exception:
                uri = f.file_path

            res_entry: Dict[str, Any] = {
                "ruleId": f.rule_id,
                "level": sarif_level,
                "message": {"text": f"[{f.status.value}] {f.message} on {f.resource_address}"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": uri},
                            "region": {
                                "startLine": max(1, f.line_number),
                                "startColumn": 1,
                            },
                        }
                    }
                ],
                "properties": {
                    "resourceAddress": f.resource_address,
                    "evaluationStatus": f.status.value,
                },
            }
            sarif_results.append(res_entry)

    sarif_doc = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "tf-misconfig-scanner",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/rajchhapariya/tf-misconfig-scanner",
                        "rules": list(rule_defs.values()),
                    }
                },
                "results": sarif_results,
            }
        ],
    }
    return json.dumps(sarif_doc, indent=2)
