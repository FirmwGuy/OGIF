# OmniGraphIF Specification
## A Transport-Agnostic Graph Interface for Introspection, Control, and Automation

**Specification Name:** OmniGraphIF  
**Short Name:** OGIF  
**Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21

---

## 1. Purpose

OmniGraphIF (OGIF) defines a **general meta-interface** for programs, subsystems, and modules by modeling them as a **typed graph** of entities connected by **typed relations**, with:

- **capabilities** (what can be done),
- **state** (what is true now),
- **operations** (how to act),
- **events** (how change is observed),
- **queries** (how things are located),
- **subscriptions** (how changes are streamed),
- and a **transport-agnostic** protocol surface.

OGIF is intended to support multiple paradigms under one umbrella without forcing a single topology (e.g., not everything must be a tree). Instead, OGIF supports **profiles** that define domain-specific semantics (e.g., UI trees, dataflow DAGs, RPC services, actor systems, ECS worlds).

---

## 2. Design Goals

An OGIF implementation MUST enable an external client (or another module) to:

1. **Discover**: enumerate entities and relations and inspect capabilities/state.
2. **Control**: invoke operations subject to policy and declared constraints.
3. **Observe**: subscribe to events and state/graph changes.
4. **Address**: locate entities and relations via stable identifiers and selectors.
5. **Compose**: relate multiple subsystems using explicit, typed edges rather than implicit coupling.

### 2.1 Non-goals

OGIF does NOT standardize:

- UI layout, rendering details, pixels, terminal bytes, audio waveforms.
- A single “one true” model for all programs (profiles exist because paradigms differ).
- A particular schema language (JSON Schema is RECOMMENDED; Protobuf/others MAY be used).
- Network authentication mechanisms (OGIF defines requirements and hooks; deployment chooses concrete auth).

---

## 3. Terminology and Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

- **Entity**: a uniquely identified node in the OGIF graph.
- **Relation** (Edge): a typed connection between two entities.
- **Graph Snapshot**: a point-in-time view of entities and relations.
- **Capability**: an advertised affordance; typically a prerequisite for certain operations.
- **Operation**: an invokable method with typed inputs/outputs.
- **Event**: an emitted signal about something that happened or changed.
- **Profile**: a named semantic package that constrains/extends OGIF core for a paradigm.
- **Domain/Namespace**: an identifier space grouping entities (e.g., `world://`, `ui://`, `physics://`).
- **Facet**: a subsystem-specific representation of a canonical entity (e.g., render/physics facets of a game entity).

---

## 4. Model Overview

OGIF represents a system as a graph:

- Entities: `E = {e1, e2, ...}`
- Relations: `R = {r1, r2, ...}` where each relation has:
  - `from` entity id,
  - `to` entity id,
  - `kind` (typed relation),
  - optional directionality and attributes.

Profiles define:
- allowed entity types,
- allowed relation kinds,
- required capabilities,
- required operations/events,
- additional semantics (e.g., UI event propagation, backpressure).

---

## 5. Identity, Namespacing, and Addressing

### 5.1 Entity IDs

Every entity MUST have a globally unique identifier within the OGIF endpoint scope.

IDs SHOULD be URI-like:

- `ui://overlay/hud#healthBar`
- `world://entity/Player/42`
- `physics://body/abc123`
- `rpc://service/auth#Login`

IDs MUST be stable for the lifetime of a session.  
In **test mode**, IDs SHOULD be stable across runs or provide stable aliases (see `meta.testTag`).

### 5.2 Relation IDs

Relations SHOULD have stable IDs if they are long-lived or addressable:

- `rel://world/attach/Player42->Weapon7`

If relation IDs are omitted, relations MUST still be uniquely addressable by `(from, to, kind, attributesHash)` within a snapshot.

### 5.2.1 Relation addressing without IDs (normative)

When a relation omits `id`, clients MUST be able to refer to it using a **relation key**.

Define `attributesHash` as:
- Let `attributes` be the relation `attributes` object (or `{}` if omitted).
- Canonicalize `attributes` using the JSON Canonicalization Scheme (JCS, RFC 8785) and UTF‑8 bytes.
- Compute `SHA-256` over the canonical bytes and represent it as `sha256:<lowercase-hex>`.

A relation key is:

```json
{
  "from": "render://object/42",
  "to": "world://entity/Player/42",
  "kind": "ogif:facetOf",
  "directed": true,
  "attributesHash": "sha256:..."
}
```

