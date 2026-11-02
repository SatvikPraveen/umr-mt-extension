"""UMR file reader"""
from pathlib import Path
import re
import penman

# Read the file
def read_file(file_path):
    """Read the file at path and return the content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# Split the file into blocks
def split_blocks(content):
    """Split the blocks from the content."""
    sep = "#"*80
    blocks = content.split(sep)
    return [block.strip() for block in blocks if block.strip()]

# Split the block into sections
def split_sections(block):
    """Split the sections from the block."""
    sections = {}
    current_section = None
    for line in block.splitlines():
        if line.startswith("# ::"):
            current_section = "sentence_info"
            sections[current_section] = []
        elif line.startswith("#"):
            current_section = line.split(":")[0].lstrip("#").strip()
            if current_section == "meta-info":
                current_section = "sentence_id"
                sent_id_candidate = line.split("::")
                for s in sent_id_candidate:
                    s = s.strip()
                    if s.startswith("sent_id ="):
                        sent_id = s.split("=")[1].strip()
                        sections[current_section] = sent_id
                        break
            else:
                sections[current_section] = []
        else:
            if line.strip():
                sections[current_section].append(line.strip())
    return sections


# Parse the sentence info
def sentence_info_parser(sentence_info):
    """Parse the sentence info as a dictionary."""
    info = {}
    for item in sentence_info:
        key, sep, value = item.partition(":")
        info[key.strip()] = value.strip()
    return info

# Linearize the graph
def build_graph(graph_info):
    """Join the graph lines into a single string."""
    graph = " ".join(graph_info)
    graph = quote_invalid_penman_concepts(graph)
    return graph

# Build the record - every record should have a specific format
def record_builder(file_path, sections, position,sentence_info):
    """Build the record.
    A dictionary with the following keys:
    - sentence_id: the sentence id
    - language: the language of the sentence
    - file: the file name
    - position: the position of the sentence in the file
    - source_key: the key of the source text
    - source_text: the source text
    - target_text: the target text
    - graph: the graph of the sentence
    """
    sentence_id = sections["sentence_id"]
    file_path = Path(file_path)
    file = file_path.name
    language = file_path.stem.split("_")[0]
    graph = build_graph(sections["sentence level graph"])
    source_key = "Sentence" if "Sentence" in sentence_info else "Words"
    record = {
        "sentence_id": sentence_id,
        "language": language,
        "file": file,
        "position": position,
        "source_key": source_key,
        "source_text": sentence_info[source_key],
        "target_text": sentence_info.get("Translation(English)", None),
        "graph": graph,
    }
    return record

# Read the UMR file and return the records
def read_umr_file(file_path):
    """Read the file and return the records."""
    content = read_file(file_path)
    blocks = split_blocks(content)
    records = []
    for position, block in enumerate(blocks):
        sections = split_sections(block)
        sentence_info = sentence_info_parser(sections["sentence_info"])
        record = record_builder(file_path, sections, position, sentence_info=sentence_info)
        records.append(record)
    return records


# Function to check if a concept is valid for Penman
def is_valid_penman_concept(concept):
    """Returns True if the concept is valid for Penman."""
    try:
        penman.decode(f"( c / {concept})")
    except Exception:
        return False
    return True


# Quote invalid Penman concepts
def quote_invalid_penman_concepts(graph):
    """Wraps the concepts not valid for Penman in quotes."""
    special_concepts = set()
    concepts = re.findall(r"/ ([^\s()]+)", graph)
    for concept in concepts:
        if not is_valid_penman_concept(concept):
            special_concepts.add(concept)
    func = lambda x: '/ "' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
    for concept in special_concepts:
        graph = re.sub(r"/ " + re.escape(concept) + r"(?=[\s)])", func(concept), graph)
    return graph


# Verification of the UMR file
def check_umr_file(path):
    """Check the UMR file."""
    language_records = read_umr_file(path)
    decode_count = 0
    translation_count = 0
    for record in language_records:
        try:
            penman.decode(record['graph'])
            decode_count += 1
        except Exception as e:
            print(e)
        if record['target_text'] is not None:
            translation_count += 1
        
    number_of_records = len(language_records)
    return {"decode_count": decode_count, "translation_count": translation_count, "number_of_records": number_of_records}


if __name__ == "__main__":
    latin_file_path = 'data/raw/umr_v3.0_ae46502/latin/umr_data/latin_umr-0001.umr'
    portuguese_file_path = 'data/raw/umr_v3.0_ae46502/portuguese/umr_data/portuguese_umr-0001.umr'
    czech_file_path = 'data/raw/umr_v3.0_ae46502/czech/umr_data/czech_umr-4776.umr'

    latin_record_details = check_umr_file(latin_file_path)
    portuguese_record_details = check_umr_file(portuguese_file_path)
    czech_record_details = check_umr_file(czech_file_path)

    print(f"Latin    records: {latin_record_details["number_of_records"]}    translations: {latin_record_details["translation_count"]}    decode: {latin_record_details["decode_count"]}")
    print(f"Portuguese    records: {portuguese_record_details["number_of_records"]}    translations: {portuguese_record_details["translation_count"]}    decode: {portuguese_record_details["decode_count"]}")
    print(f"czech    records: {czech_record_details["number_of_records"]}    translations: {czech_record_details["translation_count"]}    decode: {czech_record_details["decode_count"]}")

    
