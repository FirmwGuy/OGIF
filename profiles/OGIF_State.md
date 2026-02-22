# OmniState Profile Specification
## OGIF Profile: Declarative Desired State, Observed State, Drift, and Reconciliation Controllers

**Profile Name:** OmniState  
**OGIF Profile ID:** `ogif.profile:omnistate-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Strongly Recommended With:** `ogif.profile:omnipolicy-0` (OmniPolicy), `ogif.profile:omnitel-0` (OmniTelemetry)  
**Selector Baseline:** `ogif-sel-0` + OmniState Selector Extension `state-sel-0` (defined herein)

---

## 1. Purpose

OmniState is an OGIF profile that models **declarative control systems** using the reconciliation pattern:

> A client declares a **desired state**.  
> The system continuously measures **observed state** and uses **controllers** to converge observed ? desired.

This profile is intended for:
- infrastructure and orchestration (Kubernetes-like),
- configuration management,
- deployment systems,
- feature flag rollouts,
- autoscalers,
- digital twins and controllers,
- any convergent “control loop” system.

OmniState enables:
- explicit drift detection,
- convergence status and progress,
- idempotent apply semantics,
- structured reconciliation events for auditing and testing,
without forcing imperative RPC workflows.

---

## 2. Design Goals

An OmniState implementation MUST allow a client to:

1. Discover resources, desired specs, observed state, and controllers.
2. Set and update desired state in a versioned, auditable way.
3. Observe drift and convergence progress via events and state changes.
4. Understand what is safe and authorized to change (policy integration).
5. Avoid “imperative drift”: repeated applies should be safe (idempotent intent).
6. Integrate with other profiles by allowing controllers to act upon:
   - OmniRPC services/resources,
   - OmniFlow pipelines,
   - OmniECS worlds/components,
   - etc., while keeping the *declarative* semantics explicit.

---

## 3. Non-goals

OmniState does NOT standardize:
- the internal controller algorithm,
- storage backends and retention policies,
- a single universal schema language (JSON Schema is recommended),
- UI interaction semantics (OmniDOM),
- general tool invocation semantics (OmniRPC/OGIF invoke),
- streaming DAG semantics (OmniFlow),
- tick-based simulation semantics (OmniECS).

---

## 4. Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

---

## 5. Core Concepts

### 5.1 Resource
A **resource** is the thing being controlled (service config, deployment, pipeline topology, world state slice, feature flag rule set).

### 5.2 Desired State
The authoritative declarative specification: “what should be”.

### 5.3 Observed State
Measured current reality: “what is”.

### 5.4 Drift
A difference between desired and observed.

### 5.5 Controller
A reconciliation loop that attempts to converge observed toward desired.

---

## 6. Entity Types

OmniState defines reserved OGIF entity `type` values.

### 6.1 Required Types

An OmniState endpoint MUST represent at least:

- `state.resource` — the controlled object identity
- `state.desired` — the desired state spec for a resource (or resource collection)
- `state.observed` — the observed/measured state for a resource
- `state.controller` — a reconciliation controller

### 6.2 Optional Types (Recommended)

- `state.constraint` — invariant/guard constraint (policy-like, but domain invariants)
- `state.revision` — explicit revision objects (if desired specs are versioned beyond simple integers)
- `state.diff` — explicit diff/drift entity (optional; often emitted in events)
- `state.rollout` — staged rollout controller (feature flags/deployments)
- `state.health` — health check entity (optional; can be embedded in observed state)

---

## 7. Relation Kinds and Structural Constraints

All relations are directed.

### 7.1 Reserved Relation Kinds

- `state:targets` (desired ? resource)  
  Desired spec targets a resource.

- `state:observes` (observed ? resource)  
  Observed state corresponds to a resource.

- `state:controls` (controller ? resource)  
  Controller is responsible for reconciling the resource.

- `state:convergesTo` (observed ? desired) (optional)  
  Observed is intended to converge to desired (often implied).

- `state:constrainedBy` (desired/resource ? constraint) (optional)

- `state:producedRevision` (desired ? revision) (optional)

### 7.2 Cardinality Constraints (MUST)

For each `state.resource`:

- There MUST be at least one `state.desired` that targets it, OR the resource MUST be explicitly marked unmanaged:
  - `resource.attributes.managed=false`

- There MUST be at least one `state.observed` that observes it, unless explicitly declared as “unobservable”:
  - `resource.attributes.observable=false`

- There MUST be at least one `state.controller` that controls it, unless `managed=false`.

Deployments may allow multiple controllers; if so, they MUST declare:
- `resource.attributes.controllerMode = "single"|"multi"`
and define conflict resolution policy (deployment-defined).

---

## 8. Desired State Model

### 8.1 Desired Spec Structure (MUST)

Each `state.desired` MUST include:
- `attributes.schemaRef` (URI) OR a documented schema mechanism
- `state.spec` (object) OR `state.specRef` (URI) if too large

It SHOULD also include:
- `state.revision` (monotonic integer or string)
- `attributes.author` (principal id or display name; may be redacted)
- `attributes.createdAt` (ISO-8601)
- `attributes.lastAppliedAt` (optional)
- `attributes.applyMode`:
  - `"replace"` (full desired spec replaces previous desired spec)
  - `"merge"` (merge semantics; schema-defined)
  - `"patch"` (RFC 6902 patch semantics)

### 8.2 Idempotency of Desired Apply (MUST)

Applying the same desired spec (same revision/spec content) MUST be idempotent:
- it MUST NOT create additional changes beyond reconciliation reattempts,
- it MUST NOT create duplicate resources.

### 8.3 Partial Desired Specs (Optional)
Some systems allow partial intent (e.g., set only replicas, not full deployment spec).
If supported, the endpoint MUST declare `applyMode` and merge semantics clearly and SHOULD prefer schema-defined merging.

---

## 9. Observed State Model

### 9.1 Observed Structure (MUST)

Each `state.observed` MUST include:
- `state.snapshot` (object) OR `state.snapshotRef` (URI)
- `state.observedAt` (ISO-8601)
- `state.status`:
  - `"in_sync" | "drifting" | "converging" | "error" | "unknown"`

It SHOULD also include:
- `state.health` (object; optional)
- `state.lastError` (string|object|null)
- `state.lastControllerRunAt` (ISO-8601; optional)

### 9.2 Drift Representation (MUST)

If `state.status="drifting"` or `"converging"`, the endpoint MUST provide drift information via at least one mechanism:

- `state.driftSummary` (string/object), and/or
- reconciliation/drift events with a diff payload (§12), and/or
- a `state.diff` entity linked to the resource (optional).

Drift payload SHOULD avoid huge diffs by default; provide summaries with optional detailed diff access under policy.

---

## 10. Controller Model

### 10.1 Controller Identity (MUST)

A `state.controller` MUST include:
- `name` (SHOULD)
- `attributes.controllerType` (string; e.g., `deployment`, `autoscaler`, `featureFlag`, `pipelineReconciler`)
- `state.status`:
  - `"running" | "paused" | "error"`

### 10.2 Reconciliation Semantics (MUST)

Controllers MUST:
- periodically (or on change) compare desired vs observed,
- attempt to reduce drift,
- update observed state and status,
- emit reconciliation events (§12).

### 10.3 Pause/Resume (Optional, Security-Sensitive)

If controller pausing is supported, it MUST be capability-gated:
- `state.cap:controllerPausable` (recommended)
and enforced via OmniPolicy.

---

## 11. Capabilities

OmniState reserves capability tokens:

- `state.cap:inspectable`
- `state.cap:desiredWritable` — can set desired specs
- `state.cap:observedReadable`
- `state.cap:controllerManageable` — can pause/resume controllers (optional)
- `state.cap:diffReadable` — can read detailed drift diffs (optional)
- `state.cap:adminOnly` — marker

Capabilities are advertisements; authorization is enforced by policy.

---

## 12. Events

Event types MUST be prefixed `state.event:` and use OGIF event envelopes.

### 12.1 Required Events (Observable Reconciliation)

An OmniState endpoint MUST make reconciliation progress observable via:
- OGIF patch events (`ogif.event:StateChanged` / `EntityChanged` / `GraphChanged`)
and SHOULD also emit the OmniState-specific events below for interoperability.

If OmniState-specific events are emitted, the endpoint MUST emit at least:
- `state.event:DesiredUpdated`
- `state.event:ReconciliationStarted`
- `state.event:ReconciliationSucceeded` OR `state.event:ReconciliationFailed`

### 12.2 Recommended Event Types

- `state.event:DesiredUpdated`
- `state.event:ObservedUpdated`
- `state.event:DriftDetected`
- `state.event:ReconciliationStarted`
- `state.event:ReconciliationProgress`
- `state.event:ReconciliationSucceeded`
- `state.event:ReconciliationFailed`
- `state.event:ConstraintViolated` (if constraints exist)

### 12.3 Event Payload Requirements (Recommended)

#### 12.3.1 DesiredUpdated
```json
{
  "type": "state.event:DesiredUpdated",
  "source": "state://resource/webapp",
  "data": {
    "resourceId": "state://resource/webapp",
    "desiredId": "state://desired/webapp",
    "revision": "42",
    "applyMode": "replace"
  },
  "meta": { "correlationId": "corr-apply-42" }
}
```

#### 12.3.2 DriftDetected

```json
{
  "type": "state.event:DriftDetected",
  "source": "state://resource/webapp",
  "data": {
    "resourceId": "state://resource/webapp",
    "desiredRevision": "42",
    "observedAt": "2026-02-21T12:00:00Z",
    "summary": { "fieldsChanged": 3 },
    "diffRef": "state://diff/webapp/42->obs-99"
  }
}
```

#### 12.3.3 ReconciliationSucceeded

```json
{
  "type": "state.event:ReconciliationSucceeded",
  "source": "state://controller/deployments",
  "data": {
    "resourceId": "state://resource/webapp",
    "desiredRevision": "42",
    "durationMs": 1200,
    "attempt": 2
  }
}
```

#### 12.3.4 ReconciliationFailed

```json
{
  "type": "state.event:ReconciliationFailed",
  "source": "state://controller/deployments",
  "data": {
    "resourceId": "state://resource/webapp",
    "desiredRevision": "42",
    "durationMs": 800,
    "attempt": 1,
    "reasonCode": "state.apply.validation_failed",
    "text": "Invalid image tag"
  }
}
```

---

## 13. Operations

OmniState operations MAY be implemented via OGIF operation descriptors (`ogif.invoke`) and/or wrapper methods.

### 13.1 Reserved Capabilities for Operations

* `state.cap:desiredWritable` ? set/apply desired
* `state.cap:diffReadable` ? read detailed diff
* `state.cap:controllerManageable` ? pause/resume controllers

### 13.2 Required Operations (Control Conformance)

An endpoint claiming **OmniState-Control Conformance** (§16.2) MUST support:

#### 13.2.1 `state.applyDesired`

Sets or updates desired state for a resource.

Params (recommended):

* `resourceId`
* `spec` (object) OR `specRef`
* optional `schemaRef`
* optional `applyMode` (`replace|merge|patch`)
* optional `revision` (client-provided; endpoint may assign if omitted)
* optional `correlationId`

Result:

* `desiredId`
* `revision`

Effects:

* updates/creates `state.desired`
* triggers reconciliation (immediate or scheduled)
* emits `state.event:DesiredUpdated`

#### 13.2.2 `state.getStatus`

Returns a summary of:

* desired revision,
* observed status,
* drift summary,
* last reconcile results.

Params:

* `resourceId`

Result:

* status object.

### 13.3 Recommended Operations

#### 13.3.1 `state.listResources`

Params:

* optional selector
* optional paging

Returns:

* resource IDs and summary.

#### 13.3.2 `state.readObserved`

Returns observed snapshot (subject to policy).

Params:

* `resourceId`
* optional `detailLevel` (`summary|full`)
* optional `cursor` for paging large snapshots

#### 13.3.3 `state.readDesired`

Returns desired spec (subject to policy).

#### 13.3.4 `state.readDiff` (Optional; Requires `state.cap:diffReadable`)

Params:

* `diffId` OR `{ resourceId, desiredRevision }`

Returns:

* drift diff (prefer RFC 6902 patch or structured diff schema).

#### 13.3.5 Controller Controls (Optional; Requires `state.cap:controllerManageable`)

* `state.pauseController({ controllerId })`
* `state.resumeController({ controllerId })`
* `state.triggerReconcile({ resourceId })` (optional)

---

## 14. Drift and Diff Formats

### 14.1 Recommended Diff Format

RFC 6902 JSON Patch is RECOMMENDED as a drift representation:

* patch to apply to observed to become desired, OR
* patch to apply to desired to become observed (endpoint must declare direction).

`diff.attributes.direction` MUST be:

* `"observed_to_desired"` or `"desired_to_observed"`

### 14.2 Large Diffs and Summaries (MUST/SHOULD)

Endpoints MUST provide drift summaries even when full diffs are restricted by:

* size limits,
* policy restrictions.

Full diffs SHOULD be:

* separately retrievable (`state.readDiff`),
* policy-gated (`state.cap:diffReadable`),
* optionally truncated.

---

## 15. Security and Safety (Normative)

### 15.1 Policy Enforcement (MUST)

Applying desired state is powerful. Endpoints MUST enforce authorization for:

* `state.applyDesired`,
* reading full desired/observed snapshots,
* reading diffs,
* controller management.

Using `ogif.profile:omnipolicy-0` is strongly recommended.

### 15.2 Redaction (MUST)

Desired/observed state frequently includes secrets (tokens, keys, PII). Endpoints MUST support:

* marking sensitive fields,
* redacting in snapshots, events, and diffs.

### 15.3 Safe Defaults (RECOMMENDED)

Production endpoints SHOULD:

* expose read-only status broadly (summary level),
* restrict apply operations to trusted controllers/operators,
* restrict detailed diffs and full snapshots.

### 15.4 Auditability (RECOMMENDED)

Endpoints SHOULD emit reconciliation events and (if OmniPolicy audit is enabled) decision events for desired applies.

---

## 16. Conformance Levels

### 16.1 OmniState-Read Conformance

An endpoint is OmniState-Read conformant if it:

* exposes `state.resource`, `state.desired`, `state.observed`, `state.controller`,
* links them via `state:targets`, `state:observes`, `state:controls`,
* provides observed status and drift summaries,
* makes updates observable via OGIF patch events and SHOULD emit OmniState events.

### 16.2 OmniState-Control Conformance

Includes Read and additionally:

* supports `state.applyDesired` and `state.getStatus`,
* enforces idempotency semantics for applies,
* triggers reconciliation and emits reconciliation events.

### 16.3 OmniState-Reconcile Conformance (Recommended)

Includes Control and additionally:

* emits drift detection and reconciliation started/progress/success/fail events,
* provides consistent `attempt` and `durationMs` fields.

### 16.4 OmniState-Test Conformance (Optional)

Includes Reconcile and additionally:

* stable IDs or `meta.testTag`,
* deterministic controller scheduling in test mode (or explicit time control integration),
* reproducible reconciliation outcomes under the same inputs.

---

## 17. OmniState Selector Extension (`state-sel-0`)

Endpoints MUST support `ogif-sel-0`. OmniState recommends convenience selectors:

* `resource()` ? `type("state.resource")`
* `desired()` ? `type("state.desired")`
* `observed()` ? `type("state.observed")`
* `controller()` ? `type("state.controller")`
* `drifting()` ? `type("state.observed") AND state("/status"=="drifting")`
* `converging()` ? `type("state.observed") AND state("/status"=="converging")`

Traversal:

* `#<resourceId> in("state:targets")` ? desired specs
* `#<resourceId> in("state:observes")` ? observed snapshots
* `#<controllerId> out("state:controls")` ? controlled resources

---

## 18. Worked Examples (Informative)

### 18.1 Feature Flag Rollout

* `state.resource`: `flags://resource/searchRanking`
* `state.desired`: desired rollout rules (schemaRef points to flag schema)
* `state.observed`: current applied rule set, status
* `state.controller`: rollout controller

Drift occurs if observed rules differ from desired (partial rollout not complete). Convergence events track rollout progress.

### 18.2 Pipeline Topology as Desired State (OmniFlow Integration)

Desired spec describes module graph.
Controller enforces:

* required connections exist,
* schemas are compatible,
* modules are started.

This is safer than imperative `flow.connect` sequences.

### 18.3 World Configuration (OmniECS Integration)

Desired state describes:

* initial entity set,
* component values,
* game mode constraints.
  Controller reconciles world state (spawn/despawn/patch) to desired under policy and test mode.

---

**End of OmniState Profile Specification `ogif.profile:omnistate-0` (Draft)**
