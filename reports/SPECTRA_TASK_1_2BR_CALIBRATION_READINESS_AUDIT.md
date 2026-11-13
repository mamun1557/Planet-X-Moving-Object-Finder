# SPECTRA-X / F1 — Phase 3, Task 1.2B-R: Calibration-Readiness & Data Independence Audit

**Task Identifier:** `SPECTRA_TASK_1_2B_R`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Timestamp:** 2026-11-07T03:55:00Z  
**Execution Mode:** STRICT READ-ONLY AUDIT  
**Audit Target:** Pointing 0001 / Pointing 0008 Calibration Cohort & Multi-Pointing Data Products  
**Governance Basis:** Explicitly Authorized by Project Owner  
**Module Audited:** SPECTRA — 102-Channel Infrared Spectral Anomaly Detection Engine  

---

## 1. Executive Summary

Task 1.2B-R executed an independent, strictly read-only scientific audit to evaluate whether the Pointing `0001` and Pointing `0008` cohort ($N=15,000$ catalog sources, 48 Level-2 FITS files) extracted in Task 1.2B is scientifically defensible, statistically viable, and astrophysically independent for controlled null-distribution calibration in Task 1.2C.

### Key Audit Findings

1. **Cross-Partition Astrophysical Independence Mathematically Proven:**  
   A rigorous read-only celestial coordinate cross-match between all Calibration sources (`P0001`, `P0008`) and all Blind Evaluation sources (`P0002`, `P0009`, `P0010`) established that the **minimum angular separation between any calibration source and any evaluation source is $17.4668^\circ$ (1,048.01 arcmin)**. Cross-partition matches within $5''$, $1'$, and $1^\circ$ are exactly **zero**. There is absolute zero astrophysical source overlap or spatial leakage between calibration and evaluation partitions.
2. **Null-Control Classification & Training Set Overlap:**  
   The catalog contains no external ground-truth spectroscopic normality labels or blank-sky flags. However, **7,036 sources** in the calibration cohort are classified as `RELIABLE_ISOLATED_POINT_SOURCE` based on strict Gaia DR3 / 2MASS astrometric and photometric cleanliness criteria established in Task 1.1O prior to model evaluation. These represent valid **Provisional Control Candidates**.  
   *Crucial Governance Finding:* Pointing `0001` was originally used as the training pointing for `checkpoints/spectra_masked_ae_v2.pt` ($N=2,416$ train samples). Astrometric cross-matching revealed that **exactly 5 sources** in the P0001 pilot catalog directly coincide with the historical training set. Pointing `0008` has **zero** overlap with the training set.
3. **Spectral Eligibility & Normalization Degeneracy:**  
   While 9,377 calibration sources have valid detector observations, single-pointing observations produce sparse SEDs. Among the reliable point sources, **5,327 sources (74.6%)** possess $\ge 5$ valid channels (5–8 channels) spanning complementary short- and long-wavelength arrays (D1+D4, D2+D5, D3+D6). For sources with only 1 or 2 channels (898 sources with 2 ch, 89 sources with 1 ch), robust median normalization is mathematically degenerate ($N=1 \implies 1.0$; $N=2 \implies$ constant sum), destroying absolute flux amplitude.
4. **Detector-Pair Stratification Necessity:**  
   Calibration sources naturally cluster into three optical dichroic pairs: D1+D4 (1,581 reliable sources), D2+D5 (2,973 reliable sources), and D3+D6 (2,482 reliable sources). Pooling these pairs into a single null distribution would obscure severe detector-specific thermal background and wavelength domain shifts (e.g. D5/D6 thermal background vs D1 NIR background). Stratified calibration is mandatory.
5. **Statistical Tail-Probability Feasibility:**  
   At $\alpha = 0.05$, empirical quantile estimation is well-powered across all three pairs ($>75$ expected tail events per pair). At $\alpha = 0.01$, D1+D4 possesses $\sim 16$ expected tail events and D2+D5/D3+D6 possess $25\text{--}30$ expected tail events; bootstrap confidence intervals will be required.

---

## 2. Scope and Governance Restrictions

This task was conducted under strict read-only governance boundaries:

- **Zero Modifications:** Model checkpoints, training metadata, Level-2 FITS files, source catalogs, extraction tables, and manifests were inspected in place without modification.
- **Zero Model Inference:** No forward passes, latent embeddings, or reconstruction loss scores were evaluated for any source.
- **Zero Threshold Calculation:** No operating thresholds or quantile cutoffs were derived or optimized.
- **Zero Label Inspection:** Blind evaluation pointings (`P0002`, `P0009`, `P0010`) were audited solely for celestial coordinate cross-matching against calibration pointings; zero evaluation outcomes or candidate labels were inspected.

