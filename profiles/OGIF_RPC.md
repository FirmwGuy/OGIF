# OmniRPC Profile Specification
## OGIF Profile: Services, Resources, Methods, Calls, Watches, and Compatibility Contracts

**Profile Name:** OmniRPC  
**OGIF Profile ID:** `ogif.profile:omnirpc-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Selector Baseline:** `ogif-sel-0` + OmniRPC Selector Extension `rpc-sel-0` (defined herein)

---

## 1. Purpose

OmniRPC is an OGIF profile that models **program-to-program** and **module-to-module** interfaces in terms of:

- **services**,
- **methods** (operations callable by clients),
- **resources** (stateful objects addressable by identifiers),
- and **watches** (subscriptions to resource/service changes),

with explicit metadata for:

- schemas and payload types,
- idempotency and side-effects,
- compatibility/versioning,
- authentication/authorization requirements,
- error taxonomies,
- and observability/correlation.

OmniRPC is intended to provide a **semantic interface plane** that is transport-agnostic and can map cleanly to:
- REST/HTTP resources,
- gRPC methods and streams,
- message-bus request/reply,
- local module boundaries (plugin RPC),
- and test harnesses.

---

## 2. Design Goals

An OmniRPC implementation MUST allow a client to:

1. **Discover** services, methods, and resources (introspection).
2. **Call** methods with declared schemas and predictable semantics (control surface).
3. **Watch** resources/services for changes (observation surface) when supported.
4. **Negotiate** versions/compatibility contracts explicitly (no guesswork).
5. **Enforce** security boundaries: authenticated calls, authorized access, redaction in events/snapshots.

---

## 3. Non-goals

OmniRPC does NOT standardize:

- HTTP details (headers, status codes), gRPC wire details, or message broker protocols.
- Exactly-once semantics by default (profiles/deployments may strengthen).
- UI event routing (OmniDOM), streaming dataflow semantics/backpressure (OmniFlow), or ECS worlds (OmniECS).

OmniRPC **can** coexist with those profiles under OGIF.

---

## 4. Relationship to OGIF Core

OmniRPC uses OGIF core constructs:

- services/methods/resources are OGIF **entities** with `type` in the `rpc.*` namespace.
- exposures/ownership are OGIF **relations** with kinds `rpc:*`.
- method invocation is implemented via OGIF **operations** (via `ogif.invoke`) and/or profile wrapper methods.
- watches and notifications are expressed via OGIF **events** and subscriptions.

Endpoints MUST advertise `ogif.profile:omnirpc-0` via `ogif.getVersion`.

---

## 5. Entity Types

OmniRPC defines the following reserved entity `type` values.

### 5.1 Required Types

An OmniRPC endpoint MUST represent at least:

- `rpc.service` — a callable service boundary (server, module, plugin)
- `rpc.method` — a callable method (operation descriptor holder)

### 5.2 Optional Types (Recommended)

Endpoints SHOULD represent, when applicable:

- `rpc.resource` — a stateful addressable object (REST-like resource)
- `rpc.interface` — a named interface/contract descriptor entity
- `rpc.version` — explicit version entities for services/interfaces
- `rpc.schema` — schema registry entries (or use `schemaRef` URIs only)
- `rpc.errorType` — structured error taxonomy entries

---

## 6. Relation Kinds and Structural Conventions

OmniRPC does not impose a global topology constraint (not a tree/DAG). It does define relation kinds to make the graph interpretable.

### 6.1 Reserved Relation Kinds

All are directed:

- `rpc:exposes` (service ? method)  
  A service exposes a callable method.

- `rpc:owns` (service ? resource)  
  A service is the authority for a resource.

- `rpc:implements` (service ? interface)  
  A service implements a named interface contract.

- `rpc:hasVersion` (service/interface ? version)  
  Declares versions explicitly.

- `rpc:usesSchema` (method/resource/errorType ? schema) (optional)  
  Links to schema entities if the endpoint represents them.

- `rpc:declaresError` (method ? errorType) (optional)  
  Declares possible structured errors.

Custom relation kinds MUST be namespaced (e.g., `myrpc:routesTo`).

---

## 7. Method Model

### 7.1 Method Identity

Each `rpc.method` MUST have a stable entity id. RECOMMENDED ID style:

- `rpc://service/auth#Login`
- `rpc://service/billing#Charge`

### 7.2 Method Attributes (Required / Recommended)

Every `rpc.method` MUST include, in `attributes`:

