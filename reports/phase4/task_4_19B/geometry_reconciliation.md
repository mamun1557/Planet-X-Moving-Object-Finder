# SPECTRA-X / F1 — Phase 4, Task 4.19B
## Geometry and Provenance Reconciliation Report

**Pipeline Build:** `l2b-v27-2026-222`  
**Parent Tasks:** Phase 4 Tasks 4.17, 4.18, 4.18-SKY, 4.19A  
**Module:** ASTROVISION + Spatial Sky Mapping + External Catalog Crossmatching  
**Target Cohort:** Pointings P0002, P0009, P0010 (1,500 total evaluation cutouts: 1,000 real candidates, 500 null controls)  
**Status:** COMPLETE & EMPIRICALLY AUDITED  

---

### 1. Executive Reconciliation & Historical Root Cause

A strict geometric and provenance audit of the evaluation cohort and catalog acquisition pipelines was conducted across Tasks 4.17, 4.18, 4.18-SKY, and 4.19A.

#### Authoritative Findings:
1. **Historical Undersized Query Provenance (Task 4.17):**
   - In `scripts/acquisition/execute_phase_4_17_acquisition.py`, line 125–135 defined `field_clusters` with `radius_deg: 2.30` to `2.55`.
   - However, in line 194 of the same script, the actual ADQL query submitted to the Heidelberg ARI Gaia TAP endpoint hardcoded an undersized cone:
     ```sql
     WHERE 1=CONTAINS(POINT('ICRS', g.ra, g.dec), CIRCLE('ICRS', {c_ra:.4f}, {c_dec:.4f}, 0.85))
     ```
   - Each query also enforced `SELECT TOP 10000`, truncating high-density fields.
   - For 2MASS PSC Gator queries (lines 277–284), the query radius was restricted to only $360'' = 0.10^\circ$ (6 arcminutes) around field centers.
   - Outside the $0.85^\circ$ cones, Task 4.17 relied solely on legacy pilot archival CSVs (`pilot_{p}_field{f}_gaia_dr3.csv`), which had been generated with a sparse `TOP 2500` limit.
2. **Solid Angle Mismatch:**
   - SPHEREx focal plane array spans $3.52^\circ \times 3.52^\circ$ (active solid angle $\approx 12.40\text{ deg}^2$, corner radius $r_{\text{max}} \approx 2.49^\circ$).
   - The Task 4.17 query cone of $r = 0.85^\circ$ encompassed a solid angle of only $\pi \times (0.85)^2 = 2.270\text{ deg}^2$ (covering only **18.31%** of the detector array).
   - Consequently, **77.87% (1,168 / 1,500)** of all evaluation cutouts lay outside the $0.85^\circ$ query cone!
   - For the 500 null controls: exactly **113 (22.60%)** were inside the cone, while **387 (77.40%)** were outside.
   - For the 45 ASTROVISION baseline false alarms: only **6 (13.33%)** were inside the cone, while **39 (86.67%)** were outside.
3. **Cutout Bounding Circle Approximation vs. Exact Pixel Footprint:**
   - In Task 4.17, lines 453–455 approximated a cutout footprint as a circle of radius $565.0''$:
     ```python
     r_cutout_rad = np.deg2rad(565.0 / 3600.0)
     ```
   - A $128 \times 128$ pixel cutout with pixel scale $6.2285''/\text{px}$ is a square of $797.2'' \times 797.2''$ (area $= 635,600\text{ arcsec}^2 \approx 0.0490\text{ deg}^2$).
   - A circle of radius $565.0''$ has an area of $\pi \times (565)^2 = 1,002,875\text{ arcsec}^2 \approx 0.0774\text{ deg}^2$.
   - The $565.0''$ circular approximation overestimates the true cutout area by **$1.58 \times$ ($+57.8\%$)**, erroneously including sources in the circular corners beyond the physical pixel grid ($x < 0$, $x \ge 128$, $y < 0$, or $y \ge 128$).
   - Task 4.19B mandates using the **exact WCS-derived pixel box** for all empirical coverage calculations.

---

### 2. Geometry Reconciliation Table

The table below reconciles all geometric representations utilized across the pipeline:

