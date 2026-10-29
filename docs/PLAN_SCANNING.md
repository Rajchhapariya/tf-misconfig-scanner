# Terraform Plan JSON Scanning Specification & Limitations

This document specifies the architecture, execution model, and known operational limitations of scanning Terraform plan JSON output (`terraform show -json <planfile>`), implemented as Stretch Goal 2.

---

## 1. Execution Workflow

When scanning pre-deployment Terraform plans:
1. Generate an execution plan without remote credentials using dummy/LocalStack provider settings:
   ```bash
   terraform plan -out=tfplan.binary
   terraform show -json tfplan.binary > tfplan.json
   ```
2. Execute `tfscan`:
   ```bash
   tfscan scan tfplan.json --plan --format table
   ```

`tfscan` ingests the JSON payload, extracts `planned_values.root_module.resources` (and child modules recursively), maps attributes into normalized `Resource` dataclasses, and evaluates all 12 rules.

---

## 2. Technical Advantages of Plan JSON Scanning

1. **Complete Dynamic Expression Resolution:** Variable values, Terraform interpolation strings, local expressions, and simple calculations are fully evaluated and flattened by the Terraform core engine into explicit literal attributes before `tfscan` executes.
2. **Reduced UNKNOWN Rate:** Because values are resolved by Terraform prior to static evaluation, rules that would return `UNKNOWN` during raw HCL parsing (due to unassigned variables without defaults) resolve to definitive `PASS` or `FAIL` findings.
3. **Module Inlining:** All child module resources are flattened into `planned_values`, enabling cross-module rule evaluation without manual module source traversal.

---

## 3. Engineering Limitations & Trade-Offs

| Dimension | Raw HCL Static Scanning (`tfscan`) | Plan JSON Scanning (`--plan`) |
|---|---|---|
| **Cloud Credential Dependency** | 0% (Pure offline AST parser) | High (Requires `terraform init` and provider plugins) |
| **Execution Latency** | Sub-150 ms across entire repo | 5-30 seconds (Terraform init, provider schema check, state lock) |
| **Shift-Left Boundary** | IDE pre-commit hook (runs instantly on save) | CI/CD pipeline post-plan phase |
| **Scope of Evaluation** | Evaluates 100% of declared `.tf` configurations | Evaluates only planned changes; unmanaged/untargeted code ignored |
| **Data Source Blind Spots** | Flags data source dependencies as `UNKNOWN` | Requires live network access unless mocked via LocalStack |

### Recommendation
Raw HCL static scanning is optimal for fast feedback loops (pre-commit hooks, IDE integration, fast pull request gating). Plan JSON scanning is recommended as an auxiliary defense-in-depth gate in the staging pipeline before `terraform apply`.
