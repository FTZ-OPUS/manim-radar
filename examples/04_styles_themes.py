# -*- coding: utf-8 -*-
"""04 · Styles & themes — one chart, three styles, five themes.

    manim -ql examples/04_styles_themes.py StylesThemes
"""

from manim import *

from manim_radar import RadarChart, RadarData, set_scene_background, style_names, theme_names

AXES = ["A", "B", "C", "D", "E", "F"]
VALUES = [8, 5, 9, 6, 7, 8]


class StylesThemes(Scene):
    def construct(self):
        # ---- styles ----------------------------------------------------
        set_scene_background("midnight")
        for name in style_names():
            chart = RadarChart(axes=AXES, values=VALUES, style=name, theme="midnight")
            chart.set_radius(2.6)
            label = Text(name, font_size=30).to_edge(DOWN, buff=0.6)
            self.add(chart, label)
            self.play(chart.reveal(run_time=0.6))
            self.wait(0.3)
            self.play(FadeOut(chart), FadeOut(label))

        # ---- themes ----------------------------------------------------
        for name in theme_names():
            set_scene_background(name)
            chart = RadarChart(axes=AXES, values=VALUES, theme=name,
                               style="minimal" if name == "paper" else "neo")
            chart.set_radius(2.4)
            label = Text(name, font_size=30, color=chart.theme.axis_color(0))
            label.to_edge(DOWN, buff=0.6)
            self.add(chart, label)
            self.play(chart.reveal(run_time=0.5))
            self.wait(0.25)
            self.play(FadeOut(chart), FadeOut(label))
