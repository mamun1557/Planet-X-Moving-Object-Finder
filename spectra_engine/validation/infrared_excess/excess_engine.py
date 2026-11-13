"""
Empirical Infrared Excess Significance Engine.

Calculates signed photometric flux residuals, uncertainty budgets, and statistical
excess significance (S_excess) in standard deviations relative to the stellar photospheric baseline.
"""

import math
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from spectra_engine.validation.infrared_excess.catalog_normalizer import NormalizedSourceRecord, NormalizedMeasurement
from spectra_engine.validation.infrared_excess.photospheric_model import PhotosphericBaselineEstimator, PhotosphericPrediction


@dataclass
class ExcessBandResult:
    """Calculated excess significance metrics for a single passband."""
    band_name: str
    effective_wavelength_microns: float
    observed_flux_mJy: Optional[float]
    observed_flux_uncertainty_mJy: Optional[float]
    predicted_photospheric_flux_mJy: Optional[float]
    predicted_flux_uncertainty_mJy: Optional[float]
    residual_flux_mJy: Optional[float]
    total_uncertainty_mJy: Optional[float]
    excess_significance_sigma: Optional[float]
    flux_ratio_obs_to_phot: Optional[float]
    is_upper_limit: bool
    is_evaluable: bool
    status_reason: str


@dataclass
class SPHERExOverlapResult:
    """Comparison of SPHEREx 102-channel extraction with photospheric baseline."""
    channel_index: int
    wavelength_microns: float
    spherex_flux_mJy: Optional[float]
    spherex_uncertainty_mJy: Optional[float]
    predicted_photospheric_flux_mJy: Optional[float]
    residual_flux_mJy: Optional[float]
    significance_sigma: Optional[float]
    is_valid_channel: bool


@dataclass
class SourceExcessEvaluation:
    """Master infrared excess evaluation for an individual source."""
    source_id: int
    cohort_pointing: str
    band_results: Dict[str, ExcessBandResult]
    spherex_results: List[SPHERExOverlapResult]
    primary_excess_significance: Optional[float]
    primary_excess_band: str
    has_statistically_significant_excess: bool
    evidence_state: str
    diagnostic_summary: str


