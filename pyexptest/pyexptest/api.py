from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional
import os

from pyexptest import binary, continuous

app = FastAPI(
    title="pyexptest API",
    description="Simple A/B testing tools for marketers and analysts",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BinarySampleSizeRequest(BaseModel):
    current_rate: float = Field(..., description="Current conversion rate (e.g., 5 for 5% or 0.05)")
    lift_percent: float = Field(10, description="Minimum lift to detect in % (e.g., 10 for 10%)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    power: int = Field(80, ge=50, le=99, description="Statistical power (50-99)")
    daily_visitors: Optional[int] = Field(None, gt=0, description="Optional: daily traffic for duration estimate")


class BinaryAnalyzeRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Number of visitors in control")
    control_conversions: int = Field(..., ge=0, description="Number of conversions in control")
    variant_visitors: int = Field(..., gt=0, description="Number of visitors in variant")
    variant_conversions: int = Field(..., ge=0, description="Number of conversions in variant")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    test_name: str = Field("A/B Test", description="Name for the summary report")


class BinaryConfidenceIntervalRequest(BaseModel):
    visitors: int = Field(..., gt=0, description="Total visitors")
    conversions: int = Field(..., ge=0, description="Total conversions")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class ContinuousSampleSizeRequest(BaseModel):
    current_mean: float = Field(..., description="Current average value (e.g., $50)")
    current_std: float = Field(..., gt=0, description="Standard deviation")
    lift_percent: float = Field(5, description="Minimum lift to detect in % (e.g., 5 for 5%)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    power: int = Field(80, ge=50, le=99, description="Statistical power (50-99)")
    daily_visitors: Optional[int] = Field(None, gt=0, description="Optional: daily traffic for duration estimate")


class ContinuousAnalyzeRequest(BaseModel):
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


class ContinuousConfidenceIntervalRequest(BaseModel):
    visitors: int = Field(..., gt=1, description="Sample size")
    mean: float = Field(..., description="Sample mean")
    std: float = Field(..., ge=0, description="Standard deviation")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/binary/sample-size")
def binary_sample_size(request: BinarySampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        
        plan = binary.sample_size(
            current_rate=rate,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
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


@app.post("/api/binary/analyze")
def binary_analyze(request: BinaryAnalyzeRequest):
    try:
        result = binary.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        
        return {
            "control_rate": result.control_rate,
            "variant_rate": result.variant_rate,
            "lift_percent": result.lift_percent,
            "lift_absolute": result.lift_absolute,
            "is_significant": result.is_significant,
            "confidence": result.confidence,
            "p_value": result.p_value,
            "confidence_interval": [result.confidence_interval_lower, result.confidence_interval_upper],
            "winner": result.winner,
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/binary/analyze/summary", response_class=PlainTextResponse)
def binary_analyze_summary(request: BinaryAnalyzeRequest):
    try:
        result = binary.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        return binary.summarize(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/binary/sample-size/summary", response_class=PlainTextResponse)
def binary_sample_size_summary(request: BinarySampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        
        plan = binary.sample_size(
            current_rate=rate,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return binary.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/binary/confidence-interval")
def binary_confidence_interval(request: BinaryConfidenceIntervalRequest):
    try:
        result = binary.confidence_interval(
            visitors=request.visitors,
            conversions=request.conversions,
            confidence=request.confidence,
        )
        return {
            "rate": result.rate,
            "lower": result.lower,
            "upper": result.upper,
            "confidence": result.confidence,
            "margin_of_error": result.margin_of_error,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/continuous/sample-size")
def continuous_sample_size(request: ContinuousSampleSizeRequest):
    try:
        plan = continuous.sample_size(
            current_mean=request.current_mean,
            current_std=request.current_std,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
        )
        
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


@app.post("/api/continuous/analyze")
def continuous_analyze(request: ContinuousAnalyzeRequest):
    try:
        result = continuous.analyze(
            control_visitors=request.control_visitors,
            control_mean=request.control_mean,
            control_std=request.control_std,
            variant_visitors=request.variant_visitors,
            variant_mean=request.variant_mean,
            variant_std=request.variant_std,
            confidence=request.confidence,
        )
        
        return {
            "control_mean": result.control_mean,
            "variant_mean": result.variant_mean,
            "lift_percent": result.lift_percent,
            "lift_absolute": result.lift_absolute,
            "is_significant": result.is_significant,
            "confidence": result.confidence,
            "p_value": result.p_value,
            "confidence_interval": [result.confidence_interval_lower, result.confidence_interval_upper],
            "winner": result.winner,
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/continuous/analyze/summary", response_class=PlainTextResponse)
def continuous_analyze_summary(request: ContinuousAnalyzeRequest):
    try:
        result = continuous.analyze(
            control_visitors=request.control_visitors,
            control_mean=request.control_mean,
            control_std=request.control_std,
            variant_visitors=request.variant_visitors,
            variant_mean=request.variant_mean,
            variant_std=request.variant_std,
            confidence=request.confidence,
        )
        return continuous.summarize(
            result, 
            test_name=request.test_name,
            metric_name=request.metric_name,
            currency=request.currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/continuous/sample-size/summary", response_class=PlainTextResponse)
def continuous_sample_size_summary(request: ContinuousSampleSizeRequest):
    try:
        plan = continuous.sample_size(
            current_mean=request.current_mean,
            current_std=request.current_std,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return continuous.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/continuous/confidence-interval")
def continuous_confidence_interval(request: ContinuousConfidenceIntervalRequest):
    try:
        result = continuous.confidence_interval(
            visitors=request.visitors,
            mean=request.mean,
            std=request.std,
            confidence=request.confidence,
        )
        return {
            "mean": result.mean,
            "lower": result.lower,
            "upper": result.upper,
            "confidence": result.confidence,
            "margin_of_error": result.margin_of_error,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
    
    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
