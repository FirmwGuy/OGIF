# OmniECS Profile Specification
## OGIF Profile: Entity–Component–System Worlds, Ticks, Determinism, and Cross-Subsystem Facets

**Profile Name:** OmniECS  
**OGIF Profile ID:** `ogif.profile:omniecs-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Selector Baseline:** `ogif-sel-0` + OmniECS Selector Extension `ecs-sel-0` (defined herein)

---

## 1. Purpose

OmniECS is an OGIF profile for representing and controlling **simulation “worlds”** and **game-like state** using an Entity–Component–System (ECS) paradigm.

It models:
- **worlds** (simulation contexts),
- **entities** (identities),
- **components** (typed state attached to entities),
- **systems** (processors that update components each tick/frame),

and provides:
- deterministic inspection and testing hooks,
- controlled mutation operations with safety/authorization,
- structured events for simulation steps and state changes,
- cross-subsystem integration using OGIF core relations (`ogif:facetOf`, `ogif:represents`).

OmniECS is designed for cases where forcing a single tree is artificial (3D games, robotics, simulators). It preserves interconnectedness by using a **typed graph** rather than a hierarchy.

---

## 2. Design Goals

An OmniECS implementation MUST allow a client to:

1. **Discover**: enumerate worlds, entities, components, and systems.
2. **Inspect**: read component state with stable addressing and schema references.
3. **Observe**: subscribe to entity/component lifecycle changes and tick boundaries.
4. **Control (optional)**: spawn/despawn entities and mutate components with safeguards.
5. **Test deterministically (recommended)**: step ticks with stable time and seeded randomness.
6. **Link subsystems**: connect physics/render/audio/AI facets to canonical ECS entities without forcing a single tree.

---

## 3. Non-goals

OmniECS does NOT standardize:
- rendering/scene graph details (use OmniRenderDiag profile if needed),
- dataflow/backpressure semantics (use OmniFlow),
- service/RPC contracts (use OmniRPC),
- UI interaction trees (use OmniDOM).

OmniECS may coexist with those profiles via OGIF.

---

## 4. Relationship to OGIF Core

OmniECS uses OGIF constructs:

- OmniECS entities are OGIF **entities** with `type` in the `ecs.*` namespace.
- Attachments and membership are OGIF **relations** with kinds `ecs:*`.
- Control is via OGIF **operations** (`ogif.invoke`) and/or profile wrapper methods.
- Observability uses OGIF **events** and subscriptions, with OmniECS-specific event types `ecs.event:*` plus OGIF patch events.

Implementations MUST advertise `ogif.profile:omniecs-0` via `ogif.getVersion`.

---

## 5. Entity Types

OmniECS defines reserved OGIF entity `type` values.

### 5.1 Required Types

An OmniECS endpoint MUST represent at least:

- `ecs.world` — simulation context root
- `ecs.entity` — ECS entity identity (no required internal structure)
- `ecs.component` — typed component instance attached to an entity
- `ecs.system` — system processor (physics, AI, combat, etc.)

### 5.2 Optional Types (Recommended)

- `ecs.archetype` — a canonical grouping by component set
- `ecs.eventStream` — explicit event stream entity (if events are partitioned)
- `ecs.tag` — tag-like components without state (optional representation)

---

## 6. Relation Kinds and Structural Constraints

OmniECS does not impose a global topology (not a tree). It does impose constraints for entity membership and component attachment.

### 6.1 Reserved Relation Kinds

All are directed:

- `ecs:inWorld` (entity ? world)  
  Entity belongs to a world.

- `ecs:hasComponent` (entity ? component)  
  Entity has a component instance.

- `ecs:processedBy` (entity ? system) (optional; informational)  
  Entity is processed by a system (dynamic membership; may be omitted).

- `ecs:references` (component ? entity) (optional)  
  Component contains a reference to another entity (e.g., target, owner, parent).

- `ecs:memberOf` (entity ? archetype) (optional)  
  Entity is in an archetype grouping.

Custom relation kinds MUST be namespaced (e.g., `mygame.ecs:inSquad`).

### 6.2 World Membership Constraint (MUST)

Every `ecs.entity` MUST have exactly **one** outgoing `ecs:inWorld` relation to an `ecs.world`.

If an entity is moved between worlds, it MUST be observable via:
- a relation change (graph patch) and/or
- `ecs.event:EntityMovedWorld` (optional).

### 6.3 Component Attachment Constraint (MUST)

Every `ecs.component` MUST have exactly **one** incoming `ecs:hasComponent` relation from an `ecs.entity`.

A component instance MUST NOT be attached to multiple entities simultaneously.

---

## 7. Component Model

### 7.1 Component Type Identity (MUST)

Every `ecs.component` MUST declare its component type:

- `attributes.componentType` (string)

Component type strings SHOULD be stable and namespaced if necessary:
- `Transform`, `Health`, `Inventory`
- `mygame.comp:CombatStats`

### 7.2 Schema References (SHOULD)

Components SHOULD declare:

- `attributes.schemaRef` (URI identifying the component’s data schema)

Example:
```json
{
  "id": "ecs://world/main/entity/Player42/component/Health",
  "type": "ecs.component",
  "name": "Health",
  "attributes": {
    "componentType": "Health",
    "schemaRef": "schema://mygame/Health@v2"
  },
  "state": { "current": 95, "max": 100 }
}
```

### 7.3 Component State Location (MUST)

Component data MUST be stored in the component entity’s `state` object.

* The state MUST be patchable (RFC 6902 JSON Patch RECOMMENDED).
* If the component data is too large to include, the endpoint MAY provide:

  * `state.dataRef` (URI) and/or
  * paged retrieval operations (profile extension).

### 7.4 Tag Components (Optional)

A tag component MAY be represented as an `ecs.component` with:

* `state = {}` (empty), and
* `attributes.isTag = true`.

---

## 8. World and Tick Model

### 8.1 World State (RECOMMENDED)

`ecs.world` SHOULD expose:

* `state.tick` (integer; monotonically increasing)
* `state.time` (number; seconds or milliseconds; declare unit)
* `attributes.timeUnit` (e.g., `"seconds"`, `"ms"`)
* `attributes.tickRate` (number; nominal)

### 8.2 Tick Semantics (Profile Assumption)

OmniECS assumes systems update state in discrete ticks/frames for determinism.

If a system is continuous-time, it SHOULD still expose:

* a logical tick counter for observability, or
* a time-stepped “observation tick” in test mode.

---

## 9. Systems Model

### 9.1 System Identity (MUST)

Each `ecs.system` MUST have:

* stable id
* `name` (SHOULD)

Systems SHOULD declare:

* `attributes.phase` (e.g., `"input"|"ai"|"physics"|"animation"|"renderPrep"|"audio"`)
* `attributes.order` (integer; recommended ordering within a phase)

### 9.2 System State (Optional)

Systems MAY expose:

* `state.enabled` (boolean)
* `state.lastTickDurationMs`
* `state.error`

System control operations are optional and security-sensitive.

---

## 10. Events

OmniECS event types MUST be prefixed `ecs.event:` and use OGIF event envelopes.

### 10.1 Required Events (Observable State)

An OmniECS endpoint MUST provide enough information to observe entity/component lifecycle changes. This MAY be satisfied via OGIF patch events alone, but OmniECS-specific events are strongly recommended.

For **OmniECS-Read Conformance**, the endpoint MUST emit at least one of:

* `ecs.event:EntitySpawned` / `ecs.event:EntityDespawned` / `ecs.event:ComponentAdded` / `ecs.event:ComponentRemoved` / `ecs.event:ComponentChanged`, OR
* OGIF patch events that clearly represent the same facts:

  * `ogif.event:GraphChanged` / `EntityChanged` / `StateChanged`.

For interoperability, OmniECS endpoints claiming Read Conformance SHOULD emit the OmniECS-specific events listed below.

### 10.2 Recommended Core Events

* `ecs.event:TickStarted`
* `ecs.event:TickEnded`
* `ecs.event:EntitySpawned`
* `ecs.event:EntityDespawned`
* `ecs.event:ComponentAdded`
* `ecs.event:ComponentRemoved`
* `ecs.event:ComponentChanged`

### 10.3 Optional Domain Events

Profiles/extensions or applications MAY define:

* `ecs.event:CollisionBegan`, `ecs.event:CollisionEnded`
* `ecs.event:TriggerEntered`, `ecs.event:TriggerExited`
* `ecs.event:DamageApplied`
* `ecs.event:QuestUpdated`

Custom events MUST be namespaced if not reserved.

### 10.4 Payload Requirements (Recommended)

#### 10.4.1 EntitySpawned

```json
{
  "type": "ecs.event:EntitySpawned",
  "source": "ecs://world/main",
  "data": {
    "entityId": "ecs://world/main/entity/Player42",
    "archetype": ["Transform", "Health"],
    "reason": "spawn"
  }
}
```

#### 10.4.2 ComponentChanged

```json
{
  "type": "ecs.event:ComponentChanged",
  "source": "ecs://world/main/entity/Player42/component/Health",
  "data": {
    "entityId": "ecs://world/main/entity/Player42",
    "componentType": "Health",
    "patch": [
      { "op": "replace", "path": "/current", "value": 90 }
    ],
    "revision": "rev-1050"
  }
}
```

#### 10.4.3 TickEnded

```json
{
  "type": "ecs.event:TickEnded",
  "source": "ecs://world/main",
  "data": { "tick": 12345, "dt": 0.0166667 }
}
```

---

## 11. Operations

OmniECS defines standard operations. Implementations MAY expose them as OGIF operations (invoked via `ogif.invoke`) and/or as wrapper methods.

### 11.1 Reserved Capabilities (for Gating)

OmniECS reserves these capability tokens:

* `ecs.cap:inspectable`
* `ecs.cap:spawnable`
* `ecs.cap:despawnable`
* `ecs.cap:componentReadable`
* `ecs.cap:componentWritable`
* `ecs.cap:queryable`
* `ecs.cap:tickControllable` (test/determinism)
* `ecs.cap:seedControllable` (test/determinism)
* `ecs.cap:adminOnly` (marker; policy enforced elsewhere)

### 11.2 Core Control Operations (Optional; Required for Control Conformance)

If an endpoint claims **OmniECS-Control Conformance** (§16.2), it MUST support:

#### 11.2.1 `ecs.spawn`

Creates an entity with an initial set of components.

Recommended params:

* `worldId`
* `entityType` (string; optional classification)
* `components` (map: componentType ? initialState)
* `tags` (optional list)

Returns:

* `entityId`

#### 11.2.2 `ecs.despawn`

Removes an entity (and attached components) from the world.

Params:

* `entityId`

#### 11.2.3 `ecs.addComponent`

Params:

* `entityId`
* `componentType`
* `initialState` (optional)
* `schemaRef` (optional)

#### 11.2.4 `ecs.removeComponent`

Params:

* `entityId`
* `componentType` OR `componentId`

#### 11.2.5 `ecs.patchComponent`

Params:

* `componentId` OR `(entityId, componentType)`
* `patch` (RFC 6902 JSON Patch RECOMMENDED)

Endpoints MUST validate patches against schemas when available and MUST reject invalid mutations.

### 11.3 Query Operations (SHOULD)

OmniECS endpoints SHOULD support querying for entities by component set and predicates.

Recommended operation:

* `ecs.query({ worldId, withComponents[], withoutComponents[], where?, limit? }) -> entityIds[]`

Where:

* `withComponents` is a list of componentType strings.
* `where` is an optional predicate expression (deployment-defined; equality MUST exist at minimum).

### 11.4 Determinism and Time Control Operations (Optional, Recommended)

If an endpoint supports deterministic stepping, it MUST advertise:

* `features.ecsTime = "ecs-time-0"` in `ogif.getVersion`.

Recommended operations:

* `ecs.time.freeze({ worldId })`
* `ecs.time.stepTicks({ worldId, ticks })`
* `ecs.time.step({ worldId, dt })` (optional)
* `ecs.time.resume({ worldId })`

If random processes exist, the endpoint SHOULD support:

* `ecs.setSeed({ worldId, seed })`
  and advertise:
* `features.ecsSeed = "ecs-seed-0"`.

### 11.5 Suggested JSON-RPC Wrapper Names (Informative)

If using JSON-RPC, endpoints SHOULD expose:

* `ecs.spawn`, `ecs.despawn`, `ecs.addComponent`, `ecs.removeComponent`, `ecs.patchComponent`, `ecs.query`
* `ecs.time.freeze`, `ecs.time.stepTicks`, `ecs.time.resume`, `ecs.setSeed` (if supported)

All operations MUST still be expressible via OGIF operation descriptors and `ogif.invoke` for tool interoperability.

---

## 12. Safety and Validation Semantics

### 12.1 Preconditions (MUST)

Mutation operations MUST be rejected when:

* the entity/component does not exist,
* the client lacks authorization,
* schemas/predicates fail validation,
* the requested mutation violates world rules declared by the endpoint.

Endpoints SHOULD return structured rejection errors with stable codes (deployment-defined) and MUST surface failures via:

* operation error/return, and/or
* `ecs.event:Error` (optional), and/or
* OGIF state changes.

### 12.2 No “Cheat Surface” by Default (RECOMMENDED)

In production builds, endpoints SHOULD:

* disable or restrict spawn/despawn and tick control,
* restrict visibility of hidden entities/components,
* avoid exposing privileged debug operations unless explicitly authorized.

This prevents the introspection interface from becoming a gameplay exploit surface.

---

## 13. Facets and Cross-Subsystem Integration

OmniECS strongly recommends a **canonical identity** pattern:

* ECS entities (`ecs.entity`) act as canonical identities in `ecs://` or `world://`.
* Subsystems expose facets:

  * `physics://body/...`, `render://object/...`, `audio://emitter/...`
