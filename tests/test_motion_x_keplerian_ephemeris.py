"""
SPECTRA-X / F1 — Phase 4, Task 4.20B
Comprehensive Unit & Scientific Validation Test Suite for MOTION-X Keplerian Ephemeris Engine

Mandatory Test Coverage:
 1. Circular orbit (e = 0).
 2. Low-eccentricity orbit (e = 0.0797).
 3. High but valid eccentricity (e = 0.85).
 4. Invalid eccentricity (e < 0 or e >= 1.0) fail-closed.
 5. Invalid orbital elements (a <= 0, NaN values) fail-closed.
 6. Epoch boundary (t = t_0, t >> t_0).
 7. Angular wraparound (RA across 0/360 degrees).
 8. Deterministic reproducibility across repeated calls.
 9. Missing-data fail-closed behavior (None inputs, NaN coordinates, empty catalog).
10. Ground-truth comparison against JPL Horizons Ceres reference coordinates.
11. Full integration with MotionXValidator.match_known_minor_planets().
"""

import math
import pytest
import numpy as np
from typing import Dict, Any

from models.motion_x.keplerian_ephemeris import (
    OrbitalElements,
    KeplerianPropagationResult,
    MinorPlanetMatch,
    KeplerianEphemerisEngine,
    J2000_EPOCH_MJD,
    OBLIQUITY_J2000_DEG
)
from models.motion_x.model import MotionXValidator


# ==============================================================================
# 1. Circular Orbit Test (e = 0.0)
# ==============================================================================
def test_circular_orbit():
    """Validates that for e=0, mean anomaly equals eccentric anomaly and distance equals a."""
    el = OrbitalElements(
        spkid=1001,
        name="CircularTest",
        a=2.5,
        e=0.0,
        i_deg=0.0,
        om_deg=0.0,
        w_deg=0.0,
        ma_deg=45.0,
        epoch_mjd=59000.0
    )
    res = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=59000.0)
    assert abs(res.heliocentric_distance_au - 2.5) < 1e-10
    assert abs(res.mean_anomaly_deg - 45.0) < 1e-10
    assert abs(res.true_anomaly_deg - 45.0) < 1e-10


# ==============================================================================
# 2. Low-Eccentricity Orbit Test (Ceres-like, e = 0.0797)
# ==============================================================================
def test_low_eccentricity_orbit():
    """Validates low-eccentricity orbit propagation and perihelion/aphelion distance bounds."""
    el = OrbitalElements(
        spkid=20000001,
        name="1 Ceres",
        a=2.766,
        e=0.0797,
        i_deg=10.59,
        om_deg=80.25,
        w_deg=73.29,
        ma_deg=0.0,  # Perihelion
        epoch_mjd=59000.0
    )
    # At perihelion (M=0), r should equal a*(1 - e)
    res_peri = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=59000.0)
    expected_peri = 2.766 * (1.0 - 0.0797)
    assert abs(res_peri.heliocentric_distance_au - expected_peri) < 1e-6
    assert abs(res_peri.true_anomaly_deg - 0.0) < 1e-6

    # Half an orbital period later, should be at aphelion: r = a*(1 + e)
    p_days = (2.766 ** 1.5) * 365.2568983
    res_aph = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=59000.0 + 0.5 * p_days)
    expected_aph = 2.766 * (1.0 + 0.0797)
    assert abs(res_aph.heliocentric_distance_au - expected_aph) < 0.01
    assert abs(res_aph.true_anomaly_deg - 180.0) < 0.5


# ==============================================================================
# 3. High-Eccentricity Orbit Test (e = 0.85)
# ==============================================================================
def test_high_eccentricity_orbit():
    """Validates that solver converges accurately for high-eccentricity Halley-like orbits."""
    el = OrbitalElements(
        spkid=99901,
        name="HighEccentricityObject",
        a=15.0,
        e=0.85,
        i_deg=45.0,
        om_deg=120.0,
        w_deg=60.0,
        ma_deg=90.0,
        epoch_mjd=55000.0
    )
    res = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=55100.0)
    assert 0.0 <= res.predicted_ra_deg < 360.0
    assert -90.0 <= res.predicted_dec_deg <= 90.0
    # r must lie between perihelion a*(1-e) = 2.25 and aphelion a*(1+e) = 27.75
    assert 2.25 <= res.heliocentric_distance_au <= 27.75


