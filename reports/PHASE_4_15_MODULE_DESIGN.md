# SPECTRA-X / F1 — Phase 4, Task 4.15
# Module Design Specification: CatalogAwareSourceMasker

**Target Module:** `spectra_engine.catalog_aware_source_masker`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Parent Tasks:** Phase 4 Task 4.12, Task 4.13, Task 4.14  
**Governance:** Strict Production-Preserving / Isolated Shadow Integration  
**File Link:** [`catalog_aware_source_masker.py`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py)  

---

## 1. Architectural Mission & Scope

The `CatalogAwareSourceMasker` module provides a production-grade, provenance-preserving spatial masking engine for astronomical imaging cutouts ($128 \times 128\text{ pixels}$) in the SPECTRA-X pipeline. 

### Core Scientific Problem
Diagnostic audits in Tasks 4.12, 4.13, and 4.14 established that ASTROVISION V3's elevated empirical false-positive rate (9.00% overall; 23.81% in Detector 1) is predominantly driven by **off-center cataloged stellar sources** ($d \le 31\text{ px}$ from the center). Because the convolutional autoencoder possesses an effective receptive field of $62 \times 62\text{ pixels}$ ($R = 31\text{ px}$), high reconstruction residuals from bright off-center stars propagate inward through transposed convolutional layers, artificially elevating the central aperture's peak $\chi^2$ anomaly score and causing false alarms on pristine null sky.

### Design Solution
`CatalogAwareSourceMasker` generates deterministic binary masks covering confirmed off-center catalog sources. By ingesting these masks into ASTROVISION's `MaskAwareConv2d` layers and `RobustLocalNormalizer`, off-center residual leakage is neutralized without altering the frozen model weights, checkpoints, or calibrated detection thresholds ($\tau$).

```
Raw Cutout Image + Flags + Variance
            │
            ▼
┌───────────────────────────────────────┐
│       CatalogAwareSourceMasker        │
│  - Ingests CatalogSourceContext list  │
│  - Projects coordinates to cutout     │
│  - Synthesizes circular core masks    │
│  - Applies binary dilation (d=2 px)   │
│  - Enforces Central Aperture Shield   │
│    (r <= 2.5 px protected)            │
└───────────────────┬───────────────────┘
                    │ Combined Effective Mask (M_eff = M_base & ~M_src)
                    ▼
┌───────────────────────────────────────┐
│        ASTROVISION V3 Engine          │
│  - RobustLocalNormalizer (using M_eff)│
│  - MaskAwareConv2d (using M_eff)      │
│  - Central Aperture Anomaly Scorer    │
└───────────────────┬───────────────────┘
                    │
                    ▼
    SpatialAnomalyVettedEvidence (to FUSION-X)
```

---

## 2. Mask Polarity & Representation Conventions

A critical requirement of the SPECTRA-X architecture is strict polarity consistency across the entire imaging pipeline:

| Representation | Variable Name | Polarity Definition | Pipeline Usage |
|---|---|---|---|
| **ASTROVISION Effective Mask** | `combined_effective_mask` | `1.0` = **Valid Photosensitive Sky**<br>`0.0` = **Defect or Masked Source** | Passed to `RobustLocalNormalizer` and `MaskAwareConv2d` |
| **Level-2 Base Defect Mask** | `original_defect_mask` | `1.0` = **Valid Sky**<br>`0.0` = **Hardware / Cosmic Ray Defect** | Extracted from raw FITS `FLAGS` (`flags & 615 == 0`) |
| **Standalone Source Mask** | `catalog_source_mask` | `1.0` = **Source Footprint Masked**<br>`0.0` = **Unmasked Background** | Diagnostic export and coverage tracking |

### Mathematical Combination Rule
$$\mathbf{M}_{\text{effective}} = \mathbf{M}_{\text{base}} \land \left(\neg \mathbf{M}_{\text{source}}\right)$$
In float representation:
$$\mathbf{M}_{\text{effective}}[i, j] = \begin{cases} 1.0 & \text{if } \mathbf{M}_{\text{base}}[i, j] > 0.5 \text{ and } \mathbf{M}_{\text{source}}[i, j] < 0.5 \\ 0.0 & \text{otherwise} \end{cases}$$

---

## 3. Algorithmic Steps & Complexity

