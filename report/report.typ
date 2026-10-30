#set page(
  paper: "a4",
  margin: (top: 1.6cm, bottom: 1.6cm, left: 1.8cm, right: 1.8cm),
  header: context {
    if counter(page).get().first() > 1 [
      #set text(size: 8pt, fill: rgb("#64748b"), font: "Segoe UI")
      #grid(
        columns: (1fr, 1fr),
        align(left)[*tfscan: Terraform Misconfiguration Scanner* | Technical Evaluation Report],
        align(right)[Benchmark ID: TF-EVAL-2026]
      )
      #line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
    ]
  },
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
    #text(size: 15pt, weight: "bold", fill: white)[tfscan: Terraform Misconfiguration Scanner]    #v(2pt)
    #text(size: 9.5pt, fill: rgb("#94a3b8"), weight: "medium")[Static AWS Security Analysis with a Measured Checkov Comparison]    #v(5pt)
    #line(length: 40%, stroke: 0.5pt + rgb("#334155"))
    #v(3pt)
    #text(size: 7.5pt, fill: rgb("#cbd5e1"))[
      *Author:* Raj Chhapariya #h(10pt) | #h(10pt) *Date:* October 2026 #h(10pt) | #h(10pt) *Target:* AWS Static IaC Analysis
    ]
  ]
]

#v(0.15cm)

== 1. Question and method

Can a small static scanner for 12 AWS rules, which returns UNKNOWN instead of guessing when a value cannot be resolved, match Checkov on a hand-labelled set? Ground-truth labels were established by manual code inspection prior to running either scanner to eliminate label contamination from scanner outputs. Three subsequent adjustments to fixtures and labels are documented in `docs/LABEL_CHANGES.md`. The evaluation sets comprise 102 fixture resources developed for this project, and 33 scored items on TerraGoat (AWS folder, pinned commit `729f8da`). Each fixture is scanned in its own directory to prevent cross-file state leakage. Results are keyed by full path and resource address. A mapped Checkov check that did not run on an item is counted as a miss, not as a pass.

== 2. Caveats and Evaluation Baselines

- The fixtures were written together with the scanner. High scores on them are weak evidence. TerraGoat is the independent set and is small (33 scored items).
- TerraGoat was built by Bridgecrew, the company behind Checkov, creating an inherent benchmark bias toward Checkov.
- AWS has applied SSE-S3 default encryption to all new buckets since January 2023; therefore, rule S3-03 has severity LOW and verifies explicit cryptographic choice in code (such as KMS CMK or AES256) rather than physical lack of encryption. Checkov check CKV\_AWS\_19 passes buckets without an encryption block, whereas tfscan S3-03 requires an explicit declaration. The headline benchmark row leaves S3-03 out.
- SEC-01 maps only to CKV\_AWS\_41 (provider blocks). Checkov's separate secrets scanner was not run, which lowers Checkov's SEC-01 recall.
- Each timing measurement is recorded from a single run on Windows 11.

== 3. Results

#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
    fill: (col, row) => if row == 0 { rgb("#f1f5f9") } else if row >= 13 { rgb("#f8fafc") } else { none },
    align: center, stroke: 0.4pt + luma(180), inset: 2.8pt,
    [*Rule*], [*Items*], [*tfscan P*], [*tfscan R*], [*tfscan F1*], [*tfscan UNK*], [*Checkov P*], [*Checkov R*], [*Checkov F1*], [*Checkov No-Check*],
  [CT-01], [6], [100.0%], [100.0%], [1.000], [25.0%], [100.0%], [100.0%], [1.000], [0],
  [EBS-01], [7], [100.0%], [100.0%], [1.000], [22.2%], [100.0%], [100.0%], [1.000], [2],
  [IAM-01], [8], [100.0%], [100.0%], [1.000], [20.0%], [100.0%], [100.0%], [1.000], [0],
  [KMS-01], [7], [100.0%], [100.0%], [1.000], [22.2%], [100.0%], [100.0%], [1.000], [2],
  [RDS-01], [7], [100.0%], [100.0%], [1.000], [22.2%], [100.0%], [100.0%], [1.000], [2],
  [RDS-02], [7], [100.0%], [100.0%], [1.000], [22.2%], [100.0%], [100.0%], [1.000], [2],
  [S3-01], [12], [100.0%], [100.0%], [1.000], [14.3%], [90.0%], [100.0%], [0.947], [2],
  [S3-02], [12], [100.0%], [100.0%], [1.000], [14.3%], [100.0%], [100.0%], [1.000], [2],
  [S3-03], [13], [100.0%], [100.0%], [1.000], [13.3%], [n/a], [0.0%], [n/a], [2],
  [SEC-01], [9], [100.0%], [100.0%], [1.000], [18.2%], [100.0%], [40.0%], [0.571], [6],
  [SG-01], [9], [100.0%], [100.0%], [1.000], [18.2%], [100.0%], [100.0%], [1.000], [0],
  [SG-02], [9], [100.0%], [100.0%], [1.000], [18.2%], [100.0%], [100.0%], [1.000], [0],
  [All 12], [106], [100.0%], [100.0%], [1.000], [18.5%], [97.7%], [79.6%], [0.878], [20],
  [All but S3-03], [93], [100.0%], [100.0%], [1.000], [19.1%], [97.7%], [93.5%], [0.956], [18],
  [Fixtures], [73], [100.0%], [100.0%], [1.000], [24.7%], [96.9%], [86.1%], [0.912], [19],
  [TerraGoat], [33], [100.0%], [100.0%], [1.000], [0.0%], [100.0%], [66.7%], [0.800], [1],
  ),
  caption: [Precision, recall, F1 against hand labels. UNKNOWN-labelled items are excluded from P and R.],
)

