"""
SPECTRA-X / F1 — Phase 3, Task 1.3B
Authoritative Versioned SPECTRA-to-FUSION-X Evidence Contract

Package:           spectra_engine
Contract Identity: SPECTRA_FUSION_EVIDENCE_V1
Pipeline Build:    l2b-v27-2026-222

Mathematical Normalization Semantics & Documentation:
1. Primary Ingestion Metric: Stratum-Normalized Percentile Rank
   P(S) = (1 / N_calib) * sum_{i=1}^{N_calib} 1(c_i <= S)
   Computed via deterministic empirical cumulative distribution function with side='right'
   tie handling over the verified frozen Pointing P0008 calibration distribution.

2. Secondary Diagnostic Metric: IQR-Scaled Stratum Deviation
   Z = (S - Median_stratum) / IQR_stratum
   NOTE ON NOMENCLATURE:
   This quantity is an unstandardized IQR-scaled deviation (or IQR-normalized distance).
   It is NOT the conventional MAD-based robust Z-score:
       Z_MAD = (S - Median) / (1.4826 * MAD)
   nor is it the Gaussian-standardized IQR deviation:
       Z_standardized = (S - Median) / (IQR / 1.34898)
   The field name 'optional_stratum_z_score' is preserved strictly for backward
   compatibility with downstream consumers. The primary, scientifically verified
   evidence metric remains 'stratum_normalized_percentile'.

Scientific Rules & Governance:
- Strict read-only integration interface; zero model retraining or threshold modification.
- Cross-stratum raw score pooling is strictly prohibited.
- Channel coverage gate enforces eligibility (<5 valid channels = UNINFORMATIVE).
- Provisional threshold exceedance represents empirical reference exceedance, NOT certified FPR.
- Mandatory limitation codes are attached to every record.
- Autonomous unassisted discovery is strictly prohibited; cross-modal corroboration required.
"""

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Optional, Dict, Any, List
import json
import numpy as np


CONTRACT_VERSION = "SPECTRA_FUSION_EVIDENCE_V1"
SPECTRA_FUSION_EVIDENCE_V1 = "SPECTRA_FUSION_EVIDENCE_V1"  # Constant alias for direct import
MODEL_ID = "SPECTRA_Masked_AE_v2"
MODEL_VERSION = "v2.1"
EXPECTED_CHECKPOINT_SHA256 = "6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938"
EXPECTED_THRESHOLDS_SHA256 = "d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848"
EXPECTED_CALIB_SCORES_SHA256 = "7ac34d415f8132f7f164ab20c1b25fe03461bc709eb674031e838b2208e8c1a3"
PIPELINE_BUILD = "l2b-v27-2026-222"

VALID_STRATA = {"D1,D4", "D2,D5", "D3,D6", "D1+D4", "D2+D5", "D3+D6"}

CANONICAL_STRATA_MAP = {
    "D1,D4": "D1,D4",
    "D1+D4": "D1,D4",
    "D2,D5": "D2,D5",
    "D2+D5": "D2,D5",
    "D3,D6": "D3,D6",
    "D3+D6": "D3,D6"
}

BASE_LIMITATION_CODES = [
    "CONTINUUM_SENSITIVITY_LIMITED",
    "ABSORPTION_SENSITIVITY_LIMITED",
    "PROVISIONAL_NULL_REFERENCE",
    "SKY_WIDE_GENERALIZATION_UNVERIFIED"
]

STRATUM_LIMITATION_CODES = {
    "D3,D6": ["D3_D6_REDUCED_SENSITIVITY"]
}


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    UNINFORMATIVE = "UNINFORMATIVE"
    NO_OBSERVATIONAL_COVERAGE = "NO_OBSERVATIONAL_COVERAGE"
    QUALITY_REJECTED = "QUALITY_REJECTED"
    STRATUM_UNRESOLVED = "STRATUM_UNRESOLVED"
    NORMALIZATION_UNAVAILABLE = "NORMALIZATION_UNAVAILABLE"


class ThresholdExceedanceLevel(str, Enum):
    NONE = "NONE"
    EXCEEDS_T05 = "EXCEEDS_T05"
    EXCEEDS_T01 = "EXCEEDS_T01"
    NOT_EVALUATED = "NOT_EVALUATED"


class EvidenceStrength(str, Enum):
    NONE = "NONE"
    MARGINAL = "MARGINAL"
    STRONG = "STRONG"
    EXTREME = "EXTREME"
    UNINFORMATIVE = "UNINFORMATIVE"


class CrossModalStatus(str, Enum):
    UNCONFIRMED_UNIMODAL = "UNCONFIRMED_UNIMODAL"
    CORROBORATED = "CORROBORATED"
    CONTRADICTED = "CONTRADICTED"
    NO_CROSS_MODAL_DATA = "NO_CROSS_MODAL_DATA"


