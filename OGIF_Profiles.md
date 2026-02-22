# OGIF Profile Guide
## Recommended Profiles for OmniGraphIF Deployments

**Document Type:** Informative companion (non-normative)  
**Applies To:** OmniGraphIF (OGIF) v0.1.0 (Draft)  
**Last Updated:** 2026-02-21

---

## 1. Why Profiles Exist

OGIF Core defines *how* to represent a system as a graph of entities + relations with operations and events.  
Profiles define *what it means*.

Profiles are necessary because different paradigms have different invariants:

- UI interaction prefers **trees**, focus, event routing, and “user stimulus” semantics.
- Pipelines prefer **DAGs**, streams, and backpressure.
- RPC prefers **resources + methods**, idempotency, compatibility contracts.
- Simulation/worlds prefer **entity/component sets**, ticks, determinism, and cross-cutting relationships.
- Security prefers **explicit policy**: authorization, redaction, audit obligations.
- Observability prefers **metrics/logs/traces** with correlation IDs and sampling declarations.
- Declarative systems prefer **desired vs observed state** with reconciliation semantics.
- Agents prefer **sessions/actions/observations** rather than DOM/RPC alone.

A profile specification typically includes:
- vocabulary: entity types + relation kinds,
- topology constraints,
- required operations and events,
- ordering + determinism guarantees,
- security requirements,
- conformance levels.

This guide describes the *recommended* profiles to standardize first.

---

## 2. Recommended Profile Set (Baseline)

### Cross-cutting (strongly recommended)
1) **OmniPolicy Profile** (`ogif.profile:omnipolicy-0`) — Permissions, guardrails, redaction, audit (security plane)  
2) **OmniTelemetry Profile** (`ogif.profile:omnitel-0`) — Metrics, logs, traces, correlation (observation plane)  
3) **OmniTime Extension** (`ogif.ext:timecontrol-0`) — Deterministic logical time (freeze/advance/step) (test plane)

### Core interface paradigms
4) **OmniDOM Profile** (`ogif.profile:omnidom-1`) — Multimodal interaction tree (GUI/TUI/audio overlay)  
5) **OmniRPC Profile** (`ogif.profile:omnirpc-0`) — Service/resource interfaces (method calls + watches)  
6) **OmniFlow Profile** (`ogif.profile:omniflow-0`) — Dataflow DAG / pipelines / streaming graphs  
7) **OmniECS Profile** (`ogif.profile:omniecs-0`) — World/simulation modeling (entities/components/systems) *(when applicable)*

### Recommended when you have declarative control loops
8) **OmniState Profile** (`ogif.profile:omnistate-0`) — Desired/observed state, drift, reconciliation controllers

### Recommended when you have agentic / AI orchestration
9) **OmniAgent Profile** (`ogif.profile:omniagent-0`) — Agent sessions, goals, tool actions, observations, safety interventions

### Recommended optional (common in games/media)
10) **OmniRenderDiag Profile** (`ogif.profile:omnirenderdiag-0`) — Render diagnostics for 2D/3D engines without pixel tests

Each profile can coexist in the same endpoint. Cross-links use OGIF core relations like `ogif:facetOf` and `ogif:represents`.

---

## 3. Composition Pattern

A robust multi-paradigm deployment typically has:

- **Canonical domain** (e.g., `world://` ECS entities)
- **Facets** for subsystems:
  - `render://` objects, `physics://` bodies, `audio://` emitters
  - linked with `ogif:facetOf` to the canonical entity
- **UI domain** (`ui://`) representing and controlling canonical entities via `ogif:represents`

Avoid forcing everything into one tree. Trees exist where natural (UI, skeletons, some transforms) while graphs handle cross-links and many-to-many relations.

In addition, most production deployments SHOULD treat the following as first-class planes:

- **Security plane (OmniPolicy):** define user-equivalent vs privileged surfaces, enforce redaction, and audit control operations.
- **Observation plane (OmniTelemetry):** emit metrics/logs/traces with `correlationId`/`traceId` so operators and tests can verify behavior without scraping.
- **Declarative plane (OmniState):** when the system is controller-driven ("make it so"), prefer desired/observed/reconcile instead of scripting imperative sequences.
- **Agent plane (OmniAgent):** represent agent runs as sessions of actions/observations, and link tool use to OmniRPC.

