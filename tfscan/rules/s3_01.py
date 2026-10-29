"""
Rule S3-01: S3 bucket has no public access block with all four settings true.
Supports both AWS provider v3 (inline if present) and v4+ (separate aws_s3_bucket_public_access_block).
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class S301PublicAccessBlock(Rule):
    id = "S3-01"
    title = "S3 bucket has no public access block with all four settings true"
    severity = Severity.HIGH
    resource_types = ["aws_s3_bucket"]
    cis_controls = ["2.1.4", "2.1.5"]
    aws_controls = ["[S3.1]"]

    FOUR_SETTINGS = [
        "block_public_acls",
        "block_public_policy",
        "ignore_public_acls",
        "restrict_public_buckets",
    ]

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        linked_blocks = context.find_linked_s3_resources(resource).get(
            "aws_s3_bucket_public_access_block", []
        )

        pab_source = None
        if linked_blocks:
            pab_source = linked_blocks[0]
        else:
            # Check for inline block (legacy or nested)
            inline_pab = resource.get_attr("public_access_block")
            if inline_pab and isinstance(inline_pab, dict):
                pab_source = Resource(
                    file_path=resource.file_path,
                    line_number=resource.line_number,
                    resource_type="inline_pab",
                    resource_name="inline",
                    address=f"{resource.address}.public_access_block",
                    attributes=inline_pab,
                )

        if not pab_source:
            return self.make_finding(
                resource,
                Status.FAIL,
                "S3 bucket lacks an associated aws_s3_bucket_public_access_block configuration.",
            )

        for setting in self.FOUR_SETTINGS:
            raw_val = pab_source.get_attr(setting)
            if raw_val is None:
                return self.make_finding(
                    resource,
                    Status.FAIL,
                    f"Public access block setting '{setting}' is omitted (must be true).",
                    line_number=pab_source.line_number,
                )

            resolved_val, is_resolved = context.resolve_attribute(raw_val)
            if not is_resolved:
                return self.make_finding(
                    resource,
                    Status.UNKNOWN,
                    f"Public access block setting '{setting}' contains an unresolvable expression.",
                    line_number=pab_source.line_number,
                )

            if resolved_val is not True and str(resolved_val).lower() != "true":
                return self.make_finding(
                    resource,
                    Status.FAIL,
                    f"Public access block setting '{setting}' is set to '{resolved_val}' instead of true.",
                    line_number=pab_source.line_number,
                )

        return self.make_finding(
            resource,
            Status.PASS,
            "S3 bucket is guarded by public access block with all four protection settings enabled.",
            line_number=pab_source.line_number,
        )
