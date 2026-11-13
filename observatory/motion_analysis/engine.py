"""
Astronomical Motion Analysis Engine
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline

Computes:
1. Exact spherical displacement between two observation epochs (arcsec).
2. Temporal separation baseline in hours and days.
3. Astrometric motion rates (arcsec/hour, arcsec/day).
4. Directional displacement (Position Angle in degrees North through East).
5. Formal coordinate uncertainty propagation: sigma_delta_theta = sqrt(sigma_1^2 + sigma_2^2).
6. Strict temporal eligibility safeguard:
   - dt < 1.0 day: INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY
   - dt >= 1.0 day: TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION
7. Fail-closed verification for missing coordinates, invalid timestamps, or missing WCS.
"""

import math
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union

from .coordinates import (
    validate_coordinates,
    normalize_ra_deg,
    compute_ra_difference_deg,
    spherical_angular_separation_arcsec,
    position_angle_deg
)


class MotionStatusCode(str, Enum):
    SUCCESS = "SUCCESS"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    MISSING_WCS = "MISSING_WCS"
    INSUFFICIENT_OBSERVATIONS = "INSUFFICIENT_OBSERVATIONS"
    UNCERTAINTY_UNAVAILABLE = "UNCERTAINTY_UNAVAILABLE"


class MotionEligibilityStatus(str, Enum):
    INTRA_VISIT_DITHER = "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY"
    TEMPORALLY_ELIGIBLE = "TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION"
    INELIGIBLE_MISSING_DATA = "INELIGIBLE_MISSING_DATA"


@dataclass
class ObservationEpoch:
    """Represents a single observation epoch of an astronomical target."""
    obs_id: str
    ra_deg: float
    dec_deg: float
    timestamp: Union[str, float]  # ISO 8601 UTC string or float MJD
    wcs_valid: bool = True
    sigma_coord_arcsec: float = 0.05
    mjd: Optional[float] = None


