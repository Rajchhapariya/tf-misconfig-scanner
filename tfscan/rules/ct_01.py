"""
Rule CT-01: CloudTrail trail is not multi-region, or log file validation is off.
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class CT01MultiRegionAndLogValidation(Rule):
    id = "CT-01"
    title = "CloudTrail trail is not multi-region, or log file validation is off"
    severity = Severity.HIGH
    resource_types = ["aws_cloudtrail"]
    cis_controls = ["3.1", "3.2"]
    aws_controls = ["[CloudTrail.1]", "[CloudTrail.4]"]

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        raw_multi = resource.get_attr("is_multi_region_trail")
        raw_val = resource.get_attr("enable_log_file_validation")

        res_multi, is_multi_res = context.resolve_attribute(raw_multi)
        res_val, is_val_res = context.resolve_attribute(raw_val)

        if not is_multi_res or not is_val_res:
            return self.make_finding(
                resource,
                Status.UNKNOWN,
                "CloudTrail multi-region or log file validation expressions cannot be resolved statically.",
            )

        multi_true = res_multi is True or str(res_multi).lower() == "true"
        validation_true = res_val is True or str(res_val).lower() == "true"

        issues = []
        if not multi_true:
            issues.append("is_multi_region_trail is false or omitted (must be true)")
        if not validation_true:
            issues.append("enable_log_file_validation is false or omitted (must be true)")

        if issues:
            return self.make_finding(
                resource,
                Status.FAIL,
                f"CloudTrail trail misconfigured: {'; '.join(issues)}.",
            )

        return self.make_finding(
            resource,
            Status.PASS,
            "CloudTrail trail is configured across all regions with log file validation active.",
        )