* Link facets to canonical ECS entities using OGIF core relation:

  * `ogif:facetOf` (facet ? ecs.entity)

UI overlay nodes (OmniDOM) typically link using:

* `ogif:represents` (ui node ? ecs.entity or ecs.component)

This preserves interconnectedness without forcing a single hierarchy.

Example relations:

* `physics://body/abc123 --ogif:facetOf--> ecs://world/main/entity/Player42`
* `ui://hud#healthBar --ogif:represents--> ecs://world/main/entity/Player42`

---

## 14. OmniECS Selectors (`ecs-sel-0`)

Endpoints MUST support `ogif-sel-0`. OmniECS additionally defines convenient selector forms.

### 14.1 Entity and Component Matching

* `world()` ? `type("ecs.world")`
* `entity()` ? `type("ecs.entity")`
* `system()` ? `type("ecs.system")`
* `component(type="Health")` ? `type("ecs.component") AND attr("componentType"=="Health")`

### 14.2 Component-Set Queries (Convenience)

Implementations SHOULD support:

* `with("A","B",...)` ? entities that have components of those types
* `without("A","B",...)` ? entities missing those components

These map to traversal:

* entity `out("ecs:hasComponent")` filtering by `attributes.componentType`.

Example:

* `entity() with("Transform","Health")`

