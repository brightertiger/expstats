import pytest
from pyexptest import continuous


class TestContinuousSampleSize:
    def test_basic_calculation(self):
        plan = continuous.sample_size(
            current_mean=50,
            current_std=25,
            lift_percent=5,
            confidence=95,
            power=80,
        )
        assert plan.visitors_per_variant > 0
        assert plan.total_visitors == plan.visitors_per_variant * 2
        assert plan.expected_mean == pytest.approx(52.5)

    def test_higher_lift_needs_fewer_visitors(self):
        plan_small = continuous.sample_size(current_mean=50, current_std=25, lift_percent=5)
        plan_large = continuous.sample_size(current_mean=50, current_std=25, lift_percent=10)
        assert plan_large.visitors_per_variant < plan_small.visitors_per_variant

    def test_higher_variance_needs_more_visitors(self):
        plan_low = continuous.sample_size(current_mean=50, current_std=10, lift_percent=5)
        plan_high = continuous.sample_size(current_mean=50, current_std=25, lift_percent=5)
        assert plan_high.visitors_per_variant > plan_low.visitors_per_variant

    def test_duration_estimation(self):
        plan = continuous.sample_size(current_mean=50, current_std=25, lift_percent=5)
        plan.with_daily_traffic(1000)
        assert plan.test_duration_days is not None
        assert plan.test_duration_days > 0

    def test_invalid_std(self):
        with pytest.raises(ValueError):
            continuous.sample_size(current_mean=50, current_std=-10, lift_percent=5)


class TestContinuousAnalyze:
    def test_significant_result(self):
        result = continuous.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=55,
            variant_std=15,
        )
        assert result.is_significant == True
        assert result.winner == "variant"
        assert result.lift_percent == pytest.approx(10, rel=0.1)

    def test_non_significant_result(self):
        result = continuous.analyze(
            control_visitors=50,
            control_mean=50,
            control_std=25,
            variant_visitors=50,
            variant_mean=51,
            variant_std=25,
        )
        assert result.is_significant == False
        assert result.winner == "no winner yet"

    def test_confidence_interval(self):
        result = continuous.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=52,
            variant_std=15,
        )
        assert result.confidence_interval_lower < result.confidence_interval_upper

    def test_recommendation_provided(self):
        result = continuous.analyze(
            control_visitors=100,
            control_mean=50,
            control_std=15,
            variant_visitors=100,
            variant_mean=55,
            variant_std=15,
        )
        assert result.recommendation is not None
        assert len(result.recommendation) > 0


class TestContinuousConfidenceInterval:
    def test_basic_calculation(self):
        ci = continuous.confidence_interval(visitors=100, mean=50, std=15)
        assert ci.mean == 50
        assert ci.lower < 50 < ci.upper

    def test_higher_confidence_wider_interval(self):
        ci_95 = continuous.confidence_interval(visitors=100, mean=50, std=15, confidence=95)
        ci_99 = continuous.confidence_interval(visitors=100, mean=50, std=15, confidence=99)
        width_95 = ci_95.upper - ci_95.lower
        width_99 = ci_99.upper - ci_99.lower
        assert width_99 > width_95


class TestContinuousSummarize:
    def test_summary_generation(self):
        result = continuous.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=52,
            variant_std=15,
        )
        summary = continuous.summarize(result)
        assert "Control" in summary
        assert "Variant" in summary

    def test_plan_summary_generation(self):
        plan = continuous.sample_size(current_mean=50, current_std=25, lift_percent=5)
        summary = continuous.summarize_plan(plan)
        assert "visitors" in summary.lower()
