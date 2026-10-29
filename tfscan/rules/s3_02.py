"""
Rule S3-02: S3 bucket ACL is public-read or public-read-write.
Supports both AWS provider v3 (inline acl argument) and v4+ (separate aws_s3_bucket_acl resource).
"""
from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class S302PublicAcl(Rule):
    id = "S3-02"
    title = "S3 bucket ACL is public-read or public-read-write"
    severity = Severity.HIGH
    resource_types = ["aws_s3_bucket"]
    cis_controls = []
    aws_controls = ["[S3.2]", "[S3.3]"]

    PUBLIC_ACLS = {"public-read", "public-read-write"}

    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        linked_acls = context.find_linked_s3_resources(resource).get(
            "aws_s3_bucket_acl", []
        )

        acl_source = None
        raw_acl = None

        if linked_acls:
            acl_source = linked_acls[0]
            raw_acl = acl_source.get_attr("acl")
        else:
            raw_acl = resource.get_attr("acl")
            if raw_acl is not None:
                acl_source = resource

        if raw_acl is None:
            # Default S3 bucket ACL without explicit declaration is private
            return self.make_finding(
                resource,
                Status.PASS,
                "S3 bucket does not declare public ACL permissions (defaults to private access).",
            )

        resolved_acl, is_resolved = context.resolve_attribute(raw_acl)
        if not is_resolved:
            return self.make_finding(
                resource,
                Status.UNKNOWN,
                "S3 bucket ACL expression cannot be resolved statically.",
                line_number=acl_source.line_number if acl_source else resource.line_number,
            )

        acl_str = str(resolved_acl).lower().strip()
        if acl_str in self.PUBLIC_ACLS:
            return self.make_finding(
                resource,
                Status.FAIL,
                f"S3 bucket ACL is set to '{acl_str}', allowing public unauthorized access.",
                line_number=acl_source.line_number if acl_source else resource.line_number,
            )

        return self.make_finding(
            resource,
            Status.PASS,
            f"S3 bucket ACL is set to non-public permission '{acl_str}'.",
            line_number=acl_source.line_number if acl_source else resource.line_number,
        )
