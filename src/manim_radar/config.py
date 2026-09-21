"""Structural configuration + bundled style presets.

Every knob that is *not* a colour lives here (geometry, what to draw, fonts,
transition timing). Colours live in :class:`manim_radar.theme.RadarTheme`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional, Sequence, Union

__all__ = ["RadarConfig", "STYLES", "style_names", "get_style"]


@dataclass
class RadarConfig:
    """All structural options of a :class:`~manim_radar.chart.RadarChart`."""

    # ---- geometry --------------------------------------------------------
    #: outer ring radius, in scene units (Manim's default frame is 14.22 x 8)
    radius: float = 2.9
    #: chart centre in scene units ``(x, y)``; a little below the middle leaves
    #: room for the nameplate / title above the chart
    position: tuple = (0.0, -0.18)
    #: number of concentric grid rings (the outermost ring is the full scale)
    levels: int = 5
    #: angle of the first axis, in degrees (90 = straight up)
    start_angle: float = 90.0
    #: if True the axes run clockwise
    clockwise: bool = True

    # ---- grid ------------------------------------------------------------
    ring_width: float = 1.5
    ring_width_outer: float = 2.4
    ring_opacity: float = 0.50
    ring_opacity_outer: float = 0.95
    spoke_width: float = 1.9
    spoke_opacity: float = 0.72
    grid_glow: bool = True
    grid_glow_width: float = 8.0
    grid_glow_opacity: float = 0.10
    #: draw small scale numbers (2/4/6/8…) along one spoke
    show_level_labels: bool = True
    level_label_axis: int = 0
    level_label_size: int = 17
    level_label_offset: float = 0.26

    # ---- data polygon ----------------------------------------------------
    fill_opacity: float = 0.45
    inner_tint: bool = True
    inner_tint_scale: float = 0.55
    inner_tint_opacity: float = 0.10
    inner_tint_mix: float = 0.45
    line_width: float = 4.5
    #: 0 = none, 1 = one soft glow, 2 = glow + wide halo
    glow_layers: int = 2
    glow_width: float = 15.0
    glow_opacity: float = 0.22
    halo_width: float = 30.0
    halo_opacity: float = 0.08
    #: colour the 6 edges with a gradient between the two axis colours
    rainbow_edges: bool = True
    edge_segments: int = 3
    vertex_dots: bool = True
    dot_radius: float = 0.155

    # ---- axis labels & numbers -------------------------------------------
    show_axis_names: bool = True
    #: distance of the axis names from the centre, as a multiple of ``radius``
    label_offset: float = 1.10
    name_font: Optional[str] = None
    name_size: int = 26
    name_weight: str = "BOLD"
    #: colour axis names with their axis colour (False -> near-white)
    colored_axis_names: bool = True
    #: "roll" (odometer tween) | "swap" (snap to integers) | "off"
    numbers: str = "roll"
    number_font: Optional[str] = None
    number_size: int = 28
    #: place the numbers right after the axis name (True) or inside the chart
    numbers_next_to_name: bool = True
    #: radius multiple of the numbers when ``numbers_next_to_name=False``
    number_offset: float = 0.62
    #: horizontal gap between an axis name and its number
    number_gap: float = 0.18
    number_format: str = "{:g}"
    #: appended when a value exceeds the full scale (e.g. ``10`` -> ``10+``)
    overflow_suffix: str = "+"
    #: vertical travel of the odometer wheel, in scene units (one line height
    #: keeps the outgoing and incoming digits cleanly separated while rolling)
    roll_height: float = 0.44

    # ---- decorations -----------------------------------------------------
    sweep: bool = True
    sweep_period: float = 5.5
    sweep_angle: float = 36.0
    sweep_opacity: float = 0.055
    sweep_edge_width: float = 1.6

    # ---- transitions -----------------------------------------------------
    #: add a shockwave ring on every morph
    shockwave: bool = True
    shock_duration: float = 0.40
    shock_radius: float = 5.0
    #: fraction of the morph spent "dipping" before values roll up
    dip_ratio: float = 0.24
    #: default run time of :meth:`RadarChart.morph_to`
    morph_run_time: float = 1.3
    #: how far values dip below their target (in value units)
    dip_drop: float = 1.0
    dip_floor: float = 2.0
    #: quantise values to integers while rolling (classic snap-in look)
    stepped: bool = False
    #: emphasise the dataset with an extra orange/cyan double outline
    rim: bool = False
    rim_offset_outer: float = 0.030
    rim_offset_inner: float = 0.040
    rim_width_outer: float = 4.5
    rim_width_inner: float = 2.8
    rim_pulse: float = 3.0

    # ---- chroma glitch (used by transition="glitch") ---------------------
    glitch_offset: float = 0.06
    glitch_bar_width: float = 20.0

    # ---- title & nameplate ----------------------------------------------
    title: Optional[str] = None
    title_font: Optional[str] = None
    title_size: int = 30
    #: vertical position of the header, as a multiple of ``radius``
    title_offset: float = 1.30
    #: show ``RadarData.name`` above the chart
    show_dataset_name: bool = True
    #: vertical position of the nameplate, as a multiple of ``radius``
    name_offset: float = 1.28
    name_size: int = 34
    #: extra gap between nameplate and header when both are shown
    name_gap: float = 0.55

    # ---- misc ------------------------------------------------------------
    #: global opacity multiplier (1 = fully visible)
    opacity: float = 1.0
    #: random seed for decorations that live on the chart
    seed: int = 7
    #: extra keyword arguments forwarded to every ``Text`` mobject
    text_kwargs: dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    def evolved(self, **changes) -> "RadarConfig":
        """Return a copy with a few fields replaced (``None`` values ignored)."""
        clean = {k: v for k, v in changes.items() if v is not None}
        unknown = set(clean) - set(self.__dataclass_fields__)
        if unknown:
            raise TypeError(f"unknown RadarConfig field(s): {', '.join(sorted(unknown))}")
        return replace(self, **clean)

    def validated(self) -> "RadarConfig":
        """Sanity-check the numbers; raises ``ValueError`` on nonsense."""
        if self.radius <= 0:
            raise ValueError("radius must be > 0")
        if self.levels < 1:
            raise ValueError("levels must be >= 1")
        if self.numbers not in ("roll", "swap", "off"):
            raise ValueError("numbers must be 'roll', 'swap' or 'off'")
        if not 0.0 <= self.dip_ratio < 1.0:
            raise ValueError("dip_ratio must be in [0, 1)")
        if self.morph_run_time <= 0:
            raise ValueError("morph_run_time must be > 0")
        return self


# ---------------------------------------------------------------------------
# style presets — "neo" is the 2.0 look, "classic" is the 1.0 look
# ---------------------------------------------------------------------------
STYLES: dict[str, RadarConfig] = {
    # 2.0：彩虹描边 + 顶点光点 + 刻度 + 扫光 + 双层辉光 + 滚轮数字
    "neo": RadarConfig(),
    # 1.0：单层填充 + 亮白描边 + 冷灰网格 + 跳变数字，装饰全部关掉
    "classic": RadarConfig(
        radius=3.2,
        position=(0.0, -0.14),
        ring_width=1.4,
        ring_width_outer=1.6,
        ring_opacity=0.42,
        ring_opacity_outer=0.75,
        spoke_width=1.4,
        spoke_opacity=0.42,
        grid_glow=False,
        show_level_labels=False,
        fill_opacity=0.38,
        inner_tint=False,
        line_width=5.0,
        glow_layers=1,
        glow_width=18.0,
        glow_opacity=0.30,
        rainbow_edges=False,
        vertex_dots=False,
        colored_axis_names=False,
        label_offset=1.02,
        name_size=26,
        numbers="swap",
        sweep=False,
        shockwave=False,
        dip_ratio=0.10,
        stepped=True,
        morph_run_time=0.75,
        show_dataset_name=False,
    ),
    # minimal：干净版，适合浅色主题 / 数据图表
    "minimal": RadarConfig(
        radius=2.5,
        position=(0.0, -0.10),
        levels=4,
        ring_width=1.2,
        ring_width_outer=1.8,
        ring_opacity=0.35,
        ring_opacity_outer=0.7,
        spoke_width=1.2,
        spoke_opacity=0.45,
        grid_glow=False,
        level_label_size=15,
        fill_opacity=0.22,
        inner_tint=False,
        line_width=3.5,
        glow_layers=0,
        rainbow_edges=False,
        edge_segments=1,
        vertex_dots=True,
        dot_radius=0.10,
        name_size=22,
        number_size=22,
        sweep=False,
        shockwave=False,
        morph_run_time=1.1,
    ),
}


def style_names() -> list[str]:
    """Names of all bundled styles."""
    return list(STYLES)


def get_style(style: Union[str, RadarConfig, None]) -> RadarConfig:
    """Resolve ``"neo"`` / a :class:`RadarConfig` / ``None`` to a config."""
    if style is None:
        return replace(STYLES["neo"])
    if isinstance(style, RadarConfig):
        return replace(style)
    if isinstance(style, str):
        key = style.strip().lower()
        if key in STYLES:
            return replace(STYLES[key])
        raise KeyError(f"unknown style {style!r}; available: {', '.join(style_names())}")
    raise TypeError(f"style must be str | RadarConfig | None, got {type(style)!r}")