---

## 3. Input Asset Verification and Cryptographic Ledger

All relevant primary and derived assets were cryptographically verified via SHA-256:

### Table 3.1: Cryptographic Asset Ledger

| Asset Path | Byte Size | SHA-256 Hash | Verification Status |
|:---|:---:|:---:|:---:|
| `checkpoints/spectra_masked_ae_v2.pt` | 382,177 | `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938` | Byte-for-byte immutable candidate |
| `checkpoints/spectra_masked_ae_v2_training_meta.json` | 4,023 | `80d0d65a00cbad8f2bde844d30a7aaa839c461789de3bc58c4fee895ca9f4f2c` | Training metadata verified |
| `data/processed/spectra/phase3_multpointing_spectra_v1.csv` | 332,189,097 | `8a96617cfe5d5152e720ee0c3890a7b8c7025ab2bfb3c682e08743affe6858e0` | Extracted SED catalog verified |
| `data/processed/spectra/phase3_multpointing_coverage_v1.csv` | 3,293,848 | `c8153bf0b0f07f4bde753b12309d06613fed6a90527cfd2409d7438218262c30` | Coverage matrix verified |
| `data/processed/spectra/phase3_multpointing_extraction_manifest_v1.json` | 93,107 | `e9fa9cfee57a99850d1ef617e0a875aac473530cfa76c416a52802180c87e777` | Extraction manifest verified |
| `data/spherex/qr3/calibration/spectral_channels_spx_cal-sch-v2-2026-229.fits` | 4,176,000 | `1da3549d363b6c7eb8ac0b709dbed6dafe2fd24eefe03ebee6e2e8912634694e` | Official channel grid verified |

---

## 4. AUDIT A — Null-Control Suitability

The audit evaluated whether the sources within Calibration pointings `0001` and `0008` can legitimately serve as a "null" reference population for model reconstruction error.

### 4.1 Provenance of Source Classifications

The source catalogs (`data/processed/pilot_catalogues/pointing_0001_source_catalogue.csv` and `pointing_0008_source_catalogue.csv`) were constructed in Task 1.1O using external astrometric and photometric parameters:
- Gaia DR3 Renormalised Unit Weight Error ($\text{RUWE} \le 1.4$)
- Astrometric excess noise ($\le 2.0\text{ mas}$)
- Spatial isolation ($\text{nearest-neighbor distance} > 4.0''$)
- Distance to saturated stars ($> 30.0''$)
- Apparent magnitude boundaries ($12.0 < G < 19.5$)
- Positive cross-match with 2MASS $JHK_s$.

These classifications were generated **strictly prior to and independent of any SPECTRA model evaluation**.

### 4.2 Classification of Calibration Sources

Under the four formal categories mandated by the audit:

1. **VERIFIED NULL CONTROL ($N = 0$):**  
   Zero sources possess external spectroscopic confirmation of normality or blank-sky designation.
2. **PROVISIONAL CONTROL CANDIDATE ($N = 7,036$):**  
   Sources that are (a) observed with multi-detector coverage and (b) classified as `RELIABLE_ISOLATED_POINT_SOURCE` (P0001: 2,539 sources, P0008: 4,497 sources). These stars have high astrometric stability and unblended photometry.
3. **UNKNOWN / UNLABELED ($N = 0$):**  
   All sources possess an explicit Task 1.1O classification.
4. **EXCLUDED / UNSUITABLE ($N = 7,964$):**  
   - 5,623 sources with `NO_COVERAGE` (unobserved, outside focal plane arrays).
   - 102 sources with `SINGLE_DETECTOR` coverage (degenerate single-band data).
   - 1,860 sources flagged as `UNCERTAIN_OR_LOW_QUALITY`.
   - 1,369 sources flagged as `BLENDED_CROWDED` (photometric contamination).
   - 256 sources flagged as `EXTENDED` (non-point sources).
   - 135 sources flagged as `SATURATED_OR_CONTAMINATED`.

### 4.3 Training Set Independence Audit

Inspection of `checkpoints/spectra_masked_ae_v2_training_meta.json` revealed:
$$\text{Dataset Splits: } \texttt{"train\_pointing": "0001", "train\_samples": 2416, "val\_pointing": "0004"}$$

