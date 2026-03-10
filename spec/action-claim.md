# Action Claim — Field Specification

> **Status:** v0.1 — draft

---

## Formal Definition

An **Action Claim** is a pre-execution governance object submitted by an agent to a governance evaluator. It is a contestable, machine-evaluable proposal that a specific world-state transition should be permitted. It is not a tool call, a capability declaration, or an audit record. It is a *structured proposal for a state change*, presented before that change occurs.

**Formally:** Given a world-state `W`, an agent `A` operating under delegation chain `D`, an Action Claim `AC` asserts that the transition `W → W'` is permissible under the constraints encoded in `D` and consistent with the effects declared in `AC`.

---

## Properties

| Property | Definition |
|----------|------------|
| **Operational** | Refers to a concrete, specific world-state transition — not a capability, intent, or plan |
| **Contestable** | Structured to expose all information necessary for an evaluator to challenge or deny the claim |
| **Machine-evaluable** | All fields are typed, bounded, and policy-processable without natural language interpretation |
| **Pre-execution** | Submitted and evaluated before any effect is produced in the world |

---

## Canonical Object

```json
{
  "proposed_transition": { ... },
  "originating_goal": "...",
  "relevant_context_basis": [ ... ],
  "preconditions": [ ... ],
  "capability_scope": { ... },
  "impact_profile": { ... },
  "justification_gap": { ... },
  "delegation_chain": [ ... ]
}
```

---

## Fields

### `proposed_transition`

**Authored by:** Agent (declared)

**Purpose:** Describes the specific world-state change the agent proposes to produce. This is the central field of the claim. It must describe a *state change*, not a tool invocation.

**Critical distinction:**
- ❌ **Incorrect (tool call):** `"call send_email with args {to: user@example.com, body: summary}"`
- ✅ **Correct (world-state change):** `"external disclosure of document summary to user@example.com, persisted in recipient's inbox"`

The difference is not cosmetic. A tool call describes a mechanism. A world-state transition describes an effect. Governance systems evaluate effects, not mechanisms.

**Sub-fields:**

| Sub-field | Type | Description |
|-----------|------|-------------|
| `transition_type` | enum | Category of state change (see enum values below) |
| `operation` | enum | Primitive operation being applied |
| `resource_ref` | string | Identifier of the resource being acted upon |
| `direction` | enum | Whether the effect is internal or crosses a trust boundary |
| `structured_core` | object | Type-specific structured description of the transition |

**`transition_type` values:**

| Value | Description |
|-------|-------------|
| `internal_read` | Read from internal state; no external disclosure |
| `internal_write` | Write to internal state; no external disclosure |
| `internal_execute` | Execute internal computation |
| `external_data_disclosure` | Disclose data outside the current trust boundary |
| `external_delegation` | Delegate authority to another agent or principal |
| `external_execute` | Trigger execution in an external system |
| `notify` | Send a notification (lower persistence than disclosure) |
| `escalate` | Escalate to a human principal or higher-authority system |

**`operation` values:** `read`, `create`, `update`, `delete`, `disclose`, `delegate`, `execute`, `notify`, `escalate`

**`direction` values:** `internal`, `outbound_trusted`, `outbound_third_party`

---

### `originating_goal`

**Authored by:** Agent (declared)

**Purpose:** States the high-level goal from which this specific proposed transition was derived. Used by the evaluator to assess whether the proposed transition is necessary and proportionate to the stated goal.

**Type:** string

**Example:** `"Produce a weekly summary of customer feedback and share it with the product team"`

---

### `relevant_context_basis`

**Authored by:** Agent (declared)

**Purpose:** Lists the context elements that led the agent to select this specific action. Supports contestability: an evaluator can challenge whether the cited context actually justifies the proposed transition.

**Type:** array of objects

**Sub-fields per element:**

| Sub-field | Type | Description |
|-----------|------|-------------|
| `source` | string | Where the context element came from (e.g., memory, tool result, instruction) |
| `summary` | string | Brief description of the context element |
| `relevance` | string | Why this element was relevant to action selection |

---

### `preconditions`

**Authored by:** Agent (declared)

**Purpose:** Conditions the agent asserts must hold for the proposed transition to be valid. The evaluator verifies these before approving. If a precondition cannot be verified, the evaluator may deny or escalate.

**Type:** array of objects

**Sub-fields per element:**

| Sub-field | Type | Description |
|-----------|------|-------------|
| `description` | string | Human-readable statement of the condition |
| `verifiable_by` | string | How the condition can be verified (e.g., `system_check`, `policy_lookup`, `human_review`) |

---

### `capability_scope`

**Authored by:** Governance system (derived — never authored by the agent)

**Purpose:** Describes what the agent is technically and normatively permitted to do, as computed from system state and policy. Separated into technical capability (what the agent can do) and normative authorization (what the agent is allowed to do).

**Sub-fields:**

| Sub-field | Type | Description |
|-----------|------|-------------|
| `technical` | object | Capabilities the agent has access to at the infrastructure level |
| `normative` | enum | Overall authorization assessment: `AUTHORIZED`, `REQUIRES_REVIEW`, `UNAUTHORIZED` |
| `normative_basis` | string | Policy reference or rule that produces the normative value |

