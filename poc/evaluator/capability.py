"""
Capability Scope Evaluator
Computes capability_scope — derived by system, never agent-authored.
"""
from __future__ import annotations
from models.action_claim import (
    ActionClaim, CapabilityScope, AuthorizationStatus,
    TransitionType, Direction,
)

AGENT_CAPABILITY_REGISTRY: dict[str, list[TransitionType]] = {
    "agent:report-orchestrator": [
        TransitionType.INTERNAL_READ,
        TransitionType.INTERNAL_WRITE,
        TransitionType.INTERNAL_EXECUTE,
    ],
    "agent:data-collector": [
        TransitionType.INTERNAL_READ,
        TransitionType.EXTERNAL_DATA_DISCLOSURE,
    ],
    "agent:notifier": [TransitionType.NOTIFY],
}

NORMATIVE_REVIEW_REQUIRED: set[TransitionType] = {
    TransitionType.EXTERNAL_DATA_DISCLOSURE,
    TransitionType.EXTERNAL_DELEGATION,
    TransitionType.EXTERNAL_EXECUTE,
}

ALWAYS_RESTRICTED: set[TransitionType] = {TransitionType.EXTERNAL_DELEGATION}

MANDATE_TRANSITION_MAP = {
    TransitionType.INTERNAL_READ:            ["read", "collect", "fetch", "gather", "retrieve"],
    TransitionType.INTERNAL_WRITE:           ["write", "update", "store", "save", "create"],
    TransitionType.INTERNAL_EXECUTE:         ["execute", "run", "process", "compute", "analyze"],
    TransitionType.EXTERNAL_DATA_DISCLOSURE: ["send", "disclose", "share", "transmit", "export"],
    TransitionType.NOTIFY:                   ["notify", "alert", "inform", "message"],
    TransitionType.ESCALATE:                 ["escalate", "confirm", "approve"],
}


def evaluate_capability_scope(claim: ActionClaim) -> CapabilityScope:
    transition = claim.proposed_transition
    current_agent = claim.delegation_chain[-1].principal if claim.delegation_chain else "unknown"
    technical = _evaluate_technical(current_agent, transition.transition_type)
    normative = _evaluate_normative(current_agent, transition.transition_type, transition.direction, claim)
    return CapabilityScope(technical=technical, normative=normative)


def _evaluate_technical(agent: str, transition_type: TransitionType) -> AuthorizationStatus:
    if transition_type in ALWAYS_RESTRICTED:
        return AuthorizationStatus.UNAUTHORIZED
    allowed = AGENT_CAPABILITY_REGISTRY.get(agent, [])
    if not allowed:
        return AuthorizationStatus.REQUIRES_REVIEW
    return AuthorizationStatus.AUTHORIZED if transition_type in allowed else AuthorizationStatus.UNAUTHORIZED


def _evaluate_normative(agent, transition_type, direction, claim) -> AuthorizationStatus:
    if transition_type in ALWAYS_RESTRICTED:
        return AuthorizationStatus.UNAUTHORIZED
    if transition_type in NORMATIVE_REVIEW_REQUIRED:
        return AuthorizationStatus.REQUIRES_REVIEW
    if direction == Direction.OUTBOUND_THIRD_PARTY:
        return AuthorizationStatus.REQUIRES_REVIEW
    if not claim.delegation_chain:
        return AuthorizationStatus.REQUIRES_REVIEW
    mandate_lower = claim.delegation_chain[-1].mandate.lower()
    keywords = MANDATE_TRANSITION_MAP.get(transition_type, [])
    return (
        AuthorizationStatus.AUTHORIZED
        if any(kw in mandate_lower for kw in keywords)
        else AuthorizationStatus.REQUIRES_REVIEW
    )
