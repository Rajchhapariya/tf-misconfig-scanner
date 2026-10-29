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

## Latest regeneration of the results

The scan results, scores, figure, README results block and report in the current commit were regenerated in this environment. The table above describes the earlier Windows run, which produced the previous commit's results. Wall times differ between environments, so compare timings only within one run.

| Component | Specification / Version |
|---|---|
| Operating System | Linux-6.8.0-138-generic-x86_64-with-glibc2.35 (Linux VM, no GPU) |
| CPU | 13th Gen Intel(R) Core(TM) i7-13620H |
| RAM | 3915 MB |
| Python Runtime | 3.10.12 |
| Checkov Version | 3.4.0 |
| python-hcl2 | 8.1.4 |
| Terraform Binary | not installed in this run (not needed for static scans) |
| Typst | python package typst 0.15.0 |