@dataclass
class SpectraFusionEvidenceRecord:
    """
    Versioned, typed SPECTRA-to-FUSION-X evidence record.
    Contract Identity: SPECTRA_FUSION_EVIDENCE_V1
    
    Fields:
      optional_stratum_z_score: Legacy-named IQR-scaled deviation: (S - Median) / IQR.
                                Not a MAD-based robust Z-score.
      stratum_normalized_percentile: Primary empirical percentile rank in [0.0, 1.0].
    """

    # A. Identity and Provenance
    contract_version: str
    model_id: str
    model_version: str
    checkpoint_sha256: str
    threshold_artifact_sha256: str
    pipeline_build: str
    inference_timestamp: str
    source_id: str
    pointing_id: str
    detector_stratum: str
    provenance_reference: str

    # B. Spectral Evidence
    raw_anomaly_score: Optional[float]
    stratum_normalized_percentile: Optional[float]
    optional_stratum_z_score: Optional[float]
    threshold_05: Optional[float]
    threshold_01: Optional[float]
    threshold_exceedance_level: str
    valid_channel_count: int
    channel_coverage_fraction: float
    spectral_feature_scope: str

    # C. Scientific Quality
    uncertainty_available: bool
    data_quality_flags: Optional[int]
    eligibility_status: str
    limitation_codes: List[str]
    calibration_reference_version: str

    # D. Interpretation & Governance
    anomaly_detected: bool
    evidence_strength: str
    interpretation: str
    human_review_required: bool

    # E. Cross-Modal Corroboration Metadata (nullable / explicitly unverified)
    cross_modal_corroboration_status: str = CrossModalStatus.NO_CROSS_MODAL_DATA.value
    astrovision_corroboration: Optional[Dict[str, Any]] = None
    chronos_corroboration: Optional[Dict[str, Any]] = None
    continuum_sidecar_corroboration: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces schema compliance and scientific integrity rules."""
        if self.contract_version != CONTRACT_VERSION:
            raise ValueError(f"Invalid contract_version: '{self.contract_version}'. Expected: '{CONTRACT_VERSION}'")

        if self.model_id != MODEL_ID:
            raise ValueError(f"Invalid model_id: '{self.model_id}'. Expected: '{MODEL_ID}'")

        if not self.source_id or not isinstance(self.source_id, str):
            raise ValueError(f"Invalid source_id: {self.source_id}")

        if not self.pointing_id or not isinstance(self.pointing_id, str):
            raise ValueError(f"Invalid pointing_id: {self.pointing_id}")

        if self.eligibility_status not in [e.value for e in EligibilityStatus]:
            raise ValueError(f"Unknown eligibility_status: '{self.eligibility_status}'")

        if self.threshold_exceedance_level not in [e.value for e in ThresholdExceedanceLevel]:
            raise ValueError(f"Unknown threshold_exceedance_level: '{self.threshold_exceedance_level}'")

        if self.evidence_strength not in [e.value for e in EvidenceStrength]:
            raise ValueError(f"Unknown evidence_strength: '{self.evidence_strength}'")

        if self.cross_modal_corroboration_status not in [e.value for e in CrossModalStatus]:
            raise ValueError(f"Unknown cross_modal_corroboration_status: '{self.cross_modal_corroboration_status}'")

        if self.valid_channel_count < 0 or self.valid_channel_count > 102:
            raise ValueError(f"valid_channel_count must be in [0, 102], got {self.valid_channel_count}")

        if not (0.0 <= self.channel_coverage_fraction <= 1.0):
            raise ValueError(f"channel_coverage_fraction must be in [0.0, 1.0], got {self.channel_coverage_fraction}")

        # Quality and eligibility enforcement
        if self.eligibility_status == EligibilityStatus.ELIGIBLE.value:
            if self.valid_channel_count < 5:
                raise ValueError(f"ELIGIBLE status requires at least 5 valid channels, got {self.valid_channel_count}")
            if self.raw_anomaly_score is None or np.isnan(self.raw_anomaly_score) or self.raw_anomaly_score < 0:
                raise ValueError("ELIGIBLE record must have a valid non-negative raw_anomaly_score")
            if self.stratum_normalized_percentile is None:
                raise ValueError("ELIGIBLE record must have stratum_normalized_percentile")
            if not (0.0 <= self.stratum_normalized_percentile <= 1.0):
                raise ValueError(f"stratum_normalized_percentile must be in [0.0, 1.0], got {self.stratum_normalized_percentile}")
            if self.threshold_05 is None or self.threshold_01 is None:
                raise ValueError("ELIGIBLE record must specify frozen threshold_05 and threshold_01")
        else:
            # When ineligible, raw score or percentiles must NOT be treated as active anomaly evidence
            if self.anomaly_detected:
                raise ValueError(f"anomaly_detected cannot be True when eligibility_status is '{self.eligibility_status}'")

        # Check limitation codes presence
        for base_code in BASE_LIMITATION_CODES:
            if base_code not in self.limitation_codes:
                raise ValueError(f"Mandatory limitation code '{base_code}' missing from record limitation_codes")

        # Check D3+D6 limitation
        canon_stratum = CANONICAL_STRATA_MAP.get(self.detector_stratum)
        if canon_stratum == "D3,D6":
            if "D3_D6_REDUCED_SENSITIVITY" not in self.limitation_codes:
                raise ValueError("Stratum D3,D6 requires 'D3_D6_REDUCED_SENSITIVITY' in limitation_codes")

    def to_dict(self) -> Dict[str, Any]:
        """Converts record to compliant JSON-serializable dictionary."""
        d = asdict(self)
        if d["raw_anomaly_score"] is not None:
            d["raw_anomaly_score"] = float(d["raw_anomaly_score"])
        if d["stratum_normalized_percentile"] is not None:
            d["stratum_normalized_percentile"] = float(d["stratum_normalized_percentile"])
        if d["optional_stratum_z_score"] is not None:
            d["optional_stratum_z_score"] = float(d["optional_stratum_z_score"])
        if d["threshold_05"] is not None:
            d["threshold_05"] = float(d["threshold_05"])
        if d["threshold_01"] is not None:
            d["threshold_01"] = float(d["threshold_01"])
        d["channel_coverage_fraction"] = float(d["channel_coverage_fraction"])
        return d

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serializes record to standard JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpectraFusionEvidenceRecord":
        """Instantiates and validates a record from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "SpectraFusionEvidenceRecord":
        """Instantiates and validates a record from JSON string."""
        return cls.from_dict(json.loads(json_str))

