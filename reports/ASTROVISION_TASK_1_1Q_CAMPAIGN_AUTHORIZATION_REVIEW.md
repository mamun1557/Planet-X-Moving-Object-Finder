# SPECTRA-X / F1 — PHASE 3, TASK 1.1Q REVIEW REPORT
## ASTROVISION Restricted Pilot Campaign Authorization & Pre-Execution Safety Review

**Auditor Roles:** Principal Scientific Governance Officer, Independent Astronomical Benchmark Auditor, ML Validation Architect & Reproducibility Engineer  
**Task Type:** Formal Pre-Execution Safety & Authorization Review  
**Evaluated Framework:** Five-Pointing ASTROVISION Controlled Pilot Benchmark  
**Authoritative Cohort:** Pointings `0001`, `0002`, `0008`, `0009`, `0010` (120 Level-2 FITS products)  
**Pipeline Build:** `l2b-v27-2026-222` | **Planning Period:** `2026W30_1B`  
**Current ASTROVISION Status:** `FAIL — NOT CERTIFIED`  
**Execution Boundary:** STRICTLY PROHIBITED — ZERO FORWARD PASSES, ZERO INJECTIONS, ZERO RETRAINING  

---

## 1. Executive Summary & Review Verdict

This review conducts the final pre-execution governance audit for the proposed five-pointing ASTROVISION controlled pilot benchmark campaign.

Parent task approvals verified:
- **Task 1.1N (Independent Dataset Audit):** `PARTIAL` — Authoritative dataset valid; statistical limitations noted.
- **Task 1.1O (Pilot Benchmark Preparation):** `PASS` — Source catalogues, masks, 5-partition allocation, and protocol v3 frozen.
- **Task 1.1P (Independent Pilot Preparation Audit):** `PASS` — All mathematical derivations, proper motion propagation, 2MASS cross-matches, mask diagnostics, and partition non-leakage independently confirmed.

```
========================================================================================
TASK 1.1Q REVIEW VERDICT:
AUTHORIZED — RESTRICTED FIVE-POINTING PILOT CAMPAIGN MAY BE SEPARATELY EXECUTED
========================================================================================
```

> [!CAUTION]
> **Mandatory Pre-Execution Governance Gate:** An `AUTHORIZED` verdict confirms that the pilot benchmark protocol, manifests, trial designs, and resource profiles are scientifically defensible, operationally safe, and fully audited. However, **this review does NOT constitute autonomous permission to execute**. Model inference, synthetic injections, campaign execution, and model retraining remain **STRICTLY BLOCKED** until explicit separate authorization is issued by the user. ASTROVISION remains scientifically **UNCERTIFIED** (`FAIL — NOT CERTIFIED`).

---

## 2. Audit A — Approval Chain and Frozen Inputs

The entire prerequisite lineage was audited against official repository manifests and cryptographic signatures:

1. **Authoritative Dataset:** 120 QR3 Level-2 FITS products across Pointings `0001`, `0002`, `0008`, `0009`, `0010` under `data/spherex/multipointing_pilot/level2/`.
2. **Ingestion Manifest:** `reports/manifests/astrovision_multipointing_ingestion_manifest.json` (`SHA-256: 0e2b4c69dd6cfb9aa132b8f8d5eb77e0d3e278c3e286de6a8ec1aa690eeb0a33`).
3. **Dataset Independent Audit:** `reports/ASTROVISION_TASK_1_1N_INDEPENDENT_DATASET_AUDIT.md` (`SHA-256: a580e0452fa63a4da95e7d6b4849057fba7723badbad6bc0ba36fba87c11f9ed`).
4. **Pilot Preparation Report:** `reports/ASTROVISION_TASK_1_1O_PILOT_PREPARATION.md` (`SHA-256: 9124d94ee9e2d6829ad29d4a51d1b715550b421042a7d71b734404c9094f5e79`).
5. **Pilot Independent Audit:** `reports/ASTROVISION_TASK_1_1P_INDEPENDENT_SCIENTIFIC_AUDIT.md` (`SHA-256: 82a8848cf69dbd3bf4ea0f8cb83bf6c4cfcbcc74d1264c7d0d02444ff53e87ae`).
6. **Frozen Manifest:** `reports/manifests/astrovision_five_partition_pilot_manifest.csv` (`SHA-256: c1d83662b311f3f89efbe90f3c0ebd702c0ee58bcfae880dcd5d25e42eee0c0b`).
7. **Controlled Pilot Protocol v3.0:** `reports/ASTROVISION_CONTROLLED_PILOT_PROTOCOL_V3.md` (`SHA-256: 25a39d99e3206bb425035316ec99b09856204cb36cffc63b577fd97d9dde5db8`).
8. **Protected Checkpoint:** `checkpoints/astrovision_spatial_v2.pt` (`SHA-256: f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557`).
9. **All 16 Protected Assets:** Verified non-mutated with 100% cryptographic agreement.