---

## 4. What “Conformance” Means for Profiles

Profiles SHOULD define at least two conformance tiers:

- **Read Conformance**: graph + query + subscribe with profile vocabulary
- **Control Conformance**: required operations that allow external control (subject to authorization)
- (Optional) **Deterministic/Test Conformance**: stable IDs, controlled time, deterministic event ordering
- (Optional) **Audit Conformance**: structured decision/audit events (often via OmniPolicy + OmniTelemetry)

---

End of guide.

```markdown
# OmniPolicy Profile Overview
## OGIF Profile: `ogif.profile:omnipolicy-0`

**Document Type:** Informative overview (non-normative; draft normative spec available)  
**Profile ID:** `ogif.profile:omnipolicy-0`  
**Paradigm:** Authorization + guardrails (RBAC/ABAC hybrid)  
**Use Cases:** Least-privilege enforcement across OGIF read/query/invoke/subscribe; redaction; auditing; anti-cheat; AI tool sandboxing

---

## 1. What OmniPolicy Is For

OmniPolicy standardizes **who can do what** in an OGIF endpoint:

- **Read surface:** which entities/relations are visible, at what disclosure level.
- **Control surface:** which operations can be invoked and under what argument constraints.
- **Subscription surface:** which event types can be subscribed to, with what rate limits and redaction.
- **Obligations:** redaction, filtering, quotas, and audit requirements.

OmniPolicy exists so every profile (OmniDOM/Flow/RPC/ECS/RenderDiag/Agent/State/Time) does not reinvent authorization rules.

---

## 2. Core Ideas

- **Default deny** unless explicitly allowed.
- **Actions** are standardized identifiers (e.g., `ogif.action:invoke`, `dom.action:dispatch`, `rpc.action:call`).
- **Targets** are matched by entity selectors, opId patterns, event type patterns.
- **Rules** can impose **constraints** (ranges, allowlists, JSON Schema) rather than just allow/deny.
- **Obligations** enforce **redaction** and **limits** even when allowed.

---

## 3. Where It Fits

OmniPolicy is the “security plane” that gates:
- UI automation (user-equivalent vs privileged),
- tool use and agent orchestration,
- pipeline rewiring and test injection,
- ECS mutation and time control,
- render diagnostics (anti-wallhack).

---

End of overview.
```

```markdown
# OmniTelemetry Profile Overview
## OGIF Profile: `ogif.profile:omnitel-0`

**Document Type:** Informative overview (non-normative; draft normative spec available)  
**Profile ID:** `ogif.profile:omnitel-0`  
**Paradigm:** Observability plane (metrics + logs + traces)  
**Use Cases:** Production monitoring, regression testing, support tooling, audit trails, correlation across profiles

---

## 1. What OmniTelemetry Is For

OmniTelemetry standardizes *observation*, not control:

- metrics (counters, gauges, histograms),
- logs (structured records),
- traces (trace + span graphs),
- correlation IDs (`correlationId`, `traceId`, `spanId`).

Telemetry may be sampled and lossy; it must declare sampling/loss.

---

## 2. How It Differs From OmniDOM Input

- OmniDOM input is **causal** and can change state (control plane).
- OmniTelemetry is **derivative** and must not be required for correctness (observation plane).

---

## 3. Security

Telemetry can leak secrets. Deployments SHOULD:
- apply OmniPolicy to logs/traces,
- redact sensitive fields,
- rate-limit subscriptions and large queries.

---

End of overview.
```

```markdown
# OmniTime Extension Overview
## OGIF Extension: `ogif.ext:timecontrol-0`

**Document Type:** Informative overview (non-normative; draft normative spec available)  
**Extension ID:** `ogif.ext:timecontrol-0`  
**Paradigm:** Deterministic logical time (freeze/advance/step)  
**Use Cases:** UI animation-gated logic tests, simulation stepping, reproducible render frames, deterministic CI

---

## 1. What OmniTime Is For

OmniTime exposes one or more logical clocks (`time.clock`) so tools can:
- freeze time,
- advance time by a delta,
- step ticks/frames deterministically,
- resume.

This makes “sleep-based tests” unnecessary and improves reproducibility.

---

## 2. Integration Pattern

A clock typically controls a subsystem root via `time:controls`:
- `time://clock/ui-main → ui://root` (OmniDOM)
- `time://clock/world-main → ecs://world/main` (OmniECS)
- `time://clock/render-main → render://scene/main` (RenderDiag)

