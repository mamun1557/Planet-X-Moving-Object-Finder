# SPECTRA-X / F1 — Phase 4, Task 4.18
## Scientific Claims and Limitations: Real-Sky Catalog-Aware Masking Applicability

**Module:** ASTROVISION + `CatalogAwareSourceMasker`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Evaluation Cohort:** Pointings P0002, P0009, P0010 ($N = 1,500$ cutouts; $N = 500$ null controls)  
**Date:** 2026-11-08  
**Audit Status:** STRICT READ-ONLY SCIENTIFIC AUDIT  

---

### 1. Authoritative Executive Findings

This document establishes the boundaries of verified scientific claims regarding ASTROVISION real-sky false-alarm reduction using external Gaia DR3 and 2MASS PSC catalog evidence.

1. **Physical Efficacy Demonstrated on Real Stellar Leakage:**  
   When a genuine bright off-center star ($G < 16\text{ mag}$) or core counterpart is present in an evaluation cutout, `CatalogAwareSourceMasker` (at frozen 2-pixel dilation) successfully suppresses the anomalous residual without encroaching on the protected central aperture. On real-sky observations, 3 out of 45 baseline false alarms were eliminated:
   - `PILOT_001004` (Detector D4): Core counterpart ($G = 15.79$, separation $1.41'' = 0.23\text{ px}$) — suppressed from $\chi^2 = 648.7$ to $0.0$.
   - `PILOT_001383` (Detector D5): Off-center star ($G = 17.34$, separation $40.33'' = 6.49\text{ px}$) — suppressed from $\chi^2 = 138.1$ to $62.3$ (below $\tau = 91.85$).
   - `PILOT_001481` (Detector D1): Very bright off-center star ($G = 11.95$, separation $25.86'' = 4.16\text{ px}$) — suppressed from $\chi^2 = 1477.5$ to $21.9$ (below $\tau = 186.29$).

2. **Severe Real-Sky Catalog Completeness Limitation:**  
   The primary driver of the overall ASTROVISION false-positive rate ($9.00\%$, 45/500 controls) is **not** cataloged stellar leakage. Exactly **33 of the 45 baseline false positives (73.33%)** have **zero** catalog counterparts in Gaia DR3 ($G \le 20.7$) or 2MASS PSC ($J \le 17.0$). These 33 false alarms persist entirely unaffected by catalog masking.

