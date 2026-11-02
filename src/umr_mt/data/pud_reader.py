"""Reader for the PUD format files."""

def read_pud(file_path):
    """Read the PUD file and return the content."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def split_blocks(content):
    """Split the content into blocks."""
    sep = "\n\n"
    blocks = content.split(sep)
    return [block.strip() for block in blocks if block.strip()]

def split_sections(block):
    """Split the block into sections."""
    sections = {}
    for line in block.splitlines():
        if line.startswith("#"):
            key, sep, value = line.partition(" = ")
            if sep:
                sections[key.lstrip("#").strip()] = value.strip()
    return sections

def dict_return(file_path):
    """Return a dictionary of the sections."""
    content = read_pud(file_path)
    blocks = split_blocks(content)
    dict_representation = {}
    for block in blocks:
        sections = split_sections(block)
        dict_representation[sections["sent_id"]] = {key:values for key, values in sections.items()}
    return dict_representation


if __name__ == "__main__":
    pt_file_path = "data/raw/ud_portuguese_pud_0fdcc05/pt_pud-ud-test.conllu"
    en_file_path = "data/raw/ud_english_pud_f16eba4/en_pud-ud-test.conllu"
    pt_dict = dict_return(pt_file_path)
    en_dict = dict_return(en_file_path)
    print(pt_dict)
    print(en_dict)