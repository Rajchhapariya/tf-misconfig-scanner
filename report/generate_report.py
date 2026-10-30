import csv
import json
from pathlib import Path
import subprocess

ROOT = Path(r"C:\Users\Rajch\Desktop\Research\tf-misconfig-scanner")
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

typ = f'''#set page(
  paper: "a4",
  margin: (top: 1.6cm, bottom: 1.6cm, left: 1.8cm, right: 1.8cm),
  header: context {{
    if counter(page).get().first() > 1 [
      #set text(size: 8pt, fill: rgb("#64748b"), font: "Segoe UI")
      #grid(
        columns: (1fr, 1fr),
        align(left)[*tfscan: Terraform Misconfiguration Scanner* | Technical Evaluation Report],
        align(right)[Benchmark ID: TF-EVAL-2026]
      )
      #line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
    ]
  }},
  footer: context [
    #line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
    #set text(size: 8pt, fill: rgb("#64748b"), font: "Segoe UI")
    #grid(
      columns: (1fr, 1fr),
      align(left)[Empirical Verification | Automated Static Analysis],
      align(right)[Page #counter(page).display("1 of 1", both: true)]
    )
  ]
)

#set text(font: "Segoe UI", size: 9pt, fill: rgb("#0f172a"))
#set par(justify: true, leading: 0.52em)
#show heading: set block(above: 0.9em, below: 0.45em)

#align(center)[
  #block(
    fill: rgb("#0f172a"),
    inset: (x: 16pt, y: 12pt),
    radius: 5pt,
    width: 100%
  )[
    #text(size: 15pt, weight: "bold", fill: white)[tfscan: Terraform Misconfiguration Scanner]\
    #v(2pt)
    #text(size: 9.5pt, fill: rgb("#94a3b8"), weight: "medium")[Static AWS Security Analysis with a Measured Checkov Comparison]\
    #v(5pt)
    #line(length: 40%, stroke: 0.5pt + rgb("#334155"))
    #v(3pt)
    #text(size: 7.5pt, fill: rgb("#cbd5e1"))[
      *Author:* Raj Chhapariya #h(10pt) | #h(10pt) *Date:* October 2026 #h(10pt) | #h(10pt) *Target:* AWS Static IaC Analysis
    ]
  ]
]

#v(0.15cm)

== 1. Question and method

Can a small static scanner for 12 AWS rules, which returns UNKNOWN instead of guessing when a value cannot be resolved, match Checkov on a hand-labelled set? Ground-truth labels were established by manual code inspection prior to running either scanner to eliminate label contamination from scanner outputs. Three subsequent adjustments to fixtures and labels are documented in `docs/LABEL_CHANGES.md`. The evaluation sets comprise {fx["resources"]} fixture resources developed for this project, and {tgs} scored items on TerraGoat (AWS folder, pinned commit `729f8da`). Each fixture is scanned in its own directory to prevent cross-file state leakage. Results are keyed by full path and resource address. A mapped Checkov check that did not run on an item is counted as a miss, not as a pass.

== 2. Caveats and Evaluation Baselines

- The fixtures were written together with the scanner. High scores on them are weak evidence. TerraGoat is the independent set and is small ({tgs} scored items).
- TerraGoat was built by Bridgecrew, the company behind Checkov, creating an inherent benchmark bias toward Checkov.
- AWS has applied SSE-S3 default encryption to all new buckets since January 2023; therefore, rule S3-03 has severity LOW and verifies explicit cryptographic choice in code (such as KMS CMK or AES256) rather than physical lack of encryption. Checkov check CKV\\_AWS\\_19 passes buckets without an encryption block, whereas tfscan S3-03 requires an explicit declaration. The headline benchmark row leaves S3-03 out.
- SEC-01 maps only to CKV\\_AWS\\_41 (provider blocks). Checkov's separate secrets scanner was not run, which lowers Checkov's SEC-01 recall.
- Each timing measurement is recorded from a single run on Windows 11.

== 3. Results

#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
    fill: (col, row) => if row == 0 {{ rgb("#f1f5f9") }} else if row >= 13 {{ rgb("#f8fafc") }} else {{ none }},
    align: center, stroke: 0.4pt + luma(180), inset: 2.8pt,
    [*Rule*], [*Items*], [*tfscan P*], [*tfscan R*], [*tfscan F1*], [*tfscan UNK*], [*Checkov P*], [*Checkov R*], [*Checkov F1*], [*Checkov No-Check*],
{tbl}
  ),
  caption: [Precision, recall, F1 against hand labels. UNKNOWN-labelled items are excluded from P and R.],
)

#v(0.1cm)
#align(center)[
  #image("../results/figures/f1_comparison.png", width: 85%)
]
#v(-0.2cm)
#align(center)[
  #text(size: 7.5pt, fill: rgb("#64748b"), style: "italic")[Figure 1: F1 score comparison per rule across all 12 evaluated checks (ALL\\* excludes {ex}).]
]

On the items with a definite label, tfscan scored precision {pct(tf_t["precision"])} and recall {pct(tf_t["recall"])}; Checkov scored {pct(ck_t["precision"])} and {pct(ck_t["recall"])} (all 12 rules). Without {ex}, Checkov recall is {pct(H["checkov"]["recall"])}. On TerraGoat alone tfscan scored {pct(D["terragoat"]["tfscan"]["recall"])} recall and Checkov {pct(D["terragoat"]["checkov"]["recall"])}. Of {ck_t["unknowable_items"]} items labelled unknowable, tfscan answered UNKNOWN on {tf_t["correct_unknown"]}; Checkov gave a definite FAIL or PASS on {ck_t["overconfident"]}.

Timing (wall clock, includes process start-up): fixtures, tfscan CLI {fx["tfscan_cli_wall_ms"]:.0f} ms against Checkov {fx["checkov_wall_ms"]:.0f} ms; TerraGoat AWS, {tg["tfscan_cli_wall_ms"]:.0f} ms against {tg["checkov_wall_ms"]:.0f} ms. Much of the gap is start-up cost, so it should not be read as a per-resource speed ratio.

== 4. Disagreements

{len(dis)} labelled items got different verdicts. tfscan matched the label on {n_tf_right}, Checkov on {n_ck_right}, and {n_unk} were unknowable items. Per-item notes are in `docs/disagreement_notes.csv` and the README.

#figure(
  table(
    columns: (3fr, auto, auto, auto, auto, auto),
    fill: (col, row) => if row == 0 {{ rgb("#f1f5f9") }} else {{ none }},
    align: (left, center, center, center, center, center), stroke: 0.4pt + luma(180), inset: 2.6pt,
    [*Item*], [*Rule*], [*Label*], [*tfscan*], [*Checkov*], [*Right*],
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
subprocess.run(["typst", "compile", str(ROOT / "report" / "report.typ"), str(ROOT / "report" / "report.pdf"), "--root", str(ROOT)], check=True)
print("Report compiled successfully")
