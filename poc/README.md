# Action Claim — Reference Implementation (PoC)

**Version:** 0.1.0
**Status:** Proof of Concept — not production-ready
**Paper:** [Toward an Operational Ontology of Agentic Action](https://doi.org/10.5281/zenodo.18930044)

---

## Overview

This directory contains a Python reference implementation of the Action Claim governance model. It demonstrates the core concepts of the paper in executable form:

- The canonical `ActionClaim` object with tripartite field structure
- A governance evaluation engine that computes all derived fields independently
- The four composition axioms applied to compound action sequences
- The three canonical adversarial failure modes detected by the model

> This is a PoC — it uses heuristic approximations where the paper declares formal future work (e.g., justification gap computation). The structure and interfaces are faithful to the specification.

---

## Structure

```
poc/
├── models/
│   └── action_claim.py        # ActionClaim object and all constituent types
├── evaluator/
│   ├── capability.py          # Computes capability_scope
│   ├── impact.py              # Computes impact_profile
│   ├── justification_gap.py   # Computes justification_gap (scored)
│   └── engine.py              # Orchestrates the full evaluation pipeline
├── composition/
│   └── axioms.py              # Four axioms for net-effect computation
├── examples/
│   ├── approve.py             # Low-risk internal read → APPROVE
│   ├── escalate.py            # Paper's canonical instance → ESCALATE
│   └── decomposition.py       # Failure Mode 2 — decomposition attack
└── tests/
    └── test_failure_modes.py  # Tests for all three canonical failure modes
```

---

## Requirements

Python 3.10+ — no external dependencies.

---

## Quick Start

```bash
# Run the paper's canonical example (Section 11)
python examples/escalate.py

# Run the simple approval case
python examples/approve.py

# Run the decomposition attack example (Failure Mode 2)
python examples/decomposition.py

# Run all tests
python tests/test_failure_modes.py

# Or with pytest
pip install pytest
pytest tests/ -v
```

---

## Expected Output

### `examples/escalate.py`

```
Response:  ESCALATE
Rationale: Unverifiable precondition(s) require human confirmation: ...
Audit record: CREATED
Justification Gap:
  level:       HIGH
  chain_gap:   HIGH
  hop_count:   3
```

### `examples/decomposition.py`

```
Net Effect:
  sensitivity:    HIGH
  direction:      outbound_third_party
  reversibility:  IRREVERSIBLE
  ⚠ Disclosure chain detected — Axiom 2 applied
High-risk net effect detected: True
```

---

## Design Notes

### Tripartite field authorship

The `ActionClaim` object enforces the tripartite structure of the paper:

- **Declared fields** are provided by the agent when constructing the claim
- **Derived fields** (`capability_scope`, `impact_profile`, `justification_gap`) are `None` until `evaluate()` is called — they cannot be set by the agent
- **Delegation fields** are supplied by the calling infrastructure

### Justification gap scoring

Four signals from the paper, weighted:

| Signal | Weight |
|--------|--------|
| Hop count from human principal | 30% |
| Abstraction level delta | 25% |
| Action type divergence | 25% |
| Scope expansion | 20% |

Scores map to `LOW` (0–35), `MEDIUM` (35–65), `HIGH` (65–100).

### Composition axioms

`composition/axioms.py` implements all four axioms from Section 13. `compute_net_effect()` takes a list of `ProposedTransition` objects and returns a `NetEffect` with full rationale trace.

### Policy engine

`evaluator/engine.py` uses a simple rule-based policy. In production this would be replaced by OPA or a similar policy engine.

---

## Relationship to the Specification

| Spec document | PoC module |
|---------------|------------|
| `spec/action-claim.md` | `models/action_claim.py` |
| `spec/evaluation-model.md` | `evaluator/engine.py` |
| `spec/ontology.md` | `models/action_claim.py` (types and enums) |
| `spec/delegation-chain.md` | `models/action_claim.py` + `evaluator/justification_gap.py` |
| `spec/composition-axioms.md` | `composition/axioms.py` |
| `spec/schema/action-claim.json` | `models/action_claim.py` |
