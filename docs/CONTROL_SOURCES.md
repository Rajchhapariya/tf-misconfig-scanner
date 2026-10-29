# Security Control Sources & Mapping Reference

This document records the official compliance benchmarks, standards documents, and regulatory versions used to map the 12 AWS security rules implemented in `tf-misconfig-scanner`.

In accordance with project governance standards, all control identifiers are extracted directly from official vendor documentation. Where no specific control identifier exists in an official standard for a given rule pattern (such as static string heuristics for secrets), the field is intentionally left blank.

---

## 1. Reference Standards and Document Versions

1. **CIS Amazon Web Services Foundations Benchmark**
   - **Version:** v3.0.0 (Published May 2023) / v1.4.0 (Published May 2021)
   - **Publisher:** Center for Internet Security (CIS)
   - **Scope:** Consensus-based security configuration baselines for Amazon Web Services accounts and resources.

2. **AWS Foundational Security Best Practices (FSBP) Standard**
   - **Version:** Current (AWS Security Hub CSPM User Guide)
   - **Publisher:** Amazon Web Services (AWS)
   - **Scope:** Automated security checks aligned with AWS security expert recommendations across managed AWS accounts.

3. **Checkov Policy Catalog**
   - **Version:** 3.4.0
   - **Publisher:** Bridgecrew by Palo Alto Networks
   - **Scope:** Static analysis checks for infrastructure as code across Terraform providers.

---

## 2. Rule Control Mapping Matrix

| Rule ID | Rule Title | Resource Types | CIS AWS v1.4.0 | CIS AWS v3.0.0 | AWS FSBP Control ID | Checkov Check ID |
|---|---|---|---|---|---|---|
| S3-01 | S3 bucket has no public access block with all four settings true | `aws_s3_bucket`, `aws_s3_bucket_public_access_block` | 2.1.4, 2.1.5 | 2.1.4, 2.1.5 | [S3.1] | CKV2_AWS_6 |
| S3-02 | S3 bucket ACL is `public-read` or `public-read-write` | `aws_s3_bucket`, `aws_s3_bucket_acl` | 2.1.5 | 2.1.5 | [S3.2], [S3.3] | CKV_AWS_20, CKV_AWS_57 |
| S3-03 | S3 bucket has no explicit server-side encryption configuration | `aws_s3_bucket`, `aws_s3_bucket_server_side_encryption_configuration` | 2.1.1 | 2.1.1 | [S3.4] | CKV_AWS_19 |
| SG-01 | Security group allows ingress from `0.0.0.0/0` or `::/0` on port 22 | `aws_security_group`, `aws_security_group_rule` | 5.2 | 5.2 | [EC2.13] | CKV_AWS_24 |
| SG-02 | Security group allows ingress from `0.0.0.0/0` or `::/0` on port 3389 | `aws_security_group`, `aws_security_group_rule` | 5.3 | 5.3 | [EC2.14] | CKV_AWS_25 |
| RDS-01 | RDS instance has `publicly_accessible = true` | `aws_db_instance` | 2.3.1 | 2.3.1 | [RDS.2] | CKV_AWS_17 |
| RDS-02 | RDS instance has `storage_encrypted` false or missing | `aws_db_instance` | 2.3.2 | 2.3.2 | [RDS.3] | CKV_AWS_16 |
| EBS-01 | EBS volume has `encrypted` false or missing | `aws_ebs_volume` | 2.2.1 | 2.2.1 | [EC2.3] | CKV_AWS_3 |
| CT-01 | CloudTrail trail is not multi-region, or log file validation is off | `aws_cloudtrail` | 3.1, 3.2 | 3.1, 3.2 | [CloudTrail.1], [CloudTrail.4] | CKV_AWS_67, CKV_AWS_36 |
| IAM-01 | IAM policy document allows `Action: "*"` on `Resource: "*"` | `aws_iam_policy`, `aws_iam_policy_document`, `aws_iam_role_policy`, `aws_iam_user_policy`, `aws_iam_group_policy` | 1.16 | 1.16 | [IAM.1] | CKV_AWS_62 |
| KMS-01 | KMS key has `enable_key_rotation` false or missing | `aws_kms_key` | 2.4.1 | 2.4.1 | [KMS.4] | CKV_AWS_7 |
| SEC-01 | Hard-coded secret-like literals in provider or resource arguments | `provider.aws`, all resource configurations |  |  |  | CKV_AWS_41 |

---

## 3. Implementation Specifics & Architectural Notes

### 3.1 AWS Provider v3 vs v4+ Decoupling (S3 Architecture)
From AWS provider v4 onwards, HashiCorp decoupled bucket property configurations into dedicated standalone resources:
- Public Access Block: `aws_s3_bucket_public_access_block`
- ACL: `aws_s3_bucket_acl`
- Encryption: `aws_s3_bucket_server_side_encryption_configuration`

`tf-misconfig-scanner` constructs an in-memory resource relationship graph per scan run. It links satellite configuration blocks back to the parent `aws_s3_bucket` via direct block name references (`aws_s3_bucket.<name>.id` or `aws_s3_bucket.<name>.bucket`) or string literal bucket names. If inline configuration (v3 style) is present, the scanner evaluates the nested configuration block directly.

### 3.2 S3 Default Encryption Context (S3-03)
AWS enforced server-side encryption (SSE-S3) by default for all new S3 buckets starting January 5, 2023. Consequently, rule `S3-03` does not denote an unencrypted bucket at the AWS physical layer; rather, it flags the absence of an explicit encryption declaration (such as KMS customer-managed key configuration or explicit encryption block) in infrastructure-as-code definitions. In production GitOps environments, explicit declarations prevent drift and enforce cryptographic governance. This rule is assigned `LOW` severity.

### 3.3 Rule SEC-01 Control Mapping Rationale
While CIS Benchmark control 1.4 requires removing root user access keys, neither CIS AWS Foundations nor AWS FSBP contains a control identifier dedicated to static AST detection of hardcoded plaintext strings within IaC templates. Following project ground rules, the CIS and AWS FSBP control fields for `SEC-01` are left blank. Checkov provides check `CKV_AWS_41` ("Ensure no hard coded AWS access key and secret key exists in provider"), which serves as the comparative baseline.
