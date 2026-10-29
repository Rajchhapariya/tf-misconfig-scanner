"""
Rule S3-03: S3 bucket has no explicit server-side encryption configuration.
Severity: LOW.
AWS applies SSE-S3 encryption to all new buckets by default since January 2023.
This rule enforces an explicit encryption configuration choice in code (e.g. KMS CMK or AES256).
Supports both AWS provider v3 (inline block) and v4+ (separate resource).
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class S303ExplicitEncryption(Rule):
    id = "S3-03"
    title = "S3 bucket has no explicit server-side encryption configuration"
    severity = Severity.LOW
    resource_types = ["aws_s3_bucket"]
    cis_controls = ["2.1.1"]
    aws_controls = ["[S3.4]"]

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        linked_sses = context.find_linked_s3_resources(resource).get(
            "aws_s3_bucket_server_side_encryption_configuration", []
        )

        sse_source = None
        raw_rule = None

        if linked_sses:
            sse_source = linked_sses[0]
            raw_rule = sse_source.get_attr("rule")
        else:
            inline_sse = resource.get_attr("server_side_encryption_configuration")
            if inline_sse:
                sse_source = resource
                if isinstance(inline_sse, dict):
                    raw_rule = inline_sse.get("rule")
                elif isinstance(inline_sse, list) and inline_sse:
                    raw_rule = inline_sse[0].get("rule") if isinstance(inline_sse[0], dict) else inline_sse[0]

        if not sse_source or raw_rule is None:
            return self.make_finding(
                resource,
                Status.FAIL,
                "S3 bucket lacks an explicit server-side encryption configuration in code "
                "(AWS enforces SSE-S3 by default since Jan 2023; explicit IaC declaration enforces cryptographic standards).",
            )

        # Inspect encryption rule details
        if isinstance(raw_rule, list) and raw_rule:
            raw_rule = raw_rule[0]

        if isinstance(raw_rule, dict):
            default_enc = raw_rule.get("apply_server_side_encryption_by_default")
            if isinstance(default_enc, list) and default_enc:
                default_enc = default_enc[0]
            if isinstance(default_enc, dict):
                sse_algo = default_enc.get("sse_algorithm")
                resolved_algo, is_resolved = context.resolve_attribute(sse_algo)
                if not is_resolved:
                    return self.make_finding(
                        resource,
                        Status.UNKNOWN,
                        "Server-side encryption algorithm expression cannot be resolved statically.",
                        line_number=sse_source.line_number,
                    )

                # The rule asks whether an explicit encryption choice exists in code. Which KMS
                # key is used (a module output, a data source) does not change that answer, so an
                # unresolved kms_master_key_id is not UNKNOWN here. Only an unresolved
                # sse_algorithm is, because that is the choice itself.

                if resolved_algo in ["aws:kms", "AES256"]:
                    return self.make_finding(
                        resource,
                        Status.PASS,
                        f"S3 bucket has explicit server-side encryption declared ({resolved_algo}).",
                        line_number=sse_source.line_number,
                    )

        # Fallback if rule block is present and non-empty
        return self.make_finding(
            resource,
            Status.PASS,
            "S3 bucket has an explicit server-side encryption configuration declared in code.",
            line_number=sse_source.line_number,
        )
