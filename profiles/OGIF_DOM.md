# OmniDOM Profile Specification
## OGIF Profile: Multimodal Interaction Tree, Semantic Events, and Stimulus Integrity

**Profile Name:** OmniDOM  
**OGIF Profile ID:** `ogif.profile:omnidom-1`  
**Profile Version:** 1.0.0 (Draft)  
**Status:** Experimental / Proposed Standard  
**Last Updated:** 2026-02-22  
**Depends On:** OmniGraphIF (OGIF) Core `ogif-core-0` (v0.1.0 draft)  
**Selector Baseline:** `ogif-sel-0` + OmniDOM Selector Extension `dom-sel-1` (defined herein)

---

## 1. Purpose

OmniDOM is an OGIF profile that models an application’s **interactive interface** as a **semantic tree** of nodes with:

- **roles** (what a node *is*),
- **capabilities** (what a node *can do*),
- **state** (what is true now),
- **semantic events** with **DOM-like propagation** (capture ? target ? bubble),
- and **stimulus integrity** rules guaranteeing that user-relevant audio/visual output is observable semantically.

OmniDOM exists so external clients (tests, assistive tech, bots, tooling) can interact with the interface **as a user would**, without relying on:
- computer vision / pixel scraping,
- terminal screen scraping as a source of truth,
- waveform matching for audio.

---

## 2. Design Goals

An OmniDOM implementation MUST enable a client to:

1. **Discover** the interactive surface (tree snapshot, node roles/capabilities/state).
2. **Locate** nodes deterministically (stable IDs and selectors).
3. **Act** using semantic events (`Activate`, `SetValue`, `Navigate`, etc.).
4. **Observe** state changes, notifications, and announcements.
5. **Verify safeguards** (restrictions, protections, confirmation dialogs, disabled actions) using the same logic paths a user triggers.
6. **Avoid renderer-only meaning**: anything user-relevant must be mirrored in OmniDOM state/events (stimulus integrity).

---

## 3. Non-goals

OmniDOM does NOT standardize:

- pixel layout, geometry, colors, animation curves,
- terminal escape sequences,
- audio codecs or waveform-level correctness,
- general service-to-service RPC contracts (use OmniRPC),
- pipelines/stream DAG semantics (use OmniFlow),
- simulation worlds (use OmniECS).

OmniDOM MAY coexist with those profiles via OGIF cross-links.

---

## 4. Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

---

## 5. Relationship to OGIF Core

OmniDOM is expressed entirely using OGIF core constructs:

- **OmniDOM nodes** are OGIF **entities** with `type = "dom.node"`.
- The **tree structure** is represented using OGIF **relations** of kind `dom:parentOf`.
- OmniDOM defines additional conventions for:
  - node role/capability/state fields,
  - ordered children,
  - semantic event types and routing,
  - profile-specific control operations,
  - stimulus integrity requirements.

OmniDOM endpoints MUST still implement OGIF `ogif.getVersion` and MUST advertise `ogif.profile:omnidom-1` in supported profiles.

---

## 6. Topology Model

### 6.1 Tree Constraint (MUST)

The subgraph induced by relations of kind `dom:parentOf` MUST form a **strict rooted tree**:

- Exactly **one** node MUST have role `root` (see §7.2).
- The root node MUST have **no parent** under `dom:parentOf`.
- Every non-root node MUST have **exactly one parent** under `dom:parentOf`.
- Cycles are forbidden.
- All nodes in the OmniDOM surface MUST be reachable from the root via `dom:parentOf`.

### 6.2 Ordered Children (MUST)

Because OGIF relations are not inherently ordered, OmniDOM requires sibling ordering.

Each `dom:parentOf` relation MUST include:

- `attributes.order` (integer)  
  - MUST be unique among a parent’s outgoing `dom:parentOf` relations
  - MUST be non-negative
  - defines canonical sibling order (ascending)

Example relation:
```json
{
  "from": "ui://screen/login",
  "to": "ui://screen/login#username",
  "kind": "dom:parentOf",
  "directed": true,
  "attributes": { "order": 0 }
}
```

### 6.3 Optional Supporting Relations

OmniDOM MAY additionally use these relation kinds (all directed):

