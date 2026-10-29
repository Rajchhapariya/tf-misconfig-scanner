# Test and Execution Environment

This document records the exact runtime environment and dependency versions used for scanner execution, evaluation benchmarks, and Checkov comparisons.

| Component | Specification / Version |
|---|---|
| Operating System | Microsoft Windows 11 (Windows-10-10.0.26300-SP0 AMD64) |
| Architecture | x86_64 / AMD64 |
| Python Runtime | Python 3.11.9 (tags/v3.11.9:de54cf5, MSC v.1938 64 bit) |
| Checkov Version | 3.4.0 |
| Terraform Binary | Terraform v1.9.8 (windows_amd64) |
| Core Parser | python-hcl2 v8.1.4 (Lark parser backend) |
| Typst Engine | typst 0.14+ |

## Execution Protocol

All benchmarks and scans documented in this repository were executed in this environment under deterministic conditions:
- Tool execution was isolated to local static file analysis without remote cloud credential dependencies.
- Static scans parse HCL definitions directly into AST structures using `python-hcl2`.
- Variable interpolation resolves deterministic values from `default` attributes and `.tfvars` definitions; dynamic expressions and unresolved references evaluate strictly to `UNKNOWN`.
