"""
Generates results tables, updates README between markers, and prepares report data.
Strictly follows Ground Rule 1: Every number in the README and report is produced by script from saved results.
"""
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCORES_PATH = PROJECT_ROOT / "results" / "summary_scores.json"
DISAGREEMENT_CSV = PROJECT_ROOT / "results" / "disagreement_report.csv"
MAPPING_CSV = PROJECT_ROOT / "docs" / "checkov_mapping.csv"
README_PATH = PROJECT_ROOT / "README.md"
SUMMARY_TABLE_MD = PROJECT_ROOT / "results" / "summary_table.md"


def format_pct(val: float) -> str:
    return f"{val * 100:.1f}%"


def pct(v):
    return "n/a" if v is None else f"{v * 100:.1f}%"


def f1s(v):
    return "n/a" if v is None else f"{v:.3f}"


def _row(label, t, c):
    return (f"| {label} | {t['scored']} | {pct(t['precision'])} | {pct(t['recall'])} | {f1s(t['f1'])} | {pct(t['unknown_rate'])} "
            f"| {pct(c['precision'])} | {pct(c['recall'])} | {f1s(c['f1'])} | {c['no_result']} |")


def generate_tables():
    scores = json.loads(SCORES_PATH.read_text(encoding="utf-8"))
    titles = {}
    with open(MAPPING_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            titles[row["rule_id"]] = row["rule_title"]
    per_rule, agg, head = scores["per_rule_scores"], scores["aggregate"], scores["aggregate_headline"]
    perf, ds = scores["performance"], scores["dataset_aggregates"]

    hdr = ("| Rule | Scored items | tfscan P | tfscan R | tfscan F1 | tfscan UNKNOWN rate | Checkov P | Checkov R | Checkov F1 | Checkov items with no mapped check |\n"
           "|---|---|---|---|---|---|---|---|---|---|")
    lines = [hdr]
    for rid in sorted(per_rule):
        lines.append(_row(f"{rid}: {titles.get(rid, rid)}", per_rule[rid]["tfscan"], per_rule[rid]["checkov"]))
    lines.append(_row("All 12 rules", agg["tfscan"], agg["checkov"]))
    ex = ", ".join(scores["headline_excludes"])
    lines.append(_row(f"All rules except {ex}", head["tfscan"], head["checkov"]))
    for name in ("fixtures", "terragoat"):
        lines.append(_row(f"{name} only (all 12 rules)", ds[name]["tfscan"], ds[name]["checkov"]))
    comparison = "\n".join(lines)

    pl = ["| Dataset | Resources | tfscan engine | tfscan CLI wall | Checkov wall | tfscan CLI ms/100 res | Checkov ms/100 res | Wall-time ratio |",
          "|---|---|---|---|---|---|---|---|"]
    for name, label in (("fixtures", "Fixtures (one directory per fixture for tfscan)"), ("terragoat", "TerraGoat AWS")):
        p = perf[name]
        pl.append(f"| {label} | {p['resources']} | {p['tfscan_engine_ms']:.0f} ms | {p['tfscan_cli_wall_ms']:.0f} ms | {p['checkov_wall_ms']:.0f} ms | {p['tfscan_cli_ms_per_100']:.0f} | {p['checkov_ms_per_100']:.0f} | {p['wall_ratio']}x |")
    perf_table = "\n".join(pl)

    dl = ["| Dataset | File | Resource | Rule | Label | tfscan | Checkov | Right | Note |", "|---|---|---|---|---|---|---|---|---|"]
    with open(DISAGREEMENT_CSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            dl.append(f"| {r['dataset']} | `{r['file']}` | `{r['resource_address']}` | {r['rule_id']} | {r['expected']} | {r['tfscan']} | {r['checkov']} | {r['who_was_right']} | {r['explanation']} |")
    return comparison, perf_table, "\n".join(dl), scores


def update_readme():
    comp_tbl, perf_tbl, dis_tbl, sc = generate_tables()

    # Save summary table standalone
    SUMMARY_TABLE_MD.write_text(comp_tbl + "\n\n" + perf_tbl, encoding="utf-8")

    ag, hd = sc["aggregate"], sc["aggregate_headline"]
    results_section = f"""<!-- RESULTS:START -->
## Measured evaluation and Checkov comparison

Read these caveats first.

- The fixtures were written together with the scanner, so tfscan scoring well on them is expected and is weak evidence. TerraGoat is the independent set, and it has only {sc['dataset_aggregates']['terragoat']['tfscan']['scored']} scored items.
- TerraGoat was built by Bridgecrew, the company behind Checkov, so Checkov is expected to do well on it.
- S3-03 asks for an explicit encryption choice in code. Checkov check CKV_AWS_19 passes buckets with no configuration, so the two tools answer different questions on S3-03. The second aggregate row leaves it out.
- A mapped Checkov check that never ran on an item counts as a miss (FN if the label is FAIL). The last column shows how many items that affects. SEC-01 maps only to the provider check CKV_AWS_41, so Checkov's separate secrets scanner is not part of this comparison.
- UNKNOWN-labelled items are not in precision or recall. tfscan answered UNKNOWN on its UNKNOWN items {sc['aggregate']['tfscan']['correct_unknown']} of {sc['aggregate']['tfscan']['unknowable_items']} times; Checkov has no UNKNOWN state and gave a FAIL or PASS on {sc['aggregate']['checkov']['overconfident']} of them.
- Wall times include process start-up; Checkov's start-up is a large part of its time on small inputs. Single run each, no repetition.

### Precision, recall and F1 per rule

{comp_tbl}

### Scan time

{perf_tbl}

### F1 per rule

![F1 per rule](results/figures/f1_comparison.png)

### Disagreements

Every labelled item where the two tools gave different verdicts. The Note column is the only hand-written part (docs/disagreement_notes.csv).

{dis_tbl}
<!-- RESULTS:END -->"""

    if not README_PATH.exists():
        print("README.md does not exist yet. It will be created with results.")
        return

    content = README_PATH.read_text(encoding="utf-8")
    start_tag = "<!-- RESULTS:START -->"
    end_tag = "<!-- RESULTS:END -->"

    if start_tag in content and end_tag in content:
        before = content.split(start_tag)[0]
        after = content.split(end_tag)[1]
        new_content = before + results_section + after
    else:
        new_content = content + "\n\n" + results_section

    README_PATH.write_text(new_content, encoding="utf-8")
    print("README.md results section successfully generated from script output.")


if __name__ == "__main__":
    update_readme()
