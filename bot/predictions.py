from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import math
import random


@dataclass(frozen=True)
class PingRow:
    regular: float
    linear: float
    stepwise: float
    fraction: float
    complex: float
    slope: float


# Baseline table from the prompt (ms -> predictions)
PING_TABLE: Dict[int, PingRow] = {
    1: PingRow(0.0380000000, 0.0261000000, 0.0212000000, 0.1004444444, 0.1005006833, 0.101000000000000),
    10: PingRow(0.0470000000, 0.0360000000, 0.0320000000, 0.1044444444, 0.1050683333, 0.110000000000000),
    20: PingRow(0.0570000000, 0.0470000000, 0.0440000000, 0.1088888889, 0.1102733333, 0.120000000000000),
    30: PingRow(0.0670000000, 0.0580000000, 0.0560000000, 0.1133333333, 0.1156150000, 0.130000000000000),
    40: PingRow(0.0770000000, 0.0690000000, 0.0680000000, 0.1177777778, 0.1210933333, 0.140000000000000),
    50: PingRow(0.0870000000, 0.0800000000, 0.0850000000, 0.1222222222, 0.1267083333, 0.150000000000000),
    60: PingRow(0.0970000000, 0.0910000000, 0.0960000000, 0.1266666667, 0.1324600000, 0.160000000000000),
    70: PingRow(0.1070000000, 0.1020000000, 0.1070000000, 0.1311111111, 0.1383483333, 0.170000000000000),
    80: PingRow(0.1170000000, 0.1130000000, 0.1180000000, 0.1355555556, 0.1443733333, 0.180000000000000),
    90: PingRow(0.1270000000, 0.1240000000, 0.1290000000, 0.1400000000, 0.1505350000, 0.190000000000000),
    100: PingRow(0.1370000000, 0.1350000000, 0.1450000000, 0.1444444444, 0.1568333333, 0.200000000000000),
    110: PingRow(0.1470000000, 0.1460000000, 0.1555000000, 0.1488888889, 0.1632683333, 0.210000000000000),
    120: PingRow(0.1570000000, 0.1570000000, 0.1660000000, 0.1533333333, 0.1698400000, 0.220000000000000),
    130: PingRow(0.1630000000, 0.1680000000, 0.1765000000, 0.1577777778, 0.1765483333, 0.230000000000000),
    140: PingRow(0.1730000000, 0.1790000000, 0.1870000000, 0.1622222222, 0.1833933333, 0.240000000000000),
    150: PingRow(0.1830000000, 0.1900000000, 0.1975000000, 0.1666666667, 0.1903750000, 0.250000000000000),
    160: PingRow(0.1930000000, 0.2010000000, 0.2080000000, 0.1711111111, 0.1974933333, 0.260000000000000),
    170: PingRow(0.2030000000, 0.2120000000, 0.2185000000, 0.1755555556, 0.2047483333, 0.270000000000000),
    180: PingRow(0.2130000000, 0.2230000000, 0.2290000000, 0.1800000000, 0.2121400000, 0.280000000000000),
    190: PingRow(0.2230000000, 0.2340000000, 0.2395000000, 0.1844444444, 0.2196683333, 0.290000000000000),
    200: PingRow(0.2330000000, 0.2450000000, 0.2500000000, 0.1888888889, 0.2273333333, 0.300000000000000),
    210: PingRow(0.2430000000, 0.2560000000, 0.2605000000, 0.1933333333, 0.2351350000, 0.310000000000000),
    220: PingRow(0.2530000000, 0.2670000000, 0.2710000000, 0.1977777778, 0.2430733333, 0.320000000000000),
    230: PingRow(0.2630000000, 0.2780000000, 0.2815000000, 0.2022222222, 0.2511483333, 0.330000000000000),
    240: PingRow(0.2730000000, 0.2890000000, 0.2920000000, 0.2066666667, 0.2593600000, 0.340000000000000),
    250: PingRow(0.2830000000, 0.3000000000, 0.3025000000, 0.2111111111, 0.2677083333, 0.350000000000000),
}


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def interpolate_row(ping_ms: float) -> PingRow:
    # Clamp to known range
    min_ping, max_ping = min(PING_TABLE), max(PING_TABLE)
    p = _clamp(ping_ms, float(min_ping), float(max_ping))

    if int(p) in PING_TABLE:
        return PING_TABLE[int(p)]

    # Find bracketing keys
    keys = sorted(PING_TABLE.keys())
    lower = max([k for k in keys if k <= p])
    upper = min([k for k in keys if k >= p])
    if lower == upper:
        return PING_TABLE[int(lower)]

    t = (p - lower) / (upper - lower)
    a, b = PING_TABLE[lower], PING_TABLE[upper]
    return PingRow(
        regular=_lerp(a.regular, b.regular, t),
        linear=_lerp(a.linear, b.linear, t),
        stepwise=_lerp(a.stepwise, b.stepwise, t),
        fraction=_lerp(a.fraction, b.fraction, t),
        complex=_lerp(a.complex, b.complex, t),
        slope=_lerp(a.slope, b.slope, t),
    )


def _blend(values: List[float], weights: List[float]) -> float:
    s = sum(w for w in weights)
    if s == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / s


