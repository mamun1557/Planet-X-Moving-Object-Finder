# SPECTRA-X / F1 — Phase 4, Task 4.14G
# MOTION-X / FUSION-X Catalog-Aware Masking Integration Architecture

**Target Contract:** `CATALOG_MASKED_SPATIAL_EVIDENCE_V1`  
**Module:** ASTROVISION Engine Integration with MOTION-X and FUSION-X  
**Pipeline Build:** `l2b-v27-2026-222`  
**Governance:** Non-Coupled Standalone Design / Frozen Core Interfaces  

---

## 1. Architectural Principles

1. **Strict Engine Decoupling:** ASTROVISION remains an independent scientific engine. It does NOT import or depend on FastAPI, SQLite, or React UI frameworks.
2. **Explicit Evidence Contract:** Catalog evidence is passed into ASTROVISION via a frozen, immutable dataclass contract (`CatalogContextRecord`).
3. **Fail-Closed Default:** If catalog metadata is missing, corrupt, or unverifiable, the engine falls back to standard Level 2 defect masking and marks evidence status as `MASK_UNVERIFIABLE`.
4. **Separation of Source Types:** Non-matches in Gaia are never treated as proof of empty sky; proper motion and parallax metadata are explicitly propagated into MOTION-X.

---

## 2. Contract Specification: `CATALOG_MASKED_SPATIAL_EVIDENCE_V1`

```python
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass(frozen=True)
class CatalogSourceContext:
    """Immutable context for a single cataloged source in the cutout FOV."""
    catalog_source_id: str
    catalog_origin: str                  # e.g., 'GAIA_DR3', 'SPHEREX_L2', '2MASS'
    subpixel_x: float                   # Coordinate in 128x128 cutout
    subpixel_y: float
    angular_distance_arcsec: float       # Separation from central aperture
    apparent_magnitude: Optional[float]
    parallax_mas: Optional[float]
    proper_motion_mas_yr: Optional[float]
    uncertainty_state: str               # KNOWN_CATALOG_SOURCE | PROBABLE_SOURCE | AMBIGUOUS_SOURCE | MASK_UNVERIFIABLE
    recommended_dilation_pixels: int     # Typically 2 px for confirmed stars

@dataclass(frozen=True)
class SpatialAnomalyVettedEvidence:
    """Output contract consumable by FUSION-X."""
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
    vetting_status: str                  # CLEAN_VETTED_ANOMALY | MASK_SUPPRESSED_FALSE_ALARM | UNVERIFIABLE_BACKGROUND
```

---

## 3. End-to-End Propagation Flow

```
Raw SPHEREx FITS Image & Header
        │
        ▼
MOTION-X Track Engine (Extracts Astrometry & Gaia / Catalog Overlays)
        │
        ├── Builds CatalogSourceContext list for the 128x128 patch
        │
        ▼
ASTROVISION Engine (Input: Patch + List[CatalogSourceContext])
        │
        ├── Builds Dynamic Defect Mask: M = Base_Mask & ~Dilated_Sources
        ├── Normalizes patch via RobustLocalNormalizer using M
        ├── Computes Anomaly Map via MaskAwareConv2d using M
        ├── Scores Central Aperture (r <= 2.5 px)
        │
        ▼
FUSION-X Multi-Modal Engine (Input: SpatialAnomalyVettedEvidence + Continuum + Temporal)
        │
        ├── Evaluates Anomaly Validity
        └── Issues Authoritative Discovery Candidate Alert
```

---

## 4. Preservation of Production Contracts

- Production `CandidateRecord` and `FusionEngine.evaluate_source()` remain untouched.
- The interface design will be staged for production implementation under Phase 5 governance.
