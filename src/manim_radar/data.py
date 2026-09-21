"""The data model: one radar snapshot."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Optional, Sequence, Union

from manim import ManimColor

__all__ = ["RadarData"]

_EMPHASIS = ("zoom", "gap", "rim")


@dataclass(frozen=True)
class RadarData:
    """One radar snapshot: the axis names plus the value on each axis.

    Parameters
    ----------
    axes:
        Axis labels, e.g. ``("Speed", "Power", "Range")``. Length must match
        ``values`` and be at least 3.
    values:
        Value per axis, all ``>= 0``.
    name:
        Optional dataset name, drawn as a nameplate above the chart and morphed
        on every transition.
    color:
        Main colour of the polygon. ``None`` -> cycle through the theme palette.
    max_value:
        Full-scale value of this snapshot. Defaults to ``max(values)`` rounded
        up; values above it are shown with ``config.overflow_suffix`` (``"10+"``).
    rim:
        Draw the orange/cyan double outline (emphasis).
    emphasis:
        ``None`` | ``"zoom"`` (heavy zoom transition into this snapshot) |
        ``"gap"`` (fade to black, then glitch back in) | ``"rim"`` (same as
        ``rim=True``, handy in inline lists).
    hold:
        Seconds to hold after morphing to this snapshot (``RadarReel`` only).
    transition:
        Per-snapshot transition override, see :meth:`RadarChart.morph_to`.
    note:
        Free-form text (ignored by the chart itself, useful for the reel).
    """

    axes: Sequence[str]
    values: Sequence[float]
    name: Optional[str] = None
    color: Optional[str] = None
    max_value: Optional[float] = None
    rim: bool = False
    emphasis: Optional[str] = None
    hold: Optional[float] = None
    transition: Optional[str] = None
    note: Optional[str] = None
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        axes = tuple(self.axes)
        values = tuple(float(v) for v in self.values)
        object.__setattr__(self, "axes", axes)
        object.__setattr__(self, "values", values)

        if len(axes) != len(values):
            raise ValueError(
                f"axes and values must have the same length "
                f"({len(axes)} axes vs {len(values)} values)"
            )
        if len(axes) < 3:
            raise ValueError("a radar chart needs at least 3 axes")
        if any(v < 0 for v in values):
            raise ValueError(f"values must be >= 0, got {values}")
        if self.emphasis is not None and self.emphasis not in _EMPHASIS:
            raise ValueError(
                f"emphasis must be one of {_EMPHASIS} or None, got {self.emphasis!r}"
            )
        if self.max_value is not None and self.max_value <= 0:
            raise ValueError("max_value must be > 0")

    # ------------------------------------------------------------------
    @property
    def n_axes(self) -> int:
        """Number of axes of this snapshot."""
        return len(self.axes)

    @property
    def overflow_suffix(self) -> str:
        """``"+"`` when any value exceeds the full scale, else an empty string."""
        return "+" if max(self.values) > self.full_scale else ""

    @property
    def full_scale(self) -> float:
        """Full-scale value (``max_value`` if given, else ``ceil(max(values))``)."""
        if self.max_value is not None:
            return float(self.max_value)
        return float(max(1.0, math.ceil(max(self.values))))

    def scale_for(self, levels: int = 5) -> float:
        """Full scale snapped so the grid labels come out as round numbers.

        ``levels`` grid rings divide the scale, so a scale of ``levels * k``
        labels every ring with an integer. Values above it render with the
        overflow suffix (``10+``).
        """
        if self.max_value is not None:
            return float(self.max_value)
        levels = max(1, int(levels))
        top = max(self.values)
        if top <= 0:
            return 1.0
        if top >= levels:
            return float(levels * math.ceil(top / levels))
        return float(levels)

    def ratios(self, scale: Optional[float] = None) -> list[float]:
        """Values as fractions of the full scale (``1.0`` = outer ring)."""
        sc = float(scale if scale is not None else self.full_scale) or 1.0
        return [v / sc for v in self.values]

    def radius_values(self, radius: float, scale: Optional[float] = None) -> list[float]:
        """Values converted to scene-unit radii for a chart of ``radius``."""
        return [r * radius for r in self.ratios(scale)]

    def color_or(self, fallback: Union[str, ManimColor]) -> ManimColor:
        """``color`` if set, else ``fallback``."""
        return ManimColor(self.color) if self.color else ManimColor(fallback)

    def with_values(self, values: Sequence[float], **changes) -> "RadarData":
        """Copy of this snapshot with new ``values`` (and optional other tweaks)."""
        return replace(self, values=tuple(float(v) for v in values), **changes)

    def renamed(self, name: Optional[str]) -> "RadarData":
        """Copy of this snapshot with another ``name``."""
        return replace(self, name=name)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        label = f" name={self.name!r}" if self.name else ""
        return f"RadarData(axes={len(self.axes)}d{label}, values={tuple(self.values)})"
