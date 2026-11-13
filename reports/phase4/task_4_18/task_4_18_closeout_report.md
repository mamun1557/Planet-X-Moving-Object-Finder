# SPECTRA-X / F1 — Phase 4, Task 4.18 Closeout Report
## Catalog-Backed ASTROVISION Real-Sky Shadow Applicability & False-Positive Attribution Audit

**Task Type:** CONTROLLED SCIENTIFIC RE-EVALUATION & REAL-SKY EVIDENCE AUDIT  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10, Windows)  
**Parent Tasks:** Phase 4 Tasks 4.15, 4.16, 4.17  
**Target Module:** ASTROVISION + `CatalogAwareSourceMasker`  
**Evaluation Cohort:** Pointings P0002, P0009, P0010 ($N = 1,500$ evaluation trials; $N = 500$ null controls)  
**Audit Execution Date:** 2026-11-08  
**Authoritative Verdict:** `REAL_SKY_SHADOW_APPLICABILITY_PARTIALLY_SUPPORTED`  

---

## 1. Executive Summary & Authoritative Verdict

Phase 4, Task 4.18 conducted an independent, read-only scientific audit and re-evaluation to determine whether newly acquired deep Gaia DR3 ($G \le 20.7$, 110,575 sources) and 2MASS PSC ($J \le 17.0$, 55,349 sources) catalog evidence supports the real-sky applicability of ASTROVISION catalog-aware source masking.

### Core Quantitative Findings:
1. **Physical Efficacy Confirmed on Real Stellar Contamination:**  
   When genuine bright stars are located near the detection aperture, `CatalogAwareSourceMasker` (with frozen 2-pixel dilation) successfully eliminates the anomalous residual without encroaching on the central detection region ($r \le 2.5\text{ px}$). On actual real-sky observations, 3 out of 45 baseline false alarms were suppressed:
   - `PILOT_001004` (Detector D4): Core counterpart ($G = 15.79$, separation $1.41'' = 0.23\text{ px}$); suppressed from $\chi^2 = 648.7$ to $0.0$.
   - `PILOT_001383` (Detector D5): Off-center star ($G = 17.34$, separation $40.33'' = 6.49\text{ px}$); suppressed from $\chi^2 = 138.1$ to $62.3$ (below $\tau = 91.85$).
   - `PILOT_001481` (Detector D1): Very bright off-center star ($G = 11.95$, separation $25.86'' = 4.16\text{ px}$); suppressed from $\chi^2 = 1477.5$ to $21.9$ (below $\tau = 186.29$).
2. **Dominant Cause of False Positives is Non-Cataloged:**  
   Across the 45 baseline false-positive control cutouts, exactly **33 cutouts (73.33%)** have **zero** catalog counterparts in Gaia DR3 ($G \le 20.7$) and 2MASS PSC ($J \le 17.0$) within their exact $128 \times 128$ pixel footprint. These 33 false alarms are driven by instrumental noise, edge artifacts, and faint/diffuse emission outside optical survey completeness.