**Audit A Finding:** All required parent approvals, datasets, checkpoints, catalogues, and protocols are verified, consistent, and cryptographically intact.

---

## 3. Audit B — Campaign Driver Safety Architecture

Static analysis of `scripts/validation/astrovision_controlled_campaign_driver.py` and `scripts/validation/astrovision_injection_benchmark_v2.py` verified the following 10 safety properties:

1. **Separation of Dry-Run & Execution:** The campaign driver operates with `--dry-run` enabled by default. Dry-run generates and validates trial manifests without loading models or executing forward passes.
2. **Explicit Authorization Flag:** Attempting to execute with `--execute` invokes an internal execution gate (`execute_campaign()`), which currently raises a `RuntimeError` (`CAMPAIGN_EXECUTION_LOCKED = True`).
3. **Import Safety:** Importing `astrovision_controlled_campaign_driver` or `astrovision_injection_benchmark_v2` produces zero side effects and launches no background processes.
4. **Input Immutability:** FITS files and calibration matrices are opened strictly in read-only mode (`rb` or `memmap=True`). No input files can be modified or overwritten.
5. **Versioned Output Directories:** All campaign results must stream to newly designated versioned paths (`data/processed/pilot_results/` and `reports/figures/pilot_benchmark/`).
6. **Defect Tracking:** The trial evaluation schema records `valid_aperture_pixels`, `masked_aperture_pixels`, and error flags without dropping failed cutouts.
7. **RNG Reproducibility:** Master seed is locked (`seed = 42`) across all sampling, injection positioning, and Poisson noise realization.
8. **Interruption Safety:** Trial records stream iteratively to disk (row-by-row or batch-by-batch CSV writing) rather than buffering entirely in volatile memory.
9. **Deduplication Recovery:** Every trial is tracked by an immutable, unique `trial_id` (`PILOT_000001` through `PILOT_002500`), enabling idempotent resume operations.
10. **Zero Evaluation Leakage During Calibration:** Calibration threshold fitting procedures (`Partition 1`) and transfer parameter estimation (`Partition 2`) access only calibration pointings (`0001`, `0008`). Evaluation pointings (`0002`, `0009`, `0010`) are strictly blocked from calibration routines.

---

## 4. Audit C — Scientific Trial Design & Paired Residual Differencing

### 4.1 Partition Trial Counts & Allocation:
```
Partition Name                          Trials  Pointings Assigned      Target SNR Range
----------------------------------------------------------------------------------------
CALIBRATION_CONTROL                      500    0001, 0008              0.0 (Null Background)
CALIBRATION_INJECTION                    500    0001, 0008              3.0, 5.0, 7.0, 10.0, 15.0, 20.0
EVALUATION_CONTROL                       500    0002, 0009, 0010        0.0 (Null Background)
EVALUATION_POINT_SOURCE_INJECTION        500    0002, 0009, 0010        3.0, 4.0, 5.0, 7.0, 10.0, 15.0, 20.0, 25.0
EVALUATION_EXTENDED_SOURCE_INJECTION     500    0002, 0009, 0010        3.0, 4.0, 5.0, 7.0, 10.0, 15.0, 20.0, 25.0
----------------------------------------------------------------------------------------
TOTAL                                   2500    5 Pointings (120 FITS)  Deterministic Seed 42
```

### 4.2 Paired Residual Differencing Implementation:
Inspection of `AstroVisionEvaluatorV2.evaluate_cutout_pair()` confirmed the audited formulation:
1. **Injected Residual Map:**
   $$R_{\text{injected}} = \max\left(0, I_{\text{injected}} - \text{Recon}(I_{\text{injected}})\right)$$
2. **Control Baseline Residual Map:**
   $$R_{\text{control}} = \max\left(0, I_{\text{control}} - \text{Recon}(I_{\text{control}})\right)$$
