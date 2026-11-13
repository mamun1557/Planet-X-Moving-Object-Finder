# SPECTRA-X / F1 — PHASE 3, TASK 1.1
## Independent ASTROVISION Benchmark Integrity & Statistical Audit

**Audit date:** 2026-11-06
**Audit subject:** Phase 3 Task 1 ASTROVISION spatial injection/recovery benchmark
**Audited artifacts:**
- [`reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md) (the "original report")
- [`scripts/validation/astrovision_injection_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validation/astrovision_injection_benchmark.py)
- [`scripts/validation/run_astrovision_injection_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validation/run_astrovision_injection_benchmark.py)
- [`data/processed/validation/astrovision_injection_manifest.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/validation/astrovision_injection_manifest.csv), [`astrovision_injection_results.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/validation/astrovision_injection_results.csv), [`benchmark_metrics.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/figures/astrovision/benchmark_metrics.json)
- [`checkpoints/astrovision_spatial_v2.pt`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/checkpoints/astrovision_spatial_v2.pt), [`models/astrovision/model.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/models/astrovision/model.py), [`models/astrovision/train_spatial_astrovision.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/models/astrovision/train_spatial_astrovision.py)

> [!IMPORTANT]
> **Final decision: FAIL as currently reported.** The experiment itself is genuine and reproducible, but the original report has material errors. Its AUROC is wrong. Its photometric-linearity claim is circular. The physical noise model uses the wrong gain for 4 of the 6 detectors. Several statements in it (magnitudes, flux table, architecture, HDU layout, AUROC CI, test names) are not supported by the code or data. The experiment can reach **PASS WITH LIMITATIONS** once the corrections in §8 are applied. See §9.

> [!NOTE]
> **Conflict-of-interest disclosure.** The agent that ran this audit also wrote the original benchmark and report. To limit self-confirmation, every conclusion below comes from fresh scripts that read the persisted data and the authoritative FITS directly. Nothing was taken from the original report's text.

---

## 0. Audit method and read-only guarantees

