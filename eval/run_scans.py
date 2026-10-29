"""Scan execution runner.

Fixtures are staged one per directory so that variables, resource names and file names from
different fixtures can never interact. Both tools scan the staged copies; findings are mapped
back to the original fixtures/<rule>/<status>/<name>.tf path.

Timing is recorded two ways: in-process engine time (tfscan only) and subprocess wall time for
both tools, which includes interpreter start-up for each.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "results" / "raw"
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
STAGED_DIR = PROJECT_ROOT / "results" / "staged_fixtures"
TERRAGOAT_AWS_DIR = PROJECT_ROOT / "data" / "terragoat" / "terraform" / "aws"


def stage_fixtures() -> dict:
    if STAGED_DIR.exists():
        shutil.rmtree(STAGED_DIR)
    mapping = {}
    for tf in sorted(FIXTURES_DIR.rglob("*.tf")):
        rel = tf.relative_to(PROJECT_ROOT).as_posix()
        rule, status = tf.parent.parent.name, tf.parent.name
        staged_name = f"{rule}__{status}__{tf.stem}"
        d = STAGED_DIR / staged_name
        d.mkdir(parents=True)
        shutil.copy2(tf, d / tf.name)
        for extra in tf.parent.glob(f"{tf.stem}.tfvars"):
            shutil.copy2(extra, d / extra.name)
        mapping[staged_name] = rel
    return mapping


def run_subprocess(cmd, label):
    start = time.perf_counter()
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    ms = (time.perf_counter() - start) * 1000.0
    print(f"  {label}: {ms:.0f} ms wall")
    return res, ms


def parse_checkov_json(stdout_text: str) -> dict:
    try:
        data = json.loads(stdout_text.strip())
    except Exception:
        return {"results": {"passed_checks": [], "failed_checks": []}, "summary": {}}
    if isinstance(data, list):
        data = next((i for i in data if i.get("check_type") == "terraform"), data[0] if data else {})
    return data


def run_tfscan_dirs(dirs, rewrite) -> dict:
    from tfscan.engine import ScannerEngine

    engine = ScannerEngine()
    findings, resources = [], 0
    start = time.perf_counter()
    for d in dirs:
        result = engine.scan(d)
        payload = result.to_dict()
        resources += payload.get("resources_evaluated", 0)
        for f in payload["findings"]:
            f["file_path"] = rewrite(d, f["file_path"])
            findings.append(f)
    ms = (time.perf_counter() - start) * 1000.0
    return {"findings": findings, "resources_evaluated": resources, "scan_duration_ms": round(ms, 2)}


def run_all_scans():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stage_map = stage_fixtures()
    (RAW_DIR / "fixture_stage_map.json").write_text(json.dumps(stage_map, indent=2), encoding="utf-8")
    staged_dirs = sorted(p for p in STAGED_DIR.iterdir() if p.is_dir())

    # --- fixtures: tfscan (in-process, one directory per fixture)
    print("tfscan on staged fixtures...")
    tf_fix = run_tfscan_dirs(staged_dirs, lambda d, fp: stage_map[d.name])
    # --- fixtures: tfscan wall time through the CLI on the staged root
    _, tf_fix_wall = run_subprocess(
        [sys.executable, "-m", "tfscan.cli", "scan", str(STAGED_DIR), "--format", "json"], "tfscan CLI (fixtures)"
    )
    tf_fix["cli_wall_ms"] = round(tf_fix_wall, 2)
    (RAW_DIR / "tfscan_fixtures.json").write_text(json.dumps(tf_fix, indent=2), encoding="utf-8")

    # --- fixtures: Checkov over the staged root (each fixture is its own directory)
    print("Checkov on staged fixtures...")
    res, ckv_wall = run_subprocess(
        [sys.executable, "-m", "checkov.main", "-d", str(STAGED_DIR), "-o", "json", "--compact"],
        "Checkov (fixtures)",
    )
    ckv_fix = parse_checkov_json(res.stdout)
    for bucket in ("failed_checks", "passed_checks"):
        for c in ckv_fix.get("results", {}).get(bucket, []) or []:
            parent = Path(c.get("file_path", "").replace("\\", "/")).parent.name
            if parent in stage_map:
                c["file_path"] = stage_map[parent]
    ckv_fix["execution_duration_ms"] = round(ckv_wall, 2)
    (RAW_DIR / "checkov_fixtures.json").write_text(json.dumps(ckv_fix, indent=2), encoding="utf-8")

    # --- TerraGoat AWS
    if not TERRAGOAT_AWS_DIR.is_dir():
        from scripts.fetch_terragoat import fetch_terragoat
        fetch_terragoat()
    print("tfscan on TerraGoat AWS...")
    tf_tg = run_tfscan_dirs([TERRAGOAT_AWS_DIR], lambda d, fp: fp)
    _, tf_tg_wall = run_subprocess(
        [sys.executable, "-m", "tfscan.cli", "scan", str(TERRAGOAT_AWS_DIR), "--format", "json"], "tfscan CLI (TerraGoat)"
    )
    tf_tg["cli_wall_ms"] = round(tf_tg_wall, 2)
    (RAW_DIR / "tfscan_terragoat.json").write_text(json.dumps(tf_tg, indent=2), encoding="utf-8")

    print("Checkov on TerraGoat AWS...")
    res, ckv_tg_wall = run_subprocess(
        [sys.executable, "-m", "checkov.main", "-d", str(TERRAGOAT_AWS_DIR), "-o", "json", "--compact"],
        "Checkov (TerraGoat)",
    )
    ckv_tg = parse_checkov_json(res.stdout)
    ckv_tg["execution_duration_ms"] = round(ckv_tg_wall, 2)
    (RAW_DIR / "checkov_terragoat.json").write_text(json.dumps(ckv_tg, indent=2), encoding="utf-8")
    print(f"All scan results saved to {RAW_DIR}")


if __name__ == "__main__":
    run_all_scans()
