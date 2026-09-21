"""Odometer style value numbers (the "rolling digits" used by style ``neo``)."""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
from manim import DOWN, LEFT, UP, Text, VGroup

__all__ = ["RollingNumber"]


class RollingNumber(VGroup):
    """A value read-out that rolls like a mechanical counter.

    Instead of rebuilding a ``Text`` on every frame, all needed integers are
    rendered **lazily once** and kept in a cache; the current value then only
    moves / fades two of them. That makes it cheap enough to drive from an
    updater at 60 fps.
    """

    def __init__(
        self,
        *,
        font: Optional[str] = None,
        size: int = 28,
        color: str = "#FFFFFF",
        decimals: int = 0,
        template: str = "{:g}",
        max_value: float = 10.0,
        suffix: str = "+",
        roll_height: float = 0.30,
        mode: str = "roll",
        weight: str = "BOLD",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.font = font
        self.size = size
        self.color = color
        self.decimals = max(0, int(decimals))
        self.template = template
        self.max_value = float(max_value)
        self.suffix = suffix
        self.roll_height = float(roll_height)
        self.mode = mode
        self.weight = weight
        self._cache: dict[int, Text] = {}

    # ------------------------------------------------------------------
    def label_for(self, value: float) -> str:
        """Text that should be shown for ``value`` (handles the overflow ``+``)."""
        v = float(value)
        if self.max_value > 0 and v > self.max_value + 1e-9:
            v = self.max_value
            extra = self.suffix
        else:
            extra = ""
        q = round(v, self.decimals) if self.decimals else float(round(v))
        try:
            text = self.template.format(q)
        except (ValueError, IndexError, KeyError):  # pragma: no cover - user template
            text = f"{q:g}"
        return f"{text}{extra}"

    def _key_limit(self) -> int:
        return max(1, int(math.ceil(self.max_value)) + 1)

    def set_max_value(self, value: float) -> None:
        """Update the full scale (the odometer overflow rule follows it).

        Cached glyphs whose label is no longer correct are dropped and rebuilt
        lazily, so call this when the chart settles — not on every frame.
        """
        value = float(value)
        if abs(value - self.max_value) < 1e-9:
            return
        self.max_value = value
        limit = self._key_limit()
        for key in list(self._cache):
            txt = self._cache[key]
            if key > limit or getattr(txt, "text", None) != self.label_for(key):
                self.remove(txt)
                self._cache.pop(key, None)

    def _text_for(self, key: int) -> Text:
        """Cached ``Text`` for integer ``key``."""
        key = int(np.clip(key, 0, self._key_limit()))
        if key not in self._cache:
            txt = Text(
                self.label_for(key),
                font=self.font,
                weight=self.weight,
                font_size=self.size,
                color=self.color,
            )
            txt.set_opacity(0)
            self._cache[key] = txt
            self.add(txt)
        return self._cache[key]

    @staticmethod
    def _apply_scale(txt: Text, scale: float) -> None:
        """Hook for subclasses.

        The glyphs themselves simply inherit the chart's transform (they are
        children of the chart), so nothing has to be done here — only the wheel
        travel uses ``scale``.
        """

    # ------------------------------------------------------------------
    def render(
        self,
        value: float,
        anchor: np.ndarray,
        *,
        opacity: float = 1.0,
        scale: float = 1.0,
    ) -> None:
        """Point the counter at a new ``value`` / world ``anchor``.

        ``scale`` is the chart's current unit length, so wheel travel and glyph
        size follow when the whole chart is scaled.
        """
        value = float(value)
        op = float(np.clip(opacity, 0.0, 1.0))
        anchor = np.asarray(anchor, dtype=float)

        if self.mode == "off":
            for txt in self._cache.values():
                txt.set_opacity(0)
            return

        if self.mode == "swap":
            key = int(round(value))
            active = {key: (1.0, np.zeros(3))}
        else:  # "roll"
            lo = int(math.floor(value + 1e-9))
            frac = value - lo
            if frac > 1 - 1e-9:
                lo += 1
                frac = 0.0
            travel = self.roll_height * scale
            active = {
                lo: (1.0 - frac, UP * (frac * travel)),
                lo + 1: (frac, DOWN * ((1.0 - frac) * travel)),
            }

        for key, (weight, offset) in active.items():
            txt = self._text_for(key)
            self._apply_scale(txt, scale)
            txt.move_to(anchor + offset, aligned_edge=LEFT)
            txt.set_opacity(weight * op)
        for key, txt in self._cache.items():
            if key not in active:
                txt.set_opacity(0)