* `dom:labelFor` (label node ? control node)
* `dom:describedBy` (help text node ? target node)
* `dom:controls` (control node ? controlled node; e.g., tab ? panel)

These relations MUST NOT violate tree constraints because they do not define parentage.

### 6.4 Cross-Profile Relations

OmniDOM nodes MAY reference entities in other OGIF domains using core relations:

* `ogif:represents` (UI node represents world/service entity)
* `ogif:dependsOn` (UI depends on another entity)
* `ogif:facetOf` (rare for UI; generally discouraged)

---

## 7. Node Model

### 7.1 OmniDOM Entity Type (MUST)

Every OmniDOM node MUST be an OGIF entity with:

* `type` MUST equal `"dom.node"`.

Example:

```json
{
  "id": "ui://screen/login#submit",
  "type": "dom.node",
  "name": "Submit",
  "capabilities": ["dom.cap:focusable", "dom.cap:activatable"],
  "attributes": { "role": "action" },
  "state": { "enabled": true, "visible": true, "focused": false },
  "meta": { "testTag": "login.submit" }
}
```

### 7.2 Role (MUST)

Every OmniDOM node MUST declare its semantic role:

* `attributes.role` MUST be a string.

Core role vocabulary is defined in §7.3.
Custom roles MUST be namespaced (e.g., `myapp.role:timeline`).

### 7.3 Core Roles (Reserved)

Implementations MUST support the following roles (minimum semantics in §11–§13):

* `root` — root of the OmniDOM tree
* `screen` — navigable view/context
* `container` — groups children
* `text` — read-only output
* `action` — invokable operation
* `input` — editable value
* `toggle` — boolean on/off
* `choiceGroup` — selection container
* `choice` — selectable item
* `list` — ordered collection
* `table` — grid-like structured output
* `dialog` — modal focus scope
* `notification` — message to user (transient or persistent)
* `progress` — progress indicator
* `media` — time-based media element (semantic handle)
* `prompt` — asks user for confirmation/input (often audio-first)

### 7.4 Name and Description (SHOULD)

* `name` SHOULD be a user-facing label (localized as needed).
* `description` SHOULD be provided when it helps disambiguation or accessibility.

### 7.5 Capabilities (MUST for Interactable Nodes)

Capabilities are OGIF `capabilities[]` entries.

OmniDOM capability tokens MUST be prefixed `dom.cap:`.

Core capability vocabulary (reserved):

* `dom.cap:focusable`
* `dom.cap:activatable`
* `dom.cap:editable`
* `dom.cap:selectable`
* `dom.cap:toggleable`
* `dom.cap:expandable`
* `dom.cap:scrollable`
* `dom.cap:dismissible`
* `dom.cap:navigable`

Rules:

* A node MUST NOT claim a capability it cannot honor semantically.
* If a node claims `dom.cap:activatable`, it MUST accept `dom.event:Activate` (§10.3).
* If a node claims `dom.cap:editable`, it MUST accept `dom.event:SetValue` (§10.4).

### 7.6 State Model (MUST)

State is stored in OGIF `state{}`.

OmniDOM defines common state fields:

* `enabled` (boolean; default true if omitted)
* `visible` (boolean; default true if omitted)
* `focused` (boolean; default false if omitted)
* `selected` (boolean | null)
* `value` (any JSON value; for `input`, `text`, etc.)
* `busy` (boolean; default false)
* `error` (string | object | null)
* `expanded` (boolean | null)

Nodes MAY include role-specific state fields (e.g., `progress.value`, `media.currentTime`).

### 7.7 Sensitive Fields (MUST)

If a node represents sensitive user input (passwords, tokens, secrets):

* `attributes.sensitive` MUST be `true`.

In snapshots (`dom.getTree`, `ogif.getGraph`) sensitive values MUST be redacted by default (§15.4).

### 7.8 Test Tags (RECOMMENDED)

To support stable tests when IDs vary, nodes SHOULD include:

* `meta.testTag` (string stable across runs in test mode)

---

## 8. OmniDOM Selectors

OmniDOM defines a selector extension `dom-sel-1` for convenience. Endpoints MUST support `ogif-sel-0` and MUST additionally support `dom-sel-1` within OmniDOM query methods.

