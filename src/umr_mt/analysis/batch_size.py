"""Batch-size analysis against unbatched generation (batch size 1): whether the cleaned translations are identical,
whether per-sentence chrF and BERTScore change, and whether any protocol comparison changes its direction or significance."""

from umr_mt.evaluation.postprocess import process_record
from umr_mt.analysis.tables import write_tsv
from umr_mt.prompting.templates import PROTOCOLS, LANGUAGE_NAMES
from umr_mt.evaluation.significance import paired_ttest, paired_bootstrap, holm
from collections import defaultdict
from pathlib import Path
import json
import csv
import statistics
import yaml
import re

EXPECTED_LENGTH = 4059

def load_clean(path):
    """Load one raw generation file and clean each output using evaluation's postprocessing, 
    so identity is judged on the scored text."""
    with open(path, "r", encoding="utf-8") as f:
        raw_records = [json.loads(line) for line in f if line.strip()]
        
    cleaned_protocol_records = [process_record(record) for record in raw_records]


    return {cleaned_protocol_record["uid"]: (cleaned_protocol_record["language"], cleaned_protocol_record["clean_text"]) for cleaned_protocol_record in cleaned_protocol_records}


def is_complete(records):
    """True when a run covers all 4,059 test sentences. 
    Incomplete runs are skipped to ensure every batch size is compared on the same sentences."""
    return len(records) == EXPECTED_LENGTH


def identity(ref, other):
    """Count the sentences present in both runs, 
    and the count that received exactly the same cleaned translation."""
    # uids present in both
    shared = [uid for uid in ref.keys() if uid in other.keys()]
    n = len(shared)

    # number of cases where each shared uid has identical text.
    n_identical = sum([ref[uid]==other[uid] for uid in shared])

    return (n, n_identical)
    

def identity_rows(raw_path):
    """For every model, protocol and language, the share of sentences whose cleaned translation at batch size N 
    is identical to the translation at batch size 1."""
    
    rows = []
    for model in sorted(raw_path.iterdir()):
        if not model.is_dir():
            continue
        model_name = model.name
        for protocol in PROTOCOLS:
            protocol_files = list(model.glob(f"bs*/{protocol}.jsonl"))
            by_size = {int(f.parent.name[2:]): f for f in protocol_files}
            
            if 1 not in by_size:
                print(f"Skip {model_name} {protocol}: no bs1")
                continue
            
            ref = load_clean(by_size[1])

            if not is_complete(ref):
                print(f"incomplete: {by_size[1]} ({len(ref)} of {EXPECTED_LENGTH})")
                continue

            for bs in sorted(by_size):
                if bs == 1:
                    continue
                other = load_clean(by_size[bs])
                if not is_complete(other):
                    print(f"incomplete: {by_size[bs]} ({len(other)} of {EXPECTED_LENGTH})")
                    continue
            
                for language in LANGUAGE_NAMES:
                    filtered_ref = {k: v for k, v in ref.items() if v[0] == language}
                    filtered_other = {k: v for k, v in other.items() if v[0] == language}
                    n, identical = identity(filtered_ref, filtered_other)
                    if n == 0:
                        continue
                
                    rows.append(
                        {
                            "model": model_name,
                            "protocol": protocol,
                            "language": language,
                            "batch_size": bs,
                            "n": n,
                            "n_identical": identical,
                            "pct_identical": 100*identical/n,
                        }
                    )
    return rows


def load_scores(path):
    """Load the per-sentence chrF and BERTScore (evaluate.py), batch size and protocol, keyed by uid."""

    with open(path, "r", encoding="utf-8") as f:
        score_records = [json.loads(line) for line in f if line.strip()]

    return {score_record["uid"]: score_record for score_record in score_records}


def delta_rows(scores_path):
    """Measure how far batching moves the scores: for every model, protocol, language and metric, 
    the mean per-sentence difference between batch size N and batch size 1, 
    (paired t-test and a paired bootstrap 95% CI, and Holm-corrected across the batch sizes of that group). 
    When all scores are identical the tests are skipped and p is 1."""
    rows = []
    for model in sorted(scores_path.iterdir()):
        if not model.is_dir():
            continue
        model_name = model.name
        for protocol in PROTOCOLS:
            protocol_files = list(model.glob(f"bs*/{protocol}.jsonl"))
            by_size = {int(f.parent.name[2:]): f for f in protocol_files}
            
            if 1 not in by_size:
                print(f"Skip {model_name} {protocol}: no bs1")
                continue
            
            ref = load_scores(by_size[1])

            if not is_complete(ref):
                print(f"incomplete: {by_size[1]} ({len(ref)} of {EXPECTED_LENGTH})")
                continue

            for bs in sorted(by_size):
                if bs == 1:
                    continue
                other = load_scores(by_size[bs])
                if not is_complete(other):
                    print(f"incomplete: {by_size[bs]} ({len(other)} of {EXPECTED_LENGTH})")
                    continue
            
                for language in LANGUAGE_NAMES:
                    filtered_ref = {k: v for k, v in ref.items() if v["language"] == language}
                    filtered_other = {k: v for k, v in other.items() if v["language"] == language}
                    shared = sorted([uid for uid in filtered_ref.keys() if uid in filtered_other.keys()])
                    if not shared:
                        continue
                    for metric in ("chrf", "bertscore_f1"):
                        a = [filtered_ref[u][metric] for u in shared]
                        b = [filtered_other[u][metric] for u in shared]
                        if a == b: 
                            p, mean_diff, low, high = 1.0, 0.0, 0.0, 0.0
                        else:       
                            t, p, mean_diff = paired_ttest(a, b)
                            _, (low, high) = paired_bootstrap(a, b)
                        rows.append(
                            {
                                "model": model_name, 
                                "protocol": protocol, 
                                "language": language, 
                                "metric": metric, 
                                "batch_size": bs, 
                                "n": len(shared), 
                                "mean_bs1": statistics.mean(a), 
                                "mean_bsN": statistics.mean(b), 
                                "mean_diff": mean_diff, 
                                "ci_low": low, 
                                "ci_high": high, 
                                "p": p
                            }
                        )
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[(r["model"], r["protocol"], r["language"], r["metric"])].append(i)

    for key, idx in groups.items():
        ps = [rows[i]["p"] for i in idx]
        corrected = holm(ps)
        for i, ph in zip(idx, corrected):
            rows[i]["p_holm"] = ph
    return rows


