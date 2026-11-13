"""
SPECTRA Package Interface
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Backward compatibility interface re-exporting from authoritative spectra_engine.
"""

from spectra_engine.fusion_contract import (
    CONTRACT_VERSION,
    SPECTRA_FUSION_EVIDENCE_V1,
    MODEL_ID,
    MODEL_VERSION,
    PIPELINE_BUILD,
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
)

__all__ = [
    "CONTRACT_VERSION",
    "SPECTRA_FUSION_EVIDENCE_V1",
    "MODEL_ID",
    "MODEL_VERSION",
    "PIPELINE_BUILD",
    "SpectraFusionEvidenceRecord",
    "EligibilityStatus",
    "ThresholdExceedanceLevel",
    "EvidenceStrength",
    "CrossModalStatus",
    "SpectraEvidenceAdapter",
    "ContinuumSidecarInterface",
    "ContinuumEvidenceRecord",
    "SIDECAR_CONTRACT_VERSION",
]
