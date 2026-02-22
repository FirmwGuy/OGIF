# OmniAgent Profile Specification
## OGIF Profile: Agent Sessions, Goals, Context, Actions, Observations, Tool Use, and Safety Interventions

**Profile Name:** OmniAgent  
**OGIF Profile ID:** `ogif.profile:omniagent-0`  
**Profile Version:** 0.1.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-21  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Recommended With:** `ogif.profile:omnipolicy-0` (OmniPolicy), `ogif.profile:omnirpc-0` (OmniRPC), `ogif.ext:timecontrol-0` (Time Control)  
**Selector Baseline:** `ogif-sel-0` + OmniAgent Selector Extension `agent-sel-0` (defined herein)

---

## 1. Purpose

OmniAgent is an OGIF profile for representing and interfacing with **AI agents** (and agent-like automation systems) as a graph of:

- **agents** and **sessions**,
- **messages** and **goals**,
- **context items** (documents, constraints, memory references),
- **plans/steps** (optional but test-useful),
- **actions** (including tool calls),
- **observations** (tool results, environment feedback),
- **outputs** and **artifacts**,
- **safety interventions** (blocks, redactions, refusals).

OmniAgent standardizes the **observable decision record** of an agent run while explicitly **not requiring** exposure of internal reasoning traces.

It is designed to support:
- safe orchestration,
- tool integration (typically via OmniRPC),
- auditing and guardrails (typically via OmniPolicy),
- deterministic testing hooks (optional, capability-gated),
- and multi-agent scenarios.

---

## 2. Design Goals

An OmniAgent endpoint MUST enable a client to:

1. **Discover** agent(s), sessions, and the state of a session.
2. **Provide input** (user/system messages, goals, context items) in a structured way.
3. **Observe** what the agent does via structured events and state changes:
   - actions started/completed,
   - tool calls requested and their results (when authorized),
   - outputs produced and artifacts created,
   - safety interventions and policy blocks.
4. **Integrate tools** in one of two interoperable ways:
   - **Integrated tools:** agent directly calls tools (via OmniRPC or equivalent).
   - **Delegated tools:** agent requests tool calls and an orchestrator executes them and returns results.
5. **Support least privilege** and redaction for sensitive data.
6. **Enable testing** of behavioral invariants without relying on exact text reproduction.

---

## 3. Non-goals

OmniAgent does NOT standardize:
- model internals or weights,
- training processes,
- prompt formats,
- a universal “chain-of-thought” introspection API,
- UI interaction trees (OmniDOM), streaming DAGs (OmniFlow), or declarative reconciliation (OmniState).

OmniAgent is compatible with those profiles via OGIF cross-links.

---

## 4. Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

---

## 5. Privacy and Reasoning Exposure

### 5.1 No Requirement to Expose Internal Reasoning (MUST NOT)
OmniAgent endpoints MUST NOT be required to expose internal model reasoning traces.

### 5.2 Observable Decision Record (MUST)
Endpoints MUST expose an **observable decision record** sufficient for:
- auditing,
- testing invariants,
- understanding tool usage,
- and tracking outputs/artifacts,
without revealing private internal reasoning.

This record consists of:
- goals (as provided/updated),
- selected actions and tool calls (or tool call requests),
- observations used (by reference),
- outputs and artifacts,
- safety interventions and policy blocks (with reason codes).

### 5.3 Optional Debug Trace (MAY, Strongly Gated)
Endpoints MAY provide a deeper debug trace ONLY if:
- explicitly capability-gated (e.g., `agent.cap:debugTrace`),
- explicitly enabled in configuration,
- and protected by OmniPolicy enforcement.

Even in debug mode, endpoints SHOULD prefer structured traces over raw internal text.

---

## 6. Entity Types

OmniAgent defines reserved OGIF entity `type` values.

### 6.1 Required Types

An OmniAgent endpoint MUST represent at least:

- `agent.agent` — an agent instance (identity + capabilities)
- `agent.session` — a run/context for an agent (task or conversation)

### 6.2 Recommended Types

Endpoints SHOULD represent, when applicable:

