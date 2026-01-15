import math
from scipy.stats import norm, t
from typing import Literal
from pyexptest.models import ConfidenceIntervalResult
from pyexptest.utils.validation import (
    validate_rate,
    validate_positive,
    validate_sample_size,
)

def conversion_rate_ci(
    conversions: int,
    visitors: int,
    confidence_level: float = 0.95,
    method: Literal["normal", "wilson", "agresti-coull"] = "wilson",
) -> ConfidenceIntervalResult:
    validate_sample_size(visitors, "visitors")
    
    if conversions < 0 or conversions > visitors:
        raise ValueError("conversions must be between 0 and visitors")
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("confidence_level must be between 0 and 1")
    
    conversion_rate = conversions / visitors
    n = visitors
    alpha = 1 - confidence_level
    z = norm.ppf(1 - alpha / 2)
    
    if method == "normal":
        se = math.sqrt(conversion_rate * (1 - conversion_rate) / n)
        lower = conversion_rate - z * se
        upper = conversion_rate + z * se
        lower = max(0, lower)
        upper = min(1, upper)
        margin = z * se
        
    elif method == "wilson":
        denominator = 1 + z**2 / n
        center = (conversion_rate + z**2 / (2 * n)) / denominator
        margin = z * math.sqrt((conversion_rate * (1 - conversion_rate) + z**2 / (4 * n)) / n) / denominator
        lower = center - margin
        upper = center + margin
        se = margin / z
        
    elif method == "agresti-coull":
        n_tilde = n + z**2
        p_tilde = (conversions + z**2 / 2) / n_tilde
        se = math.sqrt(p_tilde * (1 - p_tilde) / n_tilde)
        lower = p_tilde - z * se
        upper = p_tilde + z * se
        conversion_rate = p_tilde
        margin = z * se
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return ConfidenceIntervalResult(
        point_estimate=conversion_rate,
        lower_bound=lower,
        upper_bound=upper,
        confidence_level=confidence_level,
        margin_of_error=margin,
        method=method,
    )


def lift_ci(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    confidence_level: float = 0.95,
    method: Literal["normal", "newcombe"] = "normal",
) -> ConfidenceIntervalResult:
    validate_sample_size(control_visitors, "control_visitors")
    validate_sample_size(variant_visitors, "variant_visitors")
    
    if control_conversions < 0 or control_conversions > control_visitors:
        raise ValueError("control_conversions must be between 0 and control_visitors")
    if variant_conversions < 0 or variant_conversions > variant_visitors:
        raise ValueError("variant_conversions must be between 0 and variant_visitors")
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("confidence_level must be between 0 and 1")
    
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    n1 = control_visitors
    n2 = variant_visitors
    
    diff = p2 - p1
    alpha = 1 - confidence_level
    z = norm.ppf(1 - alpha / 2)
    
    if method == "normal":
        se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        lower = diff - z * se
        upper = diff + z * se
        margin = z * se
        
    elif method == "newcombe":
        ci1 = conversion_rate_ci(control_conversions, control_visitors, confidence_level, "wilson")
        ci2 = conversion_rate_ci(variant_conversions, variant_visitors, confidence_level, "wilson")
        
        lower = diff - math.sqrt((p1 - ci1.lower_bound)**2 + (ci2.upper_bound - p2)**2)
        upper = diff + math.sqrt((ci1.upper_bound - p1)**2 + (p2 - ci2.lower_bound)**2)
        se = (upper - lower) / (2 * z)
        margin = (upper - lower) / 2
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return ConfidenceIntervalResult(
        point_estimate=diff,
        lower_bound=lower,
        upper_bound=upper,
        confidence_level=confidence_level,
        margin_of_error=margin,
        method=method,
    )


