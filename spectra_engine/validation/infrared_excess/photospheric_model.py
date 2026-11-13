"""
Empirical and Color-Dependent Stellar Photospheric Baseline Engine.

Estimates the un-reddened and un-attenuated stellar photospheric continuum in mid-infrared
passbands (WISE W1 3.35 um and W2 4.60 um) anchored by near-infrared 2MASS Ks photometry
and modulated by optical/NIR colors (Gaia BP-RP and 2MASS J-Ks).

References:
- Pecaut, M. J., & Mamajek, E. E. 2013, ApJS, 208, 9 (Intrinsic Colors of Stars)
- Davenport, J. R. A., et al. 2014, ApJ, 788, 48 (WISE colors of Kepler stars)
- The Rayleigh-Jeans approximation (F_nu ~ lambda^-2) in the thermal infrared for T_eff > 3000 K.
"""

import math
from dataclasses import dataclass
from typing import Optional, Dict, Any

from spectra_engine.validation.infrared_excess.zero_points import PHOTOMETRIC_BANDS
from spectra_engine.validation.infrared_excess.catalog_normalizer import NormalizedSourceRecord, NormalizedMeasurement


@dataclass
class PhotosphericPrediction:
    """Predicted stellar photospheric flux density in a target passband."""
    target_band: str
    effective_wavelength_microns: float
    predicted_flux_mJy: float
    predicted_flux_uncertainty_mJy: float
    predicted_magnitude: float
    anchor_band: str
    anchor_flux_mJy: float
    color_correction_mag: float
    color_uncertainty_mag: float
    baseline_method: str
    is_valid: bool
    status_reason: str


