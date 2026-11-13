# ASTROVISION Task 1.1T — Forensic Failure Analysis & Evidence-Based Remediation Design
## Comprehensive Technical Autopsy of Pilot Campaign Failure (Tasks 1.1R & 1.1S)

**Project:** SPECTRA-X / F1  
**Phase:** Phase 3 — Independent Verification & Remediation Architecture  
**Task:** 1.1T  
**Investigation Mode:** STRICT READ-ONLY FORENSIC INVESTIGATION  
**Auditor Roles:**
- Principal Astronomical ML Scientist
- Independent Scientific Validation Auditor
- Detector Characterization Specialist
- Statistical Benchmark Reviewer

**Investigation Verdict:** **`LIMITED REMEDIATION JUSTIFIED`**  
**ASTROVISION Scientific Certification Status:** **`FAIL — NOT CERTIFIED`**

---

## 1. Executive Summary

The independent scientific results audit of **Task 1.1S** passed with 100% cryptographic and numerical reproducibility, mathematically validating the raw findings of the restricted 2,500-trial pilot benchmark. However, ASTROVISION remains **`FAIL — NOT CERTIFIED`** due to unacceptable detection performance:
- **Point-Source Injections:** AUROC = **0.6861**, Overall Recovery Fraction at $\tau_d$ = **18.80% (94 / 500)**.
- **Extended-Source Injections:** AUROC = **0.5704**, Overall Recovery Fraction at $\tau_d$ = **15.20% (76 / 500)**.
- **Detector 4 Collapse:** Point AUROC = **0.4776** (worse than random chance), Extended AUROC = **0.3041**.
- **Calibration Transfer Failure:** Empirical evaluation False Positive Rate inflated to **8.60% (43 / 500)** (or **9.00%** un-gated) against the nominal $\alpha = 0.05$ target ($p = 6.39 \times 10^{-4}$).
- **Low-Background Domain Shift:** In Pointing `0010` (North Ecliptic Pole), Extended AUROC collapsed to **0.4599**, with null-control anomaly scores regularly exceeding true injection signals.

