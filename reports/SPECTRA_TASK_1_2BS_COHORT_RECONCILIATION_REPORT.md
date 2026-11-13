# SPECTRA-X / F1 — Phase 3, Task 1.2B-S: Calibration Cohort Reconciliation & Statistical Design Verification Report

**Task Identifier:** `SPECTRA_TASK_1_2B_S`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Timestamp:** 2026-11-07T04:15:00Z  
**Execution Mode:** STRICT READ-ONLY AUDIT  
**Audit Target:** Task 1.2B-R Calibration Readiness Ledger, Cohort Size Semantics & Statistical Protocol  
**Governance Basis:** Explicitly Authorized by Project Owner  
**Module Audited:** SPECTRA — 102-Channel Infrared Spectral Anomaly Detection Engine  

---

## 1. Executive Summary

Task 1.2B-S conducted an exhaustive, independent, strictly read-only numerical audit and reconciliation of the calibration cohort sizes, detector-pair counts, training-overlap exclusions, and statistical design originally reported in Task 1.2B-R.

### Core Audit Findings

1. **Resolution of the 5,327 vs 5,347 Discrepancy:**  
   The apparent numerical mismatch in Task 1.2B-R is definitively resolved. It was caused by a clerical typographical error in Table 7.1 of that report, which transcribed the `D1+D4` reliable count ($\ge 5$ channels) as **1,175** instead of the verified count of **1,155** (+20 error). All detector-pair categories are strictly mutually exclusive ($N_{\text{overlap}} = 0$). The true, verified count of reliable point sources with $\ge 5$ valid channels is **5,327** ($1,155 + 2,624 + 1,548 = 5,327$). After excluding the 5 historical training overlap sources, the clean calibration total is **5,322**.
2. **Verification of the 5 Historical Training Overlaps:**  
   All five reported Gaia DR3 source IDs (`6316932723797678080`, `6268273836710905344`, `6316494229114061952`, `6316495122467403776`, `6316948567937380224`) were traced to exact celestial coordinate matches ($<0.75''$) within `data/processed/spectral_features/validation_assembled_spectra.csv`. Crucially, **all five sources belong to Pointing 0001 under detector pair `D1,D4` with 8 valid channels**. Pointing `0008` has strictly **zero** training overlaps.
3. **P0008-Only Out-of-Sample Calibration Baseline:**  
   Pointing `0008` provides **3,206** uncorrupted, out-of-sample, reliable point sources with $\ge 5$ valid channels:
   - `D1+D4`: **1,055 sources**
   - `D2+D5`: **1,304 sources**
   - `D3+D6`: **847 sources**  
   Sum: $1,055 + 1,304 + 847 = \mathbf{3,206}$. Zero sources in P0008 overlap with historical training data.
4. **Statistical Design & Tail Estimation Limits:**  
   At $\alpha = 0.05$, empirical tail estimation is well-powered across all three pairs in P0008 ($E[K] = 42\text{--}65$ events). At $\alpha = 0.01$, tail sample counts are modest ($E[K] \approx 11$ in D1+D4, $E[K] \approx 13$ in D2+D5, and $E[K] \approx 8$ in D3+D6); bootstrap confidence intervals are mandatory to quantify tail uncertainty.
5. **Final Readiness Verdict:**  
   **CONDITIONALLY READY FOR TASK 1.2C**, subject to five strict operational safeguards.

---

## 2. Scope and Governance Restrictions

This audit was conducted strictly in read-only mode:

- **Zero Modifications:** Checkpoint weights, source code, Level-2 science FITS images, catalogs, and historical reports were preserved byte-for-byte immutable.
- **Zero Model Evaluation:** No forward passes, latent space projections, reconstruction loss scores, or anomaly quantiles were computed.
- **Zero Threshold Manipulation:** No operational cutoffs were derived, chosen, or frozen.
- **Zero Label Mutation:** Source classifications from Task 1.1O and partition memberships from Task 1.1M/1.2B were held immutable.

---

## 3. Input Asset Verification and Cryptographic Ledger

### Table 3.1: Cryptographic Input Ledger

