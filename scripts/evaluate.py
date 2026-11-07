"""Evaluate one model's raw outputs at one batch size: clean, score per sentence, compare protocols.
Takes raw outputs of one model at one batch size and provides per-sentence scores and writes summary.json."""

from umr_mt.evaluation.metrics import chrf_scores, bertscore_f1
from umr_mt.evaluation.significance import paired_ttest, paired_bootstrap, holm
from umr_mt.evaluation.postprocess import clean_output, has_umr_leakage, process_record
from umr_mt.prompting.templates import PROTOCOLS, LANGUAGE_NAMES
from collections import Counter
from pathlib import Path
import json
import argparse
import yaml
import statistics

EXPECTED_LENGTH = 4059 # total number of records in pairs_with_demos.jsonl (Czech 3,914 + Portuguese 95 + Latin 50)

pairs_file_path = Path("data/processed/pairs_with_demos.jsonl")
configuration_file_path = Path("configs/models.yaml")

raw_folder = Path("outputs/raw")
scores_folder = Path("outputs/scores")

with open(configuration_file_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True, choices=list(config["models"]), help="short name from configs/models.yaml")
parser.add_argument("--batch-size", type=int, required=True, help="batch size of the runs")
parser.add_argument("--languages", type=str, nargs="+", default=list(LANGUAGE_NAMES), choices=LANGUAGE_NAMES, help="language to evaluate")
# only for testing while runs are in progress. Final results require complete files.
parser.add_argument("--allow-partial", action="store_true", help="allows evaluating incomplete output files, for testing")

