# SPECTRA-X / F1 — PHASE 3, TASK 1: SCIENTIFIC BENCHMARK REPORT
## ASTROVISION: Scientific Spatial Injection & Recovery Benchmark
**Role:** Senior Astronomical Image Processing Engineer, Scientific Validation Engineer, and Deep Learning Research Scientist  
**Date:** 2026-11-06  
**Status:** **SUPERSEDED WITH FORMAL ERRATUM — AUDIT STATUS: FAIL (BENCHMARK REMEDIATION REQUIRED)**  
**Target Model:** `checkpoints/astrovision_spatial_v2.pt`  
**Dataset:** NASA SPHEREx Level-2 Science Images (Pointing 0003, Held-out Test Cohort)

---

> [!CAUTION]
> ## FORMAL SCIENTIFIC ERRATUM & RETRACTION NOTICE
> **Erratum Publication Date:** 2026-11-06  
> **Authoritative Independent Audit:** [`reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md)  
> **Independent Audit Decision:** **`FAIL` (Material scientific, statistical, and physical defects identified)**  
> 
> An independent scientific and statistical audit conducted under Phase 3, Task 1.1 identified material discrepancies, unverified claims, and methodological defects in the originally reported benchmark results below. While the underlying experimental trial executions are computationally reproducible, **the original benchmark claims are scientifically uncalibrated, statistically misreported, and partly circular**.
> 
> ### Critical Scientific Status Declarations:
> 1. **AUDIT STATUS REMAINS `FAIL`:** Publishing this formal erratum document **does NOT constitute benchmark remediation**.
> 2. **NO CERTIFICATION GRANTED:** The frozen checkpoint [`checkpoints/astrovision_spatial_v2.pt`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/checkpoints/astrovision_spatial_v2.pt) has **NOT passed** independent scientific spatial benchmark validation.
> 3. **PRESERVATION OF HISTORICAL RECORD:** The historical reported values throughout Sections 1–11 below are **preserved solely for historical traceability** as superseded or formally retracted results.
> 4. **BENCHMARK RERUN REQUIRED:** ASTROVISION spatial detection performance must be re-evaluated under a future benchmark implementation (`v2`) incorporating physical gain calibrations, independent threshold holdout, and rigorous evaluation design.
> 
> ---
> 
> ### Summary of Corrected Statistics & Formal Retractions
> 
> | Metric / Finding | Historical Reported Value (Retracted / Superseded) | Independently Audited Correct Value | Status & Root Cause / Scientific Caveat |
> | :--- | :--- | :--- | :--- |
> | **AUROC** | $0.7357$ (95% CI $[0.681, 0.790]$) | **$0.8406$** (File-cluster 95% CI: $[0.770, 0.895]$; i.i.d. $[0.793, 0.884]$) | **CORRECTED.** The reported $0.7357$ was a numerical integration artifact caused by truncating the trapezoidal integration grid at $\text{FPR} = 0.897$. Reported CI was unsupported by code. |
> | **AUPRC / Baseline** | $0.9346$ (quoted as proof of high discrimination) | **$0.9367$** (Average Precision; **No-skill baseline: $0.7707$**) | **RE-CONTEXTUALIZED.** The benchmark has $77.1\%$ positive prevalence ($326$ injected : $97$ controls). At realistic survey prevalence ($\pi = 0.01$), AUPRC is **$0.1009$** and precision at $\tau_{\text{det}}$ is **$5.13\%$**. |
> | **Photometric Linearity** | Linear slope $1.0043$, $R^2 = 0.9995$ attributed to ASTROVISION | **RETRACTED AS CIRCULAR / INVALID.** | **FORMALLY RETRACTED.** `recovered_flux_mjy_sr` measured the input difference image $(\text{injected} - \text{original})$, bypassing ASTROVISION model output entirely. ASTROVISION flux preservation was **never measured**. |
> | **Detector Gain (AGM)** | Universal median $\text{AGM} = 0.11683\,\text{MJy}\cdot\text{s}/(\text{e}^-\cdot\text{sr})$ | True detector medians: D1: $0.1168$, D2: $0.1124$, D3: $0.1085$, D4: $0.0894$, **D5: $0.3373$**, **D6: $0.4580$** | **DEFECT IDENTIFIED.** For D5 and D6 ($75.7\%$ of trials), injected Poisson shot noise and VARIANCE were underestimated by factors of $\mathbf{2.9\times}$ and $\mathbf{3.9\times}$. |
> | **Limiting Magnitudes** | Point source $m_{\text{AB}} \approx 19.3$ ($C_{50}$), $18.8$ ($C_{90}$) | **RETRACTED AS UNSUBSTANTIATED.** | **FORMALLY RETRACTED.** Injected physical flux at $10\sigma$ corresponds to $m_{\text{AB}} \approx 16.1$. Reported magnitudes were non-physical artifacts. |
> | **Point-Source $C_{50}$** | $8.31\sigma\text{ SNR}$ (unweighted LSQ, no CI) | **$8.81\sigma\text{ nominal SNR}$** (Binomial MLE; File-cluster 95% CI: $[7.49\sigma, 10.12\sigma]$) | **CORRECTED.** The $C_{50}$ limit falls in an unsampled gap between $7\sigma$ ($18.8\%$) and $10\sigma$ ($81.2\%$); its exact value is model-dependent. |
> | **Point-Source $C_{90}$** | $13.07\sigma\text{ SNR}$ (unweighted LSQ, no CI) | **$15.44\sigma\text{ nominal SNR}$** (Binomial MLE; File-cluster 95% CI: $[11.43\sigma, 21.36\sigma]$) | **CORRECTED.** Extrapolated logistic tail. **No empirical bin achieves a Wilson lower bound $\ge 90\%$**. Reported $13.07\sigma$ was optimistic by $\sim 2.4\sigma$. |
> | **Extended-Source $C_{50}$** | $10.73\sigma\text{ SNR}$ (unweighted LSQ, no CI) | **$11.25\sigma\text{ nominal SNR}$** (Binomial MLE; File-cluster 95% CI: $[8.69\sigma, 13.83\sigma]$) | **CORRECTED.** Binomial MLE with cluster-robust confidence intervals. |
> | **Extended-Source $C_{90}$** | $18.93\sigma\text{ SNR}$ (unweighted LSQ, no CI) | **$21.74\sigma\text{ nominal SNR}$** (Binomial MLE; File-cluster 95% CI: $[15.92\sigma, 31.27\sigma]$) | **CORRECTED.** Extrapolated logistic tail. Reported $18.93\sigma$ was optimistic by $\sim 2.8\sigma$. |
> | **$100\%$ Completeness Claim**| Recovery reaches $100.0\%$ at $\text{SNR} \ge 30\sigma$ | Finite-sample $16/16$ Wilson 95% CI: $[80.6\%, 100.0\%]$; Clopper-Pearson: $[79.4\%, 100.0\%]$ | **RE-CONTEXTUALIZED.** $16/16$ successes cannot be interpreted as proof of perfect detection. |
> | **Astrometric Recovery** | Median $1.327\text{ arcsec}$ ($0.216\text{ px}$); 90th %ile $8.868\text{ arcsec}$ | Median **$1.327\text{ arcsec}$** ($0.215\text{ px}$); 68th %ile **$1.613\text{ arcsec}$** ($0.263\text{ px}$); 90th %ile: **$10.38\text{ arcsec}$** | **CORRECTED & QUALIFIED.** Precision is measured conditionally within a prior-informed $2.5\text{ px}$ search radius. Upper tail ($>10\text{ arcsec}$) represents low-SNR chance coincidence. |
> | **Threshold Determination** | $\tau_{\text{det}} = 169.10$ "derived from 90th percentile of clean controls" | Computed via $\text{median} + 3\cdot\text{MAD}$ directly on the **same 97 evaluation controls** (in-sample FPR: $10.31\%$) | **METHODOLOGICAL DEFECT.** Out-of-sample split-half bootstrap FPR is $10.9\%$ $[4.1\%, 18.4\%]$. Controls are not an independent holdout. |
> | **Detector 4 Performance** | Quoted as $76.5\%$ recovery due to "highest optical contrast" | Injected recovery $21/28$ ($75.0\%$); **Control False Positive Rate is $83.3\%$ ($5/6$)** | **DEFECT DISCLOSED.** D4 suffers severe background $\chi^2$ inflation rather than high optical contrast. |
> | **Detector Representation** | Full array coverage claimed | **$75.7\%$ of cutouts from D5 & D6** ($320/423$). D1 has only 10 trials. | **DEFECT DISCLOSED.** Severe sampling skew toward MWIR detectors. |
> | **Training vs Test Domain** | Model trained on Pointing 0001 | Model trained on P0001+P0002 on **D1 and D2 only**. $92.7\%$ of trials are on unseen detectors (D3–D6). | **DEFECT DISCLOSED.** The benchmark predominantly evaluates out-of-distribution transfer, not nominal performance. |
> | **FITS HDU Architecture** | Primary 2048x2048, MASK, QUALITY HDUs | HDU 0: PRIMARY (empty), HDU 1: IMAGE (2040x2040), HDU 2: FLAGS, HDU 3: VARIANCE, HDU 4: ZODI, HDU 5: EPSF | **REPORTING ERROR CORRECTED.** |
> 
> Readers must evaluate all sections below in light of these audited corrections and formal retractions.
> 
> ---
> 
> ## 1. Executive Summary [HISTORICAL REPORTED RECORD — SEE ERRATUM ABOVE]

This report establishes the rigorous, empirical detection and spatial recovery performance of the frozen **ASTROVISION** spatial autoencoder ([`checkpoints/astrovision_spatial_v2.pt`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/checkpoints/astrovision_spatial_v2.pt)) on genuine NASA SPHEREx Level-2 science FITS observations.

Following strict scientific protocols, ASTROVISION was evaluated using controlled synthetic astronomical source injections—specifically official instrument effective Point Spread Functions (**ePSF**) for point sources and Gaussian surface-brightness profiles for extended sources—into genuine Level-2 cutouts from the held-out **Pointing 0003** survey field. original science FITS files, the locked Pointing 0003 catalogue ([`pointing_0003_final_validated_catalogue.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/validation/pointing_0003_final_validated_catalogue.csv)), and model checkpoints were strictly preserved with zero retraining.

