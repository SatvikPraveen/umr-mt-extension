"""Build all the prompts required for the project before hand."""
import hashlib
from umr_mt.prompting.build_prompts import build_messages
from umr_mt.prompting.templates import PROTOCOLS
from pathlib import Path
import json


processed_data_file = Path("data/processed/pairs_with_demos.jsonl")
sha_file = Path("data/processed/SHA256SUMS")
output_prompt_file = Path("data/processed/prompts.jsonl")
output_folder = Path("data/processed")

def verify_sha(test_file, stored_sha):
    test_sha = hashlib.sha256(test_file.read_bytes()).hexdigest()
    if test_sha != stored_sha:
        raise ValueError(f"Expected {stored_sha} got {test_sha}")


if __name__ == "__main__":
    stored_lines = sha_file.read_text()
    sha_dict = {}
    for line in stored_lines.splitlines():
        line_content_list = line.split()
        sha_dict[line_content_list[1]] = line_content_list[0]

    verify_sha(processed_data_file, sha_dict[processed_data_file.name])

    with open(processed_data_file, "r", encoding="utf-8") as f:
        content_list = [json.loads(line) for line in f if line.strip()]
    
    lookup_dict = {record["uid"]: record for record in content_list}

    prompts = []
    for record in content_list:
        demos = [lookup_dict[u] for u in record["demo_uids"]]
        
        for protocol in PROTOCOLS:
            prompt_dict = {}
            prompt_dict["prompt_id"] = f"{record['uid']}|{protocol}"
            prompt_dict["uid"] = record["uid"]
            prompt_dict["language"] = record["language"]
            messages = build_messages(record, demos, protocol)
            prompt_dict["protocol"] = protocol
            prompt_dict["messages"] = messages
            prompts.append(prompt_dict)

    # length check
    EXPECTED_LENGTH = len(PROTOCOLS) * len(content_list)
    if len(prompts) != EXPECTED_LENGTH:
        raise ValueError(f"Expected {EXPECTED_LENGTH} but got {len(prompts)}")

    # uniqueness check
    prompt_ids = set([prompt["prompt_id"] for prompt in prompts])
    if len(prompt_ids) != EXPECTED_LENGTH:
        raise ValueError(f"Expected {EXPECTED_LENGTH} got {len(prompt_ids)}")

    # adding prompts to the file in the data/processed
    with open(output_prompt_file, "w", encoding="utf-8") as f:
        for prompt in prompts:
            f.write(json.dumps(prompt, ensure_ascii=False) + "\n")

    print(f"Saved {len(prompts)} records to {output_prompt_file}")

    sha_dict[output_prompt_file.name] = hashlib.sha256(output_prompt_file.read_bytes()).hexdigest()

    collect_lines = []
    for filename, hash_val in sha_dict.items():
        line = f"{hash_val}  {filename}\n"
        collect_lines.append(line)
    lines = "".join(collect_lines)
    (output_folder / "SHA256SUMS").write_text(lines, encoding="utf-8")
    print(lines, end="")



