# Action Claim — Specification Overview

> **Status:** v0.1 — draft
> Companion specification to: *Toward an Operational Ontology of Agentic Action* ([DOI 10.5281/zenodo.18930044](https://doi.org/10.5281/zenodo.18930044))

---

## Documents

| File | Description |
|------|-------------|
| [action-claim.md](action-claim.md) | Field-by-field specification of the Action Claim object |
| [ontology.md](ontology.md) | Operational ontology: entities, relations, and scope |
| [delegation-chain.md](delegation-chain.md) | Delegation chain structure and mandate propagation rules |
| [evaluation-model.md](evaluation-model.md) | Governance evaluation model and latency tiers |
| [composition-axioms.md](composition-axioms.md) | Formal axioms for effect composition |
| [schema/action-claim.json](schema/action-claim.json) | JSON Schema (Draft 2020-12) |

---

## Design Principles

The Action Claim object is designed around five principles that jointly define its role as a governance object:

### 1. Pre-execution

Governance happens **before** the world-state transition occurs, not after. The Action Claim is submitted to an evaluator prior to any effect being produced. This is the fundamental departure from audit-based approaches: the claim is a *proposal*, not a report.

### 2. Tripartite Authorship

No single party authors the full claim. Fields are distributed across three sources of authority:

- **Declared** — provided by the agent itself (intent, context, preconditions)
- **Derived** — computed by the governance system from system state (capability scope, impact profile, justification gap)
- **Delegation-supplied** — injected by the delegation infrastructure (chain of principals and mandates)

This separation prevents agents from self-certifying their own authorization.

### 3. Contestable

Every Action Claim is contestable by a governance evaluator. The evaluator may approve, deny, reduce scope, escalate, or sandbox the proposed transition. Contestability is structural: the claim format exposes enough information to support challenge without requiring the evaluator to reconstruct agent intent.

### 4. Machine-evaluable

The claim is structured for automated evaluation. All fields are typed and bounded. Policy systems (e.g., OPA, XACML) can evaluate claims without natural language interpretation. Human escalation is possible but not required for the common case.

### 5. Composition-aware

Effects compose. An agent that reads, then summarizes, then discloses has produced a compound effect that is not captured by evaluating each step in isolation. The claim format and the composition axioms in this spec support net-effect reasoning across action sequences.

---

## Canonical Object

```
ActionClaim {
  // Declared by the agent
  proposed_transition       // The specific world-state change being requested
  originating_goal          // The high-level goal from which this action derives
  relevant_context_basis    // The context elements that informed this action selection
  preconditions             // Conditions the agent asserts must hold before execution

  // Derived by the system (never authored by the agent)
  capability_scope          // What the agent is technically and normatively permitted to do
  impact_profile            // Sensitivity, reversibility, persistence of the transition
  justification_gap         // Distance between claimed mandate and proposed effect

  // Supplied by the delegation infrastructure
  delegation_chain          // Ordered sequence of principals and mandate constraints
}
```

---

## Canonical Failure Modes

The spec addresses three canonical failure modes that governance systems must handle:

| ID | Name | Description |
|----|------|-------------|
| FM-1 | **Scope Creep** | Agent proposes a transition that exceeds the mandate granted by its principal chain |
| FM-2 | **Decomposition Attack** | Agent achieves a prohibited compound effect by decomposing it into individually-permitted steps |
| FM-3 | **Mandate Laundering** | Agent acquires authorization through a delegation chain that obscures the original principal's intent |