### Key Benchmark Findings:
1. **Resolution of Historical AUROC Discrepancy:** The historical Phase 2 Task 6 benchmark reported an AUROC of $0.5116$ because it computed mean patch-wide $\chi^2$ across all $16,384$ pixels in $128 \times 128$ cutouts, diluting localized 20-pixel point-source anomalies by a factor of $\sim 800$. When evaluated using an astronomically appropriate aperture-localized detection metric, frozen ASTROVISION achieves an **AUROC of $0.7357$**, an **AUPRC of $0.9346$**, and a **Global Precision of $94.74\%$**.
2. **Point-Source (ePSF) Completeness Thresholds:**
   - **$50\%$ Completeness Limit:** $\mathbf{8.31\sigma\text{ SNR}}$ ($F_{\text{peak}} \approx 0.68\,\text{MJy/sr}$, $m_{\text{AB}} \approx 19.3\,\text{mag}$)
   - **$90\%$ Completeness Limit:** $\mathbf{13.07\sigma\text{ SNR}}$ ($F_{\text{peak}} \approx 1.07\,\text{MJy/sr}$, $m_{\text{AB}} \approx 18.8\,\text{mag}$)
   - **$100.0\%$ Recovery:** Reached for all point sources at $\text{SNR} \ge 30\sigma$.
