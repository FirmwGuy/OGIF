# OGIF Time Control Extension Specification
## Deterministic Logical Time, Freezing, Stepping, and Rate Control Across Profiles

**Extension Name:** OGIF Time Control (OmniTime)  
**OGIF Extension ID:** `ogif.ext:timecontrol-0`  
**Extension Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Applies To:** Any OGIF endpoint; commonly used by `ogif.profile:omnidom-1` and `ogif.profile:omniecs-0`

---

## 1. Purpose

`ogif.ext:timecontrol-0` standardizes **deterministic logical time control** for OGIF endpoints.

It enables external clients (test harnesses, automation tools, simulators) to:

- freeze time (pause autonomous progression),
- advance time deterministically by a specified delta,
- step ticks/frames deterministically (when a profile defines ticks),
- resume real-time progression,
- query current time/tick and time mode,
- and subscribe to time changes.

This extension exists to make time-based behavior testable and reproducible without relying on wall-clock timing, sleeps, or fragile animation/simulation assumptions.

---

## 2. Design Goals

An endpoint implementing this extension MUST provide:

1. A discoverable **logical clock** concept (one or more clocks).
2. Deterministic control of time progression in **test mode**:
   - freeze / resume,
   - advance by delta,
   - optional tick stepping.
3. Clear integration semantics with profiles:
   - OmniDOM: animation-/transition-gated logic becomes semantically testable.
   - OmniECS: stepping ticks makes simulation deterministic.
   - Render diagnostics: stepping frames can be deterministic if supported.
4. Strong security gating so time control cannot be abused in production.

---

## 3. Non-goals

This extension does NOT standardize:

- OS clock APIs,
- real-time scheduling guarantees,
- networking time synchronization,
- physics determinism details (handled by OmniECS profile rules),
- animation curve definitions (handled by application/renderers).

It provides only the **control surface** and **basic invariants**.

---

## 4. Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

---

## 5. Feature Advertisement and Negotiation

Endpoints implementing this extension MUST advertise it via `ogif.getVersion`:

```json
{
  "features": {
    "timeControl": "ogif.ext:timecontrol-0"
  }
}
````

If only partial functionality is implemented (e.g., freeze/resume but not tick stepping), the endpoint MUST declare supported operations in the clock descriptor (§7.3).

---

## 6. Clock Model

### 6.1 Logical Clocks

A **logical clock** is a controllable time base for a scope such as:

* an entire endpoint runtime,
* a UI subsystem,
* a simulation world,
* a render scene/viewport,
* a pipeline scheduler.

Endpoints MAY expose multiple clocks.

### 6.2 Clock Scopes (Recommended)

Each clock SHOULD declare a scope:

* `endpoint` — global/default for the runtime
* `ui` — OmniDOM/UI timebase
* `world` — OmniECS simulation timebase
* `render` — render loop timebase
* `custom:<name>` — custom subsystems

### 6.3 Clock Units

Clocks MUST declare time units:

* `attributes.timeUnit` = `"seconds"` or `"ms"` (recommended)
* `state.now` MUST be expressed in that unit (number)

If the clock supports ticks/frames, it SHOULD also expose:

* `state.tick` (integer; monotonic)
* `attributes.tickUnit` (e.g., `"tick"`, `"frame"`, `"step"`)
* `attributes.tickRateNominal` (number; optional)

---

## 7. Entities and Relations

### 7.1 Clock Entity Type (MUST)

Each logical clock MUST be represented as an OGIF entity:

* `type = "time.clock"`

Example:

```json
{
  "id": "time://clock/world-main",
  "type": "time.clock",
  "name": "World Main Clock",
  "capabilities": ["time.cap:freezable", "time.cap:advanceable", "time.cap:tickSteppable"],
  "attributes": {
    "scope": "world",
    "timeUnit": "seconds",
    "tickUnit": "tick",
    "tickRateNominal": 60
  },
  "state": {
    "mode": "running",
    "now": 123.456,
    "tick": 7407,
    "rate": 1.0
  }
}
```

### 7.2 Clock Attachment (Recommended)

If a clock controls a specific profile root (e.g., an `ecs.world` or `render.scene`), the endpoint SHOULD link it with:

* `time:controls` (clock ? target entity)

Example:

* `time://clock/world-main --time:controls--> ecs://world/main`

