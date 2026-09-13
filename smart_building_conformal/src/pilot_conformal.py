"""Fixed ordinary split conformal using each model's absolute calibration error."""
from decimal import Decimal, ROUND_CEILING
import numpy as np


def calibrate_absolute(y, point, level):
    y, point = np.asarray(y,float), np.asarray(point,float)
    if y.shape != point.shape or y.ndim != 1:
        raise ValueError("calibration shapes differ")
    if not 0 < level < 1 or not np.isfinite(y).all() or not np.isfinite(point).all():
        raise ValueError("invalid calibration values or level")
    errors = np.abs(y-point)
    rank = int((Decimal(len(errors)+1)*Decimal(str(level))).to_integral_value(rounding=ROUND_CEILING))
    if rank > len(errors):
        return dict(n_calibration=len(errors), rank=rank, q=float("inf"),
                    status="insufficient_calibration", nominal_level=level)
    q = float(np.partition(errors, rank-1)[rank-1])
    return dict(n_calibration=len(errors), rank=rank, q=q, status="ok", nominal_level=level)


def fixed_bounds(point, calibration):
    point = np.asarray(point,float)
    return point-calibration["q"], point+calibration["q"]