### Primary Forensic Breakthrough
This investigation identified the exact physical and algorithmic mechanisms responsible for these failures:
1. **Unmasked Input Convolutional Bleed (The Smoking Gun):**  
   In [`models/astrovision/model.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/astrovision/model.py), the `AstroVisionAutoencoder` passes raw image cutouts directly into standard PyTorch `nn.Conv2d` layers **without applying the defect mask at input**. Even though fatal pixels are zeroed in the final residual calculation, saturated stars ($>75,000\text{ MJy/sr}$) and fatal defects inside the $128 \times 128$ receptive field pollute the latent space. This contaminates clean central pixels, causing spurious reconstructions (e.g., predicting $6.57\text{ MJy/sr}$ on a clean $0.095\text{ MJy/sr}$ sky), generating extreme false anomaly peaks up to $\chi^2 = 410,561$.
2. **Absence of Background Normalization (DC Baseline Offset):**  
   The autoencoder was trained on raw, non-zero-centered surface brightness from Pointings `0001` and `0002` (where D1 background was $\sim 0.28\text{ MJy/sr}$). In low-background regimes like Pointing `0010` (where background drops to $0.08 - 0.13\text{ MJy/sr}$), the network's static convolutional bias generates large DC reconstruction residuals on empty sky, burying faint injections.
3. **Scoring Metric Mismatch for Extended Sources:**  
   The benchmark evaluated detection using single peak-pixel $\chi^2$ (`model_target_peak_chi2`). For diffuse sources whose flux is dispersed over dozens of pixels, peak $\chi^2$ is naturally low ($<150$), while null controls frequently exhibit single-pixel noise spikes exceeding $300$. When recomputed using aperture-integrated differential flux (`differential_residual_flux`), extended source AUROC jumps from **0.5704** to **0.9700**.
4. **Poisson Variance Dilution:**  
   The physical injection engine correctly added shot variance to `inj_var`. However, dividing by elevated variance in the $(I - \hat{I})^2 / \text{Var}$ formulation paradoxically dampened the normalized anomaly score of diffuse injections below that of quiet null controls.

---

## 2. Task 1.1S Result Recap & Inspected Artifacts

All forensic analyses are grounded directly in authoritative, hashed repository deliverables:

| Inspected Artifact Path | SHA-256 Checksum | Forensic Utility |
| :--- | :--- | :--- |
| [`checkpoints/astrovision_spatial_v2.pt`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/checkpoints/astrovision_spatial_v2.pt) | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | Architecture, weights, layer definitions |
| [`reports/ASTROVISION_TASK_1_1S_INDEPENDENT_AUDIT_REPORT.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/ASTROVISION_TASK_1_1S_INDEPENDENT_AUDIT_REPORT.md) | `91026b3afe2943a6a58e307875eccdee70c9b6bc2af8baadf71391057b4128d4` | Verified metrics and confusion matrices |
| [`reports/manifests/astrovision_task_1_1s_independent_audit_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/manifests/astrovision_task_1_1s_independent_audit_manifest.json) | `c9ec031af04762b13cf092552961733de8a4b43d3e48f4e42e2b445dd8c72002` | Machine-readable metrics & audit outputs |
| [`data/processed/pilot_results/astrovision_pilot_trial_results.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/data/processed/pilot_results/astrovision_pilot_trial_results.csv) | `4afddbb31d9f1b579d711712da431bf1c19701d7a63d25e9a06995a71c9d523f` | 2,500 raw per-trial execution records |
| [`data/processed/pilot_results/calibration_parameters.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/data/processed/pilot_results/calibration_parameters.json) | `4a5bbe8a04dffb609b507eba45f0d34a1ebb235e18d2f586bbad4906f09a46ac` | Operating thresholds $\tau_d$ and transfer curves |
| [`data/processed/pilot_results/pilot_evaluation_metrics.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/data/processed/pilot_results/pilot_evaluation_metrics.json) | `688b98d123b3cd5bc942a1bda050ee88ccbf03132c038ed09605cd1a22e14393` | Summary performance, detector/pointing breakdowns |
| [`models/astrovision/train_spatial_astrovision.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/astrovision/train_spatial_astrovision.py) | *Source Code* | Training pipeline, dataset loader, loss formulation |
| [`scripts/validation/astrovision_injection_benchmark_v2.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/scripts/validation/astrovision_injection_benchmark_v2.py) | *Source Code* | Cutout extraction, injection physics, inference runner |

---

## 3. Detector-Wise Forensic Analysis

### 3.1 Detector Disparity Summary

```
+----------+---------------+------------+------------+---------------+----------------+-------------------+
| Detector | Bandpass (µm) | Eval FPR   | Point AUROC| Point Recovery| Extended AUROC | Extended Recovery |
+----------+---------------+------------+------------+---------------+----------------+-------------------+
| D1       | 0.75 – 1.11   | 0.1905     | 0.7188     | 44.05%        | 0.6087         | 27.38%            |
| D2       | 1.11 – 1.63   | 0.0595     | 0.6835     |  5.95%        | 0.4957         |  3.57%            |
| D3       | 1.63 – 2.42   | 0.0602     | 0.7216     | 16.87%        | 0.5992         | 20.48%            |
| D4       | 2.42 – 3.48   | 0.1084     | 0.4776     |  4.82%        | 0.3041         |  6.02%            |
| D5       | 3.48 – 4.42   | 0.0361     | 0.7596     |  6.02%        | 0.6847         |  9.64%            |
| D6       | 4.42 – 5.00   | 0.0602     | 0.8763     | 34.94%        | 0.7750         | 24.10%            |
+----------+---------------+------------+------------+---------------+----------------+-------------------+
```

### 3.2 Forensic Autopsy of Detector 4 Catastrophe (AUROC = 0.4776 / 0.3041)

1. **Threshold Hyper-Inflation via Calibration Outliers:**  
   The D4 operating threshold was calibrated at $\tau_d = \mathbf{1,007.30}$. In `CALIBRATION_CONTROL`, extreme outliers reached $\chi^2 = 10,515.58$. In `EVALUATION_CONTROL`, an outlier reached $\chi^2 = \mathbf{410,561.84}$.
