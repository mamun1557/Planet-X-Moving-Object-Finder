"""
SPECTRA-X / F1 — Phase 4, Task 4.15G
MOTION-X Interface Contract & FUSION-X Evidence Adapter
Target Contract: CATALOG_MASKED_SPATIAL_EVIDENCE_V1

Package:           spectra_engine
Module:            motion_x_mask_interface.py
Pipeline Build:    l2b-v27-2026-222
Governance Mode:   Strict Production-Preserving / Isolated Shadow Integration

Responsibilities:
1. Provide authoritative `SpatialAnomalyVettedEvidence` dataclass contract for FUSION-X.
2. Bridge MOTION-X / Gaia / Pilot Catalogues to ASTROVISION via `CatalogSourceContext`.
3. Support deterministic coordinate projection (sky RA/Dec to cutout subpixel coordinates).
4. Enforce fail-closed governance for unknown, missing, or corrupt catalog tables.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd

from spectra_engine.catalog_aware_source_masker import (
    CatalogSourceContext,
    SourceEvidenceState,
    CatalogMaskResult,
    ShadowEvaluationResult
)


class VettingStatus(str, Enum):
    """Authoritative vetting categorization for FUSION-X consumption."""
    CLEAN_VETTED_ANOMALY = "CLEAN_VETTED_ANOMALY"
    MASK_SUPPRESSED_FALSE_ALARM = "MASK_SUPPRESSED_FALSE_ALARM"
    UNVERIFIABLE_BACKGROUND = "UNVERIFIABLE_BACKGROUND"
    CONFIRMED_STELLAR_SOURCE = "CONFIRMED_STELLAR_SOURCE"
    NOMINAL_CLEAN_BACKGROUND = "NOMINAL_CLEAN_BACKGROUND"


@dataclass(frozen=True)
class SpatialAnomalyVettedEvidence:
    """
    Authoritative output contract consumable by FUSION-X.
    Contract Identifier: CATALOG_MASKED_SPATIAL_EVIDENCE_V1
    """
    trial_id: str
    pointing_id: str
    detector_id: str
    central_peak_chi2: float
    central_pt_integrated_chi2: float
    operating_threshold_tau: float
    is_anomaly_detected: bool
    catalog_vetting_applied: bool
    offcenter_sources_masked_count: int
    central_aperture_encroached: bool
    vetting_status: str
    contract_version: str = "CATALOG_MASKED_SPATIAL_EVIDENCE_V1"
    limitation_codes: Tuple[str, ...] = ()
    provenance_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["limitation_codes"] = list(self.limitation_codes)
        return d


class MotionXMaskExtractor:
    """
    Extracts and maps astrometric catalog sources into `CatalogSourceContext`
    objects positioned within a 128x128 cutout FOV.
    """

    DEFAULT_PIXEL_SCALE_ARCSEC = 6.2  # Nominal SPHEREx pixel scale (arcsec/pixel)

    @classmethod
    def extract_sources_from_catalog(
        cls,
        target_ra_deg: float,
        target_dec_deg: float,
        catalog_df: Optional[pd.DataFrame],
        catalog_name: str = "GAIA_DR3",
        catalog_version: str = "DR3",
        cutout_shape: Tuple[int, int] = (128, 128),
        target_pixel: Tuple[float, float] = (64.0, 64.0),
        pixel_scale_arcsec: float = DEFAULT_PIXEL_SCALE_ARCSEC,
        search_radius_arcsec: Optional[float] = None,
        target_match_radius_arcsec: float = 3.0
    ) -> List[CatalogSourceContext]:
        """
        Extracts catalog sources within cutout FOV around target (ra, dec).
        Fails closed with MASK_UNVERIFIABLE if catalog_df is None or empty.
        """
        # If no catalog dataframe provided or empty, fail closed
        if catalog_df is None or catalog_df.empty:
            return [
                CatalogSourceContext(
                    source_id=f"UNKNOWN_TARGET_AT_{target_ra_deg:.4f}_{target_dec_deg:.4f}",
                    catalog_name=catalog_name,
                    catalog_version=catalog_version,
                    evidence_state=SourceEvidenceState.MASK_UNVERIFIABLE,
                    ra_deg=target_ra_deg,
                    dec_deg=target_dec_deg,
                    notes="Catalog table missing or empty; unverified sky footprint."
                )
            ]

        H, W = cutout_shape
        t_px_x, t_px_y = target_pixel

        # Max half-diagonal radius in arcseconds
        max_dist_px = math.sqrt((H / 2.0)**2 + (W / 2.0)**2) + 10.0
        max_fov_arcsec = max_dist_px * pixel_scale_arcsec if search_radius_arcsec is None else search_radius_arcsec

        # Standardize column names
        cols = {c.lower(): c for c in catalog_df.columns}
        ra_col = cols.get("ra")
        dec_col = cols.get("dec")
        id_col = cols.get("source_id") or cols.get("id") or cols.get("tmass_id")

        if not ra_col or not dec_col or not id_col:
            return [
                CatalogSourceContext(
                    source_id="CORRUPT_CATALOG_SCHEMA",
                    catalog_name=catalog_name,
                    catalog_version=catalog_version,
                    evidence_state=SourceEvidenceState.MASK_UNVERIFIABLE,
                    notes=f"Catalog missing standard coordinate columns: found {list(catalog_df.columns)}"
                )
            ]

        ra_arr = catalog_df[ra_col].to_numpy(dtype=float)
        dec_arr = catalog_df[dec_col].to_numpy(dtype=float)

        cos_dec = math.cos(math.radians(target_dec_deg))
        dra_arcsec = (ra_arr - target_ra_deg) * cos_dec * 3600.0
        ddec_arcsec = (dec_arr - target_dec_deg) * 3600.0
        dist_arcsec = np.sqrt(dra_arcsec**2 + ddec_arcsec**2)

        within_fov = dist_arcsec <= max_fov_arcsec
        if not np.any(within_fov):
            # Verified search performed, no counterpart in cone
            return []

        matched_indices = np.where(within_fov)[0]
        contexts: List[CatalogSourceContext] = []

        for idx in matched_indices:
            row = catalog_df.iloc[idx]
            sid = str(row[id_col])
            r_arcsec = float(dist_arcsec[idx])

            # Convert tangent plane offset (dRA, dDec) to pixel offset
            # Standard astronomical orientation: X corresponds to -RA (East left), Y to +Dec (North up)
            # or direct local pixel tangent plane:
            dx_px = - (dra_arcsec[idx] / pixel_scale_arcsec)
            dy_px = (ddec_arcsec[idx] / pixel_scale_arcsec)
            sub_x = t_px_x + dx_px
            sub_y = t_px_y + dy_px

            # Check if source corresponds to the central target candidate
            is_center = bool(r_arcsec <= target_match_radius_arcsec)

            # Determine evidence state
            ruwe = row.get(cols.get("ruwe")) if "ruwe" in cols else None
            is_ambiguous = (ruwe is not None and not pd.isna(ruwe) and float(ruwe) > 1.4)

            if is_ambiguous:
                state = SourceEvidenceState.AMBIGUOUS_SOURCE
            elif is_center:
                state = SourceEvidenceState.KNOWN_CATALOG_SOURCE
            else:
                state = SourceEvidenceState.KNOWN_CATALOG_SOURCE

            mag = row.get(cols.get("phot_g_mean_mag")) if "phot_g_mean_mag" in cols else None
            plx = row.get(cols.get("parallax")) if "parallax" in cols else None
            pmra = row.get(cols.get("pmra")) if "pmra" in cols else None
            pmdec = row.get(cols.get("pmdec")) if "pmdec" in cols else None

            ctx = CatalogSourceContext(
                source_id=sid,
                catalog_name=catalog_name,
                catalog_version=catalog_version,
                evidence_state=state,
                ra_deg=float(row[ra_col]),
                dec_deg=float(row[dec_col]),
                subpixel_x=float(sub_x),
                subpixel_y=float(sub_y),
                angular_separation_arcsec=r_arcsec,
                apparent_magnitude=float(mag) if mag is not None and not pd.isna(mag) else None,
                parallax_mas=float(plx) if plx is not None and not pd.isna(plx) else None,
                pmra_mas_yr=float(pmra) if pmra is not None and not pd.isna(pmra) else None,
                pmdec_mas_yr=float(pmdec) if pmdec is not None and not pd.isna(pmdec) else None,
                match_reliability=1.0,
                is_center_target=is_center
            )
            contexts.append(ctx)

        return contexts

    @classmethod
    def create_vetted_evidence_from_shadow(
        cls,
        shadow_result: ShadowEvaluationResult,
        pointing_id: str,
        detector_id: str
    ) -> SpatialAnomalyVettedEvidence:
        """
        Translates a ShadowEvaluationResult into an authoritative SpatialAnomalyVettedEvidence
        record consumable by FUSION-X.
        """
        mask_res = shadow_result.mask_result
        is_detected = shadow_result.shadow_anomaly_detected
        was_detected_orig = shadow_result.original_anomaly_detected

        # Determine vetting status
        if shadow_result.false_alarm_suppressed:
            v_status = VettingStatus.MASK_SUPPRESSED_FALSE_ALARM.value
        elif is_detected:
            v_status = VettingStatus.CLEAN_VETTED_ANOMALY.value
        elif mask_res.unverifiable_sources_count > 0:
            v_status = VettingStatus.UNVERIFIABLE_BACKGROUND.value
        else:
            v_status = VettingStatus.NOMINAL_CLEAN_BACKGROUND.value

        prov = {
            "mask_dilation_pixels": mask_res.dilation_radius_pixels,
            "masked_area_fraction_pct": mask_res.masked_area_fraction_pct,
            "original_peak_chi2": shadow_result.original_peak_chi2,
            "shadow_peak_chi2": shadow_result.shadow_peak_chi2,
            "delta_peak_chi2": shadow_result.delta_peak_chi2
        }

        return SpatialAnomalyVettedEvidence(
            trial_id=shadow_result.trial_id,
            pointing_id=pointing_id,
            detector_id=detector_id,
            central_peak_chi2=shadow_result.shadow_peak_chi2,
            central_pt_integrated_chi2=shadow_result.shadow_pt_integrated_chi2,
            operating_threshold_tau=shadow_result.operating_threshold_tau,
            is_anomaly_detected=is_detected,
            catalog_vetting_applied=True,
            offcenter_sources_masked_count=mask_res.masked_sources_count,
            central_aperture_encroached=mask_res.central_aperture_encroached,
            vetting_status=v_status,
            limitation_codes=tuple(mask_res.limitation_codes),
            provenance_metadata=prov
        )

