"""All animations: the morph, the intro/outro and the transition effects."""

from __future__ import annotations

import math
from typing import Optional, Sequence

import numpy as np
from manim import (
    DOWN,
    RIGHT,
    UP,
    Animation,
    ManimColor,
    Polygon,
    Rectangle,
    VGroup,
    smooth,
)

from .data import RadarData
from .utils import ease_in_out_cubic, mix

__all__ = [
    "RadarMorph",
    "RadarReveal",
    "RadarFade",
    "Shockwave",
    "GlitchFlash",
    "TRANSITIONS",
]

#: Named transition presets understood by :meth:`RadarChart.morph_to`.
TRANSITIONS = {
    "smooth": dict(dip=False, shockwave=False),
    "dip": dict(dip=True, shockwave=False),
    "shockwave": dict(dip=True, shockwave=True),
    "zoom": dict(dip=True, shockwave=True, dim=True),
    "glitch": dict(dip=True, shockwave=False, glitch=True),
    "stepped": dict(dip=True, shockwave=False, stepped=True),
}


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _ring_points(center: np.ndarray, radius: float, segments: int = 64) -> np.ndarray:
    """A circle as a closed polygon, so its stroke can be restyled freely."""
    angles = np.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
    pts = np.array(
        [
            center + np.array([radius * math.cos(a), radius * math.sin(a), 0.0])
            for a in angles
        ]
    )
    return np.vstack([pts, pts[:1]])


class _Ring(Polygon):
    """A ring whose radius / stroke width / opacity change per frame."""

    def __init__(self, center, color, **kwargs) -> None:
        center = np.asarray(center, dtype=float)
        super().__init__(*(np.tile(center, (3, 1))), stroke_color=color, **kwargs)
        self.ring_center = center
        self.ring_color = ManimColor(color)

    def restyle(self, radius: float, width: float, opacity: float) -> None:
        self.set_points_as_corners(_ring_points(self.ring_center, radius))
        self.set_stroke(
            color=self.ring_color,
            width=max(0.05, width),
            opacity=float(np.clip(opacity, 0.0, 1.0)),
        )


def _flicker(alpha: float, steps: int = 6) -> float:
    """1 / 0.25 alternating opacity used by the glitch entrance."""
    return 0.25 if int(alpha * steps) % 2 == 0 else 1.0


# ---------------------------------------------------------------------------
# shockwave
# ---------------------------------------------------------------------------
class Shockwave(Animation):
    """An expanding (or imploding) ring.

    Cheap on its own, and a great way to cover a shape change.

    Examples
    --------
    ``self.play(chart.shockwave(color="#E868C8"))``
    """

    def __init__(
        self,
        center=None,
        *,
        color="#FFFFFF",
        radius_start: float = 0.18,
        radius_end: float = 5.0,
        width_start: float = 4.5,
        width_end: float = 0.7,
        expand: bool = True,
        run_time: float = 0.42,
        rate_func=smooth,
        **kwargs,
    ) -> None:
        if center is None:
            center = np.zeros(3)
        self._expand = expand
        self._r0, self._r1 = (radius_start, radius_end) if expand else (radius_end, radius_start)
        self._w0, self._w1 = (width_start, width_end) if expand else (width_end, width_start)
        super().__init__(
            _Ring(np.asarray(center, dtype=float), color, stroke_width=width_start),
            run_time=run_time,
            rate_func=rate_func,
            **kwargs,
        )

    def interpolate_mobject(self, alpha: float) -> None:
        k = self.rate_func(alpha)
        self.mobject.restyle(
            self._r0 + (self._r1 - self._r0) * k,
            self._w0 + (self._w1 - self._w0) * k,
            0.9 * (1.0 - k),
        )


