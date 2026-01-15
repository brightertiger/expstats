import pytest
from pyexptest import binary


class TestBinarySampleSize:
    def test_basic_calculation(self):
        plan = binary.sample_size(
            current_rate=0.05,
            lift_percent=10,
            confidence=95,
            power=80,
        )
        assert plan.visitors_per_variant > 0
        assert plan.total_visitors == plan.visitors_per_variant * 2
        assert plan.expected_rate == pytest.approx(0.055)

    def test_accepts_percentage_input(self):
        plan = binary.sample_size(current_rate=5, lift_percent=10)
        assert plan.current_rate == 0.05
        assert plan.expected_rate == pytest.approx(0.055)

    def test_higher_lift_needs_fewer_visitors(self):
        plan_small = binary.sample_size(current_rate=0.05, lift_percent=5)
        plan_large = binary.sample_size(current_rate=0.05, lift_percent=20)
        assert plan_large.visitors_per_variant < plan_small.visitors_per_variant

    def test_higher_confidence_needs_more_visitors(self):
        plan_95 = binary.sample_size(current_rate=0.05, lift_percent=10, confidence=95)
        plan_99 = binary.sample_size(current_rate=0.05, lift_percent=10, confidence=99)
        assert plan_99.visitors_per_variant > plan_95.visitors_per_variant

    def test_duration_estimation(self):
        plan = binary.sample_size(current_rate=0.05, lift_percent=10)
        plan.with_daily_traffic(1000)
        assert plan.test_duration_days is not None
        assert plan.test_duration_days > 0

    def test_invalid_rate(self):
        with pytest.raises(ValueError):
            binary.sample_size(current_rate=-0.1, lift_percent=10)
        with pytest.raises(ValueError):
            binary.sample_size(current_rate=101, lift_percent=10)


class TestBinaryAnalyze:
    def test_significant_result(self):
        result = binary.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=600,
        )
        assert result.is_significant == True
        assert result.winner == "variant"
        assert result.lift_percent == pytest.approx(20, rel=0.01)

    def test_non_significant_result(self):
        result = binary.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=52,
        )
        assert result.is_significant == False
        assert result.winner == "no winner yet"

    def test_negative_lift(self):
        result = binary.analyze(
            control_visitors=10000,
            control_conversions=600,
            variant_visitors=10000,
            variant_conversions=500,
        )
        assert result.lift_percent < 0
        if result.is_significant:
            assert result.winner == "control"

    def test_confidence_interval(self):
        result = binary.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=550,
        )
        assert result.confidence_interval_lower < result.confidence_interval_upper
        assert result.confidence_interval_lower < result.lift_absolute < result.confidence_interval_upper

    def test_recommendation_provided(self):
        result = binary.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )
        assert result.recommendation is not None
        assert len(result.recommendation) > 0


class TestBinaryConfidenceInterval:
    def test_basic_calculation(self):
        ci = binary.confidence_interval(visitors=1000, conversions=50)
        assert ci.rate == 0.05
        assert ci.lower < 0.05 < ci.upper

    def test_higher_confidence_wider_interval(self):
        ci_95 = binary.confidence_interval(visitors=1000, conversions=50, confidence=95)
        ci_99 = binary.confidence_interval(visitors=1000, conversions=50, confidence=99)
        width_95 = ci_95.upper - ci_95.lower
        width_99 = ci_99.upper - ci_99.lower
        assert width_99 > width_95

    def test_bounds_within_0_1(self):
        ci = binary.confidence_interval(visitors=100, conversions=5)
        assert ci.lower >= 0
        assert ci.upper <= 1


class TestBinarySummarize:
    def test_summary_generation(self):
        result = binary.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=550,
        )
        summary = binary.summarize(result)
        assert "Control" in summary
        assert "Variant" in summary
        assert "%" in summary

    def test_plan_summary_generation(self):
        plan = binary.sample_size(current_rate=0.05, lift_percent=10)
        summary = binary.summarize_plan(plan)
        assert "visitors" in summary.lower()
        assert "5%" in summary or "5.0%" in summary
