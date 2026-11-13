"""
Authoritative Concrete Implementation of the Continuum Sidecar Engine.

Integrates the Task 4.6 Empirical Infrared Excess Validation Engine with the
CONTINUUM_SIDECAR_EVIDENCE_V1 data contract for downstream multimodal FUSION-X ranking.
"""

import os
import math
import numpy as np
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from spectra_engine.continuum_sidecar_interface import (
    SIDECAR_CONTRACT_VERSION,
    ALLOWED_EVIDENCE_STATES,
    BASE_SIDECAR_LIMITATION_CODES,
    CANONICAL_CALIBRATION_POINTING,
    normalize_pointing_id,
    is_trusted_calibration_provenance,
    ContinuumEvidenceRecord,
    ContinuumSidecarInterface
)
from spectra_engine.validation.infrared_excess.zero_points import PHOTOMETRIC_BANDS
from spectra_engine.validation.infrared_excess.catalog_normalizer import (
    NormalizedSourceRecord,
    NormalizedMeasurement
)
from spectra_engine.validation.infrared_excess.photospheric_model import (
    PhotosphericBaselineEstimator,
    PhotosphericPrediction
)
from spectra_engine.validation.infrared_excess.excess_engine import (
    InfraredExcessEngine,
    ExcessBandResult,
    SPHERExOverlapResult
)
from spectra_engine.validation.infrared_excess.evidence_classifier import (
    InfraredEvidenceClassifier
)


