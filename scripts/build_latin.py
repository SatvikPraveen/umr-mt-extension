from umr_mt.data.umr_reader import read_umr_file
from pathlib import Path
import json

# paths to the relevant files and data
umr_data_path = Path("data/raw/umr_v3.0_ae46502/latin/umr_data/latin_umr-0001.umr")
output_file = Path("data/interim/latin_pairs.jsonl")

def check_latin_target_text(umr_data_path: Path):
    records = read_umr_file(umr_data_path)
    for record in records:
        if record["target_text"] is None or record["target_text"] == "":
            raise ValueError(f"Target text is None or empty for {record['position']} in file {umr_data_path}")
    return records

if __name__ == "__main__":
    records = check_latin_target_text(umr_data_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Saved {len(records)} records to {output_file}")