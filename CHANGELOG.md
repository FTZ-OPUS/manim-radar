# Changelog

All notable changes to `manim-radar` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-09-21

First release.

### Added

- `RadarChart` — an animated radar/spider chart as a real Manim `VGroup`
  (supports `shift` / `move_to` / `scale` / `rotate` / `FadeIn` / `FadeOut`).
- `RadarData` — immutable snapshot model with axes, values, name, colour,
  full scale, emphasis, hold and per-snapshot transition overrides.
- `RadarChart.morph_to(...)` — one command tweens values, full scale, colour,
  emphasis outline, opacity and nameplate in a single pass.
- Six transition presets: `smooth`, `dip`, `shockwave`, `zoom`, `glitch`, `stepped`.
- `RadarReel` — plays a whole list of snapshots (with black gaps) in one call.
- `RadarReveal`, `RadarFade`, `GlitchFlash` and `Shockwave` animations.
- `RollingNumber` — odometer-style value read-out with overflow labels (`10+`).
- `DeepSpace` — radial glow + corner vignette + nebula blobs + drifting stars,
  tinted by the chart colour.
- Three style presets (`neo`, `classic`, `minimal`) and five themes
  (`midnight`, `aurora`, `ember`, `violet`, `paper`).
- `RadarConfig` (~60 fields) and `RadarTheme` for full customisation.
- Legacy generations rebuilt on the library: `RadarV1Scene` (1.0) and
  `RadarV2Scene` (2.0), playing the bundled 23-snapshot demo reel.
- Cross-platform font fallback (`PingFang SC` → `Microsoft YaHei` → `Noto Sans CJK` …).
- `manim-radar` CLI: `themes`, `styles`, `template`, `demo --render`.
- Manim plugin entry point (`manim.plugins`) and example scenes under `examples/`.
- Test suite (41 tests) that runs without rendering.

[Unreleased]: https://github.com/FTZ-OPUS/manim-radar/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/FTZ-OPUS/manim-radar/releases/tag/v0.1.0
