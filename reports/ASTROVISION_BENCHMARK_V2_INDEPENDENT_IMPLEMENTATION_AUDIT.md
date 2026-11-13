# SPECTRA-X / F1 — PHASE 3, TASK 1.1C: INDEPENDENT IMPLEMENTATION AUDIT REPORT
## Independent ASTROVISION Benchmark v2 Engine Implementation & Physical Integrity Audit

**Audit Role:** Independent Principal Scientific Auditor, Astronomical Detector Calibration Specialist & ML Benchmark Verification Engineer  
**Audit Date:** 2026-11-06  
**Audit Type:** **READ-ONLY IMPLEMENTATION AUDIT**  
**Target Implementation:** [`scripts/validation/astrovision_injection_benchmark_v2.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validation/astrovision_injection_benchmark_v2.py) (SHA-256: `c7914dd4feba9324361bb59eb596b61a59b589d50e58085061e4bab92ebbbc6d`)  
**Primary Report Audited:** [`reports/ASTROVISION_BENCHMARK_V2_ENGINE_IMPLEMENTATION.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/ASTROVISION_BENCHMARK_V2_ENGINE_IMPLEMENTATION.md)  
**Target Checkpoint:** [`checkpoints/astrovision_spatial_v2.pt`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/checkpoints/astrovision_spatial_v2.pt) (SHA-256: `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557`)

---

> [!CAUTION]
> ## EXECUTIVE AUDIT VERDICT & FINAL RECOMMENDATION
> **Implementation Audit Verdict:** **`REMEDIATION REQUIRED`**  
> **ASTROVISION Model Scientific Status:** **`FAIL` (Validation Not Passed — Scientific Anomaly Detection Uncertified)**  
> 
> **EXECUTIVE SUMMARY:**  
> Benchmark Engine v2 successfully resolves **five major historical defects**: (1) it correctly maps 2D pixel-level detector gain across all detectors D1–D6, (2) prioritizes in-file ePSFs, (3) validates authoritative 7-HDU FITS structures, (4) enforces exact subpixel flux conservation, and (5) eliminates the circular input image subtraction `injected_image - original_image`.
> 
> **CRITICAL DEFECT IDENTIFIED (AUDIT D):**  
> Despite removing circular input subtraction, the replacement model-recovery metric:
> $$F_{\text{model\_residual}} = \sum_{r \le 3.5} \max\left(0, I_{\text{injected}} - \hat{I}_{\text{reconstruction}}\right) \cdot M$$
> is **scientifically invalid for uncalibrated autoencoders**. Independent empirical testing reveals that un-injected pristine clean cutouts produce a baseline artifact flux of **$1.391\,\text{MJy/sr}$** ($1.662\,\text{MJy/sr}$ on structured sky) simply due to non-zero baseline reconstruction residuals. In faint injection regimes ($S \le 1.0\,\text{MJy/sr}$), **$100\%$ of the measured "recovered flux" is dominated by pre-existing autoencoder reconstruction error rather than the injected astronomical source**.
> 
> **CAMPAIGN RECOMMENDATION:** **`REMEDIATION REQUIRED`** (A controlled validation campaign cannot be executed until Audit D is remediated via paired control differencing).

---

## 1. Audit Scope & Repository Integrity Baseline

In strict accordance with read-only preservation rules:
- No source files, checkpoints, FITS observations, catalogues, or manifests were altered.
- All numerical verifications were conducted in read-only python sessions without modifying disk state.
- Pre-audit and post-audit cryptographic SHA-256 hashes of all 11 core repository assets were verified identical:

| Repository File | Verified SHA-256 Hash | Integrity Status |
| :--- | :--- | :---: |
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **UNMODIFIED / FROZEN** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | **UNMODIFIED / LOCKED** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | **UNMODIFIED (v1)** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | **UNMODIFIED (v1)** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | **UNMODIFIED (v1)** |
| `reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | **UNMODIFIED (Audit v1)** |
| `reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | **UNMODIFIED (v1 Erratum)** |
| `scripts/validation/astrovision_injection_benchmark.py` | `d269cdf4c61164ec7ab3f0d3ffe69b01443df5fffbf966d84a1c4e3463dd63b9` | **UNMODIFIED (v1)** |
| `scripts/validation/run_astrovision_injection_benchmark.py` | `b5a1ce585dfba218c5b05bd905d896a6a4ad6dfe15defd7e5ed4063371eb98f0` | **UNMODIFIED (v1)** |
| `scripts/validation/astrovision_injection_benchmark_v2.py` | `c7914dd4feba9324361bb59eb596b61a59b589d50e58085061e4bab92ebbbc6d` | **TARGET AUDITED** |
| `tests/test_astrovision_benchmark_v2_engine.py` | `5245f41e6ccd4cbbfbfea56a607b5cd6a95dfb582a9e2eb2a093c581acc09602` | **TARGET AUDITED** |

