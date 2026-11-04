"""Create a Json Lines file for the PORTUGUESE language with matched records containing the ENGLISH translation text. The data comes from reviewed matches, the corresponding UMR and PUD."""
import csv
from pathlib import Path
import json
from umr_mt.data.umr_reader import read_umr_file
from umr_mt.data.pud_reader import dict_return

EXPECTED_COUNT = 95
reviewed_tsv_path = Path("data/interim/portuguese_pud_matches_reviewed.tsv")
umr_portuguese_path = Path("data/raw/umr_v3.0_ae46502/portuguese/umr_data/portuguese_umr-0001.umr")
pud_portuguese_path = Path("data/raw/ud_portuguese_pud_0fdcc05/pt_pud-ud-test.conllu")

output_path = Path("data/interim/portuguese_pairs.jsonl")

def return_matched(path):
    """Filter the file to keep only the cases with verdict ok. Returns a dictionary mapping UMR id --> PUD id."""
    with open(path, "r", newline="", encoding="utf-8") as f:
        kept = {}
        content = csv.DictReader(f, delimiter='\t')
        for row in content:
            if row["verdict"] == "ok":
                kept[row["umr_id"]] = row["pud_id"]
        return kept

def filter_records(matched, records):
    """Keep only those UMR records whose sentence id is in matched."""
    kept_records = []
    for record in records:
        if record["sentence_id"] in matched:
            kept_records.append(record)
    return kept_records

def attach_english(kept_records, matched, dictionary):
    """Attach the ENGLISH text which serves as the target translation to the matched records. Additionally stores PUD id in each of the records."""
    for record in kept_records:
        pud_id = matched[record["sentence_id"]]
        record["target_text"] = dictionary[pud_id]["text_en"]
        record["pud_id"] = pud_id
    return kept_records
    

if __name__ == "__main__":
    matched_cues = return_matched(reviewed_tsv_path)
    # count check for the matched cues.
    if len(matched_cues) != EXPECTED_COUNT:
        raise ValueError(f"expected {EXPECTED_COUNT} but got {len(matched_cues)}")
    umr_records = read_umr_file(umr_portuguese_path)
    pud_dicts = dict_return(pud_portuguese_path)
    kept_records = filter_records(matched_cues, umr_records)
    # count check for the filtered records.
    if len(kept_records) != EXPECTED_COUNT:
        raise ValueError(f"expected {EXPECTED_COUNT} but got {len(kept_records)}")
    records_with_english = attach_english(kept_records, matched_cues, pud_dicts)
    for record in records_with_english:
        if not record["target_text"]:
            raise ValueError(f"The matched case's record {record['sentence_id']} has an empty target_text")
    # check for repeated pud_id
    pud_ids = []
    for record in records_with_english:
        pud_ids.append(record["pud_id"])
    if len(set(pud_ids)) != len(kept_records):
        raise ValueError("The kept matched records have duplicate pud_ids")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records_with_english:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Saved {len(records_with_english)} records to {output_path}")
    