Rules:
- For key computation, if `directed` is omitted it MUST be treated as `true`.
- An endpoint MUST NOT emit two relations in the same snapshot with the same relation key.
- Any event or API result that needs to reference a relation MUST provide either `id` or a relation key.

### 5.3 Namespaces and Domains

Entities MAY declare a `domain` field to support cross-subsystem organization:

- `domain: "ui" | "world" | "physics" | "render" | "audio" | "net" | "custom"`

Domain values SHOULD be namespaced when custom:
- `mygame.domain:combat`

---

## 6. Data Model

### 6.1 Entity Schema (Core)

An OGIF entity MUST be representable as JSON with at least:

```json
{
  "id": "world://entity/Player/42",
  "type": "ogif.entity",
  "name": "Player",
  "capabilities": ["inspectable"],
  "state": {},
  "attributes": {},
  "meta": {}
}
```

#### Required Fields (full entity form)

* `id` (string)
* `type` (string)
* `capabilities` (array of strings; MAY be empty)
* `state` (object; MAY be empty)
* `attributes` (object; MAY be empty)
* `meta` (object; MAY be empty)

#### Disclosure-limited stubs (policy/redaction)

Endpoints MAY return a disclosure-limited **stub** entity (e.g., due to authorization or redaction). A stub MUST be a JSON object that includes at least:

* `id` (string)
* `type` (string)

A stub SHOULD include `meta.redacted=true` when fields are omitted due to policy.

#### Recommended Fields

* `name` (string)
* `description` (string)
* `schemaRef` (string; see §6.5)

### 6.1.1 Entity read method (JSON-RPC recommended)

`ogif.getEntity` reads one entity by id.

Request (recommended):

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "ogif.getEntity",
  "params": {
    "id": "world://entity/Player/42",
    "include": "full"
  }
}
```

Rules:
- `include` SHOULD be one of: `existence | metadata | full` (default: `metadata`).
- Responses MUST include the `revision` they reflect.

Response (recommended):

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "revision": "rev-1048",
    "entity": { "id": "world://entity/Player/42", "type": "ogif.entity" }
  }
}
```

### 6.2 Relation Schema (Core)

A relation MUST be representable as:

```json
{
  "id": "rel://world/facetOf/renderable42->player42",
  "from": "render://object/42",
  "to": "world://entity/Player/42",
  "kind": "ogif:facetOf",
  "directed": true,
  "attributes": {},
  "meta": {}
}
```

#### Required Fields

* `from` (entity id)
* `to` (entity id)
* `kind` (string)
* `directed` (boolean; default `true` if omitted)

#### Notes

* Even when `directed=false`, implementations MUST preserve `(from,to)` ordering as provided.

### 6.3 Graph Snapshot

A graph snapshot MUST include:

* `graphId` (string; endpoint-defined)
* `revision` (opaque string or integer; monotonic per endpoint)
* `entities` (list)
* `relations` (list)
* `profiles` (list of active profile IDs; see §10)

Example:

```json
{
  "graphId": "myapp://runtime",
  "revision": "rev-1048",
  "profiles": ["ogif-core-0"],
  "entities": [ /* ... */ ],
  "relations": [ /* ... */ ]
}
```

#### Optional paging (recommended)

For large graphs, an endpoint MAY return snapshots in pages.

If paging is used, the snapshot SHOULD include:

```json
{
  "page": {
    "isPartial": true,
    "nextCursor": "opaque-string"
  }
}
```

Rules:
- If `page.isPartial == true`, the returned `entities` / `relations` lists are incomplete.
- To continue, clients MUST call `ogif.getGraph` with `cursor=page.nextCursor`.
- When no more pages remain, `page.nextCursor` MUST be `null` (or `page` MAY be omitted entirely).
- Paging order MUST be deterministic for a given revision. If an endpoint does not specify an order, the RECOMMENDED default is:
  - entities ordered by `id` ascending
  - relations ordered by `(from, kind, to, attributesHash)` ascending

### 6.3.1 Graph snapshot method (JSON-RPC recommended)

`ogif.getGraph` returns the current graph snapshot (possibly paged).

