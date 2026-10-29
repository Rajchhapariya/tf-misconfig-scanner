"""
Rule RDS-01: RDS instance has publicly_accessible = true.
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class RDS01PubliclyAccessible(Rule):
    id = "RDS-01"
    title = "RDS instance has publicly_accessible = true"
    severity = Severity.HIGH
    resource_types = ["aws_db_instance"]
    cis_controls = ["2.3.3"]
    aws_controls = ["[RDS.2]"]

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        raw_val = resource.get_attr("publicly_accessible")

        # AWS default for publicly_accessible is false if omitted
        if raw_val is None:
            return self.make_finding(
                resource,
                Status.PASS,
                "RDS instance publicly_accessible attribute is omitted (defaults to false).",
            )

        resolved_val, is_resolved = context.resolve_attribute(raw_val)
        if not is_resolved:
            return self.make_finding(
                resource,
                Status.UNKNOWN,
                "RDS instance publicly_accessible expression cannot be resolved statically.",
            )

        if resolved_val is True or str(resolved_val).lower() == "true":
            return self.make_finding(
                resource,
                Status.FAIL,
                "RDS instance has publicly_accessible configured as true, exposing the database to the internet.",
            )

        return self.make_finding(
            resource,
            Status.PASS,
            "RDS instance publicly_accessible is set to false.",
        )
