# -*- coding: utf-8 -*-
"""02 · Morph gallery — every transition preset, and the nameplate crossfade.

A snapshot with a ``name`` shows it above the chart; the name crossfades on
every transition. (A ``title`` is a *static* header — it steps aside when a
snapshot brings its own name, so the two never fight for the same line.)

    manim -qh examples/02_morph_gallery.py MorphGallery
"""

from manim import *

from manim_radar import DeepSpace, RadarChart, RadarData, set_scene_background

AXES = ["速度", "力量", "续航", "舒适", "价格", "安全"]
SNAPSHOTS = {
    "smooth": RadarData(axes=AXES, values=[8, 6, 7, 9, 5, 8], name="平滑 smooth"),
    "shockwave": RadarData(axes=AXES, values=[4, 9, 5, 7, 9, 6], name="冲击波 shockwave",
                           color="#E868C8"),
    "zoom": RadarData(axes=AXES, values=[9, 5, 9, 6, 5, 9], name="大转场 zoom",
                      color="#4DD0E1"),
    "glitch": RadarData(axes=AXES, values=[6, 6, 6, 6, 6, 6], name="故障闪入 glitch",
                        color="#FFD166", emphasis="gap"),
    "rim": RadarData(axes=AXES, values=[10, 8, 9, 10, 8, 10], name="高亮描边 rim",
                     color="#F040E0", emphasis="rim"),
}


class MorphGallery(Scene):
    def construct(self):
        set_scene_background("midnight")
        chart = RadarChart(SNAPSHOTS["smooth"], theme="midnight")
        self.add(DeepSpace().link(chart))
        self.play(chart.reveal())
        self.wait(0.3)

        for key, transition in (("smooth", "smooth"), ("shockwave", "shockwave"),
                                ("zoom", "zoom"), ("glitch", "glitch"),
                                ("rim", "dip")):
            self.play(chart.morph_to(SNAPSHOTS[key], transition=transition))
            self.wait(0.25)

        self.play(chart.disappear())