def _apply_mode_shaping(value: float, type_: str, mode: str) -> float:
    # type_: blatant|hvh; mode: camlock|targetaim
    shaped = value
    if type_ == "blatant":
        shaped *= 1.0
        shaped = shaped + 0.0003 * math.tanh(12 * shaped)
    else:  # hvh
        shaped *= 0.995
        shaped = shaped + 0.0006 * math.tanh(10 * shaped)

    if mode == "camlock":
        shaped *= 0.998
    else:  # targetaim
        shaped *= 1.002
    return shaped


def _quantize_with_prefix(value: float, total_decimals: int, starter_digits: float | None) -> float:
    decimals = max(0, total_decimals)
    # Build decimal digits from shaped value
    shaped_str = f"{abs(value):.{decimals + 8}f"  # extra for source digits
    int_part, frac_part = shaped_str.split(".", 1)

    if starter_digits is not None:
        # Extract fractional digits of the starter
        starter_str = f"{abs(float(starter_digits)):.16f}"
        _, starter_frac = starter_str.split(".", 1)
        # Remove trailing zeros from starter to avoid forcing too many zeros
        starter_frac = starter_frac.rstrip("0")
        # Compose: prefix + remainder from shaped
        composed = (starter_frac + frac_part)
        new_frac = composed[:decimals] if decimals > 0 else ""
    else:
        new_frac = frac_part[:decimals] if decimals > 0 else ""

    final_str = ("-" if value < 0 else "") + int_part + ("." + new_frac if decimals > 0 else "")
    try:
        return float(final_str)
    except ValueError:
        return round(value, decimals)


def _slope_variant(base: float, distance_tag: str) -> float:
    if distance_tag == "close":
        return base * 0.997
    if distance_tag == "mid":
        return base * 1.000
    return base * 1.003  # far


def generate_single_prediction(
    ping_ms: float,
    type_: str,
    mode: str,
    digits: int,
    starterdigit: float | None,
    rng: random.Random,
) -> float:
    row = interpolate_row(ping_ms)

    close = _slope_variant(row.slope, "close")
    mid = _slope_variant(row.slope, "mid")
    far = _slope_variant(row.slope, "far")

    components = [
        row.regular,
        row.linear,
        row.stepwise,
        row.fraction,
        row.complex,
        close,
        mid,
        far,
    ]
    weights = [1.0, 1.0, 0.8, 0.6, 1.3, 0.8, 1.1, 0.9]

    base = _blend(components, weights)
    jitter = (rng.random() - 0.5) * 0.0006
    base = base + jitter
    shaped = _apply_mode_shaping(base, type_=type_, mode=mode)

    return _quantize_with_prefix(shaped, digits, starterdigit)


def generate_xy_prediction(
    ping_ms: float,
    type_: str,
    mode: str,
    digits: int,
    starterdigit: float | None,
    rng: random.Random,
) -> Tuple[float, float]:
    row = interpolate_row(ping_ms)

    # X axis
    x_components = [row.regular, row.linear, row.complex, row.slope]
    x_weights = [1.2, 1.3, 1.0, 0.8]
    x_base = _blend(x_components, x_weights)
    x_base += (rng.random() - 0.5) * 0.0005
    x_shaped = _apply_mode_shaping(x_base, type_, mode)
    x_final = _quantize_with_prefix(x_shaped, digits, starterdigit)

    # Y axis
    close = _slope_variant(row.slope, "close")
    mid = _slope_variant(row.slope, "mid")
    far = _slope_variant(row.slope, "far")
    y_components = [row.stepwise, row.fraction, close, mid, far]
    y_weights = [1.0, 0.7, 0.9, 1.1, 1.0]
    y_base = _blend(y_components, y_weights)
    y_base += (rng.random() - 0.5) * 0.0007
    y_shaped = _apply_mode_shaping(y_base, type_, mode)
    y_final = _quantize_with_prefix(y_shaped, digits, starterdigit)

    return x_final, y_final


def parse_ping(ping_str: str, rng: random.Random) -> Tuple[float, float, float, bool]:
    """Parse ping input. Returns (avg, lo, hi, is_range)."""
    s = ping_str.replace(" ", "")
    if "-" in s:
        lo_s, hi_s = s.split("-", 1)
        lo, hi = float(lo_s), float(hi_s)
        lo, hi = min(lo, hi), max(lo, hi)
        avg = (lo + hi) / 2.0
        return avg, lo, hi, True
    val = float(s)
    return val, val, val, False


def format_file_content(
    count: int,
    type_: str,
    xy: bool,
    predictions: List[float] | List[Tuple[float, float]],
) -> str:
    lines: List[str] = []
    lines.append(f"Generated {count} predictions")
    lines.append(f"Mode: {type_}")
    lines.append("---")
    lines.append("┌ Predictions:")
    if not xy:
        for i, v in enumerate(predictions):
            prefix = "├" if i < count - 1 else "└"
            lines.append(f"{prefix} {v}")
    else:
        for i, (x, y) in enumerate(predictions):
            if i < count - 1:
                lines.append(f"├ X: {x}")
                lines.append(f"├ Y: {y}")
            else:
                lines.append(f"├ X: {x}")
                lines.append(f"└ Y: {y}")
    return "\n".join(lines) + "\n"