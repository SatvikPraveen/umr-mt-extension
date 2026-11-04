"""Cleanly merge the interim language pairs, add uids and check the records."""
from pathlib import Path
import json
from collections import Counter
import hashlib
from umr_mt.prompting.demonstrations import nearest_neighbours

# Paths for interim output per language and the corresponding output.
czech_path = Path("data/interim/czech_pairs.jsonl")
latin_path = Path("data/interim/latin_pairs.jsonl")
portuguese_path = Path("data/interim/portuguese_pairs.jsonl")
output_folder = Path("data/processed/")

output_file = output_folder / "pairs_with_demos.jsonl"

EXPECTED_TOTAL = 4059

def read_jsonl(path):
    """Read the file and provide the content as a list."""
    with open(path, "r", encoding="utf-8") as f:
        content_list = [json.loads(line) for line in f if line.strip()]
    return content_list

def attach_uid(content_list):
    """Attach uid to the record in the content list."""
    for record in content_list:
        record["uid"] = f"{Path(record["file"]).stem}:{record["position"]}"

def extract_uid(content_list):
    """Extract attached uids from the records."""
    uids = []
    for record in content_list:
        uids.append(record["uid"])
    return uids

def check_if_empty(content_list):
    """Check if the crucial source text, target text or the graph is empty."""
    for record in content_list:
        for key in ("source_text", "target_text", "graph"):
            if not record[key]:
                raise ValueError(f"Key: {key} is empty for the record: {record["uid"]}")

def check_graph(content_list):
    """The graph has been linearized. Checks if the graph contains any new line character."""
    for record in content_list:
        if "\n" in record["graph"]:
            raise ValueError(f"Graph has new line character in {record["uid"]}")


def organize_demos(demo_dict):
    """organizing demos for easy attachment"""
    demo_organize = {}
    for uid, demos in demo_dict.items():
        demo_uid_list = []
        demo_scores_list = []
        for demo_score, demo_uid in demos:
            demo_uid_list.append(demo_uid)
            demo_scores_list.append(demo_score)
        demo_organize[uid] = (demo_uid_list, demo_scores_list)

    return demo_organize
            
            
def attach_demos(records, demo_organize):
    """Attach demos to the records"""
    for record in records:
        record["demo_uids"] = demo_organize[record["uid"]][0]
        record["demo_scores"] = demo_organize[record["uid"]][1]


def check_demos(records):
    """Check if each record has 5 demo_uid"""
    for record in records:
        if len(record["demo_uids"]) != 5:
            raise ValueError(f"Record {record["uid"]} expected 5, but got {len(record["demo_uids"])} demos !!!")
        if record["uid"] in record["demo_uids"]:
            raise ValueError(f"Record {record["uid"]} has its own id in the demo ids !!!")


if __name__ == "__main__":
    czech_records = read_jsonl(czech_path)
    attach_uid(czech_records)
    latin_records = read_jsonl(latin_path)
    attach_uid(latin_records)
    portuguese_records = read_jsonl(portuguese_path)
    attach_uid(portuguese_records)
    combined_list = czech_records + latin_records + portuguese_records
    if len(combined_list) != EXPECTED_TOTAL:
        raise ValueError(f'Expected {EXPECTED_TOTAL} but got {len(combined_list)}')

    # uid uniqueness
    combined_set_uid = set(extract_uid(combined_list))

    if len(combined_set_uid) != len(combined_list):
        raise ValueError(f"{len(combined_set_uid)} unique uids for {len(combined_list)} records")

    check_if_empty(combined_list)

    check_graph(combined_list)

    count_cases = Counter(c["language"] for c in combined_list)

    latin_demos = nearest_neighbours(latin_records)
    portuguese_demos = nearest_neighbours(portuguese_records)
    czech_demos = nearest_neighbours(czech_records)

    latin_demos_organized = organize_demos(latin_demos)
    portuguese_demos_organized = organize_demos(portuguese_demos)
    czech_demos_organized = organize_demos(czech_demos)

    attach_demos(latin_records, latin_demos_organized)
    attach_demos(portuguese_records, portuguese_demos_organized)
    attach_demos(czech_records, czech_demos_organized)

    print(count_cases)
    print(latin_records[0]["demo_uids"])
    print(portuguese_records[0]["demo_uids"])

    check_demos(latin_records)
    check_demos(portuguese_records)
    check_demos(czech_records)


    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for record in combined_list:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Saved {len(combined_list)} records to {output_file}")

    digest = hashlib.sha256(output_file.read_bytes()).hexdigest()
    line = f"{digest}  {output_file.name}\n"
    (output_folder / "SHA256SUMS").write_text(line, encoding="utf-8")
    print(line, end="")
