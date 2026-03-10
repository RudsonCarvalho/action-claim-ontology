# Evaluation Model

> **Status:** v0.1 — draft

---

## Overview

The governance evaluator receives an Action Claim and produces a structured response. The evaluation model defines:
1. The latency tier at which evaluation occurs
2. The steps of the evaluation process
3. The possible responses and their conditions
4. How the model handles the three canonical failure modes

The evaluator is a stateless policy engine: it takes a claim as input, evaluates it against policy and system state, and returns a response. It does not retain claim history (that is the responsibility of the audit log). It does not modify agent state.

---

## Latency Tiers

Not all evaluations require the same level of scrutiny or have the same time budget. The evaluation model defines three tiers based on claim properties.

### Tier 1 — Inline (< 5ms)

**Conditions for Tier 1:**
- `impact_profile.sensitivity` is `LOW`
- `impact_profile.reversibility` is `reversible`
- `justification_gap.level` is `NONE`
- `impact_profile.regulatory_significance` is `false`
- `proposed_transition.direction` is `internal`

**Mechanism:** Pure policy lookup against a compiled policy cache. No external calls. No human involvement.

**Typical response:** `approve`

### Tier 2 — Near-real-time (< 50ms)

**Conditions for Tier 2:**
- `impact_profile.sensitivity` is `MEDIUM` or `HIGH`
- OR `justification_gap.level` is `MINOR`
- OR `proposed_transition.direction` is `outbound_trusted`
- AND `impact_profile.regulatory_significance` is `false`

**Mechanism:** Full policy evaluation (e.g., OPA policy engine with `action-claim.json` as input). May include a cache-miss policy load. No human involvement.

**Typical responses:** `approve`, `reduce-scope`, `deny`

### Tier 3 — Asynchronous (seconds to minutes)

**Conditions for Tier 3 (any of the following):**
- `impact_profile.sensitivity` is `CRITICAL`
- `justification_gap.level` is `SIGNIFICANT` or `CRITICAL`
- `proposed_transition.direction` is `outbound_third_party`
- `impact_profile.regulatory_significance` is `true`
- Any `regulatory_tag` matches a policy-configured high-risk category
- Evaluator detects a pattern consistent with FM-2 or FM-3

**Mechanism:** Human principal is notified and must review. Agent execution is paused. The claim is queued in the escalation subsystem. If no response is received within the configured timeout, the default behavior is `deny` (fail-closed).

**Typical responses:** `escalate`, `sandbox`, `deny`

---

## Evaluation Steps

### Step 1: Receive and Validate

The evaluator receives the Action Claim and validates its structure against the JSON Schema (`schema/action-claim.json`). Claims that fail schema validation are rejected immediately with a structured error. Validation errors are not governance decisions — they are protocol errors.

Fields validated at this step:
- All required fields present
- All enum values are within defined sets
- `delegation_chain` array is non-empty and root hop has `principal.type: "human"`
- `proposed_transition.direction` is consistent with `transition_type`

### Step 2: Compute Derived Fields

If derived fields (`capability_scope`, `impact_profile`, `justification_gap`) are absent or flagged for re-computation, the evaluator computes them:

- **`capability_scope.normative`:** Evaluated by looking up the agent's identity in the policy store and checking the proposed transition type against authorized operations
- **`impact_profile`:** Derived from a sensitivity classification registry keyed on `resource_ref`, `transition_type`, and `direction`
- **`justification_gap`:** Computed per the methodology in [`delegation-chain.md`](delegation-chain.md)

If an agent submits derived fields, the evaluator **recomputes** them independently and uses its own values — not the agent's. An agent cannot influence its own `normative` authorization level or its own `justification_gap`.

### Step 3: Verify Preconditions

The evaluator verifies each precondition in `preconditions[]`:

- `verifiable_by: "system_check"` → evaluator performs the check directly
- `verifiable_by: "policy_lookup"` → evaluator queries the policy store
- `verifiable_by: "human_review"` → claim is escalated to Tier 3 regardless of other fields

If any precondition fails verification, the evaluator produces `deny` with a structured reason referencing the failed precondition.

### Step 4: Evaluate Policy

The evaluator submits the full claim (with recomputed derived fields) to the policy engine. The policy engine evaluates:

1. Is the `transition_type` authorized for this agent under this delegation chain?
2. Is the `resource_ref` within the scope of the mandate?
3. Does the `justification_gap.level` require escalation or denial?
4. Do any `regulatory_tags` trigger specific handling rules?
5. Is the combination of `sensitivity`, `reversibility`, and `direction` within policy thresholds?

