"""
Scan execution runner.
Executes both tfscan and Checkov on test fixtures and TerraGoat AWS.
Saves raw JSON outputs into results/raw/.
Records deterministic runtime measurements.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "results" / "raw"
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
TERRAGOAT_AWS_DIR = PROJECT_ROOT / "data" / "terragoat" / "terraform" / "aws"


def run_tfscan(target_dir: Path, output_file: Path) -> dict:
    from tfscan.engine import ScannerEngine
    from tfscan.reporter import format_json

    print(f"Running tfscan on {target_dir}...")
    start_time = time.perf_counter()
    engine = ScannerEngine()
    result = engine.scan(target_dir)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    output_file.parent.mkdir(parents=True, exist_ok=True)
    json_data = result.to_dict()
    json_data["scan_duration_ms"] = round(elapsed_ms, 2)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    print(f"  tfscan finished in {elapsed_ms:.2f} ms ({len(result.findings)} findings)")
    return json_data


def run_checkov(target_dir: Path, output_file: Path) -> dict:
    print(f"Running Checkov on {target_dir}...")
    start_time = time.perf_counter()
    cmd = [
        sys.executable,
        "-m",
        "checkov.main",
        "-d",
        str(target_dir),
        "-o",
        "json",
        "--compact",
    ]
    # Checkov returns non-zero when finding failures; capture stdout
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    stdout_text = res.stdout.strip()
    # Checkov can output multiple JSON objects if multiple frameworks match; extract terraform
    try:
        data = json.loads(stdout_text)
    except Exception:
        # Check if output is a list or contains JSON blocks
        data = {"results": {"passed_checks": [], "failed_checks": []}, "summary": {}}
        for line in stdout_text.splitlines():
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict) and "results" in parsed:
                    data = parsed
                    break
            except Exception:
                pass

    output_file.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, list):
        # find the terraform item
        tf_item = next((item for item in data if item.get("check_type") == "terraform"), data[0] if data else {})
        data = tf_item

    data["execution_duration_ms"] = round(elapsed_ms, 2)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    summary = data.get("summary", {})
    print(
        f"  Checkov finished in {elapsed_ms:.2f} ms (Passed: {summary.get('passed', 0)}, Failed: {summary.get('failed', 0)})"
    )
    return data


def run_all_scans():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # 1. tfscan on fixtures
    tf_fix_out = RAW_DIR / "tfscan_fixtures.json"
    run_tfscan(FIXTURES_DIR, tf_fix_out)

    # 2. Checkov on fixtures
    ckv_fix_out = RAW_DIR / "checkov_fixtures.json"
    run_checkov(FIXTURES_DIR, ckv_fix_out)

    # 3. tfscan on TerraGoat AWS
    if not TERRAGOAT_AWS_DIR.is_dir():
        from scripts.fetch_terragoat import fetch_terragoat
        fetch_terragoat()

    tf_tg_out = RAW_DIR / "tfscan_terragoat.json"
    run_tfscan(TERRAGOAT_AWS_DIR, tf_tg_out)

    # 4. Checkov on TerraGoat AWS
    ckv_tg_out = RAW_DIR / "checkov_terragoat.json"
    run_checkov(TERRAGOAT_AWS_DIR, ckv_tg_out)

    print(f"All scan results successfully saved to {RAW_DIR}")


if __name__ == "__main__":
    run_all_scans()
