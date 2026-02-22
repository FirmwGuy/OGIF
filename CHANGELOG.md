# Changelog
## OmniGraphIF (OGIF) Specification Documents

**Document Type:** Changelog  
**Status:** Draft  
**Last Updated:** 2026-02-22

---

This file tracks notable changes to the specification documents in this repository.

The canonical spec version is defined in `OGIF.md`.

## [Unreleased]

## [0.1.0] - 2026-02-22

### Added

- Initial OmniGraphIF (OGIF) core spec (`OGIF.md`)
- Initial profile set under `profiles/` (OmniDOM, OmniRPC, OmniFlow, OmniECS, OmniPolicy, OmniTelemetry, OmniTime, OmniState, OmniAgent, RenderDiag)

### Changed

- Clarified core APIs (relation keys, paging, subscriptions)
- Aligned OmniDOM time-control semantics with `ogif.ext:timecontrol-0`
- Normalized Markdown encoding (UTF-8/LF) and fixed code fences
