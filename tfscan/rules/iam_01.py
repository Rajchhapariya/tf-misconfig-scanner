"""
Rule IAM-01: IAM policy document allows Action: "*" on Resource: "*".
Evaluates aws_iam_policy, aws_iam_role_policy, aws_iam_user_policy, aws_iam_group_policy.
"""
import json
from typing import Any, List

from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class IAM01WildcardAdmin(Rule):
    id = "IAM-01"
    title = 'IAM policy document allows Action: "*" on Resource: "*"'
    severity = Severity.CRITICAL
    resource_types = [
        "aws_iam_policy",
        "aws_iam_role_policy",
        "aws_iam_user_policy",
        "aws_iam_group_policy",
    ]
    cis_controls = ["1.16"]
    aws_controls = ["[IAM.1]"]

    def _is_wildcard(self, val: Any) -> bool:
        if val == "*":
            return True
        if isinstance(val, list) and len(val) == 1 and val[0] == "*":
            return True
        return False

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        raw_policy = resource.get_attr("policy")
        if raw_policy is None:
            return self.make_finding(
                resource, Status.PASS, "No policy document attached to IAM resource."
            )

        resolved_policy, is_resolved = context.resolve_attribute(raw_policy)
        if not is_resolved:
            return self.make_finding(
                resource,
                Status.UNKNOWN,
                "IAM policy document expression cannot be resolved statically.",
            )

        policy_obj = None
        if isinstance(resolved_policy, dict):
            policy_obj = resolved_policy
        elif isinstance(resolved_policy, str):
            try:
                policy_obj = json.loads(resolved_policy)
            except Exception:
                # Might contain syntax or dynamic placeholders
                return self.make_finding(
                    resource,
                    Status.UNKNOWN,
                    "IAM policy string could not be parsed as valid JSON.",
                )

        if not isinstance(policy_obj, dict):
            return self.make_finding(
                resource, Status.UNKNOWN, "IAM policy object structure is unrecognized."
            )

        statements = policy_obj.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]

        for stmt in statements:
            if not isinstance(stmt, dict):
                continue
            effect = stmt.get("Effect")
            if str(effect).lower() != "allow":
                continue

            action = stmt.get("Action")
            resource_val = stmt.get("Resource")

            if self._is_wildcard(action) and self._is_wildcard(resource_val):
                return self.make_finding(
                    resource,
                    Status.FAIL,
                    "IAM policy statement allows full unrestricted administrative access ('Action': '*' on 'Resource': '*').",
                )

        return self.make_finding(
            resource,
            Status.PASS,
            "IAM policy does not allow full wildcard administrative permissions ('*' on '*').",
        )