All time control operations MUST be strongly authorization-gated (usually via OmniPolicy).

---

End of overview.
```

```markdown
# OmniState Profile Overview
## OGIF Profile: `ogif.profile:omnistate-0`

**Document Type:** Informative overview (non-normative; draft normative spec available)  
**Profile ID:** `ogif.profile:omnistate-0`  
**Paradigm:** Declarative control loop (desired vs observed)  
**Use Cases:** Deployments, configuration controllers, feature-flag rollouts, autoscaling, orchestration, convergent systems

---

## 1. What OmniState Is For

OmniState models systems where you don't “call methods in order”, you declare intent:

- **Desired state**: what should be true.
- **Observed state**: what is currently true.
- **Controllers**: reconcile observed → desired.
- **Drift**: the difference between desired and observed.

This is the natural interface for Kubernetes-like reconciliation systems.

---

## 2. Why It Matters

Without OmniState, declarative systems get forced into imperative RPC scripts, losing:
- drift detection,
- convergence status,
- idempotent apply semantics.

---

End of overview.
```

```markdown
# OmniAgent Profile Overview
## OGIF Profile: `ogif.profile:omniagent-0`

**Document Type:** Informative overview (non-normative; draft normative spec available)  
**Profile ID:** `ogif.profile:omniagent-0`  
**Paradigm:** Agent loop (sessions → actions → observations)  
**Use Cases:** AI agents, autonomous automation, tool-orchestrated assistants, multi-agent workflows

---

## 1. What OmniAgent Is For

OmniAgent represents an agent run as:
- sessions (stateful runs),
- goals and context items,
- actions (often tool calls),
- observations (tool results / environment feedback),
- outputs and artifacts,
- safety interventions.

It standardizes an **observable decision record** without requiring exposure of internal reasoning.

---

## 2. Tool Use

Tool calls are best modeled via OmniRPC:
- `agent.action --agent:usesTool--> rpc.method`

OmniAgent supports:
- **integrated** tool calls (agent executes),
- **delegated** tool calls (agent requests; orchestrator executes and submits observation).

---

## 3. Safety

OmniAgent should almost always be deployed with OmniPolicy to enforce:
- tool allowlists,
- argument constraints,
- redaction of sensitive context/tool outputs,
- audit requirements.

---

End of overview.
```

```markdown
# OmniDOM Profile Overview
## OGIF Profile: `ogif.profile:omnidom-1`

**Document Type:** Informative overview (informative; draft normative spec available)  
**Profile ID:** `ogif.profile:omnidom-1`  
**Paradigm:** Interaction Tree (DOM-like)  
**Use Cases:** GUI, TUI, audio-first UI, assistive tech, UI automation, game overlays

---

## 1. What OmniDOM Is For

OmniDOM provides a **user-equivalent interaction surface**:

- a semantic tree of interaction nodes (not pixels),
- stable identity, roles, capabilities, state,
- semantic events and routing (capture → target → bubble),
- stimulus integrity (audio/visual feedback mirrored in semantics),
- testability without CV/screen scraping/waveform inspection.

It is ideal for:
- menu systems, HUD overlays, configuration panels,
- interactive flows with focus, dialogs, and safeguards,
- accessibility and automation.

It is not meant to represent:
- simulation worlds,
- streaming pipelines,
- RPC service contracts.

Those are separate profiles.

---

## 2. Topology and Relations

**Topology constraint:** strict **tree** (one root, no cycles, exactly one parent per non-root).

**Primary relation kind:**
- `dom:parentOf` (directed)

Optional supporting relations:
- `dom:labelFor` (label node → control node)
- `dom:describedBy` (help text → target node)

Cross-profile relations:
- `ogif:represents` (UI node represents world entity/component)
- `ogif:facetOf` (rare for UI; usually UI represents other domains)

---