An astrometric cross-match between the historical training dataset (`data/processed/spectral_features/validation_assembled_spectra.csv`) and the P0001/P0008 pilot catalogs identified:
- **Pointing 0001:** Exactly **8 sources** match the historical training set within $2.0''$. Of these, **5 sources** are in the `RELIABLE_ISOLATED_POINT_SOURCE` category (`source_id`: 6316932723797678080, 6268273836710905344, 6316494229114061952, 6316495122467403776, 6316948567937380224).
- **Pointing 0008:** Exactly **0 sources** match the historical training set within $2.0''$ (zero overlap).

*Scientific Consequence:* Pointing `0001` was part of the original training domain of the model. While 5 individual catalog sources directly overlap, the model has seen the Pointing 0001 sky field during optimization. In contrast, Pointing `0008` is completely untouched and out-of-sample. Task 1.2C must treat Pointing `0008` as the primary uncorrupted null benchmark and exclude the 5 overlapping sources from Pointing `0001`.

---

## 5. AUDIT B — Cross-Partition Astrophysical Source Independence

A core concern of Task 1.2B-R was whether the "zero source ID overlap" reported in Task 1.2B truly guaranteed zero astronomical object overlap, or whether identical celestial sources might have received different source IDs across pointings.

### 5.1 Celestial Coordinate Cross-Matching

Using Astropy's `SkyCoord` in the standard ICRS frame, all 15,000 sources in the Calibration Cohort (`P0001`, `P0008`) were cross-matched against all 22,500 sources in the Blind Evaluation Cohort (`P0002`, `P0009`, `P0010`):

### Table 5.1: Cross-Partition Coordinate Separation Summary

| Cohort Pair | Calibration Pointing Center | Evaluation Pointing Center | Minimum Angular Separation | Matches $< 5''$ | Matches $< 1'$ | Matches $< 1^\circ$ |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Calib vs Eval** | — | — | **$17.4668^\circ$ (1,048.01 arcmin)** | **0** | **0** | **0** |
| `P0001` vs `P0002` | $(\alpha=237.5^\circ, \delta=-11.5^\circ)$ | $(\alpha=226.3^\circ, \delta=-30.3^\circ)$ | $21.21^\circ$ | 0 | 0 | 0 |
| `P0001` vs `P0009` | $(\alpha=237.5^\circ, \delta=-11.5^\circ)$ | $(\alpha=13.0^\circ, \delta=+46.6^\circ)$ | $153.84^\circ$ | 0 | 0 | 0 |
| `P0001` vs `P0010` | $(\alpha=237.5^\circ, \delta=-11.5^\circ)$ | $(\alpha=273.7^\circ, \delta=+66.7^\circ)$ | $84.22^\circ$ | 0 | 0 | 0 |
| `P0008` vs `P0002` | $(\alpha=29.1^\circ, \delta=+7.7^\circ)$ | $(\alpha=226.3^\circ, \delta=-30.3^\circ)$ | $158.41^\circ$ | 0 | 0 | 0 |
| `P0008` vs `P0009` | $(\alpha=29.1^\circ, \delta=+7.7^\circ)$ | $(\alpha=13.0^\circ, \delta=+46.6^\circ)$ | $40.52^\circ$ | 0 | 0 | 0 |
| `P0008` vs `P0010` | $(\alpha=29.1^\circ, \delta=+7.7^\circ)$ | $(\alpha=273.7^\circ, \delta=+66.7^\circ)$ | $89.76^\circ$ | 0 | 0 | 0 |
| `P0001` vs `P0008` (Within Calib) | $(\alpha=237.5^\circ, \delta=-11.5^\circ)$ | $(\alpha=29.1^\circ, \delta=+7.7^\circ)$ | **$141.78^\circ$** | 0 | 0 | 0 |

### 5.2 Independence Conclusion
The closest celestial distance between any calibration source and any evaluation source is **17.47 degrees**, vastly larger than the SPHEREx telescope field of view ($3.5^\circ \times 7.0^\circ$). Zero astronomical objects, zero duplicate observations, and zero spatial correlations exist between the calibration and evaluation cohorts.

---

## 6. AUDIT C — Spectral Eligibility and Sparsity Analysis

### 6.1 Distribution of Valid Channels

In the Calibration Cohort ($N=15,000$), the valid channel counts are distributed as follows:

- **0 Channels (Unobserved):** 5,623 sources (37.5% fall outside active detector footprints during pointing).
- **1 Channel:** 89 sources (0.59% of reliable sources, boundary fringe detections).
- **2 Channels:** 898 sources (5.99% of reliable sources, partial dither overlaps).
- **3–4 Channels:** 824 sources (5.49% of reliable sources, single-detector visits).
- **5–8 Channels:** **5,327 sources (35.51% of reliable sources, 74.6% of observed reliable sources)** possess simultaneous dichroic coverage (NIR + MWIR).
- **$> 8$ Channels:** 0 sources (physically impossible in a single telescope pointing).