- `agent.message` — an input or output message turn
- `agent.goal` — a declared objective
- `agent.contextItem` — a context entry (doc ref, snippet, constraint, memory ref)
- `agent.action` — an action taken (tool call, internal step, external effect request)
- `agent.observation` — a result received (tool output, environment feedback)
- `agent.output` — a produced response (text/audio/structured)
- `agent.artifact` — a persistent output (file, patch, dataset, report)
- `agent.plan` and `agent.planStep` — optional planning representation
- `agent.safetyEvent` — an explicit safety intervention record (optional; may also be an event-only)

---

## 7. Relation Kinds

All relations are directed unless otherwise specified.

### 7.1 Reserved Relation Kinds

- `agent:inSession` (message/goal/context/action/observation/output/artifact ? session)
- `agent:hasMessage` (session ? message)
- `agent:hasGoal` (session ? goal)
- `agent:hasContext` (session ? contextItem)
- `agent:hasPlan` (session ? plan) (optional)
- `agent:hasStep` (plan ? planStep) (optional)
- `agent:executes` (planStep ? action) (optional)
- `agent:produced` (action ? observation)
- `agent:producedOutput` (session or action ? output)
- `agent:producedArtifact` (session or action ? artifact)

### 7.2 Tool Integration Relations (Recommended)

When tools are represented as OmniRPC methods, the endpoint SHOULD link:

- `agent.action --agent:usesTool--> rpc.method`

Where `agent.action.attributes.toolMethodId` MUST match the `rpc.method` entity id if both exist.

### 7.3 Context Usage Relations (Recommended)

To make behavior testable without exposing internal reasoning, endpoints SHOULD link:

- `agent.action --agent:usedContext--> agent.contextItem`
- `agent.output --agent:groundedIn--> agent.contextItem` (optional)

These links MAY be coarse-grained (by item id only), and MUST NOT leak sensitive content when redaction is required.

---

## 8. Core State and Attributes

### 8.1 `agent.agent` Fields (Recommended)

`agent.agent` SHOULD expose:

- `attributes.displayName` (string)
- `attributes.modalities` (e.g., `["text","audio"]`)
- `attributes.supportsTools` (boolean)
- `attributes.toolMode` = `"integrated" | "delegated" | "none"`
- `attributes.supportsPlanning` (boolean)
- `attributes.supportsArtifacts` (boolean)

`agent.agent` capabilities MAY include:
- `agent.cap:createSession`
- `agent.cap:acceptMessages`
- `agent.cap:acceptGoals`
- `agent.cap:acceptContext`
- `agent.cap:produceArtifacts`
- `agent.cap:requestToolCalls` (delegated mode)
- `agent.cap:callToolsDirectly` (integrated mode)
- `agent.cap:pauseResume` (optional)
- `agent.cap:debugTrace` (optional; privileged)

### 8.2 `agent.session` State (MUST)

Each `agent.session` MUST include:

- `state.status` in:
  - `created`
  - `running`
  - `waiting_for_input`
  - `waiting_for_tool`
  - `paused`
  - `completed`
  - `failed`
  - `canceled`

And SHOULD include:
- `state.turn` (integer; monotonic)
- `state.lastActivity` (ISO-8601)
- `state.modelRef` (string; model identifier/version)
- `state.policyScopeRef` (optional link to policy scope/binding)
- `state.seed` (optional; for determinism)
- `attributes.environment` (`prod|staging|dev|test`) (recommended)

### 8.3 Sensitive Data Marking (MUST)

Messages/context items that may contain secrets or PII MUST be markable:

- `attributes.sensitive = true`

When `attributes.sensitive=true`, the endpoint MUST support redaction in snapshots/events per OmniPolicy obligations.

### 8.4 Trust and Origin Labels (RECOMMENDED)

To support prompt-injection defenses and provenance:

`agent.contextItem` SHOULD include:
- `attributes.origin` = `user|system|external|tool|memory`
- `attributes.trust` = `trusted|untrusted|unknown`
- `attributes.classification` = `public|internal|confidential|secret` (optional)

These are metadata for guardrails; enforcement is typically via OmniPolicy and agent implementation.