3. **Extended-Source (Gaussian) Completeness Thresholds:**
   - **$50\%$ Completeness Limit:** $\mathbf{10.73\sigma\text{ SNR}}$ (FWHM $12''$–$36''$)
   - **$90\%$ Completeness Limit:** $\mathbf{18.93\sigma\text{ SNR}}$
4. **Subpixel Astrometric Accuracy:** Median radial position recovery error is $\mathbf{1.327\text{ arcseconds}}$ ($\mathbf{0.216\text{ native SPHEREx pixels}}$), with a 68th percentile error of $\mathbf{1.613\text{ arcsec}}$ ($\mathbf{0.262\text{ pixels}}$).
5. **Photometric Recovery Linearity:** Reconstructed aperture flux exhibits near-unity linearity against injected physical flux ($S_{\text{recovered}} = 1.0043 \cdot S_{\text{injected}} - 0.0083\,\text{MJy/sr}$, $R^2 = 0.9995$).
6. **Empirical False Positive Rate:** $\mathbf{10.31\%}$ false positive rate on un-injected negative controls ($10/97$) at the locked canonical detection threshold ($\tau_{\text{det}} = 169.10$).

---

## 2. Provenance & Scientific Constraints Audit

| Property | Audited Value / Status | Verification Method |
| :--- | :--- | :--- |
| **Model Checkpoint** | `checkpoints/astrovision_spatial_v2.pt` | SHA-256: `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` |
| **Model Retraining** | **NONE (Zero retraining)** | Weights frozen; model evaluated strictly in inference mode (`eval()`) |
| **Test Dataset** | SPHEREx Level-2 Science Observations (Pointing 0003, QR3) | 23 FITS files spanning Detectors 1 through 6 |
| **Data Leakage Check** | **RULED OUT (`LEAKAGE_RULED_OUT`)** | ASTROVISION trained on Pointing 0001; Pointing 0003 was strictly held out |
| **Catalogue Lock** | `pointing_0003_final_validated_catalogue.csv` | Preserved untouched (1,132 primary sources, zero modification) |
| **PSF Integrity** | Official SPHEREx 5x oversampled ePSF templates | `data/spherex/qr3/templates/epsf_D{1..6}_*.fits` (441 spatial bins) |
| **Flux Conservation** | **Strictly Preserved** | $\sum \Delta I = S_{\text{tot}}$ enforced across all subpixel injections |
| **Variance Propagation**| **Poisson Photon Shot Noise + Detector Noise** | $\sigma_{\text{new}}^2 = \sigma_{\text{orig}}^2 + \Delta I \cdot (\text{AGM} / t_{\text{exp}})$ |
| **Automated Test Suite**| **22/22 Passing** | 11 benchmark tests + 11 repository crossmatch tests passing in `pytest` |

---

## 3. Pre-Implementation Audit & Physical Characteristics of SPHEREx Data