---

## 2. Comprehensive Area-by-Area Audit Findings

### Audit A — Detector Gain Calibration: **`PASS`**
1. **Authoritative File Mapping:** Verified that `AbsoluteGainProviderV2` queries `data/spherex/qr3/calibration/abs_gain_matrix_D{detector_id}_*.fits`. All 6 detector gain files (D1–D6) exist and map cleanly.
2. **HDU & Unit Integrity:** Verified that each gain file contains an HDU 1 named `IMAGE` of dimensions `(2040, 2040)` with `BUNIT = 'MJy s / (electron sr)'`.
3. **Data Fidelity & Pixel Sampling:** Sampled coordinates `(100, 100)`, `(500, 1020)`, `(1020, 500)`, `(1500, 1800)`, and `(2039, 2039)` across all 6 detectors. Provider output matches raw FITS data down to float precision ($< 10^{-7}$).
4. **Coordinate Mapping & Safe Fallbacks:** 
   - Row-major numpy indexing `(y_pix, x_pix)` is strictly preserved across `get_pixel_gain` and `get_patch_gain`.
   - Verified that non-positive / NaN pixels (e.g., pixel `(54, 1684)` in D1 where raw gain is $-1.3831$) correctly fall back to the detector median ($0.11683$), preventing negative variance bugs.
   - Out-of-bounds coordinates fall back to the detector's own median, **never falling back to universal D1 gain**.
5. **Provenance:** Each record tracks `applied_agm_median` and `applied_agm_bunit`.

---

### Audit B — In-File ePSF and Flux Conservation: **`PASS`**
1. **In-File HDU Prioritization:** Verified that `InFilePSFProviderV2` extracts HDU 5 (`EPSF`) directly from the input Level-2 FITS file.
2. **Resolution of Detector 3 Mismatch:** Verified that for Detector 3 (where science files carry the 451-bin v2 model), `get_psf_model_for_file` extracts all 451 spatial bins directly from the in-file table.
3. **Flux Conservation in Actual Injection:** In `inject_point_source` and `inject_extended_source`, subpixel kernel evaluation enforces:
   $$\sum \Delta I_{\text{kernel}} = S_{\text{tot}}$$
   Independent numerical verification confirms $\left|\sum \Delta I - S_{\text{tot}}\right| / S_{\text{tot}} < 10^{-6}$ across subpixel fractional offsets.
4. **Physical Flux Scaling:** Correctly tracks integrated surface brightness sum ($\text{MJy/sr}\cdot\text{pix}$) and converts to absolute flux density in Jansky:
   $$F_{\nu}\text{ [Jy]} = S_{\text{tot}}\text{ [MJy/sr}\cdot\text{pix]} \times 10^6 \times \Omega_{\text{pix}}$$
   where $\Omega_{\text{pix}} \approx 8.8963 \times 10^{-10}\,\text{sr}$.

---

### Audit C — Physical Noise & Variance Propagation: **`PASS`**
1. **Mathematical Formulation:** Independent derivation of `PhysicalSpatialInjectionEngineV2` verifies:
   - Electron rate coupling: $\mu_e(x, y) = \Delta I(x, y) \cdot \frac{t_{\text{exp}}}{\text{AGM}(x, y)}$ [electrons]
   - Injected shot noise variance: $\text{Var}_{\text{shot}}(x, y) = \Delta I(x, y) \cdot \frac{\text{AGM}(x, y)}{t_{\text{exp}}}$ [$\text{MJy}^2/\text{sr}^2$]
   - Dimensional consistency: $[(\text{MJy/sr}) \times (\text{MJy}\cdot\text{s}/(\text{e}^-\cdot\text{sr})) / \text{s}] = \text{MJy}^2/\text{sr}^2$.
2. **Detector-Specific Noise Scaling:** Verified that for Detector 6 (MWIR), injected photon shot noise variance scales with $\text{AGM} \approx 0.458$, matching true detector Poisson statistics ($3.9\times$ higher variance than D1).
3. **No Double-Counting:** The existing background variance $\text{Var}_{\text{orig}}$ is preserved and accumulated additively: $\text{Var}_{\text{new}} = \text{Var}_{\text{orig}} + \text{Var}_{\text{shot}}$.
4. **Boundary Margin Protection:** Injections centered within $6\text{ px}$ of the cutout boundary (or whose extended profile exceeds the boundary) are rejected with a recorded `rejection_reason`.

