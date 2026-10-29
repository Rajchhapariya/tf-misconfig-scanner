# Security Control Sources & Mapping Reference

This document records the official compliance benchmarks, standards documents, and regulatory versions used to map the 12 AWS security rules implemented in `tf-misconfig-scanner`.

In accordance with project governance standards, all control identifiers are extracted directly from official vendor documentation. Where no specific control identifier exists in an official standard for a given rule pattern (such as static string heuristics for secrets), the field is intentionally left blank.

---

## 1. Reference Standards and Document Versions

1. **CIS Amazon Web Services Foundations Benchmark**
   - **Version:** v3.0.0 and v1.4.0 (publication dates not confirmed from the sources used)
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

Looked up on 30 October 2026 in the AWS Security Hub user guide pages "CIS AWS Foundations Benchmark" (requirement to control tables for v1.4.0 and v3.0.0) and "AWS Foundational Security Best Practices standard", plus the requirement titles in Prowler's `cis_3.0_aws.json`. The CIS Benchmark PDF itself was not read (it needs a CIS account), so a CIS number is recorded only when one of these sources ties it to the same check. Security Hub IDs are AWS control IDs.

| Rule ID | Resource Types | CIS AWS v1.4.0 | CIS AWS v3.0.0 | Security Hub control | Checkov Check ID |
|---|---|---|---|---|---|
| S3-01 | `aws_s3_bucket`, `aws_s3_bucket_public_access_block` | 2.1.5 | 2.1.4 | S3.1 | CKV2_AWS_6 |
| S3-02 | `aws_s3_bucket`, `aws_s3_bucket_acl` |  |  | S3.2, S3.3 | CKV_AWS_20, CKV_AWS_57 |
| S3-03 | `aws_s3_bucket`, `aws_s3_bucket_server_side_encryption_configuration` |  |  |  | CKV_AWS_19 |
| SG-01 | `aws_security_group`, `aws_security_group_rule` |  | 5.2, 5.3 | EC2.53, EC2.54 | CKV_AWS_24 |
| SG-02 | `aws_security_group`, `aws_security_group_rule` |  | 5.2, 5.3 | EC2.53, EC2.54 | CKV_AWS_25 |
| RDS-01 | `aws_db_instance` |  | 2.3.3 | RDS.2 | CKV_AWS_17 |
| RDS-02 | `aws_db_instance` | 2.3.1 | 2.3.1 | RDS.3 | CKV_AWS_16 |
| EBS-01 | `aws_ebs_volume` |  |  | EC2.3 | CKV_AWS_3 |
| CT-01 | `aws_cloudtrail` | 3.1, 3.2 | 3.1, 3.2 | CloudTrail.1, CloudTrail.4 | CKV_AWS_67, CKV_AWS_36 |
| IAM-01 | `aws_iam_policy`, `aws_iam_role_policy`, `aws_iam_user_policy`, `aws_iam_group_policy` | 1.16 | 1.16 | IAM.1 | CKV_AWS_62 |
| KMS-01 | `aws_kms_key` | 3.8 | 3.6 | KMS.4 | CKV_AWS_7 |
| SEC-01 | `provider.aws`, resource arguments |  |  |  | CKV_AWS_41 |

Blank cells mean no clear match was found in the sources above. The earlier version of this table had wrong CIS numbers; corrections made on 30 October 2026:
- S3-03: CIS v3.0.0 2.1.1 is "S3 bucket policy denies HTTP requests", not encryption. No encryption control was confirmed on the FSBP page, so the field stays blank.
- EBS-01: CIS v3.0.0 2.2.1 (Security Hub EC2.7) is the account-level EBS default encryption setting, not the `encrypted` argument on a volume, so it is not recorded. EC2.3 ("Attached EBS volumes should be encrypted at-rest") is the closest match.
- RDS-01: CIS v3.0.0 2.3.3 is RDS public access. It has no row in the Security Hub v1.4.0 table.
- RDS-02: 2.3.1 is RDS encryption at rest in both versions. The earlier value 2.3.2 is automatic minor version upgrade.
- KMS-01: key rotation is 3.6 in v3.0.0 and 3.8 in v1.4.0. The earlier value 2.4.1 is the EFS encryption item.
- SG-01 and SG-02: v3.0.0 5.2 (IPv4) and 5.3 (IPv6) each cover remote administration ports, so both rules map to both. The Security Hub v1.4.0 table has a gap at 5.2, so no v1.4.0 value is recorded. EC2.13 and EC2.14 were not found on the FSBP page and are dropped; EC2.53 and EC2.54 are the documented controls.
- S3-02: the CIS items for public access (2.1.4 and 2.1.5) are about the public access block setting, not ACL values, so no CIS number is recorded.
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
