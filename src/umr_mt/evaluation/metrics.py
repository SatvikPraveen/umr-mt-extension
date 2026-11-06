"""Calculate chrf and bert scores on the model output."""
from sacrebleu.metrics import CHRF
import bert_score

def chrf_scores(hypotheses, references):
    """Per sentence chrf scores."""
    output_list = []
    chrf = CHRF()
    if len(hypotheses) != len(references):
        raise ValueError(f"Hypotheses are {len(hypotheses)} in number while references are {len(references)} in number.")
    for hypothesis, reference in zip(hypotheses, references):
        score = chrf.sentence_score(hypothesis, [reference]).score
        output_list.append(score)
    signature = str(chrf.get_signature())
    return output_list, signature

def bertscore_f1(hypotheses, references):
    """Per sentence BERTScore F1"""
    if len(hypotheses) != len(references):
        raise ValueError(f"Hypotheses are {len(hypotheses)} in number while references are {len(references)} in number.")
    (P, R, F1), bs_hash = bert_score.score(hypotheses, references, lang="en", return_hash=True)
    return F1.tolist(), bs_hash


if __name__ == "__main__":
    print(chrf_scores(["The cat sat.", "Hello world"], ["The cat sat.", "A dog ran away"]))
    print(bertscore_f1(["The cat sat.", "Hello world"], ["The cat sat.", "A dog ran away"]))