import numpy as np
from typing import Tuple

def pooled_proportion(p1: float, p2: float, n1: int, n2: int) -> float:
    return (p1 * n1 + p2 * n2) / (n1 + n2)

def pooled_variance(var1: float, var2: float, n1: int, n2: int) -> float:
    return ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)

def effect_size_cohens_h(p1: float, p2: float) -> float:
    phi1 = 2 * np.arcsin(np.sqrt(p1))
    phi2 = 2 * np.arcsin(np.sqrt(p2))
    return phi1 - phi2

def effect_size_cohens_d(mean1: float, mean2: float, sd_pooled: float) -> float:
    if sd_pooled == 0:
        return np.inf if mean1 != mean2 else 0.0
    return (mean1 - mean2) / sd_pooled

def normal_cdf(x: float) -> float:
    from scipy.stats import norm
    return norm.cdf(x)

def normal_ppf(p: float) -> float:
    from scipy.stats import norm
    return norm.ppf(p)

def t_cdf(x: float, df: float) -> float:
    from scipy.stats import t
    return t.cdf(x, df)

def t_ppf(p: float, df: float) -> float:
    from scipy.stats import t
    return t.ppf(p, df)

def welch_degrees_of_freedom(var1: float, var2: float, n1: int, n2: int) -> float:
    se1_sq = var1 / n1
    se2_sq = var2 / n2
    numerator = (se1_sq + se2_sq) ** 2
    denominator = (se1_sq ** 2) / (n1 - 1) + (se2_sq ** 2) / (n2 - 1)
    if denominator == 0:
        return float('inf')
    return numerator / denominator

def calculate_lift(baseline: float, variant: float) -> Tuple[float, float]:
    if baseline == 0:
        return (np.inf if variant > 0 else 0.0, variant)
    absolute_lift = variant - baseline
    relative_lift = (variant - baseline) / baseline
    return relative_lift, absolute_lift