Request (recommended):

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "ogif.getGraph",
  "params": {
    "graphId": "myapp://runtime",
    "include": "metadata",
    "maxEntities": 5000,
    "maxRelations": 20000,
    "cursor": null
  }
}
```

Rules:
- `include` SHOULD be one of: `existence | metadata | full` (default: `metadata`).
- `cursor` MUST be treated as opaque by clients.
- Responses MUST include the `revision` they reflect.

Response (recommended):

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "graphId": "myapp://runtime",
    "revision": "rev-1048",
    "profiles": ["ogif-core-0"],
    "entities": [],
    "relations": []
  }
}
```

### 6.4 Capabilities

Capabilities are strings that indicate affordances.

* Capabilities MAY be used as prerequisites for operations.
* Capabilities SHOULD be namespaced when custom:

  * `ogif.cap:inspectable`
  * `ogif.cap:invokable`
  * `mygame.cap:teleportable`

### 6.5 State and Attributes

* `state` MUST represent **current values** and **observable conditions**.
* `attributes` SHOULD represent **stable metadata** (configuration, classification, hints).

State SHOULD be patchable and observable via events (see §8.4).

### 6.6 Schema References

Entities, operations, and events MAY reference external schemas for typed payloads.

* `schemaRef` SHOULD be a resolvable URI:

  * `schemaRef: "schema://myapp/player@v3"`

OGIF does not mandate a schema system, but RECOMMENDS:

* JSON Schema for JSON payloads,
* Protobuf descriptors for binary payloads,
* or a documented custom schema registry.

Implementations SHOULD expose schema discovery via operation descriptors (§7).

---

## 7. Operations Model

OGIF defines operations as typed invocations on entities.

### 7.1 Operation Descriptor

An entity MAY advertise operations in `meta.interface.operations`:

```json
{
  "meta": {
    "interface": {
      "operations": [
        {
          "opId": "op://world/player42/move",
          "name": "Move",
          "capabilityRequired": "mygame.cap:movable",
          "paramsSchemaRef": "schema://myapp/moveParams@v1",
          "resultSchemaRef": "schema://myapp/moveResult@v1",
          "idempotency": "non_idempotent",
          "sideEffects": "state_change",
          "timeoutMsSuggested": 2000
        }
      ]
    }
  }
}
```

#### Descriptor Fields (Recommended)

* `opId` (string; stable)
* `name` (string)
* `capabilityRequired` (string | null)
* `paramsSchemaRef`, `resultSchemaRef` (string | null)
* `idempotency`: `"idempotent" | "non_idempotent" | "unknown"`
* `sideEffects`: `"none" | "state_change" | "external_effect" | "unknown"`
* `timeoutMsSuggested` (integer; optional)

Profiles MAY add stronger guarantees (e.g., transactional semantics).

### 7.2 Core Invocation Primitive

OGIF endpoints that support control MUST provide an invocation method (transport-specific).
For JSON-RPC, the REQUIRED method is:

* `ogif.invoke`

Request shape:

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "ogif.invoke",
  "params": {
    "opId": "op://world/player42/move",
    "target": "world://entity/Player/42",
    "args": { "dx": 1, "dy": 0, "dz": 0 },
    "correlationId": "corr-abc"
  }
}
```

Response MUST indicate acceptance and MAY include a result:

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "accepted": true,
    "result": { "ok": true },
    "correlationId": "corr-abc"
  }
}
```

If rejected, the endpoint MUST return a protocol error (see §12.3) or a typed rejection result if a profile requires it.

### 7.3 Preconditions and Safeguards (Recommended)

Operations SHOULD be rejected (or no-op) if preconditions fail.
Preconditions MAY be expressed as:

* state predicates (e.g., `enabled=true`),
* capability requirements,
* policy requirements (authz).

Profiles SHOULD specify standard rejection semantics for their domains.

---

## 8. Events and Observation

### 8.1 Event Envelope (Core)

All emitted events MUST follow a consistent envelope:

```json
{
  "eventId": "evt-000123",
  "type": "ogif.event:StateChanged",
  "timestamp": "2026-02-21T12:34:56.123Z",
  "source": "world://entity/Player/42",
  "data": {},
  "meta": {
    "correlationId": "corr-abc",
    "reliability": "best_effort"
  }
}
```

#### Required Fields

* `eventId` (string)
* `type` (string)
* `timestamp` (string ISO-8601)
* `source` (entity id; MAY be `null` for global events)
* `data` (object; MAY be empty)

#### Recommended Fields

* `meta.correlationId` to link events to an invocation or external trigger.
* `meta.reliability` one of:

  * `"best_effort" | "at_least_once" | "exactly_once" | "unknown"`

### 8.2 Subscriptions (Core)

