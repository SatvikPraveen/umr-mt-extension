"""selection of k-nearest-neighbour demonstrations"""
from sacrebleu.metrics import CHRF

def nearest_neighbours(records, k=5):
    """k nearest neighbors by chrf scores on source text. The records are of one language. Record itself is excluded by one uid."""
    chrf = CHRF()
    result = {}
    for query in records:
        scores = []
        for candidate in records:
            if query["uid"] != candidate["uid"]:
                score = chrf.sentence_score(candidate["source_text"], [query["source_text"]]).score
                scores.append((score, candidate["uid"]))
        scores.sort(key=lambda x: (-x[0], x[1]))
        result[query["uid"]] = scores[:k]
    return result
