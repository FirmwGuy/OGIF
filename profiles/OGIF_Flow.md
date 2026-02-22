# OmniFlow Profile Specification
## OGIF Profile: Dataflow DAG, Ports/Streams, Backpressure, and Deterministic Pipeline Control

**Profile Name:** OmniFlow  
**OGIF Profile ID:** `ogif.profile:omniflow-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Selector Baseline:** `ogif-sel-0` + OmniFlow Selector Extension `flow-sel-0` (defined herein)

---

## 1. Purpose

OmniFlow is an OGIF profile that models **program-to-program** and **module-to-module** composition as a **dataflow graph** of:

- pipelines,
- modules/operators,
- ports,
- connections,
- and (optionally) observable streams.

It provides a **control and observability plane** for pipeline-like systems (Unix pipelines, ETL graphs, media pipelines, reactive processing), including:

- explicit connectivity (what is connected to what),
- lifecycle and configuration control,
- typed schemas for data interchange,
- backpressure/buffering semantics,
- metrics and health,
- and test hooks (optional, capability-gated) for injection/drain.

OmniFlow is designed to avoid brittle “screen scraping logs” and ad hoc supervision. It does **not** aim to replace efficient data transport protocols; instead it standardizes the **semantic graph** and **control surface**.

---

## 2. Design Goals

An OmniFlow implementation MUST allow a client to:

1. **Discover** the pipeline graph (modules, ports, connections).
2. **Connect / Disconnect** modules through explicit, typed port connections.
3. **Start / Stop / Pause / Resume** pipeline execution with predictable lifecycle semantics.
4. **Observe** module and connection state, errors, backpressure, and throughput/latency metrics.
5. **Validate** constraints (schema mismatch, permission restrictions, unsafe wiring) deterministically.
6. (Optional) **Test** data behavior by injecting and draining data in a controlled manner without production hacks.

---

## 3. Non-goals

OmniFlow does NOT standardize:

- the on-the-wire encoding for the primary data plane (though it defines optional data-plane extensions),
- a universal streaming delivery guarantee (exactly-once, etc.) unless a deployment chooses one,
- general service RPC interfaces (use OmniRPC),
- UI interaction trees (use OmniDOM),
- simulation/ECS worlds (use OmniECS).

---

## 4. Relationship to OGIF Core

OmniFlow is expressed using OGIF core constructs:

- OmniFlow components are OGIF **entities** with `type` in the `flow.*` namespace.
- Connectivity is expressed as OGIF **relations** with kinds `flow:*`.
- Control is expressed as OGIF **operations** (via `ogif.invoke`) and/or profile-friendly wrappers (recommended).
- Observation uses OGIF **events** and subscriptions, with OmniFlow-specific event types `flow.event:*`.

Implementations MUST advertise `ogif.profile:omniflow-0` via `ogif.getVersion`.

---

## 5. Entity Types

OmniFlow defines the following reserved entity `type` values.

### 5.1 Required Types

An OmniFlow endpoint MUST represent at least:

- `flow.module` — a processing unit (process, thread, operator, plugin)
- `flow.port` — an input or output interface on a module

### 5.2 Optional Types (Recommended)

Endpoints SHOULD represent, when applicable:

- `flow.pipeline` — a logical grouping/root for modules (a composition unit)
- `flow.connection` — an explicit connection entity (useful when connections carry metadata)
- `flow.schema` — explicit schema entities (alternatively use `schemaRef` URIs)

### 5.3 Common Fields (Core)

All OmniFlow entities MUST conform to OGIF entity schema and SHOULD include:

- `name` (human-friendly)
- `attributes` for stable metadata
- `state` for dynamic signals (lifecycle, backpressure, stats pointers)
- `meta.testTag` for stability in test mode (RECOMMENDED)

---

## 6. Relation Kinds and Topology Constraints

### 6.1 Reserved Relation Kinds

OmniFlow reserves these relation `kind` identifiers (all directed unless noted):

- `flow:contains` (pipeline ? module)  
- `flow:hasPort` (module ? port)  
- `flow:connectsTo` (output port ? input port)  
- `flow:dependsOn` (module ? module) (optional; informational)  

Endpoints MAY define custom relation kinds, namespaced (e.g., `myflow:mirrorsTo`).

### 6.2 Port Direction Constraint (MUST)

Every `flow.port` MUST declare:

- `attributes.direction` = `"in"` or `"out"`

A `flow:connectsTo` relation MUST be from an `"out"` port to an `"in"` port.

If violated, the endpoint MUST reject the connection attempt (see §11.2).

### 6.3 Graph Constraint (Default: DAG)

By default, the directed graph induced by `flow:connectsTo` relations SHOULD be a **DAG**.

Cycles MAY be permitted only if:

- the pipeline entity has `attributes.allowCycles = true`, OR
- the connection(s) involved have `attributes.feedback = true`

If cycles are disallowed, the endpoint MUST reject any connect operation that would introduce a cycle.

### 6.4 Ordering (RECOMMENDED)

For deterministic inspection and UI rendering, `flow:hasPort` relations SHOULD include:

- `attributes.order` (integer, unique per module)

Similarly, `flow:contains` MAY include `attributes.order` for pipeline module ordering.

---

## 7. Port Model, Schemas, and Compatibility

### 7.1 Port Attributes (MUST / SHOULD)

Every `flow.port` MUST include:

- `attributes.direction`: `"in"` or `"out"`

Every `flow.port` SHOULD include:

- `attributes.schemaRef`: URI identifying the record/batch schema (or `null` if byte-stream)
- `attributes.mediaType`: e.g., `"application/x-ndjson"`, `"application/protobuf"`, `"application/octet-stream"`
- `attributes.transport`: `"stdio" | "pipe" | "socket" | "file" | "memory" | "custom"`
- `attributes.cardinality`: `"one" | "many"` (whether multiple connections are allowed)

Example:
```json
{
  "id": "flow://module/grep#stdin",
  "type": "flow.port",
  "name": "stdin",
  "attributes": {
    "direction": "in",
    "transport": "stdio",
    "mediaType": "application/x-ndjson",
    "schemaRef": "schema://example/logRecord@v1",
    "cardinality": "one"
  },
  "state": { "connected": false }
}
```

### 7.2 Schema Compatibility (MUST)

When connecting an out port to an in port, the endpoint MUST verify schema compatibility according to one of:

* **Exact match**: `out.schemaRef == in.schemaRef`
* **Declared compatibility**: `out` declares `attributes.compatibleWith[]` including `in.schemaRef`
* **Adapter available**: a declared adapter module/operation exists (profile- or deployment-defined)

If schemas are incompatible and no adapter is configured, the endpoint MUST reject the connection.

### 7.3 Byte Streams (Allowed)

If a port’s `schemaRef` is `null` or omitted, it is treated as an untyped byte stream.

Byte stream ports MAY connect only if:

* both ports are untyped, OR
* the endpoint explicitly supports implicit encoding/decoding adapters (deployment-defined).

---

## 8. Lifecycle and State Semantics

### 8.1 Module Lifecycle State (MUST)

Every `flow.module` MUST expose `state.lifecycle` with one of:

* `created`
* `configured`
* `running`
* `paused`
* `stopped`
* `error`

Transitions MUST be caused by operations or internal faults and MUST be observable via events (§10).

### 8.2 Connection State (RECOMMENDED)

Ports SHOULD expose:

* `state.connected` (boolean)
* `state.connectionCount` (integer)

Connections (if represented as entities) SHOULD expose:

* `state.open` (boolean)
* `state.lastError` (string|object|null)

---

## 9. Backpressure, Buffering, and Flow Control

### 9.1 Backpressure Signals (MUST)

If the system can experience backpressure, the endpoint MUST expose it semantically.

At minimum, affected ports or modules MUST expose:

* `state.backpressure` (boolean)

Endpoints SHOULD also expose:

* `state.bufferedItems` (integer)
* `state.bufferedBytes` (integer)
* `state.droppedItems` (integer; if dropping occurs)
* `state.latencyMs` (number; rolling estimate)
* `state.throughputItemsPerSec` (number; rolling estimate)

### 9.2 Backpressure Events (MUST)

When `state.backpressure` changes, the endpoint MUST emit:

* `flow.event:BackpressureChanged`

with payload including:

* `data.portId` or `source` as the affected port
* `data.backpressure` boolean
* optional buffer metrics

### 9.3 Loss and Reliability Declaration (MUST)

If data may be dropped, the endpoint MUST declare loss behavior at the relevant scope:

* Port: `attributes.lossPolicy = "lossless" | "drop_oldest" | "drop_newest" | "sample" | "unknown"`
* Connection: same (if connection entities exist)

Clients MUST NOT assume lossless delivery unless declared.

---

## 10. Events

OmniFlow event types MUST be prefixed `flow.event:` and use the OGIF event envelope.

### 10.1 Required Events (Control/Observable Systems)

An OmniFlow endpoint MUST emit (directly or via OGIF patch events) enough information to observe:

* module lifecycle changes
* connection changes
* backpressure changes
* errors

Normatively, the endpoint MUST emit at least these OmniFlow-specific events:

* `flow.event:ModuleLifecycleChanged`
* `flow.event:ConnectionChanged`
* `flow.event:BackpressureChanged`
* `flow.event:Error`

The endpoint MUST ALSO emit OGIF patch events (`ogif.event:StateChanged` / `EntityChanged` / `GraphChanged`) whenever entity/graph state changes.

### 10.2 Recommended Events

* `flow.event:Stats` (periodic metrics snapshot)
* `flow.event:DataPlaneStatus` (e.g., “stream opened/closed”)
* `flow.event:ConfigChanged`

### 10.3 Event Payload Requirements

#### 10.3.1 ModuleLifecycleChanged

```json
{
  "type": "flow.event:ModuleLifecycleChanged",
  "source": "flow://module/grep",
  "data": {
    "from": "paused",
    "to": "running",
    "reason": "resume"
  }
}
```

#### 10.3.2 ConnectionChanged

```json
{
  "type": "flow.event:ConnectionChanged",
  "source": "flow://module/grep#stdout",
  "data": {
    "action": "connected",
    "fromPort": "flow://module/grep#stdout",
    "toPort": "flow://module/sort#stdin"
  }
}
```

#### 10.3.3 Error

```json
{
  "type": "flow.event:Error",
  "source": "flow://module/grep",
  "data": {
    "severity": "error",
    "messageId": "flow.module.exec_failed",
    "text": "grep exited with code 2",
    "details": { "exitCode": 2 }
  }
}
```

---

## 11. Operations

OmniFlow defines a standard set of operations. Implementations MAY expose them as:

* OGIF operation descriptors invoked via `ogif.invoke`, and/or
* profile-friendly wrapper methods (recommended names below).

### 11.1 Reserved Capabilities for Operations

Operations MUST be capability-gated. OmniFlow reserves:

* `flow.cap:inspectable`
* `flow.cap:configurable`
* `flow.cap:connectable`
* `flow.cap:startable`
* `flow.cap:stoppable`
* `flow.cap:pausable`
* `flow.cap:observableStats`
* `flow.cap:testInject` (TEST ONLY)
* `flow.cap:testDrain` (TEST ONLY)

### 11.2 Connection Operations (MUST for Control Conformance)

#### 11.2.1 `flow.connect`

Connect an out port to an in port.

Params (recommended):

* `fromPortId` (string)
* `toPortId` (string)
* optional `adapterModuleId` (string)
* optional `attributes` (object)

The endpoint MUST reject connect if:

* port directions are invalid (§6.2),
* schema compatibility fails (§7.2),
* cardinality constraints are violated (§7.1),
* it would introduce a disallowed cycle (§6.3),
* the client lacks authorization.

#### 11.2.2 `flow.disconnect`

Disconnect a specific connection or a port pair.

Params (recommended):

* `fromPortId`, `toPortId` OR `connectionId`

### 11.3 Lifecycle Operations (MUST for Control Conformance)

* `flow.start(targetId)` — pipeline or module
* `flow.stop(targetId)`
* `flow.pause(targetId)` (if supported)
* `flow.resume(targetId)` (if supported)

Lifecycle operations MUST cause `state.lifecycle` transitions and MUST emit `flow.event:ModuleLifecycleChanged` (or equivalent patch + event).

### 11.4 Configuration Operations (SHOULD)

* `flow.setConfig(targetId, patch)`

  * `patch` SHOULD be RFC 6902 JSON Patch against `attributes.config` or `state.config`
  * MUST validate against declared schemas when available

### 11.5 Stats Operations (SHOULD)

* `flow.getStats(targetId)`
  Returns a snapshot of throughput/latency/backpressure metrics.

### 11.6 Test Operations (Optional, Capability-Gated, Disabled by Default)

These are OPTIONAL and MUST be explicitly capability-gated:

* `flow.test.inject(portId, records|bytes, options)`
* `flow.test.drain(portId, maxItems|maxBytes, options)`

If implemented:

* the endpoint MUST advertise `features.flowTest = "flow-test-0"` in `ogif.getVersion`.
* production deployments SHOULD disable these by default.

---

## 12. Data Plane Extensions (Optional)

OmniFlow intentionally separates control/observability from data transport. However, standardized optional extensions are useful for testing, debugging, and small-scale pipelines.

### 12.1 `flow-data-0` Extension (Optional)

If an endpoint supports streaming records through OGIF subscriptions (not recommended for high throughput), it MUST advertise:

* `features.flowData = "flow-data-0"`

and define one or both of:

* `flow.event:Data` (record/batch events)
* `flow.event:DataBatch` (chunked/batched)

#### 12.1.1 Ordering

Data events MUST be ordered per connection (outPort?inPort pair).

#### 12.1.2 Framing and Encoding

For JSON event payloads, `flow.event:Data` SHOULD use one of:

* `data.record` (single JSON object)
* `data.records` (array of JSON objects)
* `data.bytesBase64` (for binary payloads)

and SHOULD include:

* `data.schemaRef` (or null for bytes)
* `data.mediaType`
* `data.connectionId` or `{ fromPortId, toPortId }`

Example:

```json
{
  "type": "flow.event:DataBatch",
  "source": "flow://module/cat#stdout",
  "data": {
    "fromPortId": "flow://module/cat#stdout",
    "toPortId": "flow://module/grep#stdin",
    "schemaRef": "schema://example/logRecord@v1",
    "mediaType": "application/x-ndjson",
    "records": [
      { "line": "hello" },
      { "line": "world" }
    ]
  }
}
```

### 12.2 Recommendation: External Data Plane

For serious throughput, deployments SHOULD carry data on a dedicated plane:

* stdio pipes,
* sockets,
* shared memory,
* message brokers,
* specialized streaming frameworks

OmniFlow remains the control/semantic plane that describes and supervises that data plane.

---

## 13. OmniFlow Selectors (`flow-sel-0`)

Endpoints MUST support `ogif-sel-0` and SHOULD support these profile conveniences:

* `type(flow.module)` / `type(flow.port)` / `type(flow.pipeline)`
* `port(dir="in"|"out")` (matches `flow.port` by `attributes.direction`)
* `schema("schema://...")` (matches ports by `attributes.schemaRef`)
* `connected()` (ports with `state.connected=true`)
* Traversals:

  * `out("flow:hasPort")` (module ? ports)
  * `out("flow:connectsTo")` (out port ? in port)
  * `in("flow:connectsTo")` (in port ? out port)

Example:

* `type(flow.module) name("grep") out("flow:hasPort") port(dir="out")`

---

## 14. Mapping to Unix Pipelines (Informative)

A Unix pipeline such as:

```bash
cat file | grep foo | sort
```

can be represented as:

* Modules:

  * `flow://module/cat`
  * `flow://module/grep`
  * `flow://module/sort`

