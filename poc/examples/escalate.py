"""Example: Escalate — paper's canonical instance (Section 11). Expected: ESCALATE."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.action_claim import (
    ActionClaim, ProposedTransition, DelegationHop,
    TransitionType, Operation, TargetResource, Destination, TransitionSemantics,
    Direction, EffectMode, SensitivityLevel,
)
from evaluator.engine import evaluate


def build_claim():
    return ActionClaim(
        proposed_transition=ProposedTransition(
            transition_type=TransitionType.EXTERNAL_DATA_DISCLOSURE,
            operation=Operation.DISCLOSE,
            target_resource=TargetResource(type="user_profile", id="user_123"),
            destination=Destination(system="crm_partner_z", jurisdiction="EU"),
            data_scope=["email", "phone", "transaction_summary"],
            effect_mode=EffectMode.PERSISTENT,
            sensitivity=SensitivityLevel.HIGH,
            direction=Direction.OUTBOUND_THIRD_PARTY,
            transition_semantics=TransitionSemantics(
                summary="Send contact and financial summary to CRM Partner Z",
                world_effect="Partner Z acquires a persistent copy of user data",
                why_now="Report requires external financial consolidation",
            ),
        ),
        originating_goal="Collect financial data for quarterly report",
        relevant_context_basis=["CRM Partner Z has active data-sharing agreement"],
        preconditions=[
            "user_123 has consented to this disclosure",
            "crm_partner_z is on the approved-systems registry",
            "data is correctly classified as financial + PII",
        ],
        delegation_chain=[
            DelegationHop(principal="human:user_X",          mandate="prepare quarterly report"),
            DelegationHop(principal="agent:report-orchestrator", mandate="collect financial data"),
            DelegationHop(principal="agent:data-collector",   mandate="send data to CRM"),
        ],
    )


if __name__ == "__main__":
    claim = build_claim()
    result = evaluate(claim)
    print("=" * 60)
    print("EXAMPLE: Paper's canonical instance (Section 11)")
    print("=" * 60)
    print(result)
    print()
    gap = claim.justification_gap
    print(
        f"Justification Gap:\n"
        f"  level:       {gap.level.value}\n"
        f"  chain_gap:   {gap.chain_gap.value}\n"
        f"  hop_count:   {gap.hop_count}\n"
        f"  rationale:   {gap.gap_rationale}"
    )
    ip = claim.impact_profile
    print(
        f"\nImpact Profile:\n"
        f"  reversibility: {ip.reversibility.value}\n"
        f"  persistence:   {ip.persistence.value}\n"
        f"  sensitivity:   {ip.sensitivity.value}\n"
        f"  regulatory:    {ip.regulatory_significance}"
    )
