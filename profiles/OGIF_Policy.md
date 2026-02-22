# OmniPolicy Profile Specification
## OGIF Profile: Permissions, Guardrails, Redaction, Auditing, and Least-Privilege Enforcement

**Profile Name:** OmniPolicy  
**OGIF Profile ID:** `ogif.profile:omnipolicy-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Selector Baseline:** `ogif-sel-0` + OmniPolicy Selector Extension `policy-sel-0` (defined herein)

---

## 1. Purpose

OmniPolicy is an OGIF profile that standardizes **authorization and guardrail enforcement** across OGIF endpoints and profiles.

It defines:
- **who** (principals) can
- do **what** (actions/operations/subscriptions)
- to **which** targets (entities/relations/ops/event streams)
- under **which conditions** (context)
- with **which constraints** (argument constraints, visibility constraints)
- and with **which obligations** (redaction, rate limits, auditing).

OmniPolicy is designed to prevent OGIF from becoming an accidental “root shell” by making least privilege, redaction, and audit **consistent and inspectable**.

---

## 2. Design Goals

An OmniPolicy implementation MUST enable:

1. **Consistent enforcement** of allow/deny decisions for:
   - graph reads (snapshots, entity reads),
   - queries,
   - operation invocation,
   - event subscriptions,
   - profile wrapper methods (e.g., `dom.dispatch`, `rpc.call`).

2. **Fine-grained control** at the level of:
   - entity types/domains,
   - relation kinds,
   - operation IDs,
   - event types,
   - and (optionally) field-level redaction.

3. **Guardrails beyond allow/deny**, including:
   - parameter constraints (ranges, allowlists),
   - result filtering and max limits,
   - rate limits / quotas,
   - redaction transformations,
   - policy-driven event filtering.

4. **Auditability**, including structured decision records (capability-gated).

---

## 3. Non-goals

OmniPolicy does NOT standardize:
- authentication protocols (OAuth, mTLS, etc.) — it consumes the authenticated identity as “principal”.
- a single global policy language for all deployments — it defines a minimum interoperable rule model and allows extensions.
- UI semantics (OmniDOM), streaming semantics (OmniFlow), service semantics (OmniRPC), or simulation semantics (OmniECS).

---

## 4. Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

---

## 5. Core Concepts

### 5.1 Principals
A **principal** is an authenticated actor:
- human user,
- service,
- test harness,
- AI agent session,
- automation client.

### 5.2 Actions
An **action** represents the intent of a request (read, query, invoke, subscribe, etc.). OmniPolicy standardizes action identifiers and allows extensions (§8).

### 5.3 Targets
A **target** is what the request applies to:
- entity IDs,
- relation kinds,
- operation IDs,
- event types,
- selector scopes (query constraints).

### 5.4 Conditions
A **condition** is a predicate over the request context and/or target metadata (environment, time, surface, modality, domain, classification, etc.).

### 5.5 Decisions
A **decision** is the result of policy evaluation:
- allow or deny,
- plus obligations (redaction, limits, audit, transformations).

### 5.6 Disclosure Levels
For read/query/subscribe, policies can choose how much to disclose:

- `none` — target not visible at all
- `existence` — ID/type only (opaque stub)
- `metadata` — ID/type/name/attributes (no state)
- `full` — full entity/event payload subject to redaction obligations

Disclosure levels exist to support “existence-only” visibility and invariant-preserving stubs.

---

## 6. Required Enforcement Scope

An endpoint claiming OmniPolicy enforcement MUST apply OmniPolicy decisions to:

1. **Graph snapshot reads**
   - `ogif.getGraph` and equivalent profile wrappers (e.g., `dom.getTree`).

2. **Entity reads**
   - `ogif.getEntity`, `dom.getNode`, etc.

3. **Queries**
   - `ogif.queryEntities`, `ogif.queryRelations`, and profile query wrappers.

4. **Invocations**
   - `ogif.invoke`, `rpc.call`, `dom.dispatch`, `ecs.patchComponent`, `flow.connect`, `render.getVisibleSet`, time control operations, etc.

5. **Subscriptions**
   - `ogif.subscribe` and profile subscription wrappers.

Enforcement MUST be consistent across transport (stdio, pipe, socket, localhost TCP) and modality (human vs automation vs service), except where explicitly governed by policy conditions.

---

## 7. Data Model

OmniPolicy defines policy objects as OGIF entities. Endpoints MAY enforce policy without exposing the policy graph to all clients; visibility of policy entities is itself policy-governed.

### 7.1 Entity Types (Reserved)

- `policy.principal` — an actor identity
- `policy.role` — a named role grouping permissions
- `policy.permission` — a named permission template (action + scope + constraints)
- `policy.rule` — a conditional rule (allow/deny + obligations + priority)
- `policy.binding` — attaches roles/permissions to principals (optionally conditional)
- `policy.scope` — named scoping object (e.g., “prod”, “test”, “support”, “ci”)
- `policy.decision` — (optional) decision record entity (audit store; may be externalized)

### 7.2 Relation Kinds (Reserved)

All relations are directed:

- `policy:hasRole` (principal ? role)
- `policy:grants` (role ? permission) and/or (principal ? permission)
- `policy:hasBinding` (principal ? binding)
- `policy:bindsRole` (binding ? role)
- `policy:bindsPermission` (binding ? permission)
- `policy:hasRule` (scope ? rule) or (principal/role ? rule)
- `policy:appliesToScope` (rule ? scope)
- `policy:appliesToPermission` (rule ? permission) (optional)
- `policy:producedDecision` (principal ? decision) (optional)

Deployments MAY add namespaced kinds (e.g., `myorg.policy:delegatedBy`).

---

## 8. Action Vocabulary

OmniPolicy standardizes action identifiers to enable portable policies across endpoints.

### 8.1 Core OGIF Actions (Reserved)

These MUST be supported as action identifiers in policy evaluation:

- `ogif.action:readGraph` — `ogif.getGraph`
- `ogif.action:readEntity` — `ogif.getEntity`
- `ogif.action:query` — `ogif.queryEntities` / `ogif.queryRelations`
- `ogif.action:invoke` — `ogif.invoke`
- `ogif.action:subscribe` — `ogif.subscribe`
- `ogif.action:unsubscribe` — `ogif.unsubscribe`

### 8.2 Recommended Profile Actions (Reserved)

Endpoints SHOULD map common profile wrapper methods to these action identifiers when applicable:

**OmniDOM**
- `dom.action:dispatch` — dispatch semantic UI events (e.g., `dom.dispatch`)
- `dom.action:observeInput` — observe sensitive input events (optional gating)

**OmniRPC**
- `rpc.action:call` — call a method (`rpc.call`)
- `rpc.action:watch` — watch resources (`rpc.watch`)

**OmniFlow**
- `flow.action:connect`, `flow.action:disconnect`
- `flow.action:start`, `flow.action:stop`, `flow.action:pause`, `flow.action:resume`
- `flow.action:testInject`, `flow.action:testDrain` (test-only)

**OmniECS**
- `ecs.action:spawn`, `ecs.action:despawn`
- `ecs.action:addComponent`, `ecs.action:removeComponent`, `ecs.action:patchComponent`
- `ecs.action:timeControl` (freeze/step/resume)

**OmniRenderDiag**
- `render.action:pick`
- `render.action:getVisibleSet`
- `render.action:getBounds2D`
- `render.action:testControl` (test-only)

**Time Control Extension**
- `time.action:freeze`, `time.action:resume`, `time.action:advance`, `time.action:stepTicks`, `time.action:setRate`

If an endpoint does not map wrappers to these action identifiers, it MUST still support enforcement via `ogif.action:invoke` by matching on `opId` and/or wrapper method name.

### 8.3 Extensibility
Custom actions MUST be namespaced:
- `myorg.action:exportBillingReport`

---

## 9. Permission and Rule Model

OmniPolicy supports a hybrid RBAC + ABAC model:

- **Roles/permissions** provide baseline allow scopes.
- **Rules** provide conditional overrides, constraints, redaction, and audit obligations.

### 9.1 Permission Entity

A `policy.permission` SHOULD define:

- `attributes.action` (string; one of §8 or namespaced)
- `attributes.targetSelector` (string; OGIF selector describing the permission’s scope)
- optional `attributes.opIdPattern` (string; glob `*` allowed)
- optional `attributes.eventTypePattern` (string; glob `*` allowed)
- optional `attributes.disclosure` (`none|existence|metadata|full`)
- optional `attributes.argConstraints` (object; see §9.4)
- optional `attributes.obligations` (object; see §10)

Example:
```json
{
  "id": "policy://perm/ui-interact",
  "type": "policy.permission",
  "name": "UI Interaction (User-Equivalent)",
  "attributes": {
    "action": "dom.action:dispatch",
    "targetSelector": "type(\"dom.node\")",
    "disclosure": "full",
    "obligations": {
      "audit": { "required": true, "level": "summary" }
    }
  }
}
```

### 9.2 Rule Entity

A `policy.rule` expresses conditional allow/deny with priority and obligations.

A rule SHOULD define:

* `attributes.effect` = `"allow"` or `"deny"`
* `attributes.priority` (integer; higher wins; default 0)
* `attributes.action` (string; optional; if omitted applies to any action)
* `attributes.targetSelector` (string; optional; if omitted applies to any target)
* optional `attributes.opIdPattern` and `attributes.eventTypePattern`
* optional `attributes.conditions[]` (see §9.3)
* optional `attributes.disclosure` (overrides baseline disclosure)
* optional `attributes.argConstraints` (see §9.4)
* optional `attributes.obligations` (see §10)

Example:

```json
{
  "id": "policy://rule/deny-prod-timecontrol",
  "type": "policy.rule",
  "name": "Deny Time Control in Production",
  "attributes": {
    "effect": "deny",
    "priority": 100,
    "action": "time.action:*",
    "conditions": [
      { "kind": "equals", "path": "context.environment", "value": "prod" }
    ]
  }
}
```

### 9.3 Condition Model (Minimum)

Conditions are evaluated against a **request context** object and (optionally) target metadata.

OmniPolicy defines a minimal portable condition set:

* `equals(path, value)`
* `in(path, [values...])`
* `matches(path, regex)` (RECOMMENDED)
* `exists(path)` (RECOMMENDED)
* numeric comparisons: `lt`, `lte`, `gt`, `gte` (RECOMMENDED)

`path` uses dotted traversal into the evaluation context (e.g., `context.environment`, `principal.kind`, `target.domain`, `request.opId`).

Deployments MAY add richer condition types (namespaced).

### 9.4 Argument Constraints (Guardrails)

Argument constraints restrict invocations beyond allow/deny.

OmniPolicy supports two portable constraint forms:

1. **JSON Schema constraint** (RECOMMENDED):

* `attributes.argConstraints.schema` (inline JSON Schema) OR
* `attributes.argConstraints.schemaRef` (URI)

2. **Simple field constraints** (minimum):

* `attributes.argConstraints.fields[]` items like:

  * `{ "path": "args.volume", "min": 0, "max": 1 }`
  * `{ "path": "args.mode", "allow": ["safe","normal"] }`
  * `{ "path": "args.name", "matches": "^[a-z0-9_-]{1,32}$" }`

If constraints are present and violated, the request MUST be rejected as “policy denied” (§12).

---

## 10. Obligations and Transformations

If a request is allowed, a policy decision may impose obligations. Endpoints MUST enforce obligations.

### 10.1 Obligation Types (Reserved)

#### 10.1.1 Redaction

`obligations.redact[]` entries:

* `path` (JSON Pointer; e.g., `/state/value`)
* `mode`: `"remove"|"replace"|"hash"`
* `replacement` (if replace)
* `hashAlg` (if hash; e.g., `"sha256"`; deployment-defined)

Example:

```json
"obligations": {
  "redact": [
    { "path": "/state/value", "mode": "remove" }
  ]
}
```

#### 10.1.2 Result Limits

`obligations.limits`:

* `maxEntities` (int)
* `maxRelations` (int)
* `maxResults` (int; for queries)
* `maxEventRatePerSec` (number; for subscriptions)
* `maxPayloadBytes` (int; for events/responses)

#### 10.1.3 Filtering

`obligations.filter`:

* `entitySelector` (string) to intersect with query results
* `eventTypeAllowlist` / `eventTypeDenylist` (glob patterns)
* `relationKindAllowlist` / `relationKindDenylist`

#### 10.1.4 Auditing

`obligations.audit`:

* `required` (boolean)
* `level`: `"none"|"summary"|"detailed"` (detailed MUST remain redacted)

#### 10.1.5 Challenge/Step-Up (Optional)

`obligations.challenge` MAY request additional verification (MFA, break-glass). Actual mechanisms are deployment-defined.

---

## 11. Policy Evaluation Interface

### 11.1 Request Context (Minimum Required Fields)

When evaluating a request, the endpoint MUST construct an evaluation context with at least:

* `principal.id` (string)
* `principal.kind` (string; recommended values: `human|service|automation|agent`)
* `request.action` (string; §8)
* `request.targetIds` (array of ids; may be empty for global operations)
* `request.selector` (string; for queries/subscriptions; optional)
* `request.opId` (string; for invocations; optional)
* `request.eventTypes` (array of strings; for subscriptions; optional)
* `request.args` (object; for invocations; optional; may be redacted in audit)
* `context.environment` (string; recommended: `prod|staging|dev|test`)
* `context.transport` (string; e.g., `stdio|pipe|unix_socket|named_pipe|tcp`)
* `context.surface` (string; recommended: `user_equivalent|privileged|support|ci`) (optional but strongly recommended)
* `context.time` (ISO-8601 string; optional)

Endpoints MAY include additional fields (client IP, device, session id, locale), but MUST avoid placing secrets in context.

### 11.2 Decision Result

Policy evaluation produces:

* `effect`: `allow|deny`
* `disclosure`: `none|existence|metadata|full` (for read/query/subscribe)
* `obligations`: object (possibly empty)
* `decisionId`: stable within a session (optional but recommended)
* `reasonCode`: stable string (recommended; minimal leakage)

### 11.3 Combining Algorithm (MUST)

OmniPolicy uses this default combining algorithm unless the endpoint explicitly advertises an alternative:

1. Collect all applicable rules and permissions for the principal.
2. Evaluate conditions for each candidate rule.
3. Determine the maximum `priority` among applicable candidates.
4. Consider only candidates at that maximum priority.
5. If any candidate at that priority is `deny`, the decision is **deny**.
6. Otherwise, if at least one is `allow`, decision is **allow**.
7. If no applicable allow, decision is **deny** (default deny).

Obligations and constraints from all applicable allow candidates at the winning priority MUST be combined conservatively:

* redactions are unioned,
* maximums are minimized (most restrictive),
* allowlists are intersected, denylists are unioned.

---

## 12. Enforcement Semantics by Request Type

### 12.1 Reads and Queries (Graph/Entity/Query)

If a request is denied, the endpoint MUST:

* fail the request with an authorization error (§12.5), OR
* return an empty result only if explicitly configured by policy (discouraged; must be explicit).

If allowed, the endpoint MUST apply disclosure and redaction:

* `disclosure=none`: target(s) MUST be omitted entirely.
* `disclosure=existence`: return opaque stub(s) containing only `id` and `type`, and MAY include `attributes.redacted=true`.
* `disclosure=metadata`: include `id`, `type`, `name`, `attributes`, but MUST omit `state`.
* `disclosure=full`: include full entity, then apply redaction obligations.

#### 12.1.1 Referential Integrity (MUST)

If an included entity references an omitted entity (via relations), the endpoint MUST ensure responses remain coherent by one of:

* omitting the relation,
* or replacing the referenced entity with an `existence` stub.

Which strategy is used SHOULD be consistent within an endpoint and MAY be policy-configured.

### 12.2 Invocations (Operations)

If denied, the invocation MUST NOT execute any side effects.

If allowed, the endpoint MUST:

* validate argument constraints (if any),
* apply rate limits/quotas (if any),
* apply audit obligations,
* and (if relevant) enforce additional target restrictions (e.g., only visible objects).

If argument constraints fail, the endpoint MUST reject as policy denied (§12.5).

### 12.3 Subscriptions (Events)

If denied, the subscription MUST NOT be established.

If allowed, the endpoint MUST:

* filter event types per allow/deny lists,
* apply max rate and payload limits,
* redact event payload fields per obligations,
* and enforce visibility constraints (no events about hidden targets).

### 12.4 Profile Invariants (Important)

Some profiles impose structural invariants:

* OmniDOM requires a strict tree.
* OmniFlow may require valid port connectivity.
* OmniECS requires component attachment constraints.

When policy filtering removes entities, the endpoint MUST ensure that any profile-specific response format remains valid under the profile’s rules, by pruning or stubbing consistently.

### 12.5 Standard Denial Error

When a request is denied by policy, the endpoint MUST return an authorization error consistent with OGIF core:

* Error code: `-32004` (operation not permitted)

The error payload SHOULD include:

* `reasonCode: "policy.denied"`
* optional `decisionId` (if safe)
* MUST NOT include sensitive policy internals by default.

---

## 13. Auditing and Decision Events (Optional but Recommended)

### 13.1 Decision Event Type

If auditing is enabled and the subscriber is authorized, the endpoint SHOULD emit:

* `policy.event:Decision`

with payload (recommended):

* `decisionId`
* `principalId` (or a stable pseudonym)
* `action`
* target summary (IDs may be truncated)
* `effect`
* obligation summary (redactions/limits flags)
* `correlationId` (if present)

This event is security-sensitive and MUST be policy-gated.

### 13.2 Decision Storage (Optional)

Endpoints MAY represent decision records as entities of type `policy.decision`.
Whether decisions are stored, and retention policies, are deployment-defined.

---

## 14. Required Operations

OmniPolicy primarily defines enforcement semantics. Introspection is optional because policy graphs can be sensitive.

### 14.1 Required for OmniPolicy-Enforcement Conformance

* No additional methods are required beyond OGIF core.
  (Enforcement is applied to OGIF calls.)

However, endpoints MUST advertise `ogif.profile:omnipolicy-0` and SHOULD advertise feature flags:

```json
"features": {
  "policyEnforced": true,
  "policyModelVisible": false
}
```

### 14.2 Optional Introspection Operations (Policy-Introspection Conformance)

Endpoints MAY provide:

* `policy.whoami` ? returns principal identity summary
* `policy.listRoles`, `policy.listPermissions`
* `policy.explain({ action, target, opId, eventTypes, context })` ? returns decision + reasons (capability-gated)

If `policy.explain` exists, it MUST be strongly authorization-gated and SHOULD redact sensitive internal details.

---

## 15. OmniPolicy Selector Extension (`policy-sel-0`)

Endpoints MUST support `ogif-sel-0`. OmniPolicy recommends convenience selectors:

* `principal(kind="human")` ? `type("policy.principal") AND attr("kind"=="human")`
* `role(name="Admin")` ? `type("policy.role") AND name("Admin")`
* `permission(action="ogif.action:invoke")` ? `type("policy.permission") AND attr("action"=="ogif.action:invoke")`
* `rule(effect="deny")` ? `type("policy.rule") AND attr("effect"=="deny")`

---

## 16. Security Considerations (Normative)

### 16.1 Default Deny (MUST)

If there is no applicable allow permission/rule, the endpoint MUST deny.

### 16.2 Policy Confidentiality (MUST)

Policy definitions, bindings, and decision explanations can leak security posture. Endpoints MUST treat policy entities as sensitive and MUST apply policy enforcement to policy introspection itself.

### 16.3 No “Capability = Authorization” Confusion (MUST)

OGIF `capabilities[]` are advertisements. Authorization decisions MUST be made by OmniPolicy evaluation, not by capability presence alone.

### 16.4 Production Hardening (RECOMMENDED)

In production, endpoints SHOULD:

* restrict privileged operations (time control, pipeline rewiring, ECS spawn/despawn),
* restrict render diagnostics (anti-wallhack),
* restrict observation of sensitive input events,
* and minimize verbose decision explanations.

---

## 17. Conformance Levels

### 17.1 OmniPolicy-Enforcement Conformance (Core)

An endpoint is conformant if it:

* enforces allow/deny for OGIF reads/queries/invokes/subscriptions,
* applies disclosure levels and redaction obligations,
* supports default deny and the combining algorithm (§11.3),
* returns standard denial errors (§12.5).

### 17.2 OmniPolicy-Audit Conformance (Recommended)

Includes enforcement and additionally:

* emits `policy.event:Decision` (authorized subscribers only),
* respects audit redaction requirements.

### 17.3 OmniPolicy-Introspection Conformance (Optional)

Includes enforcement and additionally:

* exposes policy entities (`policy.*`) for authorized clients,
* supports `policy.whoami` and/or `policy.explain` (capability-gated).

---

## 18. Worked Examples (Informative)

### 18.1 “User-Equivalent UI Automation” (OmniDOM)

* Allow: `dom.action:dispatch` to `type("dom.node")`
* Deny: any operation matching `time.action:*` in prod
* Redact: `/state/value` for nodes with `attributes.sensitive=true`

### 18.2 “Support Tooling” (Read-only + Safe RPC)

* Allow: `ogif.action:readGraph`, `ogif.action:readEntity`, `ogif.action:query` (metadata disclosure)
* Allow: `rpc.action:call` only where `targetSelector` matches `rpc.method` with `attributes.methodName` in allowlist (`Health`, `Status`)
* Deny: `ecs.action:*`, `flow.action:*`, `render.action:*`

### 18.3 “Anti-Cheat Render Diagnostics”

* Allow: `render.action:pick` but filter hits to objects with `attributes.visibility="public"`
* Deny: `render.action:getVisibleSet` in production for non-admin principals

### 18.4 “AI Agent Tool Scope”

* Principal kind: `agent`
* Allow: `rpc.action:call` only for a small set of safe tool methods
* Deny: any `flow.action:testInject`, `ecs.action:spawn`, `time.action:*`
* Audit required, with redacted args and results

---

**End of OmniPolicy Profile Specification `ogif.profile:omnipolicy-0` (Draft)**
