"""
SPECTRA-X / F1 — Phase 3, Task 1.3B
Backward Compatibility Re-Export Shim for SPECTRA Fusion Contract

Authoritative implementation has been relocated to `spectra_engine.fusion_contract`.
This module is maintained strictly for backward compatibility with existing callers.
"""

from spectra_engine.fusion_contract import (
    CONTRACT_VERSION,
    SPECTRA_FUSION_EVIDENCE_V1,
    MODEL_ID,
    MODEL_VERSION,
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_THRESHOLDS_SHA256,
    EXPECTED_CALIB_SCORES_SHA256,
    PIPELINE_BUILD,
    VALID_STRATA,
    CANONICAL_STRATA_MAP,
    BASE_LIMITATION_CODES,
    STRATUM_LIMITATION_CODES,
    EligibilityStatus,
    ThresholdExceedanceLevel,
    EvidenceStrength,
    CrossModalStatus,
    SpectraFusionEvidenceRecord,
)

__all__ = [
    "CONTRACT_VERSION",
    "SPECTRA_FUSION_EVIDENCE_V1",
    "MODEL_ID",
    "MODEL_VERSION",
    "EXPECTED_CHECKPOINT_SHA256",
    "EXPECTED_THRESHOLDS_SHA256",
    "EXPECTED_CALIB_SCORES_SHA256",
    "PIPELINE_BUILD",
    "VALID_STRATA",
    "CANONICAL_STRATA_MAP",
    "BASE_LIMITATION_CODES",
    "STRATUM_LIMITATION_CODES",
    "EligibilityStatus",
    "ThresholdExceedanceLevel",
    "EvidenceStrength",
    "CrossModalStatus",
    "SpectraFusionEvidenceRecord",
]
