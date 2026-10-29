"""
Execution engine for tfscan.
Runs all registered rules against parsed Terraform resources in the ScanContext.
"""
from pathlib import Path
import time
from typing import List, Optional

from tfscan.models import Finding, ScanResult
from tfscan.parser import ScanContext, parse_directory
from tfscan.rules import ALL_RULES, Rule


class ScannerEngine:
    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules = rules or ALL_RULES

    def scan(self, target_path: Path | str, is_plan_json: bool = False) -> ScanResult:
        start_time = time.perf_counter()
        target = Path(target_path)

        if is_plan_json or (target.is_file() and target.suffix.lower() == ".json"):
            from tfscan.parser import parse_plan_json
            context = parse_plan_json(target)
        else:
            context = parse_directory(target)

        findings: List[Finding] = []
        evaluated_addresses = set()

        for rule in self.rules:
            # Check providers if rule targets provider
            if any(t.startswith("provider.") for t in rule.resource_types):
                for prov in context.providers:
                    if prov.resource_type in rule.resource_types:
                        f = rule.evaluate(prov, context)
                        findings.append(f)
                        evaluated_addresses.add(prov.address)

            # Check resources
            for rtype in rule.resource_types:
                if rtype.startswith("provider."):
                    continue
                resources = context.get_resources_by_type(rtype)
                for res in resources:
                    f = rule.evaluate(res, context)
                    findings.append(f)
                    evaluated_addresses.add(res.address)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ScanResult(
            target_path=str(target),
            files_scanned=len(context.files),
            resources_evaluated=len(evaluated_addresses),
            findings=findings,
            scan_duration_ms=round(elapsed_ms, 2),
        )
