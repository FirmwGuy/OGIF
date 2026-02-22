# OmniTelemetry Profile Specification
## OGIF Profile: Metrics, Logs, Traces, and Correlated Observability Streams

**Profile Name:** OmniTelemetry  
**OGIF Profile ID:** `ogif.profile:omnitel-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Strongly Recommended With:** `ogif.profile:omnipolicy-0` (OmniPolicy)  
**Selector Baseline:** `ogif-sel-0` + OmniTelemetry Selector Extension `tel-sel-0` (defined herein)

---

## 1. Purpose

OmniTelemetry is an OGIF profile that standardizes the **observability plane** of an OGIF endpoint.

It models and exposes:
- **metrics** (counters, gauges, histograms),
- **logs** (structured log records),
- **traces** (trace graphs and spans),
- and the **correlation** between them (traceId/spanId, correlationId).

OmniTelemetry is explicitly **read/observe-oriented**:
- It MUST NOT provide control semantics.
- It MUST NOT be required for correct application behavior.
- It MAY be sampled, rate-limited, or lossy (with declaration).

This profile exists so monitoring, testing, support tooling, and agent auditors can use a **common interface** rather than vendor-specific APM/log APIs.

---

## 2. Design Goals

An OmniTelemetry implementation MUST allow a client to:

1. Discover telemetry sources and instruments (what exists).
2. Query telemetry (pull) and/or subscribe to telemetry (push).
3. Correlate telemetry to operations or sessions via stable identifiers.
4. Apply security guardrails:
   - redaction of secrets/PII,
   - restricted visibility for sensitive logs/traces,
   - rate limits and sampling declarations.
5. Distinguish between **telemetry events** (observations) and **control events** (actions).

---

## 3. Non-goals

OmniTelemetry does NOT standardize:
- storage/retention backends (files, ELK, vendor APM),
- a single mandatory aggregation strategy,
- exact delivery semantics (exactly-once) by default,
- control-plane actions (use OmniDOM/OmniRPC/OmniECS/OmniFlow for control),
- UI stimulus semantics (OmniDOM).

---

## 4. Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

---

## 5. Core Concepts and Conventions

### 5.1 Telemetry is Side-Channel Observation (MUST)
Telemetry emissions MUST NOT be required for correctness of control-plane semantics.
Clients MUST treat telemetry as observational (possibly delayed/sampled).

### 5.2 Resource, Scope, Instrument (Recommended Model)
Telemetry commonly describes:
- **resource**: the emitting process/service/environment
- **scope**: the subsystem/library/module
- **instrument**: the metric/log/trace producer

OmniTelemetry supports this model but does not require a specific internal architecture.

### 5.3 Sampling and Loss Declaration (MUST)
If the endpoint drops, samples, or rate-limits telemetry, it MUST declare this per stream or instrument.

---

## 6. Entity Types

OmniTelemetry defines reserved OGIF entity `type` values.

### 6.1 Required Types (Minimum)
An OmniTelemetry endpoint MUST represent at least one telemetry producer via:

- `telemetry.provider` — a telemetry source (process/service/module)

### 6.2 Metrics Types (Optional but Recommended)
If metrics are supported, the endpoint SHOULD represent:

- `telemetry.instrument` — base instrument entity
- `telemetry.counter`
- `telemetry.gauge`
- `telemetry.histogram`

### 6.3 Logs Types (Optional but Recommended)
If logs are supported, the endpoint SHOULD represent:

- `telemetry.logStream` — a stream/category of log records

### 6.4 Traces Types (Optional but Recommended)
If traces are supported, the endpoint SHOULD represent:

- `telemetry.trace` — a trace container (optional; may be implicit by traceId)
- `telemetry.span` — a span entity (may be query-only or materialized)

---

## 7. Relation Kinds

All relations are directed unless noted.

### 7.1 Reserved Relation Kinds

- `telemetry:emits` (provider ? instrument/logStream/span)  
- `telemetry:inScope` (instrument/logStream/span ? scope entity) (optional)
- `telemetry:inResource` (provider ? resource entity) (optional)
- `telemetry:inTrace` (span ? trace) (optional)
- `telemetry:parentOf` (span ? span) (span parent to child; optional if spans contain parentSpanId instead)

### 7.2 Cross-Profile Correlation (Recommended)
Telemetry should correlate to control-plane activity by linking (when possible) via:

- `meta.correlationId` in events (RECOMMENDED)
- `traceId` / `spanId` fields (RECOMMENDED)
- Optional OGIF relation:
  - `telemetry:correlatesTo` (span/logRecord/metricPoint ? target entity id) (optional; may be high-volume)

Because relations can be high-volume, correlation is primarily done via IDs in payloads, not edges, unless explicitly configured.

---

## 8. Metrics Model

### 8.1 Instrument Attributes (Required if Metrics Supported)

A metrics instrument entity (`telemetry.counter|gauge|histogram`) MUST include:

- `attributes.name` (string; stable)
- `attributes.unit` (string; e.g., `"ms"`, `"bytes"`, `"1"`)
- `attributes.description` (string; optional but recommended)
- `attributes.temporality`:
  - `"cumulative" | "delta" | "unknown"`
- `attributes.valueType`:
  - `"int" | "double" | "unknown"`
- `attributes.dimensions` (array of string keys; optional but recommended)

Example:
```json
{
  "id": "tel://metric/http.server.duration",
  "type": "telemetry.histogram",
  "name": "http.server.duration",
  "attributes": {
    "name": "http.server.duration",
    "unit": "ms",
    "description": "Server request duration",
    "temporality": "delta",
    "valueType": "double",
    "dimensions": ["route", "method", "status"]
  },
  "capabilities": ["telemetry.cap:queryable"],
  "state": {}
}
```

### 8.2 Metric Points (Data Model)

A metric point MUST be representable as:

* `timestamp` (ISO-8601 or epoch ms; endpoint MUST document)
* `value` (number) OR histogram structure
* `attributes` (key-value map of dimension values)
* optional `exemplars` (links to traceId/spanId)

Histogram points SHOULD include:

* `count`, `sum`, and either:

  * `buckets` with explicit boundaries, or
  * deployment-defined histogram encoding.

### 8.3 Temporality Semantics (MUST)

If `temporality="delta"`, points represent changes since last collection interval.
If `temporality="cumulative"`, points represent totals since process start (or reset).

If counters reset, the endpoint MUST either:

* emit a reset indicator, or
* set `meta.reset=true` in points/events, or
* document reset behavior.

---

## 9. Logs Model

### 9.1 Log Stream Attributes (Required if Logs Supported)

A `telemetry.logStream` MUST include:

* `attributes.name` (string; stable)
* optional `attributes.severityMin` (e.g., `"DEBUG"`, `"INFO"`, `"WARN"`, `"ERROR"`)
* optional `attributes.schemaRef` for structured logs

### 9.2 Log Record (Data Model)

A log record MUST be representable as:

* `timestamp`
* `severity` (string or numeric)
* `body` (string or structured object)
* `attributes` (key-value map)
* optional correlation:

  * `traceId`, `spanId`, `correlationId`
* optional `resource` snapshot fields (service name, instance id)

Sensitive fields MUST be redacted by policy (see §13).

---

## 10. Traces Model

### 10.1 Span Attributes (Recommended)

A span SHOULD include:

* `traceId` (string)
* `spanId` (string)
* `parentSpanId` (string|null)
* `name` (string)
* `kind` (e.g., `"server"|"client"|"internal"`)
* `startTime`, `endTime`
* `status` (e.g., `"ok"|"error"`)
* `attributes` (key-value)
* `events` (time-stamped annotations; optional)
* `links` (optional)

Span entity representation is allowed to be **virtual** (returned by query) rather than fully present in the graph snapshot, because traces can be huge.

### 10.2 Trace Graph Semantics (MUST if Traces Supported)

If traces are supported, the endpoint MUST allow reconstructing the span DAG/tree by either:

* providing `parentSpanId` in spans, and/or
* providing `telemetry:parentOf` relations (optional).

---

## 11. Capabilities

OmniTelemetry reserves these capability tokens:

* `telemetry.cap:discoverable` — provider/instrument can be discovered
* `telemetry.cap:queryable` — supports pull queries
* `telemetry.cap:subscribable` — supports push subscriptions
* `telemetry.cap:exportable` — supports exporting batches (optional)
* `telemetry.cap:adminOnly` — marker (policy enforced elsewhere)

---

## 12. Operations

OmniTelemetry operations MAY be implemented via OGIF operation descriptors (`ogif.invoke`) and/or wrapper methods.

### 12.1 Required Operations (If Telemetry Is Exposed)

An endpoint advertising `ogif.profile:omnitel-0` MUST support at least ONE of:

* pull queries, or
* subscriptions.

It MUST advertise which via `ogif.getVersion.features.telemetry` (recommended shape):

```json
"features": {
  "telemetry": {
    "metrics": true,
    "logs": true,
    "traces": true,
    "pull": true,
    "push": true
  }
}
```

### 12.2 Recommended Pull Query Operations

#### 12.2.1 `telemetry.listProviders`

Returns telemetry providers.

#### 12.2.2 `telemetry.listInstruments`

Params:

* optional `providerId`
* optional `kind` in `counter|gauge|histogram|logStream|span`

Returns:

* instrument IDs and metadata summaries.

#### 12.2.3 `telemetry.queryMetrics`

Params (recommended):

* `instrumentId` OR `selector`
* `timeRange`: `{ start, end }`
* `filter.attributes` (key-value predicates; optional)
* `resolution` (optional; server may downsample)
* `limit` (optional)

Returns:

* series of metric points.

#### 12.2.4 `telemetry.queryLogs`

Params:

* `streamId` OR `selector`
* `timeRange`
* `filter` (severity, text contains, attributes)
* `limit`, `cursor` (for pagination)

Returns:

* log records + next cursor.

#### 12.2.5 `telemetry.queryTraces`

Params:

* `timeRange`
* `filter` (service, operation name, status, minDuration, attribute match)
* `limit`, `cursor`

Returns:

* trace summaries (traceId, root span, duration, status).

#### 12.2.6 `telemetry.readTrace`

Params:

* `traceId`

Returns:

* full span set for that trace (subject to policy and size limits).

### 12.3 Recommended Push Subscription Operation

If push is supported, the endpoint SHOULD support:

* `telemetry.subscribe({ types, selector, filter, limits })`
* `telemetry.unsubscribe({ subscriptionId })`

Where `types` can include:

* `"metrics"`, `"logs"`, `"spans"` (or `"traces"`)

Subscriptions MUST be policy-gated and MUST enforce rate/payload limits (§13).

---

## 13. Events

All OmniTelemetry event types MUST be prefixed `telemetry.event:` and use OGIF event envelope semantics.

### 13.1 Recommended Event Types (Push Mode)

If push subscriptions are supported, the endpoint SHOULD emit:

* `telemetry.event:MetricPoint`
* `telemetry.event:LogRecord`
* `telemetry.event:SpanEnded` (or `SpanCompleted`)
* optional:

  * `telemetry.event:SpanStarted`
  * `telemetry.event:TraceSummary`

### 13.2 Event Payload Requirements

#### 13.2.1 MetricPoint

Must include:

* `instrumentId`
* `timestamp`
* `value` or histogram value
* `attributes` dimensions
* optional `exemplar` correlation (traceId/spanId)

#### 13.2.2 LogRecord

Must include:

* `streamId` or `providerId`
* `timestamp`, `severity`, `body`
* optional correlation IDs

#### 13.2.3 SpanEnded

Must include:

* `traceId`, `spanId`, optional `parentSpanId`
* `name`, `startTime`, `endTime`, `status`
* optional `attributes` (may be filtered/redacted)

### 13.3 Sampling and Loss Metadata (MUST)

Telemetry events MUST include, in either:

* the event envelope `meta`, or
* the event `data`,

a declaration when sampling/loss may apply, e.g.:

* `meta.reliability = "best_effort"`
* `data.sampleRate = 0.1`
* `data.droppedCount = 123`

---

## 14. Security and Privacy (Normative)

OmniTelemetry is a common source of data leakage. This section is mandatory.

### 14.1 Policy Enforcement (MUST)

Endpoints MUST enforce authorization for:

* querying logs and traces,
* subscribing to telemetry streams,
* accessing high-cardinality attributes,
* reading full trace payloads.

Using `ogif.profile:omnipolicy-0` is strongly recommended.

### 14.2 Redaction (MUST)

Endpoints MUST support redaction of sensitive fields in:

* log bodies,
* span attributes,
* metric dimension values,
* error messages,
  per policy obligations.

Redaction SHOULD support:

* remove,
* replace with sentinel,
* hash.

### 14.3 Limits (MUST)

Endpoints MUST enforce limits to prevent:

* massive data exfiltration,
* denial of service.

At minimum, enforce:

* `maxResults` for queries,
* `maxEventRatePerSec` for subscriptions,
* `maxPayloadBytes` for event payloads.

### 14.4 Correlation Leakage (SHOULD)

Trace IDs and correlation IDs can be used to infer sensitive activity.
Endpoints SHOULD treat detailed tracing as restricted in production unless explicitly authorized.

---

## 15. OmniTelemetry Selector Extension (`tel-sel-0`)

Endpoints MUST support `ogif-sel-0`. OmniTelemetry recommends these conveniences:

* `provider(name="api")` ? `type("telemetry.provider") AND name("api")`
* `metric(kind="histogram")` ? `type("telemetry.histogram")`
* `metric(name="http.server.duration")` ? `attr("name"=="http.server.duration")`
* `logStream(name="app")` ? `type("telemetry.logStream") AND attr("name"=="app")`
* `span()` ? `type("telemetry.span")` (if spans are materialized)

Traversal:

* `#<providerId> out("telemetry:emits")` ? instruments/streams

