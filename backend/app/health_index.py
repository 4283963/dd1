import math


def calc_health_index(dissolved_oxygen: float, temperature: float, salinity: float) -> float:
    """
    水质健康指数计算（0~100，越高越好）

    三个指标各占权重，偏离最佳范围越远扣分越多：
    - 溶解氧 (权重 0.4): 最佳 6~9 mg/L，海水养殖安全下限 5 mg/L
    - 温度   (权重 0.3): 最佳 18~26 °C，超出范围升温比降温更危险
    - 盐度   (权重 0.3): 最佳 28~34 ‰，近海养殖常见范围

    每个指标得分 = 100 - penalty，最终加权求和
    """
    do_score = _dissolved_oxygen_score(dissolved_oxygen)
    temp_score = _temperature_score(temperature)
    sal_score = _salinity_score(salinity)

    raw = 0.4 * do_score + 0.3 * temp_score + 0.3 * sal_score
    return round(max(0.0, min(100.0, raw)), 1)


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
