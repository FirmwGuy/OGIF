# OmniGraphIF (OGIF)
## A Transport-Agnostic Graph Interface for Introspection, Control, and Automation

**Repository:** OGIF  
**Document Type:** Repository overview (informative)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-22

---

OmniGraphIF (OGIF) is a draft specification for representing programs, subsystems, and modules as a **typed graph** of entities connected by **typed relations**, with discoverable **capabilities**, **operations**, **events**, **queries**, and **subscriptions** across a transport-agnostic surface.

### Start Here

- `OGIF.md` - OGIF Core specification (v0.1.0 draft)
- `OGIF_Profiles.md` - Profile guide (informative companion)
- `profiles/` - Individual profile specifications and extensions

### Repo Hygiene

- Validate Markdown invariants: `python3 tools/check_docs.py`
  - UTF-8, LF-only newlines
  - Balanced triple-backtick code fences
  - Presence of self-describing doc headers (e.g., `**Last Updated:**`)

### License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), same as the TCA project. See `LICENSE`.
