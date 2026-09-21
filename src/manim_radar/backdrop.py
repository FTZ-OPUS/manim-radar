"""The deep-space backdrop: radial glow, vignette, nebula blobs and stars."""

from __future__ import annotations

import math
import random
from typing import Optional, Sequence, Union

import numpy as np
from manim import Circle, ManimColor, VGroup, WHITE, config, interpolate_color

from .theme import RadarTheme, get_theme
from .utils import mix

__all__ = ["DeepSpace", "set_scene_background"]


def set_scene_background(theme: Union[str, RadarTheme, None] = "midnight") -> str:
    """Set Manim's global background colour to the theme background.

    Returns the colour that was applied. Handy at the top of a scene file::

        from manim_radar import set_scene_background
        set_scene_background("midnight")

    """
    th = get_theme(theme)
    config.background_color = th.background
    return th.background


class DeepSpace(VGroup):
    """Animated starfield + glow used behind a radar chart.

    Four stacked layers:

    * **glow** – a smooth radial glow built from many concentric circles
      (Manim has no real gradients, stacking low-opacity circles is the trick)
    * **vignette** – darker corners so the chart pops out of the frame
    * **nebula** – big soft blobs that breathe in the chart's current colour
    * **stars** – three-layer glowing dots that drift and twinkle

    Use :meth:`link` to make the nebula / stars follow a chart's colour, and
    :meth:`set_fade` to dim everything (used for the black "gap" moment).
    """

    def __init__(
        self,
        theme: Union[str, RadarTheme, None] = "midnight",
        *,
        center: Sequence[float] = (0.0, 0.0),
        glow: bool = True,
        glow_layers: int = 72,
        vignette: bool = True,
        vignette_layers: int = 14,
        nebula: bool = True,
        nebula_count: int = 8,
        stars: bool = True,
        star_count: int = 64,
        star_region: tuple = (-7.6, 7.6, -4.3, 4.3),
        seed: int = 7,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.theme = get_theme(theme)
        self._center = np.array([center[0], center[1], 0.0], dtype=float)
        self._fade = 1.0
        self._tint = ManimColor(self.theme.palette[0])
        self._time = 0.0
        rnd = random.Random(seed)

        # ---- radial glow --------------------------------------------------
        self._glow = VGroup()
        if glow:
            for k in range(glow_layers):
                r = 0.20 * (12.5 / 0.20) ** (k / max(1, glow_layers - 1))
                self._glow.add(
                    Circle(
                        radius=r,
                        fill_color=self.theme.glow,
                        fill_opacity=0.020,
                        stroke_width=0,
                    ).move_to(self._center)
                )
        self.add(self._glow)

        # ---- corner vignette ----------------------------------------------
        if vignette:
            vig = VGroup()
            for cx, cy in ((8.6, 4.9), (-8.6, 4.9), (8.6, -4.9), (-8.6, -4.9)):
                for k in range(vignette_layers):
                    r = (8.0) ** (k / max(1, vignette_layers - 1))
                    vig.add(
                        Circle(
                            radius=r,
                            fill_color=self.theme.vignette,
                            fill_opacity=0.055,
                            stroke_width=0,
                        ).move_to([cx, cy, 0])
                    )
            self._vignette = vig
            self.add(vig)

        # ---- nebula --------------------------------------------------------
        self._nebula = VGroup()
        if nebula:
            spots = [
                (-6.2, 3.4, 2.2), (6.4, 3.0, 1.9), (-6.8, -3.2, 2.1),
                (6.6, -3.4, 2.0), (0.5, 4.3, 2.4), (0.0, -4.4, 2.2),
                (-3.2, 0.4, 1.6), (3.4, -0.6, 1.7),
            ]
            for cx, cy, rr in spots[:nebula_count]:
                blob = VGroup()
                for k in range(10):
                    c = Circle(
                        radius=rr * (0.26 + 0.098 * k),
                        stroke_width=0,
                        fill_color=WHITE,
                        fill_opacity=0.017,
                    )
                    c.base_op = 0.017  # type: ignore[attr-defined]
                    blob.add(c)
                blob.move_to([cx, cy, 0])
                self._nebula.add(blob)
        self.add(self._nebula)

        # ---- stars ---------------------------------------------------------
        self._stars = VGroup()
        if stars:
            x0, x1, y0, y1 = star_region
            accents = list(self.theme.star_accents)
            for i in range(star_count):
                r = rnd.uniform(0.03, 0.10)
                core = Circle(radius=r, fill_color=WHITE, fill_opacity=0.85, stroke_width=0)
                halo1 = Circle(radius=r * 2.0, fill_color=WHITE, fill_opacity=0.10, stroke_width=0)
                halo2 = Circle(radius=r * 3.4, fill_color=WHITE, fill_opacity=0.045, stroke_width=0)
                g = VGroup(halo2, halo1, core).move_to(
                    [rnd.uniform(x0, x1), rnd.uniform(y0, y1), 0]
                )
                g.vel = np.array([rnd.uniform(-0.22, 0.22), rnd.uniform(-0.13, 0.13), 0.0])
                g.op = rnd.uniform(0.3, 1.0)
                g.freq = rnd.uniform(0.5, 1.8)
                g.phase = rnd.uniform(0.0, 6.28)
                g.accent = accents[i % len(accents)] if i % 4 == 0 and accents else None
                self._stars.add(g)
            self._star_bounds = (x0, x1, y0, y1)
        self.add(self._stars)

        self.add_updater(self._refresh)

    # ------------------------------------------------------------------
    def link(self, chart) -> "DeepSpace":
        """Follow ``chart``'s current colour (call once, e.g. in ``construct``)."""
        self._linked = chart
        chart.add_updater(lambda m, dt: self.set_tint(m.current_color))
        self.set_tint(chart.current_color)
        return self

    def set_tint(self, color) -> "DeepSpace":
        """Recolour the nebula and the star halos."""
        self._tint = ManimColor(color)
        return self

    def set_fade(self, value: float) -> "DeepSpace":
        """Global brightness of the backdrop, ``1`` = full, ``0`` = almost black."""
        self._fade = float(np.clip(value, 0.0, 1.0))
        return self

    def install(self, scene) -> "DeepSpace":
        """Add the backdrop to a scene (``backdrop.install(self)``)."""
        scene.add(self)
        return self

    # ------------------------------------------------------------------
    def _refresh(self, mob: VGroup, dt: float) -> None:
        self._time += dt
        t = self._time
        f = self._fade
        tint = self._tint

        for c in self._glow:
            c.set_opacity(0.020 * (0.25 + 0.75 * f))
        for blob in self._nebula:
            for c in blob:
                c.set_color(tint)
                c.set_opacity(c.base_op * f)

        if not len(self._stars):
            return
        x0, x1, y0, y1 = self._star_bounds
        for p in self._stars:
            p.shift(p.vel * dt)
            if p.get_x() > x1:
                p.set_x(x0)
            if p.get_x() < x0:
                p.set_x(x1)
            if p.get_y() > y1:
                p.set_y(y0)
            if p.get_y() < y0:
                p.set_y(y1)
            osc = 0.55 + 0.45 * math.sin(t * p.freq + p.phase)
            if p.accent:
                base = ManimColor(p.accent)
                halo = mix(base, tint, 0.30)
            else:
                base = mix(tint, WHITE, 0.55)
                halo = tint
            p[2].set_color(base)
            p[2].set_opacity(p.op * osc * 0.9 * f)
            p[1].set_color(halo)
            p[1].set_opacity(0.10 * p.op * osc * f)
            p[0].set_color(halo)
            p[0].set_opacity(0.045 * p.op * osc * f)