---

### Audit D — Actual ASTROVISION Model-Output Recovery: **`FAIL`**
1. **Elimination of Circular Subtraction:** Verified that `injected_image - original_image` has been removed.
2. **Inference Execution:** Verified that `AstroVisionEvaluatorV2` loads the frozen checkpoint `checkpoints/astrovision_spatial_v2.pt` and evaluates the model in `eval()` mode.
3. **Detection Metric Formulation:** Subpixel peak finding on the model's normalized $\chi^2$ anomaly map is mathematically sound.
4. **CRITICAL SCIENTIFIC DEFECT in `model_residual_flux_mjy_sr`:**
   In line 586 of `astrovision_injection_benchmark_v2.py`:
   $$\text{model\_residual} = \max\left(0, I_{\text{injected}} - \hat{I}_{\text{recon}}\right) \cdot M$$
   $$F_{\text{model\_residual}} = \sum_{r \le 3.5} \text{model\_residual}(x, y)$$
   
   **Independent Empirical Test on Pristine Uninjected Controls:**
   - On a pristine, unperturbed background cutout with **zero injection** ($S_{\text{inj}} = 0.0$), the model reconstruction does not perfectly match the background ($I_{\text{bg}} = 0.25$, but $\hat{I}_{\text{recon}} \approx 0.21$).
   - The evaluator outputs:
     $$F_{\text{model\_residual}}(\text{Zero Injection Control}) = \mathbf{1.391\,\text{MJy/sr}}$$
   - On realistic structured background sky with zero injection:
     $$F_{\text{model\_residual}}(\text{Zero Injection Control}) = \mathbf{1.662\,\text{MJy/sr}}$$
   
   **Scientific Impact:**  
   Because ASTROVISION is an uncalibrated autoencoder with a non-zero baseline reconstruction error, $\max(0, I - \hat{I})$ captures pre-existing baseline residuals. For faint sources ($S \le 1.0\,\text{MJy/sr}$), the measured "recovered flux" is dominated by pre-existing model baseline error. This will produce an artificial non-zero flux floor and distort linearity curves.
   
   **Required Remediation:**  
   To measure true injected source flux recovery from the model, the engine must employ **Paired Residual Differencing**:
   $$F_{\text{recovered, model}} = \sum_{r \le 3.5} \left[\left(I_{\text{injected}} - \hat{I}_{\text{injected}}\right) - \left(I_{\text{control}} - \hat{I}_{\text{control}}\right)\right] \cdot M$$
   This subtracts the baseline reconstruction artifact of the pristine cutout, isolating the model's actual response to the injected astronomical source.

---

### Audit E — Calibration/Evaluation Partition Leakage: **`PARTIAL`**
1. **Partition Tagging:** Dataclass schemas (`InjectionRecordV2` and `ModelOutputRecoveryRecordV2`) support explicit partition tags (`CALIBRATION_CONTROL`, `EVALUATION_CONTROL`, `POINT_SOURCE_INJECTION`, `EXTENDED_SOURCE_INJECTION`).
2. **Defect / Omission in Engine Implementation:**
   - `astrovision_injection_benchmark_v2.py` provides the data containers, but **does not implement an automated partition splitting mechanism**.
   - `StratifiedDetectorSamplerV2` harvests a flat list of cutouts per detector without assigning them to calibration vs. evaluation holdout sets.
   - Partition assignment is left to the caller/driver script. To ensure leakage cannot occur, an automated, deterministic spatial-partitioning routine must be embedded directly in the engine.

---

### Audit F — Detector-Stratified Sampling Mechanics: **`PASS`**
1. **Focal Plane Uniformity:** Verified that `StratifiedDetectorSamplerV2` generates uniform random probes across the entire $2040 \times 2040$ focal plane, eliminating the raster-scan bias of v1.
2. **Target Quotas:** Supports balanced quotas per detector across D1–D6.
3. **Data Availability Limitation:**
   - Pointing 0003 contains only **4 science FITS files for Detector 1** (`1D1`, `2D1`, `3D1`, `4D1`).
   - If a benchmark campaign requests $\ge 50$ safe, isolated cutouts for D1, the sampler may yield fewer cutouts for D1 than for MWIR detectors (which have 4 files with higher clean-sky fractions). The engine correctly logs this warning.

---

