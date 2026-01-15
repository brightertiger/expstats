import math
from scipy.stats import norm, t
from typing import Literal, Optional
from pyexptest.models import ABTestResult, TTestResult, NonInferiorityResult
from pyexptest.utils.validation import (
    validate_rate,
    validate_positive,
    validate_alpha,
    validate_sample_size,
    validate_sidedness,
)
from pyexptest.utils.math import (
    pooled_proportion,
    effect_size_cohens_h,
    effect_size_cohens_d,
    welch_degrees_of_freedom,
    calculate_lift,
)

def ab_test_significance(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    confidence_level: float = 0.95,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
) -> ABTestResult:
    alpha = 1 - confidence_level
    validate_sample_size(control_visitors, "control_visitors")
    validate_sample_size(variant_visitors, "variant_visitors")
    alpha = validate_alpha(alpha)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    if control_conversions < 0 or control_conversions > control_visitors:
        raise ValueError("control_conversions must be between 0 and control_visitors")
    if variant_conversions < 0 or variant_conversions > variant_visitors:
        raise ValueError("variant_conversions must be between 0 and variant_visitors")
    
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    n1 = control_visitors
    n2 = variant_visitors
    
    p_pooled = (control_conversions + variant_conversions) / (n1 + n2)
    
    se_pooled = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se_pooled == 0:
        z_stat = 0.0
        p_value = 1.0
    else:
        z_stat = (p2 - p1) / se_pooled
        
        if sidedness == "two-sided":
            p_value = 2 * (1 - norm.cdf(abs(z_stat)))
        else:
            p_value = 1 - norm.cdf(z_stat)
    
    se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    if sidedness == "two-sided":
        z_crit = norm.ppf(1 - alpha / 2)
        ci_lower = (p2 - p1) - z_crit * se_diff
        ci_upper = (p2 - p1) + z_crit * se_diff
    else:
        z_crit = norm.ppf(1 - alpha)
        ci_lower = (p2 - p1) - z_crit * se_diff
        ci_upper = float('inf')
    
    is_significant = bool(p_value < alpha)
    
    effect_size = effect_size_cohens_h(p1, p2)
    relative_lift, absolute_lift = calculate_lift(p1, p2)
    
    if is_significant:
        winner = "variant" if p2 > p1 else "control"
    else:
        winner = "none"
    
    return ABTestResult(
        z_score=float(z_stat),
        p_value=float(p_value),
        confidence_interval=(float(ci_lower), float(ci_upper)),
        is_significant=is_significant,
        confidence_level=confidence_level,
        effect_size=float(effect_size),
        relative_lift=float(relative_lift),
        absolute_lift=float(absolute_lift),
        control_conversion_rate=float(p1),
        variant_conversion_rate=float(p2),
        test_name="conversion_rate_test",
        test_type=test_type,
        winner=winner,
    )


def one_sample_test(
    conversions: int,
    visitors: int,
    expected_rate: float,
    confidence_level: float = 0.95,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
) -> ABTestResult:
    alpha = 1 - confidence_level
    validate_sample_size(visitors, "visitors")
    expected_rate = validate_rate(expected_rate, "expected_rate")
    alpha = validate_alpha(alpha)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    if conversions < 0 or conversions > visitors:
        raise ValueError("conversions must be between 0 and visitors")
    
    observed_rate = conversions / visitors
    p0 = expected_rate
    n = visitors
    
    se = math.sqrt(p0 * (1 - p0) / n)
    
    if se == 0:
        z_stat = 0.0
        p_value = 1.0
    else:
        z_stat = (observed_rate - p0) / se
        
        if sidedness == "two-sided":
            p_value = 2 * (1 - norm.cdf(abs(z_stat)))
        else:
            p_value = 1 - norm.cdf(z_stat)
    
    se_ci = math.sqrt(observed_rate * (1 - observed_rate) / n)
    
    if sidedness == "two-sided":
        z_crit = norm.ppf(1 - alpha / 2)
        ci_lower = observed_rate - z_crit * se_ci
        ci_upper = observed_rate + z_crit * se_ci
    else:
        z_crit = norm.ppf(1 - alpha)
        ci_lower = observed_rate - z_crit * se_ci
        ci_upper = 1.0
    
    ci_lower = max(0, ci_lower)
    ci_upper = min(1, ci_upper)
    
    is_significant = bool(p_value < alpha)
    effect_size = effect_size_cohens_h(p0, observed_rate)
    
    return ABTestResult(
        z_score=float(z_stat),
        p_value=float(p_value),
        confidence_interval=(float(ci_lower), float(ci_upper)),
        is_significant=is_significant,
        confidence_level=confidence_level,
        effect_size=float(effect_size),
        relative_lift=None,
        absolute_lift=float(observed_rate - p0),
        control_conversion_rate=float(p0),
        variant_conversion_rate=float(observed_rate),
        test_name="one_sample_test",
        test_type=test_type,
        winner="variant" if is_significant and observed_rate > p0 else "none",
    )