* Ports:

  * `#stdin`, `#stdout`, optionally `#stderr`

* Connections:

  * `cat#stdout flow:connectsTo grep#stdin`
  * `grep#stdout flow:connectsTo sort#stdin`

A deployment MAY choose to:

* represent each OS process as a `flow.module`,
* represent OS pipes as `flow.connection` entities with buffer stats,
* expose exit codes as module state:

  * `state.exitCode`, `state.lastSignal`, `state.lastError`.

---

## 15. Security Considerations

OmniFlow frequently exposes powerful controls.

### 15.1 Least Privilege (MUST)

Endpoints MUST enforce authorization for:

* connecting/disconnecting,
* starting/stopping,
* configuration changes,
* test injection/drain.

### 15.2 Data Leakage (MUST/SHOULD)

If `flow-data-0` is enabled, it can leak sensitive data. Endpoints MUST:

* restrict subscriptions to `flow.event:Data*` by policy,
* support redaction or disablement where required.

### 15.3 Production Safety (RECOMMENDED)

Production deployments SHOULD:

* disable test operations,
* restrict graph mutation to trusted controllers,
* limit debug verbosity in events.

---

## 16. Conformance Levels

### 16.1 OmniFlow-Read Conformance

An endpoint is OmniFlow-Read conformant if it:

* exposes `flow.module` and `flow.port` entities,
* exposes `flow:hasPort` and `flow:connectsTo` relations where applicable,
* provides schemas/metadata as available,
* emits required events or OGIF patches for lifecycle/connection/backpressure/error observability.

### 16.2 OmniFlow-Control Conformance

Includes OmniFlow-Read and additionally:

* supports connect/disconnect operations with schema and cycle validation,
* supports start/stop lifecycle control,
* emits required OmniFlow events for changes.

### 16.3 OmniFlow-Data Conformance (Optional)

Includes OmniFlow-Control and additionally:

* supports `flow-data-0` streaming events with ordering per connection,
* advertises the feature in `ogif.getVersion`.

### 16.4 OmniFlow-Test Conformance (Optional, Recommended for CI)

Includes OmniFlow-Control and additionally:

* provides stable IDs or `meta.testTag`,
* offers test injection/drain ops under explicit capability,
* provides deterministic behavior when configured for test mode.

---

## 17. Example (Informative)

### 17.1 Simple Pipeline Graph

Pipeline:

* `flow://pipeline/main`

Modules:

* `flow://module/source`
* `flow://module/filter`
* `flow://module/sink`

Relations:

* `pipeline flow:contains source/filter/sink`
* `module flow:hasPort ports`
* `source#out flow:connectsTo filter#in`
* `filter#out flow:connectsTo sink#in`

A test client can:

1. connect ports,
2. start pipeline,
3. watch `flow.event:BackpressureChanged` and `flow.event:Error`,
4. optionally inject test records into `filter#in` and drain from `sink#out`.

---

**End of OmniFlow Profile Specification `ogif.profile:omniflow-0` (Draft)**