| Step | Script / evidence (all outputs under `scratch/`) |
| :--- | :--- |
| FITS header, checkpoint, ePSF inspection | [`scratch/audit11_inspect.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scratch/audit11_inspect.py) |
| Full independent metric recomputation (exact AUROC, average precision, Wilson / Clopper–Pearson, binomial MLE sigmoid, iid and cluster bootstraps, threshold sensitivity, astrometry, photometry, SNR definition, AGM, noise realism, sky-overlap leakage) | [`scratch/audit11_recompute.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scratch/audit11_recompute.py) → [`scratch/audit11_out/audit_recomputed_metrics.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scratch/audit11_out/audit_recomputed_metrics.json) |
| Per-detector, background-regime and gain-impact checks | [`scratch/audit11_extra.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scratch/audit11_extra.py) |
| End-to-end re-execution with **outputs redirected** to `scratch/audit11_repro/` | [`scratch/audit11_repro_rerun.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scratch/audit11_repro_rerun.py) |

The re-run script hashed the protected files before and after execution. All were unchanged:

| Protected file | SHA-256 (prefix) before = after |
| :--- | :--- |
| `astrovision_injection_manifest.csv` | `339d5c58a12122f0` |
| `astrovision_injection_results.csv` | `22ecaf448e1f0131` |
| `benchmark_metrics.json` | `5f8fd6bc1313b8f0` |
| `pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe` |
| `astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5` (full: `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557`) |

No model was retrained, and no FITS file, catalogue, manifest, result table or original report was modified.

**Reproducibility result:** the re-run (seed 42) reproduced all 423 trial IDs, injection positions, fluxes and every `recovered` decision exactly. The JSON metrics were identical. Floating-point differences were at most 1.7×10⁻⁴ in `target_peak_chi2` (GPU non-determinism), with no effect on any decision. **Computational reproducibility: VERIFIED.**

---

## 1. Verified experimental counts and independence

### 1.1 Counts

| Quantity | Verified value | Evidence |
| :--- | :--- | :--- |
| Total trials (manifest = results, 1:1 join on unique `trial_id`) | **423** | linkage check: 423/423 joined, columns consistent |
| Negative controls / point / extended | **97 / 162 / 164** | `by_cohort` |
| Requested by driver vs. harvested | requested 150/250/250. Only **423** safe cutouts were found, so cohorts were **auto-rescaled** | driver lines 96–102; run log "Total Safe Cutouts Harvested: 423" |
| Unique Level-2 FITS files | **23** (all Pointing 0003 files on disk) | `unique_files` |
| Unique exposures (`OBSID`) | **4** (`2026W30_1B_0003_1…4`) | `unique_obs_id` |
| Unique cutouts (file, x, y) | **423** | `unique_cutout_keys` |
| Unique sky positions (friends-of-friends, 1 px / 5 px) | **423 / 421** | sky clustering via each file's WCS |
| Injection sites reused | **None** (no two trials within 1 px on sky; 0 same-file pairs within 11 px) | `frac_lt_1px = 0`, `pairs_injection_sites_within_11px_same_file = 0` |
| Cross-file trial pairs within 11 px on sky | 19 (of 89,253 pairs) | co-pointed detectors see the same sky |
| Trial pairs whose 128×128 cutout footprints overlap on sky | **1,713** pairs. 89.6% of trials have a neighbour closer than 128 px | stride 36 px < patch 128 px |
| Controls whose footprint overlaps an injected trial's footprint | **86 / 97** (69 share pixels in the same file) | `controls_with_injected_trial_footprint_overlap` |

### 1.2 Detector representation (as executed)

| Detector | Files | Controls | Point | Extended | Total | Share |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| D1 | 4 | 5 | 2 | 3 | 10 | 2.4% |
| D2 | 4 | 4 | 7 | 10 | 21 | 5.0% |
| D3 | 3 | 7 | 11 | 20 | 38 | 9.0% |
| D4 | 4 | 6 | 11 | 17 | 34 | 8.0% |
| D5 | 4 | 38 | 69 | 53 | 160 | 37.8% |
| D6 | 4 | 37 | 62 | 61 | 160 | 37.8% |

- Each file was capped at 40 cutouts, collected in raster order. The 8 D5/D6 files reached the cap within detector rows y ≈ 214–718, so their samples cover only the **lower ~25% of the array**. Files with low clean-sky yield contributed 1–3 trials (e.g. `1D4`: one row only).
- **75.7%** of all trials come from 8 MWIR files (D5, D6). Results are therefore dominated by D5/D6 and are **not** a detector-balanced characterisation.

### 1.3 Independence assessment

- Every injection went into its own **in-memory copy** of a cutout, so no injected flux leaks into another trial or into a control. Each trial is a unique sky site. **Physical cross-contamination: none.**
- Trials are **not independent astronomical observations**. They come from **4 exposures** of one pointing on 23 detector arrays. Most cutouts overlap neighbouring cutouts, and controls share background pixels with injected trials. The effective number of independent units sits somewhere between 23 (files) and 423 (sites). To account for this, file-cluster bootstrap intervals are reported alongside iid intervals in §2–3. They are 10–40% wider.
- Controls and injections were drawn from the **same shuffled pool**, so their backgrounds have the same distribution (good). The controls are still **not an independent hold-out** for threshold selection (see §5).

---

## 2. Independently recomputed metrics

### 2.1 Positive and negative definitions and matching (verified from code)

- **Positive:** an injected cutout (point or extended). **Negative:** an uninjected control evaluated at its centre (64, 64).
- **Score:** `target_peak_chi2` = maximum of the χ² map `(I − Î)² / Var × mask` within **2.5 px** (point) or **3.5 px** (extended) of the true injection position.
- **Recovered:** score ≥ τ **and** subpixel-refined peak within 2.5 px (point) / 3.5 px (extended). For controls the rule is score ≥ τ only.
- The position criterion rejected **4** injections whose score was above τ (184 → 180).
- The ROC/PR curves use **score only**, while precision and recall use **score + position**. The two definitions differ slightly.
- The original report says the match radius is "12.3″ (2.0 px)" and that detection uses a "5×5 aperture". **Both are incorrect**: the code uses circular radii of 2.5 / 3.5 px.

### 2.2 Classification at τ = 169.10

| Metric | Reported | Recomputed | Wilson 95% | File-cluster bootstrap 95% |
| :--- | :---: | :---: | :---: | :---: |
| TP / FP / FN / TN | 180/10/146/87 | **180/10/146/87** | — | — |
| Precision | 94.74% | **94.74%** | [90.6, 97.1]% | [90.3, 98.1]% |
| Recall (all SNR 2–50) | 55.21% | **55.21%** | [49.8, 60.5]% | [48.1, 63.3]% |
| FPR | 10.31% | **10.31%** (10/97) | [5.7, 17.9]% (Clopper–Pearson [5.1, 18.1]%) | [3.6, 20.6]% |
| F1 | 0.6977 | **0.6977** | — | — |

### 2.3 AUROC and AUPRC (discrepancy found)

| Metric | Reported | Recomputed (exact) | iid bootstrap 95% | File-cluster bootstrap 95% |
| :--- | :---: | :---: | :---: | :---: |
| AUROC | **0.7357** | **0.8406** (Mann–Whitney U) | [0.793, 0.884] | [0.770, 0.895] |
| AUPRC | 0.9346 | **0.9367** (average precision) | [0.907, 0.962] | [0.899, 0.966] |
| AUPRC no-skill baseline (= prevalence) | not reported | **0.771** | — | — |

**Cause of the AUROC error.** The driver integrates the ROC curve over a fixed threshold grid, `logspace(1, 4)` (10 to 10⁴). The lowest control score is **5.33**, so the grid never reaches FPR = 1: the maximum FPR reached is **0.897**. The trapezoid therefore leaves out the segment [0.897, 1.0]. This audit reproduced the reported 0.7357 exactly with the original method, which confirms the cause. **The reported AUROC is biased low and is wrong.** The "95% CI [0.681, 0.790]" in the original report is **not produced by any code in the repository** and must be retracted.

**Subset AUROC/AUPRC (exact):**

| Subset | AUROC | AUPRC | Prevalence |
| :--- | :---: | :---: | :---: |
| Point vs controls | 0.830 | 0.883 | 0.625 |
| Extended vs controls | 0.851 | 0.884 | 0.628 |
| SNR ≥ 10 vs controls | 0.945 | 0.954 | 0.650 |
| SNR ≤ 7 vs controls | 0.711 | 0.742 | 0.601 |

### 2.4 Why AUPRC is high compared with AUROC: class prevalence

The benchmark has **326 positives : 97 negatives (prevalence 77.1%)**. A random classifier would already score AUPRC = 0.771. AUPRC and precision depend on prevalence. Re-weighting the negatives to realistic prevalences gives:

| Assumed positive prevalence π | AUPRC (re-weighted) | Precision at τ = 169.1 |
| :---: | :---: | :---: |
| 0.771 (benchmark) | 0.937 | 94.7% |
| 0.5 | 0.824 | 84.3% |
| 0.1 | 0.392 | 37.3% |
| 0.01 | 0.101 | 5.1% |
| 0.001 | 0.057 | 0.5% |

In a survey setting, where genuine anomalies are rare (π ≪ 0.1), the 10% FPR at τ = 169.1 means **most alerts would be false**. The "94.74% global precision" headline is an artifact of the benchmark's class balance. It must not be quoted without the prevalence.

---

## 3. Completeness audit

### 3.1 Trials and recoveries per SNR (verified)

**Point sources (ePSF)**

| Nominal SNR | n | k | Rate | Wilson 95% | Clopper–Pearson 95% | Files | Recovered median pos. error (px) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2 | 17 | 2 | 11.8% | [3.3, 34.3] | [1.5, 36.4] | 6 | 1.67 |
| 3 | 17 | 2 | 11.8% | [3.3, 34.3] | [1.5, 36.4] | 9 | 1.77 |
| 4 | 16 | 3 | 18.8% | [6.6, 43.0] | [4.0, 45.6] | 11 | 1.71 |
| 5 | 16 | 3 | 18.8% | [6.6, 43.0] | [4.0, 45.6] | 9 | 1.16 |
| 7 | 16 | 3 | 18.8% | [6.6, 43.0] | [4.0, 45.6] | 8 | 0.14 |
| 10 | 16 | 13 | 81.2% | [57.0, 93.4] | [54.4, 96.0] | 11 | 0.20 |
| 15 | 16 | 14 | 87.5% | [64.0, 96.5] | [61.7, 98.4] | 9 | 0.21 |
| 20 | 16 | 15 | 93.8% | [71.7, 98.9] | [69.8, 99.8] | 10 | 0.23 |
| 30 | 16 | **16** | 100% | **[80.6, 100]** | **[79.4, 100]** | 10 | 0.19 |
| 50 | 16 | **16** | 100% | **[80.6, 100]** | **[79.4, 100]** | 9 | 0.21 |

**Extended sources (Gaussian, FWHM 12/18/24/36″; 5–6 trials per FWHM per SNR cell)**

| Nominal SNR | n | k | Rate | Wilson 95% | Clopper–Pearson 95% |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 3 | 24 | 4 | 16.7% | [6.7, 35.9] | [4.7, 37.4] |
| 5 | 20 | 2 | 10.0% | [2.8, 30.1] | [1.2, 31.7] |
| 7 | 20 | 6 | 30.0% | [14.5, 51.9] | [11.9, 54.3] |
| 10 | 20 | 9 | 45.0% | [25.8, 65.8] | [23.1, 68.5] |
| 15 | 20 | 15 | 75.0% | [53.1, 88.8] | [50.9, 91.3] |
| 20 | 20 | 19 | 95.0% | [76.4, 99.1] | [75.1, 99.9] |
| 30 | 20 | 18 | 90.0% | [69.9, 97.2] | [68.3, 98.8] |
| 50 | 20 | **20** | 100% | **[83.9, 100]** | **[83.2, 100]** |

> [!WARNING]
> **16/16 and 20/20 are not proof of perfect detection.** With 95% confidence they only show that true completeness is at least **79–81%** (16/16) or **83–84%** (20/20). The original report's wording "Recovery reaches 100.0% at SNR ≥ 30σ" must be restated with these lower bounds.

### 3.2 Low-SNR "recoveries" are consistent with chance

- Pooled point SNR ≤ 7: **13/82 = 15.9%**. Pooled extended SNR ≤ 7: **12/64 = 18.8%**. Control FPR: **10.3%**. Fisher exact test against controls: p = **0.37** (point) and p = **0.16** (extended). **No significant excess.**
- Recovered low-SNR point sources (SNR 2–4) have a median position error of 1.67–1.77 px. If the χ² peak were placed at random inside the 2.5 px search disc, the median error would be **1.77 px**. These "detections" therefore behave like background fluctuations that happen to fall in the match window.
- So the completeness curve has a **false-match floor of about 10%**, and the original fit did not model it.

### 3.3 Sigmoid fitting method, parameter uncertainty and C50/C90 CIs

**Original method (verified by reproduction):** `scipy.optimize.curve_fit` of a two-parameter logistic to the **binned rates**. It is unweighted, ignores binomial variance and has no false-match floor. The original report gives **no parameter uncertainty and no C50/C90 confidence interval**. The slope reported for point sources (0.4619) differs slightly from the reproduced value (0.4614).

| Estimator | Point C50 | Point C90 | Extended C50 | Extended C90 |
| :--- | :---: | :---: | :---: | :---: |
| Original (unweighted LSQ on bins) | 8.31 | 13.07 | 10.73 | 18.93 |
| LSQ delta-method 95% CI (from `pcov`) | [7.21, 9.40] | [10.49, 15.65] | [9.68, 11.79] | [16.33, 21.52] |
| **Binomial MLE (trial level), no floor** | **8.81** | **15.44** | **11.25** | **21.74** |
| MLE iid bootstrap 95% | [7.39, 10.58] | [12.26, 19.60] | [9.31, 13.50] | [16.76, 28.43] |
| MLE **file-cluster** bootstrap 95% | **[7.49, 10.12]** | **[11.43, 21.36]** | **[8.69, 13.83]** | **[15.92, 31.27]** |
| Binomial MLE with 10.3% false-match floor | 9.20 | 15.00 | 11.59 | 21.47 |
| Floor model, file-cluster bootstrap 95% | [7.77, 10.73] | [10.01, 21.41] | [9.11, 14.46] | [15.69, 31.42] |
| Linear interpolation of observed rates | 8.5 | 17.0 | 10.8 | 18.8 |
| First SNR bin with Wilson lower bound ≥ level | 10 (≥50%) | **none** | 15 (≥50%) | **none** |

**Findings**

1. **No extrapolation.** All fitted limits fall inside the sampled range (point 2–50, extended 3–50).
2. **Point C50 lies in an unsampled gap.** Completeness jumps from 18.8% at SNR 7 to 81.2% at SNR 10, and there are no trials in between. The logistic shape assumption, not the data, determines where C50 falls inside that gap.
3. **C90 is not demonstrated at 95% confidence for either source class.** No SNR bin has a Wilson lower bound ≥ 90%. The C90 values come purely from the model fit, and the cluster-robust intervals span roughly a factor of 2.
4. The defensible estimates are the trial-level MLE values with cluster-bootstrap CIs: **point C50 ≈ 8.8 [7.5, 10.1], C90 ≈ 15.4 [11.4, 21.4]; extended C50 ≈ 11.2 [8.7, 13.8], C90 ≈ 21.7 [15.9, 31.3]**, all in *nominal* SNR (see §4.4). The reported 13.07 and 18.93 C90 values are **optimistic by about 2.4σ and 2.8σ** compared with the MLE.

### 3.4 Sensitivity to the detection threshold

The table uses binomial MLE. For τ ≥ 169.1 the position criterion is applied exactly. For τ = 150 it is score-only, because position errors were not stored for non-detections.

| τ | Control FPR | Point C50 | Point C90 | Ext. C50 | Ext. C90 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 150.0 | 12.4% | 7.4 | 12.8 | 9.8 | 20.5 |
| **169.1 (canonical)** | **10.3%** | **8.8** | **15.4** | **11.2** | **21.7** |
| 200 | 7.2% | 10.3 | 16.5 | 14.1 | 26.7 |
| 251.3 (median + 5·MAD) | 5.2% | 12.2 | 19.2 | 17.4 | 32.1 |
| 500 | 3.1% | 20.0 | 29.6 | 34.3 | 58.9 * |
| 1159 (control P99) | 1.0% | 35.7 | 46.3 | 60.6 * | 84.6 * |
| 1652 (above control max) | 0.0% | 45.7 | 61.5 * | 94.9 * | 137 * |

\* Extrapolated beyond the maximum sampled SNR of 50. Not supported by data.

**The completeness limits depend strongly on the operating point.** Moving from FPR ≈ 10% to FPR ≈ 1% shifts point-source C50 from about 9σ to about 36σ. The control χ² distribution has a heavy tail (median 45.8, P95 260.9, P99 1159, max 1652). Any C50/C90 quoted without its FPR is incomplete.

---

## 4. Physical unit and noise audit

### 4.1 Verified FITS structure (from headers; original report §3.1 is incorrect)

| HDU | Name | Type / shape | BUNIT |
| :---: | :--- | :--- | :--- |
| 0 | PRIMARY | empty | — |
| 1 | IMAGE | float32 2040×2040 | `MJy / sr` |
| 2 | FLAGS | int32 2040×2040 (compressed) | dimensionless |
| 3 | VARIANCE | float32 2040×2040 | `MJy2 / sr2` |
| 4 | ZODI | float32 2040×2040 | `MJy / sr` |
| 5 | EPSF | binary table, 441 rows (D3: 451) × 33×33 | — |
| 6 | WCS-WAVE | binary table | µm |

The original report describes a 2048×2048 PRIMARY image with MASK and QUALITY HDUs. That layout does not exist in these files. The header has **no `EXPTIME` keyword**, and `PSF_FWHM = 7.53″` (1.22 px), whereas the original report claimed "≈ 6.15″ / 1.0 px".

### 4.2 Dimensional consistency (verified)

With $I$ in MJy sr⁻¹, AGM in MJy s e⁻¹ sr⁻¹ (BUNIT of `abs_gain_matrix_D*` confirmed), and $t$ in s:

$$N_e = \frac{I\,t}{\mathrm{AGM}}\;[\mathrm{e^-}],\qquad \sigma_I^2 = N_e\left(\frac{\mathrm{AGM}}{t}\right)^2 = I\,\frac{\mathrm{AGM}}{t}\;[\mathrm{MJy^2\,sr^{-2}}]$$

The code (`inv_rate = exptime/agm`, `shot_var = flux·agm/exptime`) matches these expressions. Variance is added in the same units as the VARIANCE HDU. **The formula is dimensionally correct.**

- **Exposure time:** 115.12 s is hard-coded, because `EXPTIME` is absent from the header. It agrees with `DATE-END − DATE-BEG` = **115.117 s**. Supported.
- **ePSF:** in-file EPSF tables match the external templates exactly (relative difference 0.0) for D1, D2, D4, D5 and D6. **For D3 the benchmark loaded `epsf_D3…v1` (441 bins), but the science files carry the v2 table (451 bins, identical to `epsf_D3…v2`).** The 11 point trials on D3 used a superseded PSF. Interpolation is **bilinear** (`method="linear"`), not "bicubic spline" as the original report states. The kernel (±5 px) fully contains the ePSF support (±3.2 px), and renormalising to sum = 1 is valid for a pixel-integrated ePSF. **PSF flux conservation: verified** (unit test plus code inspection).
- **Extended sources:** a discrete Gaussian renormalised to the requested total within ±4σ. FWHM is converted using the WCS-derived pixel scale (6.136–6.168″/px across files). **Verified.**

### 4.3 Physical errors and missing noise components

| # | Finding | Evidence | Impact |
| :--- | :--- | :--- | :--- |
| P1 | **One AGM value (D1 median, 0.11683) was applied to all detectors.** The true medians are D2 0.1124, D3 0.1085, D4 0.0894, **D5 0.3373, D6 0.4580**. | `abs_gain_matrix_D*` medians; driver passes `DEFAULT_AGM` to every trial | For D5 and D6 (75.7% of trials), injected-source shot noise, in both the Poisson realisation and the VARIANCE plane, is **2.9× and 3.9× too small in variance**. At nominal SNR 10, total peak-pixel variance is underestimated by ×1.56 (D5) and ×1.59 (D6). At SNR 50 the factors are ×2.3 and ×2.6. Bright injections on D5/D6 look cleaner than real sources. |
| P2 | Per-pixel AGM variation (5–95% spread ≈ ±10–20%) was ignored. A median value was used. | AGM percentiles | Second-order. |
| P3 | **"SNR" is a nominal background-only quantity.** It is defined as `total_flux × 0.25 / sqrt(median VARIANCE in a 17×17 box)`. The source's own shot noise is excluded. | driver lines 196–197, 291–292 | The SNR axis is not a detection significance. |
| P4 | **The assumed ePSF peak fraction (0.25) is wrong.** The measured median is **0.372** (range 0.24–0.65). By detector: D1 0.565, D2 0.444, D3 0.467, D4 0.347, D5 0.365, D6 0.358. | ePSF rendering of every point trial | The true background-only peak SNR is about **1.49×** the nominal value, and PSF-matched SNR about **1.87×**. The mapping differs by detector, so one "SNR" value means different physical depths on different detectors. |
| P5 | **VARIANCE underestimates the real pixel scatter.** Robust (MAD) pixel RMS / √(median VARIANCE) over the controls' 128 px cutouts has median **1.40** (16–84%: 1.19–2.76). By detector: D1 3.56, D2 2.59, D3 2.77, D4 3.60, D5 1.42, D6 1.20. In the 17×17 local box the median is 1.25. | `scratch/audit11_recompute.py` noise-realism block | The VARIANCE plane does not capture confusion, structure and correlated noise, especially on D1–D4. Nominal SNR is therefore **overstated relative to the true local fluctuation level**, partly offsetting P4. |
| P6 | **χ² is not a calibrated significance.** The median control peak χ² is **45.8**. For pure noise over about 21 pixels the expected value is **4.6**. | threshold block | Reconstruction error dominates χ², about 10× the noise expectation. "Detection significance" cannot be read as σ. |
| P7 | Missing components not simulated: correlated/1/f noise added by the source, non-linearity, flat-field and absolute-calibration uncertainty, intrapixel response beyond the ePSF, PSF colour dependence, cosmic rays. | code inspection | These limit physical interpretation. None invalidates a relative benchmark. |
| P8 | **Flux units mislabelled.** `injected_flux_mjy_sr` is a **sum over pixels of surface brightness** (units MJy sr⁻¹ · pix). Integrated flux density is that value × Ω_pix (8.896×10⁻¹⁰ sr) × 10⁶ Jy/MJy. | code | The column name and the original report's "F ≈ 0.68 MJy/sr" are dimensionally wrong. |
| P9 | **Magnitudes in the original report are wrong.** Converting the actual injected fluxes gives median point-source m_AB ≈ **16.1** at nominal SNR 10, ≈ 16.5 at SNR 7, ≈ 15.4 at SNR 15. The report's **"m_AB ≈ 19.3 / 18.8"** does not follow from any recorded value. The "Median Flux" column of its §6.2 table (0.163 … 4.088) does not match the data either (actual medians: 0.285, 0.653, 0.556, 0.845, 1.006, 1.438, 2.676, 2.863, 4.173, 9.246). Because SNR is normalised per cutout and per detector, a single magnitude limit across D1–D6 is meaningless anyway. | `photometry.injected_flux_median_by_snr_point`, `mAB_of_median_flux_by_snr_point` | Retract. |

### 4.4 Masks and image integrity

- Original NASA FITS are opened read-only. No injected FITS products are ever written. The "FITS integrity after injection" and "WCS preservation" tests therefore only confirm that the **originals** are unchanged and that the pixel scale is 6.0–6.3″. They do not test an injected product.
- Injection ignores FLAGS outside the 5×5 core (`flags=np.zeros_like(...)` is passed). Masked pixels are still excluded from χ² through `mask`. NaNs are replaced with the local median, whereas training used NaN → 0.25: a small preprocessing mismatch.
- `test_mask_preservation` passes trivially, because the engine never reads or writes `flags`.

---

## 5. Evaluation independence

| Question | Finding | Evidence |
| :--- | :--- | :--- |
| Was Pointing 0003 excluded from training and validation? | **Yes.** Checkpoint `config`: `pointing_train ['0001','0002']`, `pointing_val ['0004','0005','0006']`, `pointing_test_excluded ['0003']`. The training script filters on `_0001_`/`_0002_` in file names. | checkpoint dict; `train_spatial_astrovision.py` lines 111–113 |
| Sky overlap between training/validation and P0003? | **None.** Minimum centre separation from any P0003 file: training ≥ **50.99°**, validation ≥ **29.61°**. The detector field of view is 3.49°. | `leakage.files` |
| Which detectors did ASTROVISION see in training? | **D1 and D2 only** (QR3 D1 ×8 files, QR2 D2 ×8 files; 80 training patches, best epoch 4). | file list; checkpoint `config` |
| Consequence | **392 of 423 trials (92.7%) are on D3–D6, which the model never saw.** The benchmark mainly measures *out-of-distribution* behaviour. Per-detector conclusions for D3–D6 carry a domain-shift confound. | §1.2 |
| Was τ = 169.10 set independently of the evaluation trials? | **No.** τ = max(150, median + 3·MAD) is computed from **the same 97 controls** used to report FPR (driver lines 164–170). This is threshold-selection bias. The original report's claim that it was "derived from the 90th percentile" is also inaccurate: it is median + 3·MAD, which happens to fall at the 89.7th percentile. | `threshold` block |
| Size of the bias | Split-half test (τ from 48 controls, FPR on the other 49; 5,000 splits): out-of-sample FPR mean **10.9%**, 95% range **[4.1%, 18.4%]**. The in-sample 10.3% is roughly unbiased in expectation, but its uncertainty is underestimated. The floor of 150 is an arbitrary constant. | `split_half_oos_fpr` |
| Was the injection set used to choose τ or any hyperparameter? | No for τ. However, the scanner rules (for example the "monster star" cut) were tightened during development after inspecting control outliers such as `CTRL_0080` in this same pointing. This is a mild **analyst degree-of-freedom** leak. | conversation history / code comments |

### 5.1 Detector- and background-regime performance (absent or wrong in the original report)

| Det | Injected recovered (all SNR) | Injected recovered (SNR ≥ 10) | **Control false positives** |
| :---: | :---: | :---: | :---: |
| D1 | 3/5 [0.23, 0.88] | 1/1 | 0/5 [0.00, 0.43] |
| D2 | 9/17 [0.31, 0.74] | 9/10 [0.60, 0.98] | 1/4 [0.05, 0.70] |
| D3 | 14/31 [0.29, 0.62] | 11/19 [0.36, 0.77] | 2/7 [0.08, 0.64] |
| D4 | 21/28 [0.57, 0.87] | 12/15 [0.55, 0.93] | **5/6 [0.44, 0.97]** |
| D5 | 58/122 [0.39, 0.56] | 53/62 [0.75, 0.92] | 2/38 [0.01, 0.17] |
| D6 | 75/123 [0.52, 0.69] | 69/73 [0.87, 0.98] | 0/37 [0.00, 0.09] |

- The original report's §6.5 "recovery rate" per detector **counted control false positives as recoveries** (its 190 = 180 TP + 10 FP).
- **D4's apparent high recovery comes with an 83% control false-positive rate.** That points to background χ² inflation on D4, not to "highest optical contrast". The original interpretation is unsupported. FPR is strongly detector-dependent, and the pooled 10.3% hides this.
- The original claim that D5/D6 have "higher thermal background explaining lower recovery" is not supported. At SNR ≥ 10, D5 and D6 are among the **best** performers.
- Background regime: point-source recovery by tercile of local √VARIANCE is 29/54, 30/54 and 28/54 (low/mid/high). There is no significant trend at fixed nominal SNR. (The original report did not provide this breakdown.)

---

## 6. Astrometric and photometric recovery

### 6.1 Astrometry (recomputed)

| Quantity | Reported | Recomputed |
| :--- | :---: | :---: |
| Point n | 87 | 87 |
| Median radial error | 1.327″ (0.216 px) | **1.327″ (0.215 px)** ✔ |
| 68th percentile | 1.613″ | **1.613″ (0.263 px)** ✔ |
| 90th percentile | 8.868″ | **10.38″** ✘ |
| 95th percentile | not in report (driver log: 10.871″) | 10.87″ |
| Max | — | 12.01″ (1.95 px) |
| Extended n / median / 68% | not reported | 93 / 2.58″ (0.42 px) / 4.92″ |

**Caveats**

1. The peak is searched only within 2.5 px (3.5 px for extended) of the **known** true position. Errors are truncated, so this is a *conditional, prior-informed* astrometric precision, not blind source localisation.
2. The upper tail (P90 ≈ 10″ ≈ 1.7 px) is dominated by low-SNR chance matches (see §3.2). The SNR ≥ 7 median is about 0.2 px.
3. Pixel-to-arcsec conversion used each file's WCS scale (6.136–6.168″/px). Consistent.

### 6.2 Photometry: the claim is circular

`recovered_flux_mjy_sr` is computed as `sum(injected_image − original_image)` inside r ≤ 3.5 px (driver lines 233–237 and 327–331). **It never uses the ASTROVISION reconstruction or anomaly map.** It simply re-measures the injected signal plus its Poisson realisation. Proof: the regression gives the same result **with non-detections included** (n = 162, slope 1.0035, R² = 0.9996) as with recovered sources only (n = 87, slope 1.0043, R² = 0.9995).

> [!CAUTION]
> The original report's statement that "ASTROVISION reconstruction anomalies strictly preserve injected flux scale … R² = 0.9995" is **invalid and must be retracted**. ASTROVISION flux recovery was **not measured** in this benchmark.

---

## 7. Discrepancies with the original report

| # | Original report statement | Audited fact | Severity |
| :---: | :--- | :--- | :---: |
| D1 | AUROC = 0.7357 | Exact AUROC **0.8406** [0.770, 0.895 file-cluster]. 0.7357 is a truncated-grid artifact. | **Material** |
| D2 | AUROC 95% CI [0.681, 0.790] | Not computed by any code. Fabricated. | **Material** |
| D3 | Flux linearity R² = 0.9995 shows ASTROVISION preserves flux | Circular: measures the injected signal, not the model | **Material** |
| D4 | "AGM median 0.11683" (single value) | Correct for D1 only. D5/D6 gains are 2.9–3.9× larger. | **Material** |
| D5 | m_AB ≈ 19.3 / 18.8 and the "Median Flux" table column | Not derivable from the data. Actual median m_AB ≈ 16.1 at SNR 10. Flux column values do not match. | **Material** |
| D6 | C50/C90 = 8.31/13.07 (point), 10.73/18.93 (extended), with no uncertainty | Reproducible with the unweighted LSQ method, but no CIs. MLE gives 8.8/15.4 and 11.2/21.7 with wide CIs. C90 is not empirically established. | **Material** |
| D7 | "100% recovery at SNR ≥ 30σ" | 16/16, 95% lower bound 79–81% | Moderate |
| D8 | Threshold "derived from 90th percentile of clean controls" | median + 3·MAD (floor 150), computed on the same controls used for FPR | Moderate |
| D9 | "Trained on Pointing 0001" | Trained on 0001 + 0002, **D1/D2 only**. 92.7% of trials are on unseen detectors. | Moderate |
| D10 | Per-detector "recovery rate" table | Mixes controls into recoveries. D4 has 5/6 control FPs. Thermal-background explanation unsupported. | Moderate |
| D11 | FITS layout: PRIMARY 2048² image, MASK, QUALITY HDUs | PRIMARY empty; IMAGE/FLAGS/VARIANCE/ZODI/EPSF/WCS-WAVE; 2040² | Moderate |
| D12 | Architecture: 2 conv layers + `Linear(32·8·8, 64)` latent, 32×32 output | 4 strided convs (32→64→128→128 channels, BatchNorm), 128×8×8 latent, 4 transposed convs, 128×128 output | Moderate |
| D13 | Bicubic spline ePSF interpolation | Bilinear. D3 used the superseded v1 ePSF instead of the in-file v2. | Minor |
| D14 | Match radius 12.3″ (2 px) and 5×5 aperture; safe-region "32×32 patch"; "17-pixel radius" | 2.5 / 3.5 px radii; 128×128 patch; 17×17 box (±8 px) | Minor |
| D15 | ePSF FWHM ≈ 1.0 px (6.15″) | Header `PSF_FWHM` = 7.53″ (1.22 px) | Minor |
| D16 | 90th-percentile astrometric error 8.868″ | 10.38″ | Minor |
| D17 | Test names, e.g. `test_manifest_and_results_integrity`, `test_logistic_sigmoid_fitting` | These do not exist. The 11 actual tests are listed in §4.4 / test file. No test covers recovery matching on real model output or completeness on real data. | Minor |
| D18 | Module 768 lines, driver 354 lines | 614 and 685 lines | Minor |
| D19 | "Sub-threshold … zodiacal and 1/f noise" and the "36″ dilution" explanation | No analysis supports these. The FWHM differences are within overlapping Wilson CIs. | Minor |
| D20 | Manifest is "reproducible" | It lacks det_x/det_y, cutout origin and per-trial seed. Reproducibility depends on re-running the driver with seed 42 (verified). | Minor |

Statements **confirmed correct:** checkpoint SHA-256; 423/97/162/164 counts; TP/FP/FN/TN; precision, recall, FPR and F1; Wilson intervals per bin; median and 68% astrometric error; P0003 exclusion from training; exposure time; dimensional form of the shot-noise term; ePSF flux normalisation; catalogue size (1,132 rows); full computational reproducibility.

---

## 8. Recommended corrections

**Report-level (no re-run needed):**

1. Add a dated **erratum banner** to `ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` that links to this audit and lists D1–D20. Do not silently rewrite the original.
2. Replace the AUROC with **0.841 [0.770, 0.895]** (file-cluster bootstrap). Report AUPRC **0.937** together with its **no-skill baseline 0.771** and the prevalence-adjusted table in §2.4.
3. Replace the completeness limits with the trial-level MLE values and cluster-bootstrap CIs (§3.3). Label SNR as **"nominal background-only peak SNR (assumed peak fraction 0.25)"**. State that C90 is model-extrapolated within the sampled range and not empirically demonstrated.
4. Retract the photometric-linearity claim, the m_AB values, the flux table column, the AUROC CI, the architecture and HDU descriptions, and the per-detector table.
5. Always quote C50/C90 **together with the FPR operating point**, and include the §3.4 sensitivity table.

**Code-level (requires a new, separately versioned run; existing outputs must be preserved):**

6. Load **per-detector, per-pixel AGM** from `data/spherex/qr3/calibration/abs_gain_matrix_D{n}_*.fits`.
7. Use the **in-file `EPSF` HDU** (or the matching template version; fixes D3 v1 → v2).
8. Define SNR from the **actual rendered kernel**: report both peak SNR and PSF-matched SNR. Use an empirical local RMS in addition to √VARIANCE. Rename the flux column to `injected_flux_sum_mjy_sr_pix` and add `injected_flux_jy`.
9. Choose τ on a **separate control set** (e.g. a disjoint spatial half of P0003, or another held-out pointing). Report **per-detector τ/FPR**, since D4 is badly mis-calibrated.
10. Sample more finely between 5 and 25σ and use **≥ 50 trials per bin per detector group**, so that C90 can be demonstrated empirically. Draw cutouts **uniformly at random** across each array instead of in raster order up to a cap of 40. Balance across detectors.
11. Fit completeness by **binomial MLE with a false-match floor**, and report cluster-bootstrap CIs automatically.
12. Measure ASTROVISION-based photometry (for example the anomaly-map or residual flux), or drop the photometry figure.
13. Store `det_x`, `det_y`, cutout origin, per-trial RNG state, AGM and ePSF version in the manifest.
14. Strengthen the tests: write and re-read an injected FITS copy (check WCS and headers); test a mask that actually interacts with injection; add a regression test for an exact AUROC on a known toy dataset (to catch the grid-truncation bug); add a test that `recovered_flux` depends on model output.
15. Since ASTROVISION was trained only on D1/D2, either restrict headline claims to D1/D2, or report D3–D6 explicitly as out-of-distribution.

---

## 9. Final scientific acceptance decision

| Criterion | Status |
| :--- | :--- |
| Genuine SPHEREx data, frozen checkpoint, no retraining | ✔ Verified |
| Pointing 0003 excluded from training (no sky overlap) | ✔ Verified |
| Computational reproducibility | ✔ Verified (exact decisions) |
| Core counts and confusion matrix | ✔ Verified |
| Reported AUROC | ✘ Wrong (0.7357 → 0.8406) |
| Threshold independence | ✘ Same controls used for τ and FPR (bias small in expectation; uncertainty understated) |
| Completeness limits with uncertainties | ✘ No CIs; C90 not empirically supported; strongly threshold-dependent |
| Physical noise model | ✘ Wrong gain for D2–D6 (×2.9–3.9 for D5/D6); SNR definition mis-specified |
| Photometric recovery | ✘ Circular; not a model measurement |
| Report accuracy | ✘ Multiple unsupported or fabricated statements (D2, D5, D11, D12, D17) |
| Detector coverage | ⚠ 92.7% of trials on detectors unseen in training; D1 n = 10 |

### Decision: **FAIL**

The benchmark is a genuine, reproducible experiment, and its raw confusion-matrix results are sound. However, **material scientific and statistical problems remain**: an incorrect headline AUROC, a circular photometry claim, a detector-wrong gain in the noise model, uncertainty-free and partly unsupported completeness limits, threshold-selection on the evaluation controls, and several reported values that cannot be traced to any data or code. **P1.1 must not be considered complete.**

**Path to PASS WITH LIMITATIONS:** apply corrections 1–5 (report erratum) together with 6–11 (corrected re-run under a new version tag that does not overwrite the existing outputs). The following limitations would remain and must be stated explicitly: nominal-SNR scale, single pointing (4 exposures), out-of-distribution D3–D6, χ² not a calibrated significance, and prevalence-dependent precision.

### Audit-supported numbers (if quoted before a re-run, these must carry the §8 caveats)

- AUROC **0.841** [0.770, 0.895]; AUPRC **0.937** (baseline 0.771).
- At τ = 169.1: FPR **10.3%** [5.7, 17.9]; precision **94.7%** *at 77% prevalence only*; recall **55.2%** [49.8, 60.5].
- Point C50 **8.8σ** [7.5, 10.1], C90 **15.4σ** [11.4, 21.4]; extended C50 **11.2σ** [8.7, 13.8], C90 **21.7σ** [15.9, 31.3]. All are nominal background-only peak SNR at FPR ≈ 10%, with file-cluster bootstrap 95% CIs.
- Point astrometry (conditional on a 2.5 px prior window): median **0.215 px (1.33″)**, P68 **0.263 px (1.61″)**.

---

## 10. Reproduction commands (read-only)

```powershell
python scratch\audit11_inspect.py          # FITS / checkpoint / ePSF inspection
python scratch\audit11_recompute.py        # all recomputed metrics -> scratch\audit11_out\audit_recomputed_metrics.json
python scratch\audit11_extra.py            # per-detector, background regime, AGM impact
python scratch\audit11_repro_rerun.py      # full benchmark re-run, outputs redirected to scratch\audit11_repro\, protected-file hashes checked
python -m pytest tests\                    # existing suite (22 tests)
```