class EmpiricalContinuumSidecar(ContinuumSidecarInterface):
    """
    Empirical continuum sidecar engine connecting external photometric catalogs
    (Gaia, 2MASS, ALLWISE) and SPHEREx 102-channel aperture photometry to FUSION-X.
    """

    def __init__(self):
        self.contract_version = SIDECAR_CONTRACT_VERSION
        self.pipeline_build = "l2b-v27-2026-222"
        self.provenance_reference = "SPECTRA-X_Task_4.6_Empirical_Validation_Engine"

    def validate_sidecar_assets(self) -> bool:
        """Verifies that photometric zero points and calibration definitions are intact."""
        required_bands = ["2MASS_J", "2MASS_H", "2MASS_Ks", "WISE_W1", "WISE_W2", "Gaia_G"]
        for b in required_bands:
            if b not in PHOTOMETRIC_BANDS:
                return False
            if PHOTOMETRIC_BANDS[b].zero_point_flux_mJy <= 0:
                return False
        return True

    def evaluate_continuum(
        self,
        source_id: str,
        pointing_id: str,
        wavelengths: List[float],
        fluxes: List[float],
        uncertainties: List[float],
        valid_mask: List[bool],
        photometric_record: Optional[NormalizedSourceRecord] = None
    ) -> ContinuumEvidenceRecord:
        """
        Evaluates infrared continuum excess and stellar photospheric consistency.
        Fails closed on invalid inputs. Enforces cohort isolation.
        """
        source_id_str = str(source_id)
        pointing_id_str = str(pointing_id)
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Input sanity check & fail-closed validation
        if len(wavelengths) != len(fluxes) or len(fluxes) != len(uncertainties) or len(uncertainties) != len(valid_mask):
            raise ValueError("Mismatched spectral array lengths in evaluate_continuum.")

        for u in uncertainties:
            if u is not None and (math.isnan(u) or u < 0):
                raise ValueError("Uncertainty must be non-negative finite float or None.")

        # 2. Centralized Provenance & Calibration Eligibility Resolution (Task 4.10)
        norm_pt = normalize_pointing_id(pointing_id)
        if norm_pt is None:
            raise ValueError(f"Invalid pointing_id: must be non-empty string, got {pointing_id}")

        sec_pt = getattr(photometric_record, "cohort_pointing", None) if photometric_record else None
        photo_meta = getattr(photometric_record, "metadata", None) if photometric_record else None

        is_cal_eligible = is_trusted_calibration_provenance(
            pointing_id=pointing_id_str,
            metadata=photo_meta,
            secondary_pointing=sec_pt
        )

        limitation_codes = list(BASE_SIDECAR_LIMITATION_CODES)
        if not is_cal_eligible:
            limitation_codes.append("BLIND_COHORT_UNVERIFIED_BASELINE")

        # 3. If external photometric record is supplied: evaluate empirical excess
        if photometric_record is not None:
            # Enforce source_id match
            if str(photometric_record.source_id) != source_id_str:
                raise ValueError(
                    f"Source ID mismatch between caller ({source_id_str}) and photometric_record ({photometric_record.source_id})"
                )

            # Predict photospheric baseline
            pred_w1 = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W1", photometric_record)
            pred_w2 = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W2", photometric_record)

            # Evaluate excess in W1 and W2
            res_w1 = InfraredExcessEngine.evaluate_band_excess("WISE_W1", photometric_record, pred_w1)
            res_w2 = InfraredExcessEngine.evaluate_band_excess("WISE_W2", photometric_record, pred_w2)

            # Evidence classification
            ev_state, ev_reason = InfraredEvidenceClassifier.classify_source(photometric_record, res_w1, res_w2)

            color_excess_detected = (ev_state == "POSSIBLE_INFRARED_EXCESS")
            primary_sig = res_w2.excess_significance_sigma if res_w2.is_evaluable else res_w1.excess_significance_sigma

            candidate_indication = False
            if not is_cal_eligible:
                # Task 4.10 Calibration Allowlist Governance Enforcement (Remediates FIND-4.9-01):
                # Only canonical P0008 with trusted provenance can claim confirmed excess or verified
                # photospheric consistency because the empirical baseline locus was calibrated only on P0008.
                if ev_state == "POSSIBLE_INFRARED_EXCESS":
                    candidate_indication = True
                    ev_state = "UNVERIFIABLE"
                    ev_reason = (
                        f"UNVERIFIED_BASELINE_RESTRICTION: Candidate-level excess indication (S={primary_sig:.2f}σ) "
                        f"requires independent validation; unverified baseline cannot confirm excess on uncalibrated pointing {pointing_id_str}."
                    )
                elif ev_state == "SUPPORTED_PHOTOSPHERIC_CONSISTENCY":
                    ev_state = "UNVERIFIABLE"
                    ev_reason = (
                        f"UNVERIFIED_BASELINE_RESTRICTION: Apparent photospheric consistency on uncalibrated pointing {pointing_id_str} "
                        f"cannot be certified without field-level baseline calibration."
                    )
                # color_excess_detected must strictly be False for all non-calibration cohorts
                color_excess_detected = False

            color_indices = {}
            if res_w1.observed_flux_mJy and res_w2.observed_flux_mJy:
                color_indices["W1_W2_flux_ratio"] = round(res_w1.observed_flux_mJy / res_w2.observed_flux_mJy, 3)
            if res_w1.flux_ratio_obs_to_phot:
                color_indices["W1_obs_to_phot_ratio"] = res_w1.flux_ratio_obs_to_phot
            if res_w2.flux_ratio_obs_to_phot:
                color_indices["W2_obs_to_phot_ratio"] = res_w2.flux_ratio_obs_to_phot

            # SPHEREx overlap channels evaluation
            spherex_ch_list = []
            for i in range(len(wavelengths)):
                spherex_ch_list.append({
                    "channel_index": i,
                    "wavelength_microns": wavelengths[i],
                    "flux_mJy": fluxes[i],
                    "uncertainty_mJy": uncertainties[i],
                    "is_valid": valid_mask[i]
                })
            spx_overlap = InfraredExcessEngine.evaluate_spherex_overlap(spherex_ch_list, pred_w2)
            valid_spx = [ch for ch in spx_overlap if ch.is_valid_channel]

            spx_mean_res = float(np.mean([ch.residual_flux_mJy for ch in valid_spx])) if valid_spx else None
            spx_mean_sig = float(np.mean([ch.significance_sigma for ch in valid_spx])) if valid_spx else None

            # Multi-catalog photometric evidence preservation (Task 4.20C)
            multicatalog_evidence = {
                "catalogs_evaluated": sorted(list({m.catalog_source for m in photometric_record.measurements.values()})),
                "band_measurements": {
                    bname: {
                        "catalog_source": m.catalog_source,
                        "effective_wavelength_microns": m.effective_wavelength_microns,
                        "magnitude": m.magnitude,
                        "magnitude_error": m.magnitude_error,
                        "flux_density_mJy": m.flux_density_mJy,
                        "flux_uncertainty_mJy": m.flux_uncertainty_mJy,
                        "is_upper_limit": m.is_upper_limit,
                        "quality_flag": m.quality_flag,
                        "separation_arcsec": m.separation_arcsec,
                        "observation_epoch_mjd": m.observation_epoch_mjd,
                        "blending_flag": m.blending_flag,
                        "contamination_flag": m.contamination_flag,
                        "notes": m.notes
                    }
                    for bname, m in photometric_record.measurements.items()
                },
                "crossmatch_identifiers": {
                    "gaia_source_id": str(photometric_record.source_id),
                    "tmass_designation": photometric_record.tmass_designation,
                    "tmass_separation_arcsec": photometric_record.tmass_separation_arcsec,
                    "allwise_designation": photometric_record.allwise_designation,
                    "allwise_separation_arcsec": photometric_record.allwise_separation_arcsec,
                    "catwise_designation": getattr(photometric_record, "catwise_designation", None),
                    "catwise_separation_arcsec": getattr(photometric_record, "catwise_separation_arcsec", None),
                },
                "counterpart_ambiguity": bool(photometric_record.competing_counterparts_count > 1),
                "competing_counterparts_count": photometric_record.competing_counterparts_count,
                "is_spatially_isolated": photometric_record.is_spatially_isolated,
                "gaia_ruwe": photometric_record.gaia_ruwe,
                "gaia_astrometric_excess_noise": photometric_record.gaia_astrometric_excess_noise,
                "has_xp_continuous": photometric_record.has_xp_continuous
            }

            metadata = {
                "evidence_reason": ev_reason,
                "baseline_method": pred_w2.baseline_method,
                "w1_significance_sigma": res_w1.excess_significance_sigma,
                "w2_significance_sigma": res_w2.excess_significance_sigma,
                "spherex_overlap_channel_count": len(valid_spx),
                "spherex_overlap_mean_residual_mJy": spx_mean_res,
                "spherex_overlap_mean_significance_sigma": spx_mean_sig,
                "tmass_designation": photometric_record.tmass_designation,
                "allwise_designation": photometric_record.allwise_designation,
                "catwise_designation": getattr(photometric_record, "catwise_designation", None),
                "gaia_ruwe": photometric_record.gaia_ruwe,
                "blind_cohort_restriction_applied": (not is_cal_eligible),
                "candidate_excess_indication": candidate_indication,
                "multicatalog_infrared_evidence": multicatalog_evidence
            }

            return ContinuumEvidenceRecord(
                contract_version=SIDECAR_CONTRACT_VERSION,
                source_id=source_id_str,
                pointing_id=pointing_id_str,
                color_excess_detected=color_excess_detected,
                continuum_anomaly_score=primary_sig,
                color_indices=color_indices,
                power_law_spectral_index=None,
                excess_significance_sigma=primary_sig,
                quality_status=ev_state,
                provenance_reference=self.provenance_reference,
                evidence_state=ev_state,
                primary_band="WISE_W2",
                observed_flux_mJy=res_w2.observed_flux_mJy,
                predicted_flux_mJy=res_w2.predicted_photospheric_flux_mJy,
                residual_flux_mJy=res_w2.residual_flux_mJy,
                total_uncertainty_mJy=res_w2.total_uncertainty_mJy,
                flux_unit="mJy",
                is_upper_limit=res_w2.is_upper_limit,
                counterpart_ambiguity=bool(photometric_record.competing_counterparts_count > 1),
                validation_timestamp=now_utc,
                pipeline_build=self.pipeline_build,
                limitation_codes=limitation_codes,
                metadata=metadata
            )

        # 4. Fallback if no external catalog record supplied: evaluate SPHEREx continuum directly
        valid_indices = [i for i, v in enumerate(valid_mask) if v and fluxes[i] is not None]
        if len(valid_indices) < 3:
            limitation_codes.append("INSUFFICIENT_SPECTRAL_CHANNELS_FOR_CONTINUUM")
            return ContinuumEvidenceRecord(
                contract_version=SIDECAR_CONTRACT_VERSION,
                source_id=source_id_str,
                pointing_id=pointing_id_str,
                color_excess_detected=False,
                continuum_anomaly_score=None,
                color_indices={},
                power_law_spectral_index=None,
                excess_significance_sigma=None,
                quality_status="INSUFFICIENT_PHOTOMETRY",
                provenance_reference=self.provenance_reference,
                evidence_state="INSUFFICIENT_PHOTOMETRY",
                primary_band=None,
                observed_flux_mJy=None,
                predicted_flux_mJy=None,
                residual_flux_mJy=None,
                total_uncertainty_mJy=None,
                flux_unit="mJy",
                is_upper_limit=None,
                counterpart_ambiguity=False,
                validation_timestamp=now_utc,
                pipeline_build=self.pipeline_build,
                limitation_codes=limitation_codes,
                metadata={"reason": "External photometry not provided and fewer than 3 valid channels."}
            )

        # Compute empirical ratio between shortest and longest valid channels
        idx_min = min(valid_indices, key=lambda i: wavelengths[i])
        idx_max = max(valid_indices, key=lambda i: wavelengths[i])
        f_min = fluxes[idx_min]
        f_max = fluxes[idx_max]

        color_indices = {
            f"ratio_{wavelengths[idx_min]:.2f}um_{wavelengths[idx_max]:.2f}um": round(f_max / f_min, 3) if f_min and f_min > 0 else 1.0
        }

        fallback_state = "SUPPORTED_PHOTOSPHERIC_CONSISTENCY" if is_cal_eligible else "UNVERIFIABLE"
        return ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id=source_id_str,
            pointing_id=pointing_id_str,
            color_excess_detected=False,
            continuum_anomaly_score=None,
            color_indices=color_indices,
            power_law_spectral_index=None,
            excess_significance_sigma=None,
            quality_status=fallback_state,
            provenance_reference=self.provenance_reference,
            evidence_state=fallback_state,
            primary_band=None,
            observed_flux_mJy=None,
            predicted_flux_mJy=None,
            residual_flux_mJy=None,
            total_uncertainty_mJy=None,
            flux_unit="mJy",
            is_upper_limit=False,
            counterpart_ambiguity=False,
            validation_timestamp=now_utc,
            pipeline_build=self.pipeline_build,
            limitation_codes=limitation_codes,
            metadata={
                "note": "Evaluated using SPHEREx channel ratio alone (external photometry unattached).",
                "blind_cohort_restriction_applied": (not is_cal_eligible)
            }
        )


__all__ = [
    "EmpiricalContinuumSidecar"
]