def revenue_significance(
    control_mean: float,
    control_std: float,
    control_visitors: int,
    variant_mean: float,
    variant_std: float,
    variant_visitors: int,
    confidence_level: float = 0.95,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
) -> TTestResult:
    alpha = 1 - confidence_level
    control_std = validate_positive(control_std, "control_std", allow_zero=True)
    variant_std = validate_positive(variant_std, "variant_std", allow_zero=True)
    control_visitors = validate_sample_size(control_visitors, "control_visitors")
    variant_visitors = validate_sample_size(variant_visitors, "variant_visitors")
    alpha = validate_alpha(alpha)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    var1 = control_std ** 2
    var2 = variant_std ** 2
    
    se = math.sqrt(var1 / control_visitors + var2 / variant_visitors)
    
    if se == 0:
        t_stat = 0.0
        p_value = 1.0
        df = control_visitors + variant_visitors - 2
    else:
        t_stat = (variant_mean - control_mean) / se
        df = welch_degrees_of_freedom(var1, var2, control_visitors, variant_visitors)
        
        if sidedness == "two-sided":
            p_value = 2 * (1 - t.cdf(abs(t_stat), df))
        else:
            p_value = 1 - t.cdf(t_stat, df)
    
    if sidedness == "two-sided":
        t_crit = t.ppf(1 - alpha / 2, df)
        ci_lower = (variant_mean - control_mean) - t_crit * se
        ci_upper = (variant_mean - control_mean) + t_crit * se
    else:
        t_crit = t.ppf(1 - alpha, df)
        ci_lower = (variant_mean - control_mean) - t_crit * se
        ci_upper = float('inf')
    
    is_significant = bool(p_value < alpha)
    
    pooled_std = math.sqrt(
        ((control_visitors - 1) * var1 + (variant_visitors - 1) * var2) / 
        (control_visitors + variant_visitors - 2)
    )
    effect_size = effect_size_cohens_d(control_mean, variant_mean, pooled_std) if pooled_std > 0 else 0.0
    
    if is_significant:
        winner = "variant" if variant_mean > control_mean else "control"
    else:
        winner = "none"
    
    return TTestResult(
        t_statistic=float(t_stat),
        p_value=float(p_value),
        confidence_interval=(float(ci_lower), float(ci_upper)),
        is_significant=is_significant,
        confidence_level=confidence_level,
        effect_size=float(effect_size),
        degrees_of_freedom=float(df),
        mean_difference=float(variant_mean - control_mean),
        control_mean=float(control_mean),
        variant_mean=float(variant_mean),
        test_name="revenue_test",
        test_type=test_type,
        winner=winner,
    )