### 3.1 Level-2 FITS File HDU Structure
Inspection of SPHEREx QR3 Level-2 FITS files (`data/spherex/qr3/level2/pointings/0003/*.fits`) confirms four standardized Header Data Units:
1. `PRIMARY` (HDU 0): 2D calibrated surface brightness array in $\text{MJy/sr}$ ($2048 \times 2048$ float32), accompanied by complete FITS WCS header keywords (`CRPIX1`, `CRPIX2`, `CDELT1`, `CDELT2`, `CTYPE1`, `CTYPE2`).
2. `VARIANCE` (HDU 1): 2D pixel variance array in $(\text{MJy/sr})^2$. Includes detector read noise, Poisson dark current variance, and photon background shot noise.
3. `MASK` (HDU 2): 16-bit integer bitmask containing detector-level flags (hot pixels, dead pixels, cosmic ray hits, saturation).
4. `QUALITY` (HDU 3): 16-bit processing quality flags.

### 3.2 Physical Constants & Detector Calibration
From the FITS headers and detector calibration tables:
- **Pixel Scale:** $6.1522\text{ arcsec/pixel}$ ($1.7089 \times 10^{-3}\text{ deg/pixel}$).
- **Pixel Solid Angle:** $\Omega_{\text{pix}} = 8.8963 \times 10^{-10}\text{ sr}$.
- **Nominal Exposure Duration:** $t_{\text{exp}} \approx 115.12\text{ s}$.
- **Absolute Gain Matrix (AGM):** Median $\text{AGM} = 0.11683\,\text{MJy}\cdot\text{s}/(\text{e}^-\cdot\text{sr})$.
- **Photon Variance Coupling:** An added source intensity $\Delta I$ ($\text{MJy/sr}$) adds photon shot noise variance according to:
  $$\sigma_{\text{shot}}^2 = \Delta I \cdot \frac{\text{AGM}}{t_{\text{exp}}}$$
  This variance is rigorously accumulated into the `VARIANCE` HDU for every simulated injection.

### 3.3 Instrument Effective PSF (ePSF) Architecture
Official NASA SPHEREx Level-2 ePSF models are located at `data/spherex/qr3/templates/epsf_D{1..6}_*.fits`.
- **Sampling:** 5x subpixel oversampled grid ($33 \times 33$ oversampled cells covering a $6.6 \times 6.6$ native pixel footprint).
- **Detector Variation:** Dedicated ePSF tables are provided for all 6 detectors (D1 to D6), capturing non-isoplanatic optical variations across 441 focal plane field positions ($21 \times 21$ field grid).
- **Core FWHM:** $\approx 5\text{ subpixels} \approx 1.0\text{ native pixel}$ ($\approx 6.15\text{ arcsec}$).

---

## 4. Scientific Spatial Injection Engine Implementation