- `attributes.methodName` (string; stable)
- `attributes.callType` (string):
  - `"unary"` (required minimum)
  - `"server_stream"` (optional)
  - `"client_stream"` (optional)
  - `"bidi_stream"` (optional)
  - `"watch"` (optional; see §9)

Every `rpc.method` SHOULD include:

- `attributes.paramsSchemaRef` (URI | null)
- `attributes.resultSchemaRef` (URI | null)
- `attributes.idempotency`:
  - `"idempotent" | "non_idempotent" | "unknown"`
- `attributes.sideEffects`:
  - `"none" | "state_change" | "external_effect" | "unknown"`
- `attributes.timeoutMsSuggested` (integer)
- `attributes.auth` (object; see §13)
- `attributes.deprecated` (boolean)
- `attributes.deprecationMessage` (string | null)

Example:
```json
{
  "id": "rpc://service/auth#Login",
  "type": "rpc.method",
  "name": "Login",
  "attributes": {
    "methodName": "Login",
    "callType": "unary",
    "paramsSchemaRef": "schema://auth/loginParams@v2",
    "resultSchemaRef": "schema://auth/loginResult@v2",
    "idempotency": "non_idempotent",
    "sideEffects": "state_change",
    "timeoutMsSuggested": 5000,
    "auth": { "required": true, "schemes": ["bearer"] },
    "deprecated": false
  },
  "capabilities": ["rpc.cap:callable"],
  "state": {}
}
```

### 7.3 Capabilities (Reserved)

OmniRPC reserves these capability tokens:

* `rpc.cap:inspectable` — entity discoverable/introspectable
* `rpc.cap:callable` — method may be called via OmniRPC control surface
* `rpc.cap:watchable` — resource/method supports watch subscription semantics
* `rpc.cap:describable` — service/method supports rich description (schemas, compat)
* `rpc.cap:adminOnly` — marker suggesting privileged access required (policy still enforced elsewhere)

Implementations MUST NOT treat capability tokens as authorization. They are *advertisements*; actual authorization is enforced by policy.

---

## 8. Operations (Calls)

OmniRPC defines standard operations for invocation. Implementations MAY expose them as OGIF operation descriptors (invoked via `ogif.invoke`) and/or as wrapper methods.

### 8.1 Required Call Operation (Control Conformance)

An OmniRPC endpoint claiming **Control Conformance** (§16.2) MUST support calling unary methods.

#### 8.1.1 Standard Invocation Form

The endpoint MUST provide an operation that behaves as:

* `rpc.call({ methodId, args, options }) -> { result | error }`

If implemented via OGIF operations, a `rpc.method` entity SHOULD advertise an operation descriptor with:

* `name`: `"rpc.call"`
* `opId`: stable
* `paramsSchemaRef` / `resultSchemaRef`

If implemented via JSON-RPC wrapper, RECOMMENDED method name:

* `rpc.call`

Request (recommended shape):

```json
{
  "jsonrpc": "2.0",
  "id": 100,
  "method": "rpc.call",
  "params": {
    "methodId": "rpc://service/auth#Login",
    "args": { "username": "alice", "password": "REDACTED" },
    "options": {
      "timeoutMs": 5000,
      "idempotencyKey": "optional-string",
      "trace": { "correlationId": "corr-1" }
    }
  }
}
```

Response (success):

```json
{
  "jsonrpc": "2.0",
  "id": 100,
  "result": {
    "ok": true,
    "result": { "token": "REDACTED" },
    "meta": { "correlationId": "corr-1" }
  }
}
```

Response (typed error):

```json
{
  "jsonrpc": "2.0",
  "id": 100,
  "result": {
    "ok": false,
    "error": {
      "code": "auth.invalid_credentials",
      "message": "Invalid username or password",
      "details": { }
    },
    "meta": { "correlationId": "corr-1" }
  }
}
```

### 8.2 Idempotency and Retries (Normative Metadata)

If a method declares `attributes.idempotency = "idempotent"`, clients MAY retry safely under typical network failure assumptions.

If a method declares `non_idempotent`, clients SHOULD NOT retry automatically unless:

* an `idempotencyKey` mechanism is explicitly supported and documented.

Endpoints SHOULD document idempotency key behavior via:

* `attributes.supportsIdempotencyKey` (boolean)
* and (optionally) schema for idempotency tokens.

### 8.3 Streaming Methods (Optional)

If `attributes.callType` is one of `server_stream`, `client_stream`, or `bidi_stream`, the profile RECOMMENDS representing streams as subscriptions and/or stream entities, but does not mandate a single mechanism in v0.1.0.

