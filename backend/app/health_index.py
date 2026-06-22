from typing import Optional, Tuple


def calc_health_index(
    dissolved_oxygen: Optional[float],
    temperature: Optional[float],
    salinity: Optional[float],
) -> Tuple[Optional[float], list[str]]:
    """
    水质健康指数计算（0~100，越高越好）

    空值处理：某个指标缺失时，从计算中剔除该指标，并重新分配权重。
    若三个指标全部缺失，返回 (None, 缺失列表)。
    """
    missing: list[str] = []
    scores: list[float] = []
    weights: list[float] = []

    if dissolved_oxygen is not None:
        scores.append(_dissolved_oxygen_score(dissolved_oxygen))
        weights.append(0.4)
    else:
        missing.append("dissolved_oxygen")

    if temperature is not None:
        scores.append(_temperature_score(temperature))
        weights.append(0.3)
    else:
        missing.append("temperature")

    if salinity is not None:
        scores.append(_salinity_score(salinity))
        weights.append(0.3)
    else:
        missing.append("salinity")

    if not scores:
        return None, missing

    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]
    raw = sum(s * w for s, w in zip(scores, normalized))
    return round(max(0.0, min(100.0, raw)), 1), missing


def _dissolved_oxygen_score(do: float) -> float:
    if 6 <= do <= 9:
        return 100.0
    if do < 5:
        return max(0.0, do / 5 * 60)
    if do < 6:
        return 60 + (do - 5) / 1 * 40
    if do <= 12:
        return 100 - (do - 9) / 3 * 15
    return max(0.0, 85 - (do - 12) * 5)


def _temperature_score(temp: float) -> float:
    if 18 <= temp <= 26:
        return 100.0
    if temp < 18:
        penalty = (18 - temp) * 5
        return max(0.0, 100 - penalty)
    if temp <= 30:
        penalty = (temp - 26) * 8
        return max(0.0, 100 - penalty)
    penalty = (temp - 30) * 15 + 32
    return max(0.0, 100 - penalty)


def _salinity_score(sal: float) -> float:
    if 28 <= sal <= 34:
        return 100.0
    if sal < 28:
        penalty = (28 - sal) * 5
        return max(0.0, 100 - penalty)
    if sal <= 38:
        penalty = (sal - 34) * 5
        return max(0.0, 100 - penalty)
    penalty = (sal - 38) * 10 + 20
    return max(0.0, 100 - penalty)
