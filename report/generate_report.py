"""Build report/report.typ and report.pdf. Every number comes from results/summary_scores.json
and results/disagreement_report.csv; prose contains no hand-typed results."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = json.loads((ROOT / "results" / "summary_scores.json").read_text(encoding="utf-8"))
titles = {r["rule_id"]: r["rule_title"] for r in csv.DictReader(open(ROOT / "docs" / "checkov_mapping.csv", encoding="utf-8"))}
dis = list(csv.DictReader(open(ROOT / "results" / "disagreement_report.csv", encoding="utf-8")))


def pct(v):
    return "n/a" if v is None else f"{v*100:.1f}%"


def f1(v):
    return "n/a" if v is None else f"{v:.3f}"


def esc(t):
    return t.replace("#", "\\#").replace("$", "\\$").replace("*", "\\*").replace("_", "\\_").replace("<", "\\<").replace("@", "\\@")


A, H = S["aggregate"], S["aggregate_headline"]
D = S["dataset_aggregates"]
P = S["performance"]
ex = ", ".join(S["headline_excludes"])


def cell(x):
    return f"[{esc(str(x))}]"


rows = []
for rid in sorted(S["per_rule_scores"]):
    t, c = S["per_rule_scores"][rid]["tfscan"], S["per_rule_scores"][rid]["checkov"]
    rows.append([rid, t["scored"], pct(t["precision"]), pct(t["recall"]), f1(t["f1"]), pct(t["unknown_rate"]),
                 pct(c["precision"]), pct(c["recall"]), f1(c["f1"]), c["no_result"]])
for label, a in (("All 12", A), (f"All but {ex}", H), ("Fixtures", D["fixtures"]), ("TerraGoat", D["terragoat"])):
    t, c = a["tfscan"], a["checkov"]
    rows.append([label, t["scored"], pct(t["precision"]), pct(t["recall"]), f1(t["f1"]), pct(t["unknown_rate"]),
                 pct(c["precision"]), pct(c["recall"]), f1(c["f1"]), c["no_result"]])
tbl = "\n".join("  " + ", ".join(cell(x) for x in r) + "," for r in rows)

dtbl = "\n".join(
    "  " + ", ".join(cell(x) for x in [r["dataset"][:2] + ": " + r["file"].split("/")[-1] + (" " + r["resource_address"] if r["resource_address"] else ""),
                                       r["rule_id"], r["expected"], r["tfscan"], r["checkov"], r["who_was_right"]]) + ","
    for r in dis
)
n_tf_right = sum(r["who_was_right"] == "tfscan" for r in dis)
n_ck_right = sum(r["who_was_right"] == "checkov" for r in dis)
n_unk = sum(r["who_was_right"].startswith("n/a") for r in dis)
fx, tg = P["fixtures"], P["terragoat"]
tf_t, ck_t = A["tfscan"], A["checkov"]
tgs = D["terragoat"]["tfscan"]["scored"]

typ = f'''#set page(paper: "a4", margin: (x: 1.8cm, y: 1.6cm), numbering: "1")
#set text(size: 9.5pt, font: ("Calibri", "Liberation Sans", "DejaVu Sans"))
#set par(justify: true)
#show heading: set block(above: 1em, below: 0.5em)

= tfscan: a Terraform misconfiguration scanner compared with Checkov

Raj Chhapariya. All figures below are generated from saved scan results by `eval/` and `report/generate_report.py`.

== 1. Question and method

Can a small static scanner for 12 AWS rules, which returns UNKNOWN instead of guessing when a value cannot be resolved, match Checkov on a hand-labelled set? Ground-truth labels were established by manual code review prior to running either scanner to eliminate label contamination from scanner outputs. The sets are {fx["resources"]} fixture resources written for this project, and {tgs} scored items on TerraGoat (AWS folder, pinned commit). Each fixture is scanned in its own directory, so one fixture cannot affect another. Results are keyed by full path and resource address. A mapped Checkov check that did not run on an item is counted as a miss, not as a pass.

== 2. Caveats

- The fixtures were written together with the scanner. High scores on them are weak evidence. TerraGoat is the independent set and is small ({tgs} scored items).
- TerraGoat was built by Bridgecrew, the company behind Checkov.
- On S3-03 the tools answer different questions: Checkov CKV\\_AWS\\_19 passes a bucket with no encryption block, tfscan fails it as "no explicit choice in code". The headline row leaves S3-03 out.
- SEC-01 maps only to CKV\\_AWS\\_41 (provider blocks). Checkov's separate secrets scanner was not run, which lowers Checkov's SEC-01 recall.
- Each timing is a single run.

== 3. Results

#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
    align: center, stroke: 0.4pt + luma(180), inset: 3pt,
    [Rule], [Items], [tfscan P], [tfscan R], [tfscan F1], [tfscan UNKNOWN], [Checkov P], [Checkov R], [Checkov F1], [Checkov no result],
{tbl}
  ),
  caption: [Precision, recall, F1 against hand labels. UNKNOWN-labelled items are excluded from P and R.],
)

#figure(image("../results/figures/f1_comparison.png", width: 90%), caption: [F1 per rule. ALL\\* excludes {ex}.])

On the items with a definite label, tfscan scored precision {pct(tf_t["precision"])} and recall {pct(tf_t["recall"])}; Checkov scored {pct(ck_t["precision"])} and {pct(ck_t["recall"])} (all 12 rules). Without {ex}, Checkov recall is {pct(H["checkov"]["recall"])}. On TerraGoat alone tfscan scored {pct(D["terragoat"]["tfscan"]["recall"])} recall and Checkov {pct(D["terragoat"]["checkov"]["recall"])}. Of {ck_t["unknowable_items"]} items labelled unknowable, tfscan answered UNKNOWN on {tf_t["correct_unknown"]}; Checkov gave a definite FAIL or PASS on {ck_t["overconfident"]}.

Timing (wall clock, includes process start-up): fixtures, tfscan CLI {fx["tfscan_cli_wall_ms"]:.0f} ms against Checkov {fx["checkov_wall_ms"]:.0f} ms; TerraGoat AWS, {tg["tfscan_cli_wall_ms"]:.0f} ms against {tg["checkov_wall_ms"]:.0f} ms. Much of the gap is start-up cost, so it should not be read as a per-resource speed ratio.

== 4. Disagreements

{len(dis)} labelled items got different verdicts. tfscan matched the label on {n_tf_right}, Checkov on {n_ck_right}, and {n_unk} were unknowable items. Per-item notes are in `docs/disagreement_notes.csv` and the README.

#figure(
  table(
    columns: (3fr, auto, auto, auto, auto, auto),
    align: (left, center, center, center, center, center), stroke: 0.4pt + luma(180), inset: 3pt,
    [Item], [Rule], [Label], [tfscan], [Checkov], [Right],
{dtbl}
  ),
  caption: [All disagreements. "Right" is blank-equivalent n/a for unknowable items.],
)

== 5. Limits and what was fixed along the way

Evaluation exposed two scanner weaknesses, both found by checking disagreements against the code. The security-group rules asked for the CIDR before the port, so a rule on port 3306 with an unresolvable CIDR came back UNKNOWN; the port is now checked first. S3-03 returns UNKNOWN when an explicit encryption block has a KMS key given as a reference, which the labels treat as a pass; this is not fixed and is the one TerraGoat item where tfscan answered UNKNOWN against a PASS label. Static analysis of `.tf` files cannot see values set outside the code, which is why UNKNOWN exists.

== 6. Reproduce

`pip install -e .[dev]`, `bash scripts/fetch_terragoat.sh`, `python eval/run_scans.py`, `python -m eval.score`, `python -m eval.disagreements`, `python -m eval.plot_figure`, `python -m eval.generate_artifacts`, `python report/generate_report.py`. Environment: `results/ENVIRONMENT.md`.
'''
(ROOT / "report" / "report.typ").write_text(typ, encoding="utf-8")
import subprocess
subprocess.run(["typst", "compile", str(ROOT / "report" / "report.typ"), str(ROOT / "report" / "report.pdf"), "--root", str(ROOT)], check=True)
print("report built")
