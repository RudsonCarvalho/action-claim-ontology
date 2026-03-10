# Composition Axioms

> **Status:** v0.1 — draft

---

## Motivation

Consider the following action sequence:

1. Agent reads a confidential customer dataset (`internal_read`, `sensitivity: HIGH`)
2. Agent summarizes the dataset (`internal_write`, `sensitivity: MEDIUM` — summary is less granular)
3. Agent discloses the summary to an external partner (`external_data_disclosure`, `direction: outbound_third_party`)

Each action, evaluated in isolation, may be individually permissible:
- Reading the dataset is authorized
- Summarizing is authorized
- Notifying partners is a general capability

But the **compound effect** — an external party receiving a disclosure derived from a confidential dataset — may not be authorized. Governing the sequence step by step, without reasoning about net effects, fails to catch this.

This is **Failure Mode 2 (Decomposition Attack):** an agent achieves a prohibited compound effect by decomposing it into individually-permitted steps.

The composition axioms provide the formal foundation for net-effect reasoning. They define how the effects of sequential actions compose, and what properties are preserved (or cannot be reduced) across that composition.

---

## Formal Setup

Let:

- **T** = set of transition types (as defined in `action-claim.md`)
- **S** = sensitivity lattice: `{LOW, MEDIUM, HIGH, CRITICAL}` with `LOW < MEDIUM < HIGH < CRITICAL`
- **D** = disclosure set: the set of external parties that have received information derived from a resource
- **R** = reversibility function: `T → {reversible, partially_reversible, irreversible}`
- **C** = a sequence of world-state transitions `C = [t₁, t₂, ..., tₙ]`
- **E(C)** = net effect of the sequence `C`

For a sequence `C`, `E(C)` is a **Net-Effect Claim** — a structured object that summarizes the compound effect of the sequence as if it were a single transition.

---

## Axiom 1: Sensitivity Non-Decreasing

**Formula:**

```
sensitivity(E(C)) = max({ sensitivity(tᵢ) | tᵢ ∈ C })
```

**Statement:** The sensitivity of the net effect of a sequence is the maximum sensitivity of any individual transition in the sequence.

**Implication:** Sensitivity cannot be reduced by composition. An agent cannot launder a `HIGH`-sensitivity read through a `MEDIUM`-sensitivity summary to produce a `MEDIUM`-sensitivity net effect. The net effect inherits the maximum sensitivity of all contributing transitions.

**Application to the motivating example:**
- `read` has `sensitivity: HIGH`
- `summarize` has `sensitivity: MEDIUM`
- `disclose` has `sensitivity: MEDIUM` (on the summary itself)
- `E(C).sensitivity = HIGH` — the net effect is `HIGH`, not `MEDIUM`

---

## Axiom 2: Disclosure Transitivity

**Formula:**

```
D(E(C)) ⊇ ⋃{ D(tᵢ) | tᵢ ∈ C }
```

**Statement:** If any transition in a sequence discloses information to an external party, that party is in the disclosure set of the net effect, regardless of subsequent transformations.

**Implication:** Disclosure cannot be undone within the same sequence. Once a resource's derived form has been sent to party `P`, the net effect includes `P` in its disclosure set — even if subsequent steps appear to "summarize" or "anonymize" the data.

**Application:** In the motivating example, the disclosure at step 3 adds `crm-partner-z` to `D(E(C))`. A governance system evaluating the net effect can then check whether `crm-partner-z` is an authorized recipient under the root principal's mandate — not just whether the immediate `disclose` action is authorized.

---

## Axiom 3: Irreversibility Propagates

**Formula:**

```
R(E(C)) = irreversible  if  ∃ tᵢ ∈ C : R(tᵢ) = irreversible
R(E(C)) = partially_reversible  if  ∃ tᵢ ∈ C : R(tᵢ) = partially_reversible ∧ ∀ tⱼ ∈ C : R(tⱼ) ≠ irreversible
R(E(C)) = reversible  if  ∀ tᵢ ∈ C : R(tᵢ) = reversible
```

**Statement:** If any transition in the sequence is irreversible, the net effect is irreversible. Reversibility is determined by the least reversible element.

**Implication:** An agent cannot make an irreversible action reversible by appending reversible actions. An external disclosure (irreversible) followed by a deletion of the local copy does not become reversible — the information has already left the trust boundary.

