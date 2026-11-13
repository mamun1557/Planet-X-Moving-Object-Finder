"""
SPECTRA-X Common Candidate Output Contract
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Standardized data contract and schema enforcement across all five discovery modules:
- ASTROVISION (Spatial Morphology)
- SPECTRA (102-Band SED Outlier)
- CHRONOS-X (Temporal Differencing)
- MOTION-X (Astrometric Kinematics)
- FUSION-X (Multimodal Candidate Ranking)

Scientific Rules:
1. Explicit missing-value handling (None / null rather than magical fill numbers).
2. Different module scores are NOT treated as directly comparable probabilities.
3. Every record preserves celestial coordinates, provenance, quality flags, and evidence summary.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List, Union
import json
import re


ALLOWED_MODULES = {"ASTROVISION", "SPECTRA", "CHRONOS-X", "MOTION-X", "FUSION-X"}

ALLOWED_SCORE_TYPES = {
    "CHI2_RECON_RESIDUAL",          # Masked Chi-squared reconstruction loss (SPECTRA)
    "PEAK_SPATIAL_DEVIATION",       # Peak spatial normalized residual sigma (ASTROVISION)
    "TEMPORAL_SIGNIFICANCE_SIGMA",  # Reprojected difference map peak significance (CHRONOS-X)
    "ASTROMETRIC_OFFSET_ARCSEC",    # Proper motion or positional offset (MOTION-X)
    "HEURISTIC_PRIORITY_SCORE",     # Multimodal ranking priority [0.0 - 1.0] (FUSION-X)
    "SYNTHETIC_BENCHMARK_SCORE"     # Injection test benchmark score
}

ALLOWED_VALIDITY_STATUSES = {
    "VALID",             # Clean observation, passed all QC checks
    "WARNING",           # Passed with caveats (e.g. partial aperture, edge proximity)
    "REJECTED",          # Failed QC (e.g. fatal flag, NaN, bad neighborhood)
    "INSUFFICIENT_DATA"  # Missing observations required to evaluate modality
}

ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES = {
    "TRUE",          # Verified independent epochs meeting operational baseline and compatibility checks
    "FALSE",         # Proven ineligible (intra-visit dither, incompatible detector/band/calibration)
    "UNVERIFIABLE"   # Insufficient metadata/evidence to confirm temporal eligibility
}


@dataclass
class CandidateRecord:
    candidate_id: str
    ra: float
    dec: float
    observation_id: str
    observation_time: str
    module_name: str
    anomaly_score: float
    score_type: str
    validity_status: str
    evidence_summary: str
    input_provenance: str
    uncertainty: Optional[float] = None
    quality_flags: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    temporal_eligibility: Optional[str] = None

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces schema compliance and scientific integrity rules."""
        if not self.candidate_id or not isinstance(self.candidate_id, str):
            raise ValueError(f"Invalid candidate_id: {self.candidate_id}")
            
        if not (-360.0 <= self.ra <= 360.0):
            raise ValueError(f"RA out of valid range [-360, 360]: {self.ra}")
            
        if not (-90.0 <= self.dec <= 90.0):
            raise ValueError(f"Dec out of valid range [-90, 90]: {self.dec}")
            
        if self.module_name not in ALLOWED_MODULES:
            raise ValueError(f"Unknown module_name: '{self.module_name}'. Allowed: {ALLOWED_MODULES}")
            
        if self.score_type not in ALLOWED_SCORE_TYPES:
            raise ValueError(f"Unknown score_type: '{self.score_type}'. Allowed: {ALLOWED_SCORE_TYPES}")
            
        if self.validity_status not in ALLOWED_VALIDITY_STATUSES:
            raise ValueError(f"Unknown validity_status: '{self.validity_status}'. Allowed: {ALLOWED_VALIDITY_STATUSES}")
            
        if self.temporal_eligibility is not None and self.temporal_eligibility not in ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES:
            raise ValueError(f"Unknown temporal_eligibility: '{self.temporal_eligibility}'. Allowed: {ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES}")
            
        if not isinstance(self.anomaly_score, (int, float)) or (self.anomaly_score is not None and (self.anomaly_score != self.anomaly_score)):
            raise ValueError(f"Anomaly score must be a finite float, got: {self.anomaly_score}")
            
        if self.uncertainty is not None and (self.uncertainty < 0 or (self.uncertainty != self.uncertainty)):
            raise ValueError(f"Uncertainty must be non-negative or None, got: {self.uncertainty}")

    def to_dict(self) -> Dict[str, Any]:
        """Converts record to compliant dictionary."""
        d = asdict(self)
        # Ensure floats are standard python floats
        d["ra"] = float(d["ra"])
        d["dec"] = float(d["dec"])
        d["anomaly_score"] = float(d["anomaly_score"])
        if d["uncertainty"] is not None:
            d["uncertainty"] = float(d["uncertainty"])
        if d.get("temporal_eligibility") is not None:
            d["temporal_eligibility"] = str(d["temporal_eligibility"])
        return d

    def to_json(self) -> str:
        """Serializes to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateRecord":
        """Constructs and validates record from dictionary."""
        return cls(
            candidate_id=str(data["candidate_id"]),
            ra=float(data["ra"]),
            dec=float(data["dec"]),
            observation_id=str(data["observation_id"]),
            observation_time=str(data.get("observation_time", "UNKNOWN")),
            module_name=str(data["module_name"]),
            anomaly_score=float(data["anomaly_score"]),
            score_type=str(data["score_type"]),
            validity_status=str(data["validity_status"]),
            evidence_summary=str(data["evidence_summary"]),
            input_provenance=str(data["input_provenance"]),
            uncertainty=float(data["uncertainty"]) if data.get("uncertainty") is not None else None,
            quality_flags=int(data["quality_flags"]) if data.get("quality_flags") is not None else None,
            metadata=data.get("metadata", {}),
            temporal_eligibility=data.get("temporal_eligibility")
        )
