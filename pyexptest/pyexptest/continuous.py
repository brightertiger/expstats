import math
from scipy.stats import norm, t
from typing import Literal, Optional
from dataclasses import dataclass

@dataclass
class SampleSizePlan:
    visitors_per_variant: int
    total_visitors: int
    current_mean: float
    expected_mean: float
    standard_deviation: float
    lift_percent: float
    confidence: int
    power: int
    test_duration_days: Optional[int] = None
    
    def with_daily_traffic(self, daily_visitors: int) -> 'SampleSizePlan':
        self.test_duration_days = math.ceil(self.total_visitors / daily_visitors)
        return self

@dataclass
class TestResults:
    control_mean: float
    variant_mean: float
    lift_percent: float
    lift_absolute: float
    is_significant: bool
    confidence: int
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_visitors: int
    control_std: float
    variant_visitors: int
    variant_std: float
    winner: Literal["control", "variant", "no winner yet"]
    recommendation: str

@dataclass
class ConfidenceInterval:
    mean: float
    lower: float
    upper: float
    confidence: int
    margin_of_error: float


def sample_size(
    current_mean: float,
    current_std: float,
    lift_percent: float = 5,
    confidence: int = 95,
    power: int = 80,
) -> SampleSizePlan:
    lift_decimal = lift_percent / 100
    expected_mean = current_mean * (1 + lift_decimal)
    absolute_effect = abs(expected_mean - current_mean)
    
    if absolute_effect == 0:
        raise ValueError("lift_percent cannot be zero")
    if current_std <= 0:
        raise ValueError("current_std must be positive")
    
    alpha = 1 - (confidence / 100)
    beta = 1 - (power / 100)
    
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)
    
    n = math.ceil(2 * ((z_alpha + z_beta) * current_std / absolute_effect) ** 2)
    
    return SampleSizePlan(
        visitors_per_variant=n,
        total_visitors=n * 2,
        current_mean=current_mean,
        expected_mean=expected_mean,
        standard_deviation=current_std,
        lift_percent=lift_percent,
        confidence=confidence,
        power=power,
    )


def analyze(
    control_visitors: int,
    control_mean: float,
    control_std: float,
    variant_visitors: int,
    variant_mean: float,
    variant_std: float,
    confidence: int = 95,
) -> TestResults:
    if control_visitors <= 0 or variant_visitors <= 0:
        raise ValueError("visitors must be positive")
    if control_std < 0 or variant_std < 0:
        raise ValueError("standard deviation cannot be negative")
    
    lift_absolute = variant_mean - control_mean
    lift_percent = ((variant_mean - control_mean) / control_mean * 100) if control_mean != 0 else 0
    
    alpha = 1 - (confidence / 100)
    
    var1 = control_std ** 2
    var2 = variant_std ** 2
    
    se = math.sqrt(var1 / control_visitors + var2 / variant_visitors)
    
    if se > 0:
        t_stat = lift_absolute / se
        
        numerator = (var1 / control_visitors + var2 / variant_visitors) ** 2
        denominator = (var1 / control_visitors) ** 2 / (control_visitors - 1) + \
                      (var2 / variant_visitors) ** 2 / (variant_visitors - 1)
        df = numerator / denominator if denominator > 0 else control_visitors + variant_visitors - 2
        
        p_value = 2 * (1 - t.cdf(abs(t_stat), df))
    else:
        t_stat = 0
        p_value = 1.0
        df = control_visitors + variant_visitors - 2
    
    t_crit = t.ppf(1 - alpha / 2, df)
    ci_lower = lift_absolute - t_crit * se
    ci_upper = lift_absolute + t_crit * se
    
    is_significant = p_value < alpha
    
    if is_significant:
        winner = "variant" if variant_mean > control_mean else "control"
        if variant_mean > control_mean:
            recommendation = "Implement the variant - it performs significantly better."
        else:
            recommendation = "Keep the control - the variant performs significantly worse."
    else:
        winner = "no winner yet"
        recommendation = "Continue the test - results are not yet conclusive."
    
    return TestResults(
        control_mean=control_mean,
        variant_mean=variant_mean,
        lift_percent=lift_percent,
        lift_absolute=lift_absolute,
        is_significant=is_significant,
        confidence=confidence,
        p_value=p_value,
        confidence_interval_lower=ci_lower,
        confidence_interval_upper=ci_upper,
        control_visitors=control_visitors,
        control_std=control_std,
        variant_visitors=variant_visitors,
        variant_std=variant_std,
        winner=winner,
        recommendation=recommendation,
    )


def confidence_interval(
    visitors: int,
    mean: float,
    std: float,
    confidence: int = 95,
) -> ConfidenceInterval:
    if visitors <= 1:
        raise ValueError("visitors must be greater than 1")
    if std < 0:
        raise ValueError("standard deviation cannot be negative")
    
    alpha = 1 - (confidence / 100)
    se = std / math.sqrt(visitors)
    t_crit = t.ppf(1 - alpha / 2, visitors - 1)
    margin = t_crit * se
    
    return ConfidenceInterval(
        mean=mean,
        lower=mean - margin,
        upper=mean + margin,
        confidence=confidence,
        margin_of_error=margin,
    )