# ==============================================================================
# 4. Invalid Eccentricity Tests (e < 0 or e >= 1.0)
# ==============================================================================
def test_invalid_eccentricity_rejected():
    """Validates that parabolic, hyperbolic, and negative eccentricities are rejected fail-closed."""
    with pytest.raises(ValueError, match="Invalid eccentricity"):
        OrbitalElements(spkid=1, name="NegativeEcc", a=2.0, e=-0.05, i_deg=0, om_deg=0, w_deg=0, ma_deg=0)

    with pytest.raises(ValueError, match="Invalid eccentricity"):
        OrbitalElements(spkid=2, name="Parabolic", a=2.0, e=1.0, i_deg=0, om_deg=0, w_deg=0, ma_deg=0)

    with pytest.raises(ValueError, match="Invalid eccentricity"):
        OrbitalElements(spkid=3, name="Hyperbolic", a=2.0, e=1.25, i_deg=0, om_deg=0, w_deg=0, ma_deg=0)


# ==============================================================================
# 5. Invalid Orbital Elements (a <= 0, NaN values)
# ==============================================================================
def test_invalid_orbital_elements_rejected():
    """Validates fail-closed rejection of non-positive semi-major axis and NaN values."""
    with pytest.raises(ValueError, match="Invalid semi-major axis"):
        OrbitalElements(spkid=1, name="ZeroAxis", a=0.0, e=0.1, i_deg=0, om_deg=0, w_deg=0, ma_deg=0)

    with pytest.raises(ValueError, match="Invalid semi-major axis"):
        OrbitalElements(spkid=2, name="NegativeAxis", a=-2.5, e=0.1, i_deg=0, om_deg=0, w_deg=0, ma_deg=0)

    with pytest.raises(ValueError, match="Invalid semi-major axis"):
        OrbitalElements(spkid=3, name="NaNAxis", a=float("nan"), e=0.1, i_deg=0, om_deg=0, w_deg=0, ma_deg=0)

    with pytest.raises(ValueError, match="Invalid orbital angle"):
        OrbitalElements(spkid=4, name="NaNInclination", a=2.0, e=0.1, i_deg=float("nan"), om_deg=0, w_deg=0, ma_deg=0)


# ==============================================================================
# 6. Epoch Boundary Tests (t = t_0, t >> t_0)
# ==============================================================================
def test_epoch_boundary_behavior():
    """Validates behavior at exact epoch t=t_0 and for multi-decade propagation."""
    el = OrbitalElements(
        spkid=4,
        name="4 Vesta",
        a=2.361,
        e=0.0902,
        i_deg=7.14,
        om_deg=103.70,
        w_deg=151.47,
        ma_deg=81.19,
        epoch_mjd=51544.5
    )
    # At exact epoch, mean anomaly must match el.ma_deg
    res_t0 = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=51544.5)
    assert abs(res_t0.mean_anomaly_deg - 81.19) < 1e-10

    # 10,000 days later (~27 years)
    res_future = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=61544.5)
    assert 0.0 <= res_future.predicted_ra_deg < 360.0
    assert -90.0 <= res_future.predicted_dec_deg <= 90.0
    assert 2.361 * (1 - 0.0902) <= res_future.heliocentric_distance_au <= 2.361 * (1 + 0.0902)


# ==============================================================================
# 7. Angular Wraparound Tests
# ==============================================================================
def test_angular_wraparound():
    """Validates correct coordinate wrapping for RA across 0/360 degrees and distance calculation."""
    # Separation between RA=359.99 and RA=0.01 at Dec=0 should be 0.02 deg = 72 arcseconds
    sep1 = KeplerianEphemerisEngine.angular_separation_arcsec(359.99, 0.0, 0.01, 0.0)
    assert abs(sep1 - 72.0) < 0.1

    # Separation across the North Celestial Pole
    sep_pole = KeplerianEphemerisEngine.angular_separation_arcsec(0.0, 89.9, 180.0, 89.9)
    # Total distance is 0.2 deg = 720 arcseconds across the pole
    assert abs(sep_pole - 720.0) < 0.5


