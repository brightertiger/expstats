import math
from scipy.stats import norm
from typing import Literal, Optional
from pyexptest.models import SampleSizeResult, ContinuousSampleSizeResult
from pyexptest.utils.validation import (
    validate_rate,
    validate_positive,
    validate_alpha,
    validate_power,
    validate_allocation_ratio,
    validate_sidedness,
)

def conversion_sample_size(
    control_conversion_rate: float,
    minimum_lift: float,
    lift_type: Literal["absolute", "relative"] = "relative",
    confidence_level: float = 0.95,
    statistical_power: float = 0.80,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
    traffic_split: float = 1.0,
) -> SampleSizeResult:
    alpha = 1 - confidence_level
    control_conversion_rate = validate_rate(control_conversion_rate, "control_conversion_rate")
    alpha = validate_alpha(alpha)
    statistical_power = validate_power(statistical_power)
    traffic_split = validate_allocation_ratio(traffic_split)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    if lift_type == "relative":
        absolute_effect = control_conversion_rate * minimum_lift
        variant_conversion_rate = control_conversion_rate + absolute_effect
    else:
        absolute_effect = minimum_lift
        variant_conversion_rate = control_conversion_rate + minimum_lift
    
    if variant_conversion_rate < 0 or variant_conversion_rate > 1:
        raise ValueError(
            f"Expected variant rate ({variant_conversion_rate}) must be between 0 and 1. "
            f"Check your control_conversion_rate ({control_conversion_rate}) and minimum_lift ({minimum_lift})."
        )
    
    p1 = control_conversion_rate
    p2 = variant_conversion_rate
    
    if sidedness == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)
    
    z_beta = norm.ppf(statistical_power)
    
    k = traffic_split
    
    p_pooled = (p1 + k * p2) / (1 + k)
    
    numerator = (
        z_alpha * math.sqrt((1 + 1/k) * p_pooled * (1 - p_pooled)) +
        z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / k)
    ) ** 2
    
    denominator = (p2 - p1) ** 2
    
    if denominator == 0:
        raise ValueError("minimum_lift cannot be zero")
    
    n1 = math.ceil(numerator / denominator)
    n2 = math.ceil(n1 * k)
    
    assumptions = [
        "Two-proportion Z-test (standard A/B test)",
        "Users are randomly assigned to control/variant",
        "Each user is independent (no network effects)",
        f"{'Two-tailed' if test_type == 'two-tailed' else 'One-tailed'} test",
    ]
    
    return SampleSizeResult(
        visitors_per_variation=n1,
        total_visitors=n1 + n2,
        control_conversion_rate=control_conversion_rate,
        variant_conversion_rate=variant_conversion_rate,
        minimum_detectable_lift=minimum_lift,
        lift_type=lift_type,
        confidence_level=confidence_level,
        statistical_power=statistical_power,
        test_type=test_type,
        traffic_split=traffic_split,
        control_visitors=n1,
        variant_visitors=n2,
        assumptions=assumptions,
    )


def revenue_sample_size(
    control_mean: float,
    minimum_lift: float,
    standard_deviation: float,
    lift_type: Literal["absolute", "relative"] = "relative",
    confidence_level: float = 0.95,
    statistical_power: float = 0.80,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
    traffic_split: float = 1.0,
) -> ContinuousSampleSizeResult:
    alpha = 1 - confidence_level
    alpha = validate_alpha(alpha)
    statistical_power = validate_power(statistical_power)
    standard_deviation = validate_positive(standard_deviation, "standard_deviation")
    traffic_split = validate_allocation_ratio(traffic_split)
    sidedness = "two-sided" if test_type == "two-tailed" else "one-sided"
    validate_sidedness(sidedness)
    
    if lift_type == "relative":
        absolute_effect = control_mean * minimum_lift
    else:
        absolute_effect = minimum_lift
    
    variant_mean = control_mean + absolute_effect
    
    if absolute_effect == 0:
        raise ValueError("minimum_lift cannot be zero")
    
    if sidedness == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)
    
    z_beta = norm.ppf(statistical_power)
    
    k = traffic_split
    
    numerator = (z_alpha + z_beta) ** 2 * standard_deviation ** 2 * (1 + 1/k)
    denominator = absolute_effect ** 2
    
    n1 = math.ceil(numerator / denominator)
    n2 = math.ceil(n1 * k)
    
    assumptions = [
        "Two-sample t-test (normal approximation)",
        "Users are randomly assigned to control/variant",
        "Equal variances assumed across groups",
        f"{'Two-tailed' if test_type == 'two-tailed' else 'One-tailed'} test",
    ]
    
    return ContinuousSampleSizeResult(
        visitors_per_variation=n1,
        total_visitors=n1 + n2,
        control_mean=control_mean,
        variant_mean=variant_mean,
        standard_deviation=standard_deviation,
        minimum_detectable_lift=minimum_lift,
        lift_type=lift_type,
        confidence_level=confidence_level,
        statistical_power=statistical_power,
        test_type=test_type,
        traffic_split=traffic_split,
        control_visitors=n1,
        variant_visitors=n2,
        assumptions=assumptions,
    )


def ab_test_sample_size(
    control_conversion_rate: float,
    expected_lift: float,
    lift_type: Literal["absolute", "relative"] = "relative",
    confidence_level: float = 0.95,
    statistical_power: float = 0.80,
    test_type: Literal["one-tailed", "two-tailed"] = "two-tailed",
    traffic_split: float = 1.0,
) -> SampleSizeResult:
    return conversion_sample_size(
        control_conversion_rate=control_conversion_rate,
        minimum_lift=expected_lift,
        lift_type=lift_type,
        confidence_level=confidence_level,
        statistical_power=statistical_power,
        test_type=test_type,
        traffic_split=traffic_split,
    )


two_proportion_sample_size = conversion_sample_size
continuous_sample_size = revenue_sample_size
sample_size_from_mde = ab_test_sample_size