### Audit G — Test Suite & Regression Quality: **`PASS`**
1. **Coverage of Audited Defects:** The 9 unit tests in [`tests/test_astrovision_benchmark_v2_engine.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/tests/test_astrovision_benchmark_v2_engine.py) directly test:
   - Benchmark v1 immutability (`test_benchmark_v1_immutability`)
   - FITS 7-HDU schema validation (`test_fits_hdu_discovery_and_validation`)
   - D1–D6 detector gain maps (`test_detector_specific_gain_selection`)
   - In-file ePSF extraction and flux conservation (`test_infile_epsf_prioritization_and_flux_conservation`)
   - Physical photon variance scaling on MWIR detectors (`test_physical_variance_propagation_with_true_agm`)
   - Physical flux unit conversions to Jansky (`test_physical_unit_conversions`)
   - Cutout boundary rejection (`test_injection_boundary_rejection`)
   - Model-output recovery interface execution (`test_actual_model_output_recovery_interface`)
   - Detector-stratified sampling mechanics (`test_stratified_detector_sampling_mechanics`)
2. **Execution & Regression Integrity:** Full pytest run confirms all 31 repository tests pass in $6.95\text{ s}$ without regressions.

---

## 3. Summary of Audit Classifications

| Audit Domain | Classification | Primary Evidence & Finding |
| :--- | :---: | :--- |
| **Audit A: Detector Gain Calibration** | **`PASS`** | 2D pixel-level AGM lookup verified across D1–D6; zero fallback to D1 gain; safe fallback on non-positive pixels. |
| **Audit B: ePSF & Flux Conservation** | **`PASS`** | In-file HDU 5 priority enforced; exact flux conservation verified ($< 10^{-6}$); physical Jy conversion verified. |
| **Audit C: Noise & Variance Propagation** | **`PASS`** | Dimensional consistency verified; MWIR D5/D6 variance scales with true physical gain; boundary rejection verified. |
| **Audit D: Model-Output Recovery** | **`FAIL`** | Circular input subtraction removed, but replacement metric $\max(0, I_{\text{inj}} - \hat{I}_{\text{recon}})$ is contaminated by baseline autoencoder artifacts ($1.39\,\text{MJy/sr}$ on blank sky). Paired control differencing required. |
| **Audit E: Calibration/Evaluation Leakage** | **`PARTIAL`** | Schema supports partition tags, but automated partition assignment is not embedded in the engine module. |
| **Audit F: Detector-Stratified Sampling** | **`PASS`** | Uniform spatial probing across array replaces raster-order scanning; balanced quotas supported across D1–D6. |
| **Audit G: Test Suite & Regression** | **`PASS`** | All 9 engine tests verify scientific assertions; full 31-test repository suite passes; v1 assets 100% frozen. |

---

## 4. Remediation Requirements Prior to Campaign Execution

Before launching a full validation campaign under Phase 3 Task 1.2:
1. **Remediate Model-Output Photometry (Audit D):**  
   Update `evaluate_model_output` in `astrovision_injection_benchmark_v2.py` to accept the corresponding un-injected control cutout $(I_{\text{ctrl}}, \text{Var}_{\text{ctrl}})$, compute its model reconstruction residual $(I_{\text{ctrl}} - \hat{I}_{\text{ctrl}})$, and define recovered source flux via Paired Residual Differencing:
   $$F_{\text{recovered, model}} = \sum_{r \le r_{\text{aperture}}} \left[\max\left(0, I_{\text{injected}} - \hat{I}_{\text{injected}}\right) - \max\left(0, I_{\text{ctrl}} - \hat{I}_{\text{ctrl}}\right)\right] \cdot M$$
   This ensures that un-injected sky evaluates to exactly $0.0\,\text{MJy/sr}$ expected flux.
2. **Embed Deterministic Partition Splitting (Audit E):**  
   Add an automated method `assign_disjoint_partitions(harvested_cutouts, calibration_fraction=0.5, seed=42)` in `StratifiedDetectorSamplerV2` that enforces strict spatial or exposure-based partitioning prior to any threshold fitting.

---

## 5. Final Recommendation & Decision

**FINAL AUDIT RECOMMENDATION:** **`REMEDIATION REQUIRED`**

Benchmark Engine v2 represents major physical progress over v1, correctly implementing detector gain physics and in-file ePSFs. However, because its model-output flux metric is confounded by baseline autoencoder artifacts, it is **not yet ready for a controlled scientific campaign**.

**SCIENTIFIC STATUS DECLARATION:**  
In accordance with task constraints:
- **No benchmark campaign was executed.**
- **No performance metrics (AUROC/C50/C90) have been claimed.**
- **`checkpoints/astrovision_spatial_v2.pt` remains uncertified (Audit Status: `FAIL`).**
- **Benchmark remediation remains in progress pending the Audit D photometry fix.**