| Asset Path | Byte Size | SHA-256 Hash | Verification Status |
|:---|:---:|:---:|:---:|
| `checkpoints/spectra_masked_ae_v2.pt` | 382,177 | `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938` | Frozen Candidate Verified |
| `data/processed/spectra/phase3_multpointing_spectra_v1.csv` | 332,189,097 | `8a96617cfe5d5152e720ee0c3890a7b8c7025ab2bfb3c682e08743affe6858e0` | Verified Immutable |
| `data/processed/spectra/phase3_multpointing_coverage_v1.csv` | 3,293,848 | `c8153bf0b0f07f4bde753b12309d06613fed6a90527cfd2409d7438218262c30` | Verified Immutable |
| `data/processed/spectra/phase3_multpointing_extraction_manifest_v1.json` | 93,107 | `e9fa9cfee57a99850d1ef617e0a875aac473530cfa76c416a52802180c87e777` | Verified Immutable |
| `data/processed/spectral_features/validation_assembled_spectra.csv` | 31,529,885 | `bb693cfa3aa8ff4405d4b533a6b8d96b9f471df46eeec6113b2d6a5035f29d9a` | Historical Training Data Verified |
| `reports/SPECTRA_TASK_1_2BR_CALIBRATION_READINESS_AUDIT.md` | 20,449 | `dc44109ace8bc54895a81a0a6551c045fd11b31ba4f36e21b4831bbd11494cf7` | Previous Audit Verified |
| `reports/manifests/spectra_task_1_2br_readiness_manifest.json` | 6,658 | `41cdd287796bc33ef7b4deb160fd8e82b713388eaeb173e675a725b352536265` | Previous Manifest Verified |

---

## 4. AUDIT A — Reconcile the 5,327 vs 5,347 Discrepancy

In the Task 1.2B-R audit report, two inconsistent numbers appeared:
- Section 6.1 and Section 9 reported total reliable calibration sources with $\ge 5$ channels as **5,327** (and **5,322** after excluding 5 training overlap sources).
- Section 7, Table 7.1 reported pair-wise counts of: D1+D4: **1,175**, D2+D5: **2,624**, D3+D6: **1,548**, summing to **5,347** ($5,347 - 5,327 = +20$).

### 4.1 Independent Recomputation

An independent query across the primary extracted data tables (`phase3_multpointing_spectra_v1.csv` and `phase3_multpointing_coverage_v1.csv` merged with `pointing_0001_source_catalogue.csv` and `pointing_0008_source_catalogue.csv`) yielded:

1. **Mutual Exclusivity of Detector Categories:**  
   Every single source in the catalog has exactly ONE unique `detector_provenance` string. Across all 37,500 catalog sources, zero sources have ambiguous, overlapping, or multi-string classifications.
2. **True Pair-Wise Reliable Sources with $\ge 5$ Channels:**
   - **`D1,D4`:** Exactly **1,155 sources** (P0001: 100, P0008: 1,055).
   - **`D2,D5`:** Exactly **2,624 sources** (P0001: 1,320, P0008: 1,304).
   - **`D3,D6`:** Exactly **1,548 sources** (P0001: 701, P0008: 847).
   - **Sum:** $1,155 + 2,624 + 1,548 = \mathbf{5,327}$.
3. **Identification of the Typographical Error:**  
   The number **1,175** in Table 7.1 of Task 1.2B-R was a clerical transcription error: $1,155 + 20 = 1,175$. In that same table, the count of single-detector `D4` sources in P0008 was 20. The author erroneously added 20 or mistyped the tens digit, which cascaded into the printed total of 5,347.
4. **Single-Detector Sources:**  
   Single-detector sources (`D1` through `D6`) observe at most 4 dither channels. Exactly **0** single-detector sources possess $\ge 5$ channels.

### Table 4.1: Exact Reconciliation Ledger

| Metric / Dimension | Previous Reported Value (1.2B-R) | Independently Recomputed Value | Discrepancy | Provenance & Technical Explanation |
|:---|---:|---:|---:|:---|
| **D1+D4 ($\ge 5$ ch, Reliable)** | 1,175 | **1,155** | $-20$ | Clerical typo in Table 7.1 (typed 1,175 instead of verified 1,155). |
| **D2+D5 ($\ge 5$ ch, Reliable)** | 2,624 | **2,624** | $0$ | Verified exact match. |
| **D3+D6 ($\ge 5$ ch, Reliable)** | 1,548 | **1,548** | $0$ | Verified exact match. |
| **Pair-Wise Sum** | 5,347 | **5,327** | $-20$ | Matches true underlying catalog total ($1,155 + 2,624 + 1,548 = 5,327$). |
| **Historical Training Overlaps** | 5 | **5** | $0$ | Verified exact match (all 5 belong to D1+D4 in Pointing 0001). |
| **Clean Reconciled Total** | 5,322 | **5,322** | $0$ | True clean calibration candidates ($5,327 - 5 = 5,322$). |