---

### `impact_profile`

**Authored by:** Governance system (derived — never authored by the agent)

**Purpose:** Characterizes the effects of the proposed transition along dimensions relevant to governance: sensitivity, reversibility, persistence, and regulatory significance.

**Sub-fields:**

| Sub-field | Type | Description |
|-----------|------|-------------|
| `reversibility` | enum | `reversible`, `partially_reversible`, `irreversible` |
| `persistence` | enum | `ephemeral`, `session`, `persistent`, `permanent` |
| `sensitivity` | enum | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `regulatory_significance` | boolean | Whether the transition has implications under applicable regulations (e.g., EU AI Act, GDPR) |
| `regulatory_tags` | array | Applicable regulatory categories (e.g., `["GDPR_data_transfer", "EU_AI_Act_high_risk"]`) |

---

### `justification_gap`

**Authored by:** Governance system (derived — never authored by the agent)

**Purpose:** Measures the distance between the authority the agent claims (via its delegation chain) and the scope of the proposed transition. A gap of zero means the transition is fully covered by the mandate. A non-zero gap is the primary trigger for escalation or denial.

**Sub-fields:**

| Sub-field | Type | Description |
|-----------|------|-------------|
| `level` | enum | `NONE`, `MINOR`, `SIGNIFICANT`, `CRITICAL` |
| `gap_rationale` | string | Human-readable description of what creates the gap |
| `local_gap` | object | Gap at the immediate principal→agent boundary |
| `chain_gap` | object | Aggregate gap across the full delegation chain |

See [`delegation-chain.md`](delegation-chain.md) for the gap calculation methodology.

---

### `delegation_chain`

**Authored by:** Delegation infrastructure (supplied — never authored by the agent)

**Purpose:** Ordered sequence of delegation hops from the original human principal down to the acting agent. Each hop encodes the principal, the mandate granted, constraints applied, and the time of delegation. The chain is the authoritative record of how authority reached the agent.

**Type:** array of delegation hop objects

See [`delegation-chain.md`](delegation-chain.md) for full structure and mandate propagation rules.

---

## Evaluator Responses

An evaluator receiving an Action Claim must produce exactly one of the following responses:

| Response | Condition | Effect |
|----------|-----------|--------|
| `approve` | Claim is within scope, preconditions hold, no gap | Transition is permitted to proceed |
| `deny` | Claim is out of scope, gap is CRITICAL, or preconditions fail | Transition is blocked; agent is notified |
| `reduce-scope` | Transition exceeds mandate but a subset is permissible | Evaluator returns a constrained version of the transition for re-submission |
| `escalate` | Gap is SIGNIFICANT, regulatory tags present, or sensitivity is HIGH/CRITICAL | Claim is forwarded to a human principal or higher-authority evaluator |
| `sandbox` | Claim is suspicious (possible FM-2 or FM-3 pattern detected) | Transition is permitted to proceed in an isolated environment with no real-world effects |

---

## Example: External Disclosure

**Scenario:** Agent B, operating under a delegation chain rooted in a human principal, proposes to disclose a summarized customer dataset to CRM Partner Z.

```json
{
  "proposed_transition": {
    "transition_type": "external_data_disclosure",
    "operation": "disclose",
    "resource_ref": "dataset://crm/customers/q1-summary",
    "direction": "outbound_third_party",
    "structured_core": {
      "recipient": "crm-partner-z",
      "data_classification": "CONFIDENTIAL",
      "disclosure_format": "JSON export"
    }
  },
  "originating_goal": "Sync customer summary with CRM Partner Z for Q1 reporting",
  "relevant_context_basis": [
    {
      "source": "instruction",
      "summary": "Weekly sync task from orchestrator agent",
      "relevance": "Task specifies CRM sync as a required step"
    }
  ],
  "preconditions": [
    {
      "description": "CRM Partner Z is an authorized data recipient under current data sharing agreement",
      "verifiable_by": "policy_lookup"
    }
  ],
  "capability_scope": {
    "technical": { "can_call": ["crm_export_api"] },
    "normative": "REQUIRES_REVIEW",
    "normative_basis": "policy:external-disclosure-v2, rule:third-party-requires-review"
  },
  "impact_profile": {
    "reversibility": "irreversible",
    "persistence": "persistent",
    "sensitivity": "HIGH",
    "regulatory_significance": true,
    "regulatory_tags": ["GDPR_data_transfer"]
  },
  "justification_gap": {
    "level": "SIGNIFICANT",
    "gap_rationale": "Delegation chain authorizes internal data operations; external third-party disclosure was not explicitly granted",
    "local_gap": { "level": "SIGNIFICANT", "detail": "Agent B mandate does not include external_data_disclosure to third parties" },
    "chain_gap": { "level": "SIGNIFICANT", "detail": "No hop in the chain explicitly authorizes third-party disclosure" }
  },
  "delegation_chain": [ ... ]
}
```
