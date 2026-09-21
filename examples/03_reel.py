# -*- coding: utf-8 -*-
"""03 · Reel — a whole sequence with a single command.

    manim -qh examples/03_reel.py Reel
"""

from manim import *

from manim_radar import RadarChart, RadarData, RadarReel, set_scene_background

AXES = ["考试频率", "竞赛热度", "数学美感", "应用广度", "初等亲和", "推广深度"]
INEQS = [
    RadarData(axes=AXES, values=[10, 9, 7, 9, 10, 7], name="基本不等式", color="#17B8BA"),
    RadarData(axes=AXES, values=[10, 10, 10, 10, 8, 10], name="柯西不等式", color="#E868C8"),
    RadarData(axes=AXES, values=[8, 8, 8, 9, 5, 10], name="赫尔德不等式", color="#8F86E8"),
    RadarData(axes=AXES, values=[8, 8, 8, 9, 6, 9], name="琴生不等式", color="#40C878"),
    RadarData(axes=AXES, values=[6, 9, 8, 4, 8, 6], name="内斯比特不等式", color="#FFB74D"),
    RadarData(axes=AXES, values=[5, 7, 10, 7, 8, 9], name="等周不等式", color="#4DD0E1",
              emphasis="zoom"),
    RadarData(axes=AXES, values=[10, 10, 10, 10, 10, 10], name="六边形拉满", color="#FFD166",
              emphasis="rim", max_value=10),
]


class Reel(Scene):
    def construct(self):
        set_scene_background("midnight")
        chart = RadarChart(
            INEQS[0],
            title="不等式 · 六维雷达图鉴",
            theme="midnight",
            numbers="roll",
        )
        # One command plays the whole thing: reveal, morph through every
        # snapshot, hold, fade out — with the starfield and the black gap.
        RadarReel(
            chart,
            INEQS,
            hold=0.55,
            transition="shockwave",
            backdrop=True,
        ).play_on(self)