## 3. Entity Types and Roles (Concept)

OmniDOM typically models:
- `dom.node` (base)
- `dom.screen`, `dom.dialog`, `dom.container`
- `dom.action`, `dom.input`, `dom.toggle`
- `dom.choiceGroup`, `dom.choice`, `dom.list`, `dom.table`
- `dom.notification`, `dom.progress`, `dom.media`, `dom.prompt`

Each node has:
- `role` (semantic classification)
- `capabilities` (activatable/editable/focusable/etc.)
- `state` (enabled/visible/focused/value/error/busy/etc.)

---

## 4. Event Model

Core semantic events:
- Focus/navigation: `FocusRequest`, `FocusChanged`, `Navigate`
- Activation: `Activate`, `Submit`, `Cancel`, `Dismiss`
- Value/selection: `SetValue`, `ValueChanged`, `Toggle`, `SetSelection`, `SelectionChanged`
- Announcements: `Announce`, `Cue`
- Lifecycle: `ScreenEnter`, `ScreenExit`, `DialogOpened`, `DialogClosed`

**Routing:** capture → target → bubble along `dom:parentOf` path.  
**Cancelation:** `defaultPrevented`, `propagationStopped` semantics.

This is what makes UI safeguards testable:
- containers can intercept events,
- dialogs can trap focus,
- global handlers can prevent unsafe actions.

---

## 5. Stimulus Integrity (Critical)

OmniDOM includes strict rules that anything user-relevant shown/heard MUST be reflected in:
- node state changes, and/or
- tree changes, and/or
- semantic events (`Announce`, `Cue`, `notification` nodes).

This is what allows automation to “perceive” UI feedback without pixels/audio decoding.

(Your earlier addendum becomes part of the OmniDOM profile’s normative requirements.)

---

## 6. Operations (What Clients Do)

Typical operations:
- `dom.getTree`, `dom.query`, `dom.getNode`
- `dom.dispatch` (inject semantic events)
- `dom.subscribe` (events + state changes)
- `dom.waitFor` (selector + predicate)

These can be implemented on top of OGIF core operations:
- `ogif.getGraph`, `ogif.queryEntities`, `ogif.subscribe`
- plus profile-specific event dispatch semantics.

---

## 7. Determinism

OmniDOM is strongest when it supports:
- stable IDs or stable `testTag`,
- deterministic focus order,
- optional time control for animation-gated logic,
- explicit state changes for “busy/loading/disabled”.

---

## 8. Security Expectations

OmniDOM is typically a **user-equivalent** surface:
- it should not expose privileged internal operations,
- it should respect permissions exactly like a real user session,
- it should redact sensitive values.

---

## 9. Where OmniDOM Fits in a 3D Game

- HUD/menu overlay: OmniDOM nodes (tree)
- UI node `ogif:represents` a canonical world entity or component
- OmniDOM dispatch triggers safe gameplay operations through the game’s rules
- Visual/audio flair is mirrored by `Announce`/`Cue`/state

---

End of overview.
```

```markdown
# OmniFlow Profile Overview
## OGIF Profile: `ogif.profile:omniflow-0`

**Document Type:** Informative overview (informative; draft normative spec available)  
**Profile ID:** `ogif.profile:omniflow-0`  
**Paradigm:** Dataflow / streaming DAG  
**Use Cases:** Unix-like pipelines, ETL graphs, media processing graphs, reactive streams

---

## 1. What OmniFlow Is For

OmniFlow models systems where “interaction” is not clicking buttons but:
- **connecting producers and consumers**, and
- **moving typed data through a graph** with:
  - backpressure,
  - buffering,
  - lifecycle control,
  - and observable health.

It is ideal for:
- pipeline orchestration,
- module-to-module composability,
- monitoring and testing streaming behavior without ad hoc logs.

---

## 2. Topology and Relations

**Topology constraint:** directed graph; usually a DAG (profile may allow cycles when explicitly supported).

Key relation kinds:
- `flow:hasPort` (module → port)
- `flow:connectsTo` (outputPort → inputPort)
- `flow:dependsOn` (module → module) (optional)
- `flow:contains` (pipeline → module)

Port direction:
- `attributes.direction = "in" | "out"`