### 14.3 Traversal Patterns

* `#<entityId> out("ecs:hasComponent")` ? component instances
* `#<componentId> in("ecs:hasComponent")` ? owning entity
* `#<entityId> out("ecs:inWorld")` ? world
* `#<componentId> out("ecs:references")` ? referenced entities (if used)

---

## 15. Security Considerations (Normative)

### 15.1 Least Privilege (MUST)

Endpoints MUST enforce authorization for:

* component writes,
* entity spawn/despawn,
* tick/time control,
* access to hidden/sensitive components.

### 15.2 Redaction and Visibility (SHOULD)

If an endpoint has hidden entities/components (fog-of-war, secret state), it SHOULD:

* restrict enumeration and query results accordingly,
* optionally mark visibility in attributes:

  * `attributes.visibility = "public" | "restricted" | "hidden"`

### 15.3 Event Leakage (MUST/SHOULD)

Event streams MUST NOT leak restricted state to unauthorized subscribers.
If an event would leak restricted state, the endpoint MUST either:

* not emit it to that subscriber, or
* redact its payload.

---

## 16. Conformance Levels

### 16.1 OmniECS-Read Conformance

An endpoint is OmniECS-Read conformant if it:

* exposes `ecs.world`, `ecs.entity`, `ecs.component`, `ecs.system` entities (as applicable),
* enforces `ecs:inWorld` and `ecs:hasComponent` constraints (§6.2–§6.3),
* allows querying entities/components via OGIF selectors (and ideally `ecs-sel-0`),
* emits observable lifecycle/state changes via OGIF patches and SHOULD emit core `ecs.event:*` events (§10).