class PhotosphericBaselineEstimator:
    """
    Computes empirical stellar photospheric predictions for infrared passbands.
    Anchors the baseline at 2MASS Ks (2.16 um) where circumstellar dust emission is negligible
    compared to the stellar photosphere for typical debris and protoplanetary systems.
    """

    # Intrinsic color dispersion in bare stellar photospheres (Pecaut & Mamajek 2013)
    INTRINSIC_COLOR_DISPERSION_MAG: float = 0.040

    @classmethod
    def estimate_intrinsic_ks_wise_color(
        cls,
        bp_rp: Optional[float] = None,
        j_ks: Optional[float] = None
    ) -> tuple[float, float, str]:
        """
        Estimates the intrinsic (Ks - W1) and (Ks - W2) stellar colors based on
        optical (Gaia BP - RP) or near-IR (2MASS J - Ks) color index.

        For hot to solar-type stars (BP - RP < 1.5, J - Ks < 0.6), photospheres strictly follow
        Rayleigh-Jeans: (Ks - W1)_0 ~ 0.00, (Ks - W2)_0 ~ 0.00.
        For cool M-dwarfs / M-giants (BP - RP > 2.0, J - Ks > 0.8), molecular bands (CO, H2O)
        cause slight color shifts: (Ks - W1)_0 ~ +0.03 to +0.05, (Ks - W2)_0 ~ +0.05 to +0.08.
        """
        if bp_rp is not None and not math.isnan(bp_rp):
            if bp_rp <= 1.2:
                # O through G dwarf/giant
                return 0.00, 0.00, "EMPIRICAL_GAIA_EARLY_STELLAR_SEQUENCE"
            elif bp_rp <= 2.2:
                # K dwarf / giant
                delta_w1 = 0.02 * (bp_rp - 1.2)
                delta_w2 = 0.03 * (bp_rp - 1.2)
                return round(delta_w1, 3), round(delta_w2, 3), "EMPIRICAL_GAIA_MID_STELLAR_SEQUENCE"
            else:
                # Early to mid M-dwarf / giant
                return 0.04, 0.06, "EMPIRICAL_GAIA_COOL_STELLAR_SEQUENCE"
        elif j_ks is not None and not math.isnan(j_ks):
            if j_ks <= 0.6:
                return 0.00, 0.00, "EMPIRICAL_2MASS_EARLY_STELLAR_SEQUENCE"
            elif j_ks <= 0.9:
                return 0.02, 0.03, "EMPIRICAL_2MASS_MID_STELLAR_SEQUENCE"
            else:
                return 0.04, 0.06, "EMPIRICAL_2MASS_COOL_STELLAR_SEQUENCE"
        else:
            # Default bare stellar Rayleigh-Jeans baseline
            return 0.00, 0.00, "RAYLEIGH_JEANS_ZERO_COLOR_DEFAULT"

    @classmethod
    def predict_photospheric_flux(
        cls,
        target_band_key: str,
        record: NormalizedSourceRecord,
        anchor_band_key: str = "2MASS_Ks"
    ) -> PhotosphericPrediction:
        """
        Predicts the photospheric flux in target_band_key (e.g. WISE_W1, WISE_W2)
        anchored by 2MASS_Ks.
        """
        if target_band_key not in PHOTOMETRIC_BANDS:
            raise KeyError(f"Unknown target passband: {target_band_key}")
        if anchor_band_key not in PHOTOMETRIC_BANDS:
            raise KeyError(f"Unknown anchor passband: {anchor_band_key}")

        target_band = PHOTOMETRIC_BANDS[target_band_key]
        anchor_band = PHOTOMETRIC_BANDS[anchor_band_key]

        # Check if anchor measurement exists and is valid
        if anchor_band_key not in record.measurements:
            return PhotosphericPrediction(
                target_band=target_band.band_name,
                effective_wavelength_microns=target_band.effective_wavelength_microns,
                predicted_flux_mJy=0.0,
                predicted_flux_uncertainty_mJy=0.0,
                predicted_magnitude=0.0,
                anchor_band=anchor_band.band_name,
                anchor_flux_mJy=0.0,
                color_correction_mag=0.0,
                color_uncertainty_mag=0.0,
                baseline_method="NO_ANCHOR_AVAILABLE",
                is_valid=False,
                status_reason=f"Anchor band {anchor_band_key} missing from source measurements."
            )

        anchor_meas = record.measurements[anchor_band_key]
        if anchor_meas.is_upper_limit or anchor_meas.flux_density_mJy is None:
            return PhotosphericPrediction(
                target_band=target_band.band_name,
                effective_wavelength_microns=target_band.effective_wavelength_microns,
                predicted_flux_mJy=0.0,
                predicted_flux_uncertainty_mJy=0.0,
                predicted_magnitude=0.0,
                anchor_band=anchor_band.band_name,
                anchor_flux_mJy=anchor_meas.flux_density_mJy or 0.0,
                color_correction_mag=0.0,
                color_uncertainty_mag=0.0,
                baseline_method="UPPER_LIMIT_ANCHOR",
                is_valid=False,
                status_reason=f"Anchor band {anchor_band_key} is an upper limit ({anchor_meas.quality_flag}); cannot anchor detection baseline."
            )

        # Retrieve color constraints from record
        bp_rp = None
        if "Gaia_BP" in record.measurements and "Gaia_RP" in record.measurements:
            bp_m = record.measurements["Gaia_BP"].magnitude
            rp_m = record.measurements["Gaia_RP"].magnitude
            if bp_m is not None and rp_m is not None:
                bp_rp = bp_m - rp_m

        j_ks = None
        if "2MASS_J" in record.measurements and "2MASS_Ks" in record.measurements:
            j_m = record.measurements["2MASS_J"].magnitude
            ks_m = record.measurements["2MASS_Ks"].magnitude
            if j_m is not None and ks_m is not None:
                j_ks = j_m - ks_m

        color_w1, color_w2, method = cls.estimate_intrinsic_ks_wise_color(bp_rp, j_ks)
        color_offset = color_w1 if "W1" in target_band_key else color_w2

        # Predicted magnitude: m_target = m_anchor - (m_anchor - m_target)_phot
        # For instance: W1_phot = Ks - (Ks - W1)_0
        anchor_mag = anchor_meas.magnitude
        predicted_mag = anchor_mag - color_offset

        # Convert predicted magnitude to flux density
        f_0 = target_band.zero_point_flux_mJy
        predicted_flux = f_0 * (10.0 ** (-0.4 * predicted_mag))

        # Error propagation:
        # sigma_pred = sqrt( (pred_flux/anchor_flux * sigma_anchor_flux)^2 + (ln(10)/2.5 * pred_flux * sigma_color)^2 )
        anchor_flux = anchor_meas.flux_density_mJy
        anchor_flux_err = anchor_meas.flux_uncertainty_mJy or (0.05 * anchor_flux)

        term_anchor = (predicted_flux / anchor_flux) * anchor_flux_err
        term_color = (math.log(10.0) / 2.5) * predicted_flux * cls.INTRINSIC_COLOR_DISPERSION_MAG
        total_pred_flux_err = math.sqrt(term_anchor ** 2 + term_color ** 2)

        return PhotosphericPrediction(
            target_band=target_band.band_name,
            effective_wavelength_microns=target_band.effective_wavelength_microns,
            predicted_flux_mJy=round(predicted_flux, 4),
            predicted_flux_uncertainty_mJy=round(total_pred_flux_err, 4),
            predicted_magnitude=round(predicted_mag, 4),
            anchor_band=anchor_band.band_name,
            anchor_flux_mJy=round(anchor_flux, 4),
            color_correction_mag=color_offset,
            color_uncertainty_mag=cls.INTRINSIC_COLOR_DISPERSION_MAG,
            baseline_method=method,
            is_valid=True,
            status_reason="VALID_PHOTOSPHERIC_BASELINE"
        )

