"""
SPECTRA-X / Planet X Astronomical Motion Analysis Package
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline
"""

from .coordinates import (
    validate_coordinates,
    normalize_ra_deg,
    compute_ra_difference_deg,
    spherical_angular_separation_arcsec,
    position_angle_deg,
    pixel_to_sky_wcs
)
from .engine import (
    AstronomicalMotionEngine,
    ObservationEpoch,
    MotionAnalysisResult,
    MotionEligibilityStatus,
    MotionStatusCode
)

__all__ = [
    "validate_coordinates",
    "normalize_ra_deg",
    "compute_ra_difference_deg",
    "spherical_angular_separation_arcsec",
    "position_angle_deg",
    "pixel_to_sky_wcs",
    "AstronomicalMotionEngine",
    "ObservationEpoch",
    "MotionAnalysisResult",
    "MotionEligibilityStatus",
    "MotionStatusCode"
]