---

## 9. Messages, Goals, and Context Items

### 9.1 `agent.message` (Recommended)

A message SHOULD include:
- `attributes.role` = `user|assistant|system|tool`
- `state.content` (string or structured payload)
- `attributes.contentType` (e.g., `text/plain`, `application/json`)
- `attributes.messageId` (stable id within session; or use entity id)
- `meta.testTag` (optional)

### 9.2 `agent.goal` (Recommended)

A goal SHOULD include:
- `state.text` (goal statement) OR `state.spec` (structured goal)
- `state.status` = `active|completed|blocked|canceled`
- `attributes.priority` (int; optional)

### 9.3 `agent.contextItem` (Recommended)

A context item SHOULD include:
- `attributes.kind` = `documentRef|snippet|constraint|memoryRef|toolOutputRef|policyRef`
- `attributes.schemaRef` (optional)
- `state.content` (optional inline content; may be redacted)
- OR `state.contentRef` (URI or entity id reference)

If content is large, endpoints SHOULD use `contentRef` rather than inline content.

---

## 10. Actions and Observations

### 10.1 `agent.action` (Recommended)

An action represents a meaningful agent step that may cause external effects.

`agent.action` SHOULD include:
- `attributes.actionType`:
  - `tool_call`
  - `write_artifact`
  - `ask_user`
  - `emit_output`
  - `internal_step` (optional; should be coarse)
- `state.status` = `planned|started|completed|failed|canceled`
- `attributes.toolMethodId` (if tool_call)
- `state.args` (tool args; may be redacted)
- `meta.correlationId` (recommended)

### 10.2 `agent.observation` (Recommended)

An observation represents the result of an action or an external event.

`agent.observation` SHOULD include:
- `attributes.kind` = `tool_result|user_reply|environment_signal|error`
- `state.result` (structured; may be redacted)
- `attributes.resultSchemaRef` (optional)
- `meta.correlationId` (match the originating action if applicable)

---

## 11. Tool Use Modes

OmniAgent supports two interoperable modes.

### 11.1 Integrated Tool Mode (Agent Calls Tools Directly)

- The agent executes tool calls internally (e.g., via OmniRPC).
- The endpoint emits action/observation events describing the tool call and result.
- Policy MUST restrict which tools/methods can be called (typically via OmniPolicy on `rpc.action:call` and/or agent tool binding rules).

### 11.2 Delegated Tool Mode (Agent Requests Tool Calls)

In delegated mode:
1. Agent emits `agent.event:ToolCallRequested` describing the desired tool call.
2. Orchestrator executes the tool (often via OmniRPC).
3. Orchestrator submits the tool result back using `agent.submitObservation` (or equivalent).
4. Agent resumes.

This mode enables strong separation of duties, auditing, and safer execution.

Endpoints MUST declare which mode(s) they support via `agent.agent.attributes.toolMode`.

---

## 12. Events

All OmniAgent event types MUST be prefixed `agent.event:` and use the OGIF event envelope.

### 12.1 Required Event Types

An endpoint claiming OmniAgent-Read Conformance (§16.1) MUST emit events sufficient to observe session progression. At minimum it MUST emit:

- `agent.event:SessionStateChanged`
- `agent.event:OutputProduced` (or equivalent event that indicates user-visible output)
- and MUST also emit OGIF patch events for entity state changes.

If tools are used (integrated or delegated), the endpoint MUST also emit:
- `agent.event:ActionStarted`
- `agent.event:ActionCompleted` or `agent.event:ActionFailed`

### 12.2 Recommended Event Types

- `agent.event:SessionCreated`
- `agent.event:MessageReceived`
- `agent.event:GoalUpdated`
- `agent.event:ContextUpdated`
- `agent.event:PlanUpdated` (if planning exposed)
- `agent.event:ToolCallRequested` (delegated mode)
- `agent.event:ObservationReceived`
- `agent.event:ArtifactCreated`
- `agent.event:SafetyIntervention`

### 12.3 Event Payload Requirements (Recommended)

