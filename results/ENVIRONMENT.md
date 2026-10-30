# Test and Execution Environment

This document records the exact runtime environment and dependency versions used for scanner execution, evaluation benchmarks, and Checkov comparisons.

| Component | Specification / Version |
|---|---|
| Operating System | Microsoft Windows 11 (Windows-10-10.0.26300-SP0 AMD64) |
| Architecture | x86_64 / AMD64 |
| Python Runtime | Python 3.11.9 (tags/v3.11.9:de54cf5, MSC v.1938 64 bit) |
| Checkov Version | 3.4.0 |
| Terraform Version | Terraform v1.9.8 (windows_amd64) |
| python-hcl2 Version | 8.1.4 (Lark parser backend) |
| Typst Version | typst 0.15.1 (9dfd3a08) |

## Execution Protocol

All benchmarks and scans documented in this repository were executed natively in this Windows environment under deterministic conditions:
- Tool execution was isolated to local static file analysis without remote cloud credential dependencies.
- Static scans parse HCL definitions directly into AST structures using `python-hcl2`.
- Variable interpolation resolves deterministic values from `default` attributes and `.tfvars` definitions; dynamic expressions and unresolved references evaluate strictly to `UNKNOWN`.

## Historical Runs Note

An interim regeneration was conducted on Linux 6.8.0-138-generic (Python 3.10.12, Checkov 3.4.0) during intermediate validation without Terraform installed. All official benchmark metrics, timings, and tables recorded in the README and report have been generated natively on the Windows 11 execution environment specified above.
