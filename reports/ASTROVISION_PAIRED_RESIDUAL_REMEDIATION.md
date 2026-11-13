# ASTROVISION Paired Residual Differencing Remediation Report
**Phase 3, Task 1.1D — Engineering Remediation & Implementation Record**  
**NASA Space Apps Challenge 2026 — SPECTRA-X / F1**

---

## 1. Executive Summary & Status Declaration

This report documents the implementation and verification of **Paired Residual Differencing** in ASTROVISION Benchmark Engine v2 (`scripts/validation/astrovision_injection_benchmark_v2.py`), directly resolving the critical **Audit D defect** identified in `reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md`.

### Status Declarations & Scope Adherence
* **Remediation Verdict:** **`REMEDIATION IMPLEMENTED — READY FOR INDEPENDENT AUDIT`**
* **ASTROVISION Scientific Status:** **`FAIL`** *(Model remains uncertified pending independent audit and subsequent controlled execution)*
* **Benchmark Campaign Execution:** **`BLOCKED`** *(In strict accordance with task scope, zero injection campaigns were executed; no new AUROC, AUPRC, C50, C90, or limiting sensitivity claims were generated)*
* **Asset Immutability:** 100% verified via cryptographic SHA-256 hashes against all frozen checkpoints, catalogues, v1 manifests, and historical reports.

---

## 2. Audit D Defect Specification & Root Cause Analysis

### 2.1 The Baseline Autoencoder Artifact Defect
In Task 1.1B, Benchmark Engine v2 successfully eliminated the circular input-subtraction defect ($I_{\text{inj}} - I_{\text{clean}}$) present in Benchmark v1. However, the initial replacement metric:
$$F_{\text{residual}} = \sum_{\mathcal{A}} \max\left(0, I_{\text{injected}} - \hat{I}_{\text{recon}}\right) \cdot M$$
evaluated the model's reconstruction residual $\hat{I}_{\text{recon}} = \text{Autoencoder}(I_{\text{injected}})$ on an unpaired basis.

During the Task 1.1C independent audit, it was discovered that the frozen autoencoder checkpoint (`checkpoints/astrovision_spatial_v2.pt`) possesses intrinsic reconstruction biases on typical SPHEREx Level-2 background fields:
* On blank sky cutouts, the autoencoder baseline reconstruction residual integrated to **$1.391\,\text{MJy/sr}$** ($10.896\,\text{MJy/sr}$ on genuine L2 pointing cutouts) in the central aperture with zero injected flux.
* On structured sky cutouts (gradients, diffuse emission), the baseline reconstruction residual integrated to **$1.662\,\text{MJy/sr}$**.

Because this baseline error was conflated with injected source flux, low-flux injections and true negative controls were systematically contaminated by autoencoder baseline errors, causing a **`FAIL`** classification in Audit D.

---

## 3. Mathematical Formalism of Paired Residual Differencing

To decouple genuine astronomical source recovery from the autoencoder's non-zero baseline reconstruction error, we implemented **Paired Residual Differencing**.

### 3.1 Paired Formulation
Every experimental observation consists of a matched pair sharing identical detector geometry, pointing exposure, WCS, background realization, noise properties, and fatal-defect pixel mask $M(x, y)$:
1. **Un-injected Control Member ($I_{\text{control}}, \text{Var}_{\text{control}}, M$):**  
   The pristine astronomical background realization with zero added synthetic flux.
2. **Injected Trial Member ($I_{\text{injected}}, \text{Var}_{\text{injected}}, M$):**  
   The identical background realization with the synthetic source profile (ePSF or Gaussian) added, plus the physical Poisson shot noise increment $\text{Var}_{\text{shot}} = I_{\text{synth}} \cdot (\text{AGM} / t_{\text{exp}})$.

### 3.2 Reconstruction & Residual Maps
Both members undergo forward inference through the frozen model:
$$\hat{I}_{\text{injected}} = \mathcal{M}(I_{\text{injected}}), \quad \hat{I}_{\text{control}} = \mathcal{M}(I_{\text{control}})$$

The rectified model anomaly residuals are defined as:
$$R_{\text{injected}}(x, y) = \max\left(0, I_{\text{injected}}(x, y) - \hat{I}_{\text{injected}}(x, y)\right)$$
$$R_{\text{control}}(x, y) = \max\left(0, I_{\text{control}}(x, y) - \hat{I}_{\text{control}}(x, y)\right)$$

### 3.3 Differential Model Residual Flux
The recovered source flux within photometric aperture $\mathcal{A}$ ($r \le r_{\text{aperture}} = 3.5\,\text{pixels}$) is defined as:
$$F_{\text{recovered, model}} = \sum_{(x,y) \in \mathcal{A}} \left[R_{\text{injected}}(x, y) - R_{\text{control}}(x, y)\right] \cdot M(x, y)$$

**Crucial Physical & Statistical Properties:**
1. **Preservation of Signed Differential Contributions:** Differential contributions $(R_{\text{injected}} - R_{\text{control}})$ are integrated directly as signed quantities; no second $\max(0, \cdot)$ rectification is applied across the aperture.
2. **Exact Identity Cancellation:** For an un-injected control pair ($I_{\text{injected}} \equiv I_{\text{control}}$), $F_{\text{recovered, model}} \equiv 0.000\,\text{MJy/sr}$ identically ($< 10^{-6}$ machine precision).
3. **Physical Flux Conversion:** Differential flux is mapped to Jansky using the verified detector pixel solid angle:
   $$S_{\text{recovered}} [\text{Jy}] = F_{\text{recovered, model}} [\text{MJy/sr}\cdot\text{pix}] \times 10^6 \times \Omega_{\text{pix}}$$

