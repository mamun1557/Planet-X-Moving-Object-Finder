"""
Astronomical Coordinate Utilities & Spherical Geometry Engine
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline

Handles:
1. Coordinate validation (finite values, legal declination [-90, +90]).
2. Periodic normalization of Right Ascension into [0, 360).
3. RA wraparound across the 0°/360° celestial boundary.
4. Exact spherical angular separation using Haversine / Vincenty equations.
5. Astrometric position angle (bearing) on the celestial sphere.
6. WCS pixel-to-sky mapping with SIP distortion polynomial evaluation.
"""

import math
from typing import Tuple, Optional, Any


def validate_coordinates(ra_deg: Any, dec_deg: Any) -> Tuple[bool, str]:
    """
    Validates that RA and Dec are finite floating-point numbers
    and that Dec falls within legal spherical bounds [-90.0, +90.0].
    """
    if ra_deg is None or dec_deg is None:
        return False, "Coordinates cannot be None"

    try:
        ra = float(ra_deg)
        dec = float(dec_deg)
    except (ValueError, TypeError):
        return False, f"Non-numeric coordinates: ra={ra_deg!r}, dec={dec_deg!r}"

    if math.isnan(ra) or math.isinf(ra):
        return False, f"RA is non-finite: {ra}"
    if math.isnan(dec) or math.isinf(dec):
        return False, f"Dec is non-finite: {dec}"

    if not (-90.0 <= dec <= 90.0):
        return False, f"Declination out of physical bounds [-90.0, +90.0]: {dec}°"

    return True, "Valid"


def normalize_ra_deg(ra_deg: float) -> float:
    """Normalizes Right Ascension into the standard interval [0.0, 360.0)."""
    return float(ra_deg % 360.0)


def compute_ra_difference_deg(ra1_deg: float, ra2_deg: float) -> float:
    """
    Computes the shortest angular difference (ra2 - ra1) wrapped
    into the interval [-180.0, +180.0] degrees, resolving wraparound at 0°/360°.
    """
    diff = (ra2_deg - ra1_deg + 180.0) % 360.0 - 180.0
    return float(diff)


def spherical_angular_separation_arcsec(
    ra1_deg: float,
    dec1_deg: float,
    ra2_deg: float,
    dec2_deg: float
) -> float:
    """
    Computes exact spherical angular separation in arcseconds between two celestial
    coordinates using the Haversine formula with defensive numerical clamping.
    """
    r1, d1 = math.radians(ra1_deg), math.radians(dec1_deg)
    r2, d2 = math.radians(ra2_deg), math.radians(dec2_deg)

    # Use wrapped RA difference in radians
    d_ra = math.radians(compute_ra_difference_deg(ra1_deg, ra2_deg))
    d_dec = d2 - d1

    a = math.sin(d_dec / 2.0) ** 2 + math.cos(d1) * math.cos(d2) * math.sin(d_ra / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    dist_rad = 2.0 * math.asin(math.sqrt(a))

    return float(math.degrees(dist_rad) * 3600.0)


def position_angle_deg(
    ra1_deg: float,
    dec1_deg: float,
    ra2_deg: float,
    dec2_deg: float
) -> float:
    """
    Computes the position angle (bearing) from coordinate 1 to coordinate 2
    in degrees measured North through East [0.0, 360.0).
    """
    r1, d1 = math.radians(ra1_deg), math.radians(dec1_deg)
    r2, d2 = math.radians(ra2_deg), math.radians(dec2_deg)
    d_ra = r2 - r1

    y = math.sin(d_ra) * math.cos(d2)
    x = math.cos(d1) * math.sin(d2) - math.sin(d1) * math.cos(d2) * math.cos(d_ra)

    pa_rad = math.atan2(y, x)
    pa_deg = (math.degrees(pa_rad) + 360.0) % 360.0
    return float(pa_deg)


def pixel_to_sky_wcs(
    x_pixel: float,
    y_pixel: float,
    wcs_source: Any
) -> Tuple[Optional[float], Optional[float]]:
    """
    Converts 0-indexed detector pixel coordinates (x, y) into celestial RA/Dec (ICRS)
    using the provided WCS object (supporting SIP distortion polynomials).
    Returns (None, None) if WCS conversion fails.
    """
    if wcs_source is None:
        return None, None

    try:
        # Check if astropy WCS
        if hasattr(wcs_source, "all_pix2world"):
            sky = wcs_source.all_pix2world([[x_pixel, y_pixel]], 0)
            ra = normalize_ra_deg(float(sky[0][0]))
            dec = float(sky[0][1])
            is_valid, _ = validate_coordinates(ra, dec)
            if is_valid:
                return ra, dec
        elif hasattr(wcs_source, "pixel_to_world"):
            coord = wcs_source.pixel_to_world(x_pixel, y_pixel)
            ra = normalize_ra_deg(float(coord.ra.deg))
            dec = float(coord.dec.deg)
            is_valid, _ = validate_coordinates(ra, dec)
            if is_valid:
                return ra, dec
    except Exception:
        pass

    return None, None

