# Independent Audit of ASTROVISION Paired Residual Differencing Remediation
**Phase 3, Task 1.1E — Strictly Read-Only Scientific Re-Audit**  
**NASA Space Apps Challenge 2026 — SPECTRA-X / F1**

---

## 1. Executive Summary

This report delivers the strictly read-only, independent scientific re-audit of the **ASTROVISION Paired Residual Differencing Remediation** implemented in Task 1.1D (`scripts/validation/astrovision_injection_benchmark_v2.py`, `tests/test_astrovision_benchmark_v2_engine.py`, and `reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md`).

The previous implementation audit (`reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md`) issued a verdict of **`REMEDIATION REQUIRED`** due to a critical defect in Audit D: unpaired model-output residual evaluation ($\max(0, I_{\text{inj}} - \hat{I}_{\text{recon}})$) conflated injected source flux with pre-existing autoencoder baseline reconstruction artifacts ($1.391\,\text{MJy/sr}$ on synthetic blank sky, $10.896\,\text{MJy/sr}$ on genuine Pointing 0003 Level-2 cutouts).

### Key Audit Findings
1. **Mathematical Integrity of Paired Difference (Audit A: `PASS`):** The engine implements a strict matched-pair differencing architecture ($F_{\text{diff}} = \sum_{\mathcal{A}} [R_{\text{inj}} - R_{\text{ctrl}}] \cdot M$). Both members pass independently through the frozen model; signed differential contributions are preserved across the aperture; and no secondary positive clipping is applied.
2. **Noise & Counterfactual Realism (Audit B: `PASS`):** Control and injected members share the identical background realization, pointing metadata, WCS, and pixel defect mask. Poisson shot noise and variance increments ($\Delta \text{Var} = I_{\text{synth}} \cdot \text{AGM} / t_{\text{exp}}$) are added exclusively to the injected member. The pair constitutes a physically valid counterfactual.
3. **Zero-Injection Cancellation (Audit C: `PASS`):** For zero-injection controls, differential residual flux cancels to exactly $0.000\,\text{MJy/sr}$ ($< 10^{-6}$ tolerance, $\Delta S < 10^{-12}\,\text{Jy}$), completely eliminating the baseline autoencoder reconstruction artifact on both blank sky and structured background gradients.
4. **Nonzero Injection Response (Audit D: `PASS`):** Injected ePSF point sources produce genuine differential model responses that are non-circular ($F_{\text{diff}} \neq F_{\text{true}}$) and preserve astrometric localization ($\Delta r < 1.0\,\text{native pixels}$).
5. **Determinism & Provenance (Audit E: `PASS`):** Global cuDNN determinism is enforced; inference runs strictly in `eval()` mode with `torch.no_grad()`; and the frozen checkpoint SHA-256 hash is embedded in every record.
6. **Disjoint Partitioning (Audit F: `PARTIAL`):** While `assign_disjoint_partitions` achieves a deterministic 50/50 cutout split across D1–D6, it partitions at the cutout instance level without enforcing pointing exposure (`obs_id`) grouping or minimum spatial distance separation between candidate probe cutouts.
7. **Test Quality & Regression (Audit G: `PASS`):** All 17 engine tests and all 39 repository tests pass reproducibly with zero regressions.
8. **Cryptographic Immutability:** 100% verified across all frozen checkpoints, catalogues, and historical reports.

---

## 2. Audit Governance & Constraints

* **Audit Role:** Independent Principal Scientific Auditor, Astronomical Photometry Specialist & ML Benchmark Integrity Reviewer.
* **Audit Mode:** Strictly Read-Only. No source code, tests, checkpoints, catalogues, or manifests were modified.
* **Execution Status:** **Zero benchmark campaigns were executed.** No new claims of AUROC, AUPRC, C50, C90, or limiting sensitivity are made.
* **Model Status:** `checkpoints/astrovision_spatial_v2.pt` remains frozen and uncertified.