def sign(x):
    """Detect when a comparison changes direction: 1, -1 or 0 for a positive, negative or zero difference."""
    return (x > 0) - (x < 0)


def flips_rows(path):
    """Check whether batching would change a conclusion: 
    for every protocol comparison, whether its direction or its Holm significance at batch size 
    N differs from batch size 1."""
    with open(path, "r", encoding="utf-8") as f:
        comparisons = list(csv.DictReader(f, delimiter="\t"))
    groups_new = defaultdict(list)
    for r in comparisons:
        groups_new[(r["model"], r["language"], r["metric"], r["pair"])].append(r)

    rows = []
    for key, group in groups_new.items():
        by_bs = {int(r["batch_size"]): r for r in group}
        if 1 not in by_bs:
            continue

        ref = by_bs[1]
        diff_1 = float(ref["mean_diff"])
        sig_1 = float(ref["p_holm"]) < 0.05
        for bs in sorted(by_bs):
            if bs == 1:
                continue
            diff_n = float(by_bs[bs]["mean_diff"])
            sig_n = float(by_bs[bs]["p_holm"]) < 0.05
            rows.append({
                "model": key[0], "language": key[1], "metric": key[2], "pair": key[3],
                "batch_size": bs,
                "diff_bs1": diff_1,
                "diff_bsN": diff_n,
                "sig_bs1": sig_1,
                "sig_bsN": sig_n,
                "sign_flip": sign(diff_n) != sign(diff_1),
                "sig_flip": sig_n != sig_1,
            })
    return rows


def parse_log(path):
    """Read one generation log and total the generation time it reports. 
    A run cut by the time limit and resubmitted leaves two logs, which timing_rows adds together."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    header = re.search(r"model_index=(\d+) protocol=(\S+) bs=(\d+)", text)
    model_index, protocol, bs = int(header.group(1)), header.group(2), int(header.group(3))
    sentences, seconds = 0, 0.0

    for line in text.replace("\r", "\n").splitlines():
        m = re.match(r"^\w+: (\d+)/\d+\s+([\d.]+)s/batch", line)
        if m:
            sentences = int(m.group(1))
            seconds += float(m.group(2))

    return model_index, protocol, bs, sentences, seconds



def timing_rows(logs_path):
    """Generation speed per configuration: seconds per sentence and the speed-up over batch size 1 
    (same model and protocol)."""
    models = list(yaml.safe_load(open("configs/models.yaml"))["models"])
    totals = defaultdict(lambda: [0, 0.0])      
    for path in sorted(logs_path.glob("mq63-w-*.out")):
        model_index, protocol, bs, sentences, seconds = parse_log(path)
        key = (models[model_index], protocol, bs)
        totals[key][0] += sentences
        totals[key][1] += seconds

    rows = []

    for (model, protocol, bs), (sentences, seconds) in totals.items():
        base_sentences, base_seconds = totals[(model, protocol, 1)]
        spp = seconds / sentences
        base_spp = base_seconds / base_sentences
        rows.append({
            "model": model, "protocol": protocol, "batch_size": bs,
            "n_sentences": sentences, "gen_seconds": seconds,
            "sec_per_sentence": spp, "speedup_vs_bs1": base_spp / spp,
        })

    return rows

if __name__ == "__main__":
    raw_path = Path("outputs/raw")
    scores_path = Path("outputs/scores")
    out_dir = Path("outputs/tables")
    rows = identity_rows(raw_path)
    rows.sort(key=lambda r: (r["model"], r["language"], r["protocol"], r["batch_size"]))

    # writing tables
    if not rows:
        print("no rows: nothing to write")
        raise SystemExit
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    write_tsv(out_dir / "table_bs_identity.tsv", rows, list(rows[0].keys()))

    deltas = delta_rows(scores_path)
    deltas.sort(key=lambda r: (r["model"], r["language"], r["protocol"], r["metric"], r["batch_size"]))

    if not deltas:
        print("no rows: nothing to write")
        raise SystemExit
    
    write_tsv(out_dir / "table_bs_deltas.tsv", deltas, list(deltas[0].keys()))

    flips = flips_rows(out_dir / "table_comparisons.tsv")
    flips.sort(key=lambda r: (r["model"], r["language"], r["metric"], r["pair"], r["batch_size"]))

    if not flips:
        print("no rows: nothing to write")
        raise SystemExit
    
    write_tsv(out_dir / "table_bs_flips.tsv", flips, list(flips[0].keys()))

    timings = timing_rows(Path("../logs"))
    timings.sort(key=lambda r: ((r["model"], r["protocol"], r["batch_size"])))

    if not timings:
        print("no rows: nothing to write")
        raise SystemExit

    write_tsv(out_dir / "table_bs_timing.tsv", timings, list(timings[0].keys()))