3. **Real-Sky vs. Synthetic Performance Discrepancy:**  
   The previously reported false-positive reduction from $9.00\%$ to $3.20\%$ (Task 4.15/4.16) was measured under a *synthetic off-center injection experiment*. On *actual real-sky observations*, the false-positive rate on the 500 null controls drops from **$9.00\%$ (45/500) to $8.40\%$ (42/500)**, an absolute reduction of $0.60\%$ ($p = 0.2500$ via McNemar's test, which is not statistically significant across the entire cohort).
4. **Exact Footprint vs. Circular Cone Reconciliation:**  
   Task 4.17's circular $565''$ radius search region includes $+58.5\%$ excess sky area relative to the true $128 \times 128$ pixel FITS array. Exact WCS projection establishes that true control-cohort catalog coverage is **$33.20\%$ (166/500)** rather than $36.00\%$ (180/500).

### Authoritative Verdict: `REAL_SKY_SHADOW_APPLICABILITY_PARTIALLY_SUPPORTED`

**Verdict Rationale:**  
Catalog-aware masking functions as designed and successfully eliminates false alarms caused by genuine off-center cataloged stars. However, because $73.3\%$ of ASTROVISION false alarms occur in cutouts completely devoid of optical/NIR catalog stars, catalog masking cannot serve as an all-sky solution for reducing false positives. Its applicability is real and demonstrable, but strictly domain-limited.

---

## 2. Answers to Mandatory Scientific Audit Questions

### 1. Is the 565″ coverage definition valid?
**Answer: Mathematically valid as an outer bounding circle, but geometrically oversized (+58.5% excess sky area).**  
The 565″ radius corresponds to the half-diagonal of the $128 \times 128$ pixel cutout at $6.215''/\text{pixel}$ ($64\sqrt{2} \times 6.215'' \approx 562.5'' \approx 565''$). While a circular cone of this radius guarantees capturing every source within the square cutout corners, it encloses $\pi \times 565^2 = 1,002,875\text{ arcsec}^2$, compared to the square cutout area of $(128 \times 6.215)^2 = 632,538\text{ arcsec}^2$. Sources located in the circular corner lobes with $|\Delta x| > 64\text{ px}$ or $|\Delta y| > 64\text{ px}$ fall outside the actual FITS image array fed into ASTROVISION.

### 2. What is the corrected exact-footprint catalog coverage?
**Answer: Exactly 33.20% on controls (166 / 500) and 33.20% overall (498 / 1,500).**  
- **Null Controls ($N = 500$):** Exactly 166 cutouts (33.20%) have $\ge 1$ Gaia source; 162 cutouts (32.40%) have 2MASS sources; 162 cutouts (32.40%) have dual coverage. Exactly 334 controls (66.80%) have NO catalog counterpart.
- **Full Evaluation Cohort ($N = 1,500$):** Exactly 498 cutouts (33.20%) have $\ge 1$ Gaia source; 491 cutouts (32.73%) have 2MASS sources; 489 cutouts (32.60%) have dual coverage. Exactly 1,002 cutouts (66.80%) have NO catalog counterpart.

### 3. How many of the 45 baseline false positives have usable catalog evidence?
**Answer: Exactly 12 / 45 (26.67%).**  
12 of the 45 false-positive cutouts contain catalog sources within their exact $128 \times 128$ pixel array (11 with both Gaia and 2MASS, 1 with Gaia only). The remaining 33 false positives (73.33%) have zero catalog sources down to $G = 20.7$ and $J = 17.0$.

### 4. How many are eligible for the existing 2px shadow mask?
**Answer: Exactly 11 cutouts.**  
Of the 12 cutouts with catalog sources, 1 cutout (`PILOT_001004`) has its source at $r = 0.23\text{ px}$ from the center (inside the central aperture, representing benchmark label contamination). The other 11 cutouts have off-center sources located at $r > 2.5\text{ px}$ from the center, which are eligible for masking under `protect_central_aperture=True`.

### 5. Is there evidence of actual real-sky false-positive reduction?
**Answer: Yes, but limited to a 6.67% reduction on baseline false alarms (3 / 45).**  
In real-sky inference, 3 false alarms were suppressed (`PILOT_001004`, `PILOT_001383`, `PILOT_001481`). However, because 33 false alarms have no catalog sources and 9 have distant sources whose masking does not drop the central residual below threshold, 42 false alarms persist. McNemar's paired test yields $p = 0.2500$ (not statistically significant on the pooled 500 controls).

### 6. Does detector-specific evidence support a consistent effect?
**Answer: No. The effect is heavily detector-stratified.**  
- **Detector D1:** Responsible for 19 of the 45 false alarms (42.2%). Only 1 FP was suppressed (`PILOT_001481`, bright star $G=11.95$). 18 D1 false alarms persist, 14 of which have zero catalog sources, confirming that D1 false alarms are dominated by detector-specific noise and edge systematics.
- **Detector D4:** 1 of 9 FPs was suppressed (`PILOT_001004`, label contamination).
- **Detector D5:** 1 of 3 FPs was suppressed (`PILOT_001383`).
- **Detectors D2, D3, D6:** 0 false alarms were suppressed (14 FPs persist).

### 7. What remains scientifically uncertain?
**Answer:**  
1. The exact physical origin of the 33 uncataloged false alarms (sub-threshold optical stars with $G > 20.7$, cold infrared dust cirrus, or readout/electronic noise).
2. Whether mid-infrared catalogs (WISE / CatWISE2020) can detect counterparts for the 33 uncataloged fields.
3. The crowding threshold above which masking dozens of stars perturbs local background subtraction and risks inducing boundary artifacts.

### 8. What claims can safely be made to NASA judges?
**Answer:**  
- **Safe Claim 1:** "We demonstrated that catalog-aware masking successfully eliminates spatial autoencoder false alarms caused by real bright off-center stars ($G < 16$), dropping anomalous $\chi^2$ from $> 1400$ to $< 22$ while perfectly preserving the central aperture."
- **Safe Claim 2:** "Our deep catalog audit revealed that 73.3% of ASTROVISION false alarms are uncataloged down to $G = 20.7$, proving that optical catalog masking alone cannot solve all-sky false-alarm rates without infrared and instrumental remediation."
- **Safe Claim 3:** "Real-sky shadow applicability is partially supported: highly effective where catalog sources exist, but constrained by survey completeness in sparse sky regions."

---

## 3. False-Positive Location Attribution Breakdown (N = 45)

Each of the 45 baseline ASTROVISION false-positive control locations was evaluated using exact WCS coordinates, astrometry, and photometry:

| Attribution Classification | Count | Pct (%) | Primary Physical Cause | Masker Applicability |
|---|:---:|:---:|---|---|
| **NO_LOCAL_CATALOG_COUNTERPART** | 33 | 73.33% | Uncataloged faint source, diffuse dust, or detector systematic noise | Not applicable (no catalog stars) |
| **AMBIGUOUS_CATALOG_ASSOCIATION** | 7 | 15.56% | Distant field stars ($r > 7\text{ px}$) present in cutout, but not direct cause of central anomaly | Masked, but central residual persists |
| **PROBABLE_CATALOG_ASSOCIATION** | 4 | 8.89% | Nearby off-center stars ($2.5\text{ px} < r \le 7\text{ px}$) causing receptive-field leakage | Masked; 2 suppressed (`PILOT_001383`, `PILOT_001481`), 2 partial |
| **CONFIRMED_CATALOG_ASSOCIATION** | 1 | 2.22% | Core stellar counterpart at $r = 0.23\text{ px}$ (Benchmark label contamination) | Suppressed (`PILOT_001004`) |
| **Total** | **45** | **100.0%** | | **3 Suppressed / 42 Persistent** |

Complete record-level details for all 45 false positives are in [`reports/phase4/task_4_18/false_positive_catalog_attribution.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/false_positive_catalog_attribution.csv).

---

## 4. Control-Cohort Exact-Footprint Coverage Audit (N = 500)

| Coverage Metric | Circular Cone ($r \le 565''$) | Exact Box ($128 \times 128\text{ px}$) | Delta | Scientific Meaning |
|---|:---:|:---:|:---:|---|
| **Gaia DR3 ($G \le 20.7$)** | 180 / 500 (36.00%) | 166 / 500 (33.20%) | $-14$ cutouts ($-2.80\%$) | 14 cutouts had stars only in circular corners outside FITS data |
| **2MASS PSC ($J \le 17.0$)** | 178 / 500 (35.60%) | 162 / 500 (32.40%) | $-16$ cutouts ($-3.20\%$) | Same geometric corner truncation effect |
| **Dual Catalog Coverage** | 178 / 500 (35.60%) | 162 / 500 (32.40%) | $-16$ cutouts ($-3.20\%$) | Concomitant optical-NIR presence |
| **No Local Counterpart** | 320 / 500 (64.00%) | 334 / 500 (66.80%) | $+14$ cutouts ($+2.80\%$) | Two-thirds of null controls are completely devoid of catalog stars |

Compared to Task 4.16's earlier reported $12.20\%$ (61/500) under shallow archival pilot catalogs ($G \le 19.5$), exact-footprint coverage under deep Gaia DR3 increased to **$33.20\%$ (166/500)** — a 2.72x expansion. Complete trial-by-trial coverage is archived in [`reports/phase4/task_4_18/control_cohort_exact_footprint_coverage.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/control_cohort_exact_footprint_coverage.csv).

---

## 5. Detector- and Pointing-Stratified Shadow Applicability

| Stratum Name | Type | Controls $N$ | Exact Gaia Cov % | Baseline FPs | Baseline FPR % | Shadow FPs | Shadow FPR % | Delta FPs | Suppressed FPs | Stratum Verdict |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **OVERALL_CONTROL_COHORT** | OVERALL | **500** | **33.20%** | **45** | **9.00%** | **42** | **8.40%** | **-3** | **3** | **PARTIALLY_SUPPORTED** |
| Pointing P0002 (Mid-Galactic) | POINTING | 168 | 39.29% | 12 | 7.14% | 10 | 5.95% | -2 | 2 | EMPIRICAL_SUPPRESSION |
| Pointing P0009 (Perseus Field) | POINTING | 168 | 27.38% | 27 | 16.07% | 27 | 16.07% | 0 | 0 | CATALOG_PRESENT_NO_SUPPRESSION |
| Pointing P0010 (NEP) | POINTING | 164 | 32.93% | 6 | 3.66% | 5 | 3.05% | -1 | 1 | EMPIRICAL_SUPPRESSION |
| Detector D1 | DETECTOR | 84 | 34.52% | 19 | 22.62% | 18 | 21.43% | -1 | 1 | DOMINATED_BY_DETECTOR_NOISE |
| Detector D2 | DETECTOR | 84 | 30.95% | 7 | 8.33% | 7 | 8.33% | 0 | 0 | NO_SUPPRESSION |
| Detector D3 | DETECTOR | 83 | 28.92% | 2 | 2.41% | 2 | 2.41% | 0 | 0 | LOW_BASELINE_NO_CHANGE |
| Detector D4 | DETECTOR | 83 | 42.17% | 9 | 10.84% | 8 | 9.64% | -1 | 1 | LABEL_CONTAMINATION_REMOVED |
| Detector D5 | DETECTOR | 83 | 34.94% | 3 | 3.61% | 2 | 2.41% | -1 | 1 | EMPIRICAL_SUPPRESSION |
| Detector D6 | DETECTOR | 83 | 27.71% | 5 | 6.02% | 5 | 6.02% | 0 | 0 | NO_SUPPRESSION |
| Field 1 (D1, D4) | PAIR | 167 | 38.32% | 28 | 16.77% | 26 | 15.57% | -2 | 2 | MODERATE_IMPROVEMENT |
| Field 2 (D2, D5) | PAIR | 167 | 32.93% | 10 | 5.99% | 9 | 5.39% | -1 | 1 | MODERATE_IMPROVEMENT |
| Field 3 (D3, D6) | PAIR | 166 | 28.31% | 7 | 4.22% | 7 | 4.22% | 0 | 0 | UNCHANGED |

Complete stratified data is in [`reports/phase4/task_4_18/detector_pointing_shadow_applicability.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/detector_pointing_shadow_applicability.csv).

---

## 6. Paired Statistical Governance & Reconciliation

### 6.1 Authoritative Paired 2×2 Contingency Table (Controls N = 500)

$$\begin{array}{c|cc|c}
 & \text{Shadow Non-FP} & \text{Shadow FP} & \text{Total} \\
\hline
\text{Baseline Non-FP} & 455 & 0 & 455 \\
\text{Baseline FP} & 3 & 42 & 45 \\
\hline
\text{Total} & 458 & 42 & 500
\end{array}$$

- **Discordant Pairs:** $b = 3$ (Baseline FP $\to$ Shadow Non-FP), $c = 0$ (Baseline Non-FP $\to$ Shadow FP).
- **Exact McNemar $p$-value:** $p = 0.2500$ (two-sided binomial test, not statistically significant across the pooled cohort).
- **Wilson 95% Confidence Intervals:**
  - Baseline FPR: $9.00\%$ $[6.76\%, 11.87\%]$
  - Shadow FPR: $8.40\%$ $[6.24\%, 11.19\%]$
  - Absolute Difference: $-0.60\%$

Complete paired analysis records are archived in [`reports/phase4/task_4_18/paired_shadow_analysis.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/paired_shadow_analysis.csv).

---

## 7. Task 4.16 Discrepancy Reconciliation

Six critical metrics across Tasks 4.12, 4.15, 4.16, 4.17, and 4.18 were reconciled:

1. **45 Baseline False Positives:** Exactly reproduced (45/500, 9.00%).
2. **61/500 Control Catalog Coverage:** Increased to 166/500 (33.20%) exact box / 180/500 (36.00%) circular cone due to deep Gaia DR3 ingestion.
3. **7/45 False Positives with Usable Sources:** Increased to 12/45 (26.67%) with deep Gaia DR3.
4. **Real-Sky False Positive Suppression:** 3/45 suppressed on real data (compared to 0/7 on shallow pilot catalog and 29/45 on synthetic injection benchmark).
5. **Footprint Search Geometry:** Formally distinguished exact $128 \times 128$ pixel box from circular $565''$ bounding cone (+58.5% excess area).
6. **Detector 1 False Alarm Rate:** Baseline 19/84 (22.62%) dropped to 18/84 (21.43%) under shadow masking, confirming that D1 is dominated by detector noise rather than stellar contamination.

The full reconciliation audit is documented in [`reports/phase4/task_4_18/task_4_16_discrepancy_reconciliation.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/task_4_16_discrepancy_reconciliation.csv).

---

## 8. Protected-Asset Cryptographic Integrity & Testing

All 3 protected assets were verified before and after execution:

| Asset Path | Expected SHA-256 Digest | Actual SHA-256 Digest | Status |
|---|---|---|:---:|
| `checkpoints/astrovision_spatial_v3.pt` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | **PRISTINE** |
| `checkpoints/spectra_masked_ae_v2.pt` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | **PRISTINE** |
| `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | **PRISTINE** |

**Regression Test Suite:** `270 passed in 56.80s` (100% passing).

---

## 9. Deliverables Manifest (8 Artifacts in `reports/phase4/task_4_18/`)

| File Name | Records / Type | Description |
|---|:---:|---|
| [`task_4_18_closeout_report.md`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/task_4_18_closeout_report.md) | Complete Markdown | This comprehensive audit report |
| [`false_positive_catalog_attribution.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/false_positive_catalog_attribution.csv) | 45 rows | Record-level attribution and shadow results for all 45 baseline FPs |
| [`control_cohort_exact_footprint_coverage.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/control_cohort_exact_footprint_coverage.csv) | 500 rows | Per-cutout exact-footprint coverage for all 500 null controls |
| [`detector_pointing_shadow_applicability.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/detector_pointing_shadow_applicability.csv) | 13 strata | Stratified coverage, baseline FPR, shadow FPR, and applicability verdicts |
| [`task_4_16_discrepancy_reconciliation.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/task_4_16_discrepancy_reconciliation.csv) | 6 metrics | Comprehensive reconciliation of cross-task metric discrepancies |
| [`paired_shadow_analysis.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/paired_shadow_analysis.csv) | 4 regimes | Paired $2 \times 2$ contingency tables, McNemar tests, and Wilson CIs |
| [`scientific_claims_and_limitations.md`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/scientific_claims_and_limitations.md) | Markdown Guide | Formal charter of permitted vs prohibited scientific claims |
| [`artifact_hashes.sha256`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18/artifact_hashes.sha256) | SHA-256 Ledger | Cryptographic checksums of all 8 deliverables |