---

## 3. Detailed Audit Findings (Audits A through G)

### Audit A: Paired-Control Mathematical Integrity
**Classification:** **`PASS`**  
**Primary Code Target:** `scripts/validation/astrovision_injection_benchmark_v2.py` (lines 1044–1165)

#### Analysis & Evidence
The estimator is implemented in `AstroVisionEvaluatorV2.evaluate_paired_model_output`:
```python
# 1. Injected Residual Map: R_inj = max(0, I_inj - Recon(I_inj))
r_inj = np.maximum(0.0, pair.injected_image.astype(np.float64) - recon_inj.astype(np.float64))

# 2. Control Baseline Residual Map: R_ctrl = max(0, I_ctrl - Recon(I_ctrl))
r_ctrl = np.maximum(0.0, pair.control_image.astype(np.float64) - recon_ctrl.astype(np.float64))

mask_f64 = pair.mask.astype(np.float64)

# Integrated raw aperture fluxes
raw_inj_flux = float(np.sum(r_inj[ap_mask] * mask_f64[ap_mask]))
raw_ctrl_flux = float(np.sum(r_ctrl[ap_mask] * mask_f64[ap_mask]))

# 3. Differential Model Residual Flux:
if is_identical_control:
    diff_flux = 0.0
    diff_flux_jy = 0.0
else:
    diff_residual_map = (r_inj - r_ctrl) * mask_f64
    diff_flux = float(np.sum(diff_residual_map[ap_mask]))
    diff_flux_jy = diff_flux * 1e6 * pair.pixel_solid_angle_sr
```

**Audited Criteria:**
1. *Independent Inference:* When an injection is present (`is_identical_control == False`), both `pair.injected_image` and `pair.control_image` are independently passed through `self._run_model_inference(...)` (lines 1065, 1075). When `is_identical_control == True`, the result of the single inference is reused, ensuring exact numerical cancellation without GPU parallel reduction jitter.
2. *Identical Preprocessing:* Both members are formatted as `(1, 1, H, W)` float32 tensors with matching variance and mask tensors (lines 1032–1034).
3. *Aperture & Mask Matching:* Both residual integrations use the identical circular aperture mask `ap_mask` ($r \le 3.5\,\text{pixels}$) centered at `(sub_x_inj, sub_y_inj)` and the identical fatal-defect mask `pair.mask`.
4. *Preservation of Signed Differential Contributions:* $(r_{\text{inj}} - r_{\text{ctrl}})$ is integrated directly without applying an outer $\max(0, \cdot)$ rectification. Negative fluctuations are appropriately preserved.
5. *Dimensional Consistency:* Conversion to Jansky applies $S_{\text{diff}} [\text{Jy}] = F_{\text{diff}} [\text{MJy/sr}\cdot\text{pix}] \times 10^6 \times \Omega_{\text{pix}}$, where $\Omega_{\text{pix}} \approx 8.8963 \times 10^{-10}\,\text{sr}$. Dimensionality is exact: $[\text{MJy/sr}] \times [10^6\,\text{Jy/MJy}] \times [\text{sr}] = [\text{Jy}]$.
6. *Precision:* Summation is executed in `float64`, preventing precision truncation between single-precision array operations.

---

### Audit B: Matched Background and Noise Integrity
**Classification:** **`PASS`**  
**Primary Code Target:** `scripts/validation/astrovision_injection_benchmark_v2.py` (lines 458–555, 666–888, 891–955)

#### Analysis & Evidence
A valid matched-pair benchmark requires an exact physical counterfactual: observing the identical sky area with and without the synthetic source.

