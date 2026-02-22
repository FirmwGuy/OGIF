# OmniRenderDiag Profile Specification
## OGIF Profile: Render Diagnostics for 2D/3D/Video Without Pixel-Based Testing

**Profile Name:** OmniRenderDiag  
**OGIF Profile ID:** `ogif.profile:omnirenderdiag-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Selector Baseline:** `ogif-sel-0` + OmniRenderDiag Selector Extension `render-sel-0` (defined herein)

---

## 1. Purpose

OmniRenderDiag is an OGIF profile that exposes **stable, semantic render diagnostics** for systems that render:

- 2D/3D graphics (OpenGL/Vulkan/DirectX/Metal engines),
- video layers/overlays,
- complex HUDs,
- composited scenes with cameras, passes, and object visibility.

The goal is to enable robust automation and testing of “what is being rendered” **without** relying on:
- screenshots or pixel diffs (CV/golden images),
- brittle coordinate scraping,
- waveform-like comparisons for media.

Instead, OmniRenderDiag exposes **render facts** that are strongly correlated with the user’s perception and interaction, such as:
- which semantic objects are visible/drawn,
- object picking hit results,
- camera transforms/projection parameters,
- projected bounds in screen space (normalized),
- render-pass membership and basic stats,
- animation/skeleton pose hashes (optional but useful).

OmniRenderDiag is complementary to:
- **OmniDOM** (UI semantics, safeguards, announcements),
- **OmniECS** (world/simulation state, determinism),
and typically links render objects to canonical world entities via `ogif:facetOf`.

---

## 2. Design Goals

An OmniRenderDiag implementation MUST allow a client to:

1. **Discover** scenes, cameras, render objects, and (optionally) passes.
2. **Link** render objects to canonical entities (ECS/world) via `ogif:facetOf` (RECOMMENDED).
3. **Pick** objects (raycast/ID-buffer/engine picking) by screen coordinate and obtain stable hits.
4. **Query visibility**: which objects are considered drawn/visible for a given scene/camera/frame.
5. **Query projected bounds** for objects in a stable coordinate space (normalized).
6. **Observe** frame boundaries and render-level errors/alerts.
7. Enforce security boundaries so diagnostics do not become an “ESP/wallhack” surface in production.

---

## 3. Non-goals

OmniRenderDiag does NOT standardize:

- exact pixel output, color grading, post-processing fidelity,
- shader source, draw-call order, GPU buffer dumps,
- full scene graph authoring,
- physics correctness (OmniECS/physics facets),
- UI semantics (OmniDOM).

If exact visuals are required, pixel-based golden rendering is still valid in some contexts, but it is outside this profile’s scope.

---

## 4. Relationship to OGIF Core

OmniRenderDiag uses OGIF constructs:

- scenes/cameras/objects/passes are OGIF **entities** (`render.*` types),
- render membership is OGIF **relations** (`render:*` kinds),
- diagnostics methods are OGIF **operations** (`ogif.invoke`) and/or profile wrappers,
- render events use OGIF **event envelopes** with `render.event:*` types,
- changes are observable via OGIF patch events (`ogif.event:GraphChanged`, etc.).

Endpoints MUST advertise `ogif.profile:omnirenderdiag-0` via `ogif.getVersion`.

---

## 5. Entity Types

### 5.1 Required Types

An OmniRenderDiag endpoint MUST represent:

- `render.scene` — a renderable scene/context (may correspond to a viewport, layer, world camera)
- `render.object` — an addressable render object (mesh instance, sprite, UI quad, video plane, etc.)
- `render.camera` — a camera used for projection

### 5.2 Optional Types (Recommended)

Endpoints SHOULD represent when meaningful:

- `render.pass` — render pass/layer (opaque categories like “shadow”, “main”, “ui”, “post”)
- `render.material` — material identity (not shader source; stable material IDs)
- `render.skeleton` — skeleton/rig entity (for animated characters)
- `render.clip` — animation clip handle (if engine exposes it cleanly)

---

## 6. Relation Kinds and Structural Conventions

OmniRenderDiag does not impose a global topology constraint. It defines specific relation kinds for interpretability.

### 6.1 Reserved Relation Kinds (Directed)

- `render:inScene` (object ? scene)  
  Object participates in scene.

- `render:usesCamera` (scene ? camera)  
  Scene uses camera for projection (may be multiple; see §7.2).

- `render:hasPass` (scene ? pass) (optional)  
  Scene defines or uses passes.

- `render:drawnInPass` (object ? pass) (optional)  
  Object is categorized under a pass/layer.

- `render:hasSkeleton` (object ? skeleton) (optional)  
  Object uses a skeleton/rig.

### 6.2 Optional Scene-Graph Relation (If Engine Has It)

If the engine has a transform hierarchy (scene graph), it MAY expose:

- `render:parentOf` (object ? object)

If exposed, the subgraph induced by `render:parentOf` SHOULD be a forest (acyclic), but this is not required. Many engines do not have a strict scene-tree in modern renderers.

### 6.3 Cross-Subsystem Facets (Strongly Recommended)

Render objects SHOULD link to canonical entities using OGIF core relations:

- `render.object --ogif:facetOf--> ecs.entity` (or `world.entity`)

UI overlay elements usually use `ogif:represents` instead (OmniDOM).

---

## 7. State and Attributes Model

### 7.1 Common Object Attributes (Recommended)

A `render.object` SHOULD include:

- `attributes.objectClass` (string; e.g., `"player"`, `"enemy"`, `"prop"`, `"ui"`, `"video"`)
- `attributes.layer` (string or integer; engine-defined but stable)
- `attributes.schemaRef` (optional; for structured object metadata)
- `meta.testTag` (RECOMMENDED for stable tests)

### 7.2 Scene State (Recommended)

A `render.scene` SHOULD expose:

- `state.frameIndex` (integer; monotonic)
- `state.viewport` (object):
  - `width` (int), `height` (int)
  - `dpiScale` (number; optional)
- `state.activeCameraId` (string; if multiple cameras possible)
- `attributes.coordinateSpace` (string; see §8.1)

### 7.3 Camera State (Recommended)

A `render.camera` SHOULD expose enough data for reproducible projections:

- `state.pose` (object):
  - `position` (x,y,z)
  - `orientation` (quaternion or yaw/pitch/roll; declare format)
- `state.viewMatrix` and `state.projectionMatrix` MAY be provided (arrays), or provide derived fields:
  - `attributes.fovY`, `attributes.near`, `attributes.far`
  - `attributes.projection = "perspective"|"ortho"`
- If matrices are provided, they MUST be in a documented convention (row/column major, handedness).

### 7.4 Object State (Recommended)

A `render.object` SHOULD expose:

- `state.visible` (boolean) — intended visible (not necessarily drawn)
- `state.drawn` (boolean) — actually drawn in last frame (if known)
- `state.transform` (object; optional but useful):
  - position/rotation/scale or matrix (document format)
- `state.lod` (string|int; optional)
- `state.materialId` (string; optional)
- `state.poseHash` (string; optional; see §11.3)

---

## 8. Coordinate Spaces

Render diagnostics must be consistent across clients.

### 8.1 Required Coordinate Spaces

Operations that accept or return 2D coordinates MUST declare one of these spaces:

- `"pixels"`: integer pixel coordinates with origin at top-left of viewport  
  - x in `[0, width)`, y in `[0, height)`

- `"normalized"`: floating coordinates in `[0,1]` with origin at top-left  
  - x = 0 left, x = 1 right; y = 0 top, y = 1 bottom

Endpoints MUST support `"normalized"` for interoperability. `"pixels"` is RECOMMENDED when viewport size is known.

### 8.2 Bounds Format

Projected bounds returned by OmniRenderDiag MUST use `"normalized"` by default:

```json
{
  "space": "normalized",
  "rect": { "x": 0.25, "y": 0.10, "w": 0.30, "h": 0.40 }
}
```

If the object is offscreen, the endpoint MUST either:

* return `null`, or
* return `rect` with `w=0,h=0` and include `data.offscreen=true`.

---

## 9. Operations

OmniRenderDiag operations MAY be exposed via OGIF operation descriptors (`ogif.invoke`) and/or via wrapper methods.

### 9.1 Reserved Capabilities (for Gating)

OmniRenderDiag reserves:

* `render.cap:inspectable` — discoverable/introspectable
* `render.cap:pickable` — supports picking
* `render.cap:visibleSetQueryable` — supports visibility querying
* `render.cap:boundsQueryable` — supports projected bounds querying
* `render.cap:cameraQueryable` — supports camera inspection
* `render.cap:poseHashQueryable` — supports pose hash inspection (optional)
* `render.cap:testControl` — supports camera overrides/time stepping (TEST ONLY; optional)

Capabilities are advertisements; authorization is enforced by policy.

### 9.2 Required Operations for RenderDiag-Read Conformance

An endpoint claiming **OmniRenderDiag-Read Conformance** (§13.1) MUST provide:

#### 9.2.1 `render.getFrameInfo`

Returns current frame counters and viewport.

Recommended params:

* `sceneId`

Recommended result:

* `frameIndex`
* `viewport`
* `activeCameraId` (if applicable)

#### 9.2.2 `render.pick`

Performs a pick query by screen coordinate.

Recommended params:

* `sceneId`
* `x`, `y`
* `space`: `"normalized"` or `"pixels"`
* `mode`: `"closest"` (default) or `"all"`
* `include`: optional fields (e.g., include bounds, facet links)

Recommended result:

* `hits`: array ordered by increasing depth/distance

  * each hit includes:

    * `objectId` (render.object id)
    * `distance` (number; optional)
    * `depth` (number; optional)
    * `pointWorld` (optional)
    * `facetOf` (optional canonical entity id if linked)

If no hit:

* `hits = []`

#### 9.2.3 `render.getVisibleSet`

Returns the set of render objects considered drawn/visible.

Recommended params:

* `sceneId`
* optional `cameraId`
* optional `selector` to filter candidates (OGIF selector)
* optional `includeHidden` (default false; security-gated)

Recommended result:

* `objectIds[]`
* optional `reason` fields if the engine can explain exclusions (not required)

#### 9.2.4 `render.getBounds2D`

Returns projected bounds of a render object in normalized space.

Recommended params:

* `sceneId`
* `objectId`

Recommended result:

* `bounds` in §8.2 format (or null if not projectable)

### 9.3 Optional Operations

#### 9.3.1 `render.getCamera`

Returns camera pose/projection.

Params:

* `cameraId`

Result:

* `state.pose` and projection metadata.

#### 9.3.2 `render.getPassStats`

Returns basic per-pass stats (draw counts, object counts), if passes are modeled.

Params:

* `sceneId`
* optional `passId`

#### 9.3.3 Test-Only Controls (Optional, MUST be capability-gated)

If supported, MUST advertise `features.renderTestControl = "render-test-0"` and require `render.cap:testControl`:

* `render.test.setCameraPose({ cameraId, pose })`
* `render.test.setViewport({ sceneId, width, height, dpiScale? })`
* `render.test.freezeFrame({ sceneId })`
* `render.test.stepFrame({ sceneId, frames })`

These MUST NOT be enabled in production unless explicitly authorized.

---

## 10. Events

Event types MUST be prefixed `render.event:` and use OGIF event envelopes.

### 10.1 Required Events (Observable Rendering)

An endpoint claiming OmniRenderDiag-Read Conformance SHOULD emit frame boundary events. If it cannot (performance constraints), it MUST still expose `state.frameIndex` and patch events for it.

Recommended required event:

* `render.event:FrameRendered`

Payload (recommended):

```json
{
  "type": "render.event:FrameRendered",
  "source": "render://scene/main",
  "data": {
    "frameIndex": 1042,
    "viewport": { "width": 1920, "height": 1080 },
    "activeCameraId": "render://camera/main"
  }
}
```

### 10.2 Recommended Events

* `render.event:VisibleSetChanged` (when visible set changes materially; may be noisy)
* `render.event:RenderError` (device lost, shader compile failure in debug, missing assets)
* `render.event:PassStats` (periodic stats)

### 10.3 Event Redaction (MUST)

If events would reveal hidden objects or privileged diagnostics, the endpoint MUST:

* gate them by authorization, or
* redact payload (e.g., omit `objectIds`), or
* suppress emission to that subscriber.

---

## 11. Stability and Determinism Guidance

### 11.1 “Render Facts” Should Be Stable

Render facts exposed by this profile SHOULD be stable across:

* minor driver differences,
* nondeterministic draw ordering,
* floating point noise.

Therefore, implementations SHOULD prefer:

* object identity sets (“visible objects”),
* broad bounds rectangles,
* stable hashes (poseHash),
  over:
* exact per-vertex outputs,
* exact screen-space pixel masks.

### 11.2 Visible vs Drawn Semantics (Recommended)

Engines differ. OmniRenderDiag uses:

* `state.visible`: intended visible (game-level)
* `state.drawn`: drawn in last frame (render-level)

If `state.drawn` is not available, implementations MAY omit it and rely on `render.getVisibleSet` as the authoritative query.

### 11.3 Pose Hash (Optional but Useful)

Animated characters can be validated without pixels by exposing:

* `state.poseHash`: stable hash of relevant animation pose data (e.g., bone transforms quantized)

If implemented:

* hash algorithm MUST be documented,
* SHOULD be stable across platforms in test mode.

---

## 12. Security Considerations (Normative)

### 12.1 Anti-Wallhack Requirement (MUST)

Render diagnostics can enable cheating if exposed broadly. Endpoints MUST treat the following as sensitive in production contexts:

* visibility sets,
* picking results beyond what the user could target,
* bounds for occluded/hidden objects,
* pass stats that reveal hidden entities.

Therefore, endpoints MUST enforce authorization and SHOULD default to:

* local-only diagnostics,
* limited scopes (only objects already permitted/visible to the user session),
* suppression/redaction for restricted objects.

### 12.2 Visibility Policy (RECOMMENDED)

Objects SHOULD declare:

* `attributes.visibility = "public" | "restricted" | "hidden"`

When a client lacks permission, the endpoint MUST NOT return hidden object IDs in:

* `render.getVisibleSet`,
* `render.pick`,
* bounds queries,
* events.

### 12.3 Test Controls (MUST be gated)

Any operation that manipulates camera/time/viewport MUST require explicit capabilities and SHOULD be disabled by default in production.

---

## 13. Conformance Levels

### 13.1 OmniRenderDiag-Read Conformance

An endpoint is OmniRenderDiag-Read conformant if it:

* exposes `render.scene`, `render.object`, `render.camera`,
* connects them via `render:inScene` and `render:usesCamera`,
* supports:

  * `render.getFrameInfo`
  * `render.pick`
  * `render.getVisibleSet`
  * `render.getBounds2D`
* provides `normalized` coordinate space for inputs/outputs,
* enforces security/redaction requirements (§12),
* emits `render.event:FrameRendered` OR provides patch-observable `state.frameIndex`.

### 13.2 OmniRenderDiag-Control Conformance (Optional)

Includes Read and additionally:

* supports test-only controls (camera/viewport/frame stepping) under explicit capability and feature advertisement.

### 13.3 OmniRenderDiag-Test Conformance (Recommended for CI)

Includes Read and additionally:

* stable object IDs or `meta.testTag`,
* deterministic `frameIndex` progression under test time control (if available),
* stable pose hashes if pose hashing is enabled.

---

## 14. Interop Patterns (Informative)

### 14.1 Picking Implementations

Engines may implement `render.pick` using:

* ID buffer rendering,
* CPU raycast against collision/render proxies,
* engine-level selection APIs.

The profile does not mandate how; it mandates stable semantics and security rules.

### 14.2 Linking to World Entities

Recommended:

* `render.object --ogif:facetOf--> ecs.entity`

This makes it easy to answer:

* “Which world entity did the user click?”
* “Is the object representing Player42 visible?”

### 14.3 Coexisting With OmniDOM

* OmniDOM validates interaction rules and user-facing messages.
* OmniRenderDiag validates render-visibility/picking facts.
* Both can be used together to test a game end-to-end without pixel diffing.

---

## 15. Example (Informative)

### 15.1 Scene With Player and UI Overlay

Entities:

* `render://scene/main` (`render.scene`)
* `render://camera/main` (`render.camera`)
* `render://object/playerMesh` (`render.object`)
* `ecs://world/main/entity/Player42` (OmniECS)
* `ui://hud#reticle` (OmniDOM)

Relations:

* `render://object/playerMesh render:inScene render://scene/main`
* `render://scene/main render:usesCamera render://camera/main`
* `render://object/playerMesh ogif:facetOf ecs://world/main/entity/Player42`
* `ui://hud#reticle ogif:represents ecs://world/main/entity/Player42` (optional)

Automation:

1. `render.pick(sceneId, x,y, space="normalized")`
2. confirm hit includes `facetOf == Player42`
3. assert `render.getBounds2D(playerMesh)` overlaps reticle region
4. use OmniDOM to ensure UI feedback/permissions align with gameplay state

---

**End of OmniRenderDiag Profile Specification `ogif.profile:omnirenderdiag-0` (Draft)**