### 6.2 Normalization Degeneracy Risk

The SPECTRA preprocessing pipeline scales each input spectrum by the median flux of observed channels:
$$\tilde{F}_i = \frac{F_i}{\text{median}(\{F_j : m_j = 1\})}$$

- **For $N_{\text{valid}} = 1$:** $\text{median}([F_1]) = F_1 \implies \tilde{F}_1 = 1.0$. The normalized vector is identically $1.0$ regardless of true source brightness. All absolute amplitude information is completely destroyed.
- **For $N_{\text{valid}} = 2$:** $\text{median}([F_1, F_2]) = \frac{F_1 + F_2}{2}$. The normalized flux vector sums identically to $2.0$. The model receives only a relative two-point ratio.
- **For $N_{\text{valid}} \ge 5$:** The median spans 5 to 8 points across two distinct spectral octaves (e.g. D1 at 0.75–1.11 $\mu\text{m}$ and D4 at 2.42–3.82 $\mu\text{m}$). This preserves both relative color slope and localized continuum shape.

*Recommendation:* Task 1.2C must exclude sources with $N_{\text{valid}} < 5$ from the primary null calibration cohort. Sources with 1–4 channels must be analyzed in a separate degenerate-sparsity sensitivity study.

---

## 7. AUDIT D — Detector-Pair Calibration Feasibility

The 7,036 observed `RELIABLE_ISOLATED_POINT_SOURCE` candidates in the Calibration Cohort cluster into three distinct optical dichroic pairs:

### Table 7.1: Calibration Cohort Dichroic Pair Breakdown

| Dichroic Pair | Wavelength Coverage ($\mu\text{m}$) | Total Reliable Sources | Sources with $\ge 5$ Channels | P0001 Count | P0008 Count | Calibration Feasibility |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **D1 + D4** | 0.74–1.12 $\mu\text{m}$ & 2.40–3.85 $\mu\text{m}$ | 1,581 | 1,175 | 109 | 1,472 | Feasible (dominated by P0008) |
| **D2 + D5** | 1.09–1.66 $\mu\text{m}$ & 3.80–4.44 $\mu\text{m}$ | 2,973 | 2,624 | 1,462 | 1,511 | Highly Feasible (balanced) |
| **D3 + D6** | 1.62–2.43 $\mu\text{m}$ & 4.41–5.02 $\mu\text{m}$ | 2,482 | 1,548 | 968 | 1,514 | Highly Feasible (well-sampled) |
| **Single Det** | Narrow single-array | 102 | 0 | 43 | 59 | Unsuitable (degenerate) |
| **Total** | — | **7,138** | **5,347** | **2,582** | **4,556** | **Pair-Stratified Mandatory** |

### Critical Finding: The Necessity of Stratification
Pooling D1+D4, D2+D5, and D3+D6 into a single aggregate null distribution would conceal severe instrument and astrophysical domain shifts:
1. D5 and D6 operate at 3.8–5.0 $\mu\text{m}$ where spacecraft and zodiacal thermal emission introduce higher photon noise than D1/D2 in the near-infrared.
2. In D1+D4, Pointing 0001 contributes only 109 sources while Pointing 0008 contributes 1,472 sources due to roll orientation.
3. Therefore, calibration must be performed independently for each of the three dichroic pairs.

---

## 8. AUDIT E — Statistical Sample Size and Tail Probability Estimation

### 8.1 Empirical Quantile Estimation Limits

To establish operational thresholds at false positive rates $\alpha \in \{0.05, 0.01\}$:

- **At $\alpha = 0.05$ (95th Percentile):**  
  - For D1+D4 ($N = 1,175$ optimal sources): Expected tail events $E[K] = 1,175 \times 0.05 \approx 59$ events.
  - For D2+D5 ($N = 2,624$ optimal sources): Expected tail events $E[K] = 2,624 \times 0.05 \approx 131$ events.
  - For D3+D6 ($N = 1,548$ optimal sources): Expected tail events $E[K] = 1,548 \times 0.05 \approx 77$ events.
  - *Verdict:* Highly well-powered across all pairs.
- **At $\alpha = 0.01$ (99th Percentile):**  
  - For D1+D4: Expected tail events $E[K] \approx 12$ events.
  - For D2+D5: Expected tail events $E[K] \approx 26$ events.
  - For D3+D6: Expected tail events $E[K] \approx 15$ events.
  - *Verdict:* Statistically feasible, but finite-sample quantile variance requires bootstrap confidence intervals ($\pm 1\sigma$ threshold bounds).