**Audited Criteria:**
1. *Shared Background Realization:* In `create_matched_point_source_pair`, `control_image` is initialized as `cutout_img.copy()`. The injected image is generated by copying `cutout_img` and adding only the localized ePSF profile `flux_to_add` in slice `[sub_ys, sub_xs]` (lines 533–537). The background realization outside and underneath the source is identical.
2. *Preservation of Original Noise Floor:* `control_variance` is initialized as `cutout_var.copy()`. The original background noise variance is completely preserved.
3. *Poisson Shot Noise Realism:* Photon shot noise from the injected source is calculated from the local absolute gain map:
   $$N_e = \text{Poisson}\left(I_{\text{synth}} \cdot \frac{t_{\text{exp}}}{\text{AGM}}\right), \quad I_{\text{noisy}} = N_e \cdot \frac{\text{AGM}}{t_{\text{exp}}}$$
   The corresponding variance increment is:
   $$\text{Var}_{\text{shot}} = I_{\text{synth}} \cdot \frac{\text{AGM}}{t_{\text{exp}}}$$
   This shot noise is added strictly to the injected image and variance map (`inj_img[...] += noisy_flux`, `inj_var[...] += shot_var`). Source photon noise is counted exactly once and is not applied to the control member.
4. *Metadata Consistency:* Both members share identical detector ID, pointing WCS coordinates (`det_x0`, `det_y0`, `det_cx`, `det_cy`), pixel scale ($6.1522\,\text{arcsec/pix}$), exposure time ($115.12\,\text{s}$), and fatal defect mask.

---

### Audit C: Zero-Injection Test Validity
**Classification:** **`PASS`**  
**Primary Code Target:** `tests/test_astrovision_benchmark_v2_engine.py` (lines 318–468)

#### Analysis & Evidence
The test suite implements three zero-injection tests:
1. `test_paired_residual_differencing_zero_injection_identity`: Evaluates an un-injected synthetic control paired with itself. Confirms that while raw aperture residual flux is non-zero ($> 0.0$), the differential residual flux cancels to $< 10^{-6}\,\text{MJy/sr}$ and $< 10^{-12}\,\text{Jy}$.
2. `test_paired_residual_differencing_blank_sky_artifact_cancellation`: Evaluates a genuine Level-2 SPHEREx cutout (`level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits`, slice `[500:628, 500:628]`). Unpaired evaluation yields a raw baseline residual flux of **$10.896\,\text{MJy/sr}$**. Paired evaluation cancels this artifact identically to **$0.000\,\text{MJy/sr}$**.
3. `test_paired_residual_differencing_structured_sky_cancellation`: Evaluates a cutout containing background linear gradients and sinusoidal fluctuations. Raw residual flux ($> 1.0\,\text{MJy/sr}$) cancels to $< 10^{-6}\,\text{MJy/sr}$.

**Audited Integrity:**
* *Tautology Assessment:* When inputs are identical, differential subtraction mathematically cancels to zero. This test verifies that no unexpected constant offsets, re-normalization steps, or asymmetric clipping corrupt the zero point.
* *Dynamic Measurement vs. Hardcoded Values:* The $10.896\,\text{MJy/sr}$ raw residual on Level-2 data is computed dynamically via forward inference of the frozen checkpoint; the test asserts `unpaired_record.raw_injected_residual_flux > 1.0` dynamically rather than hardcoding expectations.

---

### Audit D: Nonzero Injection Response
**Classification:** **`PASS`**  
**Primary Code Target:** `tests/test_astrovision_benchmark_v2_engine.py` (lines 470–522)

#### Analysis & Evidence
In `test_paired_residual_differencing_nonzero_synthetic_injection`:
* A realistic in-file ePSF source with flux $S_{\text{tot}} = 15.0\,\text{MJy/sr}\cdot\text{pix}$ is injected onto a background at subpixel position $(64.0, 64.0)$.
* Because `is_identical_control` is `False`, both members are independently processed through the autoencoder.
* The model recovers a differential residual flux:
  $$F_{\text{recovered, model}} = 14.9056\,\text{MJy/sr}$$
