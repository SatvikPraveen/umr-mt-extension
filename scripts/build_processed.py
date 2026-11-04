"""Cleanly merge the interim language pairs, add uids and check the records."""
from pathlib import Path
import json
from collections import Counter

# Paths for interim output per language and the corresponding output.
czech_path = Path("data/interim/czech_pairs.jsonl")
latin_path = Path("data/interim/latin_pairs.jsonl")
portuguese_path = Path("data/interim/portuguese_pairs.jsonl")
output_folder = Path("data/processed/")


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
    return content_list

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


if __name__ == "__main__":
    czech_content = read_jsonl(czech_path)
    czech_content_uid = attach_uid(czech_content)
    latin_content = read_jsonl(latin_path)
    latin_content_uid = attach_uid(latin_content)
    portuguese_content = read_jsonl(portuguese_path)
    portuguese_content_uid = attach_uid(portuguese_content)
    combined_list = czech_content_uid + latin_content_uid + portuguese_content_uid
    if len(combined_list) != EXPECTED_TOTAL:
        raise ValueError(f'Expected {EXPECTED_TOTAL} but got {len(combined_list)}')

    # uid uniqueness
    combined_set_uid = set(extract_uid(combined_list))

    if len(combined_set_uid) != len(combined_list):
        raise ValueError(f"{len(combined_set_uid)} unique uids for {len(combined_list)} records")

    check_if_empty(combined_list)

    check_graph(combined_list)

    count_cases = Counter(c["language"] for c in combined_list)
    print(count_cases)


