# Input and Provenance Audit
## Phase 4, Task 4.19C — Controlled Counterpart Validation & Provenance Verification

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Audit Date:** 2026-11-08  
**Parent Task:** Phase 4 Tasks 4.12–4.19B  

---

### 1. Catalog Identifier & Namespace Uniqueness Audit
- **Gaia DR3 Namespace:** Unique integer 64-bit identifiers (`source_id`). Verification confirmed zero intra-catalog duplicates among the 1,176,689 Gaia sources queried across evaluation footprints.
- **CatWISE2020 Namespace:** NASA/IPAC IRSA unique source strings (`source_name`). Verification confirmed zero duplicates across the 168,780 CatWISE counterparts.
- **2MASS PSC Namespace:** Sexagesimal celestial designations (`designation`). Verification confirmed 100% uniqueness among 26,391 sources.
- **Multi-Catalog Source Accounting:** In accordance with Task 4.19C instructions, sources from different catalogs are tracked independently by catalog namespace and are **not** double-counted as independent physical sources when assessing local stellar density.

---

### 2. Astrometric Coordinate Frames & Epoch Propagation
- **Reference Frame:** All coordinates are validated on the International Celestial Reference System (ICRS) / J2000.
- **Proper Motion Propagation:**
  - Applied rigorously to all Gaia DR3 sources with non-null 5-parameter astrometric solutions:
    $$\Delta \alpha = \frac{\mu_{\alpha*} \cdot \Delta t}{\cos(\delta)} \times \frac{1}{3600 \times 1000}$$
    $$\Delta \delta = \mu_\delta \cdot \Delta t \times \frac{1}{3600 \times 1000}$$
  - Reference baseline: Gaia J2016.0 -> SPHEREx Flight Epoch 2026.5496 ($\Delta t = 10.5496\text{ years}$).
  - For sources lacking measured proper motions (2-parameter astrometry, 2MASS PSC static snapshots), coordinates remain at their catalog reference epochs. The astrometric displacement over 10–26 years for typical distant background stars is $< 0.1''$, which is $< 0.02\text{ native SPHEREx pixels}$ ($6.215''/\text{px}$).

---

### 3. Exact Footprint WCS Ingestion Verification
- Astropy WCS transformation (`wcs.all_world2pix`) was evaluated directly from the primary Level-2 FITS headers (`level2_*.fits`).
- The bounding box condition is exact: $0.0 \le x < 128.0$ and $0.0 \le y < 128.0$.
- No circular approximations were used for counterpart identification. All sources lie physically within the evaluated pixel array.

---

### 4. Anomaly Centroid Coordinates vs. Cutout Center
- **Anomaly Centroid (`model_recovered_sub_x`, `model_recovered_sub_y`):**
  - Authoritatively recorded by ASTROVISION during evaluation inference.
  - Represents the exact sub-pixel peak anomaly coordinate within the central evaluation aperture.
  - Mean centroid position across controls: $(64.23, 63.97)$.
  - Average offset from geometric center $(64.0, 64.0)$ is $1.37\text{ pixels}$ ($8.5''$).
- **Cutout Geometric Center (`64.0, 64.0`):**
  - The geometric boresight where artificial point sources are injected.
- **Audit Rule:** Both reference points were independently evaluated. The anomaly centroid is the scientifically relevant reference for false alarm hypothesis testing, while the cutout center is preserved for comparison.

---

### 5. Blind Evaluation Cohort & False-Positive Immutability
- **Evaluation Cohort Integrity:** All 1,500 evaluation trials (500 controls, 500 point injections, 500 extended injections) remain 100% identical in composition, parameters, and partition labels.
- **Baseline False Positives:** Exactly 45 false positives are identified, matching Tasks 4.11, 4.12, 4.15, and 4.18 bit-for-bit.
- **Blind Evaluation Protection:** Zero blind evaluation labels were altered or unblinded.
