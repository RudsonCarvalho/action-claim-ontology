"""
Governance Evaluation Engine
Orchestrates the full 5-step evaluation pipeline for an ActionClaim.
"""
from __future__ import annotations
from models.action_claim import (
    ActionClaim, EvaluationResult, EvaluatorResponse,
    GapLevel, SensitivityLevel, Reversibility, AuthorizationStatus,
)
from evaluator.capability import evaluate_capability_scope
from evaluator.impact import evaluate_impact_profile
from evaluator.justification_gap import evaluate_justification_gap

UNVERIFIABLE_KEYWORDS = [
    "consented", "consent", "agreed", "authorized by user",
    "user has approved", "gdpr consent", "opt-in",
]


def _classify_preconditions(preconditions):
    verifiable, unverifiable = [], []
    for p in preconditions:
        target = unverifiable if any(kw in p.lower() for kw in UNVERIFIABLE_KEYWORDS) else verifiable
        target.append(p)
    return verifiable, unverifiable


def _determine_response(claim, unverifiable):
    cap    = claim.capability_scope
    impact = claim.impact_profile
    gap    = claim.justification_gap

    if cap.overall == AuthorizationStatus.UNAUTHORIZED:
        return (
            EvaluatorResponse.DENY,
            f"Capability unauthorized: technical={cap.technical.value}, normative={cap.normative.value}",
        )

    if unverifiable:
        return (
            EvaluatorResponse.ESCALATE,
            f"Unverifiable precondition(s) require human confirmation: {unverifiable}",
        )

    if gap.level == GapLevel.HIGH and impact.is_high_risk:
        return (
            EvaluatorResponse.ESCALATE,
            f"High justification gap ({gap.chain_gap.value} chain-level) combined with high-risk impact "
            f"profile (sensitivity={impact.sensitivity.value}, reversibility={impact.reversibility.value})",
        )

    if impact.reversibility == Reversibility.IRREVERSIBLE and impact.sensitivity >= SensitivityLevel.HIGH:
        return (
            EvaluatorResponse.ESCALATE,
            f"Irreversible action with HIGH+ sensitivity ({impact.sensitivity.value}) requires human confirmation",
        )

    if cap.overall == AuthorizationStatus.REQUIRES_REVIEW and impact.is_high_risk:
        return (
            EvaluatorResponse.ESCALATE,
            "Normative authorization uncertain (REQUIRES_REVIEW) for high-risk action",
        )

    if cap.overall == AuthorizationStatus.REQUIRES_REVIEW:
        return (
            EvaluatorResponse.SANDBOX,
            "Normative authorization uncertain; executing in sandbox (no persistent effects)",
        )

    return (
        EvaluatorResponse.APPROVE,
        f"All checks passed: capability={cap.overall.value}, gap={gap.level.value}, "
        f"sensitivity={impact.sensitivity.value}, reversibility={impact.reversibility.value}",
    )


def evaluate(claim: ActionClaim) -> EvaluationResult:
    # Step 2: Compute derived fields (system-authored, never agent-authored)
    claim.capability_scope  = evaluate_capability_scope(claim)
    claim.impact_profile    = evaluate_impact_profile(claim)
    claim.justification_gap = evaluate_justification_gap(claim)

    # Step 3: Classify preconditions
    _, unverifiable = _classify_preconditions(claim.preconditions)

    # Steps 4-5: Evaluate policy and produce response
    response, rationale = _determine_response(claim, unverifiable)

    return EvaluationResult(
        response=response,
        rationale=rationale,
        claim=claim,
        unverifiable_preconditions=unverifiable,
    )
