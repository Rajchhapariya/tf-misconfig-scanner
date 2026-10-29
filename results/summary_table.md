| Rule | Scored items | tfscan P | tfscan R | tfscan F1 | tfscan UNKNOWN rate | Checkov P | Checkov R | Checkov F1 | Checkov items with no mapped check |
|---|---|---|---|---|---|---|---|---|---|
| CT-01: CloudTrail trail is not multi-region or log file validation is off | 6 | 100.0% | 100.0% | 1.000 | 25.0% | 100.0% | 100.0% | 1.000 | 0 |
| EBS-01: EBS volume has encrypted false or missing | 7 | 100.0% | 100.0% | 1.000 | 22.2% | 100.0% | 100.0% | 1.000 | 2 |
| IAM-01: IAM policy document allows Action: "*" on Resource: "*" | 8 | 100.0% | 100.0% | 1.000 | 20.0% | 100.0% | 100.0% | 1.000 | 0 |
| KMS-01: KMS key has enable_key_rotation false or missing | 7 | 100.0% | 100.0% | 1.000 | 22.2% | 100.0% | 100.0% | 1.000 | 2 |
| RDS-01: RDS instance has publicly_accessible = true | 7 | 100.0% | 100.0% | 1.000 | 22.2% | 100.0% | 100.0% | 1.000 | 2 |
| RDS-02: RDS instance has storage_encrypted false or missing | 7 | 100.0% | 100.0% | 1.000 | 22.2% | 100.0% | 100.0% | 1.000 | 2 |
| S3-01: S3 bucket has no public access block with all four settings true | 12 | 100.0% | 100.0% | 1.000 | 14.3% | 90.0% | 100.0% | 0.947 | 2 |
| S3-02: S3 bucket ACL is public-read or public-read-write | 12 | 100.0% | 100.0% | 1.000 | 14.3% | 100.0% | 100.0% | 1.000 | 2 |
| S3-03: S3 bucket has no explicit server-side encryption configuration | 13 | 100.0% | 100.0% | 1.000 | 13.3% | n/a | 0.0% | n/a | 2 |
| SEC-01: Hard-coded secret-like literals in provider or resource arguments | 9 | 100.0% | 100.0% | 1.000 | 18.2% | 100.0% | 40.0% | 0.571 | 6 |
| SG-01: Security group allows ingress from 0.0.0.0/0 or ::/0 on port 22 | 9 | 100.0% | 100.0% | 1.000 | 18.2% | 100.0% | 100.0% | 1.000 | 0 |
| SG-02: Security group allows ingress from 0.0.0.0/0 or ::/0 on port 3389 | 9 | 100.0% | 100.0% | 1.000 | 18.2% | 100.0% | 100.0% | 1.000 | 0 |
| All 12 rules | 106 | 100.0% | 100.0% | 1.000 | 18.5% | 97.7% | 79.6% | 0.878 | 20 |
| All rules except S3-03 | 93 | 100.0% | 100.0% | 1.000 | 19.1% | 97.7% | 93.5% | 0.956 | 18 |
| fixtures only (all 12 rules) | 73 | 100.0% | 100.0% | 1.000 | 24.7% | 96.9% | 86.1% | 0.912 | 19 |
| terragoat only (all 12 rules) | 33 | 100.0% | 100.0% | 1.000 | 0.0% | 100.0% | 66.7% | 0.800 | 1 |

| Dataset | Resources | tfscan engine | tfscan CLI wall | Checkov wall | tfscan CLI ms/100 res | Checkov ms/100 res | Wall-time ratio |
|---|---|---|---|---|---|---|---|
| Fixtures (one directory per fixture for tfscan) | 102 | 99 ms | 168 ms | 5035 ms | 165 | 4936 | 29.9x |
| TerraGoat AWS | 17 | 77 ms | 182 ms | 2221 ms | 1068 | 13064 | 12.2x |