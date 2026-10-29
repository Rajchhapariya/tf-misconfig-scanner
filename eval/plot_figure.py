"""
Generates high-resolution grouped bar chart comparing F1 scores of tfscan vs Checkov per rule.
Saves figure to results/figures/f1_comparison.png and results/figures/f1_comparison.svg.
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCORES_PATH = PROJECT_ROOT / "results" / "summary_scores.json"
FIG_DIR = PROJECT_ROOT / "results" / "figures"


def generate_plot():
    with open(SCORES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    per_rule = data["per_rule_scores"]
    rule_ids = sorted(list(per_rule.keys()))

    tf_f1 = [per_rule[r]["tfscan"]["f1"] or 0 for r in rule_ids]
    ckv_f1 = [per_rule[r]["checkov"]["f1"] or 0 for r in rule_ids]

    # Add aggregate
    agg = data["aggregate_headline"]
    labels = rule_ids + ["ALL*"]
    tf_f1.append(agg["tfscan"]["f1"])
    ckv_f1.append(agg["checkov"]["f1"])

    x = np.arange(len(labels))
    width = 0.36

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    rects1 = ax.bar(x - width / 2, tf_f1, width, label="tfscan (This Work)", color="#1e3a8a", edgecolor="#0f172a", linewidth=0.8)
    rects2 = ax.bar(x + width / 2, ckv_f1, width, label="Checkov v3.4.0", color="#3b82f6", edgecolor="#1d4ed8", linewidth=0.8)

    ax.set_ylabel("F1 Score", fontsize=11, fontweight="bold", color="#0f172a")
    ax.set_title("F1 per rule (ALL* excludes S3-03)", fontsize=13, fontweight="bold", pad=14, color="#0f172a")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold", rotation=0)
    ax.set_ylim(0, 1.15)
    ax.legend(frameon=True, facecolor="#f8fafc", edgecolor="#cbd5e1", fontsize=10, loc="upper right")

    # Value labels on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(
                f"{height:.2f}",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="medium",
                color="#334155",
            )

    autolabel(rects1)
    autolabel(rects2)

    # Highlight OVERALL column
    ax.axvline(x=len(rule_ids) - 0.5, color="#94a3b8", linestyle="--", linewidth=1.0)

    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIG_DIR / "f1_comparison.png"
    out_svg = FIG_DIR / "f1_comparison.svg"
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_svg)
    plt.close()

    print(f"Figure saved successfully to {out_png} and {out_svg}")


if __name__ == "__main__":
    generate_plot()
