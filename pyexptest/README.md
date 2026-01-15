# pyexptest

**Simple A/B testing tools for marketers, analysts, and product teams.**

No statistics PhD required. Just tell us your numbers, and we'll tell you what they mean.

## Installation

```bash
pip install pyexptest
```

## Quick Start

pyexptest has two modules:
- **`binary`** - for conversion rates (click rates, sign-up rates, purchase rates)
- **`continuous`** - for revenue, average order value, time on page, etc.

Each module has three functions:
- **`sample_size()`** - How many visitors do I need?
- **`analyze()`** - Did my test work? Who won?
- **`summarize()`** - Generate a report for stakeholders

---

## 📐 Sample Size Calculator

### For Conversion Rate Tests

```python
from pyexptest import binary

# "I have a 5% conversion rate and want to detect a 10% improvement"
plan = binary.sample_size(
    current_rate=5,      # Current conversion rate (5%)
    lift_percent=10,     # Want to detect 10% lift
)

print(f"You need {plan.visitors_per_variant:,} visitors per variant")
print(f"Total: {plan.total_visitors:,} visitors")

# Add daily traffic to estimate duration
plan.with_daily_traffic(5000)
print(f"Estimated duration: {plan.test_duration_days} days")
```

### For Revenue / AOV Tests

```python
from pyexptest import continuous

# "My AOV is $50 (std dev $25) and I want to detect a 5% lift"
plan = continuous.sample_size(
    current_mean=50,     # Current average order value
    current_std=25,      # Standard deviation (ask your analyst)
    lift_percent=5,      # Want to detect 5% lift
)

print(f"You need {plan.visitors_per_variant:,} visitors per variant")
```

---

## 📊 Analyze Test Results

### For Conversion Rate Tests

```python
from pyexptest import binary

result = binary.analyze(
    control_visitors=10000,
    control_conversions=500,      # 5.0% conversion rate
    variant_visitors=10000,
    variant_conversions=550,      # 5.5% conversion rate
)

print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Winner: {result.winner}")
print(f"Significant: {result.is_significant}")
print(f"Recommendation: {result.recommendation}")
```

Output:
```
Lift: +10.0%
Winner: variant
Significant: True
Recommendation: Implement the variant - it performs significantly better.
```

### For Revenue / AOV Tests

```python
from pyexptest import continuous

result = continuous.analyze(
    control_visitors=5000,
    control_mean=50.00,
    control_std=25.00,
    variant_visitors=5000,
    variant_mean=52.50,
    variant_std=25.00,
)

print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Winner: {result.winner}")
```

---

## 📋 Generate Stakeholder Reports

Get a formatted summary you can paste into Slack, email, or presentations:

```python
from pyexptest import binary

result = binary.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=550,
)

# Generate the report
print(binary.summarize(result, test_name="Homepage Button Test"))
```

Output:
```
============================================================
📊 HOMEPAGE BUTTON TEST RESULTS SUMMARY
============================================================

PERFORMANCE COMPARISON
----------------------------------------
  Control:  5.00% conversion rate
            (500 conversions / 10,000 visitors)

  Variant:  5.50% conversion rate
            (550 conversions / 10,000 visitors)

  Lift:     +10.0% (increase)
            +0.50% absolute difference

STATISTICAL ANALYSIS
----------------------------------------
  ✅ STATISTICALLY SIGNIFICANT at 95% confidence
  P-value: 0.1129
  95% CI: [+0.12%, +0.88%]

RECOMMENDATION
----------------------------------------
  🏆 WINNER: Variant
  → Implement the variant - it performs significantly better.
  → Expected improvement: +10.0%

============================================================
```

---

## 📏 Confidence Intervals

Get the range where your true rate likely falls:

```python
from pyexptest import binary

ci = binary.confidence_interval(
    visitors=1000,
    conversions=50,
    confidence=95,
)

print(f"Conversion rate: {ci.rate:.2%}")
print(f"95% CI: [{ci.lower:.2%}, {ci.upper:.2%}]")
print(f"Margin of error: ±{ci.margin_of_error:.2%}")
```

---

## Web Interface

pyexptest also includes a web UI for those who prefer clicking over coding:

```bash
# Start the server
pyexptest-server

# Open http://localhost:8000 in your browser
```

---

## API Reference

### binary module

| Function | Purpose |
|----------|---------|
| `binary.sample_size(current_rate, lift_percent, confidence=95, power=80)` | Calculate required sample size |
| `binary.analyze(control_visitors, control_conversions, variant_visitors, variant_conversions, confidence=95)` | Analyze test results |
| `binary.confidence_interval(visitors, conversions, confidence=95)` | Calculate confidence interval |
| `binary.summarize(result, test_name)` | Generate stakeholder report |
| `binary.summarize_plan(plan, test_name)` | Generate planning report |

### continuous module

| Function | Purpose |
|----------|---------|
| `continuous.sample_size(current_mean, current_std, lift_percent, confidence=95, power=80)` | Calculate required sample size |
| `continuous.analyze(control_visitors, control_mean, control_std, variant_visitors, variant_mean, variant_std, confidence=95)` | Analyze test results |
| `continuous.confidence_interval(visitors, mean, std, confidence=95)` | Calculate confidence interval |
| `continuous.summarize(result, test_name, metric_name, currency)` | Generate stakeholder report |

---

## Parameters Explained

| Parameter | What it means | Typical values |
|-----------|---------------|----------------|
| `current_rate` | Your current conversion rate | 1-10% for most sites |
| `lift_percent` | Smallest improvement worth detecting | 5-20% |
| `confidence` | How sure you want to be (avoids false positives) | 95% (standard) |
| `power` | Chance of detecting a real effect | 80% (standard) |
| `current_std` | How much your metric varies | Ask your analyst |

---

## Common Questions

### "How long should I run my test?"

Use `sample_size()` and divide by your daily traffic:

```python
plan = binary.sample_size(current_rate=5, lift_percent=10)
plan.with_daily_traffic(10000)  # 10k visitors/day
print(f"Run for at least {plan.test_duration_days} days")
```

### "Is my result significant?"

Check `result.is_significant` - if `True`, you have a winner!

```python
result = binary.analyze(...)
if result.is_significant:
    print(f"Winner: {result.winner}")
else:
    print("Keep running the test")
```

### "What if my test shows no winner?"

That's valuable information! It means the change doesn't have a meaningful impact. Either:
1. The variants are truly equivalent → ship whichever is easier
2. You need more visitors → check if you have enough sample size
3. The effect is smaller than you designed for → re-run with smaller `lift_percent`

---

## Best Practices

1. **Decide sample size BEFORE you start** - Don't peek and stop early
2. **Run for at least 1-2 weeks** - Capture weekly patterns
3. **Don't run too many tests at once** - They can interfere
4. **Statistical significance ≠ business significance** - A 0.1% lift might be "significant" but not worth the effort
5. **Look at confidence intervals, not just p-values** - They tell you the range of possible effects

---

## License

MIT License

---

## Credits

Inspired by [Evan Miller's A/B Testing Tools](https://www.evanmiller.org/ab-testing/).