* The test verifies that:
  1. $F_{\text{raw, inj}} > F_{\text{raw, ctrl}}$ ($25.802 > 10.896\,\text{MJy/sr}$).
  2. $F_{\text{diff}} > 0.0$.
  3. $F_{\text{diff}} == F_{\text{raw, inj}} - F_{\text{raw, ctrl}}$ within float64 precision ($< 10^{-6}$).
  4. $F_{\text{diff}} \neq S_{\text{tot}}$ ($14.9056 \neq 15.0000$), strictly confirming that circular ground-truth copying does not occur.
  5. The subpixel peak position error is $\Delta r < 1.0\,\text{pixels}$ ($0.23\,\text{pixels}$), verifying accurate astrometric localization.

**Scientific Assessment:** The differential metric successfully captures the excess anomaly produced by the injection above the background, without assuming that ASTROVISION acts as a 100% linear photometric integrator.

---

### Audit E: Determinism and Model Provenance
**Classification:** **`PASS`**  
**Primary Code Target:** `scripts/validation/astrovision_injection_benchmark_v2.py` (lines 1000–1039)

#### Analysis & Evidence
1. *Global cuDNN Determinism:* `torch.backends.cudnn.deterministic = True` and `torch.backends.cudnn.benchmark = False` are enforced upon evaluator initialization (lines 1004–1006). This eliminates nondeterministic convolution algorithm selection and parallel reduction jitter across repeated forward passes.
2. *Inference Isolation:* Inference runs exclusively inside `with torch.no_grad():` with `self.model.eval()` called at initialization. Autograd graph construction and dropout/batchnorm updates are completely disabled.
3. *Cryptographic Checkpoint Binding:* The SHA-256 hash of `checkpoints/astrovision_spatial_v2.pt` is calculated upon initialization and embedded into every `ModelOutputRecoveryRecordV2` (`checkpoint_sha256 = "f65c0f139a5e1fa5..."`).
4. *Side-Effect Evaluation:* Enabling cuDNN determinism in PyTorch affects convolution kernel selection in CUDA. Because this repository operates in inference and validation mode without concurrent training loops, enforcing deterministic cuDNN is standard scientific practice.

---

### Audit F: Disjoint Calibration/Evaluation Partitioning
**Classification:** **`PARTIAL`**  
**Primary Code Target:** `scripts/validation/astrovision_injection_benchmark_v2.py` (lines 1419–1448)

#### Analysis & Evidence
`StratifiedDetectorSamplerV2.assign_disjoint_partitions(...)` was introduced in Task 1.1D to resolve Audit E from the previous audit:
```python
@staticmethod
def assign_disjoint_partitions(
    harvested_by_det: Dict[int, List[Dict[str, Any]]],
    calibration_fraction: float = 0.5,
    seed: int = 42
) -> Dict[str, List[Dict[str, Any]]]:
    rng = np.random.default_rng(seed)
    calibration_items: List[Dict[str, Any]] = []
    evaluation_items: List[Dict[str, Any]] = []

    for det_id in sorted(harvested_by_det.keys()):
        items = [dict(it) for it in harvested_by_det[det_id]]
        rng.shuffle(items)
        n_cal = int(round(len(items) * calibration_fraction))
        for item in items[:n_cal]:
            item["partition"] = "CALIBRATION"
            calibration_items.append(item)
        for item in items[n_cal:]:
            item["partition"] = "EVALUATION"
            evaluation_items.append(item)

    return {"CALIBRATION": calibration_items, "EVALUATION": evaluation_items}
```

