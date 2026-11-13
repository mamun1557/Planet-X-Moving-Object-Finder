"""
SPECTRA-X / F1 — Phase 3, Task 1.3B & Phase 4, Task 4.7
Continuum Sidecar Evidence Interface Specification & Authoritative Data Contract

Package: spectra_engine

Scientific Context:
Task 1.2D/1.2E established that the SPECTRA V2 masked autoencoder is primarily an emission-line /
localized spectral feature anomaly detector with limited sensitivity to smooth continuum tilts
(12.13% recovery on broad infrared excess).

Phase 4 Task 4.7 integrates the Task 4.6 empirical infrared excess validation engine
into the authoritative CONTINUUM_SIDECAR_EVIDENCE_V1 contract for downstream consumption
by FUSION-X without modifying the frozen SPECTRA model weights or thresholds.
"""

import math
import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Set, Union


SIDECAR_CONTRACT_VERSION = "CONTINUUM_SIDECAR_EVIDENCE_V1"
CONTRACT_VERSION = SIDECAR_CONTRACT_VERSION
CONTINUUM_SIDECAR_EVIDENCE_V1 = SIDECAR_CONTRACT_VERSION

# Task 4.10 Authoritative Calibration Allowlist
CANONICAL_CALIBRATION_POINTING = "P0008"
AUTHORIZED_CALIBRATION_POINTINGS = frozenset({"P0008"})

# Authoritative Evidence States (Task 4.6 Governance Taxonomy)
ALLOWED_EVIDENCE_STATES = {
    "PENDING_VALIDATION",
    "SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
    "POSSIBLE_INFRARED_EXCESS",
    "QUALITY_FLAGGED",
    "INSUFFICIENT_PHOTOMETRY",
    "AMBIGUOUS_COUNTERPART",
    "UNVERIFIABLE"
}

# Standard Scientific Limitation Codes (Section 6 Audit)
BASE_SIDECAR_LIMITATION_CODES = [
    "EMPIRICAL_COLOR_BASELINE_ONLY",
    "INDEPENDENT_ERROR_QUADRATURE_ASSUMPTION",
    "PRELIMINARY_FLUX_SCALE_CONSISTENCY_CHECK"
]


# ==============================================================================
# Task 4.10: Deep-Freeze Immutable Data Structures
# ==============================================================================
class ReadOnlyList(list):
    """Immutable sequence wrapper for contract limitation codes and collections."""
    def append(self, *args, **kwargs):
        raise TypeError("ReadOnlyList does not support append: ContinuumEvidenceRecord collections are immutable.")
    def extend(self, *args, **kwargs):
        raise TypeError("ReadOnlyList does not support extend: ContinuumEvidenceRecord collections are immutable.")
    def insert(self, *args, **kwargs):
        raise TypeError("ReadOnlyList does not support insert: ContinuumEvidenceRecord collections are immutable.")
    def remove(self, *args, **kwargs):
        raise TypeError("ReadOnlyList does not support remove: ContinuumEvidenceRecord collections are immutable.")
    def pop(self, *args, **kwargs):
        raise TypeError("ReadOnlyList does not support pop: ContinuumEvidenceRecord collections are immutable.")
    def clear(self):
        raise TypeError("ReadOnlyList does not support clear: ContinuumEvidenceRecord collections are immutable.")
    def __setitem__(self, key, value):
        raise TypeError("ReadOnlyList does not support item assignment: ContinuumEvidenceRecord collections are immutable.")
    def __delitem__(self, key):
        raise TypeError("ReadOnlyList does not support item deletion: ContinuumEvidenceRecord collections are immutable.")
    def __deepcopy__(self, memo):
        return list(self)


class ReadOnlyDict(dict):
    """Immutable mapping wrapper for contract metadata and color indices."""
    def __setitem__(self, key, value):
        raise TypeError("ReadOnlyDict does not support item assignment: ContinuumEvidenceRecord metadata is immutable.")
    def __delitem__(self, key):
        raise TypeError("ReadOnlyDict does not support item deletion: ContinuumEvidenceRecord metadata is immutable.")
    def pop(self, *args, **kwargs):
        raise TypeError("ReadOnlyDict does not support pop: ContinuumEvidenceRecord metadata is immutable.")
    def update(self, *args, **kwargs):
        raise TypeError("ReadOnlyDict does not support update: ContinuumEvidenceRecord metadata is immutable.")
    def clear(self):
        raise TypeError("ReadOnlyDict does not support clear: ContinuumEvidenceRecord metadata is immutable.")
    def __deepcopy__(self, memo):
        return {k: copy.deepcopy(v, memo) for k, v in self.items()}


