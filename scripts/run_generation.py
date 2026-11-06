"""Run generations for a model with selected protocols, languages, batch size."""

import argparse
from pathlib import Path
import json
import yaml
import time
from build_prompts_file import verify_sha
from umr_mt.prompting.templates import PROTOCOLS, LANGUAGE_NAMES
from umr_mt.models.generate import load_model, generate_batch

prompts_file_path = Path("data/processed/prompts.jsonl")
configuration_file_path = Path("configs/models.yaml")
sha_file_path = Path("data/processed/SHA256SUMS")

raw_folder = Path("outputs/raw")

with open(configuration_file_path, 'r', encoding="utf-8") as f:
        config = yaml.safe_load(f)

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True, choices=list(config["models"]), help="short name from configs/models.yaml")
parser.add_argument("--protocols", type=str, nargs="+", default=list(PROTOCOLS), choices=PROTOCOLS,  help="at least one protocol name")
parser.add_argument("--languages", type=str, nargs="+", default=list(LANGUAGE_NAMES), choices=LANGUAGE_NAMES, help="at least one of the languages name")
parser.add_argument("--batch-size", type=int, default=8, help="provide intended batch-size, default is 8")
parser.add_argument("--limit", type=int, default=None, help="add the limit to which you intend to generate the prompts")


if __name__ == "__main__":
    args = parser.parse_args()
    
    sha_dict = {}
    for line in sha_file_path.read_text().splitlines():
        line_content_list = line.split()
        sha_dict[line_content_list[1]] = line_content_list[0]

    prompts_filename = prompts_file_path.name
    verify_sha(prompts_file_path, sha_dict[prompts_filename])
    
    with open(prompts_file_path, "r", encoding="utf-8") as f:
        prompt_content = [json.loads(line) for line in f]

    required_prompts = [prompt for prompt in prompt_content if prompt["protocol"] in args.protocols and prompt["language"] in args.languages]
    print(f"Requested number of prompts: {len(required_prompts)}")

    model_folder = raw_folder / args.model / f"bs{args.batch_size}"
    model_folder.mkdir(parents=True, exist_ok=True)
    done = set()

    for protocol in args.protocols:
        path = model_folder/f"{protocol}.jsonl"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = [json.loads(line) for line in f if line.strip()]

            for record in content:
                done.add(record["prompt_id"])
            
    todo = [p for p in required_prompts if p["prompt_id"] not in done]
    if args.limit is not None: 
        todo = todo[:args.limit]
    print(f"requested: {len(required_prompts)}, done: {len(done)}, todo: {len(todo)}")

    if not todo:
        raise SystemExit("nothing to do: all requested prompts already generated.")

    cfg = config["models"][args.model]
    tokenizer, model = load_model(cfg, config["dtype"])

    t0 = time.perf_counter()
    n_written = 0
    n_capped = 0

    for protocol in args.protocols:
        protocol_todo = [p for p in todo if p["protocol"] == protocol]
        
        if not protocol_todo:
            continue

        path = model_folder / f"{protocol}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            for start in range(0, len(protocol_todo), args.batch_size):
                t_batch = time.perf_counter()
                batch = protocol_todo[start:start+args.batch_size]
                results = generate_batch(model, tokenizer, [p["messages"] for p in batch], cfg["template_options"], config["generation"])
                if len(results) != len(batch):
                    raise ValueError(f"Expected {len(batch)} results but got {len(results)}!!!")
                for p,r in zip(batch, results):
                    n_written += 1
                    n_capped += r["hit_cap"]

                    record = {
                        "prompt_id": p["prompt_id"],
                        "uid": p["uid"],
                        "language": p["language"],
                        "protocol": p["protocol"],
                        "model": args.model, 
                        "revision": cfg["revision"],
                        "text": r["text"],
                        "n_new_tokens": r["n_new_tokens"],
                        "hit_cap": r["hit_cap"]
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                print(f"{protocol}: {start + len(batch)}/{len(protocol_todo)}  {time.perf_counter() - t_batch:.1f}s/batch", flush=True)

    print(f"done: {n_written} written, {n_capped} hit the cap, {time.perf_counter() - t0:.0f}s total", flush=True)