def summarize(result: TestResults, test_name: str = "Revenue Test", metric_name: str = "Average Order Value", currency: str = "$") -> str:
    lines = []
    lines.append(f"=" * 60)
    lines.append(f"📊 {test_name.upper()} RESULTS SUMMARY")
    lines.append(f"=" * 60)
    lines.append("")
    
    lines.append(f"PERFORMANCE COMPARISON ({metric_name})")
    lines.append("-" * 40)
    lines.append(f"  Control:  {currency}{result.control_mean:,.2f}")
    lines.append(f"            (std dev: {currency}{result.control_std:,.2f}, n={result.control_visitors:,})")
    lines.append("")
    lines.append(f"  Variant:  {currency}{result.variant_mean:,.2f}")
    lines.append(f"            (std dev: {currency}{result.variant_std:,.2f}, n={result.variant_visitors:,})")
    lines.append("")
    
    lift_direction = "increase" if result.lift_percent > 0 else "decrease"
    lines.append(f"  Lift:     {result.lift_percent:+.1f}% ({lift_direction})")
    lines.append(f"            {currency}{result.lift_absolute:+,.2f} absolute difference")
    lines.append("")
    
    lines.append("STATISTICAL ANALYSIS")
    lines.append("-" * 40)
    
    if result.is_significant:
        lines.append(f"  ✅ STATISTICALLY SIGNIFICANT at {result.confidence}% confidence")
    else:
        lines.append(f"  ❌ NOT statistically significant at {result.confidence}% confidence")
    
    lines.append(f"  P-value: {result.p_value:.4f}")
    lines.append(f"  {result.confidence}% CI: [{currency}{result.confidence_interval_lower:+,.2f}, {currency}{result.confidence_interval_upper:+,.2f}]")
    lines.append("")
    
    lines.append("RECOMMENDATION")
    lines.append("-" * 40)
    
    if result.winner == "variant":
        lines.append(f"  🏆 WINNER: Variant")
        lines.append(f"  → {result.recommendation}")
        if result.lift_absolute > 0:
            lines.append(f"  → Expected improvement: {currency}{result.lift_absolute:+,.2f} per transaction")
    elif result.winner == "control":
        lines.append(f"  🏆 WINNER: Control")
        lines.append(f"  → {result.recommendation}")
    else:
        lines.append(f"  ⏳ NO WINNER YET")
        lines.append(f"  → {result.recommendation}")
        total = result.control_visitors + result.variant_visitors
        lines.append(f"  → Current sample: {total:,} visitors")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def summarize_plan(plan: SampleSizePlan, test_name: str = "Revenue Test", metric_name: str = "Average Order Value", currency: str = "$") -> str:
    lines = []
    lines.append(f"=" * 60)
    lines.append(f"📋 {test_name.upper()} PLANNING SUMMARY")
    lines.append(f"=" * 60)
    lines.append("")
    
    lines.append(f"TEST PARAMETERS ({metric_name})")
    lines.append("-" * 40)
    lines.append(f"  Current mean:           {currency}{plan.current_mean:,.2f}")
    lines.append(f"  Standard deviation:     {currency}{plan.standard_deviation:,.2f}")
    lines.append(f"  Minimum lift to detect: {plan.lift_percent:+.0f}%")
    lines.append(f"  Expected variant mean:  {currency}{plan.expected_mean:,.2f}")
    lines.append(f"  Confidence level:       {plan.confidence}%")
    lines.append(f"  Statistical power:      {plan.power}%")
    lines.append("")
    
    lines.append("SAMPLE SIZE REQUIREMENTS")
    lines.append("-" * 40)
    lines.append(f"  Per variant:  {plan.visitors_per_variant:,} visitors")
    lines.append(f"  Total:        {plan.total_visitors:,} visitors")
    lines.append("")
    
    if plan.test_duration_days:
        lines.append("ESTIMATED DURATION")
        lines.append("-" * 40)
        if plan.test_duration_days < 7:
            lines.append(f"  ~{plan.test_duration_days} days")
        elif plan.test_duration_days < 30:
            weeks = plan.test_duration_days / 7
            lines.append(f"  ~{weeks:.1f} weeks ({plan.test_duration_days} days)")
        else:
            months = plan.test_duration_days / 30
            lines.append(f"  ~{months:.1f} months ({plan.test_duration_days} days)")
        lines.append("")
    
    lines.append("WHAT THIS MEANS")
    lines.append("-" * 40)
    lines.append(f"  If the variant truly improves {metric_name.lower()} by {plan.lift_percent}% or more,")
    lines.append(f"  this test has a {plan.power}% chance of detecting it.")
    lines.append("")
    lines.append(f"  The test has a {100 - plan.confidence}% chance of a false positive")
    lines.append(f"  (declaring a winner when there's no real difference).")
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)
