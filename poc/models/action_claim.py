"""
Action Claim — Core Data Models
================================
Toward an Operational Ontology of Agentic Action
https://doi.org/10.5281/zenodo.18930044

Defines the canonical ActionClaim object and all constituent types.
Field authorship follows the tripartite structure of the paper:
  - Declared by the agent
  - Derived by the system (never agent-authored)
  - Supplied by the delegation infrastructure
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TransitionType(str, Enum):
    INTERNAL_READ            = "internal_read"
    INTERNAL_WRITE           = "internal_write"
    INTERNAL_EXECUTE         = "internal_execute"
    EXTERNAL_DATA_DISCLOSURE = "external_data_disclosure"
    EXTERNAL_DELEGATION      = "external_delegation"
    EXTERNAL_EXECUTE         = "external_execute"
    NOTIFY                   = "notify"
    ESCALATE                 = "escalate"


class Operation(str, Enum):
    READ     = "read"
    CREATE   = "create"
    UPDATE   = "update"
    DELETE   = "delete"
    DISCLOSE = "disclose"
    DELEGATE = "delegate"
    EXECUTE  = "execute"
    NOTIFY   = "notify"
    ESCALATE = "escalate"


class Direction(str, Enum):
    INTERNAL             = "internal"
    OUTBOUND_TRUSTED     = "outbound_trusted"
    OUTBOUND_THIRD_PARTY = "outbound_third_party"


class EffectMode(str, Enum):
    TRANSIENT  = "transient"
    PERSISTENT = "persistent"


class SensitivityLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

    def __ge__(self, other: SensitivityLevel) -> bool:
        order = [self.LOW, self.MEDIUM, self.HIGH, self.CRITICAL]
        return order.index(self) >= order.index(other)

    def __gt__(self, other: SensitivityLevel) -> bool:
        order = [self.LOW, self.MEDIUM, self.HIGH, self.CRITICAL]
        return order.index(self) > order.index(other)

    @classmethod
    def join(cls, *levels: SensitivityLevel) -> SensitivityLevel:
        """Lattice join (least upper bound) — Axiom 1."""
        order = [cls.LOW, cls.MEDIUM, cls.HIGH, cls.CRITICAL]
        return max(levels, key=lambda s: order.index(s))


class Reversibility(str, Enum):
    REVERSIBLE   = "REVERSIBLE"
    IRREVERSIBLE = "IRREVERSIBLE"


class Persistence(str, Enum):
    TRANSIENT  = "TRANSIENT"
    PERMANENT  = "PERMANENT"


class AuthorizationStatus(str, Enum):
    AUTHORIZED      = "AUTHORIZED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNAUTHORIZED    = "UNAUTHORIZED"


class GapLevel(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"


class EvaluatorResponse(str, Enum):
    APPROVE      = "approve"
    DENY         = "deny"
    REDUCE_SCOPE = "reduce-scope"
    ESCALATE     = "escalate"
    SANDBOX      = "sandbox"


@dataclass
class TargetResource:
    type: str
    id: str


@dataclass
class Destination:
    system: str
    jurisdiction: str


@dataclass
class TransitionSemantics:
    summary: str
    world_effect: str
    why_now: str


@dataclass
class ProposedTransition:
    transition_type: TransitionType
    operation: Operation
    target_resource: TargetResource
    effect_mode: EffectMode
    sensitivity: SensitivityLevel
    direction: Direction
    data_scope: list[str] = field(default_factory=list)
    destination: Optional[Destination] = None
    transition_semantics: Optional[TransitionSemantics] = None


@dataclass
class CapabilityScope:
    technical: AuthorizationStatus
    normative: AuthorizationStatus

    @property
    def overall(self) -> AuthorizationStatus:
        order = {
            AuthorizationStatus.AUTHORIZED: 0,
            AuthorizationStatus.REQUIRES_REVIEW: 1,
            AuthorizationStatus.UNAUTHORIZED: 2,
        }
        return max([self.technical, self.normative], key=lambda s: order[s])


@dataclass
class ImpactProfile:
    reversibility: Reversibility
    persistence: Persistence
    sensitivity: SensitivityLevel
    scope_of_affected_entities: str = ""
    financial_cost: Optional[dict] = None
    regulatory_significance: str = "NONE"
    externalities: list[str] = field(default_factory=list)

    @property
    def is_high_risk(self) -> bool:
        return (
            self.reversibility == Reversibility.IRREVERSIBLE
            or self.sensitivity >= SensitivityLevel.HIGH
            or self.persistence == Persistence.PERMANENT
        )


@dataclass
class JustificationGap:
    level: GapLevel
    gap_rationale: str
    local_gap: GapLevel
    chain_gap: GapLevel
    hop_count: int = 0
    scope_expansion_detected: bool = False
    action_type_divergence: bool = False


@dataclass
class DelegationHop:
    principal: str
    mandate: str
    constraints: list[str] = field(default_factory=list)
    delegated_at: Optional[str] = None


@dataclass
class ActionClaim:
    # Declared by the agent
    proposed_transition: ProposedTransition
    originating_goal: str
    relevant_context_basis: list[str]
    preconditions: list[str]

    # Derived by the system (populated by evaluator, never by agent)
    capability_scope: Optional[CapabilityScope] = None
    impact_profile: Optional[ImpactProfile] = None
    justification_gap: Optional[JustificationGap] = None

    # Supplied by delegation infrastructure
    delegation_chain: list[DelegationHop] = field(default_factory=list)

    def is_evaluated(self) -> bool:
        return all([
            self.capability_scope is not None,
            self.impact_profile is not None,
            self.justification_gap is not None,
        ])


@dataclass
class EvaluationResult:
    response: EvaluatorResponse
    rationale: str
    claim: ActionClaim
    unverifiable_preconditions: list[str] = field(default_factory=list)
    audit_record: bool = False

    def __post_init__(self):
        if self.response in (EvaluatorResponse.DENY, EvaluatorResponse.ESCALATE):
            self.audit_record = True

    def __str__(self) -> str:
        lines = [
            f"Response:  {self.response.value.upper()}",
            f"Rationale: {self.rationale}",
        ]
        if self.unverifiable_preconditions:
            lines.append(f"Unverifiable preconditions: {self.unverifiable_preconditions}")
        if self.audit_record:
            lines.append("Audit record: CREATED")
        return "\n".join(lines)