def _deep_freeze_payload(val: Any) -> Any:
    """Recursively freezes dictionaries and lists into ReadOnlyDict and ReadOnlyList."""
    if isinstance(val, dict):
        return ReadOnlyDict({k: _deep_freeze_payload(v) for k, v in val.items()})
    elif isinstance(val, (list, tuple)):
        return ReadOnlyList([_deep_freeze_payload(v) for v in val])
    return val


# ==============================================================================
# Task 4.10: Centralized Provenance Resolution Policy
# ==============================================================================
def normalize_pointing_id(pointing_id: Any) -> Optional[str]:
    """
    Normalizes a pointing identifier to canonical format.
    Returns None if missing, empty, or malformed.
    Resolves legacy alias '8' to canonical 'P0008' only if unambiguous.
    """
    if pointing_id is None:
        return None
    if isinstance(pointing_id, (int, float)):
        # Malformed non-string pointing ID
        return None
    if not isinstance(pointing_id, str):
        return None
    s = pointing_id.strip()
    if not s:
        return None
    if s == "P0008":
        return "P0008"
    if s == "8":
        return "P0008"
    if s.upper() in ["P0002", "P2", "2"]:
        return "P0002"
    if s.upper() in ["P0009", "P9", "9"]:
        return "P0009"
    if s.upper() in ["P0010", "P10", "10"]:
        return "P0010"
    return s.upper()


def is_trusted_calibration_provenance(
    pointing_id: Any,
    metadata: Optional[Dict[str, Any]] = None,
    secondary_pointing: Optional[Any] = None
) -> bool:
    """
    Centralized Authoritative Provenance Resolution Policy (Task 4.10).
    Enforces strict calibration allowlist: ONLY canonical P0008 with trusted,
    non-conflicting provenance is eligible for calibration-grade excess promotion.

    Returns True ONLY IF:
    1. pointing_id resolves strictly to CANONICAL_CALIBRATION_POINTING ('P0008')
    2. secondary_pointing (e.g. from photometric record) matches P0008 if present
    3. metadata does not contain conflicting cohort/pointing values (e.g. cohort='P0002')
    4. caller-supplied metadata flags (e.g. cohort='calibration') cannot grant eligibility
       unless pointing_id itself is canonical P0008
    5. untrusted provenance or legacy aliases marked untrusted are rejected fail-closed.
    """
    norm_pt = normalize_pointing_id(pointing_id)
    if norm_pt != CANONICAL_CALIBRATION_POINTING:
        return False

    # Check secondary pointing if provided (e.g. from photometric_record.cohort_pointing)
    if secondary_pointing is not None:
        norm_sec = normalize_pointing_id(secondary_pointing)
        if norm_sec != CANONICAL_CALIBRATION_POINTING:
            return False

    # Check metadata for conflicts or untrusted markers
    if metadata:
        # Check explicit untrusted markers
        if metadata.get("untrusted") is True or metadata.get("trusted_provenance") is False:
            return False

        # Check for conflicting cohort or pointing identities in metadata
        conflict_keys = ["cohort", "pointing", "pointing_id", "raw_pointing", "cohort_pointing"]
        for k in conflict_keys:
            val = metadata.get(k)
            if val is not None:
                if isinstance(val, str):
                    norm_val = normalize_pointing_id(val)
                    if norm_val is not None and norm_val != CANONICAL_CALIBRATION_POINTING:
                        return False
                    if val.strip().lower() in ["blind", "blind_evaluation", "eval", "unverified"]:
                        return False
                elif isinstance(val, (int, float)):
                    if str(val) != "8":
                        return False

        role_val = metadata.get("role") or metadata.get("cohort_role")
        if role_val and isinstance(role_val, str):
            if role_val.strip().lower() in ["blind", "blind_evaluation", "unverified", "test"]:
                return False

    return True


