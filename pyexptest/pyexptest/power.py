import math
from scipy.stats import norm
from typing import Literal
from pyexptest.models import PowerResult, ContinuousPowerResult
from pyexptest.utils.validation import (
    validate_rate,
    validate_positive,
    validate_alpha,
    validate_sample_size,
    validate_allocation_ratio,
    validate_sidedness,
)
from pyexptest.utils.math import effect_size_cohens_h, effect_size_cohens_d

def conversion_power(
    control_conversion_rate: float,
    variant_conversion_rate: float,
    visitors_per_variation: int,
    confidence_level: float = 0.95,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
    traffic_split: float = 1.0,
) -> PowerResult:
    alpha = 1 - confidence_level
    control_conversion_rate = validate_rate(control_conversion_rate, "control_conversion_rate")
    variant_conversion_rate = validate_rate(variant_conversion_rate, "variant_conversion_rate")
    visitors_per_variation = validate_sample_size(visitors_per_variation, "visitors_per_variation")
    alpha = validate_alpha(alpha)
    traffic_split = validate_allocation_ratio(traffic_split)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    p1 = control_conversion_rate
    p2 = variant_conversion_rate
    n1 = visitors_per_variation
    n2 = int(visitors_per_variation * traffic_split)
    k = traffic_split
    
    if sidedness == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)
    
    p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
    
    se_null = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    se_alt = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    if se_alt == 0:
        power = 1.0 if p1 != p2 else 0.0
    else:
        effect = abs(p2 - p1)
        z_effect = (effect - z_alpha * se_null) / se_alt
        power = norm.cdf(z_effect)
    
    effect_size = effect_size_cohens_h(p1, p2)
    
    return PowerResult(
        statistical_power=float(power),
        visitors_per_variation=visitors_per_variation,
        control_conversion_rate=control_conversion_rate,
        variant_conversion_rate=variant_conversion_rate,
        effect_size=float(abs(effect_size)),
        confidence_level=confidence_level,
        test_type=test_type,
        traffic_split=traffic_split,
    )


def revenue_power(
    control_mean: float,
    variant_mean: float,
    standard_deviation: float,
    visitors_per_variation: int,
    confidence_level: float = 0.95,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
    traffic_split: float = 1.0,
) -> ContinuousPowerResult:
    alpha = 1 - confidence_level
    standard_deviation = validate_positive(standard_deviation, "standard_deviation")
    visitors_per_variation = validate_sample_size(visitors_per_variation, "visitors_per_variation")
    alpha = validate_alpha(alpha)
    traffic_split = validate_allocation_ratio(traffic_split)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    n1 = visitors_per_variation
    n2 = int(visitors_per_variation * traffic_split)
    
    if sidedness == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)
    
    effect = abs(variant_mean - control_mean)
    se = standard_deviation * math.sqrt(1/n1 + 1/n2)
    
    if se == 0:
        power = 1.0 if effect > 0 else 0.0
    else:
        z_effect = (effect / se) - z_alpha
        power = norm.cdf(z_effect)
    
    effect_size = effect_size_cohens_d(control_mean, variant_mean, standard_deviation)
    
    return ContinuousPowerResult(
        statistical_power=float(power),
        visitors_per_variation=visitors_per_variation,
        control_mean=float(control_mean),
        variant_mean=float(variant_mean),
        standard_deviation=float(standard_deviation),
        effect_size=float(abs(effect_size)),
        confidence_level=confidence_level,
        test_type=test_type,
        traffic_split=traffic_split,
    )


def detectable_lift(
    control_conversion_rate: float,
    visitors_per_variation: int,
    confidence_level: float = 0.95,
    statistical_power: float = 0.80,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
    traffic_split: float = 1.0,
) -> float:
    from scipy.optimize import brentq
    
    alpha = 1 - confidence_level
    control_conversion_rate = validate_rate(control_conversion_rate, "control_conversion_rate")
    visitors_per_variation = validate_sample_size(visitors_per_variation, "visitors_per_variation")
    alpha = validate_alpha(alpha)
    traffic_split = validate_allocation_ratio(traffic_split)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    def power_diff(effect):
        if control_conversion_rate + effect > 1 or control_conversion_rate + effect < 0:
            return -statistical_power
        result = conversion_power(
            control_conversion_rate=control_conversion_rate,
            variant_conversion_rate=control_conversion_rate + effect,
            visitors_per_variation=visitors_per_variation,
            confidence_level=confidence_level,
            test_type=test_type,
            traffic_split=traffic_split,
        )
        return result.statistical_power - statistical_power
    
    max_effect = min(1 - control_conversion_rate, control_conversion_rate)
    
    try:
        mde = brentq(power_diff, 0.0001, max_effect - 0.0001)
        return mde
    except ValueError:
        return max_effect


power_two_proportion = conversion_power
power_continuous = revenue_power
minimum_detectable_effect = detectable_lift