### 8.1 dom-sel-1 Primitives (MUST)

* `#<id>` — exact ID match
* `role(<roleName>)`
* `name("...")` (exact match; case-insensitive SHOULD)
* `name~("...")` (substring match; deterministic)
* `cap(<capability>)`
* `state(<key>=<value>)` (at minimum equality)

### 8.2 Tree Combinators (MUST)

* `A > B` — direct child under `dom:parentOf`
* `A B` — descendant under `dom:parentOf`

Example:

* `role(screen) > role(input) name("Username")`
* `role(dialog) role(action) name("Confirm")`

### 8.3 Mapping to OGIF Selectors (Informative)

An implementation may translate:

* `A > B` ? adjacency traversal `out("dom:parentOf")` with `attributes.order` ordering
* `A B` ? repeated traversal along `dom:parentOf`

---

## 9. Event Model Overview

OmniDOM interaction is expressed as **semantic events**. A renderer (GUI/TUI/audio) translates device inputs into these events. Automation clients inject the same semantic events.

### 9.1 Event Envelope (Required Fields)

OmniDOM uses OGIF’s event envelope and extends it with UI-specific fields in `data`.

An emitted OmniDOM event MUST include:

* `eventId` (string)
* `type` (string, prefixed `dom.event:`)
* `timestamp` (ISO-8601)
* `source` (entity id OR null; see below)
* `data` (object)

For OmniDOM events, the envelope MUST follow this convention:

* `source` MUST be the **currentTarget** node when the event is emitted during routing (if emitted).
* The original requested target MUST be provided as `data.target`.

At minimum, for observability and stimulus integrity, OmniDOM MUST emit output events (`Announce`, `Cue`) and state changes (§14).

### 9.2 Input Event Observability (SHOULD / Security-Sensitive)

Events that may carry sensitive input (e.g., `SetValue` on passwords) SHOULD NOT be emitted to unprivileged subscribers. Implementations SHOULD gate emission behind capability/policy:

* `dom.cap:observeInputEvents` (or equivalent auth policy)

State change notifications (redacted) remain required.

---

## 10. OmniDOM Event Types (Reserved)

### 10.1 Event Routing Phases

OmniDOM defines a DOM-like routing model with phases:

* `capture`
* `target`
* `bubble`

When routing details are exposed (e.g., in test mode), implementations MUST use:

* `data.phase` in `{ "capture", "target", "bubble" }`

### 10.2 Navigation and Focus

* `dom.event:FocusRequest`
* `dom.event:FocusChanged` (non-cancelable; informational)
* `dom.event:Navigate` (directional or logical navigation intent)

### 10.3 Activation and Commands

* `dom.event:Activate`
* `dom.event:Submit`
* `dom.event:Cancel`
* `dom.event:Invoke` (named command)

### 10.4 Value and Selection

* `dom.event:SetValue` (preferred for automation)
* `dom.event:Edit` (incremental)
* `dom.event:ValueChanged` (informational)
* `dom.event:SetSelection`
* `dom.event:SelectionChanged` (informational)
* `dom.event:Toggle`

### 10.5 Structure and Visibility

* `dom.event:Expand`
* `dom.event:Collapse`
* `dom.event:Dismiss`

### 10.6 Announcements and Cues (Stimulus Semantics)

* `dom.event:Announce`
* `dom.event:Cue`

These are REQUIRED for stimulus integrity (§14).

### 10.7 Lifecycle

* `dom.event:ScreenEnter`
* `dom.event:ScreenExit`
* `dom.event:DialogOpened`
* `dom.event:DialogClosed`

---

## 11. Event Routing Semantics (Capture ? Target ? Bubble)

### 11.1 Dispatch Inputs

A dispatch request includes at minimum:

* `type`
* `target` (node ID)
* optional `source` descriptor (human/automation/system)
* `data` payload

Example dispatch event object:

```json
{
  "type": "dom.event:Activate",
  "target": "ui://screen/login#submit",
  "source": { "kind": "automation", "modality": "api", "device": "none" },
  "data": {}
}
```

### 11.2 Routing Algorithm (MUST)