Endpoints that support observation MUST provide:

* `ogif.subscribe`
* `ogif.unsubscribe`

Subscriptions MUST support filtering by:

* event types,
* entity selector (see §9),
* optionally relation selector.

#### 8.2.1 `ogif.subscribe` / `ogif.unsubscribe` (JSON-RPC recommended)

`ogif.subscribe` establishes an event stream filtered by event type and optional selectors.

Request params (recommended):
- `types` (array of event type strings)
- `selector` (string; optional; OGIF-SEL-0 minimum; see §9)
- `fromRevision` (string | number; optional; resume token)

Request example:

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "ogif.subscribe",
  "params": {
    "types": ["ogif.event:StateChanged"],
    "selector": "type(\"world.entity\")",
    "fromRevision": null
  }
}
```

Response (recommended):

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "subscriptionId": "sub-1",
    "revision": "rev-1049"
  }
}
```

Rules:
- If `fromRevision` is provided, the endpoint SHOULD resume from that token. If it cannot, it MUST fail the request rather than silently skipping history.
- The response MUST include the `revision` at which the subscription is established.

For JSON-RPC transports, the RECOMMENDED delivery mechanism is notifications:

```json
{
  "jsonrpc": "2.0",
  "method": "ogif.event",
  "params": {
    "subscriptionId": "sub-1",
    "event": {
      "eventId": "evt-000123",
      "type": "ogif.event:StateChanged",
      "timestamp": "2026-02-21T12:34:56.123Z",
      "source": "world://entity/Player/42",
      "data": { "revision": "rev-1050", "patch": [] },
      "meta": { "correlationId": "corr-abc", "reliability": "best_effort" }
    }
  }
}
```

`ogif.unsubscribe` request params (recommended):
- `subscriptionId` (string)

### 8.3 Required Core Event Types

An endpoint that supports mutable graphs MUST emit at least one of:

* `ogif.event:GraphChanged` (graph-level patch)
* `ogif.event:EntityChanged` (entity-level patch)
* `ogif.event:RelationChanged` (relation-level patch)

And SHOULD emit:

* `ogif.event:StateChanged` (when state changes)

Profiles MAY define domain events (e.g., collision, message received, UI announce).

### 8.4 Patch Format (Recommended)

JSON Patch (RFC 6902) is RECOMMENDED for change payloads.

Example:

```json
{
  "type": "ogif.event:StateChanged",
  "source": "world://entity/Player/42",
  "data": {
    "patch": [
      { "op": "replace", "path": "/state/health", "value": 95 }
    ],
    "revision": "rev-1049"
  }
}
```

---

## 9. Query and Selector Language

OGIF requires a way to locate entities/relations without hardcoding IDs.

### 9.1 Minimal Selector Requirements (OGIF-SEL-0)

An OGIF endpoint MUST support selectors that can match entities by:

* `#id` exact
* `type("...")`
* `name("...")` (case-insensitive SHOULD)
* `cap("...")`
* `state(path, predicate)` (at minimum equality)

It MUST also support traversal for at least one hop:

* `out(kind)` and `in(kind)` adjacency traversal

### 9.2 Selector Syntax (Suggested)

A compact function-based syntax:

* `#<id>`
* `type("world.entity")`
* `name("Player")`
* `cap("ogif.cap:invokable")`
* `state("/health" >= 1)` (predicate grammar is endpoint-defined; equality MUST exist)
* `attr("team" == "red")`

Traversal:

* `out("ogif:facetOf")`
* `in("ogif:represents")`

Composition:

* `A AND B`
* `A OR B`
* `NOT A`
* Parentheses

Example:

* `type("mygame.entity") AND state("/alive" == true)`
* `#world://entity/Player/42 out("ogif:facetOf")`

Endpoints MAY implement richer query languages, but MUST support OGIF-SEL-0.

### 9.3 Query Methods (JSON-RPC Recommended)

OGIF provides selector-based queries for entities and relations.

#### 9.3.1 `ogif.queryEntities`

Request params (recommended):
- `selector` (string; OGIF-SEL-0 minimum; see §9.1)
- `limit` (integer; optional; endpoint may clamp)
- `include` (`existence | metadata | full`; optional; default `metadata`)
- `cursor` (string | null; optional; opaque paging cursor)

Request example:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "ogif.queryEntities",
  "params": {
    "selector": "type(\"rpc.method\")",
    "limit": 100,
    "include": "metadata",
    "cursor": null
  }
}
```

Response (recommended):

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "revision": "rev-1048",
    "entities": [],
    "page": { "nextCursor": null }
  }
}
```