def non_inferiority_test(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    non_inferiority_margin: float,
    confidence_level: float = 0.95,
) -> NonInferiorityResult:
    alpha = 1 - confidence_level
    validate_sample_size(control_visitors, "control_visitors")
    validate_sample_size(variant_visitors, "variant_visitors")
    non_inferiority_margin = validate_positive(non_inferiority_margin, "non_inferiority_margin")
    alpha = validate_alpha(alpha)
    
    if control_conversions < 0 or control_conversions > control_visitors:
        raise ValueError("control_conversions must be between 0 and control_visitors")
    if variant_conversions < 0 or variant_conversions > variant_visitors:
        raise ValueError("variant_conversions must be between 0 and variant_visitors")
    
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    n1 = control_visitors
    n2 = variant_visitors
    
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    if se == 0:
        z_stat = 0.0 if (p2 - p1) == -non_inferiority_margin else float('inf')
        p_value = 1.0
    else:
        z_stat = ((p2 - p1) + non_inferiority_margin) / se
        p_value = 1 - norm.cdf(z_stat)
    
    z_crit = norm.ppf(1 - alpha)
    ci_lower = (p2 - p1) - z_crit * se
    ci_upper = (p2 - p1) + z_crit * se
    
    is_non_inferior = bool(ci_lower > -non_inferiority_margin)
    
    return NonInferiorityResult(
        z_score=float(z_stat),
        p_value=float(p_value),
        confidence_interval=(float(ci_lower), float(ci_upper)),
        is_non_inferior=is_non_inferior,
        margin=float(non_inferiority_margin),
        confidence_level=confidence_level,
        observed_difference=float(p2 - p1),
        lower_bound=float(ci_lower),
        test_name="non_inferiority",
    )


def chi_square_test(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    confidence_level: float = 0.95,
) -> ABTestResult:
    from scipy.stats import chi2
    
    alpha = 1 - confidence_level
    validate_sample_size(control_visitors, "control_visitors")
    validate_sample_size(variant_visitors, "variant_visitors")
    alpha = validate_alpha(alpha)
    
    control_non_conversions = control_visitors - control_conversions
    variant_non_conversions = variant_visitors - variant_conversions
    
    observed = [
        [control_conversions, control_non_conversions],
        [variant_conversions, variant_non_conversions],
    ]
    
    row_totals = [sum(row) for row in observed]
    col_totals = [
        control_conversions + variant_conversions,
        control_non_conversions + variant_non_conversions,
    ]
    grand_total = sum(row_totals)
    
    expected = [
        [row_totals[i] * col_totals[j] / grand_total for j in range(2)]
        for i in range(2)
    ]
    
    chi2_stat = 0.0
    for i in range(2):
        for j in range(2):
            if expected[i][j] > 0:
                chi2_stat += (observed[i][j] - expected[i][j]) ** 2 / expected[i][j]
    
    p_value = 1 - chi2.cdf(chi2_stat, df=1)
    
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    
    se_diff = math.sqrt(p1 * (1 - p1) / control_visitors + p2 * (1 - p2) / variant_visitors)
    z_crit = norm.ppf(1 - alpha / 2)
    ci_lower = (p2 - p1) - z_crit * se_diff
    ci_upper = (p2 - p1) + z_crit * se_diff
    
    is_significant = bool(p_value < alpha)
    effect_size = effect_size_cohens_h(p1, p2)
    relative_lift, absolute_lift = calculate_lift(p1, p2)
    
    if is_significant:
        winner = "variant" if p2 > p1 else "control"
    else:
        winner = "none"
    
    return ABTestResult(
        z_score=float(chi2_stat),
        p_value=float(p_value),
        confidence_interval=(float(ci_lower), float(ci_upper)),
        is_significant=is_significant,
        confidence_level=confidence_level,
        effect_size=float(effect_size),
        relative_lift=float(relative_lift),
        absolute_lift=float(absolute_lift),
        control_conversion_rate=float(p1),
        variant_conversion_rate=float(p2),
        test_name="chi_square_test",
        test_type="two-tailed",
        winner=winner,
    )


z_test_proportions = ab_test_significance
z_test_one_sample = one_sample_test
welch_t_test = revenue_significance
