"""
SPECTRA-X / F1 — Phase 3, Task 1.3B
SPECTRA Evidence Adapter for FUSION-X Integration

Package: spectra_engine
Authoritative Implementation

Scientific Context & Rules:
1. Strict read-only integration interface; no model retraining or parameter modification.
2. Cross-stratum raw score pooling is strictly prohibited.
3. Scores are normalized to empirical percentiles and robust IQR-scaled deviations using verified frozen calibration data.
4. Channel coverage gate enforces eligibility (fewer than 5 valid channels is UNINFORMATIVE).
5. Provisional threshold exceedance represents empirical reference exceedance, NOT certified FPR.
6. Mandatory limitation codes are attached to every record.
7. Unassisted autonomous discovery is strictly prohibited; cross-modal corroboration required.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple, Union
import numpy as np
import pandas as pd

from spectra_engine.fusion_contract import (
    CONTRACT_VERSION,
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


class SpectraEvidenceAdapter:
    """
    Standardized, scientific evidence adapter connecting the frozen SPECTRA V2 model
    to downstream FUSION-X multimodal ranking.

    Authoritative implementation located in spectra_engine package.
    """

    def __init__(
        self,
        base_dir: Optional[str] = None,
        checkpoint_path: Optional[str] = None,
        thresholds_path: Optional[str] = None,
        calib_scores_path: Optional[str] = None,
        auto_load: bool = True
    ):
        self.base_dir = base_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.checkpoint_path = checkpoint_path or os.path.join(self.base_dir, "checkpoints", "spectra_masked_ae_v2.pt")
        self.thresholds_path = thresholds_path or os.path.join(self.base_dir, "data", "processed", "spectra", "spectra_v2_provisional_thresholds_v1.json")
        self.calib_scores_path = calib_scores_path or os.path.join(self.base_dir, "data", "processed", "spectra", "spectra_p0008_calibration_scores_v1.csv")

        self.assets_verified = False
        self.calib_loaded = False

        self.sorted_calib_scores: Dict[str, np.ndarray] = {}
        self.strata_stats: Dict[str, Dict[str, float]] = {}

        if auto_load:
            self.validate_assets()
            self.load_calibration_reference()

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        """Computes SHA-256 hash of a file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(1048576):
                h.update(chunk)
        return h.hexdigest()

    def validate_assets(self, raise_on_error: bool = True) -> Dict[str, Any]:
        """
        Cryptographically verifies the frozen model checkpoint and calibration assets.
        Ensures zero unauthorized tampering or modifications.
        """
        results = {
            "checkpoint": {"path": self.checkpoint_path, "expected": EXPECTED_CHECKPOINT_SHA256, "status": "UNKNOWN"},
            "thresholds": {"path": self.thresholds_path, "expected": EXPECTED_THRESHOLDS_SHA256, "status": "UNKNOWN"},
            "calib_scores": {"path": self.calib_scores_path, "expected": EXPECTED_CALIB_SCORES_SHA256, "status": "UNKNOWN"},
            "all_verified": False
        }

        all_ok = True
        for key, info in [("checkpoint", results["checkpoint"]), ("thresholds", results["thresholds"]), ("calib_scores", results["calib_scores"])]:
            p = info["path"]
            if not os.path.exists(p):
                info["status"] = "FILE_MISSING"
                all_ok = False
                if raise_on_error:
                    raise FileNotFoundError(f"Required frozen scientific asset missing: {p}")
                continue

            actual_hash = self.compute_sha256(p)
            info["actual"] = actual_hash
            if actual_hash != info["expected"]:
                info["status"] = "HASH_MISMATCH"
                all_ok = False
                if raise_on_error:
                    raise ValueError(f"CRITICAL STOP: Hash mismatch for {key}! Expected {info['expected']}, got {actual_hash}")
            else:
                info["status"] = "VERIFIED_IMMUTABLE"

        results["all_verified"] = all_ok
        self.assets_verified = all_ok
        return results

    def load_calibration_reference(self) -> None:
        """
        Loads the frozen empirical calibration scores and summary thresholds.
        Reconstructs exact empirical percentile distributions per stratum.
        """
        if not self.assets_verified:
            self.validate_assets(raise_on_error=True)

        # 1. Load thresholds JSON
        with open(self.thresholds_path, "r", encoding="utf-8") as f:
            th_data = json.load(f)

        strata_th = th_data.get("strata_thresholds", {})
        for pair_key, pdata in strata_th.items():
            canon_pair = CANONICAL_STRATA_MAP.get(pair_key, pair_key)
            score_summary = pdata.get("score_summary", {})
            t05 = pdata.get("threshold_alpha_0_05", {}).get("threshold_value")
            t01 = pdata.get("threshold_alpha_0_01", {}).get("threshold_value")
            med = score_summary.get("median")
            iqr = score_summary.get("iqr")

            self.strata_stats[canon_pair] = {
                "median": float(med),
                "iqr": float(iqr),
                "threshold_05": float(t05),
                "threshold_01": float(t01)
            }

        # 2. Load calibration scores CSV for exact empirical percentile ranking
        calib_df = pd.read_csv(self.calib_scores_path)
        for pair_key in ["D1,D4", "D2,D5", "D3,D6"]:
            pdf = calib_df[calib_df["detector_provenance"] == pair_key]
            if len(pdf) == 0:
                # Try with plus sign
                alt_pair = pair_key.replace(",", "+")
                pdf = calib_df[calib_df["detector_provenance"] == alt_pair]

            if len(pdf) == 0:
                raise ValueError(f"Missing calibration scores for stratum: {pair_key}")

            # Store sorted array for exact deterministic empirical percentile lookup
            self.sorted_calib_scores[pair_key] = np.sort(pdf["score"].values.astype(np.float64))

        self.calib_loaded = True

    def evaluate_eligibility(
        self,
        valid_channels_count: int,
        quality_flags: Optional[int] = None,
        detector_stratum: Optional[str] = None
    ) -> Tuple[EligibilityStatus, List[str]]:
        """
        Evaluates source eligibility according to strict scientific coverage and quality gates.
        Returns (EligibilityStatus, exclusion_reasons).
        """
        reasons = []

        if valid_channels_count == 0:
            return EligibilityStatus.NO_OBSERVATIONAL_COVERAGE, ["Zero observed spectral channels in field of view."]

        if valid_channels_count < 5:
            return EligibilityStatus.UNINFORMATIVE, [f"Insufficient channel coverage: {valid_channels_count} valid channels (< 5 required)."]

        if detector_stratum is None or detector_stratum not in VALID_STRATA:
            return EligibilityStatus.STRATUM_UNRESOLVED, [f"Unresolved or invalid detector stratum: '{detector_stratum}'."]

        # Check fatal quality flags (mask 615 = bits 1, 2, 4, 32, 64, 512: saturated, bad neighborhood, fatal calibration)
        if quality_flags is not None and (quality_flags & 615 != 0):
            return EligibilityStatus.QUALITY_REJECTED, [f"Fatal quality flag trigger: {quality_flags} (mask 615 violation)."]

        if not self.calib_loaded:
            return EligibilityStatus.NORMALIZATION_UNAVAILABLE, ["Calibration reference not loaded or corrupted."]

        canon_stratum = CANONICAL_STRATA_MAP[detector_stratum]
        if canon_stratum not in self.sorted_calib_scores or canon_stratum not in self.strata_stats:
            return EligibilityStatus.NORMALIZATION_UNAVAILABLE, [f"Normalization statistics unavailable for stratum '{canon_stratum}'."]

        return EligibilityStatus.ELIGIBLE, []

    def normalize_score(
        self,
        raw_score: float,
        detector_stratum: str
    ) -> Tuple[float, float]:
        """
        Computes stratum-normalized empirical percentile and IQR-scaled stratum deviation
        using verified frozen Pointing P0008 calibration data.
        Cross-stratum raw pooling is strictly prohibited.

        Mathematical Formulation & Semantics:
        1. Stratum-Normalized Percentile Rank (Primary Metric):
           P(S) = (1 / N) * sum_{i=1}^N 1(c_i <= S)
           Computed via np.searchsorted with side='right' over sorted P0008 calibration scores,
           ensuring deterministic right-continuous empirical cumulative distribution function.

        2. IQR-Scaled Stratum Deviation (Secondary Metric):
           Z = (S - Median_stratum) / IQR_stratum
           NOTE ON NOMENCLATURE:
           This quantity is an unstandardized IQR-scaled deviation (IQR-normalized distance).
           It is NOT the conventional MAD-based robust Z-score (Z_MAD = (S - Med) / (1.4826 * MAD))
           nor Gaussian-standardized IQR deviation (IQR / 1.34898).
           If IQR_stratum <= 0, a defensive guard returns 0.0 to prevent division by zero.
        """
        if not self.calib_loaded:
            raise RuntimeError("Cannot normalize score: Calibration reference not loaded.")

        if detector_stratum not in VALID_STRATA:
            raise ValueError(f"Invalid detector stratum '{detector_stratum}'. Allowed: {VALID_STRATA}")

        if raw_score is None or np.isnan(raw_score) or raw_score < 0:
            raise ValueError(f"Invalid raw anomaly score: {raw_score}")

        canon_stratum = CANONICAL_STRATA_MAP[detector_stratum]
        scores = self.sorted_calib_scores[canon_stratum]
        stats = self.strata_stats[canon_stratum]

        # 1. Deterministic Empirical Percentile
        # np.searchsorted with side='right' gives count of elements <= raw_score
        n = len(scores)
        rank = np.searchsorted(scores, raw_score, side="right")
        percentile = float(np.clip(rank / float(n), 0.0, 1.0))

        # 2. Robust IQR-scaled deviation (optional_stratum_z_score)
        median_val = stats["median"]
        iqr_val = stats["iqr"]
        z_score = float((raw_score - median_val) / iqr_val) if iqr_val > 0 else 0.0

        return percentile, z_score

    def create_evidence_record(
        self,
        source_id: Union[str, int],
        pointing_id: Union[str, int],
        detector_stratum: str,
        valid_channels_count: int,
        raw_anomaly_score: Optional[float] = None,
        uncertainty_available: bool = True,
        data_quality_flags: Optional[int] = None,
        provenance_reference: Optional[str] = None,
        astrovision_corroboration: Optional[Dict[str, Any]] = None,
        chronos_corroboration: Optional[Dict[str, Any]] = None,
        continuum_sidecar_corroboration: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SpectraFusionEvidenceRecord:
        """
        Constructs a complete, validated SpectraFusionEvidenceRecord according to
        the versioned SPECTRA_FUSION_EVIDENCE_V1 contract.
        """
        source_id_str = str(source_id)
        pointing_id_str = str(pointing_id)
        now_utc = datetime.now(timezone.utc).isoformat()
        prov_ref = provenance_reference or f"SPHEREx_L2_PTG{pointing_id_str}_SRC{source_id_str}"

        # 1. Evaluate coverage and quality gate
        eligibility, reasons = self.evaluate_eligibility(
            valid_channels_count=valid_channels_count,
            quality_flags=data_quality_flags,
            detector_stratum=detector_stratum
        )

        channel_coverage_fraction = float(np.clip(valid_channels_count / 102.0, 0.0, 1.0))
        spectral_feature_scope = "NARROW_LINE_HIGH_SENSITIVITY_CONTINUUM_LIMITED"

        # Build limitation codes
        limitation_codes = list(BASE_LIMITATION_CODES)
        canon_stratum = CANONICAL_STRATA_MAP.get(detector_stratum)
        if canon_stratum and canon_stratum in STRATUM_LIMITATION_CODES:
            limitation_codes.extend(STRATUM_LIMITATION_CODES[canon_stratum])

        # Evaluate cross-modal status
        corroborations_present = sum(1 for c in [astrovision_corroboration, chronos_corroboration, continuum_sidecar_corroboration] if c is not None)
        if corroborations_present > 0:
            cross_modal_status = CrossModalStatus.CORROBORATED.value
        else:
            cross_modal_status = CrossModalStatus.NO_CROSS_MODAL_DATA.value

        # Handle Ineligible cases safely
        if eligibility != EligibilityStatus.ELIGIBLE:
            return SpectraFusionEvidenceRecord(
                contract_version=CONTRACT_VERSION,
                model_id=MODEL_ID,
                model_version=MODEL_VERSION,
                checkpoint_sha256=EXPECTED_CHECKPOINT_SHA256,
                threshold_artifact_sha256=EXPECTED_THRESHOLDS_SHA256,
                pipeline_build=PIPELINE_BUILD,
                inference_timestamp=now_utc,
                source_id=source_id_str,
                pointing_id=pointing_id_str,
                detector_stratum=detector_stratum or "UNKNOWN",
                provenance_reference=prov_ref,
                raw_anomaly_score=None,
                stratum_normalized_percentile=None,
                optional_stratum_z_score=None,
                threshold_05=None,
                threshold_01=None,
                threshold_exceedance_level=ThresholdExceedanceLevel.NOT_EVALUATED.value,
                valid_channel_count=valid_channels_count,
                channel_coverage_fraction=channel_coverage_fraction,
                spectral_feature_scope=spectral_feature_scope,
                uncertainty_available=uncertainty_available,
                data_quality_flags=data_quality_flags,
                eligibility_status=eligibility.value,
                limitation_codes=limitation_codes,
                calibration_reference_version="provisional_p0008_v1",
                anomaly_detected=False,
                evidence_strength=EvidenceStrength.UNINFORMATIVE.value,
                interpretation=f"Ineligible for SPECTRA anomaly scoring: {'; '.join(reasons)}",
                human_review_required=False,
                cross_modal_corroboration_status=cross_modal_status,
                astrovision_corroboration=astrovision_corroboration,
                chronos_corroboration=chronos_corroboration,
                continuum_sidecar_corroboration=continuum_sidecar_corroboration,
                metadata=metadata or {}
            )

        # 2. Eligible: perform normalization and threshold evaluation
        if raw_anomaly_score is None:
            raise ValueError("raw_anomaly_score cannot be None for ELIGIBLE source.")

        percentile, z_score = self.normalize_score(raw_anomaly_score, detector_stratum)
        stats = self.strata_stats[canon_stratum]
        t05 = stats["threshold_05"]
        t01 = stats["threshold_01"]

        # Threshold exceedance level
        if raw_anomaly_score > t01:
            exceedance_level = ThresholdExceedanceLevel.EXCEEDS_T01.value
            strength = EvidenceStrength.STRONG.value
            anomaly_detected = True
            interpretation_str = (
                f"Score {raw_anomaly_score:.2f} exceeds provisional 99th percentile threshold ({t01:.2f}) "
                f"in stratum {canon_stratum} (Z={z_score:+.2f}). Extreme spectral feature anomaly. "
                "Autonomous discovery prohibited; cross-modal confirmation and human review required."
            )
            human_review = True
        elif raw_anomaly_score > t05:
            exceedance_level = ThresholdExceedanceLevel.EXCEEDS_T05.value
            strength = EvidenceStrength.MARGINAL.value
            anomaly_detected = True
            interpretation_str = (
                f"Score {raw_anomaly_score:.2f} exceeds provisional 95th percentile threshold ({t05:.2f}) "
                f"in stratum {canon_stratum} (Z={z_score:+.2f}). Candidate localized spectral feature detected. "
                "Autonomous discovery prohibited; requires cross-modal confirmation."
            )
            human_review = True
        else:
            exceedance_level = ThresholdExceedanceLevel.NONE.value
            strength = EvidenceStrength.NONE.value
            anomaly_detected = False
            interpretation_str = (
                f"Score {raw_anomaly_score:.2f} consistent with provisional-null reference in stratum {canon_stratum} "
                f"(Percentile={percentile*100:.1f}%, Z={z_score:+.2f}). No significant spectral outlier detected."
            )
            human_review = False

        return SpectraFusionEvidenceRecord(
            contract_version=CONTRACT_VERSION,
            model_id=MODEL_ID,
            model_version=MODEL_VERSION,
            checkpoint_sha256=EXPECTED_CHECKPOINT_SHA256,
            threshold_artifact_sha256=EXPECTED_THRESHOLDS_SHA256,
            pipeline_build=PIPELINE_BUILD,
            inference_timestamp=now_utc,
            source_id=source_id_str,
            pointing_id=pointing_id_str,
            detector_stratum=canon_stratum,
            provenance_reference=prov_ref,
            raw_anomaly_score=float(raw_anomaly_score),
            stratum_normalized_percentile=percentile,
            optional_stratum_z_score=z_score,
            threshold_05=t05,
            threshold_01=t01,
            threshold_exceedance_level=exceedance_level,
            valid_channel_count=valid_channels_count,
            channel_coverage_fraction=channel_coverage_fraction,
            spectral_feature_scope=spectral_feature_scope,
            uncertainty_available=uncertainty_available,
            data_quality_flags=data_quality_flags,
            eligibility_status=eligibility.value,
            limitation_codes=limitation_codes,
            calibration_reference_version="provisional_p0008_v1",
            anomaly_detected=anomaly_detected,
            evidence_strength=strength,
            interpretation=interpretation_str,
            human_review_required=human_review,
            cross_modal_corroboration_status=cross_modal_status,
            astrovision_corroboration=astrovision_corroboration,
            chronos_corroboration=chronos_corroboration,
            continuum_sidecar_corroboration=continuum_sidecar_corroboration,
            metadata=metadata or {}
        )

    def validate_contract(self, record: SpectraFusionEvidenceRecord) -> bool:
        """Validates contract compliance for an evidence record."""
        record.validate()
        return True

    def serialize_evidence(
        self,
        record: SpectraFusionEvidenceRecord,
        as_json: bool = False,
        indent: Optional[int] = 2
    ) -> Union[Dict[str, Any], str]:
        """Serializes record to dict or JSON string."""
        if as_json:
            return record.to_json(indent=indent)
        return record.to_dict()


__all__ = [
    "SpectraEvidenceAdapter",
]