Rules:
- Responses MUST include the `revision` they reflect.
- Paging order MUST be deterministic for a given revision. If an endpoint does not specify an order, the RECOMMENDED default is entities ordered by `id` ascending.

#### 9.3.2 `ogif.queryRelations`

Request params (recommended):
- `selector` (string; see §9.1)
- `limit` (integer; optional; endpoint may clamp)
- `cursor` (string | null; optional; opaque paging cursor)

Response (recommended):

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "revision": "rev-1048",
    "relations": [],
    "page": { "nextCursor": null }
  }
}
```

Rules:
- Paging order MUST be deterministic for a given revision. If an endpoint does not specify an order, the RECOMMENDED default is relations ordered by `(from, kind, to, attributesHash)` ascending.

---

## 10. Profiles

OGIF uses profiles to express paradigm-specific semantics without bloating the core.

### 10.1 Profile Declaration

A graph snapshot MUST include the active profiles:

```json
"profiles": [
  "ogif-core-0",
  "myapp.profile:runtime-graph-1"
]
```

Profile IDs MUST be stable strings with version suffixes.

### 10.2 What Profiles Define

A profile MAY define:

* entity type vocabularies,
* relation kinds and constraints,
* required operations/events,
* ordering and reliability guarantees,
* determinism/time control semantics,
* safety and authorization rules,
* domain-specific selector extensions.

### 10.3 Reserved Core Profile

This document defines the core profile:

* `ogif-core-0`

Other profiles (e.g., UI tree interaction, dataflow DAG, RPC resources, ECS world) MUST be defined in separate specification documents that reference OGIF core.

> Note: A future “OmniDOM” specification can be defined as an OGIF profile that constrains relations to a tree and adds event propagation semantics. Any UI-specific addenda (e.g., stimulus integrity rules) belong to that profile, not OGIF core.

---

## 11. Facets and Multi-Layered Entities

Complex systems often have the “same thing” represented in multiple subsystems.

OGIF supports this using **facet relations** rather than forcing everything into one hierarchy.

### 11.1 Core Relation Kinds (Reserved)

OGIF reserves these relation kinds with suggested semantics:

* `ogif:facetOf`
  **Meaning:** `from` is a subsystem facet of canonical entity `to`.
  Example: render object facet ? world entity.

* `ogif:represents`
  **Meaning:** `from` is a representation/view of `to` (not necessarily a facet).
  Example: UI health bar represents player health component.

* `ogif:dependsOn`
  **Meaning:** `from` depends on `to` (ordering/availability, not ownership).

* `ogif:contains`
  **Meaning:** containment/aggregation (not necessarily exclusive ownership).

Profiles MAY constrain these more strictly.

### 11.2 Canonical Identity Recommendation

In systems with many layers (e.g., a game), implementers SHOULD designate a canonical identity domain (often gameplay/ECS), and attach subsystem facets to canonical entities via `ogif:facetOf`.

This avoids artificial “one tree to rule them all” designs while preserving cross-layer queryability.

---

## 12. Transport and Wire Protocol

OGIF is transport-agnostic. However, for interoperability, OGIF RECOMMENDS:

* JSON-RPC 2.0 over:

  * stdio (subprocess automation),
  * Unix domain socket / Windows named pipe,
  * localhost TCP (authenticated).

Alternatively:

* gRPC with a similar method surface and streaming for subscriptions.

### 12.1 Required Methods for OGIF-Core Control Endpoints

If an endpoint claims **OGIF-Core Control**, it MUST implement:

* `ogif.getVersion`
* `ogif.getGraph` (snapshot)
* `ogif.getEntity`
* `ogif.queryEntities`
* `ogif.queryRelations`
* `ogif.invoke`
* `ogif.subscribe`
* `ogif.unsubscribe`

If an endpoint is **read-only**, it MUST still implement:

* `ogif.getVersion`
* `ogif.getGraph`
* `ogif.getEntity`
* `ogif.queryEntities`
* `ogif.queryRelations`
* `ogif.subscribe` (optional but RECOMMENDED)

### 12.2 Version Negotiation

`ogif.getVersion` MUST return:

* spec name/version,
* supported profiles,
* supported selector version,
* supported patch format,
* and SHOULD return feature flags relevant to interoperability (e.g., paging, event replay).

Example:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "spec": "OmniGraphIF",
    "version": "0.1.0",
    "profiles": ["ogif-core-0"],
    "features": {
      "selectors": "ogif-sel-0",
      "patch": "rfc6902",
      "paging": true,
      "eventReplay": false
    }
  }
}
```

