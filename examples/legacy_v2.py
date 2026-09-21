# -*- coding: utf-8 -*-
"""Legacy generation 2.0 — the glow / rainbow / shockwave look, rebuilt.

    manim -qh examples/legacy_v2.py RadarV2Scene

Try another theme by editing ``theme`` below (midnight / aurora / ember /
violet / paper) — everything else stays the same.
"""

from manim import *  # noqa: F401,F403

from manim_radar.legacy import RadarV2Scene as _RadarV2Scene


class RadarV2Scene(_RadarV2Scene):
    """2.0: rainbow outline, vertex glows, sweep beam, shockwave transitions."""

    theme = "midnight"
    title = "六维能力 · 雷达图鉴"