#### 12.3.1 SessionStateChanged
```json
{
  "type": "agent.event:SessionStateChanged",
  "source": "agent://session/abc",
  "data": { "from": "running", "to": "waiting_for_tool", "turn": 7 }
}
```

#### 12.3.2 ToolCallRequested (Delegated Mode)

```json
{
  "type": "agent.event:ToolCallRequested",
  "source": "agent://session/abc",
  "data": {
    "actionId": "agent://session/abc/action/42",
    "toolMethodId": "rpc://service/web#search",
    "args": { "query": "OGIF profile list" },
    "correlationId": "corr-42"
  }
}
```

#### 12.3.3 SafetyIntervention

```json
{
  "type": "agent.event:SafetyIntervention",
  "source": "agent://session/abc",
  "data": {
    "kind": "blocked_tool_call",
    "reasonCode": "policy.denied",
    "actionId": "agent://session/abc/action/42",
    "messageId": "agent.tool_not_allowed",
    "text": "This tool is not permitted in the current scope."
  }
}
```

---

## 13. Operations

OmniAgent operations MAY be exposed via OGIF operation descriptors (`ogif.invoke`) and/or via wrapper methods.

### 13.1 Reserved Capabilities (For Gating)

* `agent.cap:createSession`
* `agent.cap:acceptMessages`
* `agent.cap:acceptGoals`
* `agent.cap:acceptContext`
* `agent.cap:pauseResume` (optional)
* `agent.cap:requestToolCalls` (delegated mode)
* `agent.cap:submitObservations` (delegated mode)
* `agent.cap:debugTrace` (optional)
* `agent.cap:adminOnly` (marker)

Authorization MUST be enforced by OmniPolicy (recommended) or equivalent.

### 13.2 Required Operations (Control Conformance)

An endpoint claiming OmniAgent-Control Conformance (§16.2) MUST support:

#### 13.2.1 `agent.createSession`

Creates a new session bound to an agent.

Params (recommended):

* `agentId`
* optional `initialGoals[]`
* optional `initialContext[]`
* optional `options` (modelRef, environment, toolMode preference)

Returns:

* `sessionId`

#### 13.2.2 `agent.sendMessage`

Adds a message to a session (user/system/tool).

Params:

* `sessionId`
* `role` = `user|system|tool`
* `content` (string or structured)
* optional `contentType`
* optional `sensitive` flag

Effects:

* Increments `state.turn` (recommended)
* Updates session state accordingly

#### 13.2.3 `agent.run`

Requests the agent to continue processing a session until it needs input/tool or completes.

Params:

* `sessionId`
* optional `until` = `waiting_for_input|waiting_for_tool|completed|failed`
* optional `maxSteps` (safety bound)

Result:

* current session state summary

This operation MUST NOT block indefinitely; it MUST respect `maxSteps` or timeouts.

### 13.3 Delegated Tool Result Submission (Required if Delegated Tool Mode)

If the agent supports delegated tool mode, it MUST support:

#### 13.3.1 `agent.submitObservation`

Params:

* `sessionId`
* `actionId` (the requested tool call action id)
* `kind` = `tool_result|error`
* `result` (structured; may be redacted per policy)
* optional `resultSchemaRef`
* `correlationId` (should match)

Effects:

* Creates/updates an `agent.observation` entity and links it:

  * `action --agent:produced--> observation`
* Emits `agent.event:ObservationReceived`

### 13.4 Optional Operations

* `agent.setGoal`, `agent.addContextItem`, `agent.removeContextItem`
* `agent.pause`, `agent.resume` (if supported)
* `agent.requestPlan` (if planning is exposed)
* `agent.cancelSession`

### 13.5 Suggested JSON-RPC Wrapper Names (Informative)

If using JSON-RPC, endpoints SHOULD expose:

* `agent.createSession`
* `agent.sendMessage`
* `agent.run`
* `agent.submitObservation` (delegated mode)

All must remain expressible via OGIF operation descriptors for tool interoperability.

---

## 14. Safety, Guardrails, and Policy Integration

### 14.1 OmniPolicy Integration (Strongly Recommended)

Endpoints SHOULD implement `ogif.profile:omnipolicy-0` and enforce it for:

