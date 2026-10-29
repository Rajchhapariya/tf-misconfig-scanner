"""
Rule KMS-01: KMS key has enable_key_rotation false or missing.
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class KMS01KeyRotation(Rule):
    id = "KMS-01"
    title = "KMS key has enable_key_rotation false or missing"
    severity = Severity.MEDIUM
    resource_types = ["aws_kms_key"]
    cis_controls = ["2.4.1"]
    aws_controls = ["[KMS.4]"]

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        raw_val = resource.get_attr("enable_key_rotation")

        if raw_val is None:
            return self.make_finding(
                resource,
                Status.FAIL,
                "KMS key has enable_key_rotation omitted or missing (defaults to disabled).",
            )

        resolved_val, is_resolved = context.resolve_attribute(raw_val)
        if not is_resolved:
            return self.make_finding(
                resource,
                Status.UNKNOWN,
                "KMS key enable_key_rotation expression cannot be resolved statically.",
            )

        if resolved_val is True or str(resolved_val).lower() == "true":
            return self.make_finding(
                resource,
                Status.PASS,
                "KMS key automatic key rotation is enabled.",
            )

        return self.make_finding(
            resource,
            Status.FAIL,
            f"KMS key enable_key_rotation is configured as '{resolved_val}' instead of true.",
        )
