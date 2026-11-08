"""Paper figures from the result tables: chrF per protocol at batch size 1, 
and how far chrF moves at larger batch sizes, with 95% CIs."""

from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")                 
import matplotlib.pyplot as plt

tables = Path("outputs/tables")
out_dir = Path("outputs/figures")
PROTOCOLS = ["zero_shot", "zero_shot_umr", "five_shot", "five_shot_umr"]
LANGUAGES = ["czech", "latin", "portuguese"]
MODELS = ["gemma3_12b", "qwen3_8b"]
NAMES = {"gemma3_12b": "Gemma-3-12B-it", "qwen3_8b": "Qwen3-8B"}
LABELS = {"zero_shot": "zero", "zero_shot_umr": "zero+UMR", "five_shot": "five", "five_shot_umr": "five+UMR"}

def read_tsv(path):
    """Read one result table written by tables.py or batch_size.py; every value comes back as text."""

    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def figure_main(rows):
    """Mean chrF of the four prompting protocols for each model 
    and language at batch size 1, the setting used for the main comparisons."""

    fig, axes = plt.subplots(1, 3, figsize=(10, 3), sharey=True)
    width = 0.38
    for ax, lang in zip(axes, LANGUAGES):
        for k, model in enumerate(MODELS):
            means = [float(r["chrf_mean"]) for p in PROTOCOLS for r in rows
                     if r["batch_size"] == "1" and r["language"] == lang
                     and r["model"] == model and r["protocol"] == p]
            xs = [i + (k - 0.5) * width for i in range(len(PROTOCOLS))]
            bars = ax.bar(xs, means, width, label=NAMES[model])
            ax.bar_label(bars, fmt="%.1f", fontsize=6)
        ax.set_xticks(range(len(PROTOCOLS)))
        ax.set_xticklabels([LABELS[p] for p in PROTOCOLS])
        ax.set_title(lang.capitalize())
    axes[0].set_ylabel("chrF (batch size 1)")
    axes[0].set_ylim(0, 82)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out_dir / "fig1_main.pdf")


def figure_bs_deltas(rows):
    """Change in mean chrF at each batch size relative to batch size 1, per model,
    language and protocol, with paired bootstrap 95% CIs. (points on the dashed zero
    line mean batching did not change the scores)"""

    fig, axes = plt.subplots(2, 3, figsize=(10, 5.2), sharex=True, sharey=True)
    for i, model in enumerate(MODELS):
        for j, lang in enumerate(LANGUAGES):
            ax = axes[i][j]
            for k, p in enumerate(PROTOCOLS):
                sel = sorted([r for r in rows if r["metric"] == "chrf" and r["model"] == model
                              and r["language"] == lang and r["protocol"] == p],
                             key=lambda r: int(r["batch_size"]))
                if not sel:
                    continue
                x = [int(r["batch_size"]) * (1 + 0.06 * (k - 1.5)) for r in sel]
                y = [float(r["mean_diff"]) for r in sel]
                err = [[yy - float(r["ci_low"]) for yy, r in zip(y, sel)],
                       [float(r["ci_high"]) - yy for yy, r in zip(y, sel)]]
                ax.errorbar(x, y, yerr=err, fmt="o", ms=3, capsize=2, label=LABELS[p])
            ax.axhline(0, ls="--", lw=0.8, color="grey")
            ax.set_xscale("log", base=2)
            ax.set_xticks([2, 4, 8, 16, 32], labels=["2", "4", "8", "16", "32"])
            ax.set_title(f"{NAMES[model]} - {lang.capitalize()}", fontsize=9)
    for ax in axes[1]:
        ax.set_xlabel("batch size")
    for ax in axes[:, 0]:
        ax.set_ylabel("Δ chrF vs batch size 1")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out_dir / "fig2_bs_deltas.pdf")


if __name__ == "__main__":
    out_dir.mkdir(parents=True, exist_ok=True)
    figure_main(read_tsv(tables / "table_scores.tsv"))
    figure_bs_deltas(read_tsv(tables / "table_bs_deltas.tsv"))