def mean_ci(
    mean: float,
    std: float,
    visitors: int,
    confidence_level: float = 0.95,
    use_t_distribution: bool = True,
) -> ConfidenceIntervalResult:
    std = validate_positive(std, "std", allow_zero=True)
    visitors = validate_sample_size(visitors, "visitors")
    
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("confidence_level must be between 0 and 1")
    
    alpha = 1 - confidence_level
    se = std / math.sqrt(visitors)
    
    if use_t_distribution and visitors > 1:
        critical = t.ppf(1 - alpha / 2, visitors - 1)
    else:
        critical = norm.ppf(1 - alpha / 2)
    
    margin = critical * se
    lower = mean - margin
    upper = mean + margin
    
    method = "t-distribution" if use_t_distribution else "normal"
    
    return ConfidenceIntervalResult(
        point_estimate=mean,
        lower_bound=lower,
        upper_bound=upper,
        confidence_level=confidence_level,
        margin_of_error=margin,
        method=method,
    )


def revenue_lift_ci(
    control_mean: float,
    control_std: float,
    control_visitors: int,
    variant_mean: float,
    variant_std: float,
    variant_visitors: int,
    confidence_level: float = 0.95,
) -> ConfidenceIntervalResult:
    control_std = validate_positive(control_std, "control_std", allow_zero=True)
    variant_std = validate_positive(variant_std, "variant_std", allow_zero=True)
    control_visitors = validate_sample_size(control_visitors, "control_visitors")
    variant_visitors = validate_sample_size(variant_visitors, "variant_visitors")
    
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("confidence_level must be between 0 and 1")
    
    diff = variant_mean - control_mean
    alpha = 1 - confidence_level
    
    var1 = control_std ** 2
    var2 = variant_std ** 2
    
    se = math.sqrt(var1 / control_visitors + var2 / variant_visitors)
    
    from pyexptest.utils.math import welch_degrees_of_freedom
    df = welch_degrees_of_freedom(var1, var2, control_visitors, variant_visitors)
    
    critical = t.ppf(1 - alpha / 2, df)
    margin = critical * se
    
    lower = diff - margin
    upper = diff + margin
    
    return ConfidenceIntervalResult(
        point_estimate=diff,
        lower_bound=lower,
        upper_bound=upper,
        confidence_level=confidence_level,
        margin_of_error=margin,
        method="welch",
    )


def relative_lift_ci(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    confidence_level: float = 0.95,
) -> ConfidenceIntervalResult:
    validate_sample_size(control_visitors, "control_visitors")
    validate_sample_size(variant_visitors, "variant_visitors")
    
    if control_conversions < 0 or control_conversions > control_visitors:
        raise ValueError("control_conversions must be between 0 and control_visitors")
    if variant_conversions < 0 or variant_conversions > variant_visitors:
        raise ValueError("variant_conversions must be between 0 and variant_visitors")
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("confidence_level must be between 0 and 1")
    
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    n1 = control_visitors
    n2 = variant_visitors
    
    if p1 == 0:
        raise ValueError("Cannot compute relative lift when control conversion rate is 0")
    
    relative_lift = (p2 - p1) / p1
    
    alpha = 1 - confidence_level
    z = norm.ppf(1 - alpha / 2)
    
    se_log_rr = math.sqrt((1 - p1) / (n1 * p1) + (1 - p2) / (n2 * p2)) if p2 > 0 else float('inf')
    
    log_rr = math.log(p2 / p1) if p2 > 0 else float('-inf')
    
    log_lower = log_rr - z * se_log_rr
    log_upper = log_rr + z * se_log_rr
    
    lower = math.exp(log_lower) - 1
    upper = math.exp(log_upper) - 1
    
    margin = (upper - lower) / 2
    
    return ConfidenceIntervalResult(
        point_estimate=relative_lift,
        lower_bound=lower,
        upper_bound=upper,
        confidence_level=confidence_level,
        margin_of_error=margin,
        method="log_ratio",
    )


proportion_confidence_interval = conversion_rate_ci
difference_confidence_interval = lift_ci
continuous_confidence_interval = mean_ci
mean_difference_confidence_interval = revenue_lift_ci
relative_lift_confidence_interval = relative_lift_ci