If implemented, the endpoint MUST advertise feature support via `ogif.getVersion.features.streaming = "rpc-stream-0"`.

---

## 9. Resource Model and Watches

### 9.1 Resource Identity

A `rpc.resource` represents a stateful addressable object. It MUST have:

* stable `id`
* `attributes.resourceType` (string)
* `attributes.key` (string|object identifying the instance) OR an explicit address like `attributes.uri`

Example:

```json
{
  "id": "rpc://service/user/resource/User#123",
  "type": "rpc.resource",
  "name": "User 123",
  "attributes": {
    "resourceType": "User",
    "key": "123",
    "schemaRef": "schema://user/user@v3"
  },
  "capabilities": ["rpc.cap:watchable"],
  "state": {}
}
```

### 9.2 Watch Semantics (Optional but Strongly Recommended)

If resources can be observed, the endpoint SHOULD implement:

* `rpc.watch({ selector | resourceId, options }) -> subscription`

and MUST then emit:

* `rpc.event:ResourceChanged`

A resource is watchable if it has capability `rpc.cap:watchable`.

### 9.3 ResourceChanged Event (MUST if Watch Implemented)

If watch is supported, emitted events MUST include:

* `type`: `rpc.event:ResourceChanged`
* `source`: the resource id (or a stable source entity)
* `data.changeType`: `"created" | "updated" | "deleted" | "snapshot"`
* `data.patch`: RECOMMENDED RFC 6902 JSON Patch against the resource representation or resource state
* `data.schemaRef`: optional, for the resource representation

Example:

```json
{
  "eventId": "evt-9",
  "type": "rpc.event:ResourceChanged",
  "timestamp": "2026-02-21T12:00:01.000Z",
  "source": "rpc://service/user/resource/User#123",
  "data": {
    "changeType": "updated",
    "patch": [
      { "op": "replace", "path": "/email", "value": "alice@example.com" }
    ],
    "schemaRef": "schema://user/user@v3"
  },
  "meta": { "correlationId": "corr-77", "reliability": "at_least_once" }
}
```

### 9.4 Snapshot-on-Subscribe (RECOMMENDED)

When a watch is established, the endpoint SHOULD emit an initial snapshot with:

* `data.changeType = "snapshot"`

This supports deterministic clients and reduces races.

---

## 10. Service Description and Compatibility

### 10.1 Describe Operation (Read Conformance)

An OmniRPC endpoint claiming **Read Conformance** (§16.1) MUST support discovering services/methods in the graph. It SHOULD also support a richer describe operation.

RECOMMENDED operation:

* `rpc.describe({ serviceId | methodId }) -> descriptor`

The descriptor SHOULD include:

* supported versions,
* schema references,
* compatibility policy,
* deprecations,
* auth requirements,
* error taxonomy references.

### 10.2 Versioning (Normative Requirements)

Services SHOULD declare versions in at least one of these ways:

* `rpc:hasVersion` relation to `rpc.version` entities, and/or
* `attributes.version` on `rpc.service`

Version strings SHOULD follow semantic versioning (e.g., `1.4.2`), but this is not mandated.

### 10.3 Compatibility Policy (MUST if Multiple Versions Exposed)

If a service exposes multiple versions or evolving schemas, it MUST declare a compatibility policy:

* `attributes.compatibility = "backward" | "forward" | "both" | "none" | "unknown"`

Additionally, it SHOULD declare deprecation metadata:

* `attributes.deprecationDate` (ISO date string)
* `attributes.sunsetDate` (ISO date string)

---

## 11. Events and Observability

OmniRPC event types MUST be prefixed `rpc.event:` and use the OGIF event envelope.

### 11.1 Required Events (Minimal)

OmniRPC does not require emitting per-call telemetry by default (it can be sensitive/expensive). However:

* If watch is supported, `rpc.event:ResourceChanged` is REQUIRED (§9.3).
* If errors occur that affect availability, the endpoint MUST expose them via either:

  * OGIF patch events (state changes), and/or
  * `rpc.event:Error` (RECOMMENDED).

### 11.2 Recommended Telemetry Events (Optional)

If the endpoint exposes call telemetry, it SHOULD emit:

* `rpc.event:CallStarted`
* `rpc.event:CallCompleted`
* `rpc.event:CallFailed`

These events SHOULD be capability-gated (see §13.3) and MUST redact sensitive payload data.

### 11.3 Error Event (Recommended)

`rpc.event:Error` payload SHOULD include:

* `severity`
* `messageId`
* `text`
* optional structured `details`

---

## 12. OmniRPC Selectors (`rpc-sel-0`)

