"""Example: Approve — low-risk internal read. Expected: APPROVE."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.action_claim import (
    ActionClaim, ProposedTransition, DelegationHop,
    TransitionType, Operation, TargetResource,
    Direction, EffectMode, SensitivityLevel,
)
from evaluator.engine import evaluate


def build_claim():
    return ActionClaim(
        proposed_transition=ProposedTransition(
            transition_type=TransitionType.INTERNAL_READ,
            operation=Operation.READ,
            target_resource=TargetResource(type="report_draft", id="q3_draft_001"),
            data_scope=["report_text"],
            effect_mode=EffectMode.TRANSIENT,
            sensitivity=SensitivityLevel.LOW,
            direction=Direction.INTERNAL,
        ),
        originating_goal="Prepare quarterly report",
        relevant_context_basis=[
            "Report draft q3_draft_001 exists",
            "Agent is in active report preparation session",
        ],
        preconditions=[
            "report_draft q3_draft_001 exists",
            "agent has read access to document store",
        ],
        delegation_chain=[
            DelegationHop(principal="human:user_X", mandate="prepare quarterly report"),
            DelegationHop(principal="agent:report-orchestrator", mandate="read report draft"),
        ],
    )


if __name__ == "__main__":
    result = evaluate(build_claim())
    print("=" * 60)
    print("EXAMPLE: Simple approval — internal read")
    print("=" * 60)
    print(result)