#v(0.1cm)
#align(center)[
  #image("../results/figures/f1_comparison.png", width: 85%)
]
#v(-0.2cm)
#align(center)[
  #text(size: 7.5pt, fill: rgb("#64748b"), style: "italic")[Figure 1: F1 score comparison per rule across all 12 evaluated checks (ALL\* excludes S3-03).]
]

On the items with a definite label, tfscan scored precision 100.0% and recall 100.0%; Checkov scored 97.7% and 79.6% (all 12 rules). Without S3-03, Checkov recall is 93.5%. On TerraGoat alone tfscan scored 100.0% recall and Checkov 66.7%. Of 24 items labelled unknowable, tfscan answered UNKNOWN on 24; Checkov gave a definite FAIL or PASS on 8.

Timing (wall clock, includes process start-up): fixtures, tfscan CLI 272 ms against Checkov 35250 ms; TerraGoat AWS, 264 ms against 27326 ms. Much of the gap is start-up cost, so it should not be read as a per-resource speed ratio.

== 4. Disagreements

21 labelled items got different verdicts. tfscan matched the label on 13, Checkov on 0, and 8 were unknowable items. Per-item notes are in `docs/disagreement_notes.csv` and the README.

#figure(
  table(
    columns: (3fr, auto, auto, auto, auto, auto),
    fill: (col, row) => if row == 0 { rgb("#f1f5f9") } else { none },
    align: (left, center, center, center, center, center), stroke: 0.4pt + luma(180), inset: 2.6pt,
    [*Item*], [*Rule*], [*Label*], [*tfscan*], [*Checkov*], [*Right*],
  [Fi: case3\_v4\_pab\_linked\_by\_name.tf], [S3-01], [PASS], [PASS], [FAIL], [tfscan],
  [Fi: case1\_v3\_no\_sse.tf], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Fi: case2\_v4\_no\_sse.tf], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Fi: case3\_v4\_unrelated\_resource.tf], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Fi: case1\_cidr\_variable.tf], [SG-01], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case2\_port\_variable.tf], [SG-01], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case1\_cidr\_var.tf], [SG-02], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case2\_rule\_remote\_state.tf], [SG-02], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case1\_unresolved\_multi\_region.tf], [CT-01], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case2\_unresolved\_validation.tf], [CT-01], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case1\_policy\_variable.tf], [IAM-01], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case2\_template\_file.tf], [IAM-01], [UNKNOWN], [UNKNOWN], [PASS], [n/a (unknowable)],
  [Fi: case2\_db\_literal\_password.tf], [SEC-01], [FAIL], [FAIL], [NO\_CHECK], [tfscan],
  [Fi: case3\_resolved\_default\_password.tf], [SEC-01], [FAIL], [FAIL], [NO\_CHECK], [tfscan],
  [Fi: case2\_var\_no\_default.tf], [SEC-01], [PASS], [PASS], [NO\_CHECK], [tfscan],
  [Te: s3.tf aws\_s3\_bucket.data], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Te: s3.tf aws\_s3\_bucket.financials], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Te: s3.tf aws\_s3\_bucket.operations], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Te: s3.tf aws\_s3\_bucket.data\_science], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Te: ec2.tf aws\_s3\_bucket.flowbucket], [S3-03], [FAIL], [FAIL], [PASS], [tfscan],
  [Te: db-app.tf aws\_db\_instance.default], [SEC-01], [FAIL], [FAIL], [NO\_CHECK], [tfscan],
  ),
  caption: [All disagreements. "Right" is blank-equivalent n/a for unknowable items.],
)

== 5. Limits and what was fixed along the way

Evaluation exposed two scanner weaknesses, both found by checking disagreements against the code. The security-group rules asked for the CIDR before the port, so a rule on port 3306 with an unresolvable CIDR came back UNKNOWN; the port is now checked first. S3-03 returns UNKNOWN when an explicit encryption block has a KMS key given as a reference, which the labels treat as a pass; this is not fixed and is the one TerraGoat item where tfscan answered UNKNOWN against a PASS label. Static analysis of `.tf` files cannot see values set outside the code, which is why UNKNOWN exists.

== 6. Reproduce

`pip install -e .[dev]`, `bash scripts/fetch_terragoat.sh`, `python eval/run_scans.py`, `python -m eval.score`, `python -m eval.disagreements`, `python -m eval.plot_figure`, `python -m eval.generate_artifacts`, `python report/generate_report.py`. Environment: `results/ENVIRONMENT.md`.
