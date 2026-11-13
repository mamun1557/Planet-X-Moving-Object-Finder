"""
Photometric Catalog Normalization and Unit Conversion Layer.

Converts astronomical catalog magnitudes to physical monochromatic flux densities
(milliJanskys, mJy) with rigorous Gaussian error propagation and explicit upper-limit tracking.
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from spectra_engine.validation.infrared_excess.zero_points import PHOTOMETRIC_BANDS, BandMetadata


@dataclass
class NormalizedMeasurement:
    """Standardized photometric measurement in monochromatic flux density units."""
    band_name: str
    catalog_source: str
    effective_wavelength_microns: float
    magnitude: Optional[float]
    magnitude_error: Optional[float]
    flux_density_mJy: Optional[float]
    flux_uncertainty_mJy: Optional[float]
    is_upper_limit: bool
    quality_flag: str
    detection_snr: Optional[float] = None
    magnitude_system: str = "Vega"
    notes: str = ""
    # Enhancements for Task 4.20C Multi-Catalog Evidence Tracking
    separation_arcsec: Optional[float] = None
    observation_epoch_mjd: Optional[float] = None
    blending_flag: Optional[str] = None
    contamination_flag: Optional[str] = None


@dataclass
class NormalizedSourceRecord:
    """Normalized multi-band photometric record for a single astrophysical source."""
    source_id: int
    ra_deg: float
    dec_deg: float
    cohort_pointing: str
    measurements: Dict[str, NormalizedMeasurement] = field(default_factory=dict)
    tmass_designation: Optional[str] = None
    tmass_separation_arcsec: Optional[float] = None
    allwise_designation: Optional[str] = None
    allwise_separation_arcsec: Optional[float] = None
    catwise_designation: Optional[str] = None
    catwise_separation_arcsec: Optional[float] = None
    gaia_ruwe: Optional[float] = None
    gaia_astrometric_excess_noise: Optional[float] = None
    has_xp_continuous: bool = False
    is_spatially_isolated: bool = True
    competing_counterparts_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CatalogNormalizer:
    """Converts catalog magnitudes into normalized physical flux density measurements."""

    @staticmethod
    def magnitude_to_flux(
        magnitude: Optional[float],
        magnitude_error: Optional[float],
        band: BandMetadata,
        is_upper_limit: bool = False
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Converts a Vega magnitude to flux density in mJy using the Pogson relation:
            F_nu = F_0 * 10^(-0.4 * m)
        Propagates uncertainty using first-order Taylor expansion:
            sigma_F = (ln(10) / 2.5) * F_nu * sqrt(sigma_m^2 + sigma_zp^2)
        """
        if magnitude is None or math.isnan(magnitude):
            return None, None

        f_0 = band.zero_point_flux_mJy
        flux = f_0 * (10.0 ** (-0.4 * magnitude))

        if is_upper_limit:
            # For upper limits, uncertainty is undefined; flux represents 95% or 3-sigma bound
            return flux, None

        if magnitude_error is None or math.isnan(magnitude_error) or magnitude_error <= 0.0:
            # If no valid magnitude error, use zero-point uncertainty floor
            sigma_m_eff = band.zero_point_fractional_uncertainty / (math.log(10.0) / 2.5)
        else:
            # Combine photometric measurement error with zero-point calibration error in quadrature
            zp_frac = band.zero_point_fractional_uncertainty
            sigma_zp_mag = zp_frac / (math.log(10.0) / 2.5)
            sigma_m_eff = math.sqrt(magnitude_error ** 2 + sigma_zp_mag ** 2)

        flux_error = (math.log(10.0) / 2.5) * flux * sigma_m_eff
        return flux, flux_error

    @classmethod
    def normalize_measurement(
        cls,
        band_key: str,
        magnitude: Optional[float],
        magnitude_error: Optional[float],
        quality_flag: str,
        is_upper_limit: bool = False,
        snr: Optional[float] = None,
        notes: str = "",
        separation_arcsec: Optional[float] = None,
        observation_epoch_mjd: Optional[float] = None,
        blending_flag: Optional[str] = None,
        contamination_flag: Optional[str] = None
    ) -> NormalizedMeasurement:
        """Constructs a NormalizedMeasurement for a given passband."""
        if band_key not in PHOTOMETRIC_BANDS:
            raise KeyError(f"Passband '{band_key}' not defined in PHOTOMETRIC_BANDS.")

        band = PHOTOMETRIC_BANDS[band_key]
        flux, flux_err = cls.magnitude_to_flux(
            magnitude=magnitude,
            magnitude_error=magnitude_error,
            band=band,
            is_upper_limit=is_upper_limit
        )

        return NormalizedMeasurement(
            band_name=band.band_name,
            catalog_source=band.catalog_source,
            effective_wavelength_microns=band.effective_wavelength_microns,
            magnitude=magnitude,
            magnitude_error=magnitude_error,
            flux_density_mJy=flux,
            flux_uncertainty_mJy=flux_err,
            is_upper_limit=is_upper_limit,
            quality_flag=str(quality_flag),
            detection_snr=snr,
            magnitude_system=band.magnitude_system,
            notes=notes,
            separation_arcsec=separation_arcsec,
            observation_epoch_mjd=observation_epoch_mjd,
            blending_flag=blending_flag,
            contamination_flag=contamination_flag
        )

    @classmethod
    def from_multicatalog_dict(
        cls,
        data: Dict[str, Any],
        cohort_pointing: str = "P0008"
    ) -> NormalizedSourceRecord:
        """
        Parses multi-catalog infrared evidence from external catalog crossmatch records
        (Gaia DR3, 2MASS, ALLWISE, CatWISE2020) into a validated NormalizedSourceRecord.
        Preserves provenance, uncertainties, quality flags, upper-limits, and separations.
        """
        source_id = int(data.get("source_id", data.get("gaia_source_id", 0)))
        ra_deg = float(data.get("ra_deg", data.get("ra_gaia", data.get("ra", 0.0))))
        dec_deg = float(data.get("dec_deg", data.get("dec_gaia", data.get("dec", 0.0))))

        measurements: Dict[str, NormalizedMeasurement] = {}

        # 1. 2MASS Photometry
        has_2mass = data.get("has_2mass", True)
        tmass_desig = data.get("tmass_designation")
        tmass_sep = float(data.get("tmass_sep_arcsec", data.get("tmass_separation_arcsec", 0.0))) if data.get("tmass_sep_arcsec") or data.get("tmass_separation_arcsec") else None
        ph_qual = str(data.get("tmass_ph_qual", "AAA"))

        if has_2mass and tmass_desig != "NO_2MASS_MATCH":
            tmass_bands = [("2MASS_J", "tmass_j_m", "tmass_j_msigcom", 0),
                           ("2MASS_H", "tmass_h_m", "tmass_h_msigcom", 1),
                           ("2MASS_Ks", "tmass_k_m", "tmass_k_msigcom", 2)]
            for bname, mag_col, err_col, qidx in tmass_bands:
                mag_val = data.get(mag_col)
                if mag_val is not None and str(mag_val).strip() != "" and not (isinstance(mag_val, float) and math.isnan(mag_val)):
                    try:
                        mag = float(mag_val)
                        err_val = data.get(err_col)
                        mag_err = float(err_val) if err_val is not None and str(err_val).strip() != "" and not (isinstance(err_val, float) and math.isnan(err_val)) else 0.05
                        q_char = ph_qual[qidx] if len(ph_qual) > qidx else "A"
                        is_ul = (q_char in ["U", "D", "X"])
                        measurements[bname] = cls.normalize_measurement(
                            band_key=bname,
                            magnitude=mag,
                            magnitude_error=mag_err,
                            quality_flag=q_char,
                            is_upper_limit=is_ul,
                            separation_arcsec=tmass_sep,
                            notes=f"2MASS PSC {tmass_desig}"
                        )
                    except (ValueError, TypeError):
                        pass

        # 2. ALLWISE Photometry
        has_wise = data.get("has_allwise", True)
        wise_desig = data.get("allwise_designation")
        wise_sep = float(data.get("allwise_sep_arcsec", data.get("allwise_separation_arcsec", 0.0))) if data.get("allwise_sep_arcsec") or data.get("allwise_separation_arcsec") else None
        wise_cc = str(data.get("allwise_cc_flags", "0000"))
        wise_qual = str(data.get("allwise_ph_qual", "AAUU"))

        if has_wise and wise_desig != "NO_ALLWISE_MATCH":
            wise_bands = [("WISE_W1", "allwise_w1mpro", "allwise_w1sigmpro", 0),
                          ("WISE_W2", "allwise_w2mpro", "allwise_w2sigmpro", 1)]
            for bname, mag_col, err_col, qidx in wise_bands:
                mag_val = data.get(mag_col)
                if mag_val is not None and str(mag_val).strip() != "" and not (isinstance(mag_val, float) and math.isnan(mag_val)):
                    try:
                        mag = float(mag_val)
                        err_val = data.get(err_col)
                        mag_err = float(err_val) if err_val is not None and str(err_val).strip() != "" and not (isinstance(err_val, float) and math.isnan(err_val)) else 0.05
                        q_char = wise_qual[qidx] if len(wise_qual) > qidx else "A"
                        cc_char = wise_cc[qidx] if len(wise_cc) > qidx else "0"
                        is_ul = (q_char in ["U", "Z"])
                        measurements[bname] = cls.normalize_measurement(
                            band_key=bname,
                            magnitude=mag,
                            magnitude_error=mag_err,
                            quality_flag=q_char,
                            is_upper_limit=is_ul,
                            separation_arcsec=wise_sep,
                            contamination_flag=cc_char,
                            notes=f"ALLWISE {wise_desig}"
                        )
                    except (ValueError, TypeError):
                        pass

        # 3. CatWISE2020 Photometry (if provided)
        catwise_desig = data.get("catwise_designation")
        catwise_sep = float(data.get("catwise_sep_arcsec", data.get("catwise_separation_arcsec", 0.0))) if data.get("catwise_sep_arcsec") or data.get("catwise_separation_arcsec") else None
        for bname, mag_col, err_col in [("CatWISE_W1", "catwise_w1mpro", "catwise_w1sigmpro"),
                                        ("CatWISE_W2", "catwise_w2mpro", "catwise_w2sigmpro")]:
            mag_val = data.get(mag_col)
            if mag_val is not None and str(mag_val).strip() != "" and not (isinstance(mag_val, float) and math.isnan(mag_val)):
                try:
                    mag = float(mag_val)
                    err_val = data.get(err_col)
                    mag_err = float(err_val) if err_val is not None and str(err_val).strip() != "" and not (isinstance(err_val, float) and math.isnan(err_val)) else 0.05
                    measurements[bname] = cls.normalize_measurement(
                        band_key=bname,
                        magnitude=mag,
                        magnitude_error=mag_err,
                        quality_flag="A",
                        is_upper_limit=False,
                        separation_arcsec=catwise_sep,
                        notes=f"CatWISE2020 {catwise_desig}"
                    )
                except (ValueError, TypeError):
                    pass

        # 4. Gaia DR3 G-band (if provided)
        g_val = data.get("phot_g_mean_mag")
        if g_val is not None and str(g_val).strip() != "" and not (isinstance(g_val, float) and math.isnan(g_val)):
            try:
                mag = float(g_val)
                err_val = data.get("phot_g_mean_mag_error", 0.02)
                mag_err = float(err_val) if err_val is not None else 0.02
                measurements["Gaia_G"] = cls.normalize_measurement(
                    band_key="Gaia_G",
                    magnitude=mag,
                    magnitude_error=mag_err,
                    quality_flag="0",
                    is_upper_limit=False,
                    notes=f"Gaia DR3 {source_id}"
                )
            except (ValueError, TypeError):
                pass

        competing_count = int(data.get("competing_counterparts_count", 0))

        return NormalizedSourceRecord(
            source_id=source_id,
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            cohort_pointing=cohort_pointing,
            measurements=measurements,
            tmass_designation=tmass_desig,
            tmass_separation_arcsec=tmass_sep,
            allwise_designation=wise_desig,
            allwise_separation_arcsec=wise_sep,
            catwise_designation=catwise_desig,
            catwise_separation_arcsec=catwise_sep,
            gaia_ruwe=float(data["gaia_ruwe"]) if data.get("gaia_ruwe") is not None and not math.isnan(float(data.get("gaia_ruwe", 0))) else None,
            gaia_astrometric_excess_noise=float(data["gaia_astrometric_excess_noise"]) if data.get("gaia_astrometric_excess_noise") is not None and not math.isnan(float(data.get("gaia_astrometric_excess_noise", 0))) else None,
            has_xp_continuous=bool(data.get("has_xp_continuous", False)),
            is_spatially_isolated=bool(data.get("is_spatially_isolated", True)),
            competing_counterparts_count=competing_count,
            metadata={
                "crossmatch_acquisition_status": data.get("acquisition_status", "UNKNOWN"),
                "provenance_notes": data.get("photospheric_consistency_notes", "")
            }
        )