### 7.3 Capabilities (Reserved)

Clock entities advertise supported control actions via capabilities:

* `time.cap:queryable` (recommended; implies `getClock` supported)
* `time.cap:freezable` (freeze/resume supported)
* `time.cap:advanceable` (advance by delta supported)
* `time.cap:rateControllable` (set rate supported)
* `time.cap:tickSteppable` (step ticks/frames supported)
* `time.cap:adminOnly` (marker; policy enforced separately)

Capabilities are advertisements; authorization is enforced by policy (§11).

---

## 8. Time State and Invariants

### 8.1 Required State Fields

Every clock MUST expose in `state`:

* `mode`: `"running" | "frozen"`
* `now`: number (in declared `timeUnit`)
* `rate`: number (default 1.0; see §8.3)

If the clock supports ticks:

* `tick`: integer (monotonic)

### 8.2 Monotonicity (MUST)

* `state.now` MUST be non-decreasing over the lifetime of a clock.
* `state.tick` (if present) MUST be non-decreasing.

Time MUST NOT go backwards, even when frozen/resumed.

### 8.3 Rate Semantics (Optional)

If rate control is supported:

* `state.rate` represents the multiplier applied when in `running` mode.
* When `mode="frozen"`, rate MUST NOT cause time to progress.
* Implementations MAY clamp rates; if so they MUST declare:

  * `attributes.rateMin`, `attributes.rateMax`.

---

## 9. Operations

Operations MAY be exposed via OGIF operation descriptors (`ogif.invoke`) and/or via wrapper methods.

### 9.1 Reserved Capabilities for Operations

Endpoints MUST capability-gate time control operations (see §11). This extension reserves:

* `time.cap:freezable` ? freeze/resume
* `time.cap:advanceable` ? advance
* `time.cap:tickSteppable` ? stepTicks/stepFrames
* `time.cap:rateControllable` ? setRate

### 9.2 Required Operations (Extension Conformance)

An endpoint claiming this extension MUST support:

#### 9.2.1 `time.getClock`

Returns clock entity state snapshot (or a subset) and supported controls.

Params (recommended):

* `clockId`

Result:

* `clock` (entity snapshot) OR `{ state, attributes, capabilities }`

#### 9.2.2 `time.listClocks`

Returns available clocks.

Result:

* `clockIds[]` and optionally summaries.

### 9.3 Freeze/Resume (Required if `time.cap:freezable`)

#### 9.3.1 `time.freeze`

Params:

* `clockId`

Effects:

* Sets `state.mode = "frozen"`.

#### 9.3.2 `time.resume`

Params:

* `clockId`

Effects:

* Sets `state.mode = "running"`.

### 9.4 Advance (Required if `time.cap:advanceable`)

#### 9.4.1 `time.advance`

Params:

* `clockId`
* `delta` (number; same unit as `timeUnit`)
* `options` (optional):

  * `emitBoundaryEvents` (boolean; default true)
  * `maxSteps` (integer; safety for internal stepping loops)

Effects:

* If `delta <= 0`, MUST be rejected.
* Increases `state.now` by `delta`.
* If the controlled subsystem uses ticks/frames, the implementation SHOULD advance internal state consistently and deterministically.

**Important:** `advance` MUST NOT require wall-clock waiting. It is logical time.

### 9.5 Tick/Frame Stepping (Required if `time.cap:tickSteppable`)

#### 9.5.1 `time.stepTicks`

Params:

* `clockId`
* `ticks` (integer > 0)
* `dt` (optional number; if provided, advances `now` by `ticks*dt`)

Effects:

* Increments `state.tick` by `ticks`.
* Advances `state.now` consistently (if `dt` known/provided).
* MUST cause the subsystem to run exactly that many deterministic update steps.

