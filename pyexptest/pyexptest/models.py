from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class SampleSizeResult(BaseModel):
    visitors_per_variation: int
    total_visitors: int
    control_conversion_rate: Optional[float] = None
    variant_conversion_rate: Optional[float] = None
    minimum_detectable_lift: float
    lift_type: Literal["absolute", "relative"]
    confidence_level: float
    statistical_power: float
    test_type: Literal["one-tailed", "two-tailed"]
    traffic_split: float = 1.0
    control_visitors: Optional[int] = None
    variant_visitors: Optional[int] = None
    assumptions: List[str] = Field(default_factory=list)
    
    @property
    def sample_size_per_group(self) -> int:
        return self.visitors_per_variation
    
    @property
    def total_sample_size(self) -> int:
        return self.total_visitors

class ContinuousSampleSizeResult(BaseModel):
    visitors_per_variation: int
    total_visitors: int
    control_mean: float
    variant_mean: float
    standard_deviation: float
    minimum_detectable_lift: float
    lift_type: Literal["absolute", "relative"]
    confidence_level: float
    statistical_power: float
    test_type: Literal["one-tailed", "two-tailed"]
    traffic_split: float = 1.0
    control_visitors: Optional[int] = None
    variant_visitors: Optional[int] = None
    assumptions: List[str] = Field(default_factory=list)
    
    @property
    def sample_size_per_group(self) -> int:
        return self.visitors_per_variation

class PowerResult(BaseModel):
    statistical_power: float
    visitors_per_variation: int
    control_conversion_rate: Optional[float] = None
    variant_conversion_rate: Optional[float] = None
    effect_size: float
    confidence_level: float
    test_type: Literal["one-tailed", "two-tailed"]
    traffic_split: float = 1.0
    
    @property
    def power(self) -> float:
        return self.statistical_power

class ContinuousPowerResult(BaseModel):
    statistical_power: float
    visitors_per_variation: int
    control_mean: float
    variant_mean: float
    standard_deviation: float
    effect_size: float
    confidence_level: float
    test_type: Literal["one-tailed", "two-tailed"]
    traffic_split: float = 1.0
    
    @property
    def power(self) -> float:
        return self.statistical_power

class ABTestResult(BaseModel):
    z_score: float
    p_value: float
    confidence_interval: tuple[float, float]
    is_significant: bool
    confidence_level: float
    effect_size: float
    relative_lift: Optional[float] = None
    absolute_lift: Optional[float] = None
    control_conversion_rate: Optional[float] = None
    variant_conversion_rate: Optional[float] = None
    test_name: str
    test_type: Literal["one-tailed", "two-tailed"]
    winner: Optional[Literal["control", "variant", "none"]] = None
    
    @property
    def statistically_significant(self) -> bool:
        return self.is_significant
    
    @property
    def statistic(self) -> float:
        return self.z_score

class TTestResult(BaseModel):
    t_statistic: float
    p_value: float
    confidence_interval: tuple[float, float]
    is_significant: bool
    confidence_level: float
    effect_size: float
    degrees_of_freedom: float
    mean_difference: float
    control_mean: float
    variant_mean: float
    test_name: str = "welch_t_test"
    test_type: Literal["one-tailed", "two-tailed"]
    winner: Optional[Literal["control", "variant", "none"]] = None
    
    @property
    def statistically_significant(self) -> bool:
        return self.is_significant
    
    @property
    def statistic(self) -> float:
        return self.t_statistic

class NonInferiorityResult(BaseModel):
    z_score: float
    p_value: float
    confidence_interval: tuple[float, float]
    is_non_inferior: bool
    margin: float
    confidence_level: float
    observed_difference: float
    lower_bound: float
    test_name: str = "non_inferiority"
    
    @property
    def non_inferior(self) -> bool:
        return self.is_non_inferior

class ConfidenceIntervalResult(BaseModel):
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    margin_of_error: float
    method: str


SignificanceTestResult = ABTestResult
