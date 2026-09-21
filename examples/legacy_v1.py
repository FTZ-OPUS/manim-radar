# -*- coding: utf-8 -*-
"""Legacy generation 1.0 — the classic look, rebuilt on the library.

    manim -qh examples/legacy_v1.py RadarV1Scene

Subclassing the bundled scene is the easiest way to tweak it (theme, title,
radius, …) — Manim only auto-discovers scenes defined in the file it runs.
"""

from manim import *  # noqa: F401,F403

from manim_radar.legacy import RadarV1Scene as _RadarV1Scene


class RadarV1Scene(_RadarV1Scene):
    """1.0: flat grid, single glow layer, snap-in numbers, hard black gap."""

    theme = "midnight"
    title = None
