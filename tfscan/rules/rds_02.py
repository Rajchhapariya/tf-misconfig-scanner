"""
Rule RDS-02: RDS instance has storage_encrypted false or missing.
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class RDS02StorageEncrypted(Rule):
    id = "RDS-02"
    title = "RDS instance has storage_encrypted false or missing"
    severity = Severity.HIGH
    resource_types = ["aws_db_instance"]
    cis_controls = ["2.3.1"]
    aws_controls = ["[RDS.3]"]

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        raw_val = resource.get_attr("storage_encrypted")

        if raw_val is None:
            return self.make_finding(
                resource,
                Status.FAIL,
                "RDS instance storage_encrypted argument is missing or omitted (defaults to unencrypted).",
            )

        resolved_val, is_resolved = context.resolve_attribute(raw_val)
        if not is_resolved:
            return self.make_finding(
                resource,
                Status.UNKNOWN,
                "RDS instance storage_encrypted expression cannot be resolved statically.",
            )

        if resolved_val is True or str(resolved_val).lower() == "true":
            return self.make_finding(
                resource,
                Status.PASS,
                "RDS instance has storage encryption enabled.",
            )

        return self.make_finding(
            resource,
            Status.FAIL,
            f"RDS instance storage_encrypted is set to '{resolved_val}' instead of true.",
        )
