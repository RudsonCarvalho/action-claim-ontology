# Operational Ontology of Agentic Action

> **Status:** v0.1 — draft

---

## Protocol vs. Ontology

A **protocol** specifies how objects are transmitted, validated, and routed. It answers: *what is the format, and how is it exchanged?*

An **ontology** specifies what *exists* in the domain and how those things relate to each other. It answers: *what kinds of things are there, what are their properties, and how do they interact?*

Governing agentic systems requires both — but the protocol alone is insufficient. Without an ontology, a governance system can validate the structure of an Action Claim without understanding what that claim *means*: what kind of effect it produces, how that effect relates to prior effects, and whether the claimed authority is commensurate with the proposed transition.

The operational ontology defined in this spec is the semantic layer that makes the Action Claim *evaluable*, not merely *transmissible*.

---

## Three Functions of the Ontology

### 1. Define What Exists in the Domain of Agent Action

The ontology enumerates the entity types that are relevant to governing agent behavior: agents, principals, world-states, transitions, mandates, trust boundaries, and policies. Without this enumeration, governance systems cannot reason about the relationships between objects.

### 2. Define How Effects Compose

Agent actions are not isolated. An agent that reads data, summarizes it, and then discloses the summary has produced a compound effect. The ontology defines the composition rules that allow governance systems to reason about sequences of transitions as a single net effect. See [`composition-axioms.md`](composition-axioms.md).

### 3. Define How Governance Systems Evaluate Claims

The ontology provides the evaluation framework: the entity types that appear in policy, the lattice over which sensitivity is ordered, and the relationship between the Action Claim and the governance response. See [`evaluation-model.md`](evaluation-model.md).

---

## Entities

### Agent

An entity that proposes world-state transitions on behalf of a principal. An agent:
- Has a defined capability scope (technical and normative)
- Operates under a delegation chain
- Submits Action Claims before producing effects
- Cannot self-certify its own authorization

**Subtypes:** Orchestrator agent, sub-agent, tool-agent

### Principal

An entity that grants mandates to agents. A principal may be human or machine. In multi-agent systems, a sub-agent may serve as principal to another sub-agent, creating a delegation chain.

**Root principal:** Always human. The governance model does not permit machine-only delegation chains — at least one human principal must appear at the root.

### World-State

A typed snapshot of the state of the environment at a given point in time. World-states include:
- Data states (what data exists, where, in what form)
- Permission states (what authorizations are currently active)
- Relational states (what external parties have received what information)
- Computational states (what processes are running)

### World-State Transition

A transformation `W → W'` produced by an agent action. This is the core unit of governance. Transitions are characterized by their:
- **Type** (read, write, disclose, delegate, execute, etc.)
- **Direction** (internal or crossing a trust boundary)
- **Impact profile** (sensitivity, reversibility, persistence)

### Mandate

A grant of authority from a principal to an agent, specifying:
- What transitions the agent is permitted to propose
- Under what constraints
- For what duration

Mandates are not open-ended. They are scoped to specific transition types and resources. A mandate to "manage the inbox" does not include a mandate to "disclose inbox contents to third parties."

### Trust Boundary

A boundary between two domains with different security or governance contexts. A transition that crosses a trust boundary (e.g., from internal systems to an external partner) has higher governance requirements than a transition that stays within a boundary.

**Trust boundary types:** Internal, outbound_trusted, outbound_third_party

### Policy

A machine-evaluable rule set that maps Action Claims to evaluator responses. Policies are authored by principals (typically human administrators) and evaluated by the governance layer. Policies reference entity types from this ontology.

---

## System Flow

```
┌─────────────────────────────────────────────────────────┐
│                   Human Principal                       │
│  (authors mandate, defines policy, receives escalation) │
└────────────────────────┬────────────────────────────────┘
                         │ delegates mandate
                         ▼
┌─────────────────────────────────────────────────────────┐
│                       Agent                             │
│  (proposes world-state transition via Action Claim)     │
└────────────────────────┬────────────────────────────────┘
                         │ submits Action Claim
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Governance Layer                        │
│  - receives claim                                       │
│  - computes derived fields (capability_scope,           │
│    impact_profile, justification_gap)                   │
│  - evaluates against policy                             │
│  - produces evaluator response                          │
└────────────────────────┬────────────────────────────────┘
                         │ evaluates against
                         ▼
┌─────────────────────────────────────────────────────────┐
│                      Policy                             │
│  (machine-evaluable rules authored by principals)       │
└────────────────────────┬────────────────────────────────┘
                         │ response: approve / deny /
                         │ reduce-scope / escalate / sandbox
                         ▼
┌─────────────────────────────────────────────────────────┐
│                     Execution                           │
│  (world-state transition occurs only if approved)       │
└─────────────────────────────────────────────────────────┘
```

---

## Sensitivity Lattice

Sensitivity is a total order over four levels. The lattice is used to reason about effect composition: the sensitivity of a compound effect is the maximum sensitivity of its component effects.

```
CRITICAL
   │
   ▼
  HIGH
   │
   ▼
MEDIUM
   │
   ▼
  LOW
```

**Level definitions:**

| Level | Description | Examples |
|-------|-------------|---------|
| `LOW` | No significant harm potential | Reading internal non-personal data |
| `MEDIUM` | Moderate sensitivity; limited harm potential | Accessing personal data for authorized purpose |
| `HIGH` | Significant harm potential; regulatory relevance | Disclosing personal data; executing financial operations |
| `CRITICAL` | Severe or irreversible harm potential | Mass data disclosure; permanent deletion; system access modification |

The governance evaluator uses the sensitivity level as a primary determinant of evaluation tier and response type. See [`evaluation-model.md`](evaluation-model.md).

---

## Relationship to Existing Infrastructure

The Action Claim ontology does not replace existing infrastructure. It provides the semantic layer that allows existing systems to operate on a shared vocabulary.

| System | Relationship |
|--------|-------------|
| **MCP (Model Context Protocol)** | MCP defines the transport and tool-calling layer. Action Claims operate above MCP: the agent composes an Action Claim *before* invoking an MCP tool, and the claim describes the *effect* of the invocation, not the invocation itself. |
| **XACML / ABAC** | XACML and attribute-based access control systems evaluate access decisions based on subject, resource, and action attributes. Action Claims provide the structured object that ABAC/XACML policies evaluate. The claim's fields map to XACML request context attributes. |
| **OPA (Open Policy Agent)** | OPA evaluates policies expressed in Rego against structured JSON input. Action Claims are the natural input format for OPA-based governance. The `capability_scope.normative` field and `justification_gap.level` field can be derived directly from OPA policy evaluation. |
| **SPIFFE / SVID** | SPIFFE provides workload identity (cryptographic identity for software workloads). Action Claims reference agent identity via the delegation chain. SPIFFE SVIDs can serve as the identity anchor for agents in the chain. |

---

## Scope Limitations

The following are explicitly out of scope for this specification (v0.1):

1. **Intra-agent reasoning:** How an agent selects which action to take. The ontology governs what happens *after* selection, not the selection process itself.
2. **Training-time governance:** How model training affects agent behavior. The ontology operates at inference time.
3. **Cross-organization federation:** How governance systems from different organizations interoperate. This requires additional trust federation work beyond this spec.
4. **Real-time plan evaluation:** Evaluating full multi-step plans rather than individual claims. The composition axioms in this spec support net-effect reasoning but do not address plan-level evaluation.
5. **Natural language policies:** Policies expressed in natural language rather than machine-evaluable form. This spec assumes policies are machine-evaluable.
