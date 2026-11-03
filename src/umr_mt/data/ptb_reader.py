"""reader for the Penn Treebank dataset"""
import re
import nltk
from pathlib import Path

def read_ptb(file_path):
    """Read the content of the file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def split_trees(content):
    """Split the content into trees"""
    trees = []
    depth = 0
    start = None
    for i, ch in enumerate(content):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                trees.append(content[start:i+1])
                start = None
    return trees

def extract_leaves(tree):
    """Extract the leaves from the trees"""
    leaves = re.findall(r'\(([^\s()]+) ([^\s()]+)\)', tree)
    return leaves

def clean_words(leaves):
    """Clean the words from the leaves"""
    words = []
    # Penn Treebank tokenization conventions" (http://web.archive.org/web/20161125152428/http://www.cis.upenn.edu:80/~treebank/tokenization.html)
    conversion_table = {
        "-LRB-": "(",
        "-RRB-": ")",
        "-LCB-": "{",
        "-RCB-": "}",
        "-LSB-": "[",
        "-RSB-": "]",
    }
    for tag, word in leaves:
        if tag != "-NONE-":
            word = conversion_table.get(word, word)
            word = word.replace("\\/", "/")
            words.append(word)
    return words



detokenizer = nltk.tokenize.treebank.TreebankWordDetokenizer()
def detokenize(words):
    """Detokenize the words"""
    return detokenizer.detokenize(words)


def record_builder(path,position, detokenized):
    """Build the record"""
    path = Path(path)
    number = path.stem.split("_")[1]
    return {
        "wsj": number,
        "position": position,
        "text": detokenized,
    }

def read_ptb_file(file_path):
    """Read the PTB file"""
    content = read_ptb(file_path)
    trees = split_trees(content)
    records = {}
    for position, tree in enumerate(trees):
        leaves = extract_leaves(tree)
        words = clean_words(leaves)
        detokenized = detokenize(words)
        record = record_builder(file_path, position, detokenized)
        records[position] = record
    return records

if __name__ == "__main__":
    file_path = "data/raw/ptb_nltk_sample/combined/wsj_0003.mrg"
    content_records = read_ptb_file(file_path)
    print(content_records)