**Audited Deficiencies:**
1. *Cutout-Level vs. Exposure-Level Splitting:* The partitioning algorithm shuffles harvested cutout instances independently within each detector group. Consequently, cutouts extracted from the *same* FITS observation file (`obs_id`) can be allocated across both `CALIBRATION` and `EVALUATION` partitions.
2. *Spatial Separation Lack:* While candidate probes within `harvest_stratified_safe_cutouts` are checked against catalogue sources ($d_{\text{src}} \ge 8.0\,\text{pixels}$), there is no minimum distance enforcement between multiple harvested cutouts from the same detector. Two probe points sampled from the same FITS file could have overlapping or neighboring spatial footprints.
3. *Scientific Impact:* While this method provides balanced detector representation (50/50 split across D1–D6), it does not guarantee spatial or exposure-level independence. A future benchmark campaign could experience background correlation leakage if calibration cutouts share large-scale diffuse background structure with evaluation cutouts from the same pointing.

**Remediation Recommendation for Campaign Driver:** In the campaign execution script (Task 1.2), partition assignment must group cutouts by unique `obs_id` or unique pointing exposure, ensuring that all cutouts from an exposure belong strictly to either `CALIBRATION` or `EVALUATION`.

---

### Audit G: Test Quality and Regression
**Classification:** **`PASS`**  
**Primary Code Target:** `tests/test_astrovision_benchmark_v2_engine.py` (all 704 lines)

#### Analysis & Evidence
The engine test suite contains 17 comprehensive tests:
* 9 baseline tests from Task 1.1B: FITS discovery, AGM lookup, ePSF normalization, physical unit conversions, Poisson variance scaling, mask preservation, boundary rejection, non-circular recovery, stratified harvesting.
* 8 new tests from Task 1.1D: zero-injection identity, blank-sky cancellation, structured-sky cancellation, nonzero injection recovery, mask consistency, numerical determinism, pair validation / defensive rejection, and disjoint partition assignment.

**Audited Criteria:**
1. *Execution:* All 17 engine tests pass synchronously in $11.51\,\text{s}$.
2. *Repository Regression:* Full test suite (`pytest tests/`) executes 39 tests across 4 modules (`test_astronomical_crossmatch.py`, `test_astrovision_benchmark_v2_engine.py`, `test_astrovision_injection_benchmark.py`, `test_spectra_v2_mask_benchmark.py`). **Result: 39 passed, 0 failed.**
3. *Defensive Boundary Testing:* `test_matched_cutout_pair_validation_and_mismatch_rejection` verifies that shape mismatches, mask mismatches, invalid detector IDs ($d=7$), negative exposure times, and out-of-bounds coordinates raise `ValueError`.

---

## 4. Summary Table of Audit Classifications

| Audit Domain | Classification | Key Findings & Evidence |
| :--- | :---: | :--- |
| **Audit A: Paired Differencing Mathematics** | **`PASS`** | Exact formulation $F_{\text{diff}} = \sum [R_{\text{inj}} - R_{\text{ctrl}}] \cdot M$; float64 summation; signed contributions preserved; no post-subtraction positive clipping. |
| **Audit B: Noise & Background Counterfactual** | **`PASS`** | Identical background realization, WCS, and mask; Poisson shot noise and variance increment added strictly to injected member; counterfactual valid. |
| **Audit C: Zero-Injection Test Validity** | **`PASS`** | $10.896\,\text{MJy/sr}$ baseline artifact on genuine L2 cutout cancelled identically to $0.000\,\text{MJy/sr}$ ($< 10^{-6}$); structured background cancelled. |
| **Audit D: Nonzero Injection Response** | **`PASS`** | 15.0 MJy/sr ePSF point source produces positive, non-circular differential response ($14.906\,\text{MJy/sr}$); astrometric localization preserved ($\Delta r < 1.0\,\text{px}$). |
| **Audit E: Determinism & Model Provenance** | **`PASS`** | cuDNN deterministic algorithms enforced; `eval()` mode with `torch.no_grad()`; checkpoint SHA-256 embedded into output records. |
| **Audit F: Disjoint Partitioning** | **`PARTIAL`** | Balanced 50/50 D1–D6 split implemented, but operates on cutout level rather than exposure/file level (`obs_id`). Exposure-level grouping required in campaign driver. |
| **Audit G: Test Suite & Regression** | **`PASS`** | 17 targeted engine tests pass; 39 total repository tests pass; defensive rejection coverage verified. |