### 12.3 Error Codes (Recommended)

Endpoints SHOULD use stable error codes:

* `-32001` selector parse error
* `-32002` entity not found
* `-32003` relation not found
* `-32004` operation not permitted (authz)
* `-32005` operation rejected (precondition failed)
* `-32006` timeout
* `-32007` rate limited
* `-32008` resync required (invalid/expired revision or cursor)

---

## 13. Consistency, Revisions, and Concurrency

### 13.1 Graph Revision

Each snapshot MUST include a `revision`. Revisions MUST be monotonic within an endpoint instance.

### 13.2 Event Ordering (Core)

OGIF core does not mandate strict total ordering across all events. However:

* Events emitted by a single entity SHOULD be ordered.
* Patch events SHOULD include a `revision` to support reconciliation.
* Profiles MAY strengthen ordering guarantees.

### 13.3 Client Reconciliation (Recommended)

Clients SHOULD:

* record the latest seen `revision`,
* apply patch events when possible,
* fall back to `ogif.getGraph` if patches are missed or out-of-order.

---

## 14. Security and Safety

OGIF endpoints are powerful. Implementations MUST consider:

### 14.1 Principle of Least Privilege

Endpoints MUST enforce visibility and invocation permissions. Clients MUST NOT automatically get full access to all entities/ops.

### 14.2 Separation of Surfaces (Recommended)

Implementations SHOULD separate:

* **user-equivalent surfaces** (safe automation, testing, assistive tech),
* **privileged module/service surfaces** (internal control).

A client MAY be allowed to observe more than it can control.

### 14.3 Sensitive Data

Entities containing secrets MUST:

* mark sensitive fields (e.g., `attributes.sensitive=true`),
* redact them in snapshots by default,
* avoid leaking secrets through events.

Profiles MAY add stronger rules.

---

## 15. Determinism and Testability (Core Guidance)

OGIF core RECOMMENDS (but does not require) a “test mode” in which:

* IDs are stable or have stable `meta.testTag`,
* nondeterministic scheduling is minimized,
* time-based flows can be controlled.

Time control is intentionally profile- or extension-defined, because semantics differ across paradigms (UI animation vs physics stepping vs stream clocks).

---

## 16. Conformance

An endpoint is **OGIF-Core Conformant** if it:

1. Provides graph snapshots with entities and relations as specified (§6.3).
2. Supports OGIF-SEL-0 selectors and query methods (§9).
3. Emits at least graph/entity/relation change events when mutation occurs (§8.3).
4. Implements required method surface for its declared mode (control vs read-only) (§12.1).
5. Implements `ogif.getVersion` with profiles/features (§12.2).
6. Enforces basic security expectations (§14).

Profiles define additional conformance requirements beyond OGIF core.

---

## 17. Examples

### 17.1 3D Game: Canonical Entity with Facets (Graph, Not a Tree)

Entities:

* `world://entity/Player/42` (canonical)
* `render://object/42` (render facet)
* `physics://body/abc123` (physics facet)
* `ui://overlay/hud#healthBar` (UI element)

Relations:

* `render://object/42 --ogif:facetOf--> world://entity/Player/42`
* `physics://body/abc123 --ogif:facetOf--> world://entity/Player/42`
* `ui://overlay/hud#healthBar --ogif:represents--> world://entity/Player/42`

This preserves interconnectedness without forcing one parent-child hierarchy.

### 17.2 Unix-Style Pipeline (DAG)

Entities:

* `flow://module/cat`
* `flow://module/grep`
* `flow://module/sort`
* ports as entities, or ports as attributes

Relations:

* `cat --flow:connectsTo--> grep`
* `grep --flow:connectsTo--> sort`

A dataflow profile (future) would define backpressure, stream schemas, and lifecycle ops.

---

## 18. IANA / Registry Considerations (Optional)

For interoperability across vendors, OGIF deployments MAY maintain registries for:

* profile IDs,
* reserved relation kinds,
* capability namespaces,
* schema URIs.

This document reserves the `ogif:` prefix for relation kind identifiers and core capability/event naming.

---

**End of OmniGraphIF v0.1.0 (Draft)**
