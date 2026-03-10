# Delegation Chain — Specification

> **Status:** v0.1 — draft

---

## Purpose

The delegation chain is the authoritative record of how authority reached the acting agent. In multi-agent systems, a human principal rarely interacts directly with the agent that proposes a world-state transition. Instead, authority flows through a sequence of delegations: human → orchestrator → sub-agent → tool-agent, or similar.

Without a structured delegation chain, governance systems cannot determine:
- Whether the authority claimed by the agent was legitimately granted
- What constraints were imposed at each delegation step
- Whether mandate drift has occurred across the chain

**Mandate drift** is the gradual expansion of effective authority as mandates are re-interpreted, re-stated, or extended at each hop. A governance system that only examines the immediate principal→agent relationship will miss drift that accumulates across multiple hops.

---

## Hop Structure

Each element in the `delegation_chain` array is a **delegation hop** — a record of a single principal-to-agent grant.

```json
{
  "hop_index": 0,
  "principal": {
    "id": "principal-identifier",
    "type": "human | agent",
    "identity_ref": "spiffe://org/service/name"
  },
  "delegate": {
    "id": "delegate-identifier",
    "type": "agent",
    "identity_ref": "spiffe://org/agent/name"
  },
  "mandate": {
    "description": "Human-readable summary of the grant",
    "permitted_transition_types": [ "internal_read", "internal_write" ],
    "permitted_resources": [ "resource-pattern-or-ref" ],
    "constraints": [
      {
        "constraint_type": "time_bound | scope_limit | require_escalation | ...",
        "description": "Human-readable description of the constraint",
        "value": "..."
      }
    ]
  },
  "delegated_at": "ISO-8601 timestamp"
}
```

**Field descriptions:**

| Field | Description |
|-------|-------------|
| `hop_index` | Position in the chain (0 = root principal to first delegate) |
| `principal.id` | Identifier of the granting party |
| `principal.type` | `human` or `agent`; the root hop must always be `human` |
| `principal.identity_ref` | Cryptographic identity reference (e.g., SPIFFE SVID URI) |
| `delegate.id` | Identifier of the receiving agent |
| `mandate.permitted_transition_types` | Transition types the delegate is authorized to propose |
| `mandate.permitted_resources` | Resource patterns or references within scope |
| `mandate.constraints` | Restrictions that apply to the granted mandate |
| `delegated_at` | Timestamp of the delegation event |

---

## Example: Three-Hop Chain

```json
[
  {
    "hop_index": 0,
    "principal": {
      "id": "user:alice@example.com",
      "type": "human",
      "identity_ref": "mailto:alice@example.com"
    },
    "delegate": {
      "id": "agent:orchestrator-v2",
      "type": "agent",
      "identity_ref": "spiffe://example.com/agents/orchestrator-v2"
    },
    "mandate": {
      "description": "Manage weekly customer feedback reporting pipeline",
      "permitted_transition_types": [
        "internal_read",
        "internal_write",
        "internal_execute",
        "notify"
      ],
      "permitted_resources": [
        "dataset://crm/customers/*",
        "report://weekly/*"
      ],
      "constraints": [
        {
          "constraint_type": "scope_limit",
          "description": "No external disclosure without separate explicit authorization",
          "value": "external_disclosure_prohibited"
        },
        {
          "constraint_type": "time_bound",
          "description": "Mandate expires end of Q1 2026",
          "value": "2026-03-31T23:59:59Z"
        }
      ]
    },
    "delegated_at": "2026-01-06T09:00:00Z"
  },
  {
    "hop_index": 1,
    "principal": {
      "id": "agent:orchestrator-v2",
      "type": "agent",
      "identity_ref": "spiffe://example.com/agents/orchestrator-v2"
    },
    "delegate": {
      "id": "agent:summarizer-agent",
      "type": "agent",
      "identity_ref": "spiffe://example.com/agents/summarizer-agent"
    },
    "mandate": {
      "description": "Read and summarize customer feedback datasets",
      "permitted_transition_types": [
        "internal_read",
        "internal_write"
      ],
      "permitted_resources": [
        "dataset://crm/customers/*"
      ],
      "constraints": [
        {
          "constraint_type": "scope_limit",
          "description": "Write access limited to report staging area only",
          "value": "write_scope:report://weekly/staging/*"
        }
      ]
    },
    "delegated_at": "2026-03-09T08:00:00Z"
  },
  {
    "hop_index": 2,
    "principal": {
      "id": "agent:summarizer-agent",
      "type": "agent",
      "identity_ref": "spiffe://example.com/agents/summarizer-agent"
    },
    "delegate": {
      "id": "agent:export-agent-b",
      "type": "agent",
      "identity_ref": "spiffe://example.com/agents/export-agent-b"
    },
    "mandate": {
      "description": "Export finalized weekly report",
      "permitted_transition_types": [
        "internal_read",
        "notify"
      ],
      "permitted_resources": [
        "report://weekly/staging/*"
      ],
      "constraints": [
        {
          "constraint_type": "require_escalation",
          "description": "Any external action requires escalation to orchestrator",
          "value": "escalate_to:agent:orchestrator-v2"
        }
      ]
    },
    "delegated_at": "2026-03-09T08:15:00Z"
  }
]
```

