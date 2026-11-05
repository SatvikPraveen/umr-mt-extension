"""Build the chat messages (system + user) for a record under four protocols."""

from umr_mt.prompting.templates import (SYSTEM_PROMPT, INSTRUCTION, INSTRUCTION_UMR, 
                                        SOURCE_LINE, UMR_LINE, ANSWER_CUE, DEMO_LINE, DEMO_LINE_UMR, 
                                        LANGUAGE_NAMES, PROTOCOLS)



def build_messages(record, demo_records, protocol):
    if protocol not in PROTOCOLS:
        raise ValueError(f"Invalid Protocol: {protocol}.")
    
    use_umr = "umr" in protocol

    language = LANGUAGE_NAMES[record["language"]]
    
    system = SYSTEM_PROMPT.format(language=language)

    if use_umr:
        instruction = INSTRUCTION_UMR.format(language=language)
    else:
        instruction = INSTRUCTION.format(language=language)

    lines = [instruction]   

    if protocol.startswith("five_shot"):
        for demo in demo_records[::-1]:
            if not use_umr:
                demo_line = DEMO_LINE.format(language=language, sentence=demo["source_text"], translation=demo["target_text"], graph=demo["graph"])
            else:
                demo_line = DEMO_LINE_UMR.format(language=language, sentence=demo["source_text"], translation=demo["target_text"], graph=demo["graph"])
            lines.append(demo_line)
        lines.append(instruction)
    source_line = SOURCE_LINE.format(language=language, sentence=record["source_text"])
    lines.append(source_line)

    if use_umr:
        umr_graph = UMR_LINE.format(graph=record["graph"])
        lines.append(umr_graph)
    lines.append(ANSWER_CUE)

    user_message = "\n".join(lines)
    message_list = [{"role": "system", "content": system}, {"role": "user", "content": user_message}]
    return message_list


if __name__ == "__main__":
    import json
    from pathlib import Path
    processed_pair_with_demos = Path("data/processed/pairs_with_demos.jsonl")
    with open(processed_pair_with_demos, "r", encoding="utf-8") as f:
        content_list = [json.loads(line) for line in f if line.strip()]
    lookup_dict = {record["uid"]: record for record in content_list}

    latin_test_record = next(r for r in content_list if r["language"] == "latin")

    demo_record_list = [lookup_dict[demo_uid] for demo_uid in latin_test_record["demo_uids"]]
    for protocol in PROTOCOLS:
        message = build_messages(latin_test_record, demo_record_list, protocol)
        print(f"Protocol: {protocol}")
        print("="*150)
        print(message[0]["content"], message[1]["content"], sep="\n")