class InfraredExcessEngine:
    """
    Computes statistical infrared excess significance S_excess:
        Delta F = F_obs - F_phot
        sigma_tot = sqrt( sigma_obs^2 + sigma_phot^2 + sigma_sys^2 )
        S_excess = Delta F / sigma_tot
    """

    # Systematic calibration covariance floor (1.5%)
    SYSTEMATIC_COVARIANCE_FLOOR_FRAC: float = 0.015

    # Provisional significance threshold for candidate infrared excess (3.0 sigma)
    EXCESS_SIGMA_THRESHOLD: float = 3.0

    @classmethod
    def evaluate_band_excess(
        cls,
        band_key: str,
        record: NormalizedSourceRecord,
        prediction: PhotosphericPrediction
    ) -> ExcessBandResult:
        """Evaluates residual and statistical significance for a specific passband."""
        if band_key not in record.measurements:
            return ExcessBandResult(
                band_name=band_key,
                effective_wavelength_microns=prediction.effective_wavelength_microns,
                observed_flux_mJy=None,
                observed_flux_uncertainty_mJy=None,
                predicted_photospheric_flux_mJy=prediction.predicted_flux_mJy if prediction.is_valid else None,
                predicted_flux_uncertainty_mJy=prediction.predicted_flux_uncertainty_mJy if prediction.is_valid else None,
                residual_flux_mJy=None,
                total_uncertainty_mJy=None,
                excess_significance_sigma=None,
                flux_ratio_obs_to_phot=None,
                is_upper_limit=False,
                is_evaluable=False,
                status_reason=f"Band {band_key} not observed in catalog data."
            )

        meas = record.measurements[band_key]

        if not prediction.is_valid:
            return ExcessBandResult(
                band_name=meas.band_name,
                effective_wavelength_microns=meas.effective_wavelength_microns,
                observed_flux_mJy=meas.flux_density_mJy,
                observed_flux_uncertainty_mJy=meas.flux_uncertainty_mJy,
                predicted_photospheric_flux_mJy=None,
                predicted_flux_uncertainty_mJy=None,
                residual_flux_mJy=None,
                total_uncertainty_mJy=None,
                excess_significance_sigma=None,
                flux_ratio_obs_to_phot=None,
                is_upper_limit=meas.is_upper_limit,
                is_evaluable=False,
                status_reason=f"Photospheric baseline invalid: {prediction.status_reason}"
            )

        if meas.is_upper_limit or meas.flux_density_mJy is None:
            # Upper limit constraint evaluation
            f_lim = meas.flux_density_mJy
            f_phot = prediction.predicted_flux_mJy
            ratio = (f_lim / f_phot) if (f_lim is not None and f_phot > 0) else None
            return ExcessBandResult(
                band_name=meas.band_name,
                effective_wavelength_microns=meas.effective_wavelength_microns,
                observed_flux_mJy=f_lim,
                observed_flux_uncertainty_mJy=None,
                predicted_photospheric_flux_mJy=f_phot,
                predicted_flux_uncertainty_mJy=prediction.predicted_flux_uncertainty_mJy,
                residual_flux_mJy=(f_lim - f_phot) if f_lim is not None else None,
                total_uncertainty_mJy=None,
                excess_significance_sigma=None,
                flux_ratio_obs_to_phot=ratio,
                is_upper_limit=True,
                is_evaluable=False,
                status_reason=f"Observed flux is an upper limit ({meas.quality_flag}); upper limit flux ratio = {ratio:.2f}." if ratio else "Upper limit."
            )

        f_obs = meas.flux_density_mJy
        sig_obs = meas.flux_uncertainty_mJy or (0.05 * f_obs)
        f_phot = prediction.predicted_flux_mJy
        sig_phot = prediction.predicted_flux_uncertainty_mJy

        delta_f = f_obs - f_phot
        sig_sys = cls.SYSTEMATIC_COVARIANCE_FLOOR_FRAC * f_obs
        sig_tot = math.sqrt(sig_obs ** 2 + sig_phot ** 2 + sig_sys ** 2)

        s_excess = delta_f / sig_tot if sig_tot > 0 else 0.0
        flux_ratio = f_obs / f_phot if f_phot > 0 else None

        return ExcessBandResult(
            band_name=meas.band_name,
            effective_wavelength_microns=meas.effective_wavelength_microns,
            observed_flux_mJy=round(f_obs, 4),
            observed_flux_uncertainty_mJy=round(sig_obs, 4),
            predicted_photospheric_flux_mJy=round(f_phot, 4),
            predicted_flux_uncertainty_mJy=round(sig_phot, 4),
            residual_flux_mJy=round(delta_f, 4),
            total_uncertainty_mJy=round(sig_tot, 4),
            excess_significance_sigma=round(s_excess, 2),
            flux_ratio_obs_to_phot=round(flux_ratio, 3) if flux_ratio else None,
            is_upper_limit=False,
            is_evaluable=True,
            status_reason="VALID_DETECTION_EVALUATED"
        )

    @classmethod
    def evaluate_spherex_overlap(
        cls,
        spherex_channels: List[Dict[str, Any]],
        prediction_w2: PhotosphericPrediction
    ) -> List[SPHERExOverlapResult]:
        """
        Compares SPHEREx extracted channel fluxes near Band 6 (4.4 - 4.6 um)
        with the predicted photospheric baseline.
        """
        results = []
        if not prediction_w2.is_valid:
            return results

        f_phot_w2 = prediction_w2.predicted_flux_mJy
        sig_phot_w2 = prediction_w2.predicted_flux_uncertainty_mJy

        for idx, ch in enumerate(spherex_channels):
            wl = ch.get("wavelength_microns", 0.0)
            flux = ch.get("flux_mJy")
            unc = ch.get("uncertainty_mJy")
            is_valid = ch.get("is_valid", False)

            # Compare channels overlapping WISE W2 (4.3 to 4.7 um)
            if 4.3 <= wl <= 4.7:
                if is_valid and flux is not None and unc is not None and unc > 0:
                    # Scale photospheric flux by Rayleigh-Jeans lambda^-2 from 4.60 um
                    scale = (4.6028 / wl) ** 2
                    f_phot_ch = f_phot_w2 * scale
                    sig_phot_ch = sig_phot_w2 * scale

                    delta = flux - f_phot_ch
                    sig_tot = math.sqrt(unc ** 2 + sig_phot_ch ** 2)
                    s_ch = delta / sig_tot if sig_tot > 0 else 0.0

                    results.append(SPHERExOverlapResult(
                        channel_index=idx,
                        wavelength_microns=round(wl, 4),
                        spherex_flux_mJy=round(flux, 4),
                        spherex_uncertainty_mJy=round(unc, 4),
                        predicted_photospheric_flux_mJy=round(f_phot_ch, 4),
                        residual_flux_mJy=round(delta, 4),
                        significance_sigma=round(s_ch, 2),
                        is_valid_channel=True
                    ))
                else:
                    results.append(SPHERExOverlapResult(
                        channel_index=idx,
                        wavelength_microns=round(wl, 4),
                        spherex_flux_mJy=flux,
                        spherex_uncertainty_mJy=unc,
                        predicted_photospheric_flux_mJy=round(f_phot_w2, 4),
                        residual_flux_mJy=None,
                        significance_sigma=None,
                        is_valid_channel=False
                    ))
        return results

