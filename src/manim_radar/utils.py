"""Small helpers shared across :mod:`manim_radar`."""

from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence

import numpy as np
from manim import ManimColor, ParsableManimColor, WHITE, interpolate_color

__all__ = [
    "unit_vector",
    "axis_angles",
    "mix",
    "lighten",
    "ease_in_out_cubic",
    "ease_out_back",
    "pick_font",
    "closed",
]


def unit_vector(degrees: float) -> np.ndarray:
    """``(cos, sin, 0)`` for an angle given in degrees."""
    r = math.radians(degrees)
    return np.array([math.cos(r), math.sin(r), 0.0])


def axis_angles(count: int, start: float = 90.0, clockwise: bool = False) -> list[float]:
    """Evenly spaced axis angles (degrees).

    ``start`` is the angle of the first axis, ``clockwise`` flips the direction
    so that datasets read the other way round.
    """
    step = 360.0 / count
    sign = -1.0 if clockwise else 1.0
    return [start + sign * step * i for i in range(count)]


def mix(a: ParsableManimColor, b: ParsableManimColor, t: float) -> ManimColor:
    """Linear colour mix, ``t=0`` -> ``a``, ``t=1`` -> ``b``."""
    return interpolate_color(ManimColor(a), ManimColor(b), float(np.clip(t, 0.0, 1.0)))


def lighten(color: ParsableManimColor, amount: float = 0.08) -> ManimColor:
    """Push a colour towards white by ``amount``."""
    return mix(color, WHITE, amount)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out (Manim only ships smooth/linear/rush_* out of the box)."""
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def ease_out_back(t: float, overshoot: float = 1.2) -> float:
    """Ease-out with a small overshoot — nice for value tweens."""
    t = float(np.clip(t, 0.0, 1.0))
    c1 = overshoot
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


_FONT_CACHE: dict[tuple, Optional[str]] = {}


def pick_font(candidates: Sequence[str], default: Optional[str] = None) -> Optional[str]:
    """Return the first font of ``candidates`` installed on this machine.

    Lets the library look right on macOS / Windows / Linux without hard-coding a
    platform specific family. Falls back to ``default`` when nothing matches.
    """
    key = tuple(candidates) + (default,)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    available: set[str] = set()
    try:  # pragma: no cover - depends on the host system
        import manimpango

        available = set(manimpango.list_fonts())
    except Exception:
        available = set()

    found = next((name for name in candidates if name in available), None)
    if found is None and default is not None and default not in candidates:
        found = default
    _FONT_CACHE[key] = found
    return found


def closed(points: np.ndarray) -> np.ndarray:
    """Append the first point again so a polygon path is closed."""
    return np.vstack([points, points[:1]])


def as_points(values: Iterable) -> np.ndarray:
    """Coerce a sequence of 2D/3D points into an ``(n, 3)`` float array."""
    return np.array([np.pad(np.asarray(v, dtype=float), (0, 3 - np.asarray(v).size))
                     for v in values], dtype=float)
