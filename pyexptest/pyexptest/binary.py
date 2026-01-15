import math
from scipy.stats import norm
from typing import Literal, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SampleSizePlan:
    visitors_per_variant: int
    total_visitors: int
    current_rate: float
    expected_rate: float
    lift_percent: float
    confidence: int
    power: int
    test_duration_days: Optional[int] = None
    
    def with_daily_traffic(self, daily_visitors: int) -> 'SampleSizePlan':
        self.test_duration_days = math.ceil(self.total_visitors / daily_visitors)
        return self

@dataclass
class TestResults:
    control_rate: float
    variant_rate: float
    lift_percent: float
    lift_absolute: float
    is_significant: bool
    confidence: int
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_visitors: int
    control_conversions: int
    variant_visitors: int
    variant_conversions: int
    winner: Literal["control", "variant", "no winner yet"]
    recommendation: str

@dataclass  
class ConfidenceInterval:
    rate: float
    lower: float
    upper: float
    confidence: int
    margin_of_error: float


def sample_size(
    current_rate: float,
    lift_percent: float = 10,
    confidence: int = 95,
    power: int = 80,
) -> SampleSizePlan:
    if current_rate > 1:
        current_rate = current_rate / 100
    
    lift_decimal = lift_percent / 100
    expected_rate = current_rate * (1 + lift_decimal)
    
    if expected_rate > 1:
        raise ValueError(f"Expected rate ({expected_rate:.1%}) exceeds 100%. Lower your lift_percent.")
    if expected_rate < 0:
        raise ValueError(f"Expected rate cannot be negative. Check your lift_percent.")
    if current_rate <= 0 or current_rate >= 1:
        raise ValueError(f"current_rate must be between 0 and 1 (or 0% and 100%)")
    
    alpha = 1 - (confidence / 100)
    beta = 1 - (power / 100)
    
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)
    
    p1 = current_rate
    p2 = expected_rate
    p_pooled = (p1 + p2) / 2
    
    numerator = (
        z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) +
        z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p2 - p1) ** 2
    
    n = math.ceil(numerator / denominator)
    
    return SampleSizePlan(
        visitors_per_variant=n,
        total_visitors=n * 2,
        current_rate=current_rate,
        expected_rate=expected_rate,
        lift_percent=lift_percent,
        confidence=confidence,
        power=power,
    )


def analyze(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    confidence: int = 95,
) -> TestResults:
    if control_conversions > control_visitors:
        raise ValueError("control_conversions cannot exceed control_visitors")
    if variant_conversions > variant_visitors:
        raise ValueError("variant_conversions cannot exceed variant_visitors")
    
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    
    lift_absolute = p2 - p1
    lift_percent = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
    
    alpha = 1 - (confidence / 100)
    
    p_pooled = (control_conversions + variant_conversions) / (control_visitors + variant_visitors)
    se_pooled = math.sqrt(p_pooled * (1 - p_pooled) * (1/control_visitors + 1/variant_visitors))
    
    if se_pooled > 0:
        z_stat = (p2 - p1) / se_pooled
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))
    else:
        z_stat = 0
        p_value = 1.0
    
    se_diff = math.sqrt(p1 * (1 - p1) / control_visitors + p2 * (1 - p2) / variant_visitors)
    z_crit = norm.ppf(1 - alpha / 2)
    ci_lower = lift_absolute - z_crit * se_diff
    ci_upper = lift_absolute + z_crit * se_diff
    
    is_significant = p_value < alpha
    
    if is_significant:
        winner = "variant" if p2 > p1 else "control"
        if p2 > p1:
            recommendation = "Implement the variant - it performs significantly better."
        else:
            recommendation = "Keep the control - the variant performs significantly worse."
    else:
        winner = "no winner yet"
        recommendation = "Continue the test - results are not yet conclusive."
    
    return TestResults(
        control_rate=p1,
        variant_rate=p2,
        lift_percent=lift_percent,
        lift_absolute=lift_absolute,
        is_significant=is_significant,
        confidence=confidence,
        p_value=p_value,
        confidence_interval_lower=ci_lower,
        confidence_interval_upper=ci_upper,
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        winner=winner,
        recommendation=recommendation,
    )


