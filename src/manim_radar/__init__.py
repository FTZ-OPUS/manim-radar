"""``manim-radar`` — animated radar (spider) charts for Manim.

Build a chart, morph it into another one with a single command, or play a whole
sequence::

    from manim import *
    from manim_radar import RadarChart, RadarData, RadarReel, DeepSpace

    AXES = ["Speed", "Power", "Range", "Comfort", "Price", "Safety"]

    class Demo(Scene):
        def construct(self):
            chart = RadarChart(axes=AXES, values=[8, 6, 7, 9, 5, 8], title="Six axes")
            self.add(DeepSpace().link(chart))          # optional starfield
            self.play(chart.reveal())

            # one command morphs into another snapshot
            self.play(chart.morph_to([5, 9, 4, 6, 9, 7], color="#E868C8"))

            # ...or play a whole sequence in one go
            RadarReel(chart, [
                RadarData(axes=AXES, values=[9, 9, 8, 9, 9, 9], name="All round"),
            ], backdrop=True).play_on(self)
"""

from __future__ import annotations

__version__ = "0.1.0"

from .animations import (
    TRANSITIONS,
    GlitchFlash,
    RadarFade,
    RadarMorph,
    RadarReveal,
    Shockwave,
)
from .backdrop import DeepSpace, set_scene_background
from .chart import RadarChart
from .config import STYLES, RadarConfig, get_style, style_names
from .data import RadarData
from .numbers import RollingNumber
from .reel import RadarReel
from .theme import THEMES, RadarTheme, get_theme, theme_names
from .utils import ease_in_out_cubic, ease_out_back, mix, pick_font

__all__ = [
    "__version__",
    # core
    "RadarChart",
    "RadarData",
    "RadarConfig",
    "RadarTheme",
    # animations
    "RadarMorph",
    "RadarReveal",
    "RadarFade",
    "Shockwave",
    "GlitchFlash",
    "TRANSITIONS",
    # helpers
    "RadarReel",
    "DeepSpace",
    "RollingNumber",
    "set_scene_background",
    # presets & utilities
    "STYLES",
    "THEMES",
    "get_style",
    "get_theme",
    "style_names",
    "theme_names",
    "mix",
    "pick_font",
    "ease_in_out_cubic",
    "ease_out_back",
]
