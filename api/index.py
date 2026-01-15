from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional, List

from pyexptest import conversion, magnitude, timing

app = FastAPI(
    title="pyexptest API",
    description="Simple A/B testing tools for marketers and analysts",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class ConversionSampleSizeRequest(BaseModel):
    current_rate: float = Field(..., description="Current conversion rate (e.g., 5 for 5% or 0.05)")
    lift_percent: float = Field(10, description="Minimum lift to detect in % (e.g., 10 for 10%)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    power: int = Field(80, ge=50, le=99, description="Statistical power (50-99)")
    daily_visitors: Optional[int] = Field(None, gt=0, description="Optional: daily traffic for duration estimate")
    num_variants: int = Field(2, ge=2, le=10, description="Number of variants including control")


class ConversionAnalyzeRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Number of visitors in control")
    control_conversions: int = Field(..., ge=0, description="Number of conversions in control")
    variant_visitors: int = Field(..., gt=0, description="Number of visitors in variant")
    variant_conversions: int = Field(..., ge=0, description="Number of conversions in variant")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    test_name: str = Field("A/B Test", description="Name for the summary report")


class ConversionVariant(BaseModel):
    name: str = Field(..., description="Variant name (e.g., 'control', 'variant_a')")
    visitors: int = Field(..., gt=0, description="Number of visitors")
    conversions: int = Field(..., ge=0, description="Number of conversions")


class ConversionMultiAnalyzeRequest(BaseModel):
    variants: List[ConversionVariant] = Field(..., min_length=2, description="List of variants")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    correction: Literal["bonferroni", "none"] = Field("bonferroni", description="Multiple comparison correction")
    test_name: str = Field("Multi-Variant Test", description="Name for the summary report")


class ConversionConfidenceIntervalRequest(BaseModel):
    visitors: int = Field(..., gt=0, description="Total visitors")
    conversions: int = Field(..., ge=0, description="Total conversions")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class MagnitudeSampleSizeRequest(BaseModel):
    current_mean: float = Field(..., description="Current average value (e.g., $50)")
    current_std: float = Field(..., gt=0, description="Standard deviation")
    lift_percent: float = Field(5, description="Minimum lift to detect in % (e.g., 5 for 5%)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    power: int = Field(80, ge=50, le=99, description="Statistical power (50-99)")
    daily_visitors: Optional[int] = Field(None, gt=0, description="Optional: daily traffic for duration estimate")
    num_variants: int = Field(2, ge=2, le=10, description="Number of variants including control")


class MagnitudeAnalyzeRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Number of visitors in control")
    control_mean: float = Field(..., description="Average value in control")
    control_std: float = Field(..., ge=0, description="Standard deviation in control")
    variant_visitors: int = Field(..., gt=0, description="Number of visitors in variant")
    variant_mean: float = Field(..., description="Average value in variant")
    variant_std: float = Field(..., ge=0, description="Standard deviation in variant")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    test_name: str = Field("Revenue Test", description="Name for the summary report")
    metric_name: str = Field("Average Order Value", description="Name of the metric")
    currency: str = Field("$", description="Currency symbol")


class MagnitudeVariant(BaseModel):
    name: str = Field(..., description="Variant name (e.g., 'control', 'variant_a')")
    visitors: int = Field(..., gt=0, description="Sample size")
    mean: float = Field(..., description="Average value")
    std: float = Field(..., ge=0, description="Standard deviation")


class MagnitudeMultiAnalyzeRequest(BaseModel):
    variants: List[MagnitudeVariant] = Field(..., min_length=2, description="List of variants")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    correction: Literal["bonferroni", "none"] = Field("bonferroni", description="Multiple comparison correction")
    test_name: str = Field("Multi-Variant Test", description="Name for the summary report")
    metric_name: str = Field("Average Value", description="Name of the metric")
    currency: str = Field("$", description="Currency symbol")


class MagnitudeConfidenceIntervalRequest(BaseModel):
    visitors: int = Field(..., gt=1, description="Sample size")
    mean: float = Field(..., description="Sample mean")
    std: float = Field(..., ge=0, description="Standard deviation")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class ConversionDiffInDiffRequest(BaseModel):
    control_pre_visitors: int = Field(..., gt=0)
    control_pre_conversions: int = Field(..., ge=0)
    control_post_visitors: int = Field(..., gt=0)
    control_post_conversions: int = Field(..., ge=0)
    treatment_pre_visitors: int = Field(..., gt=0)
    treatment_pre_conversions: int = Field(..., ge=0)
    treatment_post_visitors: int = Field(..., gt=0)
    treatment_post_conversions: int = Field(..., ge=0)
    confidence: int = Field(95, ge=80, le=99)
    test_name: str = Field("Difference-in-Differences Analysis")


class MagnitudeDiffInDiffRequest(BaseModel):
    control_pre_n: int = Field(..., gt=0)
    control_pre_mean: float
    control_pre_std: float = Field(..., ge=0)
    control_post_n: int = Field(..., gt=0)
    control_post_mean: float
    control_post_std: float = Field(..., ge=0)
    treatment_pre_n: int = Field(..., gt=0)
    treatment_pre_mean: float
    treatment_pre_std: float = Field(..., ge=0)
    treatment_post_n: int = Field(..., gt=0)
    treatment_post_mean: float
    treatment_post_std: float = Field(..., ge=0)
    confidence: int = Field(95, ge=80, le=99)
    test_name: str = Field("Difference-in-Differences Analysis")
    metric_name: str = Field("Average Value")
    currency: str = Field("$")


class TimingAnalyzeRequest(BaseModel):
    control_times: List[float]
    control_events: List[int]
    treatment_times: List[float]
    treatment_events: List[int]
    confidence: int = Field(95, ge=80, le=99)


class TimingSampleSizeRequest(BaseModel):
    control_median: float = Field(..., gt=0)
    treatment_median: float = Field(..., gt=0)
    confidence: int = Field(95, ge=80, le=99)
    power: int = Field(80, ge=50, le=99)
    dropout_rate: float = Field(0.1, ge=0, lt=1)


class TimingSurvivalCurveRequest(BaseModel):
    times: List[float]
    events: List[int]
    confidence: int = Field(95, ge=80, le=99)


class TimingRateAnalyzeRequest(BaseModel):
    control_events: int = Field(..., ge=0)
    control_exposure: float = Field(..., gt=0)
    treatment_events: int = Field(..., ge=0)
    treatment_exposure: float = Field(..., gt=0)
    confidence: int = Field(95, ge=80, le=99)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/conversion/sample-size")
def conversion_sample_size(request: ConversionSampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        
        plan = conversion.sample_size(
            current_rate=rate,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
            num_variants=request.num_variants,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return {
            "visitors_per_variant": plan.visitors_per_variant,
            "total_visitors": plan.total_visitors,
            "current_rate": plan.current_rate,
            "expected_rate": plan.expected_rate,
            "lift_percent": plan.lift_percent,
            "confidence": plan.confidence,
            "power": plan.power,
            "test_duration_days": plan.test_duration_days,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze")
def conversion_analyze(request: ConversionAnalyzeRequest):
    try:
        result = conversion.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        
        return {
            "control_rate": float(result.control_rate),
            "variant_rate": float(result.variant_rate),
            "lift_percent": float(result.lift_percent),
            "lift_absolute": float(result.lift_absolute),
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "winner": str(result.winner),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze-multi")
def conversion_analyze_multi(request: ConversionMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "conversions": v.conversions} for v in request.variants]
        
        result = conversion.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        
        return {
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "test_statistic": float(result.test_statistic),
            "degrees_of_freedom": int(result.degrees_of_freedom),
            "best_variant": str(result.best_variant),
            "worst_variant": str(result.worst_variant),
            "variants": [
                {"name": str(v.name), "visitors": int(v.visitors), "conversions": int(v.conversions), "rate": float(v.rate)}
                for v in result.variants
            ],
            "pairwise_comparisons": [
                {
                    "variant_a": str(p.variant_a),
                    "variant_b": str(p.variant_b),
                    "rate_a": float(p.rate_a),
                    "rate_b": float(p.rate_b),
                    "lift_percent": float(p.lift_percent),
                    "lift_absolute": float(p.lift_absolute),
                    "p_value": float(p.p_value),
                    "p_value_adjusted": float(p.p_value_adjusted),
                    "is_significant": bool(p.is_significant),
                    "confidence_interval": [float(p.confidence_interval_lower), float(p.confidence_interval_upper)],
                }
                for p in result.pairwise_comparisons
            ],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze-multi/summary", response_class=PlainTextResponse)
def conversion_analyze_multi_summary(request: ConversionMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "conversions": v.conversions} for v in request.variants]
        result = conversion.analyze_multi(variants=variants, confidence=request.confidence, correction=request.correction)
        return conversion.summarize_multi(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze/summary", response_class=PlainTextResponse)
def conversion_analyze_summary(request: ConversionAnalyzeRequest):
    try:
        result = conversion.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        return conversion.summarize(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/sample-size/summary", response_class=PlainTextResponse)
def conversion_sample_size_summary(request: ConversionSampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        plan = conversion.sample_size(current_rate=rate, lift_percent=request.lift_percent, confidence=request.confidence, power=request.power, num_variants=request.num_variants)
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        return conversion.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/confidence-interval")
def conversion_confidence_interval(request: ConversionConfidenceIntervalRequest):
    try:
        result = conversion.confidence_interval(visitors=request.visitors, conversions=request.conversions, confidence=request.confidence)
        return {"rate": result.rate, "lower": result.lower, "upper": result.upper, "confidence": result.confidence, "margin_of_error": result.margin_of_error}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/sample-size")
def magnitude_sample_size(request: MagnitudeSampleSizeRequest):
    try:
        plan = magnitude.sample_size(current_mean=request.current_mean, current_std=request.current_std, lift_percent=request.lift_percent, confidence=request.confidence, power=request.power, num_variants=request.num_variants)
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        return {
            "visitors_per_variant": plan.visitors_per_variant,
            "total_visitors": plan.total_visitors,
            "current_mean": plan.current_mean,
            "expected_mean": plan.expected_mean,
            "standard_deviation": plan.standard_deviation,
            "lift_percent": plan.lift_percent,
            "confidence": plan.confidence,
            "power": plan.power,
            "test_duration_days": plan.test_duration_days,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze")
def magnitude_analyze(request: MagnitudeAnalyzeRequest):
    try:
        result = magnitude.analyze(
            control_visitors=request.control_visitors,
            control_mean=request.control_mean,
            control_std=request.control_std,
            variant_visitors=request.variant_visitors,
            variant_mean=request.variant_mean,
            variant_std=request.variant_std,
            confidence=request.confidence,
        )
        return {
            "control_mean": float(result.control_mean),
            "variant_mean": float(result.variant_mean),
            "lift_percent": float(result.lift_percent),
            "lift_absolute": float(result.lift_absolute),
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "winner": str(result.winner),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze-multi")
def magnitude_analyze_multi(request: MagnitudeMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "mean": v.mean, "std": v.std} for v in request.variants]
        result = magnitude.analyze_multi(variants=variants, confidence=request.confidence, correction=request.correction)
        return {
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "f_statistic": float(result.f_statistic),
            "df_between": int(result.df_between),
            "df_within": int(result.df_within),
            "best_variant": str(result.best_variant),
            "worst_variant": str(result.worst_variant),
            "variants": [{"name": str(v.name), "visitors": int(v.visitors), "mean": float(v.mean), "std": float(v.std)} for v in result.variants],
            "pairwise_comparisons": [
                {
                    "variant_a": str(p.variant_a), "variant_b": str(p.variant_b),
                    "mean_a": float(p.mean_a), "mean_b": float(p.mean_b),
                    "lift_percent": float(p.lift_percent), "lift_absolute": float(p.lift_absolute),
                    "p_value": float(p.p_value), "p_value_adjusted": float(p.p_value_adjusted),
                    "is_significant": bool(p.is_significant),
                    "confidence_interval": [float(p.confidence_interval_lower), float(p.confidence_interval_upper)],
                }
                for p in result.pairwise_comparisons
            ],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze-multi/summary", response_class=PlainTextResponse)
def magnitude_analyze_multi_summary(request: MagnitudeMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "mean": v.mean, "std": v.std} for v in request.variants]
        result = magnitude.analyze_multi(variants=variants, confidence=request.confidence, correction=request.correction)
        return magnitude.summarize_multi(result, test_name=request.test_name, metric_name=request.metric_name, currency=request.currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze/summary", response_class=PlainTextResponse)
def magnitude_analyze_summary(request: MagnitudeAnalyzeRequest):
    try:
        result = magnitude.analyze(
            control_visitors=request.control_visitors, control_mean=request.control_mean, control_std=request.control_std,
            variant_visitors=request.variant_visitors, variant_mean=request.variant_mean, variant_std=request.variant_std,
            confidence=request.confidence,
        )
        return magnitude.summarize(result, test_name=request.test_name, metric_name=request.metric_name, currency=request.currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/sample-size/summary", response_class=PlainTextResponse)
def magnitude_sample_size_summary(request: MagnitudeSampleSizeRequest):
    try:
        plan = magnitude.sample_size(current_mean=request.current_mean, current_std=request.current_std, lift_percent=request.lift_percent, confidence=request.confidence, power=request.power, num_variants=request.num_variants)
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        return magnitude.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/confidence-interval")
def magnitude_confidence_interval(request: MagnitudeConfidenceIntervalRequest):
    try:
        result = magnitude.confidence_interval(visitors=request.visitors, mean=request.mean, std=request.std, confidence=request.confidence)
        return {"mean": result.mean, "lower": result.lower, "upper": result.upper, "confidence": result.confidence, "margin_of_error": result.margin_of_error}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/diff-in-diff")
def conversion_diff_in_diff(request: ConversionDiffInDiffRequest):
    try:
        result = conversion.diff_in_diff(
            control_pre_visitors=request.control_pre_visitors, control_pre_conversions=request.control_pre_conversions,
            control_post_visitors=request.control_post_visitors, control_post_conversions=request.control_post_conversions,
            treatment_pre_visitors=request.treatment_pre_visitors, treatment_pre_conversions=request.treatment_pre_conversions,
            treatment_post_visitors=request.treatment_post_visitors, treatment_post_conversions=request.treatment_post_conversions,
            confidence=request.confidence,
        )
        return {
            "control_pre_rate": float(result.control_pre_rate), "control_post_rate": float(result.control_post_rate),
            "treatment_pre_rate": float(result.treatment_pre_rate), "treatment_post_rate": float(result.treatment_post_rate),
            "control_change": float(result.control_change), "treatment_change": float(result.treatment_change),
            "diff_in_diff": float(result.diff_in_diff), "diff_in_diff_percent": float(result.diff_in_diff_percent),
            "is_significant": bool(result.is_significant), "confidence": int(result.confidence),
            "p_value": float(result.p_value), "z_statistic": float(result.z_statistic),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/diff-in-diff/summary", response_class=PlainTextResponse)
def conversion_diff_in_diff_summary(request: ConversionDiffInDiffRequest):
    try:
        result = conversion.diff_in_diff(
            control_pre_visitors=request.control_pre_visitors, control_pre_conversions=request.control_pre_conversions,
            control_post_visitors=request.control_post_visitors, control_post_conversions=request.control_post_conversions,
            treatment_pre_visitors=request.treatment_pre_visitors, treatment_pre_conversions=request.treatment_pre_conversions,
            treatment_post_visitors=request.treatment_post_visitors, treatment_post_conversions=request.treatment_post_conversions,
            confidence=request.confidence,
        )
        return conversion.summarize_diff_in_diff(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/diff-in-diff")
def magnitude_diff_in_diff(request: MagnitudeDiffInDiffRequest):
    try:
        result = magnitude.diff_in_diff(
            control_pre_n=request.control_pre_n, control_pre_mean=request.control_pre_mean, control_pre_std=request.control_pre_std,
            control_post_n=request.control_post_n, control_post_mean=request.control_post_mean, control_post_std=request.control_post_std,
            treatment_pre_n=request.treatment_pre_n, treatment_pre_mean=request.treatment_pre_mean, treatment_pre_std=request.treatment_pre_std,
            treatment_post_n=request.treatment_post_n, treatment_post_mean=request.treatment_post_mean, treatment_post_std=request.treatment_post_std,
            confidence=request.confidence,
        )
        return {
            "control_pre_mean": float(result.control_pre_mean), "control_post_mean": float(result.control_post_mean),
            "treatment_pre_mean": float(result.treatment_pre_mean), "treatment_post_mean": float(result.treatment_post_mean),
            "control_change": float(result.control_change), "treatment_change": float(result.treatment_change),
            "diff_in_diff": float(result.diff_in_diff), "diff_in_diff_percent": float(result.diff_in_diff_percent),
            "is_significant": bool(result.is_significant), "confidence": int(result.confidence),
            "p_value": float(result.p_value), "t_statistic": float(result.t_statistic),
            "degrees_of_freedom": float(result.degrees_of_freedom),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/diff-in-diff/summary", response_class=PlainTextResponse)
def magnitude_diff_in_diff_summary(request: MagnitudeDiffInDiffRequest):
    try:
        result = magnitude.diff_in_diff(
            control_pre_n=request.control_pre_n, control_pre_mean=request.control_pre_mean, control_pre_std=request.control_pre_std,
            control_post_n=request.control_post_n, control_post_mean=request.control_post_mean, control_post_std=request.control_post_std,
            treatment_pre_n=request.treatment_pre_n, treatment_pre_mean=request.treatment_pre_mean, treatment_pre_std=request.treatment_pre_std,
            treatment_post_n=request.treatment_post_n, treatment_post_mean=request.treatment_post_mean, treatment_post_std=request.treatment_post_std,
            confidence=request.confidence,
        )
        return magnitude.summarize_diff_in_diff(result, test_name=request.test_name, metric_name=request.metric_name, currency=request.currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/analyze")
def timing_analyze(request: TimingAnalyzeRequest):
    try:
        result = timing.analyze(
            control_times=request.control_times, control_events=request.control_events,
            treatment_times=request.treatment_times, treatment_events=request.treatment_events,
            confidence=request.confidence,
        )
        return {
            "control_median_time": result.control_median_time, "treatment_median_time": result.treatment_median_time,
            "control_events": result.control_events, "control_censored": result.control_censored,
            "treatment_events": result.treatment_events, "treatment_censored": result.treatment_censored,
            "hazard_ratio": float(result.hazard_ratio),
            "hazard_ratio_ci": [float(result.hazard_ratio_ci_lower), float(result.hazard_ratio_ci_upper)],
            "time_saved": result.time_saved, "time_saved_percent": result.time_saved_percent,
            "is_significant": bool(result.is_significant), "confidence": result.confidence,
            "p_value": float(result.p_value), "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/sample-size")
def timing_sample_size(request: TimingSampleSizeRequest):
    try:
        plan = timing.sample_size(
            control_median=request.control_median, treatment_median=request.treatment_median,
            confidence=request.confidence, power=request.power, dropout_rate=request.dropout_rate,
        )
        return {
            "subjects_per_group": plan.subjects_per_group, "total_subjects": plan.total_subjects,
            "expected_events_per_group": plan.expected_events_per_group, "total_expected_events": plan.total_expected_events,
            "control_median": plan.control_median, "treatment_median": plan.treatment_median,
            "hazard_ratio": float(plan.hazard_ratio), "confidence": plan.confidence, "power": plan.power,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/survival-curve")
def timing_survival_curve(request: TimingSurvivalCurveRequest):
    try:
        curve = timing.survival_curve(times=request.times, events=request.events, confidence=request.confidence)
        return {
            "times": curve.times, "survival_probabilities": curve.survival_probabilities,
            "confidence_lower": curve.confidence_lower, "confidence_upper": curve.confidence_upper,
            "median_time": curve.median_time, "events": curve.events, "censored": curve.censored, "total": curve.total,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/rates/analyze")
def timing_rate_analyze(request: TimingRateAnalyzeRequest):
    try:
        result = timing.analyze_rates(
            control_events=request.control_events, control_exposure=request.control_exposure,
            treatment_events=request.treatment_events, treatment_exposure=request.treatment_exposure,
            confidence=request.confidence,
        )
        return {
            "control_rate": float(result.control_rate), "treatment_rate": float(result.treatment_rate),
            "control_events": result.control_events, "control_exposure": float(result.control_exposure),
            "treatment_events": result.treatment_events, "treatment_exposure": float(result.treatment_exposure),
            "rate_ratio": float(result.rate_ratio),
            "rate_ratio_ci": [float(result.rate_ratio_ci_lower), float(result.rate_ratio_ci_upper)],
            "rate_difference": float(result.rate_difference), "rate_difference_percent": float(result.rate_difference_percent),
            "is_significant": bool(result.is_significant), "confidence": result.confidence,
            "p_value": float(result.p_value), "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
