"""
CHRONOS-X Package Interface
Temporal Change Detection and Eligibility Verification
"""

try:
    from .model import ChronosTemporalDifferencer, FATAL_FLAG_MASK
except ImportError:
    ChronosTemporalDifferencer = None
    FATAL_FLAG_MASK = 615

from .temporal_eligibility import (
    TemporalEligibilityResult,
    evaluate_pair_temporal_eligibility,
    determine_dataset_temporal_availability,
    DEFAULT_MIN_BASELINE_DAYS,
    BASELINE_POLICY_VERSION,
    ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES,
    ALLOWED_DATASET_AVAILABILITY_STATUSES,
    ALLOWED_EVIDENCE_TIERS,
)

__all__ = [
    "ChronosTemporalDifferencer",
    "FATAL_FLAG_MASK",
    "TemporalEligibilityResult",
    "evaluate_pair_temporal_eligibility",
    "determine_dataset_temporal_availability",
    "DEFAULT_MIN_BASELINE_DAYS",
    "BASELINE_POLICY_VERSION",
    "ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES",
    "ALLOWED_DATASET_AVAILABILITY_STATUSES",
    "ALLOWED_EVIDENCE_TIERS",
]