@dataclass(frozen=True)
class ContinuumEvidenceRecord:
    """
    Standardized continuum / color excess evidence data contract.
    Contract Identity: CONTINUUM_SIDECAR_EVIDENCE_V1
    
    Preserves 100% backward compatibility with Phase 3 Task 1.3B while providing
    full empirical photometric evidence fields for Phase 4 Task 4.7 FUSION-X integration.
    Deeply immutable under Task 4.10 governance.
    """
    # Core Contract Fields (Phase 3 Task 1.3B)
    contract_version: str
    source_id: str
    pointing_id: str
    color_excess_detected: bool = False
    continuum_anomaly_score: Optional[float] = None
    color_indices: Dict[str, float] = field(default_factory=dict)  # e.g., {"W1_W2_color": -0.096}
    power_law_spectral_index: Optional[float] = None
    excess_significance_sigma: Optional[float] = None
    quality_status: str = "PENDING_VALIDATION"
    provenance_reference: str = "SPHEREx_Continuum_Sidecar_Uncertified"

    # Empirical Evidence Extensions (Phase 4 Task 4.7)
    evidence_state: Optional[str] = None
    primary_band: Optional[str] = None
    observed_flux_mJy: Optional[float] = None
    predicted_flux_mJy: Optional[float] = None
    residual_flux_mJy: Optional[float] = None
    total_uncertainty_mJy: Optional[float] = None
    flux_unit: str = "mJy"
    is_upper_limit: Optional[bool] = None
    counterpart_ambiguity: bool = False
    validation_timestamp: Optional[str] = None
    pipeline_build: str = "l2b-v27-2026-222"
    limitation_codes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Defensively freeze collections into immutable wrappers (Task 4.10 FIND-4.9-02)
        raw_lim = list(self.limitation_codes) if self.limitation_codes is not None else []
        object.__setattr__(self, "limitation_codes", ReadOnlyList(raw_lim))

        raw_ci = dict(self.color_indices) if self.color_indices is not None else {}
        object.__setattr__(self, "color_indices", ReadOnlyDict(raw_ci))

        raw_meta = dict(self.metadata) if self.metadata is not None else {}
        object.__setattr__(self, "metadata", _deep_freeze_payload(raw_meta))

        self.validate()

    def validate(self) -> None:
        """Enforces schema compliance, fail-closed validation, and strict calibration allowlist."""
        if self.contract_version != SIDECAR_CONTRACT_VERSION:
            raise ValueError(
                f"Invalid contract_version: '{self.contract_version}'. Expected: '{SIDECAR_CONTRACT_VERSION}'"
            )

        if not self.source_id or not isinstance(self.source_id, str):
            raise ValueError(f"Invalid source_id: must be non-empty string, got {self.source_id}")

        if not self.pointing_id or not isinstance(self.pointing_id, str):
            raise ValueError(f"Invalid pointing_id: must be non-empty string, got {self.pointing_id}")

        # Sync evidence_state and quality_status
        if self.evidence_state and self.evidence_state in ALLOWED_EVIDENCE_STATES:
            if self.quality_status == "PENDING_VALIDATION":
                object.__setattr__(self, "quality_status", self.evidence_state)

        if self.quality_status not in ALLOWED_EVIDENCE_STATES:
            raise ValueError(
                f"Unknown quality_status '{self.quality_status}'. Allowed: {ALLOWED_EVIDENCE_STATES}"
            )

        if self.excess_significance_sigma is not None:
            if math.isnan(self.excess_significance_sigma) or math.isinf(self.excess_significance_sigma):
                raise ValueError("excess_significance_sigma must be a finite float or None.")

        if self.total_uncertainty_mJy is not None:
            if math.isnan(self.total_uncertainty_mJy) or self.total_uncertainty_mJy < 0:
                raise ValueError("total_uncertainty_mJy must be non-negative or None.")

        # Fail closed on impossible state promotion
        if self.quality_status in ["QUALITY_FLAGGED", "INSUFFICIENT_PHOTOMETRY", "AMBIGUOUS_COUNTERPART", "UNVERIFIABLE"]:
            if self.color_excess_detected is True:
                raise ValueError(
                    f"Governance violation: Status '{self.quality_status}' must never be promoted to color_excess_detected=True."
                )

        if self.color_excess_detected is True:
            # Empirical payloads require explicit positive uncertainty and significance
            if self.observed_flux_mJy is not None:
                if self.total_uncertainty_mJy is None or self.total_uncertainty_mJy <= 0:
                    raise ValueError(
                        f"Governance violation: Empirical color_excess_detected=True requires valid positive total_uncertainty_mJy, got {self.total_uncertainty_mJy}."
                    )
            if self.is_upper_limit is True:
                raise ValueError(
                    "Governance violation: is_upper_limit=True cannot be promoted to color_excess_detected=True."
                )
            if self.counterpart_ambiguity is True:
                raise ValueError(
                    "Governance violation: counterpart_ambiguity=True cannot be promoted to color_excess_detected=True."
                )

        # Task 4.10 Explicit Calibration Allowlist Governance Enforcement (Remediates FIND-4.9-01)
        # ONLY canonical P0008 with trusted provenance can authorize calibration-grade excess.
        is_cal_eligible = is_trusted_calibration_provenance(self.pointing_id, self.metadata)
        has_blind_limitation = "BLIND_COHORT_UNVERIFIED_BASELINE" in self.limitation_codes

        if has_blind_limitation or (not is_cal_eligible and self.evidence_state is not None):
            # 1. Non-calibration pointing must include limitation code BLIND_COHORT_UNVERIFIED_BASELINE
            if not has_blind_limitation:
                raise ValueError(
                    f"Governance violation: Non-calibration pointing '{self.pointing_id}' must include limitation code 'BLIND_COHORT_UNVERIFIED_BASELINE'."
                )
            # 2. Cannot claim color_excess_detected=True without verified calibration baseline
            if self.color_excess_detected is True:
                raise ValueError(
                    f"Governance violation: Non-calibration pointing '{self.pointing_id}' cannot have color_excess_detected=True with unverified baseline."
                )
            # 3. Cannot claim verified photospheric consistency
            if self.evidence_state == "SUPPORTED_PHOTOSPHERIC_CONSISTENCY" or self.quality_status == "SUPPORTED_PHOTOSPHERIC_CONSISTENCY":
                raise ValueError(
                    f"Governance violation: Non-calibration pointing '{self.pointing_id}' cannot claim SUPPORTED_PHOTOSPHERIC_CONSISTENCY with unverified baseline."
                )
            # 4. Cannot claim verified possible infrared excess
            if self.evidence_state == "POSSIBLE_INFRARED_EXCESS" or self.quality_status == "POSSIBLE_INFRARED_EXCESS":
                raise ValueError(
                    f"Governance violation: Non-calibration pointing '{self.pointing_id}' cannot claim POSSIBLE_INFRARED_EXCESS with unverified baseline."
                )

    def to_dict(self) -> Dict[str, Any]:
        """Converts record to compliant, defensively copied dictionary."""
        d = asdict(self)
        d["limitation_codes"] = list(self.limitation_codes)
        d["color_indices"] = dict(self.color_indices)
        d["metadata"] = copy.deepcopy(dict(self.metadata))
        return d