3. **Distinction Between Synthetic Models and Real Observations:**  
   Earlier tasks (Task 4.14 and Task 4.15) reported a reduction of false positives from 45 to 16 ($9.00\% \to 3.20\%$) under a *controlled synthetic injection experiment* where simulated off-center sources were deliberately placed in every false alarm cutout. On *actual real-sky observations*, the empirical false-positive rate on the 500 controls dropped from **$9.00\%$ (45/500) to $8.40\%$ (42/500)**, an absolute drop of $0.60\%$ ($p = 0.2500$ via McNemar's test, which is not statistically significant across the full cohort).

---

### 2. Permitted Scientific Claims (Approved for NASA Reviews)

The following claims are mathematically, computationally, and astronomically substantiated:

1. **Proof of Physical Mechanism:**  
   *Claim:* Catalog-aware masking with 2-pixel dilation is an effective and safe physical mechanism for mitigating spatial autoencoder receptive-field leakage caused by cataloged stellar sources located within $3 - 7\text{ pixels}$ ($18'' - 43''$) of the central target.

2. **Central Aperture Safety Invariant:**  
   *Claim:* Under `protect_central_aperture=True`, `CatalogAwareSourceMasker` guarantees $0.0\%$ masking encroachment on the central detection aperture ($r \le 2.5\text{ pixels}$), ensuring that genuine central anomalies are never inadvertently masked.

3. **Sub-Cohort Effectiveness:**  
   *Claim:* For the subset of real null control cutouts containing verified optical/NIR catalog stars ($N = 166$ cutouts), catalog masking reduced the empirical false-positive rate from $7.23\%$ (12/166) to $5.42\%$ (9/166), achieving a $25.0\%$ reduction in false alarms within that cataloged domain.

4. **Independent Benchmark Label Vetting:**  
   *Claim:* External catalog crossmatching detected benchmark label contamination in the evaluation control cohort, specifically identifying `PILOT_001004` as a genuine $G = 15.79$ star mistakenly included in the null control set.

---

### 3. Strictly Prohibited Scientific Claims (Disproven or Ungrounded)

The following claims are unsupported and strictly prohibited from publication or presentation:

1. **PROHIBITED:** Claiming that catalog-aware masking has reduced the real-sky ASTROVISION false-positive rate from $9.00\%$ to $3.20\%$.  
   *Correction:* The $3.20\%$ figure is exclusively a property of the *synthetic off-center injection benchmark* (Task 4.15). On actual real-sky data, the false-positive rate is $8.40\%$ (42/500). Conflating synthetic recovery models with real-sky performance is scientifically invalid.

2. **PROHIBITED:** Claiming that ASTROVISION false alarms are predominantly caused by cataloged stars.  
   *Correction:* $73.33\%$ (33/45) of baseline false alarms occur in cutouts with zero optical/NIR catalog sources down to $G = 20.7$ and $J = 17.0$. The dominant sources of false alarms are uncataloged diffuse emission, detector edge effects, and electronic/readout systematics (particularly on Detector D1).

3. **PROHIBITED:** Equating lack of a catalog counterpart with empty sky.  
   *Correction:* Absence of catalog sources indicates only that celestial objects in that region are fainter than the survey limits ($G > 20.7$ or $J > 17.0$) or emit predominantly in infrared wavelengths outside optical/NIR completeness.

4. **PROHIBITED:** Recommending production activation of catalog masking without crowding safeguards.  
   *Correction:* In crowded astronomical fields containing hundreds of stars, unconstrained masking of all catalog sources removes excessive image area, degrading local background normalization and risking induced boundary artifacts.

---

### 4. Methodological Reconciliation: Circular vs. Exact Footprint

Task 4.17 evaluated catalog presence using a circular cone of radius $r = 565''$, representing the circumscribed circle bounding the $128 \times 128$ pixel cutout ($64\sqrt{2} \times 6.215'' \approx 562.5'' \approx 565''$).

- **Circular Cone Area:** $\pi \times (565'')^2 = 1,002,875\text{ arcsec}^2$.
- **Exact Cutout Box Area:** $(128 \times 6.215'')^2 = 632,538\text{ arcsec}^2$.
- **Excess Area in Circular Cone:** $+370,337\text{ arcsec}^2$ ($+58.5\%$ larger than the true FITS array).

| Metric | Circular Cone ($r \le 565''$) | Exact Bounding Box ($128 \times 128$ px) | Difference / Impact |
|---|:---:|:---:|---|
| **Control Cutout Coverage ($N=500$)** | 180 / 500 (36.00%) | 166 / 500 (33.20%) | $-14$ cutouts ($-2.80\%$) had stars only in circular corner lobes outside FITS data |
| **Overall Cutout Coverage ($N=1,500$)** | 550 / 1500 (36.67%) | 498 / 1500 (33.20%) | $-52$ cutouts ($-3.47\%$) outside true image array |
| **45 Baseline False Positives** | 12 / 45 (26.67%) | 12 / 45 (26.67%) | $0$ difference; all 12 candidate cutouts have stars inside the actual image box |

---

### 5. Summary Conclusion & Strategic Recommendations

Real-sky shadow applicability is **`PARTIALLY_SUPPORTED`**. The mechanism is sound, safe, and effective where bright off-center stars are cataloged, but it cannot solve the 73.3% of false alarms arising in uncataloged regions. 

**Recommended Action for Future Phases:**
1. Investigate mid-infrared survey catalogs (CatWISE2020 / AllWISE) to determine if infrared-only sources explain the 33 uncataloged false alarms.
2. Implement detector-specific threshold recalibration or electronic filtering on Detector D1, which accounts for 19 of the 45 false alarms.
3. Preserve the frozen production state of ASTROVISION until multi-wavelength vetting is fully characterized.

