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
    """Per sentence BERTScore F1. Empty hypotheses get F1 = 0 
    (bertscore_f1 (0.3.12) cannot encode empty string with transformers (5.x))."""
    if len(hypotheses) != len(references):
        raise ValueError(f"Hypotheses are {len(hypotheses)} in number while references are {len(references)} in number.")
    
    keep = [i for i, h in enumerate(hypotheses) if h.strip()]
    f1 = [0.0] * len(hypotheses)
    bs_hash = None
    if keep:
        (P, R, F1), bs_hash = bert_score.score([hypotheses[i] for i in keep], [references[i] for i in keep], lang="en", return_hash=True)

        for i, score in zip(keep, F1.tolist()):
            f1[i] = score

    
    return f1, bs_hash


if __name__ == "__main__":
    print(chrf_scores(["The cat sat.", "Hello world"], ["The cat sat.", "A dog ran away"]))
    print(bertscore_f1(["The cat sat.", "Hello world"], ["The cat sat.", "A dog ran away"]))
    print(bertscore_f1(["The cat sat.", ""], ["The cat sat.", "@"]))