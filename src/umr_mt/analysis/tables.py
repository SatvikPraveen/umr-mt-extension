"""Tables for the paper."""

import json
from pathlib import Path
import csv


summary_files_path = Path("outputs/scores")


# Kocmi et al. 2024, Table 2. (chrF Δ thresholds → % agreement with humans)
KOCMI_CHRF = [(3.05, 90), (2.12, 85), (1.63, 80), (1.28, 75), (1.00, 70),
              (0.76, 65), (0.54, 60), (0.33, 55), (0.14, 50)]


def load_summaries(path):
    """loads complete summary.json files."""
    summaries = []
    all_summary_files = sorted((path).glob("*/bs*/summary.json"))

    for summary_file in all_summary_files:
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)

        if summary["run"]["allow_partial"]:
            print("skipping partial:", summary_file)
            continue

        summaries.append(summary)
    return summaries 


def kocmi_accuracy(delta):
    """Estimated % agreement with human judgements for a chrF difference (Kocmi et al. 2024, Table 2); None below 0.14"""
    for threshold, accuracy in KOCMI_CHRF:
        if abs(delta) >= threshold:
            return accuracy
    return None

def write_tsv(path, rows, columns):
    """Write rows (dicts) to a TSV with the given column order"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(columns)
        for r in rows:
            writer.writerow([r[c] for c in columns])
    print(f"Total {len(rows)} written in {path}")


if __name__ == "__main__":
    summaries = load_summaries(summary_files_path)

    # Table 1
    tab1_rows = []
    for summary in summaries:
        for key, stats in summary["protocols"].items():
            protocol, language = key.split("|")
            tab1_rows.append(
                {
                    "model": summary["run"]["model"],
                    "batch_size": summary["run"]["batch_size"],
                    "language": language,
                    "protocol": protocol,
                    "n": stats["n"],
                    "chrf_mean": stats["chrf_mean"],
                    "chrf_sd": stats["chrf_sd"],
                    "bertscore_mean": stats["bertscore_f1_mean"],
                    "bertscore_sd": stats["bertscore_f1_sd"]
                }
            )
    tab1_rows.sort(key=lambda r: (r["model"], r["language"], r["protocol"], r["batch_size"]))

    if not tab1_rows:
        print("no complete summaries found.")
        raise SystemExit
    
    out_dir = Path("outputs/tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    tab1_cols = list(tab1_rows[0].keys())
    output_file = out_dir / "table_scores.tsv"
    write_tsv(output_file, tab1_rows, tab1_cols)


    # Table 2    
    tab2_rows = []
    for summary in summaries:
        for c in summary["comparisons"]:
            tab2_rows.append(
                {
                    "model": summary["run"]["model"],
                    "batch_size": summary["run"]["batch_size"],
                    "language": c["language"],
                    "metric": c["metric"], 
                    "pair": c["pair"], 
                    "n": c["n"], 
                    "mean_diff": c["mean_diff"], 
                    "ci_low": c["ci_low"], 
                    "ci_high": c["ci_high"], 
                    "p": c["p"], 
                    "p_holm": c["p_holm"],
                    "kocmi_acc": kocmi_accuracy(c["mean_diff"]) if c["metric"] == "chrf" else None
                }
            )

    tab2_rows.sort(key=lambda r: (r["model"], r["language"], r["metric"], r["pair"], r["batch_size"]))

    if not tab2_rows:
        print("no complete summaries found.")
        raise SystemExit

    tab2_cols = list(tab2_rows[0].keys())
    output_file = out_dir / "table_comparisons.tsv"
    write_tsv(output_file, tab2_rows, tab2_cols)


    # Table 3
    tab3_rows = []
    for summary in summaries:
        for key, stats in summary["protocols"].items():
            protocol, language = key.split("|")
            tab3_rows.append(
                {
                    "model": summary["run"]["model"],
                    "batch_size": summary["run"]["batch_size"],
                    "language": language,
                    "protocol": protocol,
                    "n": stats["n"],
                    "empty": stats["empty"],
                    "hit_cap": stats["hit_cap"],
                    "umr_leak": stats["umr_leak"]
                }
            )
    tab3_rows.sort(key=lambda r: (r["model"], r["language"], r["protocol"], r["batch_size"]))

    if not tab3_rows:
        print("no complete summaries found.")
        raise SystemExit
    
    tab3_cols = list(tab3_rows[0].keys())
    output_file = out_dir / "table_flags.tsv"
    write_tsv(output_file, tab3_rows, tab3_cols)
 