---

## 5. AUDIT B — Verification of the Five Historical Training Overlaps

The five source IDs reported in Task 1.2B-R were verified against the historical training catalog `data/processed/spectral_features/validation_assembled_spectra.csv` ($N=3,665$ records, of which 2,416 belong to Pointing 0001):

### Table 5.1: Detailed Verification of Historical Training Overlaps

| Gaia DR3 Source ID | Calibration Pointing | Detector Pair | Valid Channels | Astrometric Separation to Training Match | Historical Training Source ID | Historical Observation Provenance | Exclusion Status |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `6316932723797678080` | `0001` | `D1,D4` | 8 | $0.4200''$ | `SPX-J234.5044-10.4185` | `2026W30_1B_0001_1,3` | **EXCLUDED** |
| `6268273836710905344` | `0001` | `D1,D4` | 8 | $0.5596''$ | `SPX-J234.1214-11.9035` | `2026W30_1B_0001_1,2,3` | **EXCLUDED** |
| `6316494229114061952` | `0001` | `D1,D4` | 8 | $0.1446''$ | `SPX-J234.4153-10.8582` | `2026W30_1B_0001_2,3` | **EXCLUDED** |
| `6316495122467403776` | `0001` | `D1,D4` | 8 | $0.7350''$ | `SPX-J234.4199-10.7980` | `2026W30_1B_0001_3,4` | **EXCLUDED** |
| `6316948567937380224` | `0001` | `D1,D4` | 8 | $0.5488''$ | `SPX-J234.6015-10.1289` | `2026W30_1B_0001_2,4` | **EXCLUDED** |

### Key Findings
1. All 5 sources reside within Pointing `0001` and were observed in the `D1,D4` pair with full 8-channel coverage.
2. All 5 sources have separations $<0.75''$ to their training counterparts, confirming physical identity.
3. Astrometric cross-matching across all 15,000 calibration sources revealed that **zero other sources** in the `RELIABLE_ISOLATED_POINT_SOURCE` category match the training catalog. (Three additional matches in P0001 reside in `BLENDED_CROWDED` [$N=2$] and `UNCERTAIN_OR_LOW_QUALITY` [$N=1$] and are already excluded by quality cuts).
4. Pointing `0008` has **zero** matches at any separation (minimum distance $>69.89^\circ$).

---

## 6. AUDIT C — Recomputed P0008-Only Calibration Eligibility

Because Pointing `0001` was the historical training field for `spectra_masked_ae_v2.pt`, Pointing `0008` is proposed as the primary, uncorrupted, out-of-sample calibration benchmark.

### Table 6.1: Full Quantitative Accounting for Pointing 0008

| Accounting Dimension | Total Catalog Sources | Reliable Point Sources | Unsuitable / Flagged Sources |
|:---|---:|---:|---:|
| **Total Sources in Pointing 0008** | **7,500** | **5,695** | **1,805** |
| — Unobserved ($N_{\text{valid}} = 0$, outside detector footprint) | 1,521 | 1,139 | 382 |
| — Observed ($N_{\text{valid}} > 0$) | 5,979 | 4,556 | 1,423 |
| **Observed Channel Sparsity Distribution:** | | | |
| — 1 Valid Channel (boundary fringe detections) | 87 | 54 | 33 |
| — 2 Valid Channels (partial dither overlaps) | 923 | 711 | 212 |
| — 3–4 Valid Channels (single-detector visits) | 761 | 585 | 176 |
| — 5–10 Valid Channels (5–8 ch, dichroic pairs) | **4,208** | **3,206** | **1,002** |
| — $>10$ Valid Channels (physically impossible in single pointing) | 0 | 0 | 0 |
| **Dichroic Pair Breakdown for $\ge 5$ Channels:** | | | |
| — `D1,D4` | 1,353 | **1,055** | 298 |
| — `D2,D5` | 1,605 | **1,304** | 301 |
| — `D3,D6` | 1,250 | **847** | 403 |
| — Single-Detector Arrays (`D1`–`D6`) | 0 | 0 | 0 |
| **Historical Training Overlaps in Pointing 0008:** | **0** | **0** | **0** |
| **Final Eligible P0008 Calibration Candidates ($\ge 5$ ch):** | — | **3,206** | — |

