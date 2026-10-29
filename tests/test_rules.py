"""
Integration tests evaluating each rule against hand-crafted test fixtures.
Verifies that all 97 fixtures across all 12 rules produce expected status:
- fail/* -> FAIL
- pass/* -> PASS
- unknown/* -> UNKNOWN
"""
from pathlib import Path
import pytest

from tfscan.engine import ScannerEngine
from tfscan.models import Status
from tfscan.rules import ALL_RULES, RULE_REGISTRY

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.mark.parametrize("rule_id", sorted(RULE_REGISTRY.keys()))
@pytest.mark.parametrize("status", ["fail", "pass", "unknown"])
def test_rule_fixtures(rule_id: str, status: str):
    rule = RULE_REGISTRY[rule_id]
    rule_dir = FIXTURES_DIR / rule_id / status
    assert rule_dir.is_dir(), f"Missing fixture directory: {rule_dir}"

    fixture_files = list(rule_dir.glob("*.tf"))
    assert len(fixture_files) >= (2 if status == "unknown" else 3), f"Not enough {status} fixtures for {rule_id}"

    engine = ScannerEngine(rules=[rule])
    expected_status = Status[status.upper()]

    for fpath in fixture_files:
        result = engine.scan(fpath)
        matching_findings = [f for f in result.findings if f.rule_id == rule_id]
        assert len(matching_findings) > 0, f"No findings emitted for {rule_id} on {fpath.name}"

        # If multiple resources exist in the fixture, find the primary finding matching expected status
        statuses = [f.status for f in matching_findings]
        assert expected_status in statuses, (
            f"Expected {expected_status} for {rule_id} in {fpath.name}, but got {[s.value for s in statuses]}"
        )
