"""
SPECTRA-X / F1 — Phase 4, Task 4.15
Production-Grade CatalogAwareSourceMasker Module
Isolated Scientific Engineering Implementation & Provenance-Aware Source Masking Engine

Package:           spectra_engine
Module:            catalog_aware_source_masker.py
Pipeline Build:    l2b-v27-2026-222
Governance Mode:   Strict Production-Preserving / Isolated Shadow Integration

Design Principles:
1. Zero framework coupling: Pure Python, NumPy, SciPy (zero dependency on FastAPI, React, SQLite).
2. Strict Mask Polarity:
   - In ASTROVISION, valid pixels are represented by 1.0, and defect/masked pixels by 0.0.
   - The standalone `catalog_source_mask` uses 1 = source footprint masked, 0 = unmasked sky.
   - The `combined_effective_mask` uses ASTROVISION polarity: 1 = valid sky, 0 = defect or source-masked.
3. Explicit Source Evidence States:
   - KNOWN_CATALOG_SOURCE: Confirmed catalog counterpart (Gaia DR3 / vetted source).
   - PROBABLE_SOURCE: High-confidence spatial counterpart within core proximity.
   - AMBIGUOUS_SOURCE: Multiple counterparts or confusion; flagged for advisory review.
   - NO_LOCAL_CATALOG_COUNTERPART: Search conducted in verified catalog footprint, no counterpart found.
   - MASK_UNVERIFIABLE: Outside catalog coverage or missing astrometric records; fail-closed.
4. Central Aperture Protection:
   - Off-center sources are masked to prevent receptive-field contamination.
   - The central candidate aperture (r <= 2.5 px) is preserved unless explicitly configured.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import scipy.ndimage as ndimage


class SourceEvidenceState(str, Enum):
    """Explicit, non-overlapping source evidence states for catalog vetting."""
    KNOWN_CATALOG_SOURCE = "KNOWN_CATALOG_SOURCE"
    PROBABLE_SOURCE = "PROBABLE_SOURCE"
    AMBIGUOUS_SOURCE = "AMBIGUOUS_SOURCE"
    NO_LOCAL_CATALOG_COUNTERPART = "NO_LOCAL_CATALOG_COUNTERPART"
    MASK_UNVERIFIABLE = "MASK_UNVERIFIABLE"


@dataclass(frozen=True)
class CatalogSourceContext:
    """
    Immutable representation of a single catalog source within or near the cutout FOV.
    Preserves complete provenance, astrometric, and classification metadata.
    """
    source_id: str
    catalog_name: str                           # e.g., 'GAIA_DR3', 'SPHEREX_L2', '2MASS', 'ALLWISE'
    catalog_version: str                        # e.g., 'DR3', 'l2b-v27-2026-222'
    evidence_state: SourceEvidenceState
    ra_deg: Optional[float] = None              # Sky coordinate (ICRS)
    dec_deg: Optional[float] = None
    subpixel_x: Optional[float] = None          # Projected coordinate in cutout (0-indexed)
    subpixel_y: Optional[float] = None
    angular_separation_arcsec: Optional[float] = None # Separation from target aperture center
    apparent_magnitude: Optional[float] = None  # e.g. phot_g_mean_mag
    parallax_mas: Optional[float] = None
    pmra_mas_yr: Optional[float] = None
    pmdec_mas_yr: Optional[float] = None
    match_reliability: float = 1.0              # Quality score (0.0 to 1.0)
    is_center_target: bool = False              # True if this is the target candidate at (64, 64)
    custom_core_radius_pixels: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence_state"] = self.evidence_state.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CatalogSourceContext":
        data_copy = dict(data)
        if isinstance(data_copy.get("evidence_state"), str):
            data_copy["evidence_state"] = SourceEvidenceState(data_copy["evidence_state"])
        return cls(**data_copy)


@dataclass
class CatalogMaskRequest:
    """Request contract for deterministic catalog-aware mask generation."""
    request_id: str
    cutout_shape: Tuple[int, int] = (128, 128)
    target_pixel_x: float = 64.0                # Central evaluation aperture center X
    target_pixel_y: float = 64.0                # Central evaluation aperture center Y
    target_ra_deg: Optional[float] = None
    target_dec_deg: Optional[float] = None
    base_defect_mask: Optional[np.ndarray] = None # 1 = valid, 0 = defect (ASTROVISION convention)
    catalog_sources: List[CatalogSourceContext] = field(default_factory=list)
    dilation_radius_pixels: int = 2             # Configurable: 0, 1, 2, 3, 5 px
    core_mask_radius_pixels: float = 2.5        # Baseline core radius (matching PSF core)
    protect_central_aperture: bool = True       # Enforces central candidate aperture preservation
    central_aperture_radius_pixels: float = 2.5 # Radius of central protected aperture
    mask_ambiguous_sources: bool = True         # Whether ambiguous sources receive defensive mask
    wcs: Optional[Any] = None                   # Astropy WCS instance if coordinate projection needed


@dataclass(frozen=True)
class CatalogMaskResult:
    """
    Authoritative result contract containing generated masks, coverage statistics,
    provenance records, and limitation codes.
    """
    request_id: str
    combined_effective_mask: np.ndarray         # ASTROVISION polarity: 1 = valid sky, 0 = masked/defect
    catalog_source_mask: np.ndarray             # Standalone source mask: 1 = source masked, 0 = unmasked
    original_defect_mask: np.ndarray            # Preserved pristine base defect mask
    cutout_shape: Tuple[int, int]
    total_pixels: int
    original_defect_pixel_count: int
    catalog_masked_pixel_count: int
    effective_valid_pixel_count: int
    masked_area_fraction_pct: float
    central_aperture_encroached: bool
    central_aperture_masked_fraction_pct: float
    masked_sources_count: int
    unverifiable_sources_count: int
    ambiguous_sources_count: int
    dilation_radius_pixels: int
    limitation_codes: List[str]
    provenance_metadata: Dict[str, Any]

    def to_dict(self, include_arrays: bool = False) -> Dict[str, Any]:
        data = {
            "request_id": self.request_id,
            "cutout_shape": list(self.cutout_shape),
            "total_pixels": self.total_pixels,
            "original_defect_pixel_count": self.original_defect_pixel_count,
            "catalog_masked_pixel_count": self.catalog_masked_pixel_count,
            "effective_valid_pixel_count": self.effective_valid_pixel_count,
            "masked_area_fraction_pct": round(self.masked_area_fraction_pct, 4),
            "central_aperture_encroached": self.central_aperture_encroached,
            "central_aperture_masked_fraction_pct": round(self.central_aperture_masked_fraction_pct, 4),
            "masked_sources_count": self.masked_sources_count,
            "unverifiable_sources_count": self.unverifiable_sources_count,
            "ambiguous_sources_count": self.ambiguous_sources_count,
            "dilation_radius_pixels": self.dilation_radius_pixels,
            "limitation_codes": list(self.limitation_codes),
            "provenance_metadata": dict(self.provenance_metadata)
        }
        if include_arrays:
            data["combined_effective_mask"] = self.combined_effective_mask.tolist()
            data["catalog_source_mask"] = self.catalog_source_mask.tolist()
            data["original_defect_mask"] = self.original_defect_mask.tolist()
        return data


class CatalogAwareSourceMasker:
    """
    Production-grade, provenance-aware catalog source masker.
    Generates deterministic spatial masks for off-center cataloged sources
    to eliminate convolutional receptive-field contamination in ASTROVISION.
    """

    ALLOWED_DILATIONS = {0, 1, 2, 3, 5}
    DEFAULT_DILATION = 2

    @classmethod
    def generate_mask(cls, request: CatalogMaskRequest) -> CatalogMaskResult:
        """
        Executes deterministic mask generation on a cutout request.
        Fails closed on corrupt or invalid parameters.
        """
        # 1. Parameter Validation
        cls._validate_request(request)

        H, W = request.cutout_shape
        total_pixels = H * W

        # 2. Base Defect Mask Ingestion
        if request.base_defect_mask is not None:
            if request.base_defect_mask.shape != (H, W):
                raise ValueError(
                    f"base_defect_mask shape {request.base_defect_mask.shape} does not match cutout_shape {request.cutout_shape}"
                )
            base_defect_mask = (request.base_defect_mask > 0.5).astype(np.float32)
        else:
            base_defect_mask = np.ones((H, W), dtype=np.float32)

        original_defect_pixels = int(np.sum(base_defect_mask == 0.0))

        # 3. Source Selection & Projection
        source_mask_boolean = np.zeros((H, W), dtype=bool)
        masked_sources_count = 0
        unverifiable_count = 0
        ambiguous_count = 0
        limitations = []

        # Coordinate grid for distance calculations
        yy, xx = np.indices((H, W), dtype=np.float64)

        # Central evaluation aperture mask
        dsq_center = (xx - float(request.target_pixel_x))**2 + (yy - float(request.target_pixel_y))**2
        center_aperture_mask = (dsq_center <= request.central_aperture_radius_pixels**2)

        # De-duplicate sources by source_id
        seen_ids = set()
        unique_sources = []
        for src in request.catalog_sources:
            if src.source_id in seen_ids:
                limitations.append(f"DUPLICATE_SOURCE_RECORD_IGNORED_{src.source_id}")
                continue
            seen_ids.add(src.source_id)
            unique_sources.append(src)

        for src in unique_sources:
            # Handle unverifiable state
            if src.evidence_state == SourceEvidenceState.MASK_UNVERIFIABLE:
                unverifiable_count += 1
                limitations.append(f"SOURCE_EVIDENCE_UNVERIFIABLE_{src.source_id}")
                continue

            # Handle no local counterpart
            if src.evidence_state == SourceEvidenceState.NO_LOCAL_CATALOG_COUNTERPART:
                continue

            # Handle ambiguous source policy
            if src.evidence_state == SourceEvidenceState.AMBIGUOUS_SOURCE:
                ambiguous_count += 1
                limitations.append(f"AMBIGUOUS_SOURCE_PRESENT_{src.source_id}")
                if not request.mask_ambiguous_sources:
                    continue

            # Resolve cutout coordinates
            px, py = cls._resolve_pixel_coordinates(src, request, H, W)
            if px is None or py is None:
                limitations.append(f"COORDINATE_PROJECTION_FAILED_{src.source_id}")
                continue

            # If source is out of bounds by more than 32 pixels, skip
            if px < -32.0 or px > (W + 31.0) or py < -32.0 or py > (H + 31.0):
                limitations.append(f"SOURCE_OUT_OF_BOUNDS_{src.source_id}")
                continue

            # Core aperture radius
            core_r = float(src.custom_core_radius_pixels or request.core_mask_radius_pixels)
            dsq = (xx - px)**2 + (yy - py)**2
            source_core = (dsq <= core_r**2)

            # Apply Dilation
            if request.dilation_radius_pixels > 0:
                dilated_source = ndimage.binary_dilation(source_core, iterations=request.dilation_radius_pixels)
            else:
                dilated_source = source_core

            # Prevent central aperture masking if central protection is active and source is not center target
            if request.protect_central_aperture and not src.is_center_target:
                # Clear any overlap with central aperture core
                dilated_source = dilated_source & (~center_aperture_mask)

            source_mask_boolean = source_mask_boolean | dilated_source
            masked_sources_count += 1

        # 4. Standalone Source Mask (1 = source masked, 0 = unmasked sky)
        catalog_source_mask = source_mask_boolean.astype(np.float32)
        catalog_masked_pixels = int(np.sum(catalog_source_mask > 0.5))

        # 5. Combined Effective Mask (ASTROVISION polarity: 1 = valid sky, 0 = defect or source-masked)
        combined_effective_mask = (base_defect_mask > 0.5) & (~source_mask_boolean)
        combined_effective_mask = combined_effective_mask.astype(np.float32)
        effective_valid_pixels = int(np.sum(combined_effective_mask > 0.5))

        # 6. Central Aperture Encroachment Analysis
        center_ap_total_pixels = int(np.sum(center_aperture_mask))
        center_ap_masked_pixels = int(np.sum(catalog_source_mask[center_aperture_mask] > 0.5))
        center_encroached = bool(center_ap_masked_pixels > 0)
        center_masked_pct = (center_ap_masked_pixels / center_ap_total_pixels * 100.0) if center_ap_total_pixels > 0 else 0.0

        if center_encroached:
            limitations.append("CENTRAL_APERTURE_MASK_ENCROACHMENT")

        # 7. Mask Coverage Statistics
        masked_area_pct = (float(total_pixels - effective_valid_pixels) / float(total_pixels)) * 100.0

        # Provenance record
        provenance = {
            "masker_module": "spectra_engine.catalog_aware_source_masker",
            "module_version": "1.0.0",
            "pipeline_build": "l2b-v27-2026-222",
            "dilation_radius_pixels": request.dilation_radius_pixels,
            "core_mask_radius_pixels": request.core_mask_radius_pixels,
            "protect_central_aperture": request.protect_central_aperture,
            "input_catalog_sources_count": len(request.catalog_sources),
            "unique_sources_count": len(unique_sources),
            "masked_sources_count": masked_sources_count,
            "unverifiable_sources_count": unverifiable_count,
            "ambiguous_sources_count": ambiguous_count
        }

        return CatalogMaskResult(
            request_id=request.request_id,
            combined_effective_mask=combined_effective_mask,
            catalog_source_mask=catalog_source_mask,
            original_defect_mask=base_defect_mask,
            cutout_shape=request.cutout_shape,
            total_pixels=total_pixels,
            original_defect_pixel_count=original_defect_pixels,
            catalog_masked_pixel_count=catalog_masked_pixels,
            effective_valid_pixel_count=effective_valid_pixels,
            masked_area_fraction_pct=masked_area_pct,
            central_aperture_encroached=center_encroached,
            central_aperture_masked_fraction_pct=center_masked_pct,
            masked_sources_count=masked_sources_count,
            unverifiable_sources_count=unverifiable_count,
            ambiguous_sources_count=ambiguous_count,
            dilation_radius_pixels=request.dilation_radius_pixels,
            limitation_codes=limitations,
            provenance_metadata=provenance
        )

    @classmethod
    def _validate_request(cls, request: CatalogMaskRequest) -> None:
        """Strict validation of mask request parameters."""
        if not isinstance(request.dilation_radius_pixels, int) or request.dilation_radius_pixels < 0:
            raise ValueError(f"dilation_radius_pixels must be a non-negative integer, got {request.dilation_radius_pixels}")

        if math.isnan(request.dilation_radius_pixels) or math.isinf(request.dilation_radius_pixels):
            raise ValueError("dilation_radius_pixels cannot be NaN or infinite")

        if request.dilation_radius_pixels not in cls.ALLOWED_DILATIONS:
            raise ValueError(
                f"dilation_radius_pixels {request.dilation_radius_pixels} not in supported experimental set {cls.ALLOWED_DILATIONS}"
            )

        H, W = request.cutout_shape
        if H <= 0 or W <= 0 or H > 1024 or W > 1024:
            raise ValueError(f"Invalid cutout_shape: {request.cutout_shape}")

        if not math.isfinite(request.target_pixel_x) or not math.isfinite(request.target_pixel_y):
            raise ValueError(f"Invalid target coordinates: ({request.target_pixel_x}, {request.target_pixel_y})")

    @classmethod
    def _resolve_pixel_coordinates(
        cls,
        src: CatalogSourceContext,
        request: CatalogMaskRequest,
        H: int,
        W: int
    ) -> Tuple[Optional[float], Optional[float]]:
        """Resolves (x, y) pixel coordinates in cutout space with fail-closed checks."""
        # 1. Direct subpixel coordinates provided
        if src.subpixel_x is not None and src.subpixel_y is not None:
            if math.isfinite(src.subpixel_x) and math.isfinite(src.subpixel_y):
                return float(src.subpixel_x), float(src.subpixel_y)

        # 2. WCS transformation if RA/Dec provided
        if src.ra_deg is not None and src.dec_deg is not None and request.wcs is not None:
            try:
                px, py = request.wcs.world_to_pixel_values(src.ra_deg, src.dec_deg)
                if math.isfinite(px) and math.isfinite(py):
                    # If target RA/Dec is provided, calculate relative cutout coordinates
                    if request.target_ra_deg is not None and request.target_dec_deg is not None:
                        t_px, t_py = request.wcs.world_to_pixel_values(request.target_ra_deg, request.target_dec_deg)
                        rel_x = float(request.target_pixel_x) + (float(px) - float(t_px))
                        rel_y = float(request.target_pixel_y) + (float(py) - float(t_py))
                        return rel_x, rel_y
                    return float(px), float(py)
            except Exception:
                return None, None

        # 3. Relative coordinate from angular separation and position angle (fallback)
        if src.angular_separation_arcsec is not None:
            # If subpixel coordinates missing, cannot place unambiguously
            return None, None

        return None, None


@dataclass(frozen=True)
class ShadowEvaluationResult:
    """Diagnostic comparison contract between baseline ASTROVISION and shadow masked inference."""
    trial_id: str
    detector_id: str
    original_peak_chi2: float
    shadow_peak_chi2: float
    delta_peak_chi2: float
    original_pt_integrated_chi2: float
    shadow_pt_integrated_chi2: float
    operating_threshold_tau: float
    original_anomaly_detected: bool
    shadow_anomaly_detected: bool
    false_alarm_suppressed: bool
    genuine_anomaly_preserved: bool
    mask_result: CatalogMaskResult
    runtime_provenance: Dict[str, Any]


class AstroVisionShadowAdapter:
    """
    Isolated Shadow Adapter for ASTROVISION V3.
    Executes production baseline inference alongside catalog-masked diagnostic inference
    on identical cutouts without altering the production inference path.
    """

    @classmethod
    def evaluate_shadow(
        cls,
        raw_image: np.ndarray,
        raw_variance: np.ndarray,
        raw_flags: np.ndarray,
        mask_request: CatalogMaskRequest,
        model: Any,
        scorer: Any,
        threshold_tau: float,
        device: Any = "cpu",
        is_genuine_anomaly_injected: bool = False
    ) -> ShadowEvaluationResult:
        """
        Runs dual inference:
        1. Baseline ASTROVISION V3 (original Level-2 defect mask).
        2. Shadow ASTROVISION V3 (combined effective catalog mask).
        """
        import torch
        from models.astrovision.model_v3 import RobustLocalNormalizer

        # 1. Baseline Preprocessing & Inference (Production Path Unchanged)
        res_orig = RobustLocalNormalizer.normalize_patch(raw_image, raw_variance, raw_flags)
        t_img_orig = torch.from_numpy(res_orig["norm_img"]).unsqueeze(0).unsqueeze(0).to(device)
        t_msk_orig = torch.from_numpy(res_orig["mask"]).unsqueeze(0).unsqueeze(0).to(device)

        with torch.no_grad():
            anom_orig = model.compute_anomaly_map(t_img_orig, t_msk_orig).squeeze().cpu().numpy()

        scores_orig = scorer.compute_scores(
            anom_orig,
            res_orig["mask"],
            mask_request.target_pixel_x,
            mask_request.target_pixel_y,
            point_aperture_radius=mask_request.central_aperture_radius_pixels
        )
        orig_peak = float(scores_orig["peak_chi2"])
        orig_int = float(scores_orig["pt_integrated_chi2"])
        orig_detected = bool(orig_peak >= threshold_tau)

        # 2. Shadow Catalog-Aware Mask Generation
        # Provide original normalizer defect mask into request
        mask_request.base_defect_mask = res_orig["mask"]
        mask_result = CatalogAwareSourceMasker.generate_mask(mask_request)

        # 3. Shadow Inference using Combined Effective Mask
        # We re-run normalizer with catalog mask included into flags (setting fatal bit 0 where masked)
        shadow_flags = raw_flags.copy()
        shadow_flags[mask_result.catalog_source_mask > 0.5] = shadow_flags[mask_result.catalog_source_mask > 0.5] | 1

        res_shadow = RobustLocalNormalizer.normalize_patch(raw_image, raw_variance, shadow_flags)
        t_img_shadow = torch.from_numpy(res_shadow["norm_img"]).unsqueeze(0).unsqueeze(0).to(device)
        t_msk_shadow = torch.from_numpy(res_shadow["mask"]).unsqueeze(0).unsqueeze(0).to(device)

        with torch.no_grad():
            anom_shadow = model.compute_anomaly_map(t_img_shadow, t_msk_shadow).squeeze().cpu().numpy()

        scores_shadow = scorer.compute_scores(
            anom_shadow,
            res_shadow["mask"],
            mask_request.target_pixel_x,
            mask_request.target_pixel_y,
            point_aperture_radius=mask_request.central_aperture_radius_pixels
        )
        shadow_peak = float(scores_shadow["peak_chi2"])
        shadow_int = float(scores_shadow["pt_integrated_chi2"])
        shadow_detected = bool(shadow_peak >= threshold_tau)

        delta_peak = shadow_peak - orig_peak

        # Scientific Outcomes
        # If baseline had a false alarm (detected on null control) and shadow drops below threshold:
        false_alarm_suppressed = bool(orig_detected and not shadow_detected and not is_genuine_anomaly_injected)
        # If genuine anomaly was injected and remains detected:
        genuine_anomaly_preserved = bool(shadow_detected and is_genuine_anomaly_injected)

        runtime_meta = {
            "adapter_version": "1.0.0",
            "device": str(device),
            "target_pixel_x": mask_request.target_pixel_x,
            "target_pixel_y": mask_request.target_pixel_y,
            "threshold_tau": threshold_tau,
            "is_genuine_anomaly_injected": is_genuine_anomaly_injected
        }

        return ShadowEvaluationResult(
            trial_id=mask_request.request_id,
            detector_id="UNSPECIFIED",
            original_peak_chi2=orig_peak,
            shadow_peak_chi2=shadow_peak,
            delta_peak_chi2=delta_peak,
            original_pt_integrated_chi2=orig_int,
            shadow_pt_integrated_chi2=shadow_int,
            operating_threshold_tau=threshold_tau,
            original_anomaly_detected=orig_detected,
            shadow_anomaly_detected=shadow_detected,
            false_alarm_suppressed=false_alarm_suppressed,
            genuine_anomaly_preserved=genuine_anomaly_preserved,
            mask_result=mask_result,
            runtime_provenance=runtime_meta
        )