# ---------------------------------------------------------------------------
# the morph
# ---------------------------------------------------------------------------
class RadarMorph(Animation):
    """Morph a :class:`~manim_radar.chart.RadarChart` into another snapshot.

    Values, full scale, colour, emphasis outline and opacity are interpolated in
    a single pass. The shape can first "dip" and then roll up to the target (the
    signature move of style ``neo``), or snap in integer steps (``classic``).

    Usually you do not instantiate this directly — call
    :meth:`RadarChart.morph_to`.
    """

    def __init__(
        self,
        chart,
        target: RadarData,
        *,
        transition: Optional[str] = None,
        run_time: Optional[float] = None,
        rate_func=smooth,
        dip: Optional[bool] = None,
        dip_ratio: Optional[float] = None,
        shockwave: Optional[bool] = None,
        shock_color=None,
        stepped: Optional[bool] = None,
        dim: Optional[bool] = None,
        glitch: Optional[bool] = None,
        colors: bool = True,
        rim: Optional[bool] = None,
        opacity: Optional[float] = None,
        fade_name: bool = True,
        name_shift: float = 0.30,
        **kwargs,
    ) -> None:
        if transition is not None and transition not in TRANSITIONS:
            raise ValueError(
                f"unknown transition {transition!r}; available: "
                f"{', '.join(TRANSITIONS)}, or None"
            )
        preset = dict(TRANSITIONS.get(transition, {})) if transition else {}
        cfg = chart.config

        self.chart = chart
        self.target = target
        self.dip = preset.get("dip", True) if dip is None else dip
        self.dip_ratio = (
            (cfg.dip_ratio if dip_ratio is None else dip_ratio) if self.dip else 0.0
        )
        self.shockwave = (
            preset.get("shockwave", cfg.shockwave) if shockwave is None else shockwave
        )
        self.shock_color = shock_color
        self.stepped = preset.get("stepped", cfg.stepped) if stepped is None else stepped
        self.dim = preset.get("dim", False) if dim is None else dim
        self.glitch = preset.get("glitch", False) if glitch is None else glitch
        self.colors = colors
        self.rim_override = rim
        self.opacity_target = opacity
        self.fade_name = fade_name
        self.name_shift = name_shift
        self._ring: Optional[_Ring] = None
        super().__init__(
            chart,
            run_time=run_time if run_time is not None else cfg.morph_run_time,
            rate_func=rate_func,
            **kwargs,
        )

    # ------------------------------------------------------------------
    def begin(self) -> None:
        chart = self.chart
        cfg = chart.config
        self.start_values = list(chart._values)
        self.start_scale = float(chart._scale)
        self.start_color = ManimColor(chart._color)
        self.start_rim = float(chart._rim)
        self.start_opacity = float(chart._opacity)

        self.end_values = [float(v) for v in self.target.values]
        self.end_scale = float(self.target.scale_for(cfg.levels))
        self.end_color = (
            chart._resolve_color(self.target.color, 0) if self.colors else self.start_color
        )
        if self.rim_override is not None:
            self.end_rim = float(self.rim_override)
        elif self.target.rim or self.target.emphasis == "rim":
            self.end_rim = 1.0
        else:
            self.end_rim = 1.0 if cfg.rim else 0.0
        self.end_opacity = (
            self.start_opacity if self.opacity_target is None else float(self.opacity_target)
        )

        self.dip_values = (
            [max(cfg.dip_floor, v - cfg.dip_drop) for v in self.end_values]
            if self.dip
            else list(self.start_values)
        )

        if self.shockwave:
            self._ring = _Ring(chart.get_center(), self.shock_color or self.end_color,
                               stroke_width=4.5)
            chart.add(self._ring)

        if self.fade_name:
            chart._begin_name_swap(self.target.name or "", shift=self.name_shift)

    # ------------------------------------------------------------------
    def interpolate_mobject(self, alpha: float) -> None:
        a = self.rate_func(alpha)
        chart = self.chart
        r = self.dip_ratio

        # -- values: dip, then roll up to the target --------------------
        if r > 1e-6 and a < r:
            t = ease_in_out_cubic(a / r)
            values = [s + (d - s) * t for s, d in zip(self.start_values, self.dip_values)]
            scale = self.start_scale
        else:
            t = (a - r) / (1.0 - r) if r < 1.0 - 1e-6 else 1.0
            t = ease_in_out_cubic(max(0.0, min(1.0, t)))
            base = self.dip_values
            values = [b + (e - b) * t for b, e in zip(base, self.end_values)]
            scale = self.start_scale + (self.end_scale - self.start_scale) * t
        if self.stepped:
            values = [float(round(v)) for v in values]
        chart._values = values
        chart._scale = max(1e-6, scale)

        # -- colour / emphasis / opacity --------------------------------
        chart._color = mix(self.start_color, self.end_color, min(1.0, a * 1.15))
        chart._rim = self.start_rim + (self.end_rim - self.start_rim) * a

        dim_factor = 1.0
        if self.dim:
            dim_factor = 0.15 + 0.85 * abs(2.0 * a - 1.0)
        if self.glitch:
            chart._glitch = max(0.0, 1.0 - a / 0.45)
            dim_factor *= _flicker(a)
        else:
            chart._glitch = 0.0
        chart._opacity = (
            self.start_opacity + (self.end_opacity - self.start_opacity) * a
        ) * dim_factor

        # -- shockwave ring ---------------------------------------------
        if self._ring is not None:
            k = min(1.0, a / 0.55)
            radius = 0.18 + (chart.config.shock_radius - 0.18) * k
            self._ring.restyle(radius, 4.5 * (1.0 - k) + 0.7, 0.9 * (1.0 - k))

        # -- nameplate crossfade ----------------------------------------
        if self.fade_name:
            t = min(1.0, max(0.0, (a - 0.25) / 0.75))
            self.chart._swap_name_progress(t, shift=self.name_shift)

    # ------------------------------------------------------------------
    def finish(self) -> None:
        chart = self.chart
        chart._values = list(self.end_values)
        chart._scale = self.end_scale
        chart._color = self.end_color
        chart._rim = self.end_rim
        chart._opacity = self.end_opacity
        chart._glitch = 0.0
        chart._data = self.target
        chart._sync_number_scale()

        if self._ring is not None:
            chart.remove(self._ring)
            self._ring = None
        if self.fade_name:
            chart._end_name_swap()

    def clean_up_from_scene(self, scene) -> None:
        self._drop_ring()
        super().clean_up_from_scene(scene)

    def _drop_ring(self) -> None:
        if self._ring is not None:
            try:
                self.chart.remove(self._ring)
            except ValueError:  # pragma: no cover - already removed
                pass
            self._ring = None