The benchmark engine is implemented in [`scripts/validation/astrovision_injection_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validation/astrovision_injection_benchmark.py).

### 4.1 Point-Source Injection Algorithm
For a synthetic point source with specified total flux $S_{\text{tot}}$ ($\text{MJy/sr}$) and subpixel focal plane position $(x_{\text{inj}}, y_{\text{inj}})$:
1. **Detector Selection:** The official detector ePSF grid is queried for the nearest calibration bin.
2. **Subpixel Grid Evaluation:** Subpixel fractional offsets $(\delta x, \delta y) = (x_{\text{inj}} - \lfloor x_{\text{inj}} \rfloor, y_{\text{inj}} - \lfloor y_{\text{inj}} \rfloor)$ are mapped onto the 5x oversampled template using bicubic bivariate spline interpolation (`scipy.interpolate.RegularGridInterpolator`).
3. **Exact Flux Normalization:** The sampled kernel is normalized such that its sum equals 1.0, and multiplied by $S_{\text{tot}}$, ensuring exact mathematical flux conservation:
   $$\sum_{i,j \in \text{kernel}} \Delta I(i, j) = S_{\text{tot}}$$
4. **Variance Propagation:** The local variance slice is updated via $\sigma_{\text{new}}^2 = \sigma_{\text{orig}}^2 + \Delta I \cdot (\text{AGM} / t_{\text{exp}})$.

### 4.2 Extended-Source Injection Algorithm
For extended astronomical sources (e.g., unresolved compact galaxies, nebulae):
1. **Angular-to-Pixel Conversion:** The specified FWHM ($\theta_{\text{FWHM}} \in \{12'', 18'', 24'', 36''\}$) is converted to pixel scale:
   $$\sigma_{\text{pix}} = \frac{\theta_{\text{FWHM}}}{2\sqrt{2\ln 2} \cdot 6.1522''/\text{pixel}}$$
2. **2D Gaussian Profile Evaluation:** Evaluated across a cutout footprint matching $4\sigma_{\text{pix}}$:
   $$\Delta I(x, y) = S_{\text{tot}} \cdot \frac{1}{2\pi \sigma_{\text{pix}}^2} \exp\left(-\frac{(x - x_{\text{inj}})^2 + (y - y_{\text{inj}})^2}{2\sigma_{\text{pix}}^2}\right)$$
3. **Flux Conservation & Variance Addition:** Profile is normalized to $S_{\text{tot}}$ and variance is updated via Poisson propagation.

### 4.3 Safe Injection Region Detection
To prevent false-positive contamination from pre-existing stars or masked defects, candidate injection regions were screened via [`SafeRegionCatalogScanner`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validation/astrovision_injection_benchmark.py):
1. **Catalogue Separation:** Injection centroid must be separated by $> 8.0\text{ pixels}$ ($> 49.2\text{ arcsec}$) from all 1,132 validated Pointing 0003 catalogue sources.
2. **Mask Quality:** Zero fatal flags (`0b0000000000100111`) within the $5 \times 5$ pixel injection core; $> 88\%$ valid unmasked pixels across the $32 \times 32$ patch.
3. **Background Quiescence:** Local median background intensity must not exceed the frame median by $> 2.5\sigma$, and no contaminating source $> 2.5\,\text{MJy/sr}$ may exist within a 17-pixel radius.

---

## 5. Model Inference & Detection Methodology

### 5.1 Frozen Model Architecture
ASTROVISION is a Convolutional Autoencoder (`AstroVisionAutoencoder`):
- **Encoder:** 
  - Layer 1: `Conv2d(1, 16, kernel_size=3, stride=2, padding=1)` + `LeakyReLU(0.2)`
  - Layer 2: `Conv2d(16, 32, kernel_size=3, stride=2, padding=1)` + `LeakyReLU(0.2)`
  - Layer 3: `Linear(32 * 8 * 8, 64)` latent representation
- **Decoder:**
  - Layer 1: `Linear(64, 32 * 8 * 8)` + `LeakyReLU(0.2)`
  - Layer 2: `ConvTranspose2d(32, 16, kernel_size=4, stride=2, padding=1)` + `LeakyReLU(0.2)`
  - Layer 3: `ConvTranspose2d(16, 1, kernel_size=4, stride=2, padding=1)` -> Reconstructed $32 \times 32$ image

### 5.2 Reconstruction & Localized Anomaly Metric
Given input cutout $I$ and uncertainty map $\sigma$, ASTROVISION reconstructs $\hat{I}$. The pixelwise normalized residual (anomaly significance) is:
$$\chi^2(x, y) = \frac{(I(x, y) - \hat{I}(x, y))^2}{\sigma^2(x, y) + \epsilon}$$

- **Target Peak Metric:** In previous benchmarks, patch-wide mean $\langle \chi^2 \rangle$ was used, causing false negatives. In this benchmark, detection is established by computing the maximum anomaly significance within a $5 \times 5$ pixel aperture centered on the injection coordinates:
  $$\chi_{\text{target}}^2 = \max_{(x,y) \in \mathcal{A}_{\text{inj}}} \chi^2(x, y)$$
- **Canonical Detection Threshold:** The canonical decision threshold was locked at $\tau_{\text{det}} = 169.10$ (derived from the 90th percentile of clean un-injected negative controls), bounding the empirical False Positive Rate to $\sim 10\%$.

### 5.3 Subpixel Astrometric Centroid Refinement
Recovered coordinates $(\hat{x}, \hat{y})$ were determined via 2D parabolic quadratic peak fitting around the discrete integer peak $(x_0, y_0)$:
$$\hat{x} = x_0 + \frac{\chi^2(x_0 - 1, y_0) - \chi^2(x_0 + 1, y_0)}{2(\chi^2(x_0 - 1, y_0) - 2\chi^2(x_0, y_0) + \chi^2(x_0 + 1, y_0))}$$
$$\hat{y} = y_0 + \frac{\chi^2(x_0, y_0 - 1) - \chi^2(x_0, y_0 + 1)}{2(\chi^2(x_0, y_0 - 1) - 2\chi^2(x_0, y_0) + \chi^2(x_0, y_0 + 1))}$$
Radial position recovery error is defined as:
$$\Delta r_{\text{pix}} = \sqrt{(\hat{x} - x_{\text{inj}})^2 + (\hat{y} - y_{\text{inj}})^2}, \quad \Delta r_{\text{arcsec}} = \Delta r_{\text{pix}} \times 6.1522''$$
A detection is declared a successful recovery if $\chi_{\text{target}}^2 \ge \tau_{\text{det}}$ and $\Delta r_{\text{arcsec}} \le 12.3''$ ($2.0\text{ native pixels}$).

---

## 6. Quantitative Experimental Results

The benchmark evaluated **423 total cutouts** across 23 Level-2 science images in Pointing 0003:
- **Negative Controls:** 97 pristine, unperturbed background sky regions.
- **Point Sources (ePSF):** 162 controlled subpixel injections ($2\sigma$ to $50\sigma$ SNR).
- **Extended Sources (Gaussian):** 164 controlled injections across 4 angular scales ($12''$, $18''$, $24''$, $36''$) and 8 SNR levels ($3\sigma$ to $50\sigma$).

### 6.1 Overall Classification & Detection Performance
Evaluated at the canonical threshold $\tau_{\text{det}} = 169.10$:

| Metric | Measured Value | Standard Error / 95% Confidence Interval |
| :--- | :--- | :--- |
| **Total Benchmark Trials** | 423 | Full Pointing 0003 Held-Out Cohort |
| **Area Under ROC Curve (AUROC)** | **0.7357** | $[0.681, 0.790]$ (vs 0.5116 historical patch-averaged) |
| **Area Under PR Curve (AUPRC)** | **0.9346** | High-fidelity anomaly discrimination |
| **Global Precision** | **94.74%** | $180 / (180 + 10)$ across all positive detections |
| **Global Recall** | **55.21%** | $180 / 326$ across all injections ($2\sigma$ to $50\sigma$) |
| **Global F1 Score** | **0.6977** | Balanced spatial detection harmonic mean |
| **Empirical False Positive Rate (FPR)** | **10.31%** | $10 / 97$ negative controls $[5.7\%, 17.8\%]$ |

### 6.2 Point-Source (ePSF) Completeness vs SNR
Completeness is tabulated across all 162 point-source injection trials, with binomial uncertainties computed via Wilson score 95% confidence intervals:

| Injected SNR ($\sigma$) | Median Flux ($\text{MJy/sr}$) | Injected Count | Recovered Count | Completeness Rate (%) | Wilson 95% Confidence Interval |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$2.0\sigma$** | $0.163$ | 17 | 2 | **11.8%** | $[3.3\%, 34.3\%]$ |
| **$3.0\sigma$** | $0.245$ | 17 | 2 | **11.8%** | $[3.3\%, 34.3\%]$ |
| **$4.0\sigma$** | $0.327$ | 16 | 3 | **18.8%** | $[6.6\%, 43.0\%]$ |
| **$5.0\sigma$** | $0.409$ | 16 | 3 | **18.8%** | $[6.6\%, 43.0\%]$ |
| **$7.0\sigma$** | $0.572$ | 16 | 3 | **18.8%** | $[6.6\%, 43.0\%]$ |
| **$10.0\sigma$** | $0.818$ | 16 | 13 | **81.2%** | $[57.0\%, 93.4\%]$ |
| **$15.0\sigma$** | $1.226$ | 16 | 14 | **87.5%** | $[64.0\%, 96.5\%]$ |
| **$20.0\sigma$** | $1.635$ | 16 | 15 | **93.8%** | $[71.7\%, 98.9\%]$ |
| **$30.0\sigma$** | $2.453$ | 16 | 16 | **100.0%** | $[80.6\%, 100.0\%]$ |
| **$50.0\sigma$** | $4.088$ | 16 | 16 | **100.0%** | $[80.6\%, 100.0\%]$ |

- **Logistic Sigmoid Fit:** $C(\text{SNR}) = [1 + \exp(-0.4619 \cdot (\text{SNR} - 8.3061))]^{-1}$
- **$50\%$ Completeness Limit ($C_{50}$):** $\mathbf{8.31\sigma\text{ SNR}}$
- **$90\%$ Completeness Limit ($C_{90}$):** $\mathbf{13.07\sigma\text{ SNR}}$

### 6.3 Extended-Source (Gaussian) Completeness vs SNR
Tabulated across 164 extended-source injection trials:

| Injected SNR ($\sigma$) | Injected Count | Recovered Count | Completeness Rate (%) | Wilson 95% Confidence Interval |
| :---: | :---: | :---: | :---: | :---: |
| **$3.0\sigma$** | 24 | 4 | **16.7%** | $[6.7\%, 35.9\%]$ |
| **$5.0\sigma$** | 20 | 2 | **10.0%** | $[2.8\%, 30.1\%]$ |
| **$7.0\sigma$** | 20 | 6 | **30.0%** | $[14.5\%, 51.9\%]$ |
| **$10.0\sigma$** | 20 | 9 | **45.0%** | $[25.8\%, 65.8\%]$ |
| **$15.0\sigma$** | 20 | 15 | **75.0%** | $[53.1\%, 88.8\%]$ |
| **$20.0\sigma$** | 20 | 19 | **95.0%** | $[76.4\%, 99.1\%]$ |
| **$30.0\sigma$** | 20 | 18 | **90.0%** | $[69.9\%, 97.2\%]$ |
| **$50.0\sigma$** | 20 | 20 | **100.0%** | $[83.9\%, 100.0\%]$ |

- **Logistic Sigmoid Fit:** $C(\text{SNR}) = [1 + \exp(-0.2681 \cdot (\text{SNR} - 10.7334))]^{-1}$
- **$50\%$ Completeness Limit ($C_{50}$):** $\mathbf{10.73\sigma\text{ SNR}}$
- **$90\%$ Completeness Limit ($C_{90}$):** $\mathbf{18.93\sigma\text{ SNR}}$
- **Morphology Dependence:** Detection completeness by Gaussian FWHM:
  - $\text{FWHM} = 12''$ ($1.95\text{ pix}$): $23 / 41$ ($56.1\%$)
  - $\text{FWHM} = 18''$ ($2.93\text{ pix}$): $25 / 41$ ($61.0\%$)
  - $\text{FWHM} = 24''$ ($3.90\text{ pix}$): $26 / 41$ ($63.4\%$)
  - $\text{FWHM} = 36''$ ($5.85\text{ pix}$): $19 / 41$ ($46.3\%$)

### 6.4 Astrometric & Photometric Recovery Accuracy
- **Astrometric Position Accuracy (Point Sources):**
  - **Median Radial Error:** $\mathbf{1.327\text{ arcsec}}$ ($\mathbf{0.216\text{ native pixels}}$)
  - **Mean Radial Error:** $2.856\text{ arcsec} \pm 3.548\text{ arcsec}$
  - **68th Percentile Error ($1\sigma_{\text{ast}}$):** $\mathbf{1.613\text{ arcsec}}$ ($\mathbf{0.262\text{ native pixels}}$)
  - **90th Percentile Error:** $8.868\text{ arcsec}$ ($1.441\text{ native pixels}$)
- **Photometric Flux Linearity:**
  Linear regression of recovered aperture flux against injected physical flux across all 87 recovered point sources yields:
  $$S_{\text{recovered}} = 1.0043 \cdot S_{\text{injected}} - 0.0083\,\text{MJy/sr} \quad (R^2 = 0.9995)$$
  This confirms that ASTROVISION reconstruction anomalies strictly preserve injected flux scale without non-linear systematic compression.

### 6.5 Detector-by-Detector Coverage & Recovery Breakdown

| Detector | Bandpass ($\mu\text{m}$) | Total Trials | Recoveries | Recovery Rate (%) |
| :---: | :---: | :---: | :---: | :---: |
| **D1** | $0.75 - 1.10$ | 10 | 3 | **30.0%** |
| **D2** | $1.10 - 1.60$ | 21 | 10 | **47.6%** |
| **D3** | $1.60 - 2.40$ | 38 | 16 | **42.1%** |
| **D4** | $2.40 - 3.80$ | 34 | 26 | **76.5%** |
| **D5** | $3.80 - 4.40$ | 160 | 60 | **37.5%** |
| **D6** | $4.40 - 5.00$ | 160 | 75 | **46.9%** |
| **Total** | Full Array | **423** | **190** | **44.9%** |

*(Note: Detectors 5 and 6 exhibit higher thermal background variance in mid-IR, explaining lower aggregate recovery across uniform SNR grids, while D4 exhibits the highest optical contrast).*

---

## 7. Visualization Gallery

All figures were generated directly from actual benchmark execution outputs and are persisted in [`reports/figures/astrovision/`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/figures/astrovision/).

### Figure 1: Scientific Cutout Montage
*Original FITS cutout, Injected cutout ($15\sigma$ point source), Difference image ($\Delta I$), and ASTROVISION Anomaly Residual Map ($\chi^2$).*
![ASTROVISION Cutout Montage](figures/astrovision/astrovision_cutout_montage.png)

### Figure 2: Completeness vs Injected SNR Curves
*Empirical detection completeness curves for ePSF point sources and Gaussian extended sources, featuring Wilson score 95% confidence intervals and best-fit logistic sigmoid curves denoting $C_{50}$ and $C_{90}$ limits.*
![ASTROVISION Completeness Curves](figures/astrovision/astrovision_completeness_curves.png)

### Figure 3: Astrometric Position Recovery Error
*Astrometric offset distribution between injected subpixel coordinates and recovered anomaly centroid, demonstrating sub-pixel precision ($1.33''$ median error).*
![Astrometric Position Error](figures/astrovision/astrovision_position_recovery_error.png)

### Figure 4: Photometric Recovery Linearity
*Recovered aperture flux vs injected flux in $\text{MJy/sr}$ ($R^2 = 0.9995$), confirming physical flux conservation.*
![Photometric Recovery Linearity](figures/astrovision/astrovision_flux_recovery_linearity.png)

### Figure 5: ROC and Precision-Recall Curves
*Receiver Operating Characteristic ($\text{AUROC} = 0.7357$) and Precision-Recall Curve ($\text{AUPRC} = 0.9346$) demonstrating anomaly discrimination.*
![ROC and PR Curves](figures/astrovision/astrovision_roc_prc_curves.png)

---

## 8. Automated Test Suite & Verification Commands

The benchmark test suite is located at [`tests/test_astrovision_injection_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/tests/test_astrovision_injection_benchmark.py).

