"""Paired t-test, paired bootstrap CI and Holm correction for per-sentence metric scores."""
from scipy.stats import ttest_rel
from statsmodels.stats.multitest import multipletests
import numpy as np

def paired_ttest(scores_a, scores_b):
    """Paired ttest significance test"""
    if len(scores_a) != len(scores_b):
        raise ValueError(f"Scores a are {len(scores_a)} in number while scores_b are {len(scores_b)} in number.")
    res = ttest_rel(scores_b, scores_a)
    return float(res.statistic), float(res.pvalue), float(np.mean(np.array(scores_b) - np.array(scores_a)))

def paired_bootstrap(scores_a, scores_b, n_resamples=1000, seed=0):
    """Paired bootstrap significance test"""
    if len(scores_a) != len(scores_b):
        raise ValueError(f"Scores a are {len(scores_a)} in number while scores_b are {len(scores_b)} in number.")
    d = np.array(scores_b) - np.array(scores_a)
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_resamples):
        idx = rng.integers(0, len(d), size=len(d))
        means.append(d[idx].mean())
    low, high = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), (float(low), float(high))


def holm(p_values):
    """Holm corrected p-values."""
    _, pvals_corrected, _, _ = multipletests(p_values, method="holm")
    return pvals_corrected.tolist()


if __name__ == "__main__":
    A = [30, 42, 25, 51, 38] 
    B = [33, 45, 24, 56, 41]
    t, p, md = paired_ttest(A, B)
    print(f"t={t:.3f}  p={p:.3g}  mean_diff={md:.3f}")
    md, (low, high) = paired_bootstrap(A, B)
    print(f"low={low:.3f}  high={high:.3f}  mean_diff={md:.3f}")
    print([f"{x:.3f}" for x in holm([0.01, 0.04, 0.03])])
    
