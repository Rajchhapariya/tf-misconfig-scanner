| Rule ID | Rule Title | tfscan Prec | tfscan Rec | tfscan F1 | tfscan Unk Rate | Checkov Prec | Checkov Rec | Checkov F1 |
|---|---|---|---|---|---|---|---|---|
| **CT-01** | CloudTrail trail is not multi-region or log file validation is off | 100.0% | 100.0% | **1.0000** | 25.0% | 100.0% | 100.0% | **1.0000** |
| **EBS-01** | EBS volume has encrypted false or missing | 80.0% | 100.0% | **0.8889** | 22.2% | 100.0% | 100.0% | **1.0000** |
| **IAM-01** | IAM policy document allows Action: "*" on Resource: "*" | 100.0% | 100.0% | **1.0000** | 20.0% | 100.0% | 100.0% | **1.0000** |
| **KMS-01** | KMS key has enable_key_rotation false or missing | 80.0% | 100.0% | **0.8889** | 22.2% | 100.0% | 100.0% | **1.0000** |
| **RDS-01** | RDS instance has publicly_accessible = true | 100.0% | 75.0% | **0.8571** | 11.1% | 100.0% | 100.0% | **1.0000** |
| **RDS-02** | RDS instance has storage_encrypted false or missing | 80.0% | 100.0% | **0.8889** | 22.2% | 80.0% | 100.0% | **0.8889** |
| **S3-01** | S3 bucket has no public access block with all four settings true | 75.0% | 100.0% | **0.8571** | 0.0% | 90.0% | 100.0% | **0.9474** |
| **S3-02** | S3 bucket ACL is public-read or public-read-write | 50.0% | 100.0% | **0.6667** | 0.0% | 100.0% | 100.0% | **1.0000** |
| **S3-03** | S3 bucket has no explicit server-side encryption configuration | 100.0% | 62.5% | **0.7692** | 7.1% | 100.0% | 0.0% | **0.0000** |
| **SEC-01** | Hard-coded secret-like literals in provider or resource arguments | 83.3% | 100.0% | **0.9091** | 18.2% | 66.7% | 40.0% | **0.5000** |
| **SG-01** | Security group allows ingress from 0.0.0.0/0 or ::/0 on port 22 | 100.0% | 100.0% | **1.0000** | 27.3% | 100.0% | 100.0% | **1.0000** |
| **SG-02** | Security group allows ingress from 0.0.0.0/0 or ::/0 on port 3389 | 100.0% | 100.0% | **1.0000** | 27.3% | 100.0% | 100.0% | **1.0000** |
| **OVERALL** | **All 12 Evaluated Rules** | **83.3%** | **92.6%** | **0.8772** | **15.5%** | **93.5%** | **79.6%** | **0.8600** |

| Benchmark Dataset | Target Resources | tfscan Duration | tfscan ms / 100 Res | Checkov Duration | Checkov ms / 100 Res | Throughput Speedup |
|---|---|---|---|---|---|---|
| **Hand-Written Fixtures** | 20 | 103.78 ms | 518.9 ms | 9022.91 ms | 8056.2 ms | **86.9x Faster** |
| **TerraGoat AWS Target** | 17 | 122.69 ms | 721.7 ms | 9774.54 ms | 15272.7 ms | **79.7x Faster** |