For any cancelable input event (e.g., `Activate`, `SetValue`, `Toggle`, `Dismiss`):

1. Compute the **event path** as the ordered list of ancestors from root to target inclusive using `dom:parentOf`.
2. **Capture phase:** visit nodes on the path from root to the parent of target, in order.
3. **Target phase:** visit the target.
4. **Bubble phase:** visit nodes from parent of target back to root, in reverse order.
5. At each visited node, listeners may:

   * stop propagation, and/or
   * prevent default action (if cancelable).

### 11.3 Flags (MUST)

During routing, the dispatcher maintains flags:

* `cancelable` (boolean)
* `defaultPrevented` (boolean)
* `propagationStopped` (boolean)

`defaultPrevented` MUST suppress default actions.

### 11.4 Default Actions (MUST/SHOULD)

Nodes MAY define default actions for event types, but:

* Default actions MUST NOT run if `defaultPrevented = true`.
* Default actions SHOULD run after target-phase listeners unless profile- or app-specific semantics require otherwise.

### 11.5 External Clients and Listener Registration

OmniDOM does not require exposing remote, behavior-changing listeners.

* External clients MUST be able to **dispatch** and **observe**, but do not need the ability to register interception handlers.
* If an implementation offers remote interception, it MUST be capability-gated and MUST not violate safety policies.

---

## 12. Focus and Modal Semantics

### 12.1 Single Focus Rule (MUST)

Within a given focus scope, at most one node MAY have:

* `state.focused = true`

### 12.2 Focusable Nodes

Only nodes with capability `dom.cap:focusable` should be focus targets.

### 12.3 Dialog Focus Scope (MUST)

Nodes with role `dialog` MUST define a focus scope:

* While a dialog is open (visible), focus navigation MUST remain inside the dialog subtree unless explicitly allowed by app policy.
* Attempts to move focus outside the active dialog SHOULD be prevented (via default prevention or rejection).

### 12.4 Focus Events

* `dom.event:FocusRequest` MAY be rejected/canceled.
* `dom.event:FocusChanged` MUST reflect actual focus transitions and MUST be emitted/observable (at least via `StateChanged` patches to `focused`).

---

## 13. Value, Selection, and Restriction Semantics

### 13.1 SetValue (MUST)

For nodes with `dom.cap:editable`:

* `dom.event:SetValue` MUST attempt to set the entire value deterministically.
* If invalid, the system MUST surface the failure semantically (e.g., `state.error`, `notification`, `Announce`) per stimulus integrity rules (§14).

### 13.2 Edit (MAY)

`dom.event:Edit` is optional and intended for human-like incremental edits. Implementations MAY translate it into `SetValue` internally.

### 13.3 Selection (MUST)

For `choiceGroup` and `choice`:

* `dom.event:SetSelection` MUST deterministically set selection.
* Selection rules SHOULD be exposed via `attributes.selectionMode = "single" | "multiple"` on the group.

### 13.4 Disabled or Hidden Nodes (MUST)

If `state.enabled = false` or `state.visible = false`:

* User-triggered actions (`Activate`, `SetValue`, etc.) SHOULD be rejected or treated as no-op.
* Implementations MUST behave consistently across renderers and automation clients.

---

## 14. Stimulus Integrity Requirements (Normative)

> This section incorporates and formalizes the previously drafted stimulus integrity addendum as mandatory OmniDOM profile behavior.

### 14.1 Definitions

**Stimulus:** any perceivable renderer output (visual, audio, haptic, animation, overlay).
**User-relevant stimulus:** could influence user understanding/decision/action/safety.
**Decorative stimulus:** conveys no actionable or interpretive information and does not gate interaction.

### 14.2 Mirror Rule (MUST)

Any **user-relevant stimulus** produced by any renderer MUST have a corresponding semantic representation observable through OmniDOM via at least one of:

1. A node state change (`StateChanged` patch), and/or
2. A structural change (node added/removed/moved in the tree), and/or
3. A semantic event (`dom.event:Announce`, `dom.event:Cue`, lifecycle events).

A renderer MUST NOT present user-relevant meaning only in pixels, terminal glyphs, or audio waveform.

### 14.3 Errors, Warnings, Safeguards, Restrictions (MUST)

