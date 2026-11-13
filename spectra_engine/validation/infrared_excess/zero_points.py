"""
Authoritative Astronomical Photometric Zero Points and Filter Metadata.

Governs conversion between catalog magnitudes and physical monochromatic flux densities
(in milliJanskys, mJy) for Gaia DR3, 2MASS, and ALLWISE.

References:
- Cohen, M., Wheaton, W. A., & Megeath, S. T. 2003, AJ, 126, 1090 (2MASS absolute calibration)
- Jarrett, T. H., Cohen, M., Masci, F., et al. 2011, ApJ, 735, 112 (WISE calibration)
- Wright, E. L., Eisenhardt, P. R. M., Mainzer, A. K., et al. 2010, AJ, 140, 1868 (WISE mission)
- Carrasco, J. M., Weiler, M., Jordi, C., et al. 2021, A&A, 652, A86 (Gaia EDR3/DR3 passbands)
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class BandMetadata:
    """Photometric passband specification."""
    band_name: str
    catalog_source: str
    effective_wavelength_microns: float
    zero_point_flux_mJy: float
    zero_point_fractional_uncertainty: float
    magnitude_system: str
    reference: str


PHOTOMETRIC_BANDS: Dict[str, BandMetadata] = {
    # 2MASS Passbands (Cohen et al. 2003)
    "2MASS_J": BandMetadata(
        band_name="2MASS_J",
        catalog_source="2MASS",
        effective_wavelength_microns=1.235,
        zero_point_flux_mJy=1594000.0,  # 1594 Jy
        zero_point_fractional_uncertainty=0.017,  # 1.7%
        magnitude_system="Vega",
        reference="Cohen et al. (2003), AJ, 126, 1090"
    ),
    "2MASS_H": BandMetadata(
        band_name="2MASS_H",
        catalog_source="2MASS",
        effective_wavelength_microns=1.662,
        zero_point_flux_mJy=1024000.0,  # 1024 Jy
        zero_point_fractional_uncertainty=0.019,  # 1.9%
        magnitude_system="Vega",
        reference="Cohen et al. (2003), AJ, 126, 1090"
    ),
    "2MASS_Ks": BandMetadata(
        band_name="2MASS_Ks",
        catalog_source="2MASS",
        effective_wavelength_microns=2.159,
        zero_point_flux_mJy=666700.0,  # 666.7 Jy
        zero_point_fractional_uncertainty=0.019,  # 1.9%
        magnitude_system="Vega",
        reference="Cohen et al. (2003), AJ, 126, 1090"
    ),

    # ALLWISE Passbands (Jarrett et al. 2011; Wright et al. 2010)
    "WISE_W1": BandMetadata(
        band_name="WISE_W1",
        catalog_source="ALLWISE",
        effective_wavelength_microns=3.3526,
        zero_point_flux_mJy=309540.0,  # 309.54 Jy
        zero_point_fractional_uncertainty=0.015,  # 1.5%
        magnitude_system="Vega",
        reference="Jarrett et al. (2011), ApJ, 735, 112"
    ),
    "WISE_W2": BandMetadata(
        band_name="WISE_W2",
        catalog_source="ALLWISE",
        effective_wavelength_microns=4.6028,
        zero_point_flux_mJy=171787.0,  # 171.787 Jy
        zero_point_fractional_uncertainty=0.015,  # 1.5%
        magnitude_system="Vega",
        reference="Jarrett et al. (2011), ApJ, 735, 112"
    ),
    # CatWISE2020 Passbands (Eisenhardt et al. 2020; Marocco et al. 2021)
    "CatWISE_W1": BandMetadata(
        band_name="CatWISE_W1",
        catalog_source="CatWISE2020",
        effective_wavelength_microns=3.3526,
        zero_point_flux_mJy=309540.0,  # 309.54 Jy
        zero_point_fractional_uncertainty=0.015,  # 1.5%
        magnitude_system="Vega",
        reference="Marocco et al. (2021), ApJS, 253, 8"
    ),
    "CatWISE_W2": BandMetadata(
        band_name="CatWISE_W2",
        catalog_source="CatWISE2020",
        effective_wavelength_microns=4.6028,
        zero_point_flux_mJy=171787.0,  # 171.787 Jy
        zero_point_fractional_uncertainty=0.015,  # 1.5%
        magnitude_system="Vega",
        reference="Marocco et al. (2021), ApJS, 253, 8"
    ),
    "WISE_W3": BandMetadata(
        band_name="WISE_W3",
        catalog_source="ALLWISE",
        effective_wavelength_microns=11.5608,
        zero_point_flux_mJy=31674.0,  # 31.674 Jy
        zero_point_fractional_uncertainty=0.020,  # 2.0%
        magnitude_system="Vega",
        reference="Jarrett et al. (2011), ApJ, 735, 112"
    ),
    "WISE_W4": BandMetadata(
        band_name="WISE_W4",
        catalog_source="ALLWISE",
        effective_wavelength_microns=22.0883,
        zero_point_flux_mJy=8363.0,  # 8.363 Jy
        zero_point_fractional_uncertainty=0.030,  # 3.0%
        magnitude_system="Vega",
        reference="Jarrett et al. (2011), ApJ, 735, 112"
    ),

    # Gaia DR3 Broadband Passbands (Carrasco et al. 2021)
    "Gaia_G": BandMetadata(
        band_name="Gaia_G",
        catalog_source="Gaia_DR3",
        effective_wavelength_microns=0.673,
        zero_point_flux_mJy=3228750.0,  # 3228.75 Jy
        zero_point_fractional_uncertainty=0.010,
        magnitude_system="Vega",
        reference="Carrasco et al. (2021), A&A, 652, A86"
    ),
    "Gaia_BP": BandMetadata(
        band_name="Gaia_BP",
        catalog_source="Gaia_DR3",
        effective_wavelength_microns=0.532,
        zero_point_flux_mJy=3552010.0,  # 3552.01 Jy
        zero_point_fractional_uncertainty=0.010,
        magnitude_system="Vega",
        reference="Carrasco et al. (2021), A&A, 652, A86"
    ),
    "Gaia_RP": BandMetadata(
        band_name="Gaia_RP",
        catalog_source="Gaia_DR3",
        effective_wavelength_microns=0.797,
        zero_point_flux_mJy=2554950.0,  # 2554.95 Jy
        zero_point_fractional_uncertainty=0.010,
        magnitude_system="Vega",
        reference="Carrasco et al. (2021), A&A, 652, A86"
    ),
}

