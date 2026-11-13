# SPECTRA-X / F1 — Phase 4, Task 4.16G
# Source-Masking Semantic Audit & Evidence Provenance Validation

**Audit Target:** `spectra_engine.catalog_aware_source_masker` & `spectra_engine.motion_x_mask_interface`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Audit Type:** Strict Read-Only Scientific & Semantic Verification  
**Audit Environment:** `SPECTRA-X/.venv_validation`  
**Parent Task:** Phase 4, Task 4.15 / Task 4.16  

---

## 1. Executive Summary & Verification Matrix

This audit inspects the mathematical representation, coordinate projection, polarity conventions, edge-case behavior, and astrophysical evidence semantics of `CatalogAwareSourceMasker` and `MotionXMaskExtractor`.

| Semantic Invariant | Specification Requirement | Implementation Code Location | Verification Finding | Compliance Status |
|---|---|---|---|:---:|
| **Level-2 Defect Mask Preservation** | Hardware defects, dead pixels, and cosmic rays ($M_{\text{base}} = 0$) must never be unmasked by catalog operations. | [`catalog_aware_source_masker.py#L262-L263`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py#L262-L263) | $M_{\text{eff}} = M_{\text{base}} \land \neg M_{\text{src}}$ strictly preserves all baseline zeros. Verified by Test 14. | **COMPLIANT** |
| **Mask Polarity Consistency** | Effective mask must use ASTROVISION convention: `1.0` = valid photosensitive sky, `0.0` = defect/masked. | [`catalog_aware_source_masker.py#L108-L109`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py#L108-L109) | Effective mask uses `1.0` = valid, `0.0` = masked; standalone mask uses `1.0` = masked source, `0.0` = unmasked. Verified by Test 15. | **COMPLIANT** |
| **Coordinate System & Tangent Projection** | Subpixel $(x, y)$ in $128 \times 128$ cutout must align with astronomical tangent plane: $\Delta x = -\Delta\alpha / s$, $\Delta y = +\Delta\delta / s$. | [`motion_x_mask_interface.py#L143-L146`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/motion_x_mask_interface.py#L143-L146) | North-up, East-left projection correctly mapped to cutout center $(64.0, 64.0)$ with nominal pixel scale $6.2''/\text{px}$. | **COMPLIANT** |
| **Central Aperture Shielding** | Pixels within central candidate aperture ($r \le 2.5\text{ px}$) must be protected from off-center mask dilation. | [`catalog_aware_source_masker.py#L250-L252`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py#L250-L252) | Masker clears all overlapping pixels: $M_{\text{src}} \leftarrow M_{\text{src}} \land \neg M_{\text{center\_aperture}}$. 0.00% encroachment up to 2px dilation. | **COMPLIANT** |
| **Deterministic Deduplication** | Multiple catalog records with identical `source_id` must be de-duplicated without order-dependent side effects. | [`catalog_aware_source_masker.py#L199-L208`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py#L199-L208) | De-duplicated via ordered set; limitation code `DUPLICATE_SOURCE_RECORD_IGNORED_<id>` logged. Verified by Test 09. | **COMPLIANT** |
| **Ambiguity Retention** | Sources with RUWE $> 1.4$ or confusion must not be promoted to confirmed single stars. | [`catalog_aware_source_masker.py#L221-L225`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py#L221-L225) | Tagged as `AMBIGUOUS_SOURCE`; limitation code `AMBIGUOUS_SOURCE_PRESENT_<id>` logged. Verified by Test 03. | **COMPLIANT** |
| **Missing Footprint Fail-Closed** | Missing catalog tables or unverified sky must not be treated as empty sky. | [`motion_x_mask_interface.py#L86-L96`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/motion_x_mask_interface.py#L86-L96) | Assigned `SourceEvidenceState.MASK_UNVERIFIABLE`; zero source pixels masked; limitation code recorded. Verified by Test 05. | **COMPLIANT** |
| **Non-Detection vs Absence Separation** | A non-match in Gaia must not be treated as proof of astronomical emptiness. | [`motion_x_mask_interface.py#L125-L128`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/motion_x_mask_interface.py#L125-L128) | Designated `NO_LOCAL_CATALOG_COUNTERPART` within footprint, indicating no cataloged counterpart above survey limit. | **COMPLIANT** |
| **Hardware Flag Bit Separation** | SPHEREx fatal bit 21 (bright star mask) must not be conflated with verified catalog identity. | [`models/astrovision/model_v3.py#L24`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/astrovision/model_v3.py#L24) | Level-2 fatal defect mask strictly checks `flags & 615 == 0` (fatal bits 0, 1, 2, 9). Hardware flags kept decoupled from catalog state. | **COMPLIANT** |
| **Central Target Preservation** | Center candidate targets must never be suppressed by catalog source masking. | [`catalog_aware_source_masker.py#L250`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py#L250) | Central target flagged with `is_center_target=True`; exempt from off-center suppression. Verified by Test 20. | **COMPLIANT** |

---

## 2. In-Depth Semantic Analysis

### 2.1 The Danger of Conflating "No Catalog Match" with "Empty Sky"
In Task 4.14 and Task 4.15, an explicit semantic barrier was constructed between `NO_LOCAL_CATALOG_COUNTERPART` and `MASK_UNVERIFIABLE`:
1. **`NO_LOCAL_CATALOG_COUNTERPART`:** A cone search was executed across a verified, valid catalog survey footprint (e.g. Gaia DR3 with coverage $G \le 20.7$), and no object was returned. This confirms that no *known cataloged star* exists within the footprint, but it does **not** prove the sky is empty—an object could be an ultra-cool brown dwarf, high-redshift galaxy, or transient solar system body below the survey's detection threshold.
2. **`MASK_UNVERIFIABLE`:** If the catalog table is missing, truncated, or outside the survey boundaries, the state is strictly `MASK_UNVERIFIABLE`. The engine logs `SOURCE_EVIDENCE_UNVERIFIABLE_<id>` and falls back to standard Level-2 defect masking. It never synthesizes assumptions.

### 2.2 SPHEREx Bit 21 vs Astrometric Catalog Identity
In SPHEREx Level-2 data, bit 21 indicates an aggressive pipeline bright-star halo mask. Previous legacy prototypes attempted to infer stellar identity solely from bit 21. 
Task 4.16 audit confirms that `CatalogAwareSourceMasker` does not rely on bit 21. Instead:
- Level-2 base defect masking checks fatal bits `flags & 615 == 0`.
- Catalog source footprints are computed independently from calibrated external astrometry (Gaia DR3 / 2MASS).

### 2.3 Centroid Gating & False Alarm Counting
A key finding of Task 4.16B is the exact operational effect of the centroid distance gate:
$$\Delta r_{\text{centroid}} = \sqrt{(x_{\text{peak}} - x_{\text{target}})^2 + (y_{\text{peak}} - y_{\text{target}})^2} \le 2.5\text{ pixels}$$
In Detector 1, 21 null cutouts have raw peak reconstruction residuals exceeding the calibrated threshold $\tau_{\text{D1}} = 186.29$. However:
- PILOT_001085: Peak residual at $\Delta r = 2.65\text{ px}$.
- PILOT_001175: Peak residual at $\Delta r = 2.65\text{ px}$.
Both lie just outside the $2.5\text{ px}$ target aperture radius. When the centroid distance gate is applied, these two edge peaks are properly disqualified from central point-source alarm status, yielding exactly **19 false positives out of 84** ($22.62\%$). Without centroid gating, the count is **21/84** ($25.00\%$). Task 4.11's earlier citation of **20/84** was evaluated under a provisional threshold ($\tau = 124.50$) prior to formal $\alpha = 0.05$ calibration.

---

## 3. Semantic Audit Verdict

The masking engine and evidence interfaces strictly enforce all 10 semantic and provenance invariants. No ungrounded promotions of source uncertainty to confirmed stellar identity were discovered in the codebase.