# ==============================================================================
# 8. Deterministic Reproducibility
# ==============================================================================
def test_deterministic_reproducibility():
    """Validates that identical inputs yield bit-for-bit identical coordinates."""
    el = OrbitalElements(
        spkid=99942,
        name="99942 Apophis",
        a=0.9224,
        e=0.1912,
        i_deg=3.331,
        om_deg=204.45,
        w_deg=126.40,
        ma_deg=230.12,
        epoch_mjd=59000.0,
        neo=True,
        pha=True
    )
    res1 = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=60000.0)
    res2 = KeplerianEphemerisEngine.propagate_orbit(el, observation_mjd=60000.0)

    assert res1.predicted_ra_deg == res2.predicted_ra_deg
    assert res1.predicted_dec_deg == res2.predicted_dec_deg
    assert res1.topocentric_distance_au == res2.topocentric_distance_au


# ==============================================================================
# 9. Missing-Data Fail-Closed Behavior
# ==============================================================================
def test_missing_data_fail_closed():
    """Validates that None coordinates, NaNs, and empty catalogs return None without crashing."""
    engine = KeplerianEphemerisEngine()  # Empty catalog

    assert engine.match_candidate(100.0, 20.0, 59000.0) is None
    assert engine.match_candidate(None, 20.0, 59000.0) is None
    assert engine.match_candidate(100.0, None, 59000.0) is None
    assert engine.match_candidate(100.0, 20.0, None) is None
    assert engine.match_candidate(float("nan"), 20.0, 59000.0) is None
    assert engine.match_candidate(100.0, float("nan"), 59000.0) is None
    assert engine.match_candidate(100.0, 20.0, float("nan")) is None
    assert engine.match_candidate(100.0, 95.0, 59000.0) is None  # Invalid Dec > 90


# ==============================================================================
# 10. JPL Horizons Ground-Truth Comparison (Ceres)
# ==============================================================================
def test_ceres_reference_ephemeris_accuracy():
    """
    Validates two-body propagation of Ceres against NASA/JPL Horizons osculating state.
    Osculating state: Epoch JD 2458849.5 (2020-Jan-01.0 TDB, MJD 58849.0).
    JPL DE441 equivalent ICRF heliocentric coordinates:
      X = 1.007609 AU, Y = -2.390064 AU, Z = -1.332125 AU
    """
    el_ceres = OrbitalElements(
        spkid=20000001,
        name="1 Ceres",
        a=2.769289,
        e=0.076875,
        i_deg=10.5913,
        om_deg=80.3012,
        w_deg=73.8090,
        ma_deg=130.3160,
        epoch_mjd=58849.0
    )
    res = KeplerianEphemerisEngine.propagate_orbit(el_ceres, observation_mjd=58849.0)

    # Heliocentric distance at this epoch in Horizons: sqrt(1.007609^2 + 2.390064^2 + 1.332125^2) = 2.91583 AU
    expected_r = math.sqrt(1.007609**2 + (-2.390064)**2 + (-1.332125)**2)
    assert abs(res.heliocentric_distance_au - expected_r) < 0.001


# ==============================================================================
# 11. Full Integration with MotionXValidator
# ==============================================================================
def test_motion_x_validator_integration():
    """Validates end-to-end integration with MotionXValidator.match_known_minor_planets()."""
    el_ceres = OrbitalElements(
        spkid=20000001,
        name="1 Ceres",
        a=2.769289,
        e=0.076875,
        i_deg=10.5913,
        om_deg=80.3012,
        w_deg=73.8090,
        ma_deg=130.3160,
        epoch_mjd=58849.0
    )
    engine = KeplerianEphemerisEngine()
    engine._catalog = [el_ceres]

    validator = MotionXValidator(ephemeris_engine=engine)

    # Predict Ceres coordinates at MJD 58849.0
    prop = engine.propagate_orbit(el_ceres, 58849.0)

    # Query with exact predicted coordinates -> should match with dist < 0.1 arcsec
    match = validator.match_known_minor_planets(
        ra_deg=prop.predicted_ra_deg,
        dec_deg=prop.predicted_dec_deg,
        mjd=58849.0,
        tolerance_arcsec=10.0
    )
    assert match is not None
    assert match["is_known_minor_planet"] is True
    assert match["name"] == "1 Ceres"
    assert match["dist_arcsec"] < 0.1
    assert "provenance" in match
    assert match["provenance"]["propagation_method"] == "KEPLERIAN_TWO_BODY_UNPERTURBED"

    # Query far away (> tolerance) -> should return None fail-closed
    no_match = validator.match_known_minor_planets(
        ra_deg=prop.predicted_ra_deg + 2.0,  # 2 degrees away
        dec_deg=prop.predicted_dec_deg,
        mjd=58849.0,
        tolerance_arcsec=10.0
    )
    assert no_match is None

