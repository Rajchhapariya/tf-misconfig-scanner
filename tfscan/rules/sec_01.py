"""
Rule SEC-01: Hard-coded secret-like literals in provider or resource arguments.
Flags plaintext credentials (access_key, secret_key, password) embedded in IaC templates.
Mapped to Checkov CKV_AWS_41. CIS and AWS controls left blank per Ground Rule 3.
"""
import re
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class SEC01HardcodedSecrets(Rule):
    id = "SEC-01"
    title = "Hard-coded secret-like literals in provider or resource arguments"
    severity = Severity.HIGH
    resource_types = ["provider.aws", "aws_db_instance", "aws_mq_broker", "aws_redshift_cluster"]
    cis_controls = []
    aws_controls = []

    SECRET_KEYS = {"access_key", "secret_key", "password"}

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        matched_secrets = []
        has_unknown = False
        unknown_reason = ""

        for key in self.SECRET_KEYS:
            if key not in resource.attributes:
                continue

            raw_val = resource.attributes[key]
            if raw_val is None:
                continue

            resolved_val, is_resolved = context.resolve_attribute(raw_val)
            if not is_resolved:
                has_unknown = True
                unknown_reason = f"Secret argument '{key}' expression cannot be statically resolved."
                continue

            if isinstance(resolved_val, str) and len(resolved_val.strip()) > 0:
                matched_secrets.append(key)

        if matched_secrets:
            return self.make_finding(
                resource,
                Status.FAIL,
                f"Hard-coded secret literal found in argument(s): {', '.join(matched_secrets)}.",
            )

        if has_unknown:
            return self.make_finding(resource, Status.UNKNOWN, unknown_reason)

        return self.make_finding(
            resource,
            Status.PASS,
            "No hard-coded secret literals detected in resource arguments.",
        )
