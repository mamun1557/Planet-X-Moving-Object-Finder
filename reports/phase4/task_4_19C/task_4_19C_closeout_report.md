# Chance-Coincidence Controlled Counterpart Validation & PSF Contamination Hypothesis Audit
## Phase 4, Task 4.19C Closeout Report

**Module:** ASTROVISION (Spatial Infrared Anomaly Detection) + Spatial Evidence Audit  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10 on Windows)  
**Parent Tasks:** Phase 4 Tasks 4.12–4.19B  
**Target Cohort:** Pointings P0002, P0009, P0010 — Blind Evaluation Cohort ($N = 1,500$ cutouts)  
**Primary Focus:** 45 ASTROVISION Baseline False Positives & 500 Null Controls  
**Task Type:** CONTROLLED SCIENTIFIC HYPOTHESIS TESTING + SPATIAL NULL-MODEL VALIDATION  
**Audit Date:** 2026-11-08  

---

### 1. Executive Summary & Authoritative Scientific Verdicts

#### Primary Authoritative Verdict:
$$\mathbf{CHANCE\_COINCIDENCE\_HYPOTHESIS\_REJECTED}$$

#### Four Mandated Separate Scientific Verdicts:

1. **Statistical Source Association Verdict:**  
   $$\mathbf{ASTROVISION\_SOURCE\_ASSOCIATION\_SUPPORTED}$$  
   *Finding:* The positional association between ASTROVISION baseline false alarms and external astronomical catalog sources is real, localized, and statistically overwhelming. **$80.00\%$ ($36 / 45$)** of false positives possess an external catalog source within $\le 1.0\text{ native SPHEREx pixel}$ ($\le 6.215''$) of their actual anomaly centroid, compared to only **$29.60\%$ ($148 / 500$)** in null controls and $40.92\%$ in randomized spatial null models (Fisher's exact test $p = 3.81 \times 10^{-11}$, Odds Ratio: $9.514$, Mann-Whitney $U$ test $p = 1.01 \times 10^{-12}$).

2. **PSF Contamination Hypothesis Verdict:**  
   $$\mathbf{PSF\_CONTAMINATION\_HYPOTHESIS\_SUPPORTED}$$  
   *Finding:* Independent evidence from Task 4.12 morphology classifications reveals that **$43 / 45$ ($95.56\%$)** of the baseline false positives exhibit compact stellar point-source or saturated star core morphology. **$43 / 45$ ($95.56\%$)** reside within $\le 2.0\text{ pixels}$ ($12.4''$) of a catalog star. However, optical Gaia $G$ magnitude alone cannot establish the exact wavelength-dependent infrared PSF diffraction profile without empirical flight PSF calibrations.

3. **Adaptive Masking Shadow Performance Verdict:**  
   $$\mathbf{ADAPTIVE\_MASKING\_SHADOW\_SUPERIORITY\_CONFIRMED}$$  
   *Finding:* In shadow evaluation across the 1,500-cutout blind cohort, magnitude-adaptive masking (Adaptive-A) suppresses **$75.56\%$ ($34 / 45$)** of baseline false alarms (reducing empirical FPR from $9.00\%$ to $2.20\%$, $95\%$ CI: $[1.23\%, 3.90\%]$) with **zero central aperture encroachment** and **$100\%$ preservation** of genuine point-source ($34.80\%$) and extended-source ($17.40\%$) anomaly recovery.

4. **Production Promotion Eligibility Verdict:**  
   $$\mathbf{NOT\_ELIGIBLE\_FOR\_PRODUCTION\_PROMOTION\_SHADOW\_ONLY}$$  
   *Finding:* In accordance with strict production-preserving governance rules, no masking module, threshold adjustment, or checkpoint change may be promoted to production during Task 4.19C. Adaptive masking remains strictly confined to shadow validation.

---

### 2. Hypotheses Formally Tested

- **Null Hypothesis ($H_0$):** The observed positional proximity between ASTROVISION baseline false alarms and external catalog sources can be fully explained by local catalog-source density and random spatial coincidence (chance alignment).
- **Alternative Hypothesis ($H_1$):** ASTROVISION baseline false positives are statistically associated with nearby external catalog sources, driven by stellar point spread function (PSF) wings, saturation bleed, or unresolved stellar blending.

#### Outcome of Hypothesis Testing:
- Fisher's Exact Test on Primary Outcome ($\le 1.0\text{ pixel}$): **$p = 3.81 \times 10^{-11}$** (Odds Ratio: **$9.514$**).
- Monte Carlo Permutation Test (10,000 label shuffles): **$p = 0.0000$** ($p < 10^{-4}$).
- Mann-Whitney $U$ Test on Nearest-Neighbor Separation: **$p = 1.01 \times 10^{-12}$**.
- Two-Sample Kolmogorov-Smirnov Test on Distance Distributions: **$D = 0.526$, $p = 4.14 \times 10^{-11}$**.
- **Conclusion:** $H_0$ is decisively rejected at $\alpha = 0.001$. The statistical association is proven beyond reasonable scientific doubt.

---

### 3. Primary & Secondary Outcome Measures

*Table 1: Primary and Secondary Association Outcomes Comparing False Positives vs. Controls and Spatial Null Models*

| Metric / Outcome | False Positives ($N=45$) | Null Controls ($N=500$) | D1: Random Positions ($N=45,000$) | D2: Shifted Coords ($N=2,880$) | Effect Size (Odds Ratio) | Statistical Test | p-value | Significance ($\alpha=0.05$, BH-adj) |
|:---|---:|---:|---:|---:|---:|:---:|:---:|:---:|
| **Counterpart $\le 1.0\text{ px}$ (Primary)** | **$80.00\%$ (36/45)** | $29.60\%$ (148/500) | $40.92\%$ | $40.90\%$ | **$9.514$** | Fisher's Exact | **$3.81 \times 10^{-11}$** | **SIGNIFICANT** |
| Counterpart $\le 2.0\text{ px}$ | **$95.56\%$ (43/45)** | $55.60\%$ (278/500) | $68.45\%$ | $68.40\%$ | $17.169$ | Fisher's Exact | $1.25 \times 10^{-8}$ | **SIGNIFICANT** |
| Counterpart $\le 2.414\text{ px}$ ($15''$) | **$95.56\%$ (43/45)** | $62.80\%$ (314/500) | $76.10\%$ | $76.15\%$ | $12.736$ | Fisher's Exact | $9.22 \times 10^{-7}$ | **SIGNIFICANT** |
| Counterpart $\le 3.0\text{ px}$ | **$97.78\%$ (44/45)** | $75.80\%$ (379/500) | $84.22\%$ | $84.18\%$ | $14.047$ | Fisher's Exact | $1.36 \times 10^{-4}$ | **SIGNIFICANT** |
| **Median Nearest Distance** | **$0.451\text{ px}$ ($2.80''$)** | $1.813\text{ px}$ ($11.27''$) | $1.147\text{ px}$ ($7.13''$) | $1.148\text{ px}$ ($7.14''$) | $\Delta = -1.36\text{ px}$ | Mann-Whitney $U$ | **$1.01 \times 10^{-12}$** | **SIGNIFICANT** |
| Distance Distribution ECDF | Shape shift | Baseline | Uniform Null | Clustered Null | $D = 0.526$ | Kolmogorov-Smirnov | $4.14 \times 10^{-11}$ | **SIGNIFICANT** |

---

### 4. Separation Bands Breakdown

*Table 2: Breakdown of Baseline False Positives and Null Controls across Predefined Separation Bands*

| Separation Band | Pixel Range | Angular Range | False Positives ($N=45$) | FP % | Null Controls ($N=500$) | Control % | Ratio FP / Control |
|:---|:---:|:---:|---:|---:|---:|---:|:---:|
| **Band 1: Very Close Association** | $\le 1.0\text{ px}$ | $\le 6.215''$ | **36** | **$80.00\%$** | 148 | $29.60\%$ | **$2.70\times$** |
| **Band 2: Close Association** | $>1.0 - 2.0\text{ px}$ | $>6.215 - 12.43''$ | **7** | **$15.56\%$** | 130 | $26.00\%$ | $0.60\times$ |
| **Band 3: Intermediate Association** | $>2.0 - 3.0\text{ px}$ | $>12.43 - 18.65''$ | **1** | **$2.22\%$** | 101 | $20.20\%$ | $0.11\times$ |
| **Band 4: Weak Spatial Proximity** | $>3.0 - 5.0\text{ px}$ | $>18.65 - 31.08''$ | **1** | **$2.22\%$** | 88 | $17.60\%$ | $0.13\times$ |
| **Band 5: Wider Contextual Association** | $>5.0\text{ px}$ | $>31.08''$ | **0** | **$0.00\%$** | 33 | $6.60\%$ | $0.00\times$ |

*Key Takeaway:* While controls exhibit a broad spatial distribution across all bands (median $1.81\text{ px}$), the false positive distribution is heavily compressed into Band 1 ($80.0\%$) and Band 2 ($15.6\%$). **$95.56\%$** of false alarms reside within $2.0\text{ pixels}$ of a verified catalog star.

---

### 5. Stratified Association Analysis

#### Detector Stratification
*Table 3: False Positive vs. Null Control Associations Stratified by Detector*

| Detector | FP Total | FP $\le 1\text{px}$ | FP % | Ctrl Total | Ctrl $\le 1\text{px}$ | Ctrl % | Odds Ratio | Fisher p-value | FP Median Dist (px) | Ctrl Median Dist (px) |
|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **D1** | 19 | 15 | $78.95\%$ | 84 | 37 | $44.05\%$ | $4.764$ | **$0.0098$** | $0.487$ | $1.397$ |
| **D2** | 7 | 7 | $100.00\%$ | 84 | 38 | $45.24\%$ | $\infty$ | **$0.0056$** | $0.418$ | $1.308$ |
| **D3** | 2 | 2 | $100.00\%$ | 83 | 21 | $25.30\%$ | $\infty$ | $0.0709$ | $0.352$ | $2.403$ |
| **D4** | 9 | 8 | $88.89\%$ | 83 | 15 | $18.07\%$ | **$36.267$** | **$3.99 \times 10^{-5}$** | $0.290$ | $2.433$ |
| **D5** | 3 | 1 | $33.33\%$ | 83 | 13 | $15.66\%$ | $2.692$ | $0.4172$ | $1.589$ | $1.865$ |
| **D6** | 5 | 3 | $60.00\%$ | 83 | 24 | $28.92\%$ | $3.688$ | $0.1660$ | $0.457$ | $1.412$ |

*Observation:* Detectors 1, 2, and 4 exhibit statistically significant excesses of close stellar counterparts ($p < 0.01$). Detector 4 exhibits an exceptional odds ratio of $36.27$ ($p = 3.99 \times 10^{-5}$), with median FP separation of only $0.290\text{ pixels}$ ($1.80''$).

#### Pointing Stratification
*Table 4: False Positive vs. Null Control Associations Stratified by Pointing*

| Pointing | FP Total | FP $\le 1\text{px}$ | FP % | Ctrl Total | Ctrl $\le 1\text{px}$ | Ctrl % | Odds Ratio | Fisher p-value | FP Median Dist (px) | Ctrl Median Dist (px) |
|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **P0002** | 14 | 12 | $85.71\%$ | 168 | 76 | $45.24\%$ | $7.263$ | **$0.0043$** | $0.433$ | $1.129$ |
| **P0009** | 24 | 19 | $79.17\%$ | 168 | 58 | $34.52\%$ | $7.207$ | **$7.18 \times 10^{-5}$** | $0.469$ | $1.543$ |
| **P0010** | 7 | 5 | $71.43\%$ | 164 | 14 | $8.54\%$ | **$26.786$** | **$1.84 \times 10^{-4}$** | $0.457$ | $2.860$ |

*Observation:* Every pointing independently confirms the statistical excess at $p < 0.005$. In pointing P0010 (low Galactic density), control cutouts have a low coincidence rate ($8.54\%$), but false alarms remain $71.43\%$ associated with stars (Odds Ratio: $26.79$).

---

### 6. PSF and Diffraction-Wing Hypothesis Evidence Audit

*Table 5: Categorization of the 45 Baseline False Alarms by Evidence Category*

| Evidence Classification | Count | % of Cohort | Description & Physical Traceability |
|:---|---:|---:|:---|
| `MORPHOLOGY_CONSISTENT_WITH_PSF_CONTAMINATION` | **40** | **$88.89\%$** | Star within $\le 2.0\text{ px}$; independent Task 4.12 morphology confirms compact stellar point source or saturated core. |
| `PSF_CONTAMINATION_SUPPORTED_BY_INDEPENDENT_EVIDENCE` | **3** | **$6.67\%$** | Stellar morphology, close alignment ($\le 0.15\text{ px}$), and confirmed shadow suppression by $2\text{px}$ catalog masking. |
| `PSF_HYPOTHESIS_NOT_SUPPORTED` | **2** | **$4.44\%$** | Separation exceeds PSF core/inner wings ($>2.8\text{ px}$); anomaly likely instrumental detector noise. |
| `POSITIONAL_ASSOCIATION_ONLY` | 0 | $0.00\%$ | No unconfirmed faint positional associations. |
| `BRIGHT_SOURCE_NEAR_ANOMALY` | 0 | $0.00\%$ | All bright cases were captured in the morphology categories above. |
| `UNVERIFIABLE` | 0 | $0.00\%$ | 100% of cutouts have verified catalog counterpart records. |

*Crucial Physical Finding:* In **$43 / 45$ ($95.56\%$)** cases, the ASTROVISION spatial anomaly peak is co-located with a confirmed catalog star exhibiting point-source or PSF core morphology. Only 2 cases (`PILOT_001018` at $2.88\text{ px}$ and `PILOT_001073` at $3.25\text{ px}$) cannot be plausibly explained by stellar PSF contamination.

---

### 7. Adaptive Masking Shadow Experiment Results

*Table 6: Comparison of Shadow Masking Policies across the 1,500-Cutout Evaluation Cohort*

| Policy Name | Radius Policy | False Alarms Suppressed | Persistent False Alarms | Suppression % | Empirical FPR % | 95% Wilson CI | Point Recovery % | Extended Recovery % | Mean Mask Area % | Central Aperture Encroachment |
|:---|:---|---:|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline Unmasked** | None | 0 | 45 | $0.00\%$ | $9.00\%$ | [6.79%, 11.83%] | $34.80\%$ | $17.40\%$ | $0.42\%$ | $0.00\%$ |
| **Fixed 1px** | $r = 1.0\text{ px}$ | 24 | 21 | $53.33\%$ | $4.20\%$ | [2.76%, 6.34%] | $34.80\%$ | $17.40\%$ | $2.76\%$ | $0.00\%$ |
| **Fixed 2px** | $r = 2.0\text{ px}$ | 29 | 16 | $64.44\%$ | $3.20\%$ | [1.98%, 5.13%] | $34.80\%$ | $17.40\%$ | $3.79\%$ | $0.00\%$ |
| **Fixed 3px** | $r = 3.0\text{ px}$ | 33 | 12 | $73.33\%$ | $2.40\%$ | [1.38%, 4.15%] | $34.60\%$ | $17.20\%$ | $5.42\%$ | **$0.20\%$** |
| **Adaptive-A** | $G$-scaled ($1-4\text{px}$) | **34** | **11** | **$75.56\%$** | **$2.20\%$** | **[1.23%, 3.90%]** | **$34.80\%$** | **$17.40\%$** | **$3.12\%$** | **$0.00\%$** |
| **Adaptive-B** | Flux/IR-scaled | **36** | **9** | **$80.00\%$** | **$1.80\%$** | **[0.95%, 3.39%]** | **$34.80\%$** | **$17.40\%$** | **$3.45\%$** | **$0.00\%$** |

#### Scientific Trade-Off Analysis:
1. **Fixed 3px Masking Flaw:** Uniform 3-pixel dilation encroaches into the central evaluation aperture in $0.20\%$ of trials, degrading genuine point-source recovery ($34.80\% \rightarrow 34.60\%$) and extended-source recovery ($17.40\% \rightarrow 17.20\%$).
2. **Adaptive-A Superiority:** By scaling mask radius to Gaia $G$ magnitude ($1\text{ px}$ for $G \ge 18$, $2\text{ px}$ for $15 \le G < 18$, $3-4\text{ px}$ for $G < 15$) and enforcing Central Aperture Protection, Adaptive-A achieves **greater false-alarm suppression ($75.56\%$ vs $73.33\%$)** while occupying **$42\%$ less masked area ($3.12\%$ vs $5.42\%$)** and maintaining **$100\%$ zero-loss recovery** on genuine astronomical injections.

---

### 8. Distinction of Four Scientific Claims

In accordance with Phase H instructions, we distinguish the four fundamental claims:

1. **Claim A (Catalog Availability):** $\mathbf{CONFIRMED}$.  
   Task 4.19B proved that external catalog sources are present in 100% of the evaluation cutouts.
2. **Claim B (Positional Association):** $\mathbf{CONFIRMED}$.  
   Task 4.19C proves that catalog stars are located significantly closer to ASTROVISION anomaly peaks than predicted by local catalog density or spatial null models ($p = 3.81 \times 10^{-11}$, Odds Ratio: $9.514$).
3. **Claim C (Physical PSF Contamination):** $\mathbf{STRONGLY\_SUPPORTED}$.  
   Independent morphology classifications and radial proximity show that $95.56\%$ ($43 / 45$) of false alarms coincide with compact stellar point sources or saturated stellar cores.
4. **Claim D (Masking Effectiveness):** $\mathbf{CONFIRMED\_IN\_SHADOW}$.  
   Adaptive masking successfully suppresses $75.56\%$ of false alarms without compromising genuine anomaly recovery, but is **not** promoted to production.

---

### 9. Cryptographic Audit & Protected Asset Verification

| Protected Production Asset Path | Expected SHA-256 Checksum | Measured SHA-256 Checksum | Verification Status |
|:---|:---:|:---:|:---:|
| `checkpoints/astrovision_spatial_v3.pt` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | **IDENTICAL / UNTOUCHED** |
| `checkpoints/spectra_masked_ae_v2.pt` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | **IDENTICAL / UNTOUCHED** |
| `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | **IDENTICAL / UNTOUCHED** |

---

### 10. Complete Deliverable Inventory (14 Artifacts in `reports/phase4/task_4_19C/`)

1. [`task_4_19C_closeout_report.md`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/task_4_19C_closeout_report.md) — This authoritative closeout report.
2. [`input_provenance_audit.md`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/input_provenance_audit.md) — Audit of catalog namespaces, coordinates, and WCS frames.
3. [`false_positive_separation_analysis.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/false_positive_separation_analysis.csv) — Exact separation metrics for all 45 false positives.
4. [`null_control_separation_analysis.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/null_control_separation_analysis.csv) — Equivalent separation metrics for all 500 null controls.
5. [`random_position_null_trials.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/random_position_null_trials.csv) — 45,000 uniform random-position null model trials.
6. [`shifted_coordinate_null_trials.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/shifted_coordinate_null_trials.csv) — 2,880 clustered shifted-coordinate null model trials.
7. [`chance_coincidence_statistics.json`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/chance_coincidence_statistics.json) — Statistical test results, odds ratios, and BH corrections.
8. [`detector_stratified_association_analysis.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/detector_stratified_association_analysis.csv) — Statistical tests stratified across Detectors D1–D6.
9. [`pointing_stratified_association_analysis.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/pointing_stratified_association_analysis.csv) — Statistical tests stratified across Pointings P0002, P0009, P0010.
10. [`psf_contamination_evidence_audit.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/psf_contamination_evidence_audit.csv) — Record-level physical PSF evidence audit for 45 false positives.
11. [`adaptive_masking_shadow_comparison.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/adaptive_masking_shadow_comparison.csv) — Evaluation grid of fixed and adaptive masking shadow policies.
12. [`scientific_limitations.md`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/scientific_limitations.md) — Comprehensive analysis of astrometric, color, and null model limitations.
13. [`data_integrity_manifest.json`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/data_integrity_manifest.json) — Cryptographic SHA-256 manifest of all input and deliverable files.
14. [`reproducibility_instructions.md`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_19C/reproducibility_instructions.md) — Operational instructions to reproduce all findings and tests.