If the subsystem defines ticks (e.g., OmniECS), this MUST align with that profile’s tick semantics.

### 9.6 Rate Control (Required if `time.cap:rateControllable`)

#### 9.6.1 `time.setRate`

Params:

* `clockId`
* `rate` (number > 0)

Effects:

* Sets `state.rate = rate`.
* Does not change `now` immediately.

---

## 10. Events and Observation

Event types MUST be prefixed `time.event:` and use the OGIF event envelope.

### 10.1 Required Events

When clock state changes (mode, now, tick, rate), the endpoint MUST make it observable via:

* OGIF patch events (`ogif.event:StateChanged` / `EntityChanged`) and SHOULD also emit:

* `time.event:ClockChanged`

Payload (recommended):

```json
{
  "type": "time.event:ClockChanged",
  "source": "time://clock/world-main",
  "data": {
    "mode": "frozen",
    "now": 123.456,
    "tick": 7407,
    "rate": 1.0
  }
}
```

### 10.2 Boundary Events (Recommended)

When stepping/advancing causes subsystem boundary events (ticks/frames), those events SHOULD be emitted by the subsystem profile as normal.

Example expectations:

* OmniECS: `ecs.event:TickStarted` / `ecs.event:TickEnded`
* RenderDiag: `render.event:FrameRendered`
* OmniDOM: state changes that would occur during animations/transitions become visible via state changes and/or completion events if defined by the app.

This extension does not define subsystem boundary events; it only controls time and recommends coherent integration.

---

## 11. Security Considerations (Normative)

Time control is powerful and can break production behavior.

### 11.1 Authorization (MUST)

Endpoints MUST restrict:

* freeze/resume,
* advance,
* tick stepping,
* rate changes

to authorized clients only.

A safe default is:

* enabled only in test/dev builds,
* local-only transport,
* explicit tokens/ACLs.

### 11.2 Visibility (SHOULD)

Even read access to clocks can leak system behavior timing. Endpoints SHOULD allow read-only introspection broadly but may restrict details in production.

### 11.3 Audit (SHOULD)

Endpoints SHOULD log time control operations:

* actor/client identity,
* clockId,
* delta/ticks/rate,
* timestamp,
* correlationId.

---

## 12. Conformance Levels

### 12.1 TimeControl-Read Conformance

An endpoint is conformant at read level if it:

* exposes one or more `time.clock` entities,
* supports `time.listClocks` and `time.getClock`,
* makes clock state observable via patch events.

### 12.2 TimeControl-Control Conformance

Includes read and additionally:

* supports `freeze` and `resume` for clocks advertising `time.cap:freezable`,
* supports `advance` for clocks advertising `time.cap:advanceable`,
* enforces authorization.

### 12.3 TimeControl-Deterministic Conformance (Recommended)

Includes control and additionally:

* provides deterministic stepping (`time.stepTicks`) for clocks advertising `time.cap:tickSteppable`,
* ensures repeated runs under the same inputs produce identical tick and state outcomes (within documented tolerances),
* documents determinism limits (floating point, platform differences).

---

## 13. Example Integration Patterns (Informative)

### 13.1 OmniECS Deterministic Simulation

* `time://clock/world-main time:controls ecs://world/main`
* Test harness:

  1. `time.freeze(world-main)`
  2. `time.stepTicks(world-main, 600, dt=1/60)`
  3. assert ECS component states and events deterministically

### 13.2 OmniDOM Animation-Gated UI Logic

* `time://clock/ui-main time:controls ui://root`
* Test harness:

  1. click a button that starts a transition
  2. `time.advance(ui-main, 0.3)` to finish transition
  3. assert new screen nodes present and focus moved

### 13.3 Render Loop Stepping

* `time://clock/render-main time:controls render://scene/main`
* Test harness:

  1. `time.freeze(render-main)`
  2. `time.stepTicks(render-main, 1)` (frame stepping)
  3. query `render.getVisibleSet`

---

**End of OGIF Time Control Extension `ogif.ext:timecontrol-0` (Draft)**
