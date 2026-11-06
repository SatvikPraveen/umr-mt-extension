"""Load a model at a pinned revision and generate greedy translations for a batch of chat prompts."""

import torch
from transformers import AutoTokenizer 
from transformers import AutoModelForCausalLM

def load_model(cfg, dtype):
    """Load the model and tokenizer at the pinned revision, bf16 and left padding."""
    tokenizer = AutoTokenizer.from_pretrained(cfg["hf_id"], revision=cfg["revision"], padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(cfg["hf_id"], revision=cfg["revision"], dtype=dtype, device_map="auto")
    model.eval()
    return tokenizer, model




def generate_batch(model, tokenizer, messages_list, template_options, generation):
    """generate greedy translations for a batch of prompts and return one record per prompt"""
    prompt_list = [tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False, **template_options) for messages in messages_list]

    inputs = tokenizer(prompt_list, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)

    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=generation["max_new_tokens"], do_sample=generation["do_sample"])
    width = inputs["input_ids"].shape[1]
    new = out[:, width:]
    texts = tokenizer.batch_decode(new, skip_special_tokens=True)
    n_new_tokens = (new != tokenizer.pad_token_id).sum(dim=1).tolist()

    hit_cap = [i == generation["max_new_tokens"] for i in n_new_tokens]

    prompt_record = [{"text": t, "n_new_tokens": n, "hit_cap": h} for t, n, h in zip(texts, n_new_tokens, hit_cap)]
    return prompt_record

    
    

if __name__ == "__main__":
    pass