---

## 3. Entity Types (Concept)

Typical entities:
- `flow.pipeline`
- `flow.module`
- `flow.port`
- `flow.stream` (optional explicit entity)
- `flow.schema` (optional; or via `schemaRef`)

---

## 4. Core Capabilities

Common capabilities:
- `flow.cap:startable`, `flow.cap:stoppable`, `flow.cap:pausable`
- `flow.cap:connectable`, `flow.cap:reconfigurable`
- `flow.cap:observableThroughput`, `flow.cap:observableBackpressure`

---

## 5. Operations (What Clients Do)

Lifecycle:
- `flow.start(pipeline|module)`
- `flow.stop(...)`
- `flow.pause(...)`, `flow.resume(...)`

Graph editing:
- `flow.connect(outPort, inPort)`
- `flow.disconnect(outPort, inPort)`

Configuration:
- `flow.setConfig(module, patch)` (with schemaRef)

Testing:
- `flow.test.inject(port, data)` (test-only, capability-gated)
- `flow.test.drain(port, maxItems)` (test-only, capability-gated)

---

## 6. Events and Semantics

Data and control events (conceptual):
- `flow.event:Data` (record/batch)
- `flow.event:Error`
- `flow.event:Closed`
- `flow.event:Backpressure`
- `flow.event:Watermark` (optional)
- `flow.event:Stats` (throughput, latency)

**Ordering:** data events MUST be ordered per stream/connection.  
**Reliability:** profile should declare delivery semantics (best-effort vs at-least-once).

**Backpressure:** profile MUST specify how a producer learns a consumer is slow:
- explicit `Backpressure` events and/or
- flow control fields in stats.

---

## 7. Schemas and Framing

OmniFlow must be explicit about data encoding:
- NDJSON (newline-delimited JSON) is practical for pipes
- MessagePack / Protobuf for efficiency
- Arrow for columnar batches

A profile spec should standardize:
- framing for stream events,
- schema references (`schemaRef`),
- and error record formats.

---

## 8. Mapping to Unix Pipelines

A Unix pipeline is often:
- modules connected by stdout→stdin

OmniFlow makes it inspectable and controllable:
- each process is a `flow.module`
- stdin/stdout are `flow.port`
- pipe connections are `flow:connectsTo`

This enables:
- “show me the pipeline graph”
- “disconnect grep and reconnect to awk”
- “measure throughput and backpressure”
- deterministic integration tests by injecting records

---

## 9. Security Expectations

OmniFlow can expose powerful internals; it MUST:
- restrict graph editing and injection to authorized clients,
- separate observation from control when needed,
- prevent injection into production pipelines unless explicitly allowed.

---

End of overview.
```

```markdown
# OmniRPC Profile Overview
## OGIF Profile: `ogif.profile:omnirpc-0`

**Document Type:** Informative overview (informative; draft normative spec available)  
**Profile ID:** `ogif.profile:omnirpc-0`  
**Paradigm:** Service/resource interface (RPC, REST-like resources, watches)  
**Use Cases:** Microservices, module APIs, networked systems, internal plugin boundaries

---

## 1. What OmniRPC Is For

OmniRPC models systems where the natural interface is:
- request/response method calls,
- plus subscription/watches for change streams.

It is best for:
- program-to-program integration,
- module boundaries,
- internet RPCs (when paired with concrete auth/transport).

---

## 2. Topology and Relations

OmniRPC does not require a tree or DAG. Common relations:

- `rpc:exposes` (service → method)
- `rpc:owns` (service → resource)
- `rpc:hasVersion` (service → version entity)
- `rpc:dependsOn` (service → service) (observational)
- `rpc:implements` (service → interface descriptor)

---

## 3. Entity Types (Concept)

- `rpc.service`
- `rpc.method`
- `rpc.resource`
- `rpc.schema` / `rpc.interface` (optional)
- `rpc.errorType` (optional)

---

## 4. Operations

Typical operations:
- `rpc.call(methodId, params)` → result or error
- `rpc.watch(resourceSelector, options)` → stream of change events
- `rpc.describe(serviceId)` → schema + compatibility info
- `rpc.health(serviceId)` → liveness/readiness semantics (optional but common)