if __name__ == "__main__":
    args = parser.parse_args()
    run_raw = raw_folder / args.model / f"bs{args.batch_size}"
    if not run_raw.exists():
        raise ValueError(f"no outputs for {args.model} at batch size {args.batch_size}: {run_raw}")

    score_runs = scores_folder / args.model / f"bs{args.batch_size}"
    score_runs.mkdir(parents=True, exist_ok=True)

    print("options:", args)
    print("raw:", run_raw)
    print("scores:", score_runs)
    
    with open(pairs_file_path, "r", encoding="utf-8") as f:
        content = [json.loads(line) for line in f if line.strip()]

    refs = {}
    for record in content:
        refs[record["uid"]] = record
    if len(refs) != EXPECTED_LENGTH:
        raise ValueError(f"Expected: {EXPECTED_LENGTH} but got {len(refs)}")

    print(Counter(r["language"] for r in refs.values()))

    outputs = {}
    metric_info = {}
    all_scores = {}

    for protocol in PROTOCOLS:
        path = run_raw / f"{protocol}.jsonl"
        # not every protocol exists at every batch size. 
        if not path.exists():
            print(f"{protocol}: no file at this batch size")
            continue
        with open(path, "r", encoding="utf-8") as f:
            raw_records = [json.loads(line) for line in f if line.strip()]
        
        cleaned_protocol_records = [process_record(record) for record in raw_records]
        processed_protocol_records = [record for record in cleaned_protocol_records if record["language"] in args.languages]
        
        outputs[protocol] = processed_protocol_records

        # checks: a resumed run could potentially duplicate or miss sentences. Score must cover the same sentences in every protocol.
        if len({r["uid"] for r in processed_protocol_records}) != len(processed_protocol_records):
            raise ValueError(f"{protocol}: unique records: {len({r["uid"] for r in processed_protocol_records})} and records: {len(processed_protocol_records)}")
        
        if not all(r["uid"] in refs for r in processed_protocol_records):
            raise ValueError(f"{protocol}: unknown uid in output.")
        
        expected = sum(1 for r in refs.values() if r["language"] in args.languages)
        
        if len(processed_protocol_records) != expected:
            if args.allow_partial:
                print(f"Warning: Protocol - {protocol} --> 'partial', {len(processed_protocol_records)} of expected {expected}")
            else:
                raise ValueError(f"Protocol - {protocol} --> 'incomplete', {len(processed_protocol_records)} of expected {expected}, use '--allow-partial' to test")
        
        # Summary
        langs = Counter(r["language"] for r in processed_protocol_records)
        n_empty = sum(r["empty"] for r in processed_protocol_records)
        n_cap   = sum(r["hit_cap"] for r in processed_protocol_records)
        n_leak  = sum(r["umr_leak"] for r in processed_protocol_records)

        print(f"Protocol: {protocol}| Languages: {langs}| Empty Records: {n_empty}| Capped Records: {n_cap}| Leak detected records: {n_leak}")

        scored = []
        for language in args.languages:
            # sorted: a fixed order makes the score files identical across reruns.
            lang_records = sorted([r for r in processed_protocol_records if r["language"] == language], key=lambda r: r["uid"])
            
            if not lang_records:
                continue
            
            hyps = [r["clean_text"] for r in lang_records]
            refs_text = [refs[r["uid"]]["target_text"] for r in lang_records]

            chrf, chrf_sig = chrf_scores(hyps, refs_text)
            bs, bs_hash = bertscore_f1(hyps, refs_text)
            metric_info["chrf"] = chrf_sig
            metric_info["bertscore"] = bs_hash

            for lang_record, c, b in zip(lang_records, chrf, bs):
                dict_intermediate = {}
                dict_intermediate["uid"] = lang_record["uid"]
                dict_intermediate["language"] = lang_record["language"]
                dict_intermediate["protocol"] = protocol
                dict_intermediate["chrf"] = c
                dict_intermediate["bertscore_f1"] = b
                dict_intermediate["empty"] = lang_record["empty"]
                dict_intermediate["hit_cap"] = lang_record["hit_cap"]
                dict_intermediate["umr_leak"] = lang_record["umr_leak"]
                scored.append(dict_intermediate)

        # partial runs can have nothing yet for a language -- avoid empty files and division by zero.
        if not scored:
            print(f"{protocol}: nothing to score for {args.languages}")
            continue

        protocol_output_score_file = score_runs / f"{protocol}.jsonl"

        with open(protocol_output_score_file, "w", encoding="utf-8") as f:
            for item in scored:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        all_scores[protocol] = {s["uid"]: s for s in scored}

        print(f"Confirmation: Protocol - {protocol} | number of lines written: {len(scored)} | mean chrf: {sum(s["chrf"] for s in scored) / len(scored):.2f}")
    
    pairs = [("zero_shot", "zero_shot_umr"), ("zero_shot", "five_shot"), ("five_shot", "five_shot_umr")]
    results = []
    for language in args.languages:
        for metric in ("chrf", "bertscore_f1"):
            for p1, p2 in pairs:
                if p1 not in all_scores or p2 not in all_scores:
                    continue
                uids_1 = {u for u, s in all_scores[p1].items() if s["language"] == language}
                uids_2 = {u for u, s in all_scores[p2].items() if s["language"] == language}
                uids = sorted(uids_1 & uids_2)          # & = in both sets -- paired tests need the same sentences in both protocols.
                if not uids:
                    continue
                a = [all_scores[p1][u][metric] for u in uids]
                b = [all_scores[p2][u][metric] for u in uids]
                t, p, md = paired_ttest(a, b)
                _, (low, high) = paired_bootstrap(a, b)
                results.append(
                    {
                        "language": language,
                        "metric": metric,
                        "pair": f"{p1} vs {p2}", 
                        "n": len(uids),
                        "mean_a": sum(a) / len(a),
                        "mean_b": sum(b) / len(b),
                        "mean_diff": md, 
                        "t": t, 
                        "p": p, 
                        "ci_low": low, 
                        "ci_high": high
                    }
                )


    # Holm block: up to 3 comparisons of one language x metric are corrected together
    for language in args.languages:
        for metric in ("chrf", "bertscore_f1"):
            family = [r for r in results if r["language"] == language and r["metric"] == metric]
            if not family:
                continue
            adjusted = holm([r["p"] for r in family])
            for r, p_adj in zip(family, adjusted):
                r["p_holm"] = p_adj
    
    for r in results:
        print(f"{r['language']:10} {r['metric']:12} {r['pair']:28} n={r['n']:5}  "
              f"diff={r['mean_diff']:+.3f}  CI=[{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]  "
              f"p={r['p']:.3g}  p_holm={r['p_holm']:.3g}")

    # Writing summary.json file
    protocol_stats = {}
    for protocol, by_uid in all_scores.items():
        for language in args.languages:
            items = [s for s in by_uid.values() if s["language"] == language]
            if not items:
                continue
            stats = {"n": len(items)}
            for metric in ("chrf", "bertscore_f1"):
                values = [s[metric] for s in items]
                stats[f"{metric}_mean"] = statistics.mean(values)
                stats[f"{metric}_sd"] = statistics.stdev(values) if len(values) > 1 else None
            for flag in ("empty", "hit_cap", "umr_leak"):
                stats[flag] = sum(s[flag] for s in items)
            protocol_stats[f"{protocol}|{language}"] = stats

    # allow_partial in summary: such that summary built from partial outputs can't be mistaken for a final one.
    summary = {
        "run": {"model": args.model, "revision": config["models"][args.model]["revision"],
                "batch_size":args.batch_size, "languages": args.languages, "allow_partial":args.allow_partial},
        "metrics": metric_info,
        "protocols": protocol_stats,
        "comparisons": results
    }

    with open(score_runs / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


    print("summary:", score_runs / "summary.json")
    
