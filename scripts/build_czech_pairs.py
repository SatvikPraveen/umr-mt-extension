from umr_mt.data.ptb_reader import read_ptb_file
from umr_mt.data.umr_reader import read_umr_file
from pathlib import Path
import json
import re

# paths to the relevant files and data
umr_mapping_file = Path("data/raw/umr_v3.0_ae46502/umr_file_name_mapping.txt")
umr_data_path = Path("data/raw/umr_v3.0_ae46502")
treebank_data_path = Path("data/raw/ptb_nltk_sample/combined")

output_file = Path("data/interim/czech_pairs.jsonl")

def read_umr_mapping_file(umr_mapping_file: Path):
    with open(umr_mapping_file, "r", encoding="utf-8") as f:
        return f.read()

def find_czech_wsj_files(mapping_file_content):
    pairs = []
    for line in mapping_file_content.splitlines():
        line = line.strip()
        original, release = line.split("\t")
        original = original.strip()
        release = release.strip()
        original_rec = re.search(r"czech_wsj(\d{4})\.cz\.umr", original)
        if original_rec and int(original_rec.group(1)) <= 199:
            original_id = original_rec.group(1)
            pairs.append((original_id, umr_data_path/release))
    return pairs

# def check_count(pairs):
#     for pair in pairs:
#         czech_records = read_umr_file(pair[1])
#         english_records = read_ptb_file(treebank_data_path/f"wsj_{pair[0]}.mrg")
#         if len(czech_records) != len(english_records):
#             print(f"Mismatch in count for {pair[1]} and {treebank_data_path/f'wsj_{pair[0]}.mrg'}")
#             return False
#     return True

def pair_english_czech(pairs):
    list_of_pairs = []
    for wsj, czech_path in pairs:
        czech_records = read_umr_file(czech_path)  # list of records
        english_records = read_ptb_file(treebank_data_path/f"wsj_{wsj}.mrg")  # dictionary of records
        if len(czech_records) != len(english_records):
            raise ValueError(f"Mismatch in count for {len(czech_records)} and {len(english_records)} for {czech_path} and {treebank_data_path/f'wsj_{wsj}.mrg'}")
        for record in czech_records:
            record["target_text"] = english_records[record["position"]]["text"]
            record["wsj"] = wsj
            list_of_pairs.append(record)
    return list_of_pairs
                


if __name__ == "__main__":
    mapping_file_content = read_umr_mapping_file(umr_mapping_file)
    pairs = find_czech_wsj_files(mapping_file_content)
    records = pair_english_czech(pairs)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Saved {len(records)} records to {output_file}")