---

## Mandate Propagation Rules

### Rule 1: Scope Non-Expansion

A delegate may not receive a mandate that is broader than the mandate held by its principal at the time of delegation. Formally: if principal `P` holds mandate `M_P`, and `P` delegates to agent `A` with mandate `M_A`, then `M_A ⊆ M_P` must hold for all transition types and resource scopes.

Violation: An orchestrator agent that was not authorized for external disclosure cannot grant external disclosure authority to a sub-agent.

### Rule 2: Constraint Inheritance

Constraints imposed at hop `i` apply to all subsequent hops `j > i`, regardless of whether those constraints are restated in subsequent mandate objects. A time-bound imposed at hop 0 cannot be removed by an agent at hop 1.

The governance system must evaluate the *intersection* of all constraints across the chain, not just the constraints in the most recent hop.

### Rule 3: Root Principal Traceability

Every delegation chain must be traceable to a human principal at `hop_index: 0`. The governance system must reject chains that:
- Begin with a machine principal
- Have no root hop
- Have a root hop with `principal.type != "human"`

This rule prevents fully machine-generated authorization chains, which would remove human principals from the authorization path entirely.

---

## Justification Gap Calculation

The **justification gap** measures the distance between the authority encoded in the delegation chain and the scope of the proposed transition.

### Local Gap (immediate boundary)

The local gap compares the proposed transition against the mandate at the final hop (the immediate principal→agent boundary):

- If `proposed_transition.transition_type ∈ mandate.permitted_transition_types` AND
  `proposed_transition.resource_ref` matches `mandate.permitted_resources`:
  → `local_gap.level = NONE`
- If transition type is permitted but resource is out of scope:
  → `local_gap.level = MINOR`
- If transition type is not in the permitted list:
  → `local_gap.level = SIGNIFICANT`
- If transition type is explicitly prohibited by a constraint:
  → `local_gap.level = CRITICAL`

### Chain Gap (aggregate)

The chain gap evaluates whether the proposed transition is within scope for *any* hop in the chain. If a higher-level principal explicitly prohibited the transition type (Rule 2: Constraint Inheritance), the chain gap must reflect this prohibition regardless of what individual hops state.

- All hops permit the transition: `chain_gap.level = NONE`
- No hop explicitly prohibits, but scope is ambiguous: `chain_gap.level = MINOR`
- At least one hop's constraints reduce the scope below the proposed transition: `chain_gap.level = SIGNIFICANT`
- Root principal explicitly prohibited the transition type: `chain_gap.level = CRITICAL`

**Overall `justification_gap.level`:** `max(local_gap.level, chain_gap.level)`

### Signals of Gap Approach

The following patterns indicate that a justification gap is likely before full computation:

1. **Transition type escalation:** The proposed `transition_type` is of higher privilege than any type in the most recent mandate's `permitted_transition_types`
2. **Trust boundary crossing:** The proposed `direction` is `outbound_third_party` but no hop in the chain explicitly grants third-party disclosure
3. **Resource scope expansion:** The proposed `resource_ref` does not match any pattern in any hop's `permitted_resources`
4. **Constraint conflict:** A constraint in the chain uses `constraint_type: scope_limit` or `external_disclosure_prohibited` and the proposed transition crosses that limit

---

## Failure Mode 3: Mandate Laundering

**Definition:** An agent acquires authorization for a transition through a delegation chain that obscures, dilutes, or misrepresents the original principal's intent — producing a chain where each individual hop appears plausible but the compound grant exceeds what the root principal actually authorized.

**Mechanism:** At each hop, the mandate description is re-stated in slightly broader terms. No single hop is obviously invalid, but the cumulative effect is a mandate that was never granted.

**Example:**

```
Hop 0: Human → Orchestrator
  mandate: "manage weekly reporting pipeline; no external disclosure"

Hop 1: Orchestrator → Summarizer
  mandate: "process and prepare reports for distribution"
  (note: "distribution" is ambiguous; "no external disclosure" constraint not restated)

Hop 2: Summarizer → Export Agent
  mandate: "distribute finalized reports to stakeholders"
  (note: "stakeholders" is undefined; could include external parties)
```

At hop 2, an agent proposes `external_data_disclosure` to a third party. The immediate mandate says "distribute to stakeholders." The root principal said "no external disclosure."

**Why it is dangerous:** Rule 2 (Constraint Inheritance) requires governance systems to apply the root-level prohibition regardless of restatement. Mandate laundering exploits systems that only evaluate the most recent hop. The chain gap calculation is the defense: it traces the prohibition from hop 0 and sets `chain_gap.level = CRITICAL`.

**Model Response:** Evaluator response `deny`, citing `chain_gap.level: CRITICAL` and referencing the constraint at `hop_index: 0`. The evaluator does not approve a transition that is prohibited by any ancestor principal in the chain.