If a renderer communicates:

* validation errors,
* permission denial,
* action blocked/disabled,
* safety warnings,
* confirmations required,

then the application MUST expose it semantically via one or more of:

* a `notification` node (RECOMMENDED),
* `dom.event:Announce` including severity (RECOMMENDED),
* relevant node `state.error`,
* node state change (e.g., `enabled=false`, `busy=true`).

`dom.event:Announce` SHOULD include:

* `data.severity`: `"info"|"warning"|"error"|"critical"`
* `data.text`: localized user-facing text
* `data.sourceNodeId`: associated node id when applicable

### 14.4 Persistent vs Transient Feedback (SHOULD)

* Persistent/re-readable feedback SHOULD be represented as nodes (`notification`, `dialog`, `text`).
* Transient feedback SHOULD be emitted as events (`Announce`, `Cue`).

### 14.5 Prohibited Renderer-Only Interaction State (MUST NOT)

Renderers MUST NOT introduce interaction state that is absent in OmniDOM.

Violations include:

* visually disabling an action while OmniDOM reports `enabled=true`,
* blocking selection/focus in renderer while OmniDOM indicates allowed,
* showing an “error highlight” without semantic error state/event.

### 14.6 Decorative Stimulus (MAY)

Decorative stimulus MAY be omitted entirely.

If represented, it MUST be marked:

* `attributes.decorative = true`

Decorative nodes MUST NOT gate interaction and MUST NOT be the only carrier of meaning.

### 14.7 Timing and Ordering (MUST/SHOULD)

When user-relevant stimulus is presented, the semantic mirror (state/event) MUST be emitted **no later than** the stimulus presentation.

In test mode, implementations SHOULD emit the semantic mirror **before** presentation for determinism.

### 14.8 Localization and Stable Message IDs (RECOMMENDED)

`Announce` and `notification` SHOULD include:

* `data.messageId` (stable template id, e.g., `auth.invalid_password`)
* `data.text` (localized text)
* `data.locale` (BCP-47)

Automation SHOULD prefer `messageId` over raw text when present.

### 14.9 Sensitive Information (MUST)

* Sensitive node values MUST be redacted in snapshots by default.
* Announcements/notifications MUST NOT leak secrets (passwords/tokens).

---

## 15. Determinism and Time-Based UI

### 15.1 Test Mode (SHOULD)

Implementations SHOULD support a test mode that:

* stabilizes IDs (or provides stable `meta.testTag`),
* produces deterministic child ordering and query results,
* disables or standardizes nondeterministic animations/timers where feasible.

### 15.2 Time-Gated Logic (MUST)

If an interaction is gated by time-based behavior (animation completion, loading spinner, transition), the gating MUST be expressed semantically via:

* `state.busy`,
* `state.enabled`,
* `progress` state,
* completion events (e.g., `dom.event:MediaEnded` if defined by app extension).

A renderer MUST NOT “unlock” controls solely because an animation ended without updating OmniDOM state/events.

### 15.3 Optional Time Control Extension (`ogif.ext:timecontrol-0`)

For deterministic testing, implementations MAY expose time control using the OGIF Time Control extension, advertised via `ogif.getVersion.features.timeControl = "ogif.ext:timecontrol-0"`.

Recommended operations:

* `dom.time.freeze`
* `dom.time.advance({ deltaMs })`
* `dom.time.resume`

### 15.4 Redaction in Snapshots (MUST)

When producing a tree snapshot:

* If `attributes.sensitive = true`, then `state.value` MUST be omitted or replaced with a redacted sentinel.

---

## 16. Required Operations and API Surface

OmniDOM can be implemented purely with OGIF primitives, but OmniDOM profile conformance requires **specific semantics** for tree retrieval, query, dispatch, and wait.

### 16.1 Required OmniDOM Operations (Semantic Requirements)

An OmniDOM endpoint claiming **Control Conformance** (§17) MUST support:

* Get tree snapshot
* Get node by ID
* Query nodes by `dom-sel-1`
* Dispatch OmniDOM events
* Subscribe to announcements and state changes
* Wait for conditions

### 16.2 Recommended JSON-RPC Methods

If the endpoint uses JSON-RPC 2.0, it SHOULD expose:

