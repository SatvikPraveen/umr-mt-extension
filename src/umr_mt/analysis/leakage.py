"""Counts the test sentences whose five nearest-neighbour demonstrations repeat their source sentence or their English 
reference exactly, a side effect of allowing identical sentences in the 5-NN selection. 
(Only the five-shot protocols are affected)"""

from umr_mt.analysis.tables import write_tsv
from collections import Counter
from pathlib import Path
import json

pairs_path = Path("data/processed/pairs_with_demos.jsonl")
out_dir = Path("outputs/tables")


def load_pairs(path):
    """Load the processed pairs with their precomputed demonstrations."""

    with open(path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return {r["uid"]: r for r in records}


def repeats(record, demos, field):
    """True when any demonstration has exactly the same text as the test sentence 
    in the given field (source or English reference)."""

    return any(d[field].strip() == record[field].strip() for d in demos)


if __name__ == "__main__":
    by_uid = load_pairs(pairs_path)
    n, same_source, same_reference = Counter(), Counter(), Counter()

    for uid, r in by_uid.items():
        demos = [by_uid[u] for u in r["demo_uids"]]
        n[r["language"]] += 1
        if repeats(r, demos, "source_text"):
            same_source[r["language"]] += 1
            print("same source:", uid)
        if repeats(r, demos, "target_text"):
            same_reference[r["language"]] += 1
            print("same reference:", uid)

    rows = [{"language": lang, "n": n[lang],
             "same_source": same_source[lang], "same_reference": same_reference[lang]}
            for lang in sorted(n)]

    out_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(out_dir / "table_leakage_overlap.tsv", rows, list(rows[0].keys()))