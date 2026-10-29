"""
Pre-scan ground-truth labeling for TerraGoat AWS resources.
Written and verified by code inspection BEFORE running any security scanning tool.
"""
import csv
from pathlib import Path

LABELS = [
    # S3-01: S3 bucket has no public access block with all four settings true
    ("s3.tf", "aws_s3_bucket.data", "S3-01", "FAIL", "No public access block resource or inline configuration defined"),
    ("s3.tf", "aws_s3_bucket.financials", "S3-01", "FAIL", "No public access block resource or inline configuration defined"),
    ("s3.tf", "aws_s3_bucket.operations", "S3-01", "FAIL", "No public access block resource or inline configuration defined"),
    ("s3.tf", "aws_s3_bucket.data_science", "S3-01", "FAIL", "No public access block resource or inline configuration defined"),
    ("s3.tf", "aws_s3_bucket.logs", "S3-01", "FAIL", "No public access block resource or inline configuration defined"),
    ("ec2.tf", "aws_s3_bucket.flowbucket", "S3-01", "FAIL", "No public access block resource or inline configuration defined"),

    # S3-02: S3 bucket ACL is public-read or public-read-write
    ("s3.tf", "aws_s3_bucket.data", "S3-02", "PASS", "No public ACL declared (defaults to private)"),
    ("s3.tf", "aws_s3_bucket.financials", "S3-02", "PASS", "Explicit acl = 'private'"),
    ("s3.tf", "aws_s3_bucket.operations", "S3-02", "PASS", "Explicit acl = 'private'"),
    ("s3.tf", "aws_s3_bucket.data_science", "S3-02", "PASS", "Explicit acl = 'private'"),
    ("s3.tf", "aws_s3_bucket.logs", "S3-02", "PASS", "Explicit acl = 'log-delivery-write' (not public)"),
    ("ec2.tf", "aws_s3_bucket.flowbucket", "S3-02", "PASS", "No public ACL declared"),

    # S3-03: S3 bucket has no explicit server-side encryption configuration
    ("s3.tf", "aws_s3_bucket.data", "S3-03", "FAIL", "No server_side_encryption_configuration block present"),
    ("s3.tf", "aws_s3_bucket.financials", "S3-03", "FAIL", "No server_side_encryption_configuration block present"),
    ("s3.tf", "aws_s3_bucket.operations", "S3-03", "FAIL", "No server_side_encryption_configuration block present"),
    ("s3.tf", "aws_s3_bucket.data_science", "S3-03", "FAIL", "No server_side_encryption_configuration block present"),
    ("s3.tf", "aws_s3_bucket.logs", "S3-03", "PASS", "Explicit server_side_encryption_configuration with aws:kms"),
    ("ec2.tf", "aws_s3_bucket.flowbucket", "S3-03", "FAIL", "No server_side_encryption_configuration block present"),

    # SG-01: Security group allows ingress from 0.0.0.0/0 or ::/0 on port 22
    ("db-app.tf", "aws_security_group.default", "SG-01", "PASS", "No ingress rule allowing port 22 from 0.0.0.0/0"),
    ("db-app.tf", "aws_security_group_rule.ingress", "SG-01", "PASS", "Rule restricts to port 3306 from VPC CIDR, not port 22"),
    ("ec2.tf", "aws_security_group.web-node", "SG-01", "FAIL", "Inline ingress block allows 0.0.0.0/0 on port 22"),

    # SG-02: Security group allows ingress from 0.0.0.0/0 or ::/0 on port 3389
    ("db-app.tf", "aws_security_group.default", "SG-02", "PASS", "No ingress rule allowing port 3389 from 0.0.0.0/0"),
    ("db-app.tf", "aws_security_group_rule.ingress", "SG-02", "PASS", "Rule restricts to port 3306 from VPC CIDR, not port 3389"),
    ("ec2.tf", "aws_security_group.web-node", "SG-02", "PASS", "Ingress rules allow port 80 and 22, but port 3389 is not allowed"),

    # RDS-01: RDS instance has publicly_accessible = true
    ("db-app.tf", "aws_db_instance.default", "RDS-01", "FAIL", "Explicitly configured with publicly_accessible = true"),

    # RDS-02: RDS instance has storage_encrypted false or missing
    ("db-app.tf", "aws_db_instance.default", "RDS-02", "FAIL", "Explicitly configured with storage_encrypted = false"),

    # EBS-01: EBS volume has encrypted false or missing
    ("ec2.tf", "aws_ebs_volume.web_host_storage", "EBS-01", "FAIL", "encrypted argument is commented out and missing"),

    # CT-01: CloudTrail trail is not multi-region or log file validation is off
    # TerraGoat AWS has no aws_cloudtrail resource; recorded for complete coverage
    ("ec2.tf", "aws_flow_log.vpcflowlogs", "CT-01", "N/A", "VPC flow log is not an aws_cloudtrail resource"),

    # IAM-01: IAM policy document allows Action: "*" on Resource: "*"
    ("db-app.tf", "aws_iam_role_policy.ec2policy", "IAM-01", "PASS", "Actions are scoped to ['s3:*', 'ec2:*', 'rds:*'], not full wildcard '*'"),
    ("iam.tf", "aws_iam_user_policy.userpolicy", "IAM-01", "PASS", "Actions are scoped to ['ec2:*', 's3:*', 'lambda:*', 'cloudwatch:*'], not full wildcard '*'"),

    # KMS-01: KMS key has enable_key_rotation false or missing
    ("kms.tf", "aws_kms_key.logs_key", "KMS-01", "FAIL", "enable_key_rotation attribute is omitted (defaults to false)"),

    # SEC-01: Hard-coded secret-like literals in provider or resource arguments
    ("providers.tf", "provider.aws.plain_text_access_keys_provider", "SEC-01", "FAIL", "Hardcoded access_key and secret_key in provider block"),
    ("providers.tf", "provider.aws.default", "SEC-01", "PASS", "No hardcoded credentials; references variables"),
    ("db-app.tf", "aws_db_instance.default", "SEC-01", "FAIL", "Password resolves from variable default value 'Aa1234321Bb'"),
]


def write_labels(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "resource_address", "rule_id", "expected", "note"])
        for row in LABELS:
            writer.writerow(row)
    print(f"Wrote {len(LABELS)} hand-verified labels to {output_path}")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "labels" / "terragoat_labels.csv"
    write_labels(out)
