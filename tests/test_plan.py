"""
Tests for Terraform Plan JSON scanning (Stretch Goal 2).
"""
import json
from pathlib import Path
from tfscan.cli import main
from tfscan.engine import ScannerEngine
from tfscan.models import Status


def test_plan_json_scanning(tmp_path):
    plan_data = {
        "format_version": "1.0",
        "terraform_version": "1.9.8",
        "planned_values": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_s3_bucket.vulnerable_bucket",
                        "type": "aws_s3_bucket",
                        "name": "vulnerable_bucket",
                        "values": {
                            "bucket": "test-plan-bucket",
                            "acl": "public-read",
                        },
                    },
                    {
                        "address": "aws_kms_key.secure_key",
                        "type": "aws_kms_key",
                        "name": "secure_key",
                        "values": {
                            "description": "plan key",
                            "enable_key_rotation": True,
                        },
                    },
                ]
            }
        },
    }

    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan_data), encoding="utf-8")

    engine = ScannerEngine()
    result = engine.scan(plan_file, is_plan_json=True)

    assert result.has_failures is True

    # S3-02 should fail on vulnerable_bucket
    s3_findings = [f for f in result.findings if f.rule_id == "S3-02"]
    assert len(s3_findings) == 1
    assert s3_findings[0].status == Status.FAIL

    # KMS-01 should pass on secure_key
    kms_findings = [f for f in result.findings if f.rule_id == "KMS-01"]
    assert len(kms_findings) == 1
    assert kms_findings[0].status == Status.PASS


def test_cli_plan_flag(tmp_path):
    plan_data = {
        "planned_values": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_kms_key.clean_key",
                        "type": "aws_kms_key",
                        "name": "clean_key",
                        "values": {
                            "enable_key_rotation": True,
                        },
                    }
                ]
            }
        }
    }
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan_data), encoding="utf-8")

    exit_code = main(["scan", str(plan_file), "--plan", "--format", "json"])
    assert exit_code == 0
