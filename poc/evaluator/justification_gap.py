"""
Justification Gap Evaluator — medium complexity scoring.
Four signals: hop count (30%), abstraction delta (25%),
action divergence (25%), scope expansion (20%).
"""
from __future__ import annotations
from models.action_claim import (
    ActionClaim, JustificationGap, GapLevel, TransitionType, Direction,
)

WEIGHT_HOP_COUNT        = 0.30
WEIGHT_ABSTRACTION_DELTA = 0.25
WEIGHT_ACTION_DIVERGENCE = 0.25
WEIGHT_SCOPE_EXPANSION   = 0.20

GAP_LOW_THRESHOLD    = 35
GAP_MEDIUM_THRESHOLD = 65

HIGH_RISK_TRANSITIONS = {
    TransitionType.EXTERNAL_DATA_DISCLOSURE,
    TransitionType.EXTERNAL_DELEGATION,
    TransitionType.EXTERNAL_EXECUTE,
}

TRANSITION_VOCABULARY: dict[TransitionType, list[str]] = {
    TransitionType.INTERNAL_READ:            ["read", "get", "fetch", "retrieve", "check", "collect", "gather", "look up"],
    TransitionType.INTERNAL_WRITE:           ["write", "save", "store", "update", "create", "record"],
    TransitionType.INTERNAL_EXECUTE:         ["run", "execute", "process", "compute", "analyze", "generate", "prepare"],
    TransitionType.EXTERNAL_DATA_DISCLOSURE: ["send", "share", "disclose", "transmit", "export", "forward", "publish"],
    TransitionType.EXTERNAL_DELEGATION:      ["delegate", "assign", "transfer", "hand off"],
    TransitionType.EXTERNAL_EXECUTE:         ["trigger", "invoke", "call", "activate"],
    TransitionType.NOTIFY:                   ["notify", "alert", "message", "inform"],
    TransitionType.ESCALATE:                 ["escalate", "confirm", "request approval"],
}


def evaluate_justification_gap(claim: ActionClaim) -> JustificationGap:
    chain = claim.delegation_chain
    transition = claim.proposed_transition

    if not chain:
        return JustificationGap(
            level=GapLevel.HIGH, gap_rationale="No delegation chain.",
            local_gap=GapLevel.HIGH, chain_gap=GapLevel.HIGH, hop_count=0,
        )

    hop_count          = len(chain)
    originating_mandate = chain[0].mandate
    immediate_mandate   = chain[-1].mandate

    hop_score        = _score_hop_count(hop_count)
    abstraction_score = _score_abstraction_delta(originating_mandate, transition.transition_type)
    divergence_score  = _score_action_divergence(immediate_mandate, transition.transition_type)
    scope_score       = _score_scope_expansion(originating_mandate, transition)

    local_score = divergence_score * 0.5 + scope_score * 0.3 + abstraction_score * 0.2
    chain_score = (
        hop_score        * WEIGHT_HOP_COUNT +
        abstraction_score * WEIGHT_ABSTRACTION_DELTA +
        divergence_score  * WEIGHT_ACTION_DIVERGENCE +
        scope_score       * WEIGHT_SCOPE_EXPANSION
    )

    local_gap = _score_to_level(local_score)
    chain_gap = _score_to_level(chain_score)
    overall   = _max_gap(local_gap, chain_gap)

    return JustificationGap(
        level=overall,
        gap_rationale=_build_rationale(
            hop_count, originating_mandate, immediate_mandate,
            transition, chain_gap, scope_score > 50, divergence_score > 50,
        ),
        local_gap=local_gap,
        chain_gap=chain_gap,
        hop_count=hop_count,
        scope_expansion_detected=scope_score > 50,
        action_type_divergence=divergence_score > 50,
    )


def _score_hop_count(n: int) -> float:
    if n <= 1: return 0.0
    if n == 2: return 30.0
    if n == 3: return 60.0
    return min(85.0 + (n - 4) * 5, 100.0)


def _score_abstraction_delta(mandate: str, tt: TransitionType) -> float:
    if any(kw in mandate.lower() for kw in TRANSITION_VOCABULARY.get(tt, [])):
        return 0.0
    return 80.0 if tt in HIGH_RISK_TRANSITIONS else 50.0


def _score_action_divergence(mandate: str, tt: TransitionType) -> float:
    if any(kw in mandate.lower() for kw in TRANSITION_VOCABULARY.get(tt, [])):
        return 0.0
    return 85.0 if tt in HIGH_RISK_TRANSITIONS else 45.0


def _score_scope_expansion(mandate: str, transition) -> float:
    score = 0.0
    internal_words = ["report", "analyze", "prepare", "review", "check", "read"]
    if any(w in mandate.lower() for w in internal_words) and transition.direction.value.startswith("outbound"):
        score += 50.0
    if len(transition.data_scope) > 2:
        score += 20.0
    if transition.effect_mode.value == "persistent" and transition.direction.value.startswith("outbound"):
        score += 30.0
    return min(score, 100.0)


def _score_to_level(score: float) -> GapLevel:
    if score <= GAP_LOW_THRESHOLD:    return GapLevel.LOW
    if score <= GAP_MEDIUM_THRESHOLD: return GapLevel.MEDIUM
    return GapLevel.HIGH


def _max_gap(a: GapLevel, b: GapLevel) -> GapLevel:
    order = {GapLevel.LOW: 0, GapLevel.MEDIUM: 1, GapLevel.HIGH: 2}
    return a if order[a] >= order[b] else b


def _build_rationale(hop_count, orig, immed, transition, chain_gap, scope_exp, div) -> str:
    parts = [
        f"{hop_count} delegation hop(s)",
        f"originating mandate: '{orig}'",
        f"immediate mandate: '{immed}'",
        f"proposed: {transition.transition_type.value} ({transition.direction.value})",
    ]
    if div:       parts.append("action type not implied by immediate mandate vocabulary")
    if scope_exp: parts.append("scope expansion detected relative to originating mandate")
    if chain_gap == GapLevel.HIGH: parts.append("chain-level gap is HIGH")
    return "; ".join(parts)