class ContinuumSidecarInterface(ABC):
    """
    Abstract interface for broadband color / continuum evidence sidecar.
    FUSION-X or multimodal pipelines pair SPECTRA line evidence with continuum evidence.
    """

    @abstractmethod
    def evaluate_continuum(
        self,
        source_id: str,
        pointing_id: str,
        wavelengths: List[float],
        fluxes: List[float],
        uncertainties: List[float],
        valid_mask: List[bool],
        photometric_record: Optional[Any] = None
    ) -> ContinuumEvidenceRecord:
        """
        Evaluates broadband continuum slopes, infrared excess, and stellar photospheric consistency.
        Must return a validated ContinuumEvidenceRecord.
        """
        pass

    @abstractmethod
    def validate_sidecar_assets(self) -> bool:
        """Verifies integrity and certification status of continuum calibration models."""
        pass


__all__ = [
    "SIDECAR_CONTRACT_VERSION",
    "ALLOWED_EVIDENCE_STATES",
    "BASE_SIDECAR_LIMITATION_CODES",
    "CANONICAL_CALIBRATION_POINTING",
    "AUTHORIZED_CALIBRATION_POINTINGS",
    "normalize_pointing_id",
    "is_trusted_calibration_provenance",
    "ReadOnlyList",
    "ReadOnlyDict",
    "ContinuumEvidenceRecord",
    "ContinuumSidecarInterface",
]
