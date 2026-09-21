# -*- coding: utf-8 -*-
"""Smoke tests — no rendering, so they run fast in CI.

Run with::

    pytest -q
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from manim_radar import (
    STYLES,
    THEMES,
    RadarChart,
    RadarConfig,
    RadarData,
    RadarMorph,
    RadarReel,
    RadarTheme,
    __version__,
    get_style,
    get_theme,
    style_names,
    theme_names,
)

AXES = ["A", "B", "C", "D", "E", "F"]
VALUES = [8, 6, 7, 9, 5, 8]


# ---------------------------------------------------------------------------
# data model
# ---------------------------------------------------------------------------
def test_version_and_registry():
    assert isinstance(__version__, str) and __version__.count(".") == 2
    assert set(style_names()) == {"neo", "classic", "minimal"}
    assert "midnight" in theme_names() and "paper" in theme_names()


def test_radar_data_validation():
    RadarData(axes=AXES, values=VALUES)
    with pytest.raises(ValueError):
        RadarData(axes=AXES, values=VALUES[:-1])  # length mismatch
    with pytest.raises(ValueError):
        RadarData(axes=["A", "B"], values=[1, 2])  # too few axes
    with pytest.raises(ValueError):
        RadarData(axes=AXES, values=[1, 2, 3, 4, 5, -1])  # negative
    with pytest.raises(ValueError):
        RadarData(axes=AXES, values=VALUES, emphasis="nope")


def test_radar_data_is_immutable_and_helpers_work():
    data = RadarData(axes=AXES, values=VALUES, name="first")
    assert data.values == tuple(float(v) for v in VALUES)
    assert data.n_axes == 6
    other = data.with_values([1, 1, 1, 1, 1, 1])
    assert other.values == (1.0,) * 6 and data.values == tuple(float(v) for v in VALUES)
    assert other.renamed("second").name == "second"
    assert data.ratios(10)[0] == pytest.approx(0.8)


def test_scale_snaps_to_round_level_labels():
    # scale = levels * k  -> every grid ring gets an integer label
    assert RadarData(axes=AXES, values=[8, 6, 7, 9, 5, 8]).scale_for(5) == 10
    assert RadarData(axes=AXES, values=[3, 2, 4, 1, 3, 2]).scale_for(5) == 5
    assert RadarData(axes=AXES, values=[45, 30, 50, 20, 40, 35]).scale_for(5) == 50
    # an explicit max_value always wins (enables the "10+" overflow look)
    assert RadarData(axes=AXES, values=[11, 5, 7, 9, 10, 11], max_value=10).scale_for(
        5
    ) == 10


# ---------------------------------------------------------------------------
# theme / style plumbing
# ---------------------------------------------------------------------------
def test_theme_and_style_lookup():
    from manim import ManimColor

    midnight = get_theme("midnight")
    assert midnight.axis_color(0) == ManimColor(midnight.axis_colors[0])
    assert midnight.axis_color(6) == midnight.axis_color(0)  # cycles
    assert get_theme(RadarTheme(name="x")).name == "x"
    with pytest.raises(KeyError):
        get_theme("does-not-exist")
    with pytest.raises(KeyError):
        get_style("does-not-exist")
    with pytest.raises(TypeError):
        get_theme(12)
    # presets must not be mutated by callers
    cfg = get_style("neo")
    cfg.radius = 99
    assert STYLES["neo"].radius != 99


def test_config_evolved_rejects_unknown_fields():
    with pytest.raises(TypeError):
        RadarConfig().evolved(nonsense=1)
    with pytest.raises(ValueError):
        RadarConfig(numbers="phone").validated()
    with pytest.raises(ValueError):
        RadarConfig(radius=0).validated()


# ---------------------------------------------------------------------------
# the chart
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("style", style_names())
@pytest.mark.parametrize("theme", theme_names())
def test_chart_builds_for_every_style_and_theme(style, theme):
    chart = RadarChart(axes=AXES, values=VALUES, style=style, theme=theme)
    assert chart.axis_count == 6
    assert chart.values == [float(v) for v in VALUES]
    assert chart.width > 0 and chart.height > 0
    assert len(chart.web) == chart.config.levels + 6


def test_chart_shorthands():
    data = RadarData(axes=AXES, values=VALUES, name="n")
    assert RadarChart(data).values == chart_values(RadarChart(axes=AXES, values=VALUES))
    with pytest.raises(ValueError):
        RadarChart()  # nothing to draw
    with pytest.raises(ValueError):
        RadarChart(RadarData(axes=AXES, values=VALUES), axes=AXES, values=VALUES)
    with pytest.raises(ValueError):
        RadarChart(axes=AXES, values=VALUES, numbers="banana")


def chart_values(chart):
    return [float(v) for v in chart.values]


def test_polygon_geometry_tracks_values():
    chart = RadarChart(axes=AXES, values=VALUES)
    pts = chart._polygon_local()[:-1]
    # local coordinates are relative to the chart centre (the frame anchor)
    radii = [float(np.linalg.norm(p)) for p in pts]
    expected = [chart.config.radius * v / chart.full_scale for v in VALUES]
    assert radii == pytest.approx(expected, rel=1e-6)


def test_chart_survives_transforms():
    chart = RadarChart(axes=AXES, values=VALUES)
    before = float(np.linalg.norm(chart._polygon_local()[0]))
    chart.scale(0.5)
    unit = float(np.linalg.norm(chart._anchor[1].get_center() - chart._anchor[0].get_center()))
    assert unit == pytest.approx(0.5, rel=1e-6)
    chart.shift([1.0, 0.5, 0])
    chart.rotate(0.3)
    chart._refresh(chart, 0.0)
    # local geometry is unchanged, the world mapping carries the transform
    assert float(np.linalg.norm(chart._polygon_local()[0])) == pytest.approx(before)
    assert not np.allclose(chart._anchor[0].get_center(), [0, 0, 0])


def test_set_values_and_radius():
    chart = RadarChart(axes=AXES, values=VALUES)
    chart.set_values([1] * 6, scale=5)
    assert chart.values == [1.0] * 6 and chart.full_scale == 5
    with pytest.raises(ValueError):
        chart.set_values([1, 2])
    chart.set_radius(1.5)
    assert chart.config.radius == 1.5


# ---------------------------------------------------------------------------
# numbers
# ---------------------------------------------------------------------------
def test_odometer_labels_and_overflow():
    chart = RadarChart(
        RadarData(axes=AXES, values=[11, 5, 7, 9, 10, 11], max_value=10)
    )
    num = chart.value_numbers[0]
    assert num.label_for(7) == "7"
    assert num.label_for(10) == "10"
    assert num.label_for(11) == "10+"  # overflow suffix
    num.render(6.4, np.zeros(3))
    visible = [t for t in num._cache.values() if t.get_fill_opacity() > 0]
    assert len(visible) == 2  # rolling between two integers


@pytest.mark.parametrize("mode", ["roll", "swap", "off"])
def test_number_modes(mode):
    chart = RadarChart(axes=AXES, values=VALUES, numbers=mode)
    chart._refresh(chart, 0.0)
    shown = [
        t
        for num in chart.value_numbers
        for t in num._cache.values()
        if t.get_fill_opacity() > 0.01
    ]
    assert len(shown) == (0 if mode == "off" else len(VALUES))


# ---------------------------------------------------------------------------
# animations
# ---------------------------------------------------------------------------
def test_morph_interpolates_values_colour_and_scale():
    chart = RadarChart(axes=AXES, values=VALUES)
    target = RadarData(axes=AXES, values=[2] * 6, color="#FF0000", max_value=5.0)
    anim = chart.morph_to(target, transition="smooth", run_time=1.0)
    anim.begin()
    anim.interpolate_mobject(0.0)
    assert chart.values == [float(v) for v in VALUES]
    anim.interpolate_mobject(0.5)
    mid = chart.values
    assert all(2.0 < v < 9.0 for v in mid)
    anim.interpolate_mobject(1.0)
    anim.finish()
    assert chart.values == [2.0] * 6
    assert chart.full_scale == 5.0
    assert chart.current_color.to_hex().upper().startswith("#FF")
    assert chart.data is target


def test_morph_dips_before_rolling_up():
    chart = RadarChart(axes=AXES, values=[9] * 6)
    chart.config = chart.config.evolved(dip_ratio=0.25)
    anim = chart.morph_to(RadarData(axes=AXES, values=[9] * 6), transition="dip")
    anim.begin()
    anim.interpolate_mobject(0.25)  # end of the dip phase
    dipped = chart.values[0]
    anim.interpolate_mobject(1.0)
    assert dipped < 9.0
    anim.finish()


def test_unknown_transition_raises():
    chart = RadarChart(axes=AXES, values=VALUES)
    with pytest.raises(ValueError):
        chart.morph_to(RadarData(axes=AXES, values=VALUES), transition="teleport")
    assert isinstance(chart.morph_to([1] * 6), RadarMorph)


def test_morph_requires_same_axis_layout():
    chart = RadarChart(axes=AXES, values=VALUES)
    with pytest.raises(ValueError):
        chart.morph_to(RadarData(axes=["A", "B", "C"], values=[1, 2, 3]))


def test_reveal_sets_values_from_zero_and_disappear_fades():
    chart = RadarChart(axes=AXES, values=VALUES)
    reveal = chart.reveal()
    reveal.begin()
    reveal.interpolate_mobject(0.0)
    assert chart.values == [0.0] * 6
    reveal.interpolate_mobject(1.0)
    reveal.finish()
    assert chart.values == [float(v) for v in VALUES]

    fade = chart.disappear()
    fade.begin()
    fade.interpolate_mobject(1.0)
    fade.finish()
    assert chart._opacity == 0.0


def test_shockwave_and_glitch_are_constructible():
    chart = RadarChart(axes=AXES, values=VALUES)
    wave = chart.shockwave(color="#FF0000")
    wave.interpolate_mobject(0.5)
    glitch = chart.glitch_in()
    glitch.begin()
    glitch.interpolate_mobject(0.5)
    assert chart._glitch >= 0.0
    glitch.finish()
    assert chart._glitch == 0.0


def test_fade_out_plugin_still_works_through_updater():
    # FadeOut animates opacity of the whole family; the chart redirects it.
    chart = RadarChart(axes=AXES, values=VALUES)
    chart.set_opacity(0.3)
    assert chart._opacity == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# reel
# ---------------------------------------------------------------------------
def test_reel_assigns_palette_colours_and_summarises():
    chart = RadarChart(axes=AXES, values=VALUES)
    snapshots = [RadarData(axes=AXES, values=[i + 1] * 6, name=f"n{i}") for i in range(4)]
    reel = RadarReel(chart, snapshots, hold=0.5)
    assert all(d.color for d in reel.datasets)
    assert len({d.color for d in reel.datasets}) == 4
    assert reel.total_time > 0
    assert "RadarReel" in reel.summary()
    with pytest.raises(ValueError):
        RadarReel(chart, [])


def test_reel_keeps_explicit_colours():
    chart = RadarChart(axes=AXES, values=VALUES)
    snap = RadarData(axes=AXES, values=[1] * 6, color="#123456")
    reel = RadarReel(chart, [snap])
    assert reel.datasets[0].color == "#123456"


# ---------------------------------------------------------------------------
# legacy generations
# ---------------------------------------------------------------------------
def test_legacy_timeline_converts():
    from manim_radar.legacy import REPLICA_TIMELINE, replica_datasets

    datasets = replica_datasets()
    assert len(datasets) == len(REPLICA_TIMELINE) == 23
    assert all(d.max_value == 10 for d in datasets)
    emphases = [d.emphasis for d in datasets if d.emphasis]
    assert "zoom" in emphases and "gap" in emphases and "rim" in emphases
    assert all(d.hold and d.hold > 0 for d in datasets)


def test_legacy_scenes_exist():
    from manim_radar.legacy import RadarV1Scene, RadarV2Scene

    assert issubclass(RadarV1Scene, object) and issubclass(RadarV2Scene, object)
    assert RadarV1Scene.style == "classic" and RadarV2Scene.style == "neo"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def test_utility_math():
    from manim import ManimColor

    from manim_radar import ease_in_out_cubic, mix, pick_font

    assert ease_in_out_cubic(0.0) == 0.0 and ease_in_out_cubic(1.0) == 1.0
    assert ease_in_out_cubic(0.5) == pytest.approx(0.5)
    assert mix("#000000", "#FFFFFF", 0.0) == ManimColor("#000000")
    assert mix("#000000", "#FFFFFF", 1.0) == ManimColor("#FFFFFF")
    grey = mix("#000000", "#FFFFFF", 0.5).to_hex().upper()
    assert grey[1:3] == grey[3:5] == grey[5:7]  # neutral grey
    assert pick_font(["definitely-not-a-font"]) is None
    assert pick_font(["definitely-not-a-font"], default="sans") == "sans"
