"""
SPECTRA-X / F1 — Phase 3, Task 1.3K
CHRONOS-X Temporal Eligibility & Evidence Tier Engine

Core Principles & Rules:
1. Temporal Eligibility is an orthogonal axis to Evidence Completeness (E0-E4).
2. Exactly three pair-level states exist: TRUE, FALSE, UNVERIFIABLE.
3. Operational minimum baseline is a versioned project safety rule (default: 1.0 day).
4. Intra-visit dithers (2.15-6.47 min) achieve full E4 completeness but are strictly FALSE
   for secular temporal variability.
5. Incompatible detectors (e.g. Det 1 vs Det 2) or concurrent focal-plane observations are FALSE.
6. Missing required metadata produces structured UNVERIFIABLE records with provenance.
7. Dataset-level availability reports TEMPORAL_DATA_AVAILABLE only if genuine TRUE pairs exist,
   otherwise reporting TEMPORAL_DATA_UNAVAILABLE.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import json
import numpy as np


# Versioned Baseline Policy
BASELINE_POLICY_VERSION = "v1.0-2026-F1"
DEFAULT_MIN_BASELINE_DAYS = 1.0  # Project safety rule: 1.0 day minimum for secular variability

ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES = {"TRUE", "FALSE", "UNVERIFIABLE"}
ALLOWED_DATASET_AVAILABILITY_STATUSES = {"TEMPORAL_DATA_AVAILABLE", "TEMPORAL_DATA_UNAVAILABLE"}
ALLOWED_EVIDENCE_TIERS = {"E0", "E1", "E2", "E3", "E4", "NONE"}

# SPHEREx Detector to nominal wavelength range (microns)
SPHEREx_DETECTOR_WAVELENGTHS = {
    1: (0.75, 1.11),
    2: (1.11, 1.64),
    3: (1.64, 2.42),
    4: (2.42, 3.82),
    5: (3.82, 4.42),
    6: (4.42, 5.00),
}


@dataclass
class TemporalEligibilityResult:
    """Standardized result for pair-level temporal eligibility and evidence completeness."""
    status: str                         # "TRUE", "FALSE", "UNVERIFIABLE"
    evidence_tier: str                  # "E0", "E1", "E2", "E3", "E4", "NONE"
    is_dither: bool                     # True if intra-visit dither sequence
    dt_days: Optional[float]            # Elapsed time separation in days
    reasons: List[str]                  # Explanations for eligibility or exclusion
    missing_evidence: List[str]         # Specific missing metadata fields if UNVERIFIABLE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.status not in ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES:
            raise ValueError(f"Invalid status: '{self.status}'. Allowed: {ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES}")
        if self.evidence_tier not in ALLOWED_EVIDENCE_TIERS:
            raise ValueError(f"Invalid evidence_tier: '{self.evidence_tier}'. Allowed: {ALLOWED_EVIDENCE_TIERS}")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["dt_days"] is not None:
            d["dt_days"] = float(d["dt_days"])
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def evaluate_pair_temporal_eligibility(
    obs1: Dict[str, Any],
    obs2: Dict[str, Any],
    min_baseline_days: float = DEFAULT_MIN_BASELINE_DAYS,
    max_sep_arcsec: float = 12600.0,  # 3.5 deg FOV
    policy_version: str = BASELINE_POLICY_VERSION
) -> TemporalEligibilityResult:
    """
    Evaluates an observation pair against all 10 scientific eligibility criteria
    and assigns an orthogonal Evidence Tier (E0-E4) and Temporal Eligibility (TRUE/FALSE/UNVERIFIABLE).
    """
    reasons: List[str] = []
    missing_evidence: List[str] = []

    # ---------------------------------------------------------
    # 1. Metadata Normalization & Extraction
    # ---------------------------------------------------------
    f1 = obs1.get("filename") or obs1.get("file_1") or obs1.get("file") or "UNKNOWN_1"
    f2 = obs2.get("filename") or obs2.get("file_2") or obs2.get("file") or "UNKNOWN_2"

    obsid1 = str(obs1.get("obsid") or obs1.get("plan_id") or obs1.get("OBSID") or "")
    obsid2 = str(obs2.get("obsid") or obs2.get("plan_id") or obs2.get("OBSID") or "")

    mjd1 = obs1.get("mjd_obs") or obs1.get("mjd_1") or obs1.get("MJD-OBS")
    mjd2 = obs2.get("mjd_obs") or obs2.get("mjd_2") or obs2.get("MJD-OBS")

    ra1 = obs1.get("ra_deg") or obs1.get("ra") or obs1.get("CRVAL1")
    dec1 = obs1.get("dec_deg") or obs1.get("dec") or obs1.get("CRVAL2")
    ra2 = obs2.get("ra_deg") or obs2.get("ra") or obs2.get("CRVAL1")
    dec2 = obs2.get("dec_deg") or obs2.get("dec") or obs2.get("CRVAL2")

    wcs1_avail = bool(obs1.get("wcs_available", True))
    wcs2_avail = bool(obs2.get("wcs_available", True))

    det1 = obs1.get("detector") or obs1.get("DETECTOR")
    det2 = obs2.get("detector") or obs2.get("DETECTOR")

    chan1 = obs1.get("channel") or obs1.get("CHANNEL")
    chan2 = obs2.get("channel") or obs2.get("CHANNEL")

    rel1 = str(obs1.get("release") or obs1.get("release_1") or "UNKNOWN").upper()
    rel2 = str(obs2.get("release") or obs2.get("release_2") or "UNKNOWN").upper()

    cal1 = obs1.get("cal_version") or obs1.get("VERSION") or "UNKNOWN"
    cal2 = obs2.get("cal_version") or obs2.get("VERSION") or "UNKNOWN"

    var1_avail = bool(obs1.get("variance_available", True))
    var2_avail = bool(obs2.get("variance_available", True))

    flags1_avail = bool(obs1.get("flags_available", True))
    flags2_avail = bool(obs2.get("flags_available", True))

    dither1 = obs1.get("dither") or obs1.get("DITHER")
    dither2 = obs2.get("dither") or obs2.get("DITHER")

    # ---------------------------------------------------------
    # 2. Separation and dt Calculations
    # ---------------------------------------------------------
    dt_days: Optional[float] = None
    if mjd1 is not None and mjd2 is not None:
        try:
            m1 = float(mjd1)
            m2 = float(mjd2)
            if not np.isnan(m1) and not np.isnan(m2):
                dt_days = abs(m2 - m1)
        except (ValueError, TypeError):
            dt_days = None

    sep_arcsec: Optional[float] = obs1.get("sep_arcsec") or obs2.get("sep_arcsec")
    if sep_arcsec is None and ra1 is not None and dec1 is not None and ra2 is not None and dec2 is not None:
        try:
            r1, d1_val, r2, d2_val = float(ra1), float(dec1), float(ra2), float(dec2)
            dra = (r2 - r1) * np.cos(np.deg2rad((d1_val + d2_val) / 2.0)) * 3600.0
            ddec = (d2_val - d1_val) * 3600.0
            sep_arcsec = float(np.sqrt(dra**2 + ddec**2))
        except Exception:
            sep_arcsec = None

    # ---------------------------------------------------------
    # 3. Evidence Tier Evaluation (E0 to E4) - Independent of dt
    # ---------------------------------------------------------
    # E0: Archive / observation identity evidence
    has_e0 = bool((f1 and f1 != "UNKNOWN_1") or (obsid1 and obsid2))
    tier = "E0" if has_e0 else "NONE"

    # E1: Spatial / WCS overlap evidence
    has_e1 = False
    if has_e0 and wcs1_avail and wcs2_avail and sep_arcsec is not None and sep_arcsec <= max_sep_arcsec:
        has_e1 = True
        tier = "E1"

    # E2: Same-detector and spectral band compatibility evidence
    has_e2 = False
    if has_e1 and det1 is not None and det2 is not None and str(det1) == str(det2):
        # If channels are specified, they must match
        if chan1 is None or chan2 is None or str(chan1) == str(chan2):
            has_e2 = True
            tier = "E2"

    # E3: Observation metadata and temporal-pair evidence
    has_e3 = False
    if has_e2 and dt_days is not None:
        has_e3 = True
        tier = "E3"

    # E4: E3 + calibration, quality flags, and uncertainty compatibility
    has_e4 = False
    cal_compat = (rel1 == rel2) if (rel1 != "UNKNOWN" and rel2 != "UNKNOWN") else (cal1 == cal2)
    if has_e3 and var1_avail and var2_avail and flags1_avail and flags2_avail and cal_compat:
        has_e4 = True
        tier = "E4"

    # ---------------------------------------------------------
    # 4. Same-Visit Dither Detection
    # ---------------------------------------------------------
    is_dither = False
    # Intra-visit dithers occur within the same observation sequence (< 30 minutes)
    if dt_days is not None and dt_days < (30.0 / 1440.0):
        is_dither = True
    elif dt_days is not None and dt_days < min_baseline_days:
        # Also flag if pointing/visit matches and time is sub-baseline
        p1 = obsid1.split("_")[0] if "_" in obsid1 else obsid1
        p2 = obsid2.split("_")[0] if "_" in obsid2 else obsid2
        if p1 == p2 and p1 != "":
            is_dither = True
        elif dither1 is not None and dither2 is not None and str(dither1) != str(dither2):
            is_dither = True

    # ---------------------------------------------------------
    # 5. Temporal Eligibility Evaluation (TRUE / FALSE / UNVERIFIABLE)
    # ---------------------------------------------------------
    # Check for missing essential metadata first -> UNVERIFIABLE
    if dt_days is None:
        missing_evidence.append("MISSING_OBSERVATION_TIMESTAMPS")

    if not wcs1_avail or not wcs2_avail or sep_arcsec is None:
        missing_evidence.append("MISSING_WCS_OVERLAP_EVIDENCE")

    if det1 is None or det2 is None:
        missing_evidence.append("MISSING_DETECTOR_IDENTITY")

    if not var1_avail or not var2_avail:
        missing_evidence.append("MISSING_VARIANCE_UNCERTAINTY_METADATA")

    if not flags1_avail or not flags2_avail:
        missing_evidence.append("MISSING_QUALITY_FLAG_METADATA")

    # If missing required evidence to evaluate -> UNVERIFIABLE
    # Note: If timestamps, WCS, or detector identity are missing, we cannot verify eligibility.
    if "MISSING_OBSERVATION_TIMESTAMPS" in missing_evidence or "MISSING_WCS_OVERLAP_EVIDENCE" in missing_evidence or "MISSING_DETECTOR_IDENTITY" in missing_evidence:
        reasons.append("UNVERIFIABLE: Insufficient metadata to determine temporal eligibility.")
        return TemporalEligibilityResult(
            status="UNVERIFIABLE",
            evidence_tier=tier,
            is_dither=is_dither,
            dt_days=dt_days,
            reasons=reasons,
            missing_evidence=missing_evidence,
            metadata={
                "policy_version": policy_version,
                "min_baseline_days": min_baseline_days,
                "sep_arcsec": sep_arcsec,
                "detector_1": det1,
                "detector_2": det2,
                "file_1": f1,
                "file_2": f2
            }
        )

    # Next, evaluate decisive scientific exclusions -> FALSE
    # Check 1: Incompatible detectors
    if str(det1) != str(det2):
        reasons.append(f"INELIGIBLE: Incompatible detectors ({det1} vs {det2}) - observes different spectral bands.")
        return TemporalEligibilityResult(
            status="FALSE",
            evidence_tier=tier,
            is_dither=is_dither,
            dt_days=dt_days,
            reasons=reasons,
            missing_evidence=missing_evidence,
            metadata={"exclusion": "INCOMPATIBLE_DETECTORS", "det1": det1, "det2": det2}
        )

    # Check 2: Incompatible spectral bands
    if chan1 is not None and chan2 is not None and str(chan1) != str(chan2):
        reasons.append(f"INELIGIBLE: Incompatible spectral channels ({chan1} vs {chan2}).")
        return TemporalEligibilityResult(
            status="FALSE",
            evidence_tier=tier,
            is_dither=is_dither,
            dt_days=dt_days,
            reasons=reasons,
            missing_evidence=missing_evidence,
            metadata={"exclusion": "INCOMPATIBLE_CHANNELS", "chan1": chan1, "chan2": chan2}
        )

    # Check 3: Spatial separation outside FOV
    if sep_arcsec > max_sep_arcsec:
        reasons.append(f"INELIGIBLE: Spatial separation {sep_arcsec:.1f}\" exceeds detector FOV {max_sep_arcsec:.1f}\".")
        return TemporalEligibilityResult(
            status="FALSE",
            evidence_tier=tier,
            is_dither=is_dither,
            dt_days=dt_days,
            reasons=reasons,
            missing_evidence=missing_evidence,
            metadata={"exclusion": "INSUFFICIENT_SPATIAL_OVERLAP", "sep_arcsec": sep_arcsec}
        )

    # Check 4: Incompatible calibration / release (e.g. QR2 vs QR3 without cross-calibration)
    if rel1 != "UNKNOWN" and rel2 != "UNKNOWN" and rel1 != rel2:
        reasons.append(f"INELIGIBLE: Incompatible pipeline releases ({rel1} vs {rel2}) without unified photometric calibration.")
        return TemporalEligibilityResult(
            status="FALSE",
            evidence_tier=tier,
            is_dither=is_dither,
            dt_days=dt_days,
            reasons=reasons,
            missing_evidence=missing_evidence,
            metadata={"exclusion": "INCOMPATIBLE_RELEASES", "rel1": rel1, "rel2": rel2}
        )

    # Check 5: Same-visit dither or baseline below minimum threshold
    # Rule: Same-visit metadata overrides misleading timestamp separation
    if is_dither or dt_days < min_baseline_days:
        dt_mins = (dt_days * 1440.0) if dt_days is not None else 0.0
        reasons.append(
            f"INELIGIBLE: Temporal baseline {dt_days:.4f} days ({dt_mins:.2f} min) is below operational minimum "
            f"baseline of {min_baseline_days:.1f} days (Policy: {policy_version}). Same-visit dither sequence."
        )
        return TemporalEligibilityResult(
            status="FALSE",
            evidence_tier=tier,
            is_dither=True,
            dt_days=dt_days,
            reasons=reasons,
            missing_evidence=missing_evidence,
            metadata={
                "exclusion": "INTRA_VISIT_DITHER",
                "dt_days": dt_days,
                "dt_minutes": dt_mins,
                "min_baseline_days": min_baseline_days,
                "usable_for_registration": True,
                "usable_for_dipole_vetting": True
            }
        )

    # Check 6: Uncertainty and flag completeness for multi-epoch comparison
    if "MISSING_VARIANCE_UNCERTAINTY_METADATA" in missing_evidence or "MISSING_QUALITY_FLAG_METADATA" in missing_evidence:
        reasons.append("UNVERIFIABLE: Independent epochs verified, but variance or quality flag metadata is missing.")
        return TemporalEligibilityResult(
            status="UNVERIFIABLE",
            evidence_tier=tier,
            is_dither=False,
            dt_days=dt_days,
            reasons=reasons,
            missing_evidence=missing_evidence,
            metadata={"missing_fields": missing_evidence}
        )

    # All 10 requirements satisfied -> TRUE
    reasons.append(
        f"ELIGIBLE: Independent observation epochs verified (dt={dt_days:.2f} days >= {min_baseline_days:.1f} days). "
        f"Same detector ({det1}), compatible calibration ({rel1}), and full E4 quality/variance verified."
    )
    return TemporalEligibilityResult(
        status="TRUE",
        evidence_tier=tier,
        is_dither=False,
        dt_days=dt_days,
        reasons=reasons,
        missing_evidence=[],
        metadata={
            "policy_version": policy_version,
            "min_baseline_days": min_baseline_days,
            "dt_days": dt_days,
            "detector": det1,
            "release": rel1,
            "sep_arcsec": sep_arcsec
        }
    )


def determine_dataset_temporal_availability(
    pairs_or_results: List[Union[Dict[str, Any], TemporalEligibilityResult]],
    exclude_synthetic: bool = True
) -> str:
    """
    Exposes dataset/system-level availability status:
    - TEMPORAL_DATA_AVAILABLE if at least one genuine pair is TRUE.
    - TEMPORAL_DATA_UNAVAILABLE if no genuine multi-epoch pairs exist.
    Never infers availability from synthetic benchmarks or intra-visit dithers.
    """
    if not pairs_or_results:
        return "TEMPORAL_DATA_UNAVAILABLE"

    for item in pairs_or_results:
        if isinstance(item, TemporalEligibilityResult):
            status = item.status
            is_synth = bool(item.metadata.get("is_synthetic", False))
        elif isinstance(item, dict):
            status = item.get("temporal_eligibility") or item.get("status")
            is_synth = bool(item.get("is_synthetic", False) or item.get("synthetic", False))
        else:
            continue

        if exclude_synthetic and is_synth:
            continue

        if status == "TRUE":
            return "TEMPORAL_DATA_AVAILABLE"

    return "TEMPORAL_DATA_UNAVAILABLE"