2. **Inspecting the Worst Outlier (`PILOT_001118`):**  
   - File: `level2_2026W30_1B_0009_4D4_spx_l2b-v27-2026-222.fits`
   - Center coordinate: $(x=1600.94, y=805.35)$.
   - Center true flux: $0.0955\text{ MJy/sr}$, variance: $1.02 \times 10^{-4}$, flag: $2097152$ (Clean astronomical sky).
   - In the same $128 \times 128$ patch, pixel $(93, 53)$ contained an unflagged/partially flagged saturated star with flux **$75,035.55\text{ MJy/sr}$** and flag $2097217$ (`MP_SUR_ERROR` + `MP_SOURCE`).
   - Because `AstroVisionAutoencoder` has no mask input, $75,000\text{ MJy/sr}$ entered `Conv2d`. The autoencoder smeared this flux across its bottleneck, predicting $\hat{I}(64, 64) = \mathbf{6.568\text{ MJy/sr}}$ at the center.
   - Resulting residual:
     $$\chi^2 = \frac{(0.0955 - 6.5681)^2}{1.02 \times 10^{-4}} = \frac{41.89}{0.000102} = \mathbf{409,866.56}$$
3. **Score Inversion:**  
   Because null cutouts frequently contain neighboring bright sources that contaminate the receptive field, D4 null controls produced a higher median score ($\text{median} = 283.80$) than extended injections ($\text{median} = 154.42$), directly producing an inverted AUROC $< 0.50$.
4. **Hardware / Pipeline Bug Hypothesis Rejection:**  
   Inspection of the raw FITS extensions (`IMAGE`, `VARIANCE`, `FLAGS`, `ZODI`, `EPSF`, `WCS-WAVE`) confirmed that D4 FITS products conform strictly to SPHEREx QR3 specifications. The failure is **100% architectural and algorithmic**.

### 3.3 Forensic Comparison: Why D6 Succeeded While D2/D3/D4 Stagnated
Analysis of Pearson correlation $r(\text{SNR}, \chi^2)$ across detectors explains the disparity:
- **D6:** $r = \mathbf{+0.4429}$ — Point injections scale cleanly from median $\chi^2 = 89.97$ ($\text{SNR}=3$) to $\chi^2 = 667.48$ ($\text{SNR}=25$, 85.7% recovery).
- **D5:** $r = \mathbf{+0.4537}$ — Linear response, but conservative threshold ($\tau_d = 358.42$) limits recovery.
- **D4:** $r = \mathbf{+0.1002}$ — Signal drowned by convolutional bleed.
- **D2 & D3:** $r = \mathbf{+0.0050}$ and $\mathbf{+0.0365}$ — Near-zero correlation! The model output is completely decoupled from injection SNR due to background mismatch and wide threshold spreads.

---

## 4. Pointing-Wise Domain & Background Analysis

```
+----------+--------------------+----------------------+-------------------+-------------------+-------------------+
| Pointing | Coordinates (RA, Dec) | Zodiacal Regime    | D1 Median Flux    | D4 Median Flux    | D6 Median Flux    |
+----------+--------------------+----------------------+-------------------+-------------------+-------------------+
| P0008    | (240.5°, -1.2°)    | High Zodiacal Plane  | 0.4262 MJy/sr     | 0.2307 MJy/sr     | 0.7014 MJy/sr     |
| P0002    | (240.0°, +4.8°)    | Mid-High Zodiacal    | 0.2970 MJy/sr     | 0.1512 MJy/sr     | 0.4272 MJy/sr     |
| P0001    | (239.5°, +10.2°)   | Mid Zodiacal         | 0.2834 MJy/sr     | 0.1465 MJy/sr     | 0.3950 MJy/sr     |
| P0009    | (240.2°, +7.4°)    | Mid Zodiacal Survey  | 0.2186 MJy/sr     | 0.1275 MJy/sr     | 0.4245 MJy/sr     |
| P0010    | (270.0°, +66.6°)   | North Ecliptic Pole  | 0.1370 MJy/sr     | 0.0830 MJy/sr     | 0.3037 MJy/sr     |
+----------+--------------------+----------------------+-------------------+-------------------+-------------------+
```

### 4.1 Forensic Analysis of Pointing 0010 (NEP) Collapse
Pointing `0010` is located at the North Ecliptic Pole ($\beta = +90^\circ$). It represents the deepest, lowest-zodiacal-emission field in the SPHEREx mission.

