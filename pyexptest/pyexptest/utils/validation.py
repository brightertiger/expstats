from typing import Union

def validate_rate(value: float, name: str = "rate") -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")
    return float(value)

def validate_positive(value: Union[int, float], name: str = "value", allow_zero: bool = False) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} must be non-negative, got {value}")
    else:
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")
    return float(value)

def validate_alpha(alpha: float) -> float:
    if not isinstance(alpha, (int, float)):
        raise TypeError(f"alpha must be a number, got {type(alpha).__name__}")
    if alpha <= 0 or alpha >= 1:
        raise ValueError(f"alpha must be between 0 and 1 (exclusive), got {alpha}")
    return float(alpha)

def validate_power(power: float) -> float:
    if not isinstance(power, (int, float)):
        raise TypeError(f"power must be a number, got {type(power).__name__}")
    if power <= 0 or power >= 1:
        raise ValueError(f"power must be between 0 and 1 (exclusive), got {power}")
    return float(power)

def validate_sample_size(n: int, name: str = "sample_size") -> int:
    if not isinstance(n, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"{name} must be positive, got {n}")
    return int(n)

def validate_sidedness(sidedness: str) -> str:
    valid = ["one-sided", "two-sided"]
    if sidedness not in valid:
        raise ValueError(f"sidedness must be one of {valid}, got {sidedness}")
    return sidedness

def validate_allocation_ratio(ratio: float) -> float:
    if not isinstance(ratio, (int, float)):
        raise TypeError(f"allocation_ratio must be a number, got {type(ratio).__name__}")
    if ratio <= 0:
        raise ValueError(f"allocation_ratio must be positive, got {ratio}")
    return float(ratio)
