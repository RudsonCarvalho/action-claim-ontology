"""
Impact Profile Evaluator
Computes impact_profile from actual proposed_transition content —
not from agent-declared labels (paper Section 10.1, Failure Mode 1).
"""
from __future__ import annotations
from models.action_claim import (
    ActionClaim, ImpactProfile, TransitionType, Direction,
    EffectMode, SensitivityLevel, Reversibility, Persistence,
)

GDPR_DATA_CATEGORIES = {
    "email", "phone", "address", "name", "pii", "personal", "financial",
    "transaction", "health", "medical", "biometric", "location",
    "ip_address", "cookie", "identifier",
}
HIPAA_DATA_CATEGORIES = {
    "health", "medical", "diagnosis", "treatment", "prescription",
    "patient", "clinical", "phi",
}
FINANCIAL_CATEGORIES = {
    "financial", "transaction", "payment", "bank", "credit",
    "invoice", "revenue", "salary", "account",
}


def evaluate_impact_profile(claim: ActionClaim) -> ImpactProfile:
    t = claim.proposed_transition
    return ImpactProfile(
        reversibility=_compute_reversibility(t.transition_type, t.effect_mode),
        persistence=_compute_persistence(t.effect_mode, t.transition_type),
        sensitivity=_compute_effective_sensitivity(t.sensitivity, t.data_scope, t.direction),
        scope_of_affected_entities=_describe_scope(t),
        regulatory_significance=_compute_regulatory_significance(t.data_scope, t.destination),
        externalities=_detect_externalities(t),
    )


def _compute_reversibility(transition_type, effect_mode):
    if transition_type in {TransitionType.EXTERNAL_DATA_DISCLOSURE, TransitionType.EXTERNAL_DELEGATION}:
        return Reversibility.IRREVERSIBLE
    return Reversibility.IRREVERSIBLE if effect_mode == EffectMode.PERSISTENT else Reversibility.REVERSIBLE


def _compute_persistence(effect_mode, transition_type):
    if transition_type in {TransitionType.EXTERNAL_DATA_DISCLOSURE, TransitionType.EXTERNAL_DELEGATION}:
        return Persistence.PERMANENT
    return Persistence.PERMANENT if effect_mode == EffectMode.PERSISTENT else Persistence.TRANSIENT


def _compute_effective_sensitivity(declared, data_scope, direction):
    scope_lower = {s.lower() for s in data_scope}
    detected = declared
    if scope_lower & GDPR_DATA_CATEGORIES or scope_lower & FINANCIAL_CATEGORIES:
        detected = SensitivityLevel.join(detected, SensitivityLevel.HIGH)
    if scope_lower & HIPAA_DATA_CATEGORIES:
        detected = SensitivityLevel.join(detected, SensitivityLevel.CRITICAL)
    if direction == Direction.OUTBOUND_THIRD_PARTY:
        order = [SensitivityLevel.LOW, SensitivityLevel.MEDIUM, SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]
        detected = order[min(order.index(detected) + 1, len(order) - 1)]
    return detected


def _compute_regulatory_significance(data_scope, destination):
    scope_lower = {s.lower() for s in data_scope}
    flags = []
    if scope_lower & GDPR_DATA_CATEGORIES:
        flags.append("GDPR_SCOPED")
    if scope_lower & HIPAA_DATA_CATEGORIES:
        flags.append("HIPAA_SCOPED")
    if scope_lower & FINANCIAL_CATEGORIES:
        flags.append("FINANCIAL_REGULATION_SCOPED")
    if destination and destination.jurisdiction.upper() in ("EU", "EEA") and "GDPR_SCOPED" not in flags:
        flags.append("GDPR_SCOPED")
    return " | ".join(flags) if flags else "NONE"


def _detect_externalities(t):
    out = []
    if t.direction == Direction.OUTBOUND_THIRD_PARTY:
        out.append("Data copy created outside current trust boundary")
    if t.effect_mode == EffectMode.PERSISTENT and t.destination:
        out.append(f"Persistent record in external system: {t.destination.system}")
    return out


def _describe_scope(t):
    parts = [f"resource:{t.target_resource.type}:{t.target_resource.id}"]
    if t.data_scope:
        parts.append(f"data:{','.join(t.data_scope)}")
    if t.destination:
        parts.append(f"destination:{t.destination.system}")
    return " | ".join(parts)
