# SPECTRA-X / F1 — PHASE 2, TASK 4B: ANOMALY CORRELATION AUDIT
## Independent Forensic Audit of SPECTRA v2 Scores, RUWE Binarity, Top-10 Anomalies, & YSO Candidate

**Role:** Independent Scientific Validation Engineer  
**Date:** 2026-11-04  
**Audit Status:** **INCORRECT (RUWE 3.37 CLAIM) / UNVERIFIED (TRAINING SET CLAIM) / PROVISIONAL (YSO CANDIDATE)**  

---

## 1. Executive Summary

Phase 2, Task 4 integrated external astronomical cross-matches with the frozen SPECTRA v2 Condition B inference benchmark ([`data/processed/benchmarks/spectra_v2_source_scores.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/benchmarks/spectra_v2_source_scores.csv)), asserting several major scientific conclusions.

This independent forensic audit investigates:
1. **The RUWE Binarity Claim:** The assertion that sources with RUWE > 2.0 have an elevated average anomaly score of **3.37** and confirm binarity.
2. **The Top-10 Anomaly Interpretation:** The assertion that all 10 highest-scoring anomalies are hot A/F main-sequence stars ($BP - RP \le 0.47$) and represent genuine astrophysical outliers.
3. **The Training Set Composition Claim:** The assertion that SPECTRA v2 training data (Pointing 0001) consisted predominantly of cool red giants.
4. **The YSO / Infrared Excess Candidate:** The physical nature and empirical reliability of candidate `SPX-J166.9881-70.9094`.

---

## 2. Independent Audit of the RUWE Claim

### 1. Headline Finding: Claim Refuted as Incorrect
The Task 4 report states:
> *"Sources with severe astrometric disturbance (RUWE > 2.0, isolated into QUALITY_REJECTED) exhibit elevated anomaly scores (Mean $\chi^2 = 3.37$), demonstrating that physical binarity and photocenter jitter directly perturb multi-band SED reconstruction."*
> — [`reports/F1_PHASE2_TASK4_SPECTRA_CORRELATION.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/F1_PHASE2_TASK4_SPECTRA_CORRELATION.md), lines 20–22, 67–69.

An exhaustive recalculation across the actual database reveals that **the reported mean of 3.37 is completely unproducible and incorrect**:

| Astrometric Sample | Sample Size ($N$) | Mean $\chi^2_{\text{B}}$ | Median $\chi^2_{\text{B}}$ | Std Dev ($\sigma$) | SEM | Interquartile Range (IQR) | Max Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Task 4 Claimed** | **72** | **3.37** | — | — | — | — | — |
| **Actual `QUALITY_REJECTED`** | **72** | **0.9637** | **0.3365** | $1.0964$ | $0.1292$ | $[0.2391, 1.3463]$ | $4.4332$ |
| **All Sources with $\text{RUWE} > 2.0$** | **80** | **0.9219** | **0.3692** | $1.0578$ | $0.1183$ | $[0.2429, 1.2849]$ | $4.4332$ |
| **All Sources with $\text{RUWE} \le 2.0$** | **1,023** | **0.6978** | **0.3580** | $0.9189$ | $0.0287$ | $[0.2523, 0.7680]$ | $8.0018$ |

### 2. Rigorous Statistical Hypothesis Testing
- **Difference in Means:** $\Delta\mu = 0.9219 - 0.6978 = \mathbf{+0.2241 \pm 0.1217}$.
- **Welch's Two-Sample t-Test:** $t = 1.8417$ ($p = 0.068$, two-tailed).
- **Mann-Whitney Non-Parametric Rank-Sum Test:**
  - $U = 43,526.0$, $E[U] = 40,920.0$, $\sigma_U = 2,744.0$.
  - Standardized $Z\text{-score} = \mathbf{0.9497}$.
  - **Asymptotic $p\text{-value} = \mathbf{0.3423}$** (no statistical significance).
- **Median Difference:** The median anomaly score for $\text{RUWE} > 2.0$ ($0.3692$) differs from $\text{RUWE} \le 2.0$ ($0.3580$) by only **$0.0112$** (a 3% shift).
- **Audit Verdict:** The claim that $\text{RUWE} > 2.0$ sources have a mean score of 3.37 is **INCORRECT**. The association between elevated RUWE and elevated SPECTRA reconstruction error is **not statistically credible** ($p = 0.34$).

### 3. Confounder Analysis & Binarity Caveats
1. **RUWE is Not Proof of Binarity:**
   RUWE measures the square root of the reduced $\chi^2$ of the astrometric 5-parameter model. While unresolved orbital motion can cause photocenter wobble, RUWE is elevated by:
   - Optical doubles and blended background stars within the Gaia PSF ($0.1'' - 0.4''$).
   - Color errors or variability in saturated or near-threshold stars.
   - Partially resolved background galaxies.
   Describing RUWE > 2.0 as definitive proof of binarity is scientifically invalid.
2. **Confounding by Channel Masking & Pipeline Exclusion:**
   As discovered in the Data Integrity Audit, the pipeline set `g_ok = False` for all 72 `QUALITY_REJECTED` stars, preventing them from being classified. Their spectral anomaly scores are driven not by binarity, but by varying valid channel counts in SPHEREx Level-2 images.

---

## 3. Top-10 SPECTRA Anomaly Audit

The Task 4 report claimed that all 10 highest-scoring D1+D4 anomalies are hot A/F main-sequence stars with $BP - RP \le 0.47$.

### 1. Comprehensive Independent Multi-Wavelength Profile of the Top 10 Anomalies

| Rank | Source ID | $\chi^2_{\text{B}}$ | $\chi^2_{\text{D1}}$ | $\chi^2_{\text{D4}}$ | Valid Ch. | Gaia Cat. | Sep ($''$) | $G$ [mag] | $BP - RP$ | Parallax [mas] (SNR) | RUWE | AllWISE Cat. | $W1 - W2$ | WISE cc/ph | Assigned Class (Conf) | True Astrophysical Type |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **1** | **SPX-J168.0334-70.2792** | $8.0018$ | $17.79$ | $0.85$ | 7 | `PROBABLE` | $0.57$ | $11.00$ | $0.336$ | $1.66$ ($114\sigma$) | $1.01$ | `HIGH_CONF` | $-0.017$ | `0h00` / AAAU | `MAIN_SEQUENCE` (HIGH) | Late A / Early F dwarf |
| **2** | **SPX-J169.3502-68.8832** | $6.9083$ | $21.15$ | $1.17$ | 3 | `PROBABLE` | $0.85$ | $10.93$ | $0.466$ | $1.37$ ($109\sigma$) | $0.89$ | `HIGH_CONF` | $-0.020$ | `0000` / AAAU | `MAIN_SEQUENCE` (HIGH) | Early F dwarf |
| **3** | **SPX-J169.3604-70.1582** | $6.7985$ | $14.71$ | $0.97$ | 7 | `HIGH_CONF` | $0.36$ | $10.96$ | $0.386$ | $2.17$ ($169\sigma$) | $0.86$ | `HIGH_CONF` | $-0.011$ | `dd00` / AAAU | `MAIN_SEQUENCE` (HIGH) | Late A dwarf |
| **4** | **SPX-J170.5689-70.3501** | $6.4039$ | $27.55$ | $1.11$ | 5 | `HIGH_CONF` | $0.36$ | $10.92$ | $0.285$ | $0.86$ ($57\sigma$) | $0.85$ | `HIGH_CONF` | $-0.018$ | `hh00` / AAAU | `MAIN_SEQUENCE` (HIGH) | A-type star ($M_G = 0.61$) |
| **5** | **SPX-J169.5086-69.7227** | $6.0871$ | $33.51$ | $1.00$ | 4 | `HIGH_CONF` | $0.16$ | $10.67$ | $0.187$ | $0.87$ ($67\sigma$) | $0.85$ | `HIGH_CONF` | $-0.009$ | `0000` / AAAC | `MAIN_SEQUENCE` (HIGH) | Early A star ($M_G = 0.37$) |
| **6** | **SPX-J166.6596-67.8821** | $5.3655$ | $21.61$ | $1.05$ | 4 | `PROBABLE` | $0.75$ | $10.82$ | $0.444$ | $0.79$ ($65\sigma$) | $1.01$ | `HIGH_CONF` | $-0.012$ | `0000` / AAAC | `MAIN_SEQUENCE` (HIGH) | F-type subgiant/dwarf |
| **7** | **SPX-J169.5526-69.7526** | $5.3115$ | $11.79$ | $1.00$ | 5 | `HIGH_CONF` | $0.50$ | $11.23$ | **$0.760$** | $1.54$ ($54\sigma$) | $1.79$ | `HIGH_CONF` | $+0.002$ | `0o00` / AAAU | `MAIN_SEQUENCE` (HIGH) | **Late F / Early G dwarf** |
| **8** | **SPX-J169.8790-70.1676** | $4.7709$ | $14.10$ | $1.04$ | 6 | `PROBABLE` | $0.59$ | $11.11$ | **$0.646$** | $2.07$ ($145\sigma$) | $0.99$ | `HIGH_CONF` | $-0.014$ | `0000` / AAAU | `MAIN_SEQUENCE` (HIGH) | **Late F dwarf** |
| **9** | **SPX-J160.5956-70.1226** | $4.7248$ | $11.21$ | $0.40$ | 5 | `HIGH_CONF` | $0.41$ | $10.86$ | $0.011$ | $0.83$ ($49\sigma$) | $0.88$ | `HIGH_CONF` | $-0.049$ | `00PP` / AAAU | `MAIN_SEQUENCE` (HIGH) | Late B / Early A star |
| **10** | **SPX-J169.6630-69.1283** | $4.7244$ | $12.39$ | $1.29$ | 3 | `PROBABLE` | $0.62$ | $11.12$ | **$0.830$** | $3.94$ ($292\sigma$) | $0.90$ | `HIGH_CONF` | $-0.024$ | `d000` / AAAU | `MAIN_SEQUENCE` (HIGH) | **G / Early K dwarf** |

### 2. Critical Audit Findings on Top 10 Anomalies:
1. **$BP - RP \le 0.47$ Claim is INCORRECT:**
   - **Only 7 of the 10 sources** have $BP - RP \le 0.47$.
   - Source 7 has $BP - RP = \mathbf{0.760}$ (solar-type G star).
   - Source 8 has $BP - RP = \mathbf{0.646}$ (late F star).
   - Source 10 has $BP - RP = \mathbf{0.830}$ (G/K dwarf, $T_{\text{eff}} \sim 5300\,\text{K}$).
   - The blanket claim that all 10 are A/F dwarf stars with $BP - RP \le 0.47$ directly contradicts the database records.
2. **Fabricated Apparent Magnitudes in Report Table 3:**
   - Table 3 in [`reports/F1_PHASE2_TASK4_SPECTRA_CORRELATION.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/F1_PHASE2_TASK4_SPECTRA_CORRELATION.md) listed $G$ magnitudes between $13.68$ and $14.82$ (e.g. Rank 1: $14.12$, Rank 2: $14.39$).
   - In actual Gaia DR3 astrometry, **all 10 sources are bright optical stars with $G \in [10.67, 11.23]$**.
   - These values appear to have been typed erroneously or copied from an unrelated catalog.
3. **Severe Channel Sparsity in Top Anomalies:**
   - The SPHEREx 102-channel spectrophotometric vector has only **3 to 7 valid channels** for these top anomalies (e.g. Rank 2 has 3 channels; Rank 10 has 3 channels).
   - High reconstruction error ($\chi^2 \sim 5 - 8$) computed over only 3 to 7 degrees of freedom is highly susceptible to small-number channel levering rather than comprehensive broadband SED failure.

---

## 4. Audit of SPECTRA v2 Training Distribution Claims

Task 4 claimed:
> *"SPECTRA v2 was trained on Pointing 0001, where the majority of high-SNR extractions were cool red giants ($T_{\text{eff}} \approx 4200\,\text{K}$, $BP - RP \sim 1.3$)."*

### Forensic Verification of Repository Assets:
1. The training pipeline [`models/spectra/train_masked_spectra.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/models/spectra/train_masked_spectra.py) was trained on 2,416 sources from `data/processed/spectral_features/validation_assembled_spectra.csv` matching Pointing 0001.
2. An exhaustive scan of the repository reveals that **Pointing 0001 was never cross-matched against Gaia DR3 or AllWISE**.
3. No optical colors ($BP - RP$), Gaia magnitudes ($G$), or spectroscopic temperatures exist on disk for the 2,416 training sources.
4. **Audit Verdict:** The claim that the training population was predominantly cool red giants is **UNVERIFIED**. While stellar population synthesis models predict that red giants dominate flux-limited infrared surveys at low Galactic latitudes, asserting this as an empirical fact without catalogue evidence violates validation standards.

### Distinction: Domain Shift vs Genuine Anomaly
Autoencoders minimize reconstruction loss over empirical training distributions. If an autoencoder trains on cooler stars, hot A/F stars with steep Rayleigh-Jeans slopes will naturally produce elevated reconstruction errors ($\chi^2_{\text{D1}} \sim 15 - 33$).
- This is an **out-of-distribution (OOD) / domain-shift effect**, not an astrophysical anomaly.
- The stars themselves are standard, single main-sequence stars following normal stellar physics.

---

## 5. Reassessment of Candidate `SPX-J166.9881-70.9094`

Task 4 identified `SPX-J166.9881-70.9094` as a Young Stellar Object (YSO) / circumstellar dust debris disk candidate.

### 1. Multi-Wavelength Observational Profile

| Parameter | Measured Value | Standard Error / Flag | Physical Meaning |
| :--- | :---: | :---: | :--- |
| **SPHEREx Coordinates** | $(166.988083^\circ, -70.909396^\circ)$ | Level-2 science frame | Spatial centroid |
| **Gaia DR3 ID** | `5228488578215714048` | $d_{\text{prop}} = 0.205''$ | Astrometrically pristine match |
| **Gaia $G$ / $BP$ / $RP$** | $10.918$ / $11.002$ / $10.710$ | $\sigma < 0.003\,\text{mag}$ | Bright early-type star |
| **Gaia Color ($BP - RP$)** | **$+0.291$** | Photometric clean | Hot stellar photosphere ($T_{\text{eff}} \sim 8000\,\text{K}$) |
| **Gaia RUWE** | **$1.051$** | Nominal single star | Zero astrometric disturbance |
| **Gaia Proper Motion** | $\mu_{\alpha*} = -8.17, \mu_\delta = +1.28$ | $|\mu| = 8.27\,\text{mas/yr}$ | Verified Galactic disk kinematics |
| **Gaia Parallax ($\varpi$)** | **$0.0545\,\text{mas}$** | $\sigma_\varpi = 0.0159\,\text{mas}$ ($\mathbf{3.43\sigma}$) | Inverted distance $d \sim 18.4\,\text{kpc}$ (uncalibrated) |
| **AllWISE Designation** | `J110757.14-705433.9` | $d = 0.125''$ | Perfect spatial concordance |
| **AllWISE W1 ($3.4\,\mu\text{m}$)** | **$9.762\,\text{mag}$** | $\sigma = 0.022\,\text{mag}$ ($\text{SNR} = 48.3$) | High-SNR detection |
| **AllWISE W2 ($4.6\,\mu\text{m}$)** | **$9.454\,\text{mag}$** | $\sigma = 0.020\,\text{mag}$ ($\text{SNR} = 55.4$) | High-SNR detection |
| **Mid-IR Color ($W1 - W2$)** | **$+0.308\,\text{mag}$** | $\sigma = \mathbf{0.030\,\text{mag}}$ | **$+10\sigma$ infrared excess** |
| **AllWISE Quality Flags** | `cc_flags = '0000'`, `ph_qual = 'AAAA'` | `ext_flg = 0.0` | Pristine point source, zero contamination |
| **SPHEREx Benchmark Score** | $\chi^2_{\text{B}} = \mathbf{0.2966}$ | 8 valid channels | Nominal fit (below survey median $0.358$) |

### 2. Discrepancy in Task 4 Documentation
Line 88 of [`reports/F1_PHASE2_TASK4_SOURCE_CLASSIFICATION.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/F1_PHASE2_TASK4_SOURCE_CLASSIFICATION.md) reported:
`Warm mid-infrared excess: W1 - W2 = +0.308 (W1 = 10.51, W2 = 10.20)`
- In the actual AllWISE database, **$W1 = 9.762$ and $W2 = 9.454$**.
- While the difference $W1 - W2 = 0.308$ is exact, the reported magnitudes were incorrect.

### 3. Rigorous Astrophysical Reassessment
- **Is Infrared Excess Present?**
  **YES.** For an A-type star ($BP - RP = 0.291$), photospheric Rayleigh-Jeans emission predicts $W1 - W2 \approx 0.00 \pm 0.02$. The observed color $W1 - W2 = +0.308 \pm 0.030$ represents a statistically significant $+10\sigma$ excess with clean AllWISE flags (`0000`/`AAAA`).
- **Can it be Confirmed as a YSO or Debris Disk?**
  **NO.** 
  1. The small parallax ($\varpi = 0.054\,\text{mas}$) carries substantial zero-point uncertainty in Gaia DR3 (typical zero-point offset $\sim -0.02\,\text{mas}$).
  2. If the star is at $d > 5\,\text{kpc}$, it is a luminous supergiant or classical Be star whose infrared excess originates from circumstellar free-free plasma emission rather than young dust.
  3. Alternatively, an unresolved cool M-dwarf companion could produce apparent infrared brightening.
  4. Without optical spectroscopy (detecting $\text{H}\alpha$ emission, Li I $\lambda 6708$ absorption) or mid-IR spectroscopy (silicate/PAH features), **a definitive YSO or debris disk classification is scientifically unsupportable**.

### 4. Reassessment Conclusion
`SPX-J166.9881-70.9094` is classified as a **Probable Infrared-Excess Source / Circumstellar Dust Candidate**, but remains **UNCONFIRMED as a YSO or debris disk**.

---

## 6. Correlation Audit Conclusion

| Audit Item | Task 4 Claim | Forensic Audit Finding | Validation Status |
| :--- | :--- | :--- | :--- |
| **RUWE Anomaly Score** | Mean $\chi^2 = 3.37$, proves binarity | Actual mean $\chi^2 = 0.92$, median $0.37$ (vs $0.36$ for RUWE $\le 2.0$), $p = 0.34$ | **INCORRECT** |
| **Top 10 Anomalies** | All 10 are A/F dwarfs with $BP - RP \le 0.47$ | 3 of 10 have $BP - RP > 0.47$ (up to $0.83$); $G$ mags in report table fabricated/erroneous | **INCORRECT** |
| **Training Population** | Predominantly cool red giants | Zero Gaia cross-match data exist for Pointing 0001 training cohort | **UNVERIFIED** |
| **YSO Candidate** | Confirmed YSO / debris disk discovery | Valid $+10\sigma$ IR excess, but unconfirmed without spectroscopic follow-up | **PROVISIONAL / UNCONFIRMED** |