* tool calls (integrated mode) and tool call requests (delegated mode),
* access to sensitive context items,
* subscription to agent events containing sensitive payloads,
* debug trace access.

### 14.2 Prompt Injection and Untrusted Context (Recommended Semantics)

The protocol supports marking context items as `trust=untrusted`. Endpoints SHOULD:

* treat untrusted context as data, not authority,
* ensure policy constraints and system instructions cannot be overridden by untrusted items,
* make safety interventions observable via `agent.event:SafetyIntervention` and/or policy decision events (if enabled).

### 14.3 Redaction (MUST)

Sensitive content in:

* messages,
* tool arguments/results,
* context items,
* artifacts

MUST be redacted in snapshots and events according to policy obligations. Endpoints MUST NOT leak secrets by default.

---

## 15. Determinism and Testing (Optional, Recommended)

AI behavior is often nondeterministic; OmniAgent focuses on testable **invariants**.

### 15.1 Stable Identity (Recommended)

In test mode, endpoints SHOULD provide stable IDs or `meta.testTag` for:

* sessions,
* actions,
* artifacts.

### 15.2 Seed Control (Optional)

If the endpoint supports seeded sampling, it SHOULD:

* expose `session.state.seed`
* provide an operation `agent.setSeed({ sessionId, seed })`
* advertise `features.agentSeed = "agent-seed-0"`

### 15.3 Time Control Integration (Optional)

If `ogif.ext:timecontrol-0` is present, a clock MAY control agent scheduling/step boundaries for deterministic harnesses.

---

## 16. Conformance Levels

### 16.1 OmniAgent-Read Conformance

An endpoint is OmniAgent-Read conformant if it:

* exposes `agent.agent` and `agent.session`,
* emits session state changes and output production events,
* allows observing session progression via events and OGIF patches,
* supports redaction for sensitive data.

### 16.2 OmniAgent-Control Conformance

Includes Read and additionally:

* supports `agent.createSession`, `agent.sendMessage`, `agent.run`,
* enforces authorization and guardrails.

### 16.3 OmniAgent-Tool Conformance (Optional, Recommended)

Includes Control and additionally:

* supports either integrated or delegated tool mode, and declares which,
* emits action start/completion and tool request/observation events accordingly.

### 16.4 OmniAgent-Audit Conformance (Optional)

Includes Control and additionally:

* emits `agent.event:SafetyIntervention`,
* integrates with OmniPolicy decision/audit events (when enabled).

### 16.5 OmniAgent-Test Conformance (Optional)

Includes Tool conformance and additionally:

* stable IDs/testTags,
* optional seed control and/or time control integration,
* deterministic step bounds for `agent.run`.

---

## 17. OmniAgent Selector Extension (`agent-sel-0`)

Endpoints MUST support `ogif-sel-0`. OmniAgent recommends these conveniences:

* `agent()` ? `type("agent.agent")`
* `session(status="running")` ? `type("agent.session") AND state("/status"=="running")`
* `message(role="user")` ? `type("agent.message") AND attr("role"=="user")`
* `action(type="tool_call")` ? `type("agent.action") AND attr("actionType"=="tool_call")`
* `artifact(kind="file")` ? `type("agent.artifact") AND attr("kind"=="file")`

Traversal examples:

* `#<sessionId> out("agent:hasMessage")`
* `#<sessionId> out("agent:hasContext")`
* `#<actionId> out("agent:produced")`

---

## 18. Example (Informative)

### Delegated Tool Mode Example

1. Client creates session and sends user message:

* “Summarize repo status.”

2. Agent emits:

* `agent.event:ToolCallRequested` ? `rpc://service/github#listPRs`

3. Orchestrator calls OmniRPC tool and submits result:

* `agent.submitObservation(actionId, tool_result, result)`

4. Agent emits:

* `agent.event:OutputProduced` (summary)
* `agent.event:ArtifactCreated` (optional report)

If policy denies tool access, agent emits:

* `agent.event:SafetyIntervention` with `reasonCode="policy.denied"`.

---

**End of OmniAgent Profile Specification `ogif.profile:omniagent-0` (Draft)**