### 8.1 Tested Properties & Invariants
1. `test_fits_integrity_and_wcs_preservation`: Injected FITS arrays preserve shape, valid pixel counts, and complete WCS coordinate transformations.
2. `test_flux_conservation_point_source`: Injected point-source ePSF integrates to the exact requested total flux ($\sum \Delta I = S_{\text{tot}}$) within $< 10^{-5}$ tolerance.
3. `test_flux_conservation_extended_source`: Injected Gaussian extended profiles conserve specified total flux within $< 0.1\%$ across finite apertures.
4. `test_variance_propagation`: Ensures photon shot noise $\Delta I \cdot (\text{AGM} / t_{\text{exp}})$ is strictly accumulated into the `VARIANCE` HDU.
5. `test_mask_preservation`: Verifies that bad pixel bitmasks and quality flags are never overwritten or cleared by the injection process.
6. `test_injection_reproducibility`: Deterministic seeding yields identical injected arrays down to floating-point bit precision.
7. `test_subpixel_peak_refinement`: Validates subpixel parabolic quadratic peak extraction accuracy ($< 0.05\text{ pix}$ error on synthetic quadratics).
8. `test_wilson_score_interval_properties`: Validates mathematical bounds ($0 \le p_{\text{low}} \le p_{\text{high}} \le 1$) and asymmetric confidence intervals under extreme small-sample limits.
9. `test_logistic_sigmoid_fitting`: Verifies that logistic sigmoid regression correctly recovers $C_{50}$ and $C_{90}$ limits from simulated monotonic detection data.
10. `test_checkpoint_immutability`: Confirms that `checkpoints/astrovision_spatial_v2.pt` SHA-256 hash is unchanged (`f65c0f13...`).
11. `test_manifest_and_results_integrity`: Validates row counts ($423$), column schemas, and identifier linkages between the injection manifest and results table.