### 16.2 OmniECS-Control Conformance

Includes OmniECS-Read and additionally:

* supports spawn/despawn and component mutation operations (§11.2),
* validates mutations against schemas/rules,
* emits appropriate events/patches reflecting changes.

### 16.3 OmniECS-Deterministic Conformance (Recommended for CI)

Includes OmniECS-Control and additionally:

* supports deterministic time/tick control (`ecs-time-0`) OR provides a documented deterministic stepping mechanism,
* supports seeded randomness control (`ecs-seed-0`) when randomness affects state,
* provides stable IDs or `meta.testTag` in test mode.

### 16.4 OmniECS-PhysicsEvents Conformance (Optional)

If collision/trigger semantics are exposed, the endpoint:

* emits `ecs.event:CollisionBegan/Ended` (or namespaced equivalents),
* includes stable entity IDs for participants,
* documents ordering relative to ticks (e.g., emitted during TickEnded).

---

## 17. Example (Informative)

### 17.1 Player Entity with Components and Facets

Entities:

* `ecs://world/main` (`ecs.world`)
* `ecs://world/main/entity/Player42` (`ecs.entity`)
* `ecs://world/main/entity/Player42/component/Transform` (`ecs.component`)
* `ecs://world/main/entity/Player42/component/Health` (`ecs.component`)
* `physics://body/abc123` (physics facet, separate domain)
* `render://object/42` (render facet, separate domain)

Relations:

* `Player42 ecs:inWorld main`
* `Player42 ecs:hasComponent Transform`
* `Player42 ecs:hasComponent Health`
* `physics://body/abc123 ogif:facetOf Player42`
* `render://object/42 ogif:facetOf Player42`

A UI element (OmniDOM):

* `ui://hud#healthBar ogif:represents Player42`

A deterministic test could:

1. freeze time,
2. step 10 ticks,
3. assert `Health.state.current` changed only under expected rules,
4. verify collision events occurred.

---

**End of OmniECS Profile Specification `ogif.profile:omniecs-0` (Draft)**
