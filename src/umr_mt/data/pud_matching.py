"""Matching Portuguese in the Portuguese UMR and Portuguese PUD to obtain a credible english reference."""

from umr_mt.data.umr_reader import read_umr_file
from umr_mt.data.pud_reader import dict_return
from pathlib import Path
import re
import difflib
import csv

portuguese_umr_path = Path("data/raw/umr_v3.0_ae46502/portuguese/umr_data/portuguese_umr-0001.umr")
portuguese_pud_path = Path("data/raw/ud_portuguese_pud_0fdcc05/pt_pud-ud-test.conllu")
output_path = Path("data/interim/portuguese_pud_matches.tsv")

def normalize(text):
    """Normalize the texts: lower case and remove non-word characters."""

    text = text.lower()
    text = re.sub(r'[\W_]', "", text)
    return text


def best_match(umr_record, pud_dict):
    """For each UMR records and pud dicts as inputs. Finds the PUD sentence with the highest difflib ratio on normalized text. 
    Outputs a list of tuples with 5 information with both the ids, score, and both the texts."""

    match_list = []
    for record in umr_record:
        max_match = 0
        win_sent_id = None
        win_text_pud = None
        text_record = normalize(record["source_text"])
        for sent_id, val in pud_dict.items():
            text_pud = normalize(val["text"])
            match_score = difflib.SequenceMatcher(None, text_record, text_pud).ratio()
            if match_score > max_match:
                max_match = match_score
                win_sent_id = sent_id
                win_text_pud = val["text"]
        rec_sentence_id = record["sentence_id"]
        rec_source_text = record["source_text"]

        match_list.append((rec_sentence_id, win_sent_id, max_match, rec_source_text, win_text_pud))
    return match_list
        

if __name__ == "__main__":
    portuguese_umr_records = read_umr_file(portuguese_umr_path)
    portuguese_pud_dict = dict_return(portuguese_pud_path)
    result = best_match(portuguese_umr_records, portuguese_pud_dict)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(('umr_id', 'pud_id', 'score', 'umr_text', 'pud_text', 'pud_text_en', 'verdict'))
        new_list = []
        for umr_id, pud_id, score, umr_text, pud_text in result:
            new_list.append((umr_id, pud_id, round(score, 5), umr_text, pud_text, portuguese_pud_dict[pud_id]["text_en"], ''))
        for row in sorted(new_list, key = lambda r: r[2], reverse=True):
            writer.writerow(row)




   