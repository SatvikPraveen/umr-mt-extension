"""Process the raw outputs obtained from the model."""
import json
from pathlib import Path
import re

raw_output_folder = Path("outputs/raw")
LEAKAGE_PATTERNS = [r":[A-Za-z]\w*", r"(\(\w+\s/\s)", r"refer-(number|person)",  r"(full|partial|neutral)-(affirmative|negative)"]

def clean_output(raw):
    """Clean the raw outputs of the models under different protocols."""
    text = raw.strip()
    pattern = r"^\s*English\s*:\s*"
    text = re.sub(pattern, "", text, count=1, flags=re.IGNORECASE)
    text = text.split("\n", 1)[0]
    return text.strip()


def has_umr_leakage(text):
    """States whether the graph notation got copied into the translation."""
    return any(re.search(p, text) for p in LEAKAGE_PATTERNS)


def process_record(record):
    """Processed record with additional fields without the changes made to the existing ones."""
    clean = clean_output(record["text"])
    return {**record, "clean_text": clean, "empty": clean == "", "umr_leak": has_umr_leakage(record["text"])}

if __name__ == "__main__":
    clean = clean_output("English: The cat")
    print(repr(clean))
    clean = clean_output("\n English: The cat sat.\nNote: literal.")
    print(repr(clean))
    clean = clean_output("The cat sat.")
    print(repr(clean))
    clean = clean_output("The English: section.")
    print(repr(clean))
    clean = clean_output("")
    print(repr(clean))
    print(repr(has_umr_leakage("All people should strive.")))
    print(repr(has_umr_leakage("Fees 1 3/4.")))
    print(repr(has_umr_leakage("Meeting at 10:30.")))
    print(repr(has_umr_leakage("(s1 / say-01 :modal-strength full-affirmative)")))