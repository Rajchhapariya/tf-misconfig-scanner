"""
Rule EBS-01: EBS volume has encrypted false or missing.
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class EBS01Encrypted(Rule):
    id = "EBS-01"
    title = "EBS volume has encrypted false or missing"
    severity = Severity.HIGH
    resource_types = ["aws_ebs_volume"]
    cis_controls = ["2.2.1"]
    aws_controls = ["[EC2.3]"]

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        raw_val = resource.get_attr("encrypted")

        if raw_val is None:
            return self.make_finding(
                resource,
                Status.FAIL,
                "EBS volume encrypted argument is missing or omitted (defaults to unencrypted).",
            )

        resolved_val, is_resolved = context.resolve_attribute(raw_val)
        if not is_resolved:
            return self.make_finding(
                resource,
                Status.UNKNOWN,
                "EBS volume encrypted expression cannot be resolved statically.",
            )

        if resolved_val is True or str(resolved_val).lower() == "true":
            return self.make_finding(
                resource,
                Status.PASS,
                "EBS volume encryption is enabled.",
            )

        return self.make_finding(
            resource,
            Status.FAIL,
            f"EBS volume encrypted argument is set to '{resolved_val}' instead of true.",
        )