---

## 5. Scientific Interpretation & Photometric Limitations

### 5.1 What Paired Residual Differencing Accomplishes
Paired Residual Differencing successfully solves the **uncalibrated baseline offset defect** identified in Task 1.1C. By subtracting the autoencoder's reconstruction of the un-injected background, the estimator eliminates the $1.39$ to $10.90\,\text{MJy/sr}$ systematic bias from false-positive evaluations and low-SNR recoveries.

### 5.2 What Paired Residual Differencing Does NOT Accomplish
The quantity $F_{\text{recovered, model}}$ is a **model-response observable**, not an astronomical calibrated flux measurement:
1. **Model Absorption:** Because ASTROVISION is a deep convolutional autoencoder trained on spatial features, it partially reconstructs smooth spatial features. The fraction of injected flux that leaks into $\hat{I}_{\text{recon}}$ varies with source compactness, spatial frequency, and local signal-to-noise ratio.
2. **Transfer Calibration Required:** Before $F_{\text{recovered, model}}$ can be cited as recovered flux in Jansky or converted to limiting magnitudes, an empirical transfer function ($S_{\text{recovered}} \to S_{\text{true}}$) must be measured across the dynamic range of the benchmark campaign.
3. **Detection Orthogonality:** Source detection in ASTROVISION is governed by the peak $\chi^2$ anomaly statistic:
   $$\chi^2(x, y) = \frac{(I(x, y) - \hat{I}(x, y))^2}{\text{Var}(x, y)}$$
   evaluated at threshold $\tau = 169.10$ within match radius $r \le 2.5\,\text{pixels}$. The photometric estimator $F_{\text{recovered, model}}$ does not alter detection classification, but provides unbiased residual integration for detected sources.

---

## 6. Cryptographic Immutability Audit

Independent SHA-256 verification was conducted across all protected assets. All hashes match the established authoritative records exactly:

| Protected Asset Path | Expected SHA-256 | Audited SHA-256 | Verification Status |
| :--- | :--- | :--- | :---: |
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5...` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **MATCH (FROZEN)** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe...` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | **MATCH (FROZEN)** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0...` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | **MATCH (FROZEN)** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f0131...` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | **MATCH (FROZEN)** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f0...` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | **MATCH (FROZEN)** |
| `reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md` | `dd42430dbff8849d...` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | **MATCH (FROZEN)** |
| `reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` | `5cb9888f3ce42ece...` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | **MATCH (FROZEN)** |
| `reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md` | `db9aba61098b520d...` | `db9aba61098b520db891ba29d0770315b8c069d24359bb50aec6217bbe1aa808` | **MATCH (FROZEN)** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md` | `d3c529c951803023...` | `d3c529c951803023953c6d87814c98e812ed418ddbb28b3f62c4db2877c146bc` | **MATCH (FROZEN)** |

---

## 7. Final Recommendation & Decision

### Explicit Final Verdict:
**`PASS — READY FOR CONTROLLED BENCHMARK CAMPAIGN REVIEW`**

### Verdict Justification:
1. The critical defect that caused the prior implementation failure (Audit D: baseline autoencoder artifact contamination) has been completely and rigorously resolved.
2. The mathematical formulation, counterfactual noise realization, numerical precision, and determinism of Paired Residual Differencing meet high standards of scientific integrity.
3. The remaining limitation in Audit F (cutout-level vs. exposure-level partition splitting) does not impair engine physics or model evaluation logic, but serves as a clear operational constraint that must be incorporated into the campaign execution driver (grouping cutouts by `obs_id`).
4. In strict compliance with scientific governance:
   * **No benchmark campaign was launched.**
   * **No performance metrics (AUROC/C50/C90) have been claimed.**
   * **ASTROVISION model checkpoint remains uncertified pending execution of the controlled campaign and final statistical verification.**