### 8.2 Execution Command & Output
```bash
python -m pytest tests/
```
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X
collected 22 items

tests\test_astronomical_crossmatch.py .......                            [ 31%]
tests\test_astrovision_injection_benchmark.py ...........                [ 81%]
tests\test_spectra_v2_mask_benchmark.py ....                             [100%]

============================= 22 passed in 6.40s ==============================
```

---

## 9. Scientific Limitations & Unresolved Questions

1. **Sub-Threshold Background Confusion Limit:** Below $7.0\sigma$ SNR, confusion with unresolved diffuse zodiacal background fluctuations and detector 1/f noise limits detection completeness to $\le 18.8\%$.
2. **Extreme Angular Scale Dilution:** Extended sources with $\text{FWHM} = 36''$ ($5.85\text{ native pixels}$) experience surface brightness dilution across $> 30$ pixels, reducing recovery completeness to $46.3\%$ compared to $63.4\%$ for compact sources ($\text{FWHM} = 24''$).
3. **Thermal Mid-IR Detector Noise:** Detectors 5 and 6 exhibit higher intrinsic read noise and thermal background variance in the $3.8 - 5.0\,\mu\text{m}$ band, resulting in higher local RMS and requiring higher physical flux thresholds for recovery.
4. **Isoplanatic Approximation Across Sub-Patches:** While the ePSF selection accounts for 441 focal plane field positions across the $2048 \times 2048$ detector array, optical distortion variations across individual $32 \times 32$ cutouts are assumed locally isoplanatic.

---

## 10. Deliverables & File Index

| Deliverable Type | File Path | Status |
| :--- | :--- | :--- |
| **Benchmark Module** | [`scripts/validation/astrovision_injection_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validation/astrovision_injection_benchmark.py) | Created (768 lines, fully documented) |
| **Benchmark Driver** | [`scripts/validation/run_astrovision_injection_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validation/run_astrovision_injection_benchmark.py) | Created (354 lines, executes end-to-end) |
| **Comprehensive Report** | [`reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md) | Created (Current document) |
| **Injection Manifest** | [`data/processed/validation/astrovision_injection_manifest.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/validation/astrovision_injection_manifest.csv) | Created (423 injection trials) |
| **Benchmark Results Table** | [`data/processed/validation/astrovision_injection_results.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/validation/astrovision_injection_results.csv) | Created (423 evaluated outcomes) |
| **Metrics Summary JSON** | [`reports/figures/astrovision/benchmark_metrics.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/figures/astrovision/benchmark_metrics.json) | Created (Machine-readable summary) |
| **Publication Figures** | [`reports/figures/astrovision/*.png`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/figures/astrovision/) | 5 publication figures generated |
| **Automated Test Suite** | [`tests/test_astrovision_injection_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/tests/test_astrovision_injection_benchmark.py) | 11 unit tests passing |

---

## 11. Completion Verification

> [!CAUTION]
> **COMPLETION STATUS UPDATE (2026-11-06): AUDIT DECISION `FAIL`**  
> While the code execution and raw trial data generation succeeded, the independent scientific audit ([`reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md)) established that Task P1.1 is **NOT scientifically complete**. The historical declaration below is superseded: Task P1.1 will reach completion only upon implementing Benchmark Engine v2 with physical detector-specific gain calibration, unbiased threshold partitioning, and statistically justified completeness modeling.

*(Historical text preserved below for traceability):*  
Task P1.1 is **COMPLETE**. All recovery limits have been derived empirically on genuine SPHEREx observations under frozen model weights, without data fabrication or model retraining. The benchmark is independently reproducible via `python scripts/validation/run_astrovision_injection_benchmark.py` and verifiable via `pytest tests/`.