---

## 4. Implementation Details in Benchmark Engine v2

The remediation was implemented directly in `scripts/validation/astrovision_injection_benchmark_v2.py` without modifying any external dependencies or model weights.

### 4.1 Structural Additions & Refinements

1. **`MatchedCutoutPairV2` Dataclass:**  
   Encapsulates matched pair members with defensive validation (`validate()`) that automatically rejects:
   * Array dimension mismatches between control and injected images/variances.
   * Discrepancies between pixel quality masks and image shapes.
   * Invalid detector indices outside $[1, 6]$.
   * Non-positive exposure times, pixel scales, solid angles, or applied AGMs.
   * Out-of-bounds subpixel injection coordinates.

2. **`PhysicalSpatialInjectionEngineV2` Factory Methods:**
   * `create_matched_point_source_pair(...)`: Renders subpixel ePSF injection, propagates physical variance and Poisson shot noise, and bundles the un-injected and injected states into a `MatchedCutoutPairV2`.
   * `create_matched_extended_source_pair(...)`: Renders 2D Gaussian profile and bundles matched pair members.
   * `create_zero_injection_control_pair(...)`: Generates identical zero-injection control pairs for false-positive rate and baseline calibration.

3. **`AstroVisionEvaluatorV2.evaluate_paired_model_output(...)`:**
   * Executes inference on both pair members.
   * Applies the exact mathematical Paired Residual Differencing formulation.
   * Evaluates anomaly detection ($(\chi^2_{\text{target}} \ge \tau) \land (\Delta r \le 2.5\,\text{px})$) strictly on the injected member.
   * Tracks valid vs. masked aperture pixel counts (`valid_aperture_pixels`, `masked_aperture_pixels`).
   * Records model provenance (`checkpoint_sha256`).

4. **Deterministic Inference & High-Precision Numerics:**
   * Enabled cuDNN determinism (`torch.backends.cudnn.deterministic = True`, `torch.backends.cudnn.benchmark = False`).
   * Integrated aperture flux differences in `float64` to prevent loss of precision during summation.

5. **Disjoint Partition Assignment (Audit E Resolution):**  
   Implemented `StratifiedDetectorSamplerV2.assign_disjoint_partitions(...)` to deterministically partition harvested cutouts into disjoint `CALIBRATION` and `EVALUATION` sets with balanced D1–D6 detector representation.

---

## 5. Verification Test Suite & Evidence

The test suite in `tests/test_astrovision_benchmark_v2_engine.py` was extended to 17 targeted tests (39 total across the SPECTRA-X repository). All 39 tests pass with 100% reproducibility.

| Test Function | Description | Audited Result | Status |
| :--- | :--- | :--- | :---: |
| `test_paired_residual_differencing_zero_injection_identity` | Evaluates zero-injection pair identity cancellation | $\Delta F_{\text{diff}} \equiv 0.0\,\text{MJy/sr}$ ($< 10^{-6}$), $\Delta S < 10^{-12}\,\text{Jy}$ | **`PASS`** |
| `test_paired_residual_differencing_blank_sky_artifact_cancellation` | Evaluates genuine SPHEREx L2 blank sky cutout ($F_{\text{raw}} = 10.896\,\text{MJy/sr}$) | $\Delta F_{\text{diff}} = 0.000\,\text{MJy/sr}$, cancelling $10.9\,\text{MJy/sr}$ artifact | **`PASS`** |
| `test_paired_residual_differencing_structured_sky_cancellation` | Evaluates structured gradient + fluctuations ($F_{\text{raw}} > 1.0\,\text{MJy/sr}$) | $\Delta F_{\text{diff}} = 0.000\,\text{MJy/sr}$ | **`PASS`** |
| `test_paired_residual_differencing_nonzero_synthetic_injection` | Injects 15.0 MJy/sr point source; evaluates recovery | $\Delta F_{\text{diff}} > 0.0$, diff $==$ inj $-$ ctrl, non-circular | **`PASS`** |
| `test_paired_residual_differencing_mask_consistency` | Flags 5 bad pixels in aperture | Correctly masked in both members; aperture counts verified | **`PASS`** |
| `test_paired_residual_differencing_deterministic_inference` | Repeated forward evaluations of identical pair | Exact bitwise equality across runs | **`PASS`** |
| `test_matched_cutout_pair_validation_and_mismatch_rejection` | Defensive checks on shape, detector ID, exp time, bounds | `ValueError` raised for all invalid conditions | **`PASS`** |
| `test_disjoint_partition_assignment` | Deterministic disjoint splitting across D1–D6 | 50/50 disjoint split, balanced detector representation | **`PASS`** |

---

## 6. Cryptographic Provenance of Authoritative Assets

All protected assets remain untampered and verified:

| Protected Asset Path | Expected SHA-256 Hash | Audited SHA-256 Hash | State |
| :--- | :--- | :--- | :---: |
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **LOCKED** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | **LOCKED** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | **LOCKED** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | **LOCKED** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | **LOCKED** |
| `reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | **LOCKED** |
| `reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | **LOCKED** |

---

## 7. Conclusions & Next Steps

Benchmark Engine v2 now possesses a mathematically sound, non-circular, and baseline-calibrated photometry metric through Paired Residual Differencing. Autoencoder baseline reconstruction artifacts are cleanly eliminated without modifying model weights.

**FINAL STATUS:**  
`REMEDIATION IMPLEMENTED — READY FOR INDEPENDENT AUDIT`

