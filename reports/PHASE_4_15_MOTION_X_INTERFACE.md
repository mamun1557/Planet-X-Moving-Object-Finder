# SPECTRA-X / F1 — Phase 4, Task 4.15
# MOTION-X / ASTROVISION Mask Interface Specification

**Target Contract:** `CATALOG_MASKED_SPATIAL_EVIDENCE_V1`  
**Target Module:** `spectra_engine.motion_x_mask_interface`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Governance:** Strict Production-Preserving / Isolated Shadow Integration  
**File Link:** [`motion_x_mask_interface.py`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/motion_x_mask_interface.py)  

---

## 1. Architectural Mission

The `motion_x_mask_interface` bridges astrometric catalog databases (Gaia DR3, JPL Horizons, SPHEREx Level-2 Catalogues) curated by MOTION-X into spatial mask requests consumable by ASTROVISION.

### Separation of Concerns
1. **MOTION-X Responsibilities:**
   - Catalog ingestion, ephemeris crossmatching, high-proper-motion tracking.
   - Converts celestial sky coordinates $(\alpha, \delta)$ into local cutout tangent-plane pixel coordinates $(x, y)$.
   - Evaluates astrometric quality (RUWE, parallax significance, proper motion).
2. **ASTROVISION Responsibilities:**
   - Ingests `List[CatalogSourceContext]`.
   - Generates deterministic spatial masks.
   - Evaluates spatial autoencoder reconstruction residuals.
   - Produces authoritative `SpatialAnomalyVettedEvidence` for FUSION-X.

```
       MOTION-X / Pilot Catalogues / Gaia DR3
                        │
                        ▼
┌───────────────────────────────────────────────┐
│              MotionXMaskExtractor             │
│  - extract_sources_from_catalog(...)          │
│  - Tangent-plane projection:                  │
│    dx = -(dra * cos(dec) * 3600) / scale      │
│    dy = +(ddec * 3600) / scale                │
│  - Classifies SourceEvidenceState             │
└───────────────────────┬───────────────────────┘
                        │ List[CatalogSourceContext]
                        ▼
┌───────────────────────────────────────────────┐
│           CatalogAwareSourceMasker            │
│  - Generates combined effective mask          │
│  - AstroVisionShadowAdapter.evaluate_shadow() │
└───────────────────────┬───────────────────────┘
                        │ ShadowEvaluationResult
                        ▼
┌───────────────────────────────────────────────┐
│   create_vetted_evidence_from_shadow(...)     │
│  - Evaluates false alarm suppression          │
│  - Evaluates genuine anomaly preservation     │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│         SpatialAnomalyVettedEvidence          │
│  Contract: CATALOG_MASKED_SPATIAL_EVIDENCE_V1 │
│  (Ready for FUSION-X consumption)             │
└───────────────────────────────────────────────┘
```

---

## 2. Contract Specification: SpatialAnomalyVettedEvidence

```python
@dataclass(frozen=True)
class SpatialAnomalyVettedEvidence:
    """
    Authoritative spatial evidence contract consumable by FUSION-X.
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
    vetting_status: str                         # VettingStatus enum value
    contract_version: str = "CATALOG_MASKED_SPATIAL_EVIDENCE_V1"
    limitation_codes: Tuple[str, ...] = ()
    provenance_metadata: Optional[Dict[str, Any]] = None
```

### VettingStatus Enumeration

| VettingStatus Value | Operational Meaning | FUSION-X Multi-Modal Action |
|---|---|---|
| `CLEAN_VETTED_ANOMALY` | Spatial anomaly detected with off-center catalog sources masked and central aperture uncompromised. | Promoted to high-priority candidate evaluation. |
| `MASK_SUPPRESSED_FALSE_ALARM` | Baseline detected an anomaly, but masking off-center catalog stars dropped peak $\chi^2 < \tau$. | **False positive eliminated; candidate dropped.** |
| `NOMINAL_CLEAN_BACKGROUND` | No anomaly detected; catalog sources safely masked. | Nominal null detection. |
| `UNVERIFIABLE_BACKGROUND` | Background catalog survey footprint missing or unverifiable. | Retained with advisory limitation code; non-confirmatory. |
| `CONFIRMED_STELLAR_SOURCE` | Candidate matches known stationary star at center. | Forwarded to MOTION-X for proper motion vetting. |

---

## 3. Astrometric Coordinate Transformation

The `MotionXMaskExtractor` implements local tangent-plane projection from sky coordinates $(\alpha, \delta)$ to cutout subpixel coordinates $(x, y)$:

$$\Delta \alpha_{\text{arcsec}} = (\alpha_{\text{source}} - \alpha_{\text{target}}) \cdot \cos(\delta_{\text{target}}) \cdot 3600.0$$
$$\Delta \delta_{\text{arcsec}} = (\delta_{\text{source}} - \delta_{\text{target}}) \cdot 3600.0$$
$$x_{\text{cutout}} = x_{\text{target}} - \frac{\Delta \alpha_{\text{arcsec}}}{s_{\text{pixel}}}$$
$$y_{\text{cutout}} = y_{\text{target}} + \frac{\Delta \delta_{\text{arcsec}}}{s_{\text{pixel}}}$$

where $s_{\text{pixel}} = 6.2''\text{/pixel}$ is the nominal SPHEREx pixel scale, and $(x_{\text{target}}, y_{\text{target}}) = (64.0, 64.0)$ is the cutout center.

### Fail-Closed Safeguards
- If `catalog_df` is `None` or empty, `MotionXMaskExtractor` immediately returns a single record with state `MASK_UNVERIFIABLE`.
- If required columns (`ra`, `dec`, `source_id`) are missing, the extractor fails closed with limitation `CORRUPT_CATALOG_SCHEMA`.
- If RUWE $> 1.40$, the state is automatically assigned to `AMBIGUOUS_SOURCE`.