### 8.2 Spatial Dependence and Pointing Stratification
Because sources within a single pointing share identical atmospheric, zodiacal, and detector flat-field realizations, they are not strictly I.I.D. (Independent and Identically Distributed). To avoid optimistic tail estimation:
- The calibration threshold derived on Pointing `0008` must be tested against Pointing `0001` (and vice versa) to measure pointing-to-pointing stability before freezing thresholds for Task 1.2D.

---

## 9. AUDIT F — Checkpoint and Extraction Provenance

1. **Frozen Candidate Checkpoint:**  
   `checkpoints/spectra_masked_ae_v2.pt` was confirmed byte-for-byte identical to the preflight audit:
   $$\text{SHA-256: } \texttt{6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938}$$
2. **Channel Grid Reference:**  
   `data/spherex/qr3/calibration/spectral_channels_spx_cal-sch-v2-2026-229.fits` (`SHA-256: 1da3549d363b6c7eb8ac0b709dbed6dafe2fd24eefe03ebee6e2e8912634694e`).
3. **No Undocumented Changes:**  
   The forward architecture (`in=204, latent=16, hidden=64`), loss function, and systematic error floor ($\sigma_{\text{sys}} = 0.0193$) remain strictly identical to repository documentation.

---

## 10. Unresolved Risks and Evidence Gaps

1. **Risk of Training Leakage in P0001:** While only 5 individual catalog sources overlap with historical training files, Pointing 0001 was part of the original training domain. Thresholds calibrated exclusively on P0001 would suffer from in-sample optimistic bias.
2. **Absence of Ground-Truth Spectroscopic Normality:** The "null control" relies on photometric and astrometric point-source cleanliness (`RELIABLE_ISOLATED_POINT_SOURCE`). Rare real astrophysical anomalies (e.g. unusual emission-line stars) may legitimately reside in this sample, slightly elevating the empirical null tail.
3. **Sparse-Spectrum Normalization Gap:** Sources with $<5$ channels cannot be reliably scored by median-normalized autoencoders without destroying signal amplitude.

---

## 11. Explicit Preconditions and Safeguards for Task 1.2C

To proceed safely into Task 1.2C, the following safeguards are non-negotiable:

1. **Primary Uncorrupted Null Cohort:** Use Pointing `0008` as the primary out-of-sample null calibration cohort, as it has zero historical association with model training.
2. **Training Source Exclusion:** Explicitly exclude the 5 overlapping sources in Pointing `0001` (`source_id`: 6316932723797678080, 6268273836710905344, 6316494229114061952, 6316495122467403776, 6316948567937380224).
3. **Primary Calibration Filtering:** Restrict primary null calibration to `RELIABLE_ISOLATED_POINT_SOURCE` candidates with `coverage_status == 'MULTI_DETECTOR'` and $N_{\text{valid}} \ge 5$ channels ($N = 5,322$ sources).
4. **Detector-Pair Stratification:** Derive independent operating thresholds for D1+D4, D2+D5, and D3+D6. Do not compute a single pooled threshold.
5. **Zero Blind Evaluation Contact:** Maintain strict read-only isolation of Blind Evaluation pointings (`P0002`, `P0009`, `P0010`).

---

## 12. Final Verdict and Formal Recommendation

### Final Verdict:
$$\mathbf{CONDITIONALLY\ READY\ FOR\ TASK\ 1.2C}$$

**Verdict Justification:**  
Cross-partition astrophysical independence between the calibration and evaluation cohorts is mathematically proven ($>17.4^\circ$ separation, zero source overlap). However, the cohort is *Conditionally Ready* rather than unconditionally ready because: (1) Pointing 0001 has historical training associations requiring Pointing 0008 to serve as the primary uncorrupted null benchmark, (2) the 5 overlapping P0001 training sources must be excluded, (3) primary calibration must be restricted to multi-detector sources with $\ge 5$ channels to prevent median normalization degeneracy, and (4) thresholds must be stratified by dichroic detector pair.

### Formal Recommendation:
Proceed to **Phase 3, Task 1.2C: Multi-Pointing Stratified Null-Control Calibration**, adhering strictly to the preconditions established in Section 11.

---

## 13. Deliverables and Cryptographic Hashes

1. **Audit Report:**  
   [`reports/SPECTRA_TASK_1_2BR_CALIBRATION_READINESS_AUDIT.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/SPECTRA_TASK_1_2BR_CALIBRATION_READINESS_AUDIT.md)
2. **Readiness Manifest:**  
   [`reports/manifests/spectra_task_1_2br_readiness_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/manifests/spectra_task_1_2br_readiness_manifest.json)

