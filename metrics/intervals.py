"""Desvio amostral e intervalo de confiança de 95% (t de Student), só com a stdlib."""

from math import sqrt
from statistics import NormalDist, fmean, stdev

# t bicaudal de 95% (quantil 0,975) para 1 a 30 graus de liberdade.
_T_975 = (
    12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
    2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
    2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042,
)


def t_critical_95(degrees_of_freedom: int) -> float:
    """Quantil 0,975 da t de Student; acima de 30 usa a expansão de Cornish-Fisher."""
    if degrees_of_freedom < 1:
        raise ValueError("Os graus de liberdade devem ser ao menos 1.")
    if degrees_of_freedom <= len(_T_975):
        return _T_975[degrees_of_freedom - 1]
    z = NormalDist().inv_cdf(0.975)
    nu = degrees_of_freedom
    return (
        z + (z ** 3 + z) / (4 * nu)
        + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * nu ** 2)
    )


def sample_stddev(values: list[float]) -> float | None:
    """Desvio-padrão amostral (n - 1); indefinido (None) com menos de 2 valores."""
    return stdev(values) if len(values) >= 2 else None


def confidence_interval_95(values: list[float]) -> tuple[float, float] | None:
    """(limite inferior, limite superior) de média ± t·s/√n; None com n < 2."""
    if len(values) < 2:
        return None
    half_width = t_critical_95(len(values) - 1) * stdev(values) / sqrt(len(values))
    center = fmean(values)
    return center - half_width, center + half_width