Key method descriptor fields (recommended):
- input/output schema refs,
- idempotency (`idempotent` vs `non_idempotent`),
- retry policy hints,
- authentication requirements.

---

## 5. Events

- `rpc.event:RequestReceived` (optional; often sensitive)
- `rpc.event:RequestCompleted` (optional; useful for tracing)
- `rpc.event:ResourceChanged` (watch streams)
- `rpc.event:Error`

**Correlation:** request IDs and correlation IDs are crucial here.

---

## 6. Compatibility and Versioning (Core Value)

OmniRPC profile specs should define:
- how versioning is expressed (semantic versioning recommended),
- compatibility guarantees,
- deprecation signaling,
- schema evolution rules.

This is where OmniRPC differs from OmniDOM:
- UI automation tolerates minor changes;
- RPC integrations require explicit compatibility contracts.

---

## 7. Security Expectations

OmniRPC often crosses trust boundaries; it MUST include:
- clear authentication hooks,
- authorization per method/resource,
- redaction rules for sensitive fields,
- audit-friendly event emission.

A safe pattern:
- expose descriptions broadly,
- restrict calls,
- restrict request/response logging.

---

## 8. Relationship to OGIF Core

OmniRPC uses OGIF as a universal introspection layer:
- discover services/methods/resources as entities,
- call operations via `ogif.invoke` (or a profile-specific `rpc.call` op),
- subscribe to `rpc.event:*` events via `ogif.subscribe`.

---

End of overview.
```

```markdown
# OmniECS Profile Overview
## OGIF Profile: `ogif.profile:omniecs-0`

**Document Type:** Informative overview (informative; draft normative spec available)  
**Profile ID:** `ogif.profile:omniecs-0`  
**Paradigm:** World/simulation (Entity-Component-System)  
**Use Cases:** 3D videogames, robotics, simulations, digital twins

---

## 1. What OmniECS Is For

OmniECS models systems where the primary structure is:
- a **set of entities**,
- each with **components** (data),
- processed by **systems** in ticks/frames.

This is a better fit than DOM for 3D worlds because:
- relationships are many-to-many,
- subsystems overlap (physics/render/audio/AI),
- “ownership” is not inherently hierarchical.

OmniECS aims to make world state:
- inspectable,
- controllable (with safeguards),
- testable deterministically.

---

## 2. Topology and Relations

No global topology constraint (not a tree). Core relations:

- `ecs:hasComponent` (entity → component)
- `ecs:processedBy` (system → entity) (optional / observational)
- `ecs:references` (component → entity) (for links like target, parent, owner)
- `ecs:inWorld` (entity → world root)
- `ecs:memberOf` (entity → archetype) (optional)

Cross-subsystem:
- `ogif:facetOf` for physics/render/audio facets belonging to canonical ECS entities
- `ogif:represents` for UI overlay reflecting ECS entity state

---

## 3. Entity Types (Concept)

- `ecs.world`
- `ecs.entity`
- `ecs.component` (typed by schemaRef)
- `ecs.system`
- `ecs.archetype` (optional)
- `ecs.eventStream` (optional explicit event entities)

---

## 4. Capabilities

Common capabilities:
- `ecs.cap:spawnable`, `ecs.cap:despawnable`
- `ecs.cap:componentReadable`, `ecs.cap:componentWritable`
- `ecs.cap:tickControllable` (test mode)
- `ecs.cap:telemetryObservable`

Important: **capabilities are the safety boundary**:
- observers can read,
- authorized clients can mutate,
- test harness may get extra powers under explicit “test mode”.

---

## 5. Operations

Core operations (conceptual):
- `ecs.spawn(type, initialComponents)`
- `ecs.despawn(entityId)`
- `ecs.addComponent(entityId, componentType, value)`
- `ecs.removeComponent(entityId, componentType)`
- `ecs.patchComponent(entityId, componentType, patch)`
- `ecs.query(archetypeSelector)` (entities with component set)

Determinism/test (recommended):
- `ecs.stepTicks(n)` or `ecs.step(dt)` in test mode
- `ecs.setSeed(seed)` for randomness control
- `ecs.freezeTime()` / `ecs.advanceTime()` if time-based