*Scientific Note:* These 3,206 sources are **Provisional Control Candidates** based on external Gaia DR3/2MASS point-source cleanliness. They are NOT verified astrophysical null controls, as no ground-truth spectroscopic confirmation exists.

---

## 7. AUDIT D — Verify Detector-Pair Count Semantics

The table below reconciles the full calibration cohort across all stages of filtering:

### Table 7.1: Comprehensive Detector-Pair Semantic Breakdown

| Metric | Pair: `D1,D4` | Pair: `D2,D5` | Pair: `D3,D6` | Single Detectors (`D1`–`D6`) | Unobserved (`NONE`) | Total Calibration Cohort |
|:---|---:|---:|---:|---:|---:|---:|
| **All Observed Sources (P0001 + P0008)** | 2,028 | 3,884 | 3,248 | 217 | 0 | **9,377** |
| — Contributing P0001 Sources | 122 | 2,020 | 1,173 | 83 | 4,102 | 7,500 |
| — Contributing P0008 Sources | 1,906 | 1,864 | 2,075 | 134 | 1,521 | 7,500 |
| **Reliable Point Sources (Total Observed)** | 1,581 | 2,973 | 2,482 | 102 | 0 | **7,138** |
| — P0001 Reliable Count | 109 | 1,462 | 968 | 43 | 3,103 | 5,685 |
| — P0008 Reliable Count | 1,472 | 1,511 | 1,514 | 59 | 1,139 | 5,695 |
| **Reliable Sources with $\ge 5$ Channels** | **1,155** | **2,624** | **1,548** | **0** | **0** | **5,327** |
| — P0001 Reliable ($\ge 5$ ch) | 100 | 1,320 | 701 | 0 | 0 | 2,121 |
| — P0008 Reliable ($\ge 5$ ch) | 1,055 | 1,304 | 847 | 0 | 0 | 3,206 |
| **Historical Training Overlaps** | **5** | **0** | **0** | **0** | **0** | **5** |
| — P0001 Overlaps | 5 | 0 | 0 | 0 | 0 | 5 |
| — P0008 Overlaps | 0 | 0 | 0 | 0 | 0 | 0 |
| **Clean Reconciled Total (P0001 + P0008)** | **1,150** | **2,624** | **1,548** | **0** | **0** | **5,322** |
| **Primary Out-of-Sample Cohort (P0008 Only)** | **1,055** | **1,304** | **847** | **0** | **0** | **3,206** |

---

## 8. AUDIT E — Statistical Design Verification

### 8.1 Empirical Tail Estimation Limits on P0008 ($N = 3,206$)

When estimating empirical quantiles $q_{1-\alpha}$ from the out-of-sample P0008 sample:

- **At $\alpha = 0.05$ (95th Percentile):**
  - `D1+D4` ($N = 1,055$): Expected tail count $E[K] = 1,055 \times 0.05 = \mathbf{52.75}$ events.
  - `D2+D5` ($N = 1,304$): Expected tail count $E[K] = 1,304 \times 0.05 = \mathbf{65.20}$ events.
  - `D3+D6` ($N = 847$): Expected tail count $E[K] = 847 \times 0.05 = \mathbf{42.35}$ events.
  - *Assessment:* Well-powered. All pairs comfortably exceed the minimum threshold of $k \ge 20$ tail events required for stable non-parametric empirical quantile estimation.
- **At $\alpha = 0.01$ (99th Percentile):**
  - `D1+D4`: Expected tail count $E[K] = 1,055 \times 0.01 = \mathbf{10.55}$ events.
  - `D2+D5`: Expected tail count $E[K] = 1,304 \times 0.01 = \mathbf{13.04}$ events.
  - `D3+D6`: Expected tail count $E[K] = 847 \times 0.01 = \mathbf{8.47}$ events.
  - *Assessment:* Severely constrained. For `D3+D6`, only $\sim 8$ sources define the tail. The arrival or departure of a single outlier shifts the empirical quantile by $\sim 12\%$. Therefore, $\alpha = 0.01$ threshold estimates on P0008 must carry explicit bootstrap confidence intervals.

