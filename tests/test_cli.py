"""
CLI integration tests for tfscan.
Tests format output options (table, json, sarif) and CI gating exit codes.
"""
import json
from pathlib import Path
import subprocess
import sys

from tfscan.cli import main

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_cli_exit_code_on_fail(tmp_path):
    vulnerable_file = FIXTURES_DIR / "S3-01" / "fail" / "case1_v3_no_pab.tf"
    exit_code = main(["scan", str(vulnerable_file), "--format", "json"])
    assert exit_code == 1, "Expected exit code 1 for vulnerable target"


def test_cli_exit_code_on_pass(tmp_path):
    compliant_file = FIXTURES_DIR / "KMS-01" / "pass" / "case1_explicit_true.tf"
    exit_code = main(["scan", str(compliant_file), "--format", "json"])
    assert exit_code == 0, "Expected exit code 0 for compliant target"


def test_cli_json_format(capsys):
    target = FIXTURES_DIR / "S3-02" / "fail" / "case1_v3_public_read.tf"
    exit_code = main(["scan", str(target), "--format", "json"])
    assert exit_code == 1

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "target_path" in data
    assert "findings" in data
    assert data["summary"]["FAIL"] >= 1


def test_cli_sarif_format(capsys):
    target = FIXTURES_DIR / "SG-01" / "fail" / "case1_inline_all_0.tf"
    exit_code = main(["scan", str(target), "--format", "sarif"])
    assert exit_code == 1

    captured = capsys.readouterr()
    sarif = json.loads(captured.out)
    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) > 0
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "tf-misconfig-scanner"
    assert len(run["results"]) >= 1
    assert run["results"][0]["ruleId"] == "SG-01"


def test_cli_invalid_path():
    exit_code = main(["scan", "non_existent_directory_xyz", "--format", "table"])
    assert exit_code == 2, "Expected exit code 2 for non-existent path"
