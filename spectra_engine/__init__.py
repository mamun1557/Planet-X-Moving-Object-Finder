"""
SPECTRA Engine Packaging Interface
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Authoritative package for the SPECTRA Evidence Adapter, FUSION Contract,
and Continuum Sidecar Interface.
Zero dependencies on models.spectra or application frameworks.
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
    SpectraFusionEvidenceRecord,
    EligibilityStatus,
    ThresholdExceedanceLevel,
    EvidenceStrength,
    CrossModalStatus,
)
from spectra_engine.spectra_evidence_adapter import SpectraEvidenceAdapter
from spectra_engine.continuum_sidecar_interface import (
    ContinuumSidecarInterface,
    ContinuumEvidenceRecord,
    SIDECAR_CONTRACT_VERSION,
    ALLOWED_EVIDENCE_STATES,
    BASE_SIDECAR_LIMITATION_CODES,
)
from spectra_engine.continuum_sidecar_engine import EmpiricalContinuumSidecar

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
    "SpectraFusionEvidenceRecord",
    "EligibilityStatus",
    "ThresholdExceedanceLevel",
    "EvidenceStrength",
    "CrossModalStatus",
    "SpectraEvidenceAdapter",
    "ContinuumSidecarInterface",
    "ContinuumEvidenceRecord",
    "EmpiricalContinuumSidecar",
    "SIDECAR_CONTRACT_VERSION",
    "ALLOWED_EVIDENCE_STATES",
    "BASE_SIDECAR_LIMITATION_CODES",
]