**Application:** This axiom closes a common attack vector: "undo the source to undo the effect." Once an irreversible transition has occurred, the net effect carries that irreversibility forward.

---

## Axiom 4: Scope Is the Union

**Formula:**

```
scope(E(C)) = ⋃{ scope(tᵢ) | tᵢ ∈ C }
```

Where `scope(tᵢ)` is the set of resources accessed or affected by transition `tᵢ`.

**Statement:** The resource scope of the net effect is the union of the scopes of all individual transitions in the sequence.

**Implication:** An agent that reads from resource `A`, transforms the result, and writes to resource `B` has produced a net effect that spans both `A` and `B`. The governance system must check the entire union against the mandate's `permitted_resources` — not just the scope of the final action.

**Application:** This axiom prevents agents from escaping resource scope restrictions by routing through intermediate resources. The mandate check applies to the union of all touched resources.

---

## Net-Effect Claim

A **Net-Effect Claim** is a structured summary of the compound effect `E(C)` of a sequence of transitions. It is computed by the governance layer and used for sequence-level policy evaluation.

```json
{
  "net_effect_claim": {
    "sequence_id": "seq-20260309-001",
    "transition_count": 3,
    "transitions": [
      { "claim_id": "ac-001", "transition_type": "internal_read" },
      { "claim_id": "ac-002", "transition_type": "internal_write" },
      { "claim_id": "ac-003", "transition_type": "external_data_disclosure" }
    ],
    "net_sensitivity": "HIGH",
    "net_reversibility": "irreversible",
    "net_disclosure_set": [ "crm-partner-z" ],
    "net_scope": [
      "dataset://crm/customers/q1-summary",
      "report://weekly/staging/q1",
      "external://crm-partner-z/api/import"
    ],
    "requires_net_effect_evaluation": true,
    "net_justification_gap": {
      "level": "SIGNIFICANT",
      "gap_rationale": "Net effect includes external_data_disclosure to crm-partner-z; no hop in the delegation chain authorizes external disclosure"
    }
  }
}
```

---

## Application to Failure Mode 2 (Decomposition Attack)

**Scenario:** An agent is authorized to read customer data and to notify internal stakeholders. It is not authorized to disclose data externally. The agent decomposes the prohibited external disclosure into three steps:

| Step | Action Claim | Individual Evaluation |
|------|-------------|----------------------|
| 1 | Read `dataset://crm/customers/q1` | `approve` (authorized read) |
| 2 | Write summary to `report://weekly/staging/q1` | `approve` (authorized internal write) |
| 3 | POST summary to `external://crm-partner-z/api/import` | `approve` (agent has `notify` capability; evaluator classifies as `notify` rather than `external_data_disclosure`) |

**Without net-effect reasoning:** Each step is approved. The compound effect — external disclosure of customer data — was never evaluated as a governance object.

**With net-effect reasoning:**

1. Governance layer tracks the sequence and computes `E(C)`
2. Axiom 1: `E(C).sensitivity = HIGH` (inherited from step 1)
3. Axiom 2: `E(C).disclosure_set = {crm-partner-z}` (step 3 added an external party)
4. Axiom 4: `E(C).scope` includes `dataset://crm/customers/q1` — the original source
5. Net-effect policy check: `external_data_disclosure` of `HIGH`-sensitivity data to `crm-partner-z` is not authorized → evaluator response `sandbox` for step 3

**Key observation:** Step 3 may have been submitted as `notify` (an authorized type) but the net-effect evaluation reclassifies the compound action as `external_data_disclosure` based on Axiom 2 (disclosure transitivity). The evaluator must check the *effective* transition type, not just the declared one.

---

## Future Work

### Dependent Type Encoding

The composition axioms can be formalized using a dependent type system where:
- The type of a Net-Effect Claim is parameterized by its `net_sensitivity`, `net_reversibility`, and `net_disclosure_set`
- The evaluator's `approve` branch has a type that requires `net_justification_gap.level = NONE`
- Composition is a type-level operation that propagates the axiom constraints

This would allow static verification of evaluation logic: a type-correct evaluator implementation cannot approve a Net-Effect Claim with a non-zero justification gap.

### Datalog Encoding

The composition axioms and delegation chain propagation rules can be encoded in Datalog, enabling:
- Efficient incremental computation of net effects as new claims arrive
- Integration with OPA's Rego (which has a Datalog-like evaluation model)
- Formal provability of mandate laundering detection

Both directions are left for subsequent specification versions.
