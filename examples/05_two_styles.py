# -*- coding: utf-8 -*-
"""05 · Two charts side by side — the classic (1.0) and neo (2.0) styles.

Because a :class:`RadarChart` is an ordinary Manim mobject you can lay several
of them out, give each its own style/theme, and animate them in the same
``self.play`` call.

    manim -qh examples/05_two_styles.py TwoStyles
"""

from manim import *

from manim_radar import DeepSpace, RadarChart, RadarData, set_scene_background

AXES = ["速度", "力量", "续航", "舒适", "价格", "安全"]
SNAPSHOTS = [
    RadarData(axes=AXES, values=[5, 7, 6, 8, 4, 7], name="起步", color="#17B8BA"),
    RadarData(axes=AXES, values=[8, 6, 9, 5, 7, 9], name="均衡", color="#4DD0E1"),
    RadarData(axes=AXES, values=[10, 9, 10, 9, 10, 10], name="拉满", color="#FFD166"),
]


class TwoStyles(Scene):
    def construct(self):
        set_scene_background("midnight")

        classic = RadarChart(SNAPSHOTS[0], style="classic", radius=1.85,
                             title="1.0 · classic", numbers="swap")
        neo = RadarChart(SNAPSHOTS[0], style="neo", radius=1.85, title="2.0 · neo")
        classic.move_to(LEFT * 3.5)
        neo.move_to(RIGHT * 3.5)

        self.add(DeepSpace(star_count=48).link(neo))
        self.play(classic.reveal(run_time=0.7), neo.reveal(run_time=0.7))

        # same data, two very different feels — stepped vs shockwave
        for snap in SNAPSHOTS[1:]:
            self.play(
                classic.morph_to(snap, transition="stepped", run_time=1.2),
                neo.morph_to(snap, transition="shockwave", run_time=1.2),
            )
            self.wait(0.45)

        self.play(classic.disappear(), neo.disappear())