@dataclass
class MotionAnalysisResult:
    """Standardized response contract for astronomical motion analysis."""
    status: str
    is_valid: bool
    obs_a: Optional[Dict[str, Any]]
    obs_b: Optional[Dict[str, Any]]
    angular_displacement_arcsec: Optional[float]
    position_angle_deg: Optional[float]
    time_baseline_hours: Optional[float]
    time_baseline_days: Optional[float]
    motion_rate_arcsec_per_hour: Optional[float]
    motion_rate_arcsec_per_day: Optional[float]
    coordinate_uncertainty_arcsec: Optional[float]
    significance_snr: Optional[float]
    temporal_eligibility_status: str
    is_secular_motion_eligible: bool
    notes: str
    limitation_codes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AstronomicalMotionEngine:
    """
    Authoritative motion calculation engine implementing spherical astrometry,
    uncertainty propagation, and fail-closed dither governance.
    """

    @classmethod
    def parse_timestamp_to_mjd(cls, ts: Union[str, float, int]) -> Optional[float]:
        """
        Parses an ISO 8601 UTC string or numeric timestamp to Modified Julian Date (MJD).
        Returns None if parsing fails.
        """
        if ts is None:
            return None

        # If already numeric MJD (e.g. 50000 - 80000)
        if isinstance(ts, (float, int)):
            val = float(ts)
            if math.isnan(val) or math.isinf(val):
                return None
            # If timestamp looks like unix timestamp (e.g. > 1e9)
            if val > 1_000_000_000:
                # Unix timestamp seconds to MJD: MJD = (unix / 86400) + 40587.0
                return (val / 86400.0) + 40587.0
            return val

        if isinstance(ts, str):
            clean_str = ts.strip().rstrip("Z")
            # Try float conversion first in case MJD was passed as string
            try:
                numeric_val = float(clean_str)
                if not (math.isnan(numeric_val) or math.isinf(numeric_val)):
                    if numeric_val > 1_000_000_000:
                        return (numeric_val / 86400.0) + 40587.0
                    return numeric_val
            except ValueError:
                pass

            # Try ISO 8601 parsing
            for fmt in (
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ):
                try:
                    dt = datetime.strptime(clean_str, fmt).replace(tzinfo=timezone.utc)
                    # Convert datetime to MJD: MJD = (unix_timestamp / 86400) + 40587.0
                    unix_sec = dt.timestamp()
                    return (unix_sec / 86400.0) + 40587.0
                except ValueError:
                    continue

        return None

    @classmethod
    def calculate_motion(
        cls,
        obs_a: Optional[ObservationEpoch],
        obs_b: Optional[ObservationEpoch],
        sigma_a_override: Optional[float] = None,
        sigma_b_override: Optional[float] = None
    ) -> MotionAnalysisResult:
        """
        Calculates astrometric displacement and motion rates between two observations.
        Enforces strict fail-closed criteria and intra-visit dither safeguards.
        """
        # Guard 1: Insufficient observations
        if obs_a is None or obs_b is None:
            return MotionAnalysisResult(
                status=MotionStatusCode.INSUFFICIENT_OBSERVATIONS.value,
                is_valid=False,
                obs_a=obs_a.__dict__ if obs_a else None,
                obs_b=obs_b.__dict__ if obs_b else None,
                angular_displacement_arcsec=None,
                position_angle_deg=None,
                time_baseline_hours=None,
                time_baseline_days=None,
                motion_rate_arcsec_per_hour=None,
                motion_rate_arcsec_per_day=None,
                coordinate_uncertainty_arcsec=None,
                significance_snr=None,
                temporal_eligibility_status=MotionEligibilityStatus.INELIGIBLE_MISSING_DATA.value,
                is_secular_motion_eligible=False,
                notes="Two valid observation epochs are required to compute motion displacement.",
                limitation_codes=["INSUFFICIENT_OBSERVATIONS"]
            )

        # Guard 2: Missing WCS validation
        if not obs_a.wcs_valid or not obs_b.wcs_valid:
            return MotionAnalysisResult(
                status=MotionStatusCode.MISSING_WCS.value,
                is_valid=False,
                obs_a=obs_a.__dict__,
                obs_b=obs_b.__dict__,
                angular_displacement_arcsec=None,
                position_angle_deg=None,
                time_baseline_hours=None,
                time_baseline_days=None,
                motion_rate_arcsec_per_hour=None,
                motion_rate_arcsec_per_day=None,
                coordinate_uncertainty_arcsec=None,
                significance_snr=None,
                temporal_eligibility_status=MotionEligibilityStatus.INELIGIBLE_MISSING_DATA.value,
                is_secular_motion_eligible=False,
                notes="Valid WCS astrometric solution is required for both observation epochs.",
                limitation_codes=["MISSING_OR_CORRUPT_WCS"]
            )

        # Guard 3: Coordinate validation
        valid_a, msg_a = validate_coordinates(obs_a.ra_deg, obs_a.dec_deg)
        valid_b, msg_b = validate_coordinates(obs_b.ra_deg, obs_b.dec_deg)
        if not valid_a or not valid_b:
            err_msg = f"Invalid celestial coordinates: Epoch A: {msg_a}; Epoch B: {msg_b}"
            return MotionAnalysisResult(
                status=MotionStatusCode.INVALID_COORDINATES.value,
                is_valid=False,
                obs_a=obs_a.__dict__,
                obs_b=obs_b.__dict__,
                angular_displacement_arcsec=None,
                position_angle_deg=None,
                time_baseline_hours=None,
                time_baseline_days=None,
                motion_rate_arcsec_per_hour=None,
                motion_rate_arcsec_per_day=None,
                coordinate_uncertainty_arcsec=None,
                significance_snr=None,
                temporal_eligibility_status=MotionEligibilityStatus.INELIGIBLE_MISSING_DATA.value,
                is_secular_motion_eligible=False,
                notes=err_msg,
                limitation_codes=["INVALID_COORDINATES"]
            )

        # Guard 4: Timestamp validation & baseline
        mjd_a = obs_a.mjd if obs_a.mjd is not None else cls.parse_timestamp_to_mjd(obs_a.timestamp)
        mjd_b = obs_b.mjd if obs_b.mjd is not None else cls.parse_timestamp_to_mjd(obs_b.timestamp)

        if mjd_a is None or mjd_b is None:
            return MotionAnalysisResult(
                status=MotionStatusCode.INVALID_TIMESTAMP.value,
                is_valid=False,
                obs_a=obs_a.__dict__,
                obs_b=obs_b.__dict__,
                angular_displacement_arcsec=None,
                position_angle_deg=None,
                time_baseline_hours=None,
                time_baseline_days=None,
                motion_rate_arcsec_per_hour=None,
                motion_rate_arcsec_per_day=None,
                coordinate_uncertainty_arcsec=None,
                significance_snr=None,
                temporal_eligibility_status=MotionEligibilityStatus.INELIGIBLE_MISSING_DATA.value,
                is_secular_motion_eligible=False,
                notes="One or both observation epochs lack a parseable UTC or MJD timestamp.",
                limitation_codes=["INVALID_TIMESTAMP"]
            )

        dt_days = abs(mjd_b - mjd_a)
        dt_hours = dt_days * 24.0

        if dt_hours <= 0.0:
            return MotionAnalysisResult(
                status=MotionStatusCode.INVALID_TIMESTAMP.value,
                is_valid=False,
                obs_a=obs_a.__dict__,
                obs_b=obs_b.__dict__,
                angular_displacement_arcsec=None,
                position_angle_deg=None,
                time_baseline_hours=0.0,
                time_baseline_days=0.0,
                motion_rate_arcsec_per_hour=None,
                motion_rate_arcsec_per_day=None,
                coordinate_uncertainty_arcsec=None,
                significance_snr=None,
                temporal_eligibility_status=MotionEligibilityStatus.INELIGIBLE_MISSING_DATA.value,
                is_secular_motion_eligible=False,
                notes="Observations must have non-zero temporal separation (dt > 0).",
                limitation_codes=["ZERO_TIME_SEPARATION"]
            )

        # Coordinate Uncertainty Propagation
        sig_a = float(sigma_a_override if sigma_a_override is not None else obs_a.sigma_coord_arcsec)
        sig_b = float(sigma_b_override if sigma_b_override is not None else obs_b.sigma_coord_arcsec)

        if sig_a <= 0.0 or sig_b <= 0.0 or math.isnan(sig_a) or math.isnan(sig_b):
            return MotionAnalysisResult(
                status=MotionStatusCode.UNCERTAINTY_UNAVAILABLE.value,
                is_valid=False,
                obs_a=obs_a.__dict__,
                obs_b=obs_b.__dict__,
                angular_displacement_arcsec=None,
                position_angle_deg=None,
                time_baseline_hours=dt_hours,
                time_baseline_days=dt_days,
                motion_rate_arcsec_per_hour=None,
                motion_rate_arcsec_per_day=None,
                coordinate_uncertainty_arcsec=None,
                significance_snr=None,
                temporal_eligibility_status=MotionEligibilityStatus.INELIGIBLE_MISSING_DATA.value,
                is_secular_motion_eligible=False,
                notes="Coordinate uncertainty sigma must be strictly positive and finite.",
                limitation_codes=["UNCERTAINTY_UNAVAILABLE"]
            )

        sigma_delta_theta = math.sqrt(sig_a**2 + sig_b**2)

        # Perform Spherical Calculations
        ra_a = normalize_ra_deg(obs_a.ra_deg)
        dec_a = obs_a.dec_deg
        ra_b = normalize_ra_deg(obs_b.ra_deg)
        dec_b = obs_b.dec_deg

        angular_disp_arcsec = spherical_angular_separation_arcsec(ra_a, dec_a, ra_b, dec_b)
        pa_deg = position_angle_deg(ra_a, dec_a, ra_b, dec_b)

        motion_rate_hr = angular_disp_arcsec / dt_hours
        motion_rate_day = angular_disp_arcsec / dt_days
        snr = angular_disp_arcsec / sigma_delta_theta if sigma_delta_theta > 0 else 0.0

        # Temporal Eligibility Safeguard Enforcement
        if dt_days < 1.0:
            eligibility = MotionEligibilityStatus.INTRA_VISIT_DITHER.value
            is_secular_eligible = False
            notes = (
                f"Observation baseline (dt = {dt_hours:.2f} hours, {dt_days:.4f} days) is less than 1.0 day. "
                "Classified strictly as INTRA-VISIT DITHER. Measured displacement reflects optical/spacecraft "
                "dither registration, NOT secular astronomical motion."
            )
            lim_codes = ["INTRA_VISIT_DITHER", "SECULAR_MOTION_INELIGIBLE"]
        else:
            eligibility = MotionEligibilityStatus.TEMPORALLY_ELIGIBLE.value
            is_secular_eligible = True
            notes = (
                f"Observation baseline (dt = {dt_days:.2f} days) satisfies temporal separation requirement. "
                "Pair is TEMPORALLY ELIGIBLE for multi-epoch motion analysis. Note: Confirmation requires "
                "astrometric cross-match and multi-point orbital fit."
            )
            lim_codes = ["REQUIRES_ASTROMETRIC_VETTING"]

        return MotionAnalysisResult(
            status=MotionStatusCode.SUCCESS.value,
            is_valid=True,
            obs_a={
                "obs_id": obs_a.obs_id,
                "ra_deg": ra_a,
                "dec_deg": dec_a,
                "timestamp": str(obs_a.timestamp),
                "mjd": mjd_a,
                "sigma_arcsec": sig_a
            },
            obs_b={
                "obs_id": obs_b.obs_id,
                "ra_deg": ra_b,
                "dec_deg": dec_b,
                "timestamp": str(obs_b.timestamp),
                "mjd": mjd_b,
                "sigma_arcsec": sig_b
            },
            angular_displacement_arcsec=round(angular_disp_arcsec, 4),
            position_angle_deg=round(pa_deg, 2),
            time_baseline_hours=round(dt_hours, 4),
            time_baseline_days=round(dt_days, 5),
            motion_rate_arcsec_per_hour=round(motion_rate_hr, 4),
            motion_rate_arcsec_per_day=round(motion_rate_day, 4),
            coordinate_uncertainty_arcsec=round(sigma_delta_theta, 4),
            significance_snr=round(snr, 2),
            temporal_eligibility_status=eligibility,
            is_secular_motion_eligible=is_secular_eligible,
            notes=notes,
            limitation_codes=lim_codes
        )