# ---------------------------------------------------------------------------
# intro / outro
# ---------------------------------------------------------------------------
class RadarReveal(Animation):
    """Grow the chart out of its centre while fading in."""

    def __init__(
        self,
        chart,
        *,
        run_time: float = 0.9,
        rate_func=smooth,
        from_values: Optional[Sequence[float]] = None,
        with_shockwave: Optional[bool] = None,
        **kwargs,
    ) -> None:
        self.chart = chart
        self.from_values = (
            list(from_values) if from_values is not None else [0.0] * chart.axis_count
        )
        self.with_shockwave = (
            chart.config.shockwave if with_shockwave is None else with_shockwave
        )
        self._ring: Optional[_Ring] = None
        super().__init__(chart, run_time=run_time, rate_func=rate_func, **kwargs)

    def begin(self) -> None:
        chart = self.chart
        self.to_values = list(chart._values)
        self.to_opacity = float(chart._opacity) or 1.0
        chart._values = list(self.from_values)
        chart._opacity = 0.0
        if self.with_shockwave:
            self._ring = _Ring(chart.get_center(), chart._color, stroke_width=4.5)
            chart.add(self._ring)

    def interpolate_mobject(self, alpha: float) -> None:
        a = self.rate_func(alpha)
        chart = self.chart
        chart._values = [f + (t - f) * a for f, t in zip(self.from_values, self.to_values)]
        chart._opacity = self.to_opacity * a
        if self._ring is not None:
            k = min(1.0, a / 0.6)
            radius = 0.18 + (chart.config.shock_radius - 0.18) * k
            self._ring.restyle(radius, 4.5 * (1.0 - k) + 0.7, 0.9 * (1.0 - k))

    def finish(self) -> None:
        chart = self.chart
        chart._values = list(self.to_values)
        chart._opacity = self.to_opacity
        if self._ring is not None:
            chart.remove(self._ring)
            self._ring = None

    def clean_up_from_scene(self, scene) -> None:
        if self._ring is not None:
            try:
                self.chart.remove(self._ring)
            except ValueError:  # pragma: no cover
                pass
            self._ring = None
        super().clean_up_from_scene(scene)