### 8.2 Source-Level vs Spatial-Block Bootstrap

1. **Source-Level Bootstrap:** Resampling individual sources with replacement estimates the finite-sample variance of the empirical quantile under an I.I.D. assumption. However, it completely fails to capture intra-pointing spatial correlations (e.g. large-scale zodiacal gradients, stray light, or focal plane temperature variations).
2. **Spatial-Block Bootstrap:**  
   - Pointing `0008` spans $\Delta \alpha \approx 10.7^\circ$ and $\Delta \delta \approx 5.9^\circ$.
   - Defining spatial blocks of $1.0^\circ \times 1.0^\circ$ yields approximately $35\text{--}40$ occupied spatial cells.
   - Resampling spatial blocks preserves localized spatial correlation.
   - *Limitation:* While block bootstrap captures intra-field spatial covariance, it remains strictly conditional on Pointing `0008`'s specific celestial line of sight ($l \approx 150^\circ, b \approx -50^\circ$). It cannot extrapolate to the completely different Galactic environment of P0002 ($b \approx +24^\circ$) or P0010 ($b \approx +28^\circ$).

### 8.3 Role of Pointing 0001
Because Pointing `0001` was part of the original model training domain:
- **Permitted Use:** Descriptive distribution comparison and domain-shift diagnostics (measuring whether P0001 scores systematically underpredict P0008 scores due to training memorization).
- **Prohibited Use:** Primary null calibration or independent generalization validation.

---

## 9. AUDIT F — Calibration Protocol Recommendation

Based on the verified evidence, the final governance verdict is:

$$\mathbf{CONDITIONALLY\ READY\ FOR\ TASK\ 1.2C}$$

### Five Mandatory Operational Safeguards for Task 1.2C

1. **Primary Out-of-Sample Null Baseline:** Derive the primary null calibration distributions exclusively from Pointing `0008` ($N = 3,206$ clean reliable sources with $\ge 5$ channels).
2. **Dichroic Pair Stratification:** Establish separate operating thresholds for `D1+D4`, `D2+D5`, and `D3+D6`. A single pooled threshold is strictly prohibited.
3. **Training Source Exclusion:** In all secondary P0001 diagnostics, exclude the 5 verified training overlap sources (`6316932723797678080`, `6268273836710905344`, `6316494229114061952`, `6316495122467403776`, `6316948567937380224`).
4. **Finite-Sample Uncertainty Reporting:** Report bootstrap confidence intervals ($\pm 1\sigma$) on all thresholds, highlighting the tail sparsity of $\alpha = 0.01$.
5. **Rigorous Semantic Distinction:** Explicitly report thresholds as **Empirical Provisional-Null Quantiles**, NOT production-certified false-positive rates.

---

## 10. Protected Asset Integrity Check

All protected assets remain byte-for-byte immutable:
- `checkpoints/spectra_masked_ae_v2.pt`: Verified unchanged (`SHA-256: 6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938`).
- `data/processed/spectra/phase3_multpointing_spectra_v1.csv`: Verified unchanged (`SHA-256: 8a96617cfe5d5152e720ee0c3890a7b8c7025ab2bfb3c682e08743affe6858e0`).
- No model inference was executed; zero thresholds were computed or selected.

---

## 11. Deliverables and Cryptographic Hashes

1. **Reconciliation Audit Report:**  
   [`reports/SPECTRA_TASK_1_2BS_COHORT_RECONCILIATION_REPORT.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/SPECTRA_TASK_1_2BS_COHORT_RECONCILIATION_REPORT.md)
2. **Reconciliation Governance Manifest:**  
   [`reports/manifests/spectra_task_1_2bs_reconciliation_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/manifests/spectra_task_1_2bs_reconciliation_manifest.json)
3. **Reproducibility Test Suite:**  
   [`tests/test_spectra_task_1_2bs_reconciliation.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/tests/test_spectra_task_1_2bs_reconciliation.py)