def confidence_interval(
    visitors: int,
    conversions: int,
    confidence: int = 95,
) -> ConfidenceInterval:
    if conversions > visitors:
        raise ValueError("conversions cannot exceed visitors")
    if visitors <= 0:
        raise ValueError("visitors must be positive")
    
    rate = conversions / visitors
    alpha = 1 - (confidence / 100)
    z = norm.ppf(1 - alpha / 2)
    
    denominator = 1 + z**2 / visitors
    center = (rate + z**2 / (2 * visitors)) / denominator
    margin = z * math.sqrt((rate * (1 - rate) + z**2 / (4 * visitors)) / visitors) / denominator
    
    lower = max(0, center - margin)
    upper = min(1, center + margin)
    
    return ConfidenceInterval(
        rate=rate,
        lower=lower,
        upper=upper,
        confidence=confidence,
        margin_of_error=margin,
    )


def summarize(result: TestResults, test_name: str = "A/B Test") -> str:
    lines = []
    lines.append(f"=" * 60)
    lines.append(f"📊 {test_name.upper()} RESULTS SUMMARY")
    lines.append(f"=" * 60)
    lines.append("")
    
    lines.append("PERFORMANCE COMPARISON")
    lines.append("-" * 40)
    lines.append(f"  Control:  {result.control_rate:.2%} conversion rate")
    lines.append(f"            ({result.control_conversions:,} conversions / {result.control_visitors:,} visitors)")
    lines.append("")
    lines.append(f"  Variant:  {result.variant_rate:.2%} conversion rate")
    lines.append(f"            ({result.variant_conversions:,} conversions / {result.variant_visitors:,} visitors)")
    lines.append("")
    
    lift_direction = "increase" if result.lift_percent > 0 else "decrease"
    lines.append(f"  Lift:     {result.lift_percent:+.1f}% ({lift_direction})")
    lines.append(f"            {result.lift_absolute:+.2%} absolute difference")
    lines.append("")
    
    lines.append("STATISTICAL ANALYSIS")
    lines.append("-" * 40)
    
    if result.is_significant:
        lines.append(f"  ✅ STATISTICALLY SIGNIFICANT at {result.confidence}% confidence")
    else:
        lines.append(f"  ❌ NOT statistically significant at {result.confidence}% confidence")
    
    lines.append(f"  P-value: {result.p_value:.4f}")
    lines.append(f"  {result.confidence}% CI: [{result.confidence_interval_lower:+.2%}, {result.confidence_interval_upper:+.2%}]")
    lines.append("")
    
    lines.append("RECOMMENDATION")
    lines.append("-" * 40)
    
    if result.winner == "variant":
        lines.append(f"  🏆 WINNER: Variant")
        lines.append(f"  → {result.recommendation}")
        if result.lift_percent > 0:
            lines.append(f"  → Expected improvement: {result.lift_percent:+.1f}%")
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


def summarize_plan(plan: SampleSizePlan, test_name: str = "A/B Test") -> str:
    lines = []
    lines.append(f"=" * 60)
    lines.append(f"📋 {test_name.upper()} PLANNING SUMMARY")
    lines.append(f"=" * 60)
    lines.append("")
    
    lines.append("TEST PARAMETERS")
    lines.append("-" * 40)
    lines.append(f"  Current conversion rate: {plan.current_rate:.2%}")
    lines.append(f"  Minimum lift to detect:  {plan.lift_percent:+.0f}%")
    lines.append(f"  Expected variant rate:   {plan.expected_rate:.2%}")
    lines.append(f"  Confidence level:        {plan.confidence}%")
    lines.append(f"  Statistical power:       {plan.power}%")
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
    lines.append(f"  If the variant truly improves conversion by {plan.lift_percent}% or more,")
    lines.append(f"  this test has a {plan.power}% chance of detecting it.")
    lines.append("")
    lines.append(f"  The test has a {100 - plan.confidence}% chance of a false positive")
    lines.append(f"  (declaring a winner when there's no real difference).")
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)