The policy engine returns a preliminary response recommendation.

### Step 5: Produce Response

The evaluator produces one of the five structured responses (see table below) and returns it to the agent runtime. The response includes:

- `decision`: The response type
- `claim_id`: Reference to the evaluated claim
- `evaluated_at`: Timestamp
- `reason`: Structured reason object (not a free-text string — machine-readable)
- `constrained_transition` (if `reduce-scope`): The permitted subset of the proposed transition
- `escalation_target` (if `escalate`): The principal or system to which the claim was forwarded

---

## Evaluator Responses

| Response | Conditions | Effect on Agent | Effect on World-State |
|----------|-----------|-----------------|----------------------|
| `approve` | All checks pass; gap is NONE; no regulatory triggers | Agent proceeds with proposed transition | Transition executes |
| `deny` | Gap is CRITICAL; precondition fails; policy violation; root constraint violated | Agent receives structured denial; must not proceed | No transition |
| `reduce-scope` | Transition exceeds mandate but a permitted subset exists | Agent may re-submit with constrained transition | No transition until re-submission approved |
| `escalate` | Gap is SIGNIFICANT; regulatory tags present; sensitivity HIGH/CRITICAL; precondition requires human review | Agent execution paused; claim forwarded to principal | No transition pending human decision |
| `sandbox` | FM-2 or FM-3 pattern detected; suspicious claim composition | Transition permitted in isolated environment only | Sandboxed transition; no real-world effect |

---

## Canonical Failure Mode Handling

### FM-1: Scope Creep

**Detection:** `justification_gap.level` is `SIGNIFICANT` or `CRITICAL`; `capability_scope.normative` is `UNAUTHORIZED` or `REQUIRES_REVIEW`

**Response:** Tier 2 or Tier 3 depending on sensitivity level. If gap is `CRITICAL`, evaluator produces `deny` immediately. If `SIGNIFICANT`, evaluator escalates to Tier 3 for human review.

**Why not reduce-scope:** Scope creep usually indicates an agent that is systematically operating beyond its mandate. `reduce-scope` would permit a constrained version of the over-scoped action, which may not address the underlying authorization failure.

### FM-2: Decomposition Attack

**Detection:** Evaluator maintains a short-horizon claim sequence window. If a sequence of individually `approve`-able claims would produce a compound effect that is not `approve`-able under the composition axioms (see [`composition-axioms.md`](composition-axioms.md)), the evaluator flags the sequence.

**Response:** `sandbox` — the transition is permitted in isolation but sandboxed so its real-world effect is suppressed. The claim sequence is logged for human review.

**Why sandbox:** Decomposition attacks are subtle. The evaluator may not be certain that the pattern is intentional. Sandboxing allows the agent to proceed while protecting the real world from the compound effect.

### FM-3: Mandate Laundering

**Detection:** Chain gap calculation finds that the proposed transition is explicitly prohibited by a constraint at a root or near-root hop, even though the most recent mandate is ambiguous or permissive.

**Response:** `deny`, citing `chain_gap.level: CRITICAL` and the specific constraint hop. The evaluator does not accept mandate re-interpretations from intermediate agents.

---

## Relation to OPA

The evaluation model is designed to be implementable in Open Policy Agent (OPA). The Action Claim object maps directly to OPA's `input` document. Policy rules are expressed in Rego and evaluate `input.proposed_transition`, `input.justification_gap`, `input.delegation_chain`, etc.

Example Rego fragment (illustrative):

```rego
deny[reason] {
  input.justification_gap.level == "CRITICAL"
  reason := {
    "code": "CRITICAL_JUSTIFICATION_GAP",
    "detail": input.justification_gap.gap_rationale
  }
}

escalate[reason] {
  input.justification_gap.level == "SIGNIFICANT"
  reason := {
    "code": "SIGNIFICANT_GAP_REQUIRES_REVIEW",
    "detail": input.justification_gap.gap_rationale
  }
}

escalate[reason] {
  input.impact_profile.regulatory_significance == true
  reason := {
    "code": "REGULATORY_SIGNIFICANCE",
    "detail": concat(", ", input.impact_profile.regulatory_tags)
  }
}
```

## Relation to Dependent Type Systems

The evaluation model's tier and gap calculations can be formalized using dependent types. The `justification_gap.level` is a type-level property: a transition with `CRITICAL` gap is of a different *type* than one with `NONE` gap, and the type system can enforce that `CRITICAL`-gap claims cannot reach the `approve` branch of the evaluator.

This formalization is left for future work (see [`composition-axioms.md`](composition-axioms.md) — Future Work section).