| Geometry Entity | Angular Size / Dimensions | Solid Angle (deg²) | Intended Scope / Definition | Task 4.19B Geometric Verification |
|---|---|---:|---|---|
| **Exact 128×128 Cutout Box** | $797.2'' \times 797.2''$ ($0.221^\circ \times 0.221^\circ$) | **0.0490 deg²** | True evaluated SPHEREx science image array; bounded by $[0, 128) \times [0, 128)$ in local WCS coordinates. | **Authoritative Ground Truth:** Derived from Level-2 FITS WCS via Astropy `all_world2pix`. |
| **565 arcsec Circular Approximation** | Radius $r = 565.0''$ ($0.1569^\circ$, diameter $1,130''$) | **0.0774 deg²** | Circumscribed circle bounding the $128 \times 128$ square cutout. Used in Task 4.17 as a KD-tree ball query. | **Over-inclusive by 1.58× (+57.8% area):** Useful only as a conservative enclosing filter, NOT for final coverage. |
| **0.85° Cone Query** | Radius $r = 0.85^\circ$ ($3,060''$, diameter $1.70^\circ$) | **2.270 deg²** | Historical TAP query cone used in Task 4.17 centered on field clusters. Enclosed only 18.31% of focal plane. | **Historically Undersized:** Proven responsible for Task 4.17's 33.20% coverage ceiling. |
| **2.50° Cone Query** | Radius $r = 2.50^\circ$ ($9,000''$, diameter $5.00^\circ$) | **19.635 deg²** | Minimum circular cone centered on pointing boresight that encloses the complete $3.52^\circ \times 3.52^\circ$ array. | **Complete Enclosing Geometry:** Encloses 100.0% (1,500 / 1,500) of all evaluated cutouts across all 9 fields. |
| **Full Detector Footprint** | $2040 \times 2040$ pixels ($3.529^\circ \times 3.529^\circ$) | **12.457 deg²** | Physical field of view of an individual SPHEREx detector channel (D1–D6) in Level-2 Build `l2b-v27-2026-222`. | **WCS Reconstructed:** Verified across all 72 FITS headers in Task 4.18-SKY with WCS error $< 10^{-6}\text{ px}$. |

---

### 3. Spatial Separation Audit Across 9 Evaluation Fields

For all 1,500 cutouts, angular separations from their respective field centers were computed:

$$\theta = 2 \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \delta}{2}\right) + \cos \delta_1 \cos \delta_2 \sin^2\left(\frac{\Delta \alpha}{2}\right)}\right)$$

| Pointing | Field Index | Detector Channels | Cutout Count (N) | Separation Range (min – max) | Cutouts inside 0.85° Cone | Cutouts inside 2.50° Cone |
|---|---|---|---:|---|---:|---:|
| **P0002** | Field 1 | D1, D4 | 168 | $0.09^\circ\text{ -- }2.26^\circ$ | 38 / 168 (22.6%) | 168 / 168 (100.0%) |
| **P0002** | Field 2 | D2, D5 | 168 | $0.14^\circ\text{ -- }2.09^\circ$ | 41 / 168 (24.4%) | 168 / 168 (100.0%) |
| **P0002** | Field 3 | D3, D6 | 168 | $0.08^\circ\text{ -- }2.38^\circ$ | 31 / 168 (18.5%) | 168 / 168 (100.0%) |
| **P0009** | Field 1 | D1, D4 | 168 | $0.13^\circ\text{ -- }2.13^\circ$ | 37 / 168 (22.0%) | 168 / 168 (100.0%) |
| **P0009** | Field 2 | D2, D5 | 168 | $0.11^\circ\text{ -- }2.16^\circ$ | 41 / 168 (24.4%) | 168 / 168 (100.0%) |
| **P0009** | Field 3 | D3, D6 | 168 | $0.09^\circ\text{ -- }2.25^\circ$ | 37 / 168 (22.0%) | 168 / 168 (100.0%) |
| **P0010** | Field 1 | D1, D4 | 165 | $0.13^\circ\text{ -- }2.13^\circ$ | 38 / 165 (23.0%) | 165 / 165 (100.0%) |
| **P0010** | Field 2 | D2, D5 | 165 | $0.04^\circ\text{ -- }2.28^\circ$ | 31 / 165 (18.8%) | 165 / 165 (100.0%) |
| **P0010** | Field 3 | D3, D6 | 162 | $0.17^\circ\text{ -- }2.16^\circ$ | 38 / 162 (23.5%) | 162 / 162 (100.0%) |
| **TOTAL** | **All 9 Fields** | **D1–D6** | **1,500** | **0.04° – 2.38°** | **332 / 1,500 (22.13%)** | **1,500 / 1,500 (100.00%)** |

#### Cohort Partition Breakdown:
- **Null Controls (N = 500):** Exactly 113 (22.60%) were inside the 0.85° cone; 387 (77.40%) were outside. 100.0% are inside 2.50°.
- **Real Injections (N = 1,000):** Exactly 219 (21.90%) were inside the 0.85° cone; 781 (78.10%) were outside. 100.0% are inside 2.50°.
- **Baseline False Positives (N = 45):** Exactly 6 (13.33%) were inside the 0.85° cone; 39 (86.67%) were outside. 100.0% are inside 2.50°.

---

### 4. Methodological Invariants for Task 4.19B Execution

To prevent geometric conflation and guarantee exact scientific reproducibility:
1. **No Circular Approximations for Evaluation:** While a circumscribed circle ($r = 0.157^\circ$) is valid as a high-recall enclosing filter during candidate ingestion, every candidate source must be mapped via the cutout's specific FITS WCS to pixel coordinates $(x, y)$.
2. **Exact Boundary Criterion:** A source is classified as inside the cutout if and only if:
   $$0.0 \le x_{\text{pix}} < 128.0 \quad \text{and} \quad 0.0 \le y_{\text{pix}} < 128.0$$
3. **Astrometric Epoch Consistency:** Gaia DR3 coordinates (epoch J2016.0) and CatWISE2020 coordinates (epoch J2015.5) must be propagated using proper motions to SPHEREx observation epoch **2026.5496** before evaluating pixel positions.
4. **Historical Preservation:** The 33.20% coverage figure reported in Task 4.17 remains an immutable empirical record of the legacy query configuration and must not be altered.