class RadarFade(Animation):
    """Fade the whole chart (dims every layer, not only the group opacity)."""

    def __init__(self, chart, to: float = 0.0, *, run_time: float = 0.8,
                 rate_func=smooth, **kwargs) -> None:
        self.chart = chart
        self.to = float(np.clip(to, 0.0, 1.0))
        super().__init__(chart, run_time=run_time, rate_func=rate_func, **kwargs)

    def begin(self) -> None:
        self.start = float(self.chart._opacity)

    def interpolate_mobject(self, alpha: float) -> None:
        a = self.rate_func(alpha)
        self.chart._opacity = self.start + (self.to - self.start) * a

    def finish(self) -> None:
        self.chart._opacity = self.to


class GlitchFlash(Animation):
    """Chromatic split + scan bars — the "glitch back in" entrance.

    Typical use::

        self.play(chart.disappear())   # fade to black
        self.wait(1.5)
        self.play(chart.glitch_in())   # snap back on
    """

    def __init__(
        self,
        chart,
        *,
        run_time: float = 0.75,
        rate_func=smooth,
        bars: bool = True,
        flickers: int = 3,
        **kwargs,
    ) -> None:
        self.chart = chart
        self.bars = bars
        self.flickers = max(1, int(flickers))
        self._bars: Optional[VGroup] = None
        super().__init__(chart, run_time=run_time, rate_func=rate_func, **kwargs)

    def begin(self) -> None:
        chart = self.chart
        self._to_opacity = max(0.6, float(chart._opacity) or 1.0)
        chart._opacity = 0.0
        chart.set_glitch(1.0)
        if self.bars:
            width = chart.config.glitch_bar_width
            self._bars = VGroup(
                Rectangle(width=width, height=0.16, fill_color="#FFFFFF",
                          fill_opacity=0.40, stroke_width=0),
                Rectangle(width=width, height=0.07, fill_color="#FFFFFF",
                          fill_opacity=0.30, stroke_width=0),
            )
            center = chart.get_center()
            self._bars[0].move_to(center + DOWN * 3.4)
            self._bars[1].move_to(center + UP * 3.2)
            chart.add(self._bars)

    def interpolate_mobject(self, alpha: float) -> None:
        a = self.rate_func(alpha)
        chart = self.chart
        chart.set_glitch(max(0.0, 1.0 - a / 0.6))
        chart._opacity = self._to_opacity if a > 0.6 else self._to_opacity * _flicker(a, self.flickers + 1)
        if self._bars is not None:
            center = chart.get_center()
            self._bars[0].set_y(center[1] - 3.4 + 8.0 * a)
            self._bars[1].set_y(center[1] + 3.2 - 8.0 * a)
            self._bars.set_opacity(max(0.0, 1.0 - a * 1.5))

    def finish(self) -> None:
        chart = self.chart
        chart.set_glitch(0.0)
        chart._opacity = self._to_opacity
        if self._bars is not None:
            chart.remove(self._bars)
            self._bars = None

    def clean_up_from_scene(self, scene) -> None:
        if self._bars is not None:
            try:
                self.chart.remove(self._bars)
            except ValueError:  # pragma: no cover
                pass
            self._bars = None
        super().clean_up_from_scene(scene)
