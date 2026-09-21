"""One-command sequence player: :class:`RadarReel`."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional, Union

from manim import Scene, UpdateFromAlphaFunc

from .backdrop import DeepSpace
from .chart import RadarChart
from .data import RadarData

__all__ = ["RadarReel"]


class RadarReel:
    """Play a whole list of snapshots with a single command.

    Examples
    --------
    ::

        chart = RadarChart(axes=SIX_AXES, values=[...], title="Six axes")
        RadarReel(chart, [d1, d2, d3, d4], hold=0.6, backdrop=True).play_on(self)

    Per-snapshot overrides come from :class:`~manim_radar.data.RadarData`:
    ``hold``, ``transition``, ``emphasis`` (``"zoom"`` / ``"gap"`` / ``"rim"``)
    and ``color``. Snapshots without an explicit colour get one from the theme
    palette, in order.
    """

    def __init__(
        self,
        chart: RadarChart,
        datasets: Iterable[RadarData],
        *,
        hold: float = 0.6,
        transition: Optional[str] = None,
        run_time: Optional[float] = None,
        intro: Union[bool, float] = True,
        outro: Union[bool, float] = True,
        backdrop: Union[bool, DeepSpace, None] = None,
        gap_hold: float = 1.5,
        auto_color: bool = True,
        verbose: bool = False,
    ) -> None:
        self.chart = chart
        self.hold = float(hold)
        self.transition = transition
        self.run_time = run_time
        self.intro = intro
        self.outro = outro
        self.gap_hold = float(gap_hold)
        self.auto_color = auto_color
        self.verbose = verbose
        self.backdrop_spec = backdrop
        self.backdrop: Optional[DeepSpace] = None

        items = list(datasets)
        if not items:
            raise ValueError("RadarReel needs at least one dataset")
        self.datasets = (
            [self._with_palette_color(d, i) for i, d in enumerate(items)]
            if auto_color
            else items
        )

    # ------------------------------------------------------------------
    def _with_palette_color(self, data: RadarData, index: int) -> RadarData:
        if data.color:
            return data
        return replace(data, color=str(self.chart.theme.dataset_color(index)))

    # ------------------------------------------------------------------
    @property
    def total_time(self) -> float:
        """Rough duration of the reel in seconds."""
        default_rt = self.run_time or self.chart.config.morph_run_time
        total = 0.0
        for d in self.datasets:
            total += default_rt + (d.hold if d.hold is not None else self.hold)
            if d.emphasis == "gap":
                total += self.gap_hold + 0.9
        return total

    def summary(self) -> str:
        """Human readable description of what :meth:`play_on` will do."""
        lines = [
            f"RadarReel · {len(self.datasets)} snapshots · "
            f"~{self.total_time:.1f}s · style={self.chart.config.title or '-'}"
        ]
        for i, d in enumerate(self.datasets):
            flags = []
            if d.emphasis:
                flags.append(f"emphasis={d.emphasis}")
            if d.transition:
                flags.append(f"transition={d.transition}")
            if d.rim:
                flags.append("rim")
            tail = ("  [" + ", ".join(flags) + "]") if flags else ""
            lines.append(
                f"  {i + 1:>3}. {str(d.name or '-'):<16} {tuple(d.values)}{tail}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def play_on(self, scene: Scene) -> "RadarReel":
        """Play the whole sequence on ``scene``."""
        chart = self.chart
        if self.verbose:
            print(self.summary())
        if chart not in scene.mobjects:
            scene.add(chart)
        self._install_backdrop(scene)

        if self.intro:
            rt = float(self.intro) if isinstance(self.intro, (int, float)) and self.intro is not True else 0.9
            scene.play(chart.reveal(run_time=rt), run_time=rt)

        for d in self.datasets:
            if d.emphasis == "gap":
                scene.play(chart.disappear(), run_time=0.8)
                self._fade_backdrop(scene, 0.0, 0.6)
                scene.wait(self.gap_hold)
                self._fade_backdrop(scene, 1.0, 0.4)
                scene.play(chart.glitch_in(), run_time=0.75)
            else:
                trans = d.transition or ("zoom" if d.emphasis == "zoom" else self.transition)
                scene.play(
                    chart.morph_to(
                        d,
                        transition=trans,
                        run_time=self.run_time,
                        rim=1.0 if d.emphasis == "rim" else None,
                    )
                )
            wait = d.hold if d.hold is not None else self.hold
            if wait > 0:
                scene.wait(wait)

        if self.outro:
            rt = float(self.outro) if isinstance(self.outro, (int, float)) and self.outro is not True else 0.8
            scene.play(chart.disappear(run_time=rt), run_time=rt)
            if self.backdrop is not None:
                self._fade_backdrop(scene, 0.0, 0.5)
                scene.remove(self.backdrop)
        return self

    # ------------------------------------------------------------------
    def _install_backdrop(self, scene: Scene) -> None:
        spec = self.backdrop_spec
        if spec is False or spec is None:
            return
        if isinstance(spec, DeepSpace):
            self.backdrop = spec
            if spec not in scene.mobjects:
                scene.add(spec)
        else:
            self.backdrop = DeepSpace(theme=self.chart.theme)
            scene.add(self.backdrop)
        self.backdrop.link(self.chart)

    def _fade_backdrop(self, scene: Scene, to: float, run_time: float) -> None:
        if self.backdrop is None:
            return
        start = self.backdrop._fade
        scene.play(
            UpdateFromAlphaFunc(
                self.backdrop,
                lambda m, a, s=start, t=to: m.set_fade(s + (t - s) * a),
            ),
            run_time=run_time,
        )