---

## 16. Conformance Levels

### 16.1 OmniTelemetry-Discover Conformance

An endpoint is conformant if it:

* exposes at least one `telemetry.provider`,
* exposes discoverable instruments/streams when applicable,
* supports queries or subscriptions and declares which.

### 16.2 OmniTelemetry-Pull Conformance

Includes Discover and additionally:

* supports pull queries for at least one telemetry kind (metrics/logs/traces),
* enforces limits and redaction.

### 16.3 OmniTelemetry-Push Conformance

Includes Discover and additionally:

* supports subscriptions and emits `telemetry.event:*` records,
* declares sampling/loss,
* enforces rate and payload limits.

### 16.4 OmniTelemetry-Full Conformance (Recommended for Operators)

Includes Pull + Push and additionally:

* supports metrics, logs, and traces together,
* supports correlation fields (traceId/spanId/correlationId),
* supports reading full traces with paging/limits.

---

## 17. Informative Mapping Notes

### 17.1 Relationship to “Input Events” in OmniDOM

OmniDOM input events (`dom.event:SetValue`, `dom.event:Activate`) are **control-plane** and can cause side effects.
OmniTelemetry events are **observation-plane** and MUST NOT cause side effects.

### 17.2 Compatibility With Common Observability Standards

This profile intentionally aligns with widely used conceptual models:

* metrics instruments + points,
* structured logs,
* traces/spans with attributes and events,
  but does not mandate a specific vendor or wire format.

---

**End of OmniTelemetry Profile Specification `ogif.profile:omnitel-0` (Draft)**
