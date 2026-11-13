"""
SPECTRA-X Model 4: MOTION-X
Celestial Object Movement & Asteroid Track Validation

Inputs:
- Detections from ASTROVISION / CHRONOS-X (RA, Dec, MJD)
- Gaia DR3 Astrometric Reference (proper motion pmRA, pmDec, parallax)
- JPL Horizons Ephemerides & JPL SBDB Asteroid Orbits

Purpose:
- Matches stationary stars with Gaia DR3 to eliminate stellar proper motion outliers.
- Matches transient motion tracks with known asteroids, comets, and NEOs from JPL Horizons / SBDB.
- Flags uncatalogued fast-moving objects (potential newly discovered asteroids or interstellar objects).
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

try:
    from .keplerian_ephemeris import KeplerianEphemerisEngine, OrbitalElements, MinorPlanetMatch
except ImportError:
    from models.motion_x.keplerian_ephemeris import KeplerianEphemerisEngine, OrbitalElements, MinorPlanetMatch


class MotionXValidator:
    def __init__(
        self,
        gaia_df: Optional[pd.DataFrame] = None,
        horizons_dict: Optional[Dict[str, pd.DataFrame]] = None,
        ephemeris_engine: Optional[KeplerianEphemerisEngine] = None,
        sbdb_path: Optional[str] = "data/external/minor_planets/jpl_sbdb_asteroid_orbits.json"
    ):
        self.gaia_df = gaia_df
        self.horizons_dict = horizons_dict or {}
        if ephemeris_engine is not None:
            self.ephemeris_engine = ephemeris_engine
        elif sbdb_path and os.path.exists(sbdb_path):
            self.ephemeris_engine = KeplerianEphemerisEngine(catalog_path=sbdb_path)
        else:
            self.ephemeris_engine = KeplerianEphemerisEngine()

    def crossmatch_gaia(self, ra_deg: float, dec_deg: float, match_radius_arcsec: float = 2.0) -> Optional[Dict[str, Any]]:
        """Matches a detection against Gaia DR3 astrometric reference stars."""
        if self.gaia_df is None or self.gaia_df.empty:
            return None

        ra_vals = self.gaia_df["ra"].values
        dec_vals = self.gaia_df["dec"].values
        cos_dec = np.cos(np.deg2rad(dec_deg))

        dra = (ra_vals - ra_deg) * cos_dec * 3600.0
        ddec = (dec_vals - dec_deg) * 3600.0
        dist_arcsec = np.sqrt(dra**2 + ddec**2)

        min_idx = np.argmin(dist_arcsec)
        if dist_arcsec[min_idx] <= match_radius_arcsec:
            match = self.gaia_df.iloc[min_idx]
            return {
                "source_id": match.get("source_id"),
                "dist_arcsec": float(dist_arcsec[min_idx]),
                "phot_g_mean_mag": match.get("phot_g_mean_mag"),
                "pmra": match.get("pmra"),
                "pmdec": match.get("pmdec"),
                "is_known_star": True
            }
        return None

    def match_known_minor_planets(self, ra_deg: float, dec_deg: float, mjd: float, tolerance_arcsec: float = 60.0) -> Optional[Dict[str, Any]]:
        """
        Cross-matches candidate coordinates with known minor planets using
        two-body Keplerian propagation at the requested observation epoch.
        Fails closed and returns None if no match is within tolerance or inputs are missing/invalid.
        """
        if self.ephemeris_engine is None or self.ephemeris_engine.catalog_size == 0:
            return None

        match = self.ephemeris_engine.match_candidate(
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            mjd_obs=mjd,
            tolerance_arcsec=tolerance_arcsec
        )
        if match is not None:
            return {
                "spkid": match.spkid,
                "name": match.name,
                "dist_arcsec": match.angular_separation_arcsec,
                "predicted_ra": match.predicted_ra_deg,
                "predicted_dec": match.predicted_dec_deg,
                "observed_ra": match.observed_ra_deg,
                "observed_dec": match.observed_dec_deg,
                "observation_mjd": match.observation_mjd,
                "topocentric_dist_au": match.topocentric_distance_au,
                "is_neo": match.is_neo,
                "is_pha": match.is_pha,
                "is_known_minor_planet": True,
                "provenance": match.provenance
            }
        return None