The `CatalogAwareSourceMasker.generate_mask(request: CatalogMaskRequest)` method executes deterministically in $\mathcal{O}(K \cdot H \cdot W)$ time, where $K$ is the number of catalog sources ($K \le 50$) and $(H, W) = (128, 128)$:

1. **Parameter Validation:**
   - Verifies `dilation_radius_pixels` $\in \{0, 1, 2, 3, 5\}$. Non-integer, negative, NaN, Inf, or unapproved values immediately raise `ValueError`.
   - Verifies cutout shape $0 < H, W \le 1024$ and finiteness of target coordinates.
2. **Base Defect Mask Normalization:**
   - Checks array dimensions. Converts float/int masks to binary $\{0.0, 1.0\}$.
3. **Source Deduplication:**
   - Filters duplicate records with identical `source_id`, logging `DUPLICATE_SOURCE_RECORD_IGNORED_<id>`.
4. **Coordinate Resolution & Bounds Checking:**
   - Subpixel $(x, y)$ coordinates are ingested directly or transformed via WCS.
   - Out-of-bounds sources ($x < -32$ or $x > W+31$) are safely skipped with limitation code `SOURCE_OUT_OF_BOUNDS_<id>`.
   - NaN / Inf coordinates fail closed with `COORDINATE_PROJECTION_FAILED_<id>`.
5. **Core Mask Generation & Dilation:**
   - Synthesizes circular mask of radius $R_{\text{core}} = 2.5\text{ px}$ around $(x_k, y_k)$.
   - Applies morphological binary dilation using `scipy.ndimage.binary_dilation` with $D \in \{0, 1, 2, 3, 5\}$.
6. **Central Aperture Shielding:**
   - When `protect_central_aperture=True`, all pixels within the central candidate aperture ($r \le 2.5\text{ px}$ from $(x_{\text{target}}, y_{\text{target}})$) are explicitly cleared from off-center masks:
     $$\mathbf{M}_{\text{source}} \leftarrow \mathbf{M}_{\text{source}} \land \left(\neg \mathbf{M}_{\text{center\_aperture}}\right)$$
   - This guarantees that genuine central anomalies are never suppressed by nearby dilated masks.
7. **Provenance & Metric Computation:**
   - Computes total valid pixels, masked area fraction, central encroachment status, and attaches full pipeline provenance.

---

## 4. Dilation Radius Optimization

Empirical benchmark experiments (Tasks 4.14 and 4.15) evaluated dilation radii from $0\text{ px}$ to $5\text{ px}$:

| Dilation Level | Mean Masked Area | Central Encroachment Rate | False Alarm Suppression | Point-Source Recovery | Recommendation Status |
|---|---|---|---|---|---|
| `UNMASKED` | 0.42% | 0.00% | 0.0% (Baseline FPR 9.00%) | 34.80% | High FPR Defect |
| `0 px` (Core only) | 1.84% | 0.00% | 31.1% (FPR 6.20%) | 34.80% | Under-masked (PSF wings leak) |
| `1 px` | 2.76% | 0.00% | 53.3% (FPR 4.20%) | 34.80% | Sub-optimal wing suppression |
| **`2 px`** | **3.79%** | **0.00%** | **64.4% (FPR 3.20%)** | **34.80%** | **AUTHORITATIVE OPTIMUM** |
| `3 px` | 5.42% | 0.20% | 73.3% (FPR 2.40%) | 34.60% | Minor aperture encroachment |
| `5 px` | 9.15% | 1.40% | 82.2% (FPR 1.60%) | 33.60% | Over-masked (suppresses signal) |

**Conclusion:** `dilation_radius_pixels = 2` achieves the optimal scientific tradeoff: it suppresses $64.4\%$ of empirical false alarms, drops overall FPR from $9.00\%$ to $3.20\%$ (well below the $5.00\%$ mission ceiling), preserves $100\%$ of detected central anomalies, and consumes less than $3.8\%$ of cutout sky area.

---

## 5. Fail-Closed Governance

The module implements strict fail-closed safety semantics:
- Corrupt or missing catalog data emits `MASK_UNVERIFIABLE` and reverts to standard Level-2 defect masking.
- Non-matching coordinates in Gaia are recorded as `NO_LOCAL_CATALOG_COUNTERPART` and never treated as verified empty sky.
- All operations are stateless, side-effect free, and thread-safe.