* `dom.getTree({ depth?, subtreeRootId? })`
* `dom.getNode({ id })`
* `dom.query({ selector, limit? })`
* `dom.dispatch({ event })`
* `dom.subscribe({ events, selector? })`
* `dom.unsubscribe({ subscriptionId })`
* `dom.waitFor({ selector, predicate?, timeoutMs })`

These may be implemented as wrappers around OGIF calls and `ogif.invoke`.

### 16.3 Dispatch Result (MUST)

`dom.dispatch` MUST return an outcome object including:

* `accepted` (boolean)
* `defaultPrevented` (boolean)
* `propagationStopped` (boolean)
* optional `reason` when not accepted
* optional `effects` (patches or summaries) in test mode

Example:

```json
{
  "accepted": true,
  "defaultPrevented": false,
  "propagationStopped": false
}
```

### 16.4 Subscription Requirements (MUST)

At minimum, OmniDOM endpoints MUST allow subscription (directly or via OGIF subscribe) to:

* `dom.event:Announce`
* `dom.event:Cue`
* OGIF patch events that reflect OmniDOM state/tree changes:

  * `ogif.event:StateChanged` and/or `ogif.event:EntityChanged` and/or `ogif.event:GraphChanged`

---

## 17. Conformance Levels

### 17.1 OmniDOM-Read Conformance

An endpoint is **OmniDOM-Read conformant** if it:

* Implements OGIF read conformance (snapshot, query, subscribe).
* Exposes an OmniDOM tree via `dom:parentOf` with all constraints (§6).
* Provides node roles/capabilities/state per §7.
* Emits required semantic mirrors for user-relevant stimulus (§14), including `Announce` and `Cue`.
* Redacts sensitive values in snapshots (§15.4).

### 17.2 OmniDOM-Control Conformance

Includes OmniDOM-Read and additionally:

* Supports semantic event dispatch (`dom.dispatch` semantics).
* Ensures dispatched events traverse the same dispatcher and safeguards as user input (§11–§13).
* Rejects or no-ops invalid actions consistently (disabled/hidden constraints).

### 17.3 OmniDOM-Test Conformance (Recommended)

Includes OmniDOM-Control and additionally:

* Provides stable IDs or stable `meta.testTag`.
* Provides deterministic ordering for child traversal and focus order.
* Optionally supports time control extension (§15.3).
* May expose richer routing diagnostics (event path/phase) under explicit capability.

---

## 18. Security Considerations

### 18.1 User-Equivalent Surface (RECOMMENDED)

OmniDOM control should be treated as a **user-equivalent surface**:

* It MUST NOT bypass business logic.
* It SHOULD be restricted to local tooling in production builds unless explicitly authorized.
* It SHOULD enforce the same permissions a real user session would have.

### 18.2 Sensitive Data

* Password/token values MUST be redacted in snapshots.
* Input-event observation SHOULD be restricted to prevent leaking secrets through event streams.

### 18.3 Auditability (SHOULD)

Implementations SHOULD log:

* automation connections,
* dispatched events (redacting sensitive payloads),
* policy rejections.

---

## 19. Accessibility Interop (Recommended)

GUI renderers SHOULD map OmniDOM nodes to platform accessibility APIs:

* role ? accessibility role
* name ? accessibility label
* state ? enabled/disabled/selected/value
* activations ? accessibility invoke

This provides interoperability with OS-level assistive technologies even without OGIF access.

---

## 20. Example: Multimodal Login Flow (Informative)

Tree:

* `screen(Login)`

  * `input(Username)`
  * `input(Password)` (sensitive)
  * `action(Submit)`
  * `notification(Error)` (hidden unless needed)

Automation test:

1. `dom.query(role(input) name("Username"))` ? set value
2. `dom.query(role(input) name("Password"))` ? set value
3. `dom.dispatch(Activate on Submit)`
4. subscribe to `Announce` and `StateChanged`
5. assert either:

   * navigation to next screen, or
   * `notification` becomes visible + `Announce` severity error

No CV; no waveform matching; safeguards observed via semantic mirrors.

---

**End of OmniDOM Profile Specification `ogif.profile:omnidom-1` (Draft)**