---

## 6. Events

Simulation events:
- `ecs.event:TickStarted`, `ecs.event:TickEnded`
- `ecs.event:ComponentAdded`, `ecs.event:ComponentRemoved`, `ecs.event:ComponentChanged`
- `ecs.event:EntitySpawned`, `ecs.event:EntityDespawned`
- Domain events:
  - `ecs.event:CollisionBegan`, `ecs.event:CollisionEnded`
  - `ecs.event:DamageApplied`, `ecs.event:QuestUpdated` (game-specific)

Ordering:
- events SHOULD be ordered per tick/frame,
- profile spec should define whether cross-system event ordering is stable.

---

## 7. Why Trees Feel Artificial in Games (and How OmniECS Avoids It)

In a game, the same object participates in many graphs simultaneously:
- physics constraints
- rendering visibility sets
- audio emitter graphs
- AI target graphs
- inventory containment graphs

OmniECS avoids forcing these into a single tree by:
- using typed relations and facets,
- keeping a canonical entity ID,
- letting each subsystem expose its own graph while linking back.

---

## 8. Example: Player Entity with Facets

Canonical:
- `world://entity/Player/42` (ecs.entity)

Facets:
- `physics://body/abc123 --ogif:facetOf--> world://entity/Player/42`
- `render://object/42 --ogif:facetOf--> world://entity/Player/42`
- `audio://emitter/77 --ogif:facetOf--> world://entity/Player/42`

UI:
- `ui://hud#healthBar --ogif:represents--> world://entity/Player/42`

---

## 9. Security Expectations

OmniECS can expose powerful mutation surfaces. A safe design:
- Production: read-only or tightly scoped control
- Test/Dev: expanded control behind explicit mode and strong auth
- Never allow “teleport/kill/spawn” operations without clear capability gating and audit.

---

End of overview.
```

```markdown
# OmniRenderDiag Profile Overview
## OGIF Profile: `ogif.profile:omnirenderdiag-0` (Optional, Recommended for Games/Engines)

**Document Type:** Informative overview (informative; draft normative spec available)  
**Profile ID:** `ogif.profile:omnirenderdiag-0`  
**Paradigm:** Render diagnostics without pixel tests  
**Use Cases:** OpenGL/Vulkan/3D engines, video overlays, advanced HUDs

---

## 1. What OmniRenderDiag Is For

Some regressions are “visual correctness” issues. Pure UI semantics won’t catch them, but pixel tests are brittle.

OmniRenderDiag provides a middle ground:
- expose **stable render facts** strongly correlated with visual output,
- without requiring screenshot comparison.

Examples of “render facts”:
- object visible set membership,
- object picking hit results,
- camera pose/projection,
- projected bounds for semantic objects,
- animation pose hash / skeleton state hash,
- render-pass identifiers.

---

## 2. Topology and Relations

Entities:
- `render.scene`, `render.object`, `render.camera`, `render.pass` (concept)
Relations:
- `render:inScene` (object → scene)
- `render:usesCamera` (scene → camera)
- `render:drawnInPass` (object → pass)

Cross-link:
- `render.object --ogif:facetOf--> world.entity` (canonical ECS entity)

---

## 3. Operations (Examples)

- `render.pick(x, y, space)` → object/entity id hit
- `render.getVisibleSet(selector)` → list of rendered objects
- `render.getBounds2D(objectId)` → normalized projected rect
- `render.getCamera()` → matrices/pose
- `render.getFrameInfo()` → frame counters and pass IDs

---

## 4. Events

- `render.event:FrameRendered`
- `render.event:VisibleSetChanged`
- `render.event:ObjectPicked` (optional)
- `render.event:PassStats` (optional)

---

## 5. How It Works With OmniDOM

- OmniDOM tests interaction/safeguards (what a user can do and what they’re told).
- RenderDiag tests renderer correctness facts (what is actually drawn/visible).

Both can exist in the same OGIF endpoint without conflict.

---

## 6. Security

Render diagnostics can leak sensitive scene info (e.g., hidden objects, wallhacks).  
Production builds SHOULD restrict:
- visibility sets,
- picking,
- detailed bounds,
to authorized tooling only.

---

End of overview.
```
