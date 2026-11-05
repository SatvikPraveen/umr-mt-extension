"""Measure prompt lengths in characters and in tokens for different candidate models for each case under different protocols"""

import json
from pathlib import Path
from build_prompts_file import verify_sha
from umr_mt.prompting.templates import PROTOCOLS
from collections import defaultdict
import statistics

from transformers import AutoTokenizer

# room for sentence's translation and a cap on the runaway output.
MAX_NEW_TOKENS = 256

prompts_file = Path("data/processed/prompts.jsonl")
sha_file = Path("data/processed/SHA256SUMS")

# candidates considered for model selection
# revisions pinned for reproducibility
CANDIDATES = {"olmo2_13b": { 
                "hf_id": "allenai/OLMo-2-1124-13B-Instruct",
                "revision": "3a5c85baefbb1896a54d56fe2e76c0395627ddf4",
                "context_length": 4096,
                "options": {}
              },
              "eurollm_9b": { 
                "hf_id": "utter-project/EuroLLM-9B-Instruct",
                "revision": "f7ae2bc3bcbb538c0b93fa6cfbf388d9898b1ace",
                "context_length": 4096,
                "options": {}
              },
              "aya_expanse_8b": { 
                "hf_id": "CohereLabs/aya-expanse-8b",
                "revision": "5062468bf9bc0c6035fd64e06274333ec127d980",
                "context_length": 8192,
                "options": {}
              },
              "qwen3_8b": { 
                "hf_id": "Qwen/Qwen3-8B",
                "revision": "b968826d9c46dd6066d109eabc6255188de91218",
                "context_length": 32768,
                "options": {"enable_thinking": False}
              },
              "gemma3_12b": { 
                "hf_id": "google/gemma-3-12b-it",
                "revision": "96b6f1eccf38110c56df3a15bffe176da04bfd80",
                "context_length": 131072,
                "options": {}
              },
}




if __name__ == "__main__":
    stored_lines = sha_file.read_text()
    sha_dict = {}
    for line in stored_lines.splitlines():
        line_content_list = line.split()
        sha_dict[line_content_list[1]] = line_content_list[0]

    # measurements are only valid for pinned prompt file
    verify_sha(prompts_file, sha_dict[prompts_file.name])

    with open(prompts_file, "r", encoding="utf-8") as f:
        prompt_list = [json.loads(line) for line in f if line.strip()]
    # Part1: model independent character-lengths
    char_length_list = []
    for prompt in prompt_list:
        char_length_list.append(((prompt["protocol"], prompt["language"]), len(prompt["messages"][0]["content"] + prompt["messages"][1]["content"])))
    groups = defaultdict(list)

    for k, v in char_length_list:
        groups[k].append(v)

    languages = ("czech", "latin", "portuguese")

    keys = [(protocol, language) for protocol in PROTOCOLS for language in languages]
    print("Character lengths for each protocol case in each languages")
    print(f"{'protocol':15} {'language':12} {'median':>7} {'max':>7}")
    for key in keys:
        median = round(statistics.median(groups[key]))
        maximum = max(groups[key])
        print(f"{key[0]:15} {key[1]:12} {median:>7} {maximum:>7}")

    print()
    
    # Part2: token lengths per candidate tokenizer (context limits are in tokens)
    for name, cfg in CANDIDATES.items():
        tokenizer = AutoTokenizer.from_pretrained(cfg["hf_id"], revision=cfg["revision"])

        # context must hold the prompts and the answers together.
        budget = cfg["context_length"] - MAX_NEW_TOKENS 
        token_length_list = []

        for prompt in prompt_list:
            # transformers 5.x returns a dict when tokenize=True. The `return_dict=False` gives the token list for len()
            n_tokens = len(tokenizer.apply_chat_template(prompt["messages"], add_generation_prompt=True, tokenize=True, **cfg["options"], return_dict=False))
            token_length_list.append(((prompt["protocol"], prompt["language"]), n_tokens))

        token_groups = defaultdict(list)

        for k, v in token_length_list:
            token_groups[k].append(v)
    
        print(f"{name}  context={cfg['context_length']}  budget={budget}", "="*150, sep="\n")

        total_over = 0
        print(f"{'protocol':15} {'language':12} {'median':>7} {'max':>7} {'over':>6}")

        for key in keys:
            median = round(statistics.median(token_groups[key]))
            maximum = max(token_groups[key])
            over = sum(1 for n in token_groups[key] if n > budget)
            total_over += over
            print(f"{key[0]:15} {key[1]:12} {median:>7} {maximum:>7} {over:>6}")

        print(f"over budget: {total_over} of {len(prompt_list)}")
        print()