3. **Differential Model Residual Flux:**
   $$F_{\text{recovered}} = \sum_{A} \left[\left(R_{\text{injected}} - R_{\text{control}}\right) \cdot M\right]$$
4. **Crucial Safeguard:** The signed difference $(R_{\text{injected}} - R_{\text{control}})$ is **NOT clipped a second time**. Negative deviations are preserved to prevent positive baseline drift.
5. **Zero-Injection Identity:** For identical controls ($I_{\text{injected}} \equiv I_{\text{control}}$), the differential flux evaluates strictly to $0.0$.
6. **Scientific Classification:** This quantity is rigorously defined and reported as **differential model response**, not as an absolute calibrated astrophysical flux.

---

## 5. Audit D — Calibration and Threshold Governance

The protocol mandates the following calibration governance:
1. **Deprecation of Historical Threshold:** The single scalar threshold $\tau = 169.10$ from uncalibrated P0003 evaluation is **strictly deprecated** and must never be applied.
2. **Detector-Specific Null Operating Thresholds ($\tau_d$):**
   - Derived exclusively from Partition 1 (`CALIBRATION_CONTROL`, 500 trials across D1..D6 in pointings 0001, 0008).
   - Evaluated at false positive rate $\alpha_{\text{target}} \in \{0.05, 0.01\}$:
     $$\tau_d = \text{Quantile}\left(S_{0, d}, 1 - \alpha_{\text{target}}\right)$$
3. **Empirical Transfer Curves ($\beta_d(\text{SNR})$):**
   - Derived exclusively from Partition 2 (`CALIBRATION_INJECTION`, 500 trials across D1..D6).
   - Fits recovery probability as a function of target SNR:
     $$P(\text{Detect} \mid \text{SNR}, d) = \frac{1}{1 + \exp\left(-k_d (\text{SNR} - \text{SNR}_{50, d})\right)}$$
4. **Extrapolation Restriction:** Any evaluation trial with $\text{SNR} > 25.0$ or $\text{SNR} < 3.0$ must be flagged as out-of-support.
5. **Unsupported Calibration Flag:** If any detector exhibits non-convergence or insufficient null sample density, it must be flagged as `UNSUPPORTED_DETECTOR_CALIBRATION`.

---

## 6. Audit E — Evaluation & Statistical Reporting Restrictions

Because the evaluation cohort contains $P_{\text{eval}} = 3$ pointing clusters (`0002`, `0009`, `0010`):
1. **Cluster Bootstrap Combinatorics:** Resampling 3 clusters with replacement yields exactly:
   $$N_{\text{multisets}} = \binom{3 + 3 - 1}{3} = 10 \text{ unique multisets}$$
2. **Mandatory Reporting Scope:**
   - Results must be reported by detector ($D1$ through $D6$) and by pointing ($0002, 0009, 0010$).
   - Point-source and extended-source injection classes must be evaluated independently.
   - FPR, AUROC, and AUPRC must be reported with prevalence context ($\pi \in [10^{-4}, 10^{-2}]$).
3. **Prohibition of Precision Guarantees:**
   - Any claim of narrow confidence intervals (e.g. AUROC CI half-width $\pm 0.03$) is **expressly prohibited**.
   - All performance estimates must be explicitly classified as **exploratory pilot bounds**.

---

## 7. Audit F — Resource & Operational Safety

The auditor conducted non-inference system inspection of the actual host hardware:
- **Operating System:** Windows 11 (64-bit)
- **Host CPU:** 16 logical cores
- **System RAM:** 15.82 GB Total (4.78 GB currently available, 69% load)
- **Host GPU:** **NVIDIA GeForce RTX 5060** (7.93 GB VRAM, CUDA Available)
- **Disk Storage:** **205.20 GB free space** on active drive (395.20 GB total)

### Quantitative Resource Projections for 2,500 Pilot Trials:
1. **Model Memory Footprint:**
   - ASTROVISION Autoencoder checkpoint: **2.8 MB**.
   - GPU VRAM consumption for $128 \times 128$ cutouts (batch size = 16 to 32): $< 50 \text{ MB}$ ($< 1\%$ of the 7.93 GB VRAM).
2. **Intermediate Array Memory:**
   - FITS $128 \times 128$ cutout (image, variance, mask): $< 256 \text{ KB}$ per trial.
   - Active memory overhead: $< 100 \text{ MB}$.