Endpoints MUST support `ogif-sel-0`. OmniRPC recommends these conveniences:

* `service(name="Auth")` ? `type("rpc.service") AND name("Auth")`
* `method(name="Login")` ? `type("rpc.method") AND attributes.methodName == "Login"`
* `resource(type="User")` ? `type("rpc.resource") AND attributes.resourceType == "User"`
* `callable()` ? `cap("rpc.cap:callable")`
* `watchable()` ? `cap("rpc.cap:watchable")`

Traversal examples:

* `#rpc://service/auth out("rpc:exposes")` ? methods
* `#rpc://service/user out("rpc:owns")` ? resources

---

## 13. Security Considerations (Normative)

### 13.1 Authentication and Authorization Metadata (MUST for Protected Methods)

If a method requires authentication, it MUST declare:

* `attributes.auth.required = true`

and SHOULD declare:

* `attributes.auth.schemes` (e.g., `["bearer","mtls"]`)
* `attributes.auth.scopes` (e.g., `["user.read"]`)
* `attributes.auth.audience` (string or list)

This metadata is informational; enforcement is done by the endpoint’s security policy.

### 13.2 Redaction and Sensitive Data (MUST)

Endpoints MUST NOT leak secrets through:

* graph snapshots (`ogif.getGraph`),
* events (including telemetry),
* describe results.

Implementations SHOULD support:

* `attributes.sensitiveFields` list for schemas, or
* schema-level sensitivity annotations in the schema registry.

### 13.3 Telemetry Gating (SHOULD)

If call telemetry events are implemented, they SHOULD require explicit authorization/capability such as:

* `rpc.cap:observeCallTelemetry`

And MUST be redacted even when authorized, unless explicitly configured otherwise.

### 13.4 Production Safety (RECOMMENDED)

Production deployments SHOULD:

* restrict `rpc.call` to authorized clients,
* restrict `rpc.watch` to authorized clients,
* avoid emitting payload-bearing events broadly.

---

## 14. Mapping to Common Transports (Informative)

### 14.1 REST/HTTP

* `rpc.service` ˜ API host / service boundary
* `rpc.resource` ˜ REST resource instance (`/users/123`)
* `rpc.method` ˜ endpoint action (`GET /users/{id}`, `POST /login`)
* `rpc.watch` ˜ server-sent events / websocket feed / long polling

### 14.2 gRPC

* `rpc.service` ˜ gRPC service
* `rpc.method` ˜ RPC method
* `callType` aligns directly with unary/streaming modes

### 14.3 Local Module RPC

* `rpc.service` ˜ module boundary
* transport may be stdio, pipes, shared memory, or in-proc bridge
* OmniRPC still provides the introspection and compatibility contract plane

---

## 15. Conformance Levels

### 15.1 OmniRPC-Read Conformance

An endpoint is OmniRPC-Read conformant if it:

* exposes `rpc.service` and `rpc.method` entities,
* links them via `rpc:exposes`,
* provides method metadata including callType and schema refs when available,
* supports OGIF querying to discover methods,
* provides compatibility/version metadata when multiple versions exist.

### 15.2 OmniRPC-Control Conformance

Includes OmniRPC-Read and additionally:

* supports unary method calling via `rpc.call` semantics (or equivalent OGIF invoke op),
* enforces authorization,
* returns typed success/error outcomes deterministically.

### 15.3 OmniRPC-Watch Conformance (Optional, Recommended)

Includes OmniRPC-Control and additionally:

* supports `rpc.watch`,
* emits `rpc.event:ResourceChanged` with snapshot-on-subscribe recommended,
* declares reliability metadata for watch streams.

### 15.4 OmniRPC-Test Conformance (Optional)

Includes OmniRPC-Control and additionally:

* stable IDs or `meta.testTag`,
* deterministic behavior for retries/timeouts when configured for test mode,
* optional test doubles/sandbox endpoints (deployment-defined).

---

## 16. Example (Informative)

### 16.1 Service Graph

Entities:

* `rpc://service/auth` (`rpc.service`)
* `rpc://service/auth#Login` (`rpc.method`)
* `rpc://service/auth#Logout` (`rpc.method`)

Relations:

* `auth rpc:exposes Login`
* `auth rpc:exposes Logout`

A client:

1. queries for `type("rpc.method") AND name("Login")`
2. calls `rpc.call(methodId, args)`
3. watches `rpc://service/user/resource/User#123` if watchable

---

**End of OmniRPC Profile Specification `ogif.profile:omnirpc-0` (Draft)**