1. **Background Disparity:**  
   Compared to P0008, P0010 surface brightness drops by a factor of **$3.1\times$ on D1** ($0.426 \to 0.137\text{ MJy/sr}$) and **$2.8\times$ on D4** ($0.231 \to 0.083\text{ MJy/sr}$). Median variance drops by $2.4\times$ ($0.000237 \to 0.000100$).
2. **Training Bias Root Cause:**  
   [`models/astrovision/train_spatial_astrovision.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/astrovision/train_spatial_astrovision.py) extracted only 80 training cutouts exclusively from Pointings `0001` and `0002` (where D1 flux was $\sim 0.28 - 0.30$).
   - The autoencoder learned fixed convolutional bias terms to reconstruct an average flux of $\sim 0.30\text{ MJy/sr}$.
   - In P0010, where true sky is $0.08 - 0.13\text{ MJy/sr}$, the model's minimum reconstruction is offset by $\Delta I \approx +0.15\text{ MJy/sr}$.
   - Divided by low NEP variance ($1 \times 10^{-4}$), this DC offset produces baseline $\chi^2$ anomaly values of $100 - 250$ across completely blank sky!
3. **Score Inversion on Diffuse Signals:**  
   In P0010, the median null-control anomaly score was **$125.37$**, while the median extended injection anomaly score was **$120.01$**! The background DC mismatch produced larger anomaly spikes than genuine faint extended sources, causing Extended AUROC to collapse to **0.4599**.
4. **Correction of Prior Misconceptions:**  
   P0010 did **not** have the highest FPR (its empirical FPR was the lowest at $4.88\%$). Its failure is entirely a **loss of signal contrast** caused by training domain mismatch.

---

## 5. Calibration Transfer Failure Investigation

On the unseen evaluation cohort, FPR inflated from $5.6\%$ (calibration) to **$8.60\%$** (with astrometric cut) and **$9.00\%$** (pure $\chi^2$ cut).

### 5.1 Root Causes of Calibration Transfer Breakdown
1. **Static Scalar Threshold Inadequacy:**  
   Thresholds $\tau_d$ were fitted as single global numbers per detector (e.g., $\tau_{\text{D1}} = 399.04$). Because zodiacal background shifts by $3\times$ across the sky, noise and convolutional residual distributions vary dramatically across pointings.
2. **Detector 1 Extreme Domain Shift:**  
   In D1, the 95th percentile of null controls in evaluation was $\chi^2 = \mathbf{2,714.90}$ (nearly $7\times$ higher than $\tau_{\text{D1}} = 399.04$). Applying the calibration threshold caused D1 evaluation FPR to surge to **$19.05\%$ (16 / 84)**.
3. **Statistical Invalidation of Finite-Sample Fluctuation:**  
   An exact binomial test ($43 / 500$ vs. $p=0.05$) yields $p = 6.392 \times 10^{-4}$, and the 95% Wilson CI $[0.0645, 0.1138]$ excludes $0.05$. This formally proves that static calibration transfer failed.

---

## 6. Injection Recovery Failure Investigation

### 6.1 Point-Source Recovery (18.80% Overall, 46.27% at SNR 25)
Why did ASTROVISION miss $>81\%$ of injected point sources, and $>53\%$ of bright $\text{SNR}=25$ sources?
1. **Dilution from Sky Noise Thresholds:**  
   Because calibration thresholds had to absorb unmasked convolutional bleed and background shift outliers, thresholds $\tau_d$ were driven extremely high ($\tau_{\text{D2}} = 2,120$, $\tau_{\text{D4}} = 1,007$). Genuine point sources with $\text{SNR} \le 15$ rarely produce peak single-pixel $\chi^2$ exceeding $1,000$.
2. **Astrometric Jitter on Saturated Injections:**  
   At $\text{SNR}=25$, strong subpixel gradients occasionally caused the peak $\chi^2$ pixel to shift $2.6 - 3.1$ pixels from the target center, failing the $2.5''$ match radius gate.

### 6.2 Extended-Source Recovery (15.20% Overall, AUROC = 0.5704)
Why did extended source detection fail almost completely?
1. **Peak $\chi^2$ vs. Integrated Flux Disconnect:**  
   For a Gaussian profile with $\text{FWHM} = 12''$ ($3.9$ pixels), the injected flux is distributed over $>40$ pixels. The peak pixel contains $<5\%$ of total flux. Its peak $\chi^2$ is negligible compared to point sources.
2. **Poisson Shot Variance Damping:**  
   The injection engine added Poisson shot variance $\sigma_{\text{shot}}^2 = S_{\text{flux}} \times (\text{AGM} / t_{\text{exp}})$ to `inj_var`. Dividing by this elevated variance in $(I - \hat{I})^2 / \text{Var}$ lowered the normalized anomaly score in diffuse regions.
3. **Proof via Differential Flux AUROC:**  
   When evaluated using aperture-integrated differential flux (`differential_residual_flux`), Extended AUROC jumps from **0.5704** to **0.9700**, and Point AUROC jumps from **0.6861** to **0.9870**. This proves that the spatial signal exists in the residuals, but the **single-pixel $\chi^2$ scoring formulation is completely defective for extended sources**.

---

## 7. Statistical Limitations & Sample Distinctions

Forensic auditing requires strictly preserving statistical boundaries:
- **2,500 Individual Trials:** These are correlated sub-cutouts sampled from 120 exposures across 5 pointings. They represent within-pointing trial-level power, not independent sky fields.
- **Five Sky Pointings ($G = 5$):** Only five independent celestial lines of sight were acquired.
- **Three Evaluation Clusters ($G_{\text{eval}} = 3$):** Evaluation pointings `0002`, `0009`, and `0010` yield only $\binom{3+3-1}{3} = \mathbf{10}$ distinct cluster-bootstrap multisets.
- **Inference Limitation:** With only 10 discrete bootstrap outcomes, empirical percentile confidence intervals are mathematically unsupportable. Valid survey-scale confidence intervals require $G \ge 30$ independent pointings.

---

## 8. Root-Cause Confidence Matrix

Each suspected failure mechanism is formally assigned exactly one status:

| Suspected Cause | Status | Key Evidence / Code Location | Confirmatory Diagnostic | Required Additional Evidence |
| :--- | :---: | :--- | :--- | :--- |
| **1. Unmasked Input Conv2d Bleed** | **CONFIRMED** | `models/astrovision/model.py`: `AstroVisionAutoencoder.forward` ignores mask. | `PILOT_001118` produces $\chi^2 = 409,866$ on clean sky due to $75,035\text{ MJy/sr}$ star. | PConv / masked convolution re-run. |
| **2. Absence of Background Normalization** | **CONFIRMED** | `train_spatial_astrovision.py`: raw flux trained without zero-centering. | P0010 NEP flux drops $3.1\times$, causing $+0.15\text{ MJy/sr}$ DC offset and score elevation. | Test with local median subtraction. |
| **3. Peak $\chi^2$ Scoring Mismatch for Extended Sources** | **CONFIRMED** | `astrovision_injection_benchmark_v2.py`: scoring uses peak pixel $\chi^2$. | Peak $\chi^2$ AUROC = $0.5704$, while differential flux AUROC = $0.9700$. | Aperture-summed anomaly scoring. |
| **4. Poisson Shot Variance Damping** | **CONFIRMED** | `astrovision_injection_benchmark_v2.py`: line 420 (`inj_var += shot_var`). | D4 extended injections have lower median $\chi^2$ ($154.42$) than controls ($283.80$). | Benchmark with nominal sky variance. |
| **5. Static Scalar Threshold Transfer Failure** | **CONFIRMED** | `calibration_parameters.json`: fixed $\tau_d$ across heterogeneous pointings. | D1 eval FPR surges to $19.05\%$ ($p = 6.39 \times 10^{-4}$). | Local noise-conditioned quantile model. |
| **6. Training Sample Starvation (80 patches)** | **STRONGLY SUPPORTED** | `train_spatial_astrovision.py`: only 80 patches across 16 files. | Model fails to generalize across 6 detectors and 5 sky regions. | Scaling training set to $\ge 1,000$ patches. |
| **7. D4 Hardware or QR3 Pipeline Bug** | **REJECTED** | FITS headers & images conform to QR3 spec; calibration extensions valid. | D4 failure is fully explained by unmasked bright stars and low NEP variance. | None (hypothesis disproven). |
| **8. Pointing 0010 High False Alarm Rate** | **REJECTED** | `pilot_evaluation_metrics.json`: P0010 FPR = $4.88\%$ (lowest of all pointings). | P0010 problem is loss of signal contrast (score inversion), not high FPR. | None (hypothesis disproven). |

---

## 9. Prioritized Remediation Plan

The remediation architecture addresses the 8 mandated technical areas:

```
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| Priority | Technical Area                     | Proposed Remediation Action                                   | Complexity  | Risk       | Pre-Deadline Feasible |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 1        | Mask-Aware Quality Preprocessing   | Replace Conv2d with Partial Convolutions (PConv) or clamp     | Low         | Zero       | **YES**               |
|          |                                    | fatal-flagged pixels (>5-sigma) to local median at input.     |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 2        | Background & Noise Normalization   | Implement Local Adaptive Noise Scaling (LANS):                | Low         | Very Low   | **YES**               |
|          |                                    | I_norm = (I - median(I)) / robust_sigma(I).                   |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 3        | Uncertainty-Aware Scoring          | Replace single-pixel peak chi2 with Aperture-Integrated       | Low         | Very Low   | **YES**               |
|          |                                    | Anomaly Flux: S_anom = sum_ap ((I - I_hat)^2 / Var_sky).      |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 4        | Calibration Transfer Strategy      | Replace fixed scalar tau_d with Quantile-Regression           | Medium      | Low        | **YES**               |
|          |                                    | Thresholding: tau_d(bg, sigma) conditioned on local sky.     |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 5        | Extended-Source Multi-Scale Head   | Evaluate multi-scale Gaussian pooling kernels to match        | Medium      | Low        | **YES**               |
|          |                                    | diffuse morphological footprints (FWHM 6" - 24").             |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 6        | D4 Forensic Calibration Fine-Tune  | Re-calibrate D4 with outlier-resistant median absolute        | Low         | Low        | **YES**               |
|          |                                    | deviation (MAD) scaling to eliminate 400k outlier skew.       |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 7        | Stratified Dataset Retraining      | Retrain ASTROVISION on 1,200 patches sampled across           | Medium      | Moderate   | **FEASIBLE IF SCOPED**|
|          |                                    | ecliptic, mid-latitude, and polar pointings.                  |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
| 8        | Baseline Benchmark Comparison      | Benchmark remediated ASTROVISION against classical photutils  | Low         | Zero       | **YES**               |
|          |                                    | aperture differencing and CHRONOS-X temporal baseline.       |             |            |                       |
+----------+------------------------------------+---------------------------------------------------------------+-------------+------------+-----------------------+
```

---

## 10. Deadline-Aware Recommendation (10 November 2026 Milestone)

The project milestone deadline is **10 November 2026** (approximately 3 days from current audit date).

### Strategic Feasibility Trade-Off
1. **Unfeasible Before Deadline:**  
   Attempting a full unconstrained model redesign, multi-detector neural architecture search, or training a complex multi-head transformer cannot be responsibly executed, validated, and audited within 72 hours.
2. **Feasible & High-Impact Before Deadline:**  
   A tightly scoped, bounded remediation focusing on:
   - **Fix 1 (Input Defect Clamping):** Preprocessing cutouts to clamp/impute fatal flagged pixels prior to `Conv2d`.
   - **Fix 2 (Local Background Subtraction):** Subtracting local median background before inference.
   - **Fix 3 (Aperture-Summed Scoring):** Updating benchmark scoring to integrate anomaly flux over source apertures.
   - **Fix 4 (Stratified Retraining):** Re-running the 10-epoch autoencoder training script (`train_spatial_astrovision.py`, execution time: ~30 seconds) with normalized cutouts across all 5 pointings.

---

## 11. Final Decision & Governance Rule

### Formal Recommendation:
**`LIMITED REMEDIATION JUSTIFIED`**

Proceeding to a separately authorized, tightly bounded remediation task (**Task 1.1U**) is scientifically justified. The remediation must be strictly limited to the four high-impact, low-risk fixes identified above.

### Mandatory Governance Rule:
**`ASTROVISION STATUS: FAIL — NOT CERTIFIED`**

This investigation was strictly diagnostic and read-only. Zero model weights, checkpoints, calibration manifests, or test suites were mutated. No retraining or remediation may begin until explicit authorization is granted by project governance.

