"""The two original generations, rebuilt on top of the library.

``RadarV1Scene`` reproduces the **1.0** look (flat grid, one glow layer, snap-in
numbers, hard black gap), ``RadarV2Scene`` the **2.0** look (rainbow outline,
vertex glows, sweep beam, starfield, shockwave transitions, odometer numbers).
Both play the same 23-snapshot demo reel that ships with the package.
"""

from __future__ import annotations

from typing import Optional, Sequence

from manim import Scene

from .chart import RadarChart
from .data import RadarData
from .reel import RadarReel

__all__ = [
    "REPLICA_AXES",
    "REPLICA_TIMELINE",
    "REPLICA_TOTAL",
    "replica_datasets",
    "RadarV1Scene",
    "RadarV2Scene",
]

#: Axis names used by the bundled demo reel.
REPLICA_AXES = ("理论贡献", "实践贡献", "群众路线", "个人品德", "国际主义", "历史影响")

#: Full-scale value of the demo reel (values above it render as ``10+``).
REPLICA_MAX = 10.0

#: ``(t, color, values, flags)`` — same timeline the original 120.6 s render used.
REPLICA_TIMELINE = [
    dict(t=1.0, c="#17B8BA", v=(4, 6, 6, 4, 4, 5)),
    dict(t=8.7, c="#B89AF0", v=(5, 8, 8, 8, 7, 7)),
    dict(t=10.0, c="#E868C8", v=(5, 8, 9, 8, 8, 7)),
    dict(t=13.5, c="#E8944A", v=(5, 7, 6, 7, 10, 8)),
    dict(t=18.0, c="#4A90D9", v=(5, 6, 8, 8, 8, 7)),
    dict(t=23.0, c="#8F86E8", v=(8, 3, 4, 3, 4, 7)),
    dict(t=27.2, c="#1FA8C8", v=(5, 6, 8, 8, 8, 7)),
    dict(t=32.0, c="#D8A8C8", v=(7, 3, 5, 7, 6, 8)),
    dict(t=37.0, c="#E07A4A", v=(8, 4, 5, 6, 5, 8)),
    dict(t=41.5, c="#A8C840", v=(5, 7, 8, 8, 8, 7)),
    dict(t=45.5, c="#40C878", v=(7, 6, 7, 6, 7, 7)),
    dict(t=50.5, c="#C8C830", v=(5, 7, 8, 9, 8, 8)),
    dict(t=55.5, c="#E878C8", v=(6, 7, 8, 8, 8, 7)),
    dict(t=60.5, c="#30C8C0", v=(8, 7, 9, 8, 8, 8)),
    dict(t=63.0, c="#D8A0A0", v=(4, 10, 8, 8, 6, 7), zoom=True),
    dict(t=68.5, c="#48C058", v=(7, 8, 6, 6, 10, 7)),
    dict(t=75.0, c="#30C0B0", v=(7, 8, 7, 9, 7, 8)),
    dict(t=80.5, c="#A88AE0", v=(9, 7, 7, 9, 8, 10)),
    dict(t=82.0, c="#F040E0", v=(11, 5, 7, 9, 10, 11)),
    dict(t=88.0, c="#B8C040", v=(8, 6, 6, 9, 9, 8)),
    dict(t=94.0, c="#E04858", v=(8, 9, 6, 6, 6, 8)),
    dict(t=107.0, c="#0F7E7A", v=(10, 10, 9, 10, 9, 10), gap=True, rim=True),
    dict(t=112.0, c="#B03384", v=(10, 10, 11, 10, 9, 10), rim=True),
]

#: Total length of the original reel in seconds.
REPLICA_TOTAL = 120.6
#: Length of the black gap in the middle of the reel.
REPLICA_GAP = 6.0


def replica_datasets(
    axes: Sequence[str] = REPLICA_AXES,
    *,
    transition_time: float = 1.45,
    max_value: float = REPLICA_MAX,
    hold_scale: float = 1.0,
) -> list[RadarData]:
    """Turn :data:`REPLICA_TIMELINE` into a list of :class:`RadarData`.

    Holds are derived from the original timestamps so that the whole reel keeps
    its original pace.
    """
    out: list[RadarData] = []
    n = len(REPLICA_TIMELINE)
    for i, seg in enumerate(REPLICA_TIMELINE):
        nxt = REPLICA_TIMELINE[i + 1]["t"] if i + 1 < n else REPLICA_TOTAL
        dur = nxt - seg["t"]
        emphasis: Optional[str] = None
        if seg.get("gap"):
            emphasis = "gap"
        elif seg.get("zoom"):
            emphasis = "zoom"
        elif seg.get("rim"):
            emphasis = "rim"
        out.append(
            RadarData(
                axes=axes,
                values=seg["v"],
                color=seg["c"],
                max_value=max_value,
                emphasis=emphasis,
                hold=max(0.25, (dur - transition_time) * hold_scale),
            )
        )
    return out


class RadarV1Scene(Scene):
    """The **1.0** generation: plain, angular, snap-in numbers.

    ``manim -qh examples/legacy_v1.py RadarV1Scene``
    """

    style = "classic"
    theme = "midnight"
    title: Optional[str] = None

    def construct(self) -> None:
        chart = RadarChart(
            replica_datasets()[0],
            style=self.style,
            theme=self.theme,
            title=self.title,
        )
        reel = RadarReel(
            chart,
            replica_datasets(),
            transition=None,
            backdrop=False,
            gap_hold=REPLICA_GAP,
        )
        reel.play_on(self)


class RadarV2Scene(Scene):
    """The **2.0** generation: rainbow outline, glow, sweep, shockwaves.

    ``manim -qh examples/legacy_v2.py RadarV2Scene``
    """

    style = "neo"
    theme = "midnight"
    title: Optional[str] = "六维能力 · 雷达图鉴"

    def construct(self) -> None:
        from .backdrop import set_scene_background

        set_scene_background(self.theme)
        chart = RadarChart(
            replica_datasets()[0],
            style=self.style,
            theme=self.theme,
            title=self.title,
        )
        reel = RadarReel(
            chart,
            replica_datasets(),
            transition="shockwave",
            backdrop=True,
            gap_hold=REPLICA_GAP,
        )
        reel.play_on(self)
