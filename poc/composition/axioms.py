"""
Composition Axioms — four preliminary axioms for net-effect computation
across compound action sequences (paper Section 13).

Axiom 1: Sensitivity non-decreasing  sens(E(C)) = ⊔ { sens(tᵢ) }
Axiom 2: Disclosure transitivity     read(r) then disclose(derivative) = external disclosure of sens(r)
Axiom 3: Irreversibility propagates  one irreversible step → net irreversible
Axiom 4: Scope is the union          scope(E(C)) = ⋃ { scope(tᵢ) }
"""
from __future__ import annotations
from dataclasses import dataclass, field
from models.action_claim import (
    ProposedTransition, SensitivityLevel, Reversibility,
    Persistence, Direction, TransitionType, EffectMode,
)


@dataclass
class NetEffect:
    sensitivity: SensitivityLevel
    direction: Direction
    reversibility: Reversibility
    persistence: Persistence
    scope: list[str]
    disclosure_chain_detected: bool = False
    rationale: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            "Net Effect:",
            f"  sensitivity:    {self.sensitivity.value}",
            f"  direction:      {self.direction.value}",
            f"  reversibility:  {self.reversibility.value}",
            f"  persistence:    {self.persistence.value}",
            f"  scope:          {self.scope}",
        ]
        if self.disclosure_chain_detected:
            lines.append("  ⚠ Disclosure chain detected — Axiom 2 applied")
        if self.rationale:
            lines.append("  Axioms applied:")
            for r in self.rationale:
                lines.append(f"    - {r}")
        return "\n".join(lines)


def compute_net_effect(transitions: list[ProposedTransition]) -> NetEffect:
    if not transitions:
        raise ValueError("Cannot compute net effect of empty sequence.")

    rationale: list[str] = []
    read_resources: dict[str, SensitivityLevel] = {}

    # Axiom 1: Sensitivity non-decreasing
    net_sensitivity = SensitivityLevel.join(*[t.sensitivity for t in transitions])
    rationale.append(
        f"Axiom 1 — sensitivity join: {[t.sensitivity.value for t in transitions]} → {net_sensitivity.value}"
    )

    # Axiom 2: Disclosure transitivity
    disclosure_chain = False
    net_direction = Direction.INTERNAL
    for t in transitions:
        if t.operation.value == "read":
            read_resources[t.target_resource.id] = t.sensitivity
        if t.direction in (Direction.OUTBOUND_TRUSTED, Direction.OUTBOUND_THIRD_PARTY):
            net_direction = t.direction
            if read_resources:
                max_read = SensitivityLevel.join(*read_resources.values())
                net_sensitivity = SensitivityLevel.join(net_sensitivity, max_read)
                disclosure_chain = True
                rationale.append(
                    f"Axiom 2 — disclosure transitivity: previously read {list(read_resources.keys())} "
                    f"at {max_read.value}, now disclosing externally → net sensitivity elevated to {net_sensitivity.value}"
                )

    # Axiom 3: Irreversibility propagates
    irreversible_steps = [
        t for t in transitions
        if t.effect_mode == EffectMode.PERSISTENT
        or t.transition_type in {TransitionType.EXTERNAL_DATA_DISCLOSURE, TransitionType.EXTERNAL_DELEGATION}
    ]
    net_reversibility = Reversibility.IRREVERSIBLE if irreversible_steps else Reversibility.REVERSIBLE
    if irreversible_steps:
        rationale.append(
            f"Axiom 3 — irreversibility propagates: {len(irreversible_steps)} irreversible step(s) → net is IRREVERSIBLE"
        )
    net_persistence = Persistence.PERMANENT if net_reversibility == Reversibility.IRREVERSIBLE else Persistence.TRANSIENT

    # Axiom 4: Scope is the union
    seen: set[str] = set()
    all_scope: list[str] = []
    for t in transitions:
        for item in t.data_scope:
            if item not in seen:
                all_scope.append(item)
                seen.add(item)
        rk = f"{t.target_resource.type}:{t.target_resource.id}"
        if rk not in seen:
            all_scope.append(rk)
            seen.add(rk)
    rationale.append(
        f"Axiom 4 — scope union: {len(transitions)} step(s) → {len(all_scope)} distinct entities"
    )

    return NetEffect(
        sensitivity=net_sensitivity,
        direction=net_direction,
        reversibility=net_reversibility,
        persistence=net_persistence,
        scope=all_scope,
        disclosure_chain_detected=disclosure_chain,
        rationale=rationale,
    )


def is_net_effect_high_risk(net: NetEffect) -> bool:
    return (
        net.sensitivity >= SensitivityLevel.HIGH
        or net.reversibility == Reversibility.IRREVERSIBLE
        or net.direction == Direction.OUTBOUND_THIRD_PARTY
        or net.disclosure_chain_detected
    )
