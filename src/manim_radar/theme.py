"""Colour themes for :class:`~manim_radar.chart.RadarChart`."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence, Union

from manim import ManimColor

__all__ = ["RadarTheme", "THEMES", "theme_names", "get_theme"]


@dataclass(frozen=True)
class RadarTheme:
    """A palette for one radar look.

    Everything colour related lives here, so swapping a theme restyles the whole
    chart (grid, axes, data polygon, labels, decorations) in one go.
    """

    name: str = "custom"
    #: flat background colour used by :class:`~manim_radar.backdrop.DeepSpace`
    background: str = "#070B16"
    #: colour of the soft radial glow in the middle of the backdrop
    glow: str = "#1A2547"
    #: colour of the corner vignette layers
    vignette: str = "#03040A"
    #: grid (rings) colour
    grid: str = "#8B9BB8"
    #: colour of each axis spoke / axis label (cycles if fewer than axes)
    axis_colors: Sequence[str] = (
        "#4DD0E1", "#FFB74D", "#F06292", "#FFD54F", "#64B5F6", "#CE93D8",
    )
    #: colours used for datasets that do not carry an explicit ``color``
    palette: Sequence[str] = (
        "#17B8BA", "#B89AF0", "#E868C8", "#E8944A", "#4A90D9", "#8F86E8",
        "#1FA8C8", "#40C878", "#C8C830", "#E07A4A", "#30C8C0", "#D878C8",
    )
    #: colour of the axis value numbers
    number: str = "#FFFFFF"
    #: gradient used for the header title
    title_gradient: Sequence[str] = ("#9FB2CC", "#EAF2FF")
    #: gradient used for the dataset nameplate
    name_gradient: Sequence[str] = ("#FFD166", "#F59E62")
    #: double outline colours (``rim`` emphasis)
    rim_outer: str = "#FF9C3C"
    rim_inner: str = "#3CC8FF"
    #: accent colours for the occasional coloured star
    star_accents: Sequence[str] = (
        "#FFD54F", "#4DD0E1", "#F06292", "#64B5F6", "#CE93D8", "#FFB74D",
    )
    #: chromatic split colours used by the glitch transition
    glitch_split: Sequence[str] = ("#FF7A00", "#00CFFF")
    #: how much dataset colours are pushed towards white (0 = none)
    brighten: float = 0.08

    # ---- helpers ---------------------------------------------------------
    def axis_color(self, index: int) -> ManimColor:
        """Colour assigned to axis ``index``."""
        cols = list(self.axis_colors)
        return ManimColor(cols[index % len(cols)])

    def dataset_color(self, index: int) -> ManimColor:
        """Colour assigned to the ``index``-th dataset."""
        cols = list(self.palette)
        return ManimColor(cols[index % len(cols)])

    def evolved(self, **changes) -> "RadarTheme":
        """Return a copy of this theme with a few fields replaced."""
        return replace(self, **changes)


# ---------------------------------------------------------------------------
# built-in themes
# ---------------------------------------------------------------------------
THEMES: dict[str, RadarTheme] = {
    t.name: t
    for t in [
        RadarTheme(name="midnight"),
        RadarTheme(
            name="aurora",
            background="#04121A",
            glow="#0E2A33",
            vignette="#010A0E",
            grid="#7FB2AE",
            axis_colors=("#5EEAD4", "#A3E635", "#38BDF8", "#FDE68A", "#F0ABFC", "#7DD3FC"),
            palette=("#2DD4BF", "#84CC16", "#38BDF8", "#A78BFA", "#FBBF24", "#F472B6"),
        ),
        RadarTheme(
            name="ember",
            background="#140806",
            glow="#33150E",
            vignette="#0A0403",
            grid="#D8A48F",
            axis_colors=("#FF8A65", "#FFD54F", "#F06292", "#FFB74D", "#E57373", "#BCAAA4"),
            palette=("#FF7043", "#FFCA28", "#EF5350", "#FFA726", "#8D6E63", "#F4511E"),
        ),
        RadarTheme(
            name="violet",
            background="#0B0716",
            glow="#221A3D",
            vignette="#05030C",
            grid="#A79BC8",
            axis_colors=("#C4B5FD", "#F0ABFC", "#7DD3FC", "#FDE68A", "#5EEAD4", "#FDA4AF"),
            palette=("#A78BFA", "#E879F9", "#60A5FA", "#FBBF24", "#34D399", "#FB7185"),
        ),
        RadarTheme(
            name="paper",
            background="#F7F5F0",
            glow="#FFFFFF",
            vignette="#DCD7CC",
            grid="#5B6472",
            axis_colors=("#0F766E", "#B45309", "#BE185D", "#A16207", "#1D4ED8", "#6D28D9"),
            palette=("#0F766E", "#B45309", "#BE185D", "#1D4ED8", "#6D28D9", "#15803D"),
            number="#1F2937",
            title_gradient=("#334155", "#0F172A"),
            name_gradient=("#B45309", "#92400E"),
            rim_outer="#EA580C",
            rim_inner="#0369A1",
            star_accents=("#0F766E", "#B45309", "#BE185D", "#1D4ED8"),
            brighten=0.0,
        ),
    ]
}


def theme_names() -> list[str]:
    """Names of all bundled themes."""
    return list(THEMES)


def get_theme(theme: Union[str, RadarTheme, None]) -> RadarTheme:
    """Resolve ``"midnight"`` / a :class:`RadarTheme` / ``None`` to a theme."""
    if theme is None:
        return THEMES["midnight"]
    if isinstance(theme, RadarTheme):
        return theme
    if isinstance(theme, str):
        key = theme.strip().lower()
        if key in THEMES:
            return THEMES[key]
        raise KeyError(
            f"unknown theme {theme!r}; available: {', '.join(theme_names())}"
        )
    raise TypeError(f"theme must be str | RadarTheme | None, got {type(theme)!r}")
