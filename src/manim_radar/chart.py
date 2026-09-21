"""The core object: :class:`RadarChart`."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Optional, Sequence, Union

import numpy as np
from manim import (
    ORIGIN,
    RIGHT,
    WHITE,
    Circle,
    Dot,
    Line,
    ManimColor,
    Polygon,
    Text,
    VGroup,
    config as manim_config,
)

from .config import RadarConfig, get_style
from .data import RadarData
from .numbers import RollingNumber
from .theme import RadarTheme, get_theme
from .utils import lighten, mix, pick_font

__all__ = ["RadarChart"]

TAU = 2.0 * math.pi

_CJK_FONTS = (
    "PingFang SC", "Heiti SC", "Hiragino Sans GB", "Noto Sans CJK SC",
    "Source Han Sans SC", "Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei",
)
_MONO_FONTS = ("Menlo", "Consolas", "DejaVu Sans Mono", "Liberation Mono", "Courier New")


class RadarChart(VGroup):
    """An animated radar (spider) chart that morphs into other radar charts.

    The chart is a plain Manim mobject, so ``shift`` / ``move_to`` / ``scale`` /
    ``rotate`` behave as usual: every piece of geometry is recomputed in the
    chart's own coordinate frame on each frame.

    Examples
    --------
    Minimal chart::

        chart = RadarChart(
            axes=["Speed", "Power", "Range", "Comfort", "Price", "Safety"],
            values=[8, 6, 7, 9, 5, 8],
        )
        self.play(chart.reveal())

    One command to morph into another snapshot::

        self.play(chart.morph_to(RadarData(axes=..., values=[...])))

    """

    def __init__(
        self,
        data: Optional[RadarData] = None,
        *,
        axes: Optional[Sequence[str]] = None,
        values: Optional[Sequence[float]] = None,
        name: Optional[str] = None,
        color: Optional[str] = None,
        max_value: Optional[float] = None,
        style: Union[str, RadarConfig, None] = "neo",
        theme: Union[str, RadarTheme, None] = "midnight",
        config: Optional[RadarConfig] = None,
        radius: Optional[float] = None,
        position: Optional[Sequence[float]] = None,
        title: Optional[str] = None,
        levels: Optional[int] = None,
        numbers: Optional[str] = None,
        sweep: Optional[bool] = None,
        rim: Optional[bool] = None,
        opacity: Optional[float] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        # ---- config / theme -----------------------------------------------
        base = config if config is not None else get_style(style)
        self.config = base.evolved(
            radius=radius,
            position=tuple(position) if position is not None else None,
            title=title,
            levels=levels,
            numbers=numbers,
            sweep=sweep,
            rim=rim,
            opacity=opacity,
        ).validated()
        self.theme = get_theme(theme)
        cfg = self.config

        # ---- data ----------------------------------------------------------
        if data is None:
            if axes is None or values is None:
                raise ValueError(
                    "pass either a RadarData, or both ``axes`` and ``values``"
                )
            data = RadarData(
                axes=axes, values=values, name=name, color=color, max_value=max_value
            )
        elif axes is not None or values is not None:
            raise ValueError("pass either a RadarData or axes/values, not both")
        self._data = data
        self._values = [float(v) for v in data.values]
        self._scale = data.scale_for(cfg.levels)
        self._color = self._resolve_color(data.color, 0)
        self._opacity = float(cfg.opacity)
        self._rim = 1.0 if (data.rim or data.emphasis == "rim" or cfg.rim) else 0.0
        self._glitch = 0.0
        self._phase = 0.0
        self._time = 0.0

        # ---- fonts & axes --------------------------------------------------
        # Manim 0.21 cannot hash a Text object whose font is None.  Minimal
        # Linux CI images may not contain any of our preferred families, so
        # fall back to Pango's generic families instead of passing None.
        self._font_name = cfg.name_font or pick_font(_CJK_FONTS, default="sans")
        self._font_number = cfg.number_font or pick_font(_MONO_FONTS, default="monospace")
        self._font_title = cfg.title_font or self._font_name

        n = self._n = data.n_axes
        step = 360.0 / n
        sign = -1.0 if cfg.clockwise else 1.0
        self._angles = [cfg.start_angle + sign * step * i for i in range(n)]

        # ---- invisible transform anchors -----------------------------------
        home = np.array([cfg.position[0], cfg.position[1], 0.0])
        self._anchor = VGroup(
            Dot(radius=1e-4, fill_opacity=0, stroke_opacity=0).move_to(home),
            Dot(radius=1e-4, fill_opacity=0, stroke_opacity=0).move_to(home + RIGHT),
        )
        self.add(self._anchor)

        # ---- grid ----------------------------------------------------------
        self.web = VGroup()
        self.grid_glow = VGroup()
        for lvl in range(1, cfg.levels + 1):
            outer = lvl == cfg.levels
            ring = Polygon(
                ORIGIN, ORIGIN + RIGHT, ORIGIN + RIGHT,  # placeholder, set below
                stroke_color=self.theme.grid,
                stroke_width=cfg.ring_width_outer if outer else cfg.ring_width,
                stroke_opacity=cfg.ring_opacity_outer if outer else cfg.ring_opacity,
            )
            ring.base_so = cfg.ring_opacity_outer if outer else cfg.ring_opacity  # type: ignore[attr-defined]
            self.web.add(ring)
            if cfg.grid_glow:
                g = ring.copy().set_stroke(
                    color=self.theme.grid, width=cfg.grid_glow_width,
                    opacity=cfg.grid_glow_opacity,
                )
                g.base_so = cfg.grid_glow_opacity  # type: ignore[attr-defined]
                self.grid_glow.add(g)
        for i in range(n):
            spoke = Line(
                ORIGIN, ORIGIN + RIGHT,
                stroke_color=self.theme.axis_color(i),
                stroke_width=cfg.spoke_width,
                stroke_opacity=cfg.spoke_opacity,
            )
            spoke.base_so = cfg.spoke_opacity  # type: ignore[attr-defined]
            self.web.add(spoke)
            if cfg.grid_glow:
                g = spoke.copy().set_stroke(
                    color=self.theme.axis_color(i),
                    width=cfg.grid_glow_width,
                    opacity=cfg.grid_glow_opacity,
                )
                g.base_so = cfg.grid_glow_opacity  # type: ignore[attr-defined]
                self.grid_glow.add(g)
        self.add(self.grid_glow, self.web)

        # ---- level scale numbers -------------------------------------------
        self.level_labels = VGroup()
        if cfg.show_level_labels:
            self.add(self.level_labels)

        # ---- sweep ---------------------------------------------------------
        self.sweep = VGroup()
        if cfg.sweep:
            self.sweep.add(
                Polygon(ORIGIN, ORIGIN + RIGHT, fill_opacity=0, stroke_width=0),
                Line(ORIGIN, ORIGIN + RIGHT, stroke_width=cfg.sweep_edge_width),
            )
            self.add(self.sweep)

        # ---- data polygon layers -------------------------------------------
        ph = Polygon(ORIGIN, ORIGIN + RIGHT, ORIGIN + RIGHT)
        self.halo = ph.copy().set_stroke(width=cfg.halo_width, opacity=0).set_fill(opacity=0) \
            if cfg.glow_layers >= 2 else None
        self.glow = ph.copy().set_stroke(width=cfg.glow_width, opacity=0).set_fill(opacity=0) \
            if cfg.glow_layers >= 1 else None
        self.fill = ph.copy().set_stroke(width=0).set_fill(
            color=self._color, opacity=cfg.fill_opacity)
        self.inner = ph.copy().set_stroke(width=0) if cfg.inner_tint else None
        self.edges = VGroup()
        if cfg.rainbow_edges:
            for _ in range(n * max(1, cfg.edge_segments)):
                self.edges.add(Line(ORIGIN, ORIGIN + RIGHT, stroke_width=cfg.line_width))
        else:
            self.outline = ph.copy().set_fill(opacity=0).set_stroke(width=cfg.line_width)
        self.dots = VGroup()
        if cfg.vertex_dots:
            for i in range(n):
                col = self.theme.axis_color(i)
                for radius, opacity in (
                    (cfg.dot_radius * 3.2, 0.10),
                    (cfg.dot_radius, 0.90),
                    (cfg.dot_radius * 0.55, 0.95),
                ):
                    dot = Circle(radius=radius, stroke_width=0, fill_color=col)
                    dot.base_op = opacity  # type: ignore[attr-defined]
                    self.dots.add(dot)
        self.rim_outer = ph.copy().set_fill(opacity=0).set_stroke(
            width=cfg.rim_width_outer, color=self.theme.rim_outer, opacity=0)
        self.rim_inner = ph.copy().set_fill(opacity=0).set_stroke(
            width=cfg.rim_width_inner, color=self.theme.rim_inner, opacity=0)
        self.glitch_outer = ph.copy().set_fill(opacity=0).set_stroke(
            width=cfg.line_width, color=self.theme.glitch_split[0], opacity=0)
        self.glitch_inner = ph.copy().set_fill(opacity=0).set_stroke(
            width=cfg.line_width, color=self.theme.glitch_split[1], opacity=0)
        self.add(*[m for m in (self.halo, self.glow, self.fill, self.inner) if m is not None])
        self.add(self.edges if cfg.rainbow_edges else self.outline)
        self.add(self.dots, self.rim_outer, self.rim_inner, self.glitch_outer, self.glitch_inner)

        # ---- axis names & value numbers ------------------------------------
        self.axis_names = VGroup()
        self.value_numbers = VGroup()
        for i in range(n):
            label = Text(
                str(data.axes[i]),
                font=self._font_name,
                weight=cfg.name_weight,
                font_size=cfg.name_size,
                color=self.theme.axis_color(i) if cfg.colored_axis_names else self.theme.number,
            )
            self.axis_names.add(label)
            self.value_numbers.add(
                RollingNumber(
                    font=self._font_number,
                    size=cfg.number_size,
                    color=self.theme.number,
                    template=cfg.number_format,
                    max_value=self._scale,
                    suffix=cfg.overflow_suffix,
                    roll_height=cfg.roll_height,
                    mode=cfg.numbers,
                )
            )
        self.add(self.axis_names, self.value_numbers)

        # ---- nameplate & header --------------------------------------------
        self._name_holder = VGroup()
        self._name_text: Optional[Text] = None
        self._name_old: Optional[Text] = None
        self._name_alpha = 1.0
        self._name_old_alpha = 0.0
        self._name_dy = 0.0
        self._name_old_dy = 0.0
        if cfg.show_dataset_name and data.name:
            self._name_text = self._make_name_text(data.name)
            self._name_holder.add(self._name_text)
        self.add(self._name_holder)
        self.header: Optional[Text] = None
        self._title_visible = False
        if cfg.title:
            self.header = self._make_title(cfg.title)
            self.add(self.header)

        # ---- local geometry + first paint ----------------------------------
        self._rebuild_local_geometry()
        self.add_updater(self._refresh)
        self._refresh(self, 0.0)

    # ==================================================================
    # read-only properties
    # ==================================================================
    @property
    def data(self) -> RadarData:
        """Snapshot currently displayed."""
        return self._data

    @property
    def values(self) -> list[float]:
        """Current values (may be mid-tween while animating)."""
        return list(self._values)

    @property
    def full_scale(self) -> float:
        """Current full-scale value."""
        return self._scale

    @property
    def axis_count(self) -> int:
        """Number of axes."""
        return self._n

    @property
    def current_color(self) -> ManimColor:
        """Main colour right now."""
        return ManimColor(self._color)

    # ==================================================================
    # imperative setters (driven by the animations, usable directly too)
    # ==================================================================
    def set_values(self, values: Sequence[float], scale: Optional[float] = None) -> "RadarChart":
        """Snap to new values (no animation)."""
        if len(values) != self._n:
            raise ValueError(f"expected {self._n} values, got {len(values)}")
        self._values = [float(v) for v in values]
        if scale is not None:
            self._scale = float(scale)
            self._sync_number_scale()
        return self

    def _sync_number_scale(self) -> None:
        """Keep the odometer overflow rule in sync with the current full scale."""
        for num in self.value_numbers:
            num.set_max_value(self._scale)
        self._sync_level_labels()

    def _sync_level_labels(self) -> None:
        """Re-label the grid rings after the full scale changed."""
        if not len(self.level_labels):
            return
        cfg = self.config
        for lvl, txt in enumerate(list(self.level_labels), start=1):
            want = cfg.number_format.format(self._scale * lvl / cfg.levels)
            if getattr(txt, "text", None) != want:
                txt.become(
                    Text(
                        want,
                        font=self._font_number,
                        font_size=cfg.level_label_size,
                        color=self.theme.grid,
                    )
                )

    def set_main_color(self, color) -> "RadarChart":
        """Snap the polygon colour (no animation)."""
        self._color = ManimColor(color)
        return self

    def set_rim(self, amount: float) -> "RadarChart":
        """Set the orange/cyan emphasis outline, ``0..1``."""
        self._rim = float(np.clip(amount, 0.0, 1.0))
        return self

    def set_glitch(self, amount: float) -> "RadarChart":
        """Set the chromatic-split amount used by the glitch transition."""
        self._glitch = float(np.clip(amount, 0.0, 1.0))
        return self

    def set_opacity(self, value: float) -> "RadarChart":
        """Global opacity.

        Overridden so that ``FadeIn`` / ``FadeOut`` (which animate opacity of the
        whole family) work on a radar chart even though an updater paints every
        part each frame.
        """
        self._opacity = float(np.clip(value, 0.0, 1.0))
        return self

    def set_radius(self, radius: float) -> "RadarChart":
        """Resize the chart (rebuilds the cached local geometry)."""
        self.config = self.config.evolved(radius=float(radius)).validated()
        self._rebuild_local_geometry()
        self._sync_number_scale()
        return self

    # ==================================================================
    # animations
    # ==================================================================
    def morph_to(self, data, *, color: Optional[str] = None, name: Optional[str] = None,
                 max_value: Optional[float] = None, **kwargs):
        """One command: morph this chart into ``data``.

        ``data`` may be a :class:`RadarData`, a plain sequence of values, or a
        dict such as ``{"values": [...], "name": "...", "color": "#E868C8"}``.
        ``color`` / ``name`` / ``max_value`` override the target on the fly, so
        short inline morphs stay readable::

            self.play(chart.morph_to([5, 9, 4, 6, 9, 7], color="#E868C8"))

        Keyword arguments (all optional): ``transition``
        (``"dip"`` / ``"smooth"`` / ``"shockwave"`` / ``"zoom"`` / ``"glitch"`` /
        ``"stepped"``), ``run_time``, ``dip``, ``shockwave``, ``stepped``, ``rim``.
        """
        from .animations import RadarMorph

        target = self._coerce_data(data)
        if color is not None or name is not None or max_value is not None:
            target = replace(
                target,
                color=color if color is not None else target.color,
                name=name if name is not None else target.name,
                max_value=max_value if max_value is not None else target.max_value,
            )
        return RadarMorph(self, target, **kwargs)

    def reveal(self, run_time: float = 0.9, **kwargs):
        """Intro animation: grow out of the centre while fading in."""
        from .animations import RadarReveal

        return RadarReveal(self, run_time=run_time, **kwargs)

    def disappear(self, run_time: float = 0.8, **kwargs):
        """Outro animation: fade the whole chart out."""
        from .animations import RadarFade

        return RadarFade(self, 0.0, run_time=run_time, **kwargs)

    def glitch_in(self, run_time: float = 0.75, **kwargs):
        """Glitchy entrance — pair it with :meth:`disappear` for a gap."""
        from .animations import GlitchFlash

        return GlitchFlash(self, run_time=run_time, **kwargs)

    def shockwave(self, **kwargs):
        """A single expanding shockwave ring centred on the chart."""
        from .animations import Shockwave

        return Shockwave(center=self.get_center(), **kwargs)

    # ==================================================================
    # scene helpers
    # ==================================================================
    def attach_backdrop(self, scene, theme=None, **kwargs):
        """Add a :class:`~manim_radar.backdrop.DeepSpace` behind the chart."""
        from .backdrop import DeepSpace

        backdrop = DeepSpace(theme=theme or self.theme, **kwargs)
        backdrop.link(self)
        scene.add(backdrop)
        return backdrop

    # ==================================================================
    # internals
    # ==================================================================
    def _coerce_data(self, data) -> RadarData:
        if isinstance(data, RadarData):
            target = data
        elif isinstance(data, dict):
            payload = dict(data)
            axes = payload.pop("axes", self._data.axes)
            target = RadarData(axes=axes, **payload)
        else:
            target = self._data.with_values(data)
        if len(target.axes) != self._n:
            raise ValueError(f"morph target needs {self._n} axes, got {len(target.axes)}")
        if tuple(target.axes) != tuple(self._data.axes):
            raise ValueError("morphing between different axis layouts is not supported")
        return target

    def _resolve_color(self, color: Optional[str], index: int) -> ManimColor:
        base = ManimColor(color) if color else self.theme.dataset_color(index)
        return lighten(base, self.theme.brighten) if self.theme.brighten else base

    def _make_name_text(self, name: str) -> Text:
        cfg = self.config
        txt = Text(
            str(name),
            font=self._font_name,
            weight=cfg.name_weight,
            font_size=cfg.name_size,
            **cfg.text_kwargs,
        )
        grad = list(self.theme.name_gradient)
        if len(grad) >= 2:
            txt.set_color_by_gradient(*grad)
        return txt

    def _make_title(self, title: str) -> Text:
        cfg = self.config
        txt = Text(
            str(title),
            font=self._font_title,
            weight="BOLD",
            font_size=cfg.title_size,
            **cfg.text_kwargs,
        )
        grad = list(self.theme.title_gradient)
        if len(grad) >= 2:
            txt.set_color_by_gradient(*grad)
        return txt

    def _polar_local(self, angle: float, radius: float) -> np.ndarray:
        r = math.radians(angle)
        return np.array([radius * math.cos(r), radius * math.sin(r), 0.0])

    def _rebuild_local_geometry(self) -> None:
        """Refresh cached local shapes (rings, spokes, label anchors, sweep)."""
        cfg = self.config
        R = cfg.radius
        self._ring_local = []
        for lvl in range(1, cfg.levels + 1):
            r = R * lvl / cfg.levels
            pts = np.array([self._polar_local(a, r) for a in self._angles])
            self._ring_local.append(np.vstack([pts, pts[:1]]))
        self._spoke_local = np.array([np.zeros(3), np.zeros(3)])
        self._spoke_ends = np.array([self._polar_local(a, R) for a in self._angles])
        self._label_local = np.array(
            [self._polar_local(a, R * cfg.label_offset) for a in self._angles]
        )
        if cfg.numbers_next_to_name and len(self.axis_names):
            self._number_local = np.array(
                [
                    self._label_local[i]
                    + np.array([self.axis_names[i].width / 2.0 + cfg.number_gap, 0.0, 0.0])
                    for i in range(self._n)
                ]
            )
        else:
            self._number_local = np.array(
                [self._polar_local(a, R * cfg.number_offset) for a in self._angles]
            )
        if cfg.sweep:
            self._set_sweep_local(self._wedge_local(R * 1.04, cfg.sweep_angle, 18))
        if cfg.show_level_labels and not len(self.level_labels):
            ax = cfg.level_label_axis % self._n
            u = self._polar_local(self._angles[ax], 1.0)
            side = np.array([-u[1], u[0], 0.0])
            for lvl in range(1, cfg.levels):
                txt = Text(
                    cfg.number_format.format(self._scale * lvl / cfg.levels),
                    font=self._font_number,
                    font_size=cfg.level_label_size,
                    color=self.theme.grid,
                )
                txt.local_pos = u * (R * lvl / cfg.levels) + side * cfg.level_label_offset  # type: ignore[attr-defined]
                self.level_labels.add(txt)

    def _wedge_local(self, radius: float, angle_deg: float, segments: int) -> np.ndarray:
        """Closed polygon approximating a circular wedge (the sweep beam)."""
        half = math.radians(angle_deg) / 2.0
        base = math.radians(self.config.start_angle)
        pts = [np.zeros(3)]
        for k in range(segments + 1):
            a = base - half + 2 * half * k / segments
            pts.append(np.array([radius * math.cos(a), radius * math.sin(a), 0.0]))
        pts.append(np.zeros(3))
        return np.array(pts)

    def _set_sweep_local(self, points: np.ndarray) -> None:
        self._sweep_local = points

    def _polygon_local(self, scale: float = 1.0) -> np.ndarray:
        """Current data polygon in the local frame (closed path)."""
        R = self.config.radius * scale
        pts = np.array(
            [
                self._polar_local(a, R * self._values[i] / self._scale)
                for i, a in enumerate(self._angles)
            ]
        )
        return np.vstack([pts, pts[:1]])

    def _frame(self):
        """Current ``(origin, unit-x, unit-y)`` of the chart's local frame."""
        a = self._anchor[0].get_center()
        u = self._anchor[1].get_center() - a
        v = np.array([-u[1], u[0], 0.0])
        return a, u, v

    @staticmethod
    def _to_world(local: np.ndarray, a, u, v) -> np.ndarray:
        local = np.atleast_2d(local)
        return a + local[:, :1] * u + local[:, 1:2] * v

    # ------------------------------------------------------------------
    def _refresh(self, mob: VGroup, dt: float) -> None:
        """Master updater — recompute every piece of geometry for this frame."""
        cfg = self.config
        self._time += dt
        self._phase += dt / max(1e-6, cfg.sweep_period)
        a, u, v = self._frame()
        unit = float(np.linalg.norm(u)) or 1.0
        op = self._opacity
        col = ManimColor(self._color)
        grid_dim = max(0.06, 1.0 - 0.94 * self._rim)
        pulse = 0.75 + 0.25 * math.sin(self._time * cfg.rim_pulse)

        # grid -----------------------------------------------------------
        for lvl, ring in enumerate(self.web[: cfg.levels]):
            ring.set_points_as_corners(self._to_world(self._ring_local[lvl], a, u, v))
            ring.set_stroke(opacity=ring.base_so * op * grid_dim)
        for i, spoke in enumerate(self.web[cfg.levels:]):
            end = self._to_world(self._spoke_ends[i], a, u, v)[0]
            spoke.put_start_and_end_on(a, end)
            spoke.set_stroke(opacity=spoke.base_so * op * grid_dim)
        for g in self.grid_glow:
            g.set_stroke(opacity=g.base_so * op * grid_dim)

        for txt in self.level_labels:
            txt.move_to(self._to_world(txt.local_pos, a, u, v)[0])
            txt.set_opacity(0.80 * op * grid_dim)

        # sweep ----------------------------------------------------------
        if cfg.sweep:
            wedge, edge = self.sweep
            ang = TAU * self._phase
            c, s = math.cos(ang), math.sin(ang)
            rot = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
            local = self._sweep_local @ rot.T
            wedge.set_points_as_corners(self._to_world(local, a, u, v))
            wedge.set_fill(color=col, opacity=cfg.sweep_opacity * op)
            edge.put_start_and_end_on(a, self._to_world(local[1], a, u, v)[0])
            edge.set_stroke(color=mix(col, WHITE, 0.35), width=cfg.sweep_edge_width,
                            opacity=0.32 * op)

        # data polygon ---------------------------------------------------
        poly_local = self._polygon_local()
        poly = self._to_world(poly_local, a, u, v)
        if self.halo is not None:
            self.halo.set_points_as_corners(poly)
            self.halo.set_stroke(color=mix(col, WHITE, 0.22), width=cfg.halo_width,
                                 opacity=cfg.halo_opacity * op)
        if self.glow is not None:
            self.glow.set_points_as_corners(poly)
            self.glow.set_stroke(color=mix(col, WHITE, 0.45), width=cfg.glow_width,
                                 opacity=cfg.glow_opacity * op)
        self.fill.set_points_as_corners(poly)
        self.fill.set_fill(color=col, opacity=cfg.fill_opacity * op)
        if self.inner is not None:
            inner_local = poly_local * cfg.inner_tint_scale
            self.inner.set_points_as_corners(self._to_world(inner_local, a, u, v))
            self.inner.set_fill(color=mix(col, WHITE, cfg.inner_tint_mix),
                                opacity=cfg.inner_tint_opacity * op)

        # outline --------------------------------------------------------
        if cfg.rainbow_edges:
            seg = max(1, cfg.edge_segments)
            idx = 0
            for i in range(self._n):
                j = (i + 1) % self._n
                c0, c1 = self.theme.axis_color(i), self.theme.axis_color(j)
                p0, d = poly[i], poly[j] - poly[i]
                for k in range(seg):
                    line = self.edges[idx]
                    line.put_start_and_end_on(p0 + d * (k / seg), p0 + d * ((k + 1) / seg))
                    line.set_stroke(color=mix(c0, c1, (k + 0.5) / seg),
                                    width=cfg.line_width, opacity=op)
                    idx += 1
        else:
            self.outline.set_points_as_corners(poly)
            self.outline.set_stroke(color=mix(col, WHITE, 0.55), width=cfg.line_width,
                                    opacity=op)

        # vertex dots ----------------------------------------------------
        if len(self.dots):
            for i in range(self._n):
                for k in range(3):
                    dot = self.dots[i * 3 + k]
                    dot.move_to(poly[i])
                    dot.set_fill(color=self.theme.axis_color(i) if k < 2 else WHITE,
                                 opacity=dot.base_op * op)

        # emphasis rim + chromatic split ---------------------------------
        outer = self._to_world(poly_local * (1.0 + cfg.rim_offset_outer), a, u, v)
        inner = self._to_world(poly_local * (1.0 - cfg.rim_offset_inner), a, u, v)
        self.rim_outer.set_points_as_corners(outer)
        self.rim_outer.set_stroke(color=self.theme.rim_outer, width=cfg.rim_width_outer,
                                  opacity=0.90 * self._rim * pulse * op)
        self.rim_inner.set_points_as_corners(inner)
        self.rim_inner.set_stroke(color=self.theme.rim_inner, width=cfg.rim_width_inner,
                                  opacity=0.80 * self._rim * pulse * op)
        if self._glitch > 1e-3:
            shift = RIGHT * (cfg.glitch_offset * self._glitch)
            for mob, colour in ((self.glitch_outer, self.theme.glitch_split[0]),
                                (self.glitch_inner, self.theme.glitch_split[1])):
                mob.set_points_as_corners(poly + shift)
                mob.set_stroke(color=colour, width=cfg.line_width,
                               opacity=0.85 * self._glitch * op)
        else:
            self.glitch_outer.set_stroke(opacity=0)
            self.glitch_inner.set_stroke(opacity=0)

        # labels, numbers, nameplate, header ------------------------------
        for i, label in enumerate(self.axis_names):
            label.move_to(self._to_world(self._label_local[i], a, u, v)[0])
            label.set_opacity(op)
        for i, num in enumerate(self.value_numbers):
            anchor = self._to_world(self._number_local[i], a, u, v)[0]
            num.render(self._values[i], anchor, opacity=op, scale=unit)

        # top slot: nameplate first, header above it when there is room
        label_top = max((txt.get_top()[1] for txt in self.axis_names), default=a[1])
        frame_limit = manim_config.frame_height / 2.0 - 0.12

        def slot_y(mob, offset: float):
            """``(y, fits)`` for a text at ``offset * radius`` above the chart."""
            half = mob.height / 2.0
            top_limit = frame_limit - half
            floor = label_top + 0.20 + half
            y = min(offset * cfg.radius, top_limit)
            if y < floor:
                y = floor
            return y, y <= top_limit + 1e-6

        title_y = None
        name_y = None
        if self._name_text is not None:
            name_y, _ = slot_y(self._name_text, cfg.name_offset)
        if self.header is not None:
            if self._name_text is not None and name_y is not None:
                stacked = (
                    name_y + self._name_text.height / 2.0 + 0.10
                    + self.header.height / 2.0
                )
                title_y = stacked if stacked + self.header.height / 2.0 <= frame_limit else None
            else:
                title_y, fits = slot_y(self.header, cfg.title_offset)
                if not fits:
                    title_y = None

        if self._name_text is not None and name_y is not None:
            self._name_text.move_to(a + v * (name_y + self._name_dy))
            self._name_text.set_opacity(op * self._name_alpha)
        if self._name_old is not None and name_y is not None:
            self._name_old.move_to(a + v * (name_y + self._name_old_dy))
            self._name_old.set_opacity(op * self._name_old_alpha)
        if self.header is not None:
            if title_y is None:
                self._title_visible = False
                self.header.set_opacity(0)
            else:
                self._title_visible = True
                self.header.move_to(a + v * title_y)
                self.header.set_opacity(op)

    # ==================================================================
    # nameplate plumbing used by RadarMorph
    # ==================================================================
    def _begin_name_swap(self, new_name: str, shift: float = 0.30) -> None:
        """Start a crossfade from the current nameplate to ``new_name``."""
        if not new_name or not self.config.show_dataset_name:
            return
        current = getattr(self._name_text, "text", None)
        if current == new_name:
            return
        new_text = self._make_name_text(new_name)
        new_text.set_opacity(0)
        self._name_old = self._name_text
        self._name_holder.add(new_text)
        self._name_text = new_text
        self._name_alpha = 0.0
        self._name_old_alpha = 1.0 if self._name_old is not None else 0.0
        self._name_dy = -shift
        self._name_old_dy = 0.0

    def _swap_name_progress(self, t: float, shift: float = 0.30) -> None:
        """Advance a nameplate crossfade to progress ``t`` (``0..1``)."""
        if self._name_old is None:
            return
        self._name_alpha = t
        self._name_old_alpha = max(0.0, 1.0 - 1.6 * t)
        self._name_dy = -shift * (1.0 - t)
        self._name_old_dy = shift * 0.5 * t

    def _end_name_swap(self) -> None:
        """Finish a nameplate crossfade, dropping the outgoing text."""
        if self._name_old is not None:
            self._name_holder.remove(self._name_old)
            self._name_old = None
        self._name_alpha = 1.0
        self._name_old_alpha = 0.0
        self._name_dy = 0.0
        self._name_old_dy = 0.0
