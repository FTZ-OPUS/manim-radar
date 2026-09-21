# -*- coding: utf-8 -*-
"""01 · Quickstart — the smallest useful radar chart.

    manim -qh examples/01_quickstart.py Quickstart
"""

from manim import *

from manim_radar import DeepSpace, RadarChart, set_scene_background

AXES = ["速度", "力量", "续航", "舒适", "价格", "安全"]


class Quickstart(Scene):
    def construct(self):
        set_scene_background("midnight")

        # 一个静态标题 + 一条数据 = 最简单的可用雷达图
        chart = RadarChart(
            axes=AXES,
            values=[8, 6, 7, 9, 5, 8],
            title="六维能力雷达",
            style="neo",
            theme="midnight",
        )
        self.add(DeepSpace().link(chart))

        # 1) 入场：从中心生长 + 淡入
        self.play(chart.reveal())
        self.wait(0.3)

        # 2) 一句命令：变形到另一组数据（颜色、数值、缓动一起走）
        self.play(chart.morph_to([5, 9, 5, 6, 9, 9], color="#FFB74D"))
        self.wait(0.4)

        # 3) 出场
        self.play(chart.disappear())