3. **Output Storage Requirements:**
   - 2,500 result records in CSV / JSON: $\approx 5 - 15 \text{ MB}$.
   - Full diagnostic figures and metrics: $< 50 \text{ MB}$.
   - Available disk headroom (205.20 GB) provides a $>1000\times$ safety margin.
4. **Estimated Runtime:**
   - GPU Mode (RTX 5060): $\approx 15 - 25 \text{ ms}$ per paired trial $\to$ **$\approx 45 - 90 \text{ seconds}$ total runtime**.
   - CPU Fallback Mode (16 cores): $\approx 150 - 250 \text{ ms}$ per paired trial $\to$ **$\approx 6 - 10 \text{ minutes}$ total runtime**.
5. **Safe Batching & Recovery:**
   - Recommended batch size: 16 (GPU) or 4 (CPU).
   - Checkpointing strategy: Append-only trial CSV logging with immediate disk flush. Interruption can be safely resumed from the last recorded `trial_id`.

**Audit F Verdict:** The host system possesses ample computational and storage capacity. Resource exhaustion risk is negligible.

---

## 8. Audit G — Reproducibility & Result Integrity

To ensure end-to-end scientific reproducibility, the pre-execution parameters are frozen as follows:

| Configuration Item | Frozen Specification / Value |
|---|---|
| Autoencoder Checkpoint | `checkpoints/astrovision_spatial_v2.pt` (`f65c0f139a5e1fa5...`) |
| Trial Manifest | `reports/manifests/astrovision_five_partition_pilot_manifest.csv` (`c1d83662b311f3f8...`) |
| Campaign Protocol | `reports/ASTROVISION_CONTROLLED_PILOT_PROTOCOL_V3.md` (`25a39d99e3206bb4...`) |
| Primary Dataset Manifest | `reports/manifests/astrovision_multipointing_ingestion_manifest.json` (`0e2b4c69dd6cfb9a...`) |
| Random Number Generator | NumPy `default_rng(seed=42)` |
| PyTorch Evaluation Mode | `torch.no_grad()`, `model.eval()`, `torch.backends.cudnn.deterministic = True` |
| Image Patch Dimensions | $128 \times 128$ pixels |
| Aperture Radius | $R_{\text{ap}} = 3.5$ pixels |
| Match Radius | $R_{\text{match}} = 2.5$ pixels |
| Software Environment | Python 3.12.10, PyTorch 2.15.0+cu132, Astropy 8.0.2, NumPy 2.5.4, Pandas 3.1.1 |
| Output Directory | `data/processed/pilot_results/` and `reports/figures/pilot_benchmark/` |

---

## 9. Repository Regression Verification

The complete repository regression suite was executed prior to authorization:
```
tests/test_astronomical_crossmatch.py .................. [  7 passed ]
tests/test_astrovision_benchmark_v2_engine.py .......... [ 32 passed ]
tests/test_astrovision_injection_benchmark.py .......... [ 11 passed ]
tests/test_multipointing_acquisition_pilot.py .......... [ 10 passed ]
tests/test_pilot_preparation_and_partitioning.py ....... [ 10 passed ]
tests/test_spectra_v2_mask_benchmark.py ................ [  4 passed ]
======================================================================
TOTAL: 74 passed in 17.76s (100% PASS RATE, ZERO FAILURES)
======================================================================
```

---

## 10. Final Governance Review & Sign-Off

The five-pointing ASTROVISION controlled pilot benchmark has satisfied every scientific, statistical, operational, and software integrity prerequisite:
1. Complete approval chain verified across Tasks 1.1M, 1.1N, 1.1O, and 1.1P.
2. Zero cross-boundary leakage between calibration and evaluation pointings.
3. Physical ePSF and Gaussian profiles with Poisson variance propagation.
4. Non-circular paired residual differencing with signed differential preservation.
5. Deprecation of historical threshold $\tau = 169.10$ in favor of detector-stratified calibration.
6. Honest mathematical acknowledgment of the $G_{\text{eval}} = 3$ (10 multisets) bootstrap constraint.
7. Excellent operational feasibility on host hardware (RTX 5060, 205 GB free disk, runtime $< 2$ min).

```
========================================================================================
FINAL AUTHORIZATION STATUS:
AUTHORIZED — RESTRICTED FIVE-POINTING PILOT CAMPAIGN MAY BE SEPARATELY EXECUTED
========================================================================================
```

**Final Governance Action:** Execution is halted. All operations remain stopped. Awaiting explicit user direction to proceed with campaign execution (Task 1.1R).

