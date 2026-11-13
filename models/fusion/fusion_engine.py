"""
SPECTRA-X Model 5: FUSION-X Engine
Multimodal Evidence Integration & Scientific Co-Pilot Ranking

NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline

Scientific Constraints & Rules:
1. FUSION-X is a transparent heuristic/rule-based ranker, NOT a calibrated probabilistic classifier.
2. Coordinates are matched within documented angular tolerance (default 2.0 arcsec).
3. Missing modalities are explicitly flagged and handled via weight renormalization;
   missing measurements are NEVER silently replaced with zero.
4. Instrumental defects, fatal quality flags, and temporal subtraction dipoles are
   subject to scientific QC vetoes.
5. All outputs comply with models/common/candidate_schema.py.
"""

import os
import yaml
import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Union

import sys
sys.path.insert(0, os.path.abspath("."))
from models.common.candidate_schema import CandidateRecord, ALLOWED_VALIDITY_STATUSES
from spectra_engine.continuum_sidecar_interface import (
    ContinuumEvidenceRecord,
    CONTRACT_VERSION as CONTINUUM_CONTRACT_VERSION,
    ALLOWED_EVIDENCE_STATES,
)


class FusionEngine:
    """Multimodal Anomaly Integration & Scientific Co-Pilot Ranking Engine."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            default_cfg_path = os.path.join(os.path.dirname(__file__), "fusion_config.yaml")
            if os.path.exists(default_cfg_path):
                with open(default_cfg_path, "r") as f:
                    self.config = yaml.safe_load(f)
            else:
                self.config = self._get_default_config()

        # Parse config parameters
        self.match_radius_arcsec = float(self.config.get("spatial_matching", {}).get("coordinate_match_radius_arcsec", 2.0))
        self.weights = self.config.get("modality_weights", {"spectra": 0.35, "astrovision": 0.30, "chronos": 0.25, "motion": 0.10})
        self.scalers = self.config.get("modality_scalers", {
            "spectra_chi2_scale": 0.005,
            "astrovision_sigma_scale": 5.0,
            "chronos_sigma_scale": 5.0,
            "motion_offset_scale_arcsec": 2.0
        })
        self.missing_policy = self.config.get("missing_modality_policy", {
            "strategy": "renormalize_available_weights",
            "penalty_per_missing_modality": 0.05
        })
        self.qc_filters = self.config.get("quality_control_filters", {
            "fatal_flag_mask": 615,
            "reject_on_fatal_flag": True,
            "min_valid_channels": 1,
            "min_aperture_coverage_fraction": 0.80,
            "veto_chronos_dipoles": True
        })
        self.thresholds = self.config.get("classification_thresholds", {
            "extreme_spectral_chi2_threshold": 0.005,
            "temporal_significance_sigma_threshold": 5.0,
            "spatial_anomaly_sigma_threshold": 4.0,
            "high_priority_candidate_threshold": 0.65,
            "medium_priority_candidate_threshold": 0.40
        })

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        return {
            "spatial_matching": {"coordinate_match_radius_arcsec": 2.0},
            "modality_weights": {"spectra": 0.35, "astrovision": 0.30, "chronos": 0.25, "motion": 0.10},
            "modality_scalers": {
                "spectra_chi2_scale": 0.005,
                "astrovision_sigma_scale": 5.0,
                "chronos_sigma_scale": 5.0,
                "motion_offset_scale_arcsec": 2.0
            },
            "missing_modality_policy": {
                "strategy": "renormalize_available_weights",
                "penalty_per_missing_modality": 0.05
            },
            "quality_control_filters": {
                "fatal_flag_mask": 615,
                "reject_on_fatal_flag": True,
                "min_valid_channels": 1,
                "min_aperture_coverage_fraction": 0.80,
                "veto_chronos_dipoles": True
            },
            "classification_thresholds": {
                "extreme_spectral_chi2_threshold": 0.005,
                "temporal_significance_sigma_threshold": 5.0,
                "spatial_anomaly_sigma_threshold": 4.0,
                "high_priority_candidate_threshold": 0.65,
                "medium_priority_candidate_threshold": 0.40
            }
        }

    def angular_distance_arcsec(self, ra1: float, dec1: float, ra2: float, dec2: float) -> float:
        """Computes great-circle distance between two celestial coordinates in arcseconds."""
        ra1_rad, dec1_rad = math.radians(ra1), math.radians(dec1)
        ra2_rad, dec2_rad = math.radians(ra2), math.radians(dec2)
        d_ra = ra2_rad - ra1_rad
        d_dec = dec2_rad - dec1_rad
        a = math.sin(d_dec / 2.0)**2 + math.cos(dec1_rad) * math.cos(dec2_rad) * math.sin(d_ra / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        return math.degrees(c) * 3600.0

    def normalize_score(self, raw_score: Optional[float], modality: str) -> Optional[float]:
        """Soft-saturates raw metric into normalized [0.0, 1.0] interval without clipping."""
        if raw_score is None or math.isnan(raw_score):
            return None
        if raw_score < 0.0:
            raw_score = 0.0

        if modality == "spectra":
            scale = self.scalers.get("spectra_chi2_scale", 0.005)
            # Soft saturation: 1 - exp(-chi2 / scale)
            return float(1.0 - math.exp(-raw_score / max(scale, 1e-9)))
        elif modality == "astrovision":
            scale = self.scalers.get("astrovision_sigma_scale", 5.0)
            return float(1.0 - math.exp(-raw_score / max(scale, 1e-9)))
        elif modality == "chronos":
            scale = self.scalers.get("chronos_sigma_scale", 5.0)
            return float(1.0 - math.exp(-raw_score / max(scale, 1e-9)))
        elif modality == "motion":
            scale = self.scalers.get("motion_offset_scale_arcsec", 2.0)
            return float(min(1.0, raw_score / max(scale, 1e-9)))
        return None

    def evaluate_source(
        self,
        candidate_id: str,
        ra: float,
        dec: float,
        observation_id: str,
        observation_time: str,
        spectra_score: Optional[float] = None,
        spectra_uncertainty: Optional[float] = None,
        spectra_channels: int = 1,
        astrovision_score: Optional[float] = None,
        astrovision_uncertainty: Optional[float] = None,
        chronos_score: Optional[float] = None,
        chronos_is_dipole: bool = False,
        chronos_temporal_eligibility: Optional[str] = None,
        chronos_evidence_tier: Optional[str] = None,
        is_known_gaia_star: bool = False,
        gaia_source_id: Optional[str] = None,
        gaia_dist_arcsec: Optional[float] = None,
        is_known_asteroid: bool = False,
        asteroid_name: Optional[str] = None,
        is_known_transient: bool = False,
        transient_name: Optional[str] = None,
        quality_flags: Optional[int] = None,
        aperture_coverage: float = 1.0,
        edge_distance_pixels: float = 100.0,
        continuum_sidecar: Optional[Union[ContinuumEvidenceRecord, Dict[str, Any]]] = None
    ) -> CandidateRecord:
        """Evaluates single candidate through multimodal integration and scientific QC."""

        # Task 4.7: Ingest and strictly validate empirical continuum sidecar evidence (fail closed)
        validated_sidecar: Optional[ContinuumEvidenceRecord] = None
        if continuum_sidecar is not None:
            if isinstance(continuum_sidecar, dict):
                c_version = continuum_sidecar.get("contract_version")
                if c_version != CONTINUUM_CONTRACT_VERSION:
                    raise ValueError(
                        f"Invalid continuum sidecar contract_version: '{c_version}', expected '{CONTINUUM_CONTRACT_VERSION}'"
                    )
                s_id = continuum_sidecar.get("source_id")
                if s_id != candidate_id:
                    raise ValueError(
                        f"Continuum sidecar source_id mismatch: '{s_id}' does not match candidate_id '{candidate_id}'"
                    )
                validated_sidecar = ContinuumEvidenceRecord(**continuum_sidecar)
                validated_sidecar.validate()
            elif isinstance(continuum_sidecar, ContinuumEvidenceRecord):
                if continuum_sidecar.contract_version != CONTINUUM_CONTRACT_VERSION:
                    raise ValueError(
                        f"Invalid continuum sidecar contract_version: '{continuum_sidecar.contract_version}', expected '{CONTINUUM_CONTRACT_VERSION}'"
                    )
                if continuum_sidecar.source_id != candidate_id:
                    raise ValueError(
                        f"Continuum sidecar source_id mismatch: '{continuum_sidecar.source_id}' != '{candidate_id}'"
                    )
                continuum_sidecar.validate()
                validated_sidecar = continuum_sidecar
            else:
                raise TypeError(
                    f"continuum_sidecar must be ContinuumEvidenceRecord or dict, got {type(continuum_sidecar)}"
                )

        # 1. Scientific Quality Control Screening
        rejection_reasons = []
        warning_reasons = []

        fatal_mask = self.qc_filters.get("fatal_flag_mask", 615)
        if quality_flags is not None and (quality_flags & fatal_mask) > 0:
            rejection_reasons.append(f"FATAL_QUALITY_FLAG_0x{quality_flags:04X}")

        if chronos_is_dipole and self.qc_filters.get("veto_chronos_dipoles", True):
            rejection_reasons.append("CHRONOS_DIPOLE_SUBTRACTION_ARTIFACT")

        if spectra_channels < self.qc_filters.get("min_valid_channels", 1):
            rejection_reasons.append(f"INSUFFICIENT_SPECTRAL_CHANNELS_{spectra_channels}")

        if aperture_coverage < self.qc_filters.get("min_aperture_coverage_fraction", 0.80):
            warning_reasons.append(f"PARTIAL_APERTURE_COVERAGE_{aperture_coverage:.2f}")

        if edge_distance_pixels < self.qc_filters.get("veto_edge_proximity_pixels", 5):
            warning_reasons.append(f"DETECTOR_EDGE_PROXIMITY_{edge_distance_pixels:.1f}px")

        # Task 1.3K Safety Check: Detect temporal spikes without verified multi-epoch eligibility
        temporal_sig_thresh = self.thresholds.get("temporal_significance_sigma_threshold", 5.0)
        if chronos_score is not None and chronos_score > temporal_sig_thresh:
            if chronos_temporal_eligibility != "TRUE":
                warning_reasons.append(f"UNVERIFIED_TEMPORAL_EVIDENCE_{chronos_temporal_eligibility or 'UNVERIFIABLE'}")

        # 2. Modality Normalization
        norm_scores = {
            "spectra": self.normalize_score(spectra_score, "spectra"),
            "astrovision": self.normalize_score(astrovision_score, "astrovision"),
            "chronos": self.normalize_score(chronos_score, "chronos"),
            "motion": None  # Evaluated contextually
        }

        # Motion score logic:
        # If matched with Gaia stationary star -> motion anomaly = 0.0
        # If unmatched with Gaia and high temporal significance -> candidate motion/transient anomaly
        if is_known_gaia_star:
            norm_scores["motion"] = 0.0
        elif chronos_score is not None and chronos_score > 3.0:
            norm_scores["motion"] = float(min(1.0, chronos_score / 10.0))
        elif is_known_asteroid:
            norm_scores["motion"] = 0.8
        else:
            norm_scores["motion"] = None  # Missing kinematic confirmation

        # 3. Transparent Weighted Ranking with Explicit Missing-Modality Handling
        available_modalities = {k: v for k, v in norm_scores.items() if v is not None}
        missing_modalities = [k for k, v in norm_scores.items() if v is None]

        if not available_modalities:
            validity_status = "INSUFFICIENT_DATA"
            fused_score = 0.0
            evidence_summary = "INSUFFICIENT_DATA: No active modalities available for evaluation."
        else:
            total_active_weight = sum(self.weights[k] for k in available_modalities.keys())
            if total_active_weight > 0:
                weighted_sum = sum(self.weights[k] * available_modalities[k] for k in available_modalities.keys())
                renormalized_score = weighted_sum / total_active_weight
            else:
                renormalized_score = 0.0

            # Missing modality penalty (avoids over-promoting uncorroborated single-modality spikes)
            penalty = len(missing_modalities) * self.missing_policy.get("penalty_per_missing_modality", 0.05)
            fused_score = float(np.clip(renormalized_score * (1.0 - penalty), 0.0, 1.0))

            # Determine Validity Status
            if rejection_reasons:
                validity_status = "REJECTED"
            elif warning_reasons:
                validity_status = "WARNING"
            else:
                validity_status = "VALID"

            # 4. Scientific Co-Pilot Classification
            classification_tag = self._classify(
                fused_score=fused_score,
                spectra_score=spectra_score,
                astrovision_score=astrovision_score,
                chronos_score=chronos_score,
                is_known_gaia_star=is_known_gaia_star,
                is_known_asteroid=is_known_asteroid,
                is_known_transient=is_known_transient,
                rejection_reasons=rejection_reasons,
                chronos_temporal_eligibility=chronos_temporal_eligibility
            )

            # Build evidence breakdown
            evidence_parts = [f"CLASSIFICATION: {classification_tag}"]
            for mod in ["spectra", "astrovision", "chronos", "motion"]:
                if mod in available_modalities:
                    evidence_parts.append(f"{mod.upper()}_NORM={available_modalities[mod]:.3f}(wt={self.weights[mod]:.2f})")
                else:
                    evidence_parts.append(f"{mod.upper()}=MISSING")

            if chronos_temporal_eligibility is not None:
                evidence_parts.append(f"CHRONOS_ELIGIBILITY={chronos_temporal_eligibility}")
            if chronos_evidence_tier is not None:
                evidence_parts.append(f"CHRONOS_TIER={chronos_evidence_tier}")

            if rejection_reasons:
                evidence_parts.append(f"VETOES=[{'; '.join(rejection_reasons)}]")
            if warning_reasons:
                evidence_parts.append(f"WARNINGS=[{'; '.join(warning_reasons)}]")

            if is_known_asteroid:
                evidence_parts.append(f"ASTEROID_MATCH={asteroid_name or 'CONFIRMED'}")
            if is_known_transient:
                evidence_parts.append(f"TRANSIENT_MATCH={transient_name or 'ZTF_BTS'}")
            if is_known_gaia_star:
                d_str = f"(d={gaia_dist_arcsec:.2f}\")" if gaia_dist_arcsec is not None else ""
                evidence_parts.append(f"GAIA_MATCH={gaia_source_id or 'STAR'}{d_str}")

            if validated_sidecar is not None:
                sidecar_tag = f"CONTINUUM_STATE={validated_sidecar.evidence_state}"
                if validated_sidecar.evidence_state == "POSSIBLE_INFRARED_EXCESS":
                    if validated_sidecar.excess_significance_sigma is not None:
                        sidecar_tag += f"(excess_sig={validated_sidecar.excess_significance_sigma:.2f}\u03c3)"
                evidence_parts.append(sidecar_tag)
                if validated_sidecar.counterpart_ambiguity:
                    evidence_parts.append("CONTINUUM_AMBIGUOUS_COUNTERPART=TRUE")
                if validated_sidecar.is_upper_limit:
                    evidence_parts.append("CONTINUUM_UPPER_LIMIT=TRUE")

            evidence_summary = " | ".join(evidence_parts)

        # 5. Build Standard CandidateRecord
        record = CandidateRecord(
            candidate_id=candidate_id,
            ra=float(ra),
            dec=float(dec),
            observation_id=observation_id,
            observation_time=observation_time,
            module_name="FUSION-X",
            anomaly_score=round(fused_score, 5),
            score_type="HEURISTIC_PRIORITY_SCORE",
            validity_status=validity_status,
            evidence_summary=evidence_summary,
            input_provenance=(
                f"SPECTRA:{spectra_score is not None};ASTRO:{astrovision_score is not None};"
                f"CHRONOS:{chronos_score is not None};MOTION:{norm_scores['motion'] is not None}"
                + (f";SIDECAR:{validated_sidecar.evidence_state}" if validated_sidecar else "")
            ),
            uncertainty=spectra_uncertainty if spectra_uncertainty is not None else None,
            quality_flags=quality_flags,
            metadata={
                "spectra_chi2": float(spectra_score) if spectra_score is not None else None,
                "spectra_channels": int(spectra_channels),
                "astrovision_peak_residual": float(astrovision_score) if astrovision_score is not None else None,
                "chronos_significance_sigma": float(chronos_score) if chronos_score is not None else None,
                "chronos_temporal_eligibility": chronos_temporal_eligibility,
                "chronos_evidence_tier": chronos_evidence_tier,
                "is_known_gaia_star": bool(is_known_gaia_star),
                "gaia_source_id": str(gaia_source_id) if gaia_source_id else None,
                "is_known_asteroid": bool(is_known_asteroid),
                "is_known_transient": bool(is_known_transient),
                "missing_modalities": missing_modalities,
                "rejection_reasons": rejection_reasons,
                "warning_reasons": warning_reasons,
                "continuum_sidecar": validated_sidecar.to_dict() if validated_sidecar else None,
                "continuum_evidence_state": validated_sidecar.evidence_state if validated_sidecar else None,
            },
            temporal_eligibility=chronos_temporal_eligibility
        )
        return record

    def _classify(
        self,
        fused_score: float,
        spectra_score: Optional[float],
        astrovision_score: Optional[float],
        chronos_score: Optional[float],
        is_known_gaia_star: bool,
        is_known_asteroid: bool,
        is_known_transient: bool,
        rejection_reasons: List[str],
        chronos_temporal_eligibility: Optional[str] = None
    ) -> str:
        """Assigns scientific category tag based on multimodal evidence matrix."""
        if rejection_reasons:
            return "INSTRUMENTAL_DEFECT_OR_VETOED_ARTIFACT"
        if is_known_asteroid:
            return "KNOWN_SOLAR_SYSTEM_OBJECT"
        if is_known_transient:
            return "CONFIRMED_ASTRONOMICAL_TRANSIENT"
        
        # Temporal + Kinematic (high temporal, no static Gaia counterpart)
        temporal_sig_thresh = self.thresholds.get("temporal_significance_sigma_threshold", 5.0)
        if chronos_score is not None and chronos_score > temporal_sig_thresh:
            # Task 1.3K Safety Gate: Genuinely independent multi-epoch verification required
            if chronos_temporal_eligibility == "TRUE":
                if not is_known_gaia_star:
                    return "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
                else:
                    return "STELLAR_VARIABILITY_OR_FLARE"
            else:
                # Do NOT promote without verified independent temporal evidence
                return "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"

        # Multi-modal corroboration
        multi_modal = (spectra_score is not None and spectra_score > self.thresholds.get("extreme_spectral_chi2_threshold", 0.005)) and \
                      (astrovision_score is not None and astrovision_score > self.thresholds.get("spatial_anomaly_sigma_threshold", 4.0))
        if multi_modal:
            return "MULTI_MODAL_CO_PILOT_ANOMALY"

        # Spectral outlier
        if spectra_score is not None and spectra_score > self.thresholds.get("extreme_spectral_chi2_threshold", 0.005):
            return "EXTREME_SPECTRAL_OUTLIER"

        # Spatial morphology outlier
        if astrovision_score is not None and astrovision_score > self.thresholds.get("spatial_anomaly_sigma_threshold", 4.0):
            return "EXTENDED_OR_UNUSUAL_SPATIAL_STRUCTURE"

        if fused_score >= self.thresholds.get("medium_priority_candidate_threshold", 0.40):
            return "MODERATE_ANOMALY_CANDIDATE"

        return "NOMINAL_ASTRONOMICAL_SOURCE"
