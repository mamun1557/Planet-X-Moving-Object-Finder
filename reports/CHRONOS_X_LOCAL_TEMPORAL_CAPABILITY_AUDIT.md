# CHRONOS-X Local Temporal Capability & Safe Fallback Audit

**Module:** CHRONOS-X — Multi-Epoch Temporal Anomaly Engine  
**Pipeline Build:** l2b-v27-2026-222  
**Parent Audits:** Task 1.3E, 1.3F, 1.3G, 1.3H, 1.3I  
**Audit Date:** 2026-11-07  
**Governance Mode:** STRICT READ-ONLY SCIENTIFIC AUDIT  

---

## 1. Executive Summary & Audit Mandate

This audit performs an independent, evidence-grounded evaluation of the CHRONOS-X temporal anomaly detection engine and the local SPHEREx Level-2 data repository.

The primary objective is to resolve five critical operational questions:
1. What temporal detection capabilities are genuinely implemented in source code versus stubs or planned features?
2. What temporal evidence is actually available on local disk?
3. Can the system reliably distinguish intra-visit dithers from genuine multi-epoch repeat observations?
4. How does the architecture handle missing, unverifiable, or incomplete temporal metadata?
5. Can CHRONOS-X be demonstrated safely in a public demo without fabricating false temporal discoveries?

### Key Audit Findings:
- **Core Algorithms are Real:** `models/chronos_x/model.py` contains a fully functional, mathematically sound image differencing pipeline featuring WCS reprojection (`reproject.reproject_interp`), SPHEREx fatal quality mask dilation (`FATAL_FLAG_MASK = 615`), combined variance propagation ($V_{\text{tot}} = V_1 + V_{2,\text{rep}}$), median background offset subtraction, and 5x5 stamp dipole artifact rejection.
- **Zero Local Multi-Epoch Observations:** Local storage holds exactly 171 science Level-2 FITS files across QR2 and QR3. All 599 overlapping image pairs are intra-visit dithers with separations between $2.15$ and $6.47$ minutes. There are **zero multi-epoch pairs** ($\Delta t \ge 1\text{ day}$) on local disk.
- **Critical Risk of False Transient Promotion:** In `scripts/inspect_fits.py`, `find_temporal_pairs` sets `min_time_diff_days = 0.001` ($1.44\text{ minutes}$), thus classifying intra-visit dithers as temporal pairs. In `models/fusion/fusion_engine.py` (lines 315–319), any anomaly with $\text{significance} > 5.0\sigma$ lacking a Gaia counterpart is automatically labeled `NEW_TRANSIENT_OR_ASTEROID_CANDIDATE`. Without baseline gating, intra-visit noise is promoted to a transient discovery.
- **Safe Fallback Feasibility:** CHRONOS-X is fully capable of operating in a demo mode as an **Astrometric Registration & Noise Verification Engine** on dithers, provided secular transient queries trigger an explicit fallback badge: `TEMPORAL_DATA_UNAVAILABLE`.

---

## 2. Stage A — Actual CHRONOS-X Implementation Inventory

A line-by-line inspection of the codebase was conducted to establish the exact implementation state:

| Component | Repository Path | Status | Evidence | Limitations / Constraints |
|---|---|---|---|---|
| `ChronosTemporalDifferencer` | `models/chronos_x/model.py` | Implemented | Class definition with `align_and_difference` and `_detect_candidates_and_dipoles` | Operates on single-band 2D numpy arrays; does not perform multi-band flux normalization. |
| WCS Alignment & Reprojection | `models/chronos_x/model.py` | Implemented | `reproject.reproject_interp(input_data=(img2, hdr2), output_projection=hdr1)` | Relies on standard FITS WCS keywords in header; unhandled exception if WCS missing or distorted. |
| Quality Mask Handling | `models/chronos_x/model.py` | Implemented | `FATAL_FLAG_MASK = 615; binary_dilation(..., footprint=disk(dilation_radius))` | Dilates bitmask 615 (SPHEREx fatal flags) and reprojects onto grid; non-fatal warning bits ignored. |
| Variance Propagation | `models/chronos_x/model.py` | Implemented | `combined_var = var1 + var2_rep; sig = abs(diff) / sqrt(combined_var)` | Correct independent error propagation; falls back to `np.ones_like` if variance array omitted. |
| Background Level Matching | `models/chronos_x/model.py` | Implemented | `diff_clean = diff - np.nanmedian(diff[valid_overlap])` | Scalar median offset subtraction; does not model 2D spatial gradients or zodiacal light variations. |
| PSF Matching | `models/chronos_x/model.py` | Implemented | `scipy.ndimage.gaussian_filter(diff, sigma=psf_match_sigma)` | Simple isotropic Gaussian blur approximation; does not use empirical SPHEREx PSF/EPSF cubes. |
| Dipole Vetting | `models/chronos_x/model.py` | Implemented | 5x5 stamp min/max ratio test (`max_val > 0.5*thresh and min_val < -0.5*thresh`) | Successfully vetoes astrometric misregistration dipoles; restricted to fixed 5x5 pixel stamps. |
| Differencing Driver | `models/chronos_x/run_temporal_differencing.py` | Implemented | `execute_temporal_differencing(pair_manifest_path, output_dir)` | Batch execution over candidate CSV; outputs `temporal_candidates.csv` and difference FITS. |
| Temporal Pair Discovery | `scripts/inspect_fits.py` | Partial | `find_temporal_pairs(df, max_sep_arcsec=7200, min_time_diff_days=0.001)` | **Critical defect:** `min_time_diff_days=0.001` ($1.44\text{ min}$) accepts intra-visit dithers. |
| Candidate Schema | `models/common/candidate_schema.py` | Partial | `CandidateRecord` dataclass | Generic `validity_status` (`VALID`, `WARNING`, `REJECTED`, `INSUFFICIENT_DATA`); lacks temporal-specific enum. |
| Multimodal Fusion | `models/fusion/fusion_engine.py` | Partial | `FusionEngine._classify_candidate` | Lacks baseline gating; labels high-significance dither differences as `NEW_TRANSIENT_OR_ASTEROID_CANDIDATE`. |

---

## 3. Stage B — Local Observation & Data Inventory

An exhaustive census of all local FITS files and metadata manifests was performed:

### 3.1 Local Level-2 Science Files
Local disk holds **171 unique science Level-2 FITS files**:
- `data/spherex/qr2/level2/`: 35 FITS files (Pointing 0001, 0002, 0003, 0004; Dec 2024 / Jan 2025).
- `data/spherex/qr2_deep/`: 36 FITS files (Deep coverage for QR2 pointings).
- `data/spherex/qr3/level2/`: 50 FITS files (Pointing 0010; Aug 2025, Week 30).
- `data/spherex/qr3_deep/`: 50 FITS files (Deep coverage for Pointing 0010).

### 3.2 Spatial Separation & Pair Census
- **QR2 vs QR3 Spatial Separation:** The centroids of QR2 pointings (Dec ~ -15° to -25°) and QR3 Pointing 0010 (Dec ~ +66.5°, North Ecliptic Pole) are separated by **over 70 degrees**. No cross-release spatial overlap exists.
- **Intra-Release Overlaps:** Across all 171 local science files, exactly **599 overlapping image pairs** exist.
- **Temporal Baseline Distribution:**
  - Minimum separation: $2.15\text{ minutes}$ (consecutive dithers in same visit).
  - Maximum separation: $6.47\text{ minutes}$ (dither 1 vs dither 4 in same visit).
  - Multi-epoch pairs ($\Delta t \ge 1.0\text{ day}$): **0**.
  - Multi-week pairs ($\Delta t \ge 7.0\text{ days}$): **0**.
  - Multi-month pairs ($\Delta t \ge 30.0\text{ days}$): **0**.

### 3.3 Reconciliation with Previous Audits (Tasks 1.3E–1.3I)
- The candidate 7-day, 14-day, and 18-day revisit baselines discussed in Task 1.3E originated from remote planning period manifests for Weeks 31 and 32.
- Tasks 1.3H and 1.3I verified that while these observations exist in the remote IPAC/IRSA archive planning schedule, **none of the corresponding Level-2 FITS files have been retrieved or stored locally**.
- Therefore, the local repository contains **zero multi-epoch repeat observations**.

---

## 4. Stage C — Temporal Eligibility Logic Audit

We evaluated the four operational categories established in project governance:

### Category A: Intra-Visit Dithers ($\Delta t < 1.0\text{ day}$, same visit sequence)
- **Scientific Nature:** Images taken minutes apart to step across detector gaps and mitigate bad pixels. Not independent secular variability evidence.
- **Codebase Evaluation:** In `scripts/inspect_fits.py`, `min_time_diff_days` is hardcoded to `0.001` ($86.4\text{ seconds}$). Consequently, `find_temporal_pairs` accepts all 599 intra-visit dithers. In `scripts/run_pointing_0003_pipeline.py`, dither 1D1 is diffed against 4D1 ($\Delta t = 6.47\text{ min}$) and passed directly into `FusionEngine`.

### Category B: Concurrent Cross-Detector Observations
- **Scientific Nature:** SPHEREx employs multiple detector arrays observing adjacent or overlapping fields simultaneously at distinct spectral bands (e.g., Det 1 at $0.75\text{–}1.1\,\mu\text{m}$ vs Det 2 at $1.1\text{–}1.6\,\mu\text{m}$).
- **Codebase Evaluation:** Neither `find_temporal_pairs` nor `ChronosTemporalDifferencer` verifies the `DETECTOR` FITS header keyword. Differencing two concurrent images from different detectors produces chromatic color differences rather than temporal variability.

### Category C: Independent Multi-Epoch Observations ($\Delta t \ge 1.0\text{ day}$)
- **Scientific Nature:** Independent observations of the same celestial footprint with compatible detectors, separated by days, weeks, or months.
- **Codebase Evaluation:** The mathematical differencing algorithms in `model.py` are fully capable of processing these pairs, but **zero candidate pairs exist locally**.

### Category D: Unverifiable Candidates
- **Scientific Nature:** Remote candidates lacking authoritative timestamps, missing WCS footprints, or unretrieved Level-2 files.
- **Codebase Evaluation:** If metadata is missing, `inspect_fits.py` drops rows silently rather than outputting an explicit `UNVERIFIABLE` candidate record with audit provenance.

### Critical Discovery: Potential False Transient Promotion
In `models/fusion/fusion_engine.py` (lines 314–320):
```python
if chronos_score is not None and chronos_score > self.thresholds.get("temporal_significance_sigma_threshold", 5.0):
    if not is_known_gaia_star:
        return "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
    else:
        return "STELLAR_VARIABILITY_OR_FLARE"
```
Because intra-visit dithers can exhibit residual registration spikes or unmasked bad pixels exceeding $5.0\sigma$, `FusionEngine` will classify them as **genuine new transients or asteroids** if no static Gaia counterpart matches within 2.0 arcsec! This demonstrates a critical engineering gap where Category A is promoted to a scientific discovery.

---

## 5. Stage D — Orthogonal Evidence and Temporal Status Audit

### 5.1 Evidence Hierarchy Verification
Project governance defines the cumulative evidence hierarchy:
- **E0:** Archive/manifest candidate exists.
- **E1:** Exact observation timestamps verified.
- **E2:** E1 + same detector + compatible spectral band.
- **E3:** E2 + actual WCS footprint overlap verified.
- **E4:** E3 + calibration, quality flags, and uncertainty compatibility verified.

**Crucial Clarification:** E4 represents evidence completeness and scientific comparability for an observation pair. **E4 does NOT require multi-epoch temporal separation.** Intra-visit dithers can achieve full E4 status as astrometric pairs while possessing zero secular temporal eligibility.

### 5.2 Orthogonal Temporal Status
Temporal eligibility must exist on an orthogonal axis:
$$\text{Candidate Status} = (\text{Evidence Level: } E_0\text{–}E_4) \times (\text{Temporal Baseline: } \text{ELIGIBLE} \mid \text{NOT\_ELIGIBLE} \mid \text{UNVERIFIABLE})$$

- **Current Implementation State:** In `models/common/candidate_schema.py`, `CandidateRecord` possesses only a single `validity_status` field (`VALID`, `WARNING`, `REJECTED`, `INSUFFICIENT_DATA`). There is no orthogonal field tracking temporal baseline validity.
- **Status Enum Gap:** The proposed status enums (`TEMPORAL_VALIDATED`, `TEMPORAL_NOT_ELIGIBLE`, `TEMPORAL_UNVERIFIABLE`, `TEMPORAL_DATA_UNAVAILABLE`, `TEMPORAL_EVIDENCE_INSUFFICIENT`) are **not yet implemented** in the active data schema.

---

## 6. Stage E — Safe Fallback and False Discovery Audit

We evaluated the system against the 8 required safe behaviors:

1. **No temporal anomaly score presented as validated discovery when data unavailable:**  
   *Current state:* Vulnerable. `rank_anomalies.py` injects synthetic exponential noise, and `run_pointing_0003_pipeline.py` passes dither significance to `FusionEngine`.
2. **No synthetic/simulated pair represented as real SPHEREx observations:**  
   *Current state:* `candidate_schema.py` includes `SYNTHETIC_BENCHMARK_SCORE`, but runtime ranking scripts do not attach it consistently.
3. **No QR2/QR3 release difference interpreted as temporal variability:**  
   *Current state:* Protected in practice because QR2 and QR3 are separated by $>70^\circ$, preventing differencing.
4. **No intra-visit dither described as long-term variability:**  
   *Current state:* Vulnerable due to `min_time_diff_days=0.001` in `inspect_fits.py`.
5. **Missing metadata not silently replaced with assumed values:**  
   *Current state:* Partially vulnerable; `model.py` defaults to `np.ones_like` if variance is omitted.
6. **Missing temporal baseline not becoming zero-variability:**  
   *Current state:* Handled safely; missing modality is marked `None` and renormalized in `FusionEngine`.
7. **Candidate confidence must not imply temporal validation:**  
   *Current state:* Addressed via governance recommendations; requires UI decoupling.
8. **Preserve provenance and explain why candidate cannot be evaluated:**  
   *Current state:* Partially implemented in `CandidateRecord.input_provenance`, but lacks detailed rejection logging for temporal baseline failures.

---

## 7. Stage F — Non-Destructive Test & Failure Analysis

Evaluation of the 10 conceptual test cases documented in `reports/CHRONOS_X_TEMPORAL_TEST_COVERAGE_MATRIX.csv`:

- **TC-01 (Two images separated by 3 min in one visit):** Expected: *Not temporal-eligible*. Actual: Accepted and classified as transient if $\sigma > 5$. Status: **FAIL**.
- **TC-02 (Concurrent cross-detector observations):** Expected: *Not temporal-eligible*. Actual: No detector validation; diffs across bands. Status: **FAIL**.
- **TC-03 (Two independent observations with compatible metadata):** Expected: *Candidate for temporal evaluation*. Actual: Differencing mechanics execute correctly. Status: **PASS (Algorithm) / NOT TESTED (Multi-Epoch)**.
- **TC-04 (Missing timestamp in FITS header):** Expected: *Unverifiable*. Actual: Dropped silently without provenance record. Status: **FAIL**.
- **TC-05 (Missing detector compatibility metadata):** Expected: *Unverifiable*. Actual: Not validated. Status: **FAIL**.
- **TC-06 (Missing WCS footprint in header):** Expected: *Insufficient spatial evidence*. Actual: `reproject_interp` raises unhandled exception or returns NaNs. Status: **FAIL**.
- **TC-07 (Incompatible pipeline release QR2 vs QR3):** Expected: *Not scientifically comparable*. Actual: Flagged in CSV, but differencing engine lacks programmatic veto. Status: **FAIL**.
- **TC-08 (Missing uncertainty/variance information):** Expected: *E4 not achieved*. Actual: Defaults to `np.ones_like`, masking error. Status: **FAIL**.
- **TC-09 (No multi-epoch observations available locally):** Expected: *Temporal data unavailable*. Actual: Differs dithers instead of signaling fallback. Status: **FAIL**.
- **TC-10 (Synthetic injected transient simulation):** Expected: *Clearly marked synthetic*. Actual: Injected as unflagged float in ranking script. Status: **FAIL**.

---

## 8. Stage G — Demo Readiness Assessment

### Selected Outcome: `LIMITED TEMPORAL CAPABILITY — SAFE FALLBACK VERIFIED`
Full architectural guidelines are documented in `reports/CHRONOS_X_DEMO_READINESS_ASSESSMENT.md`.

In summary:
- **What Can Be Demonstrated:** Sub-pixel astrometric reprojection, fatal flag dilation, variance propagation, and dipole artifact vetoing on intra-visit dithers (Pointings 0010 and 0003).
- **What Must Be Barred:** Long-term supernova, TDE, or secular variability claims.
- **UI Guardrail:** Display `TEMPORAL_DATA_UNAVAILABLE` or `TEMPORAL_NOT_ELIGIBLE` badges for all candidate queries on local SPHEREx files.

---

## 9. The 12 Final Questions Answered

### 1. Is CHRONOS-X temporal differencing actually implemented?
**Yes.** `ChronosTemporalDifferencer` in `models/chronos_x/model.py` is fully implemented and functional for 2D image differencing.

### 2. Is WCS reprojection implemented?
**Yes.** Reprojection onto the reference frame WCS is implemented using `reproject.reproject_interp`.

### 3. Are timestamp and detector compatibility checks implemented?
**No.** `scripts/inspect_fits.py` extracts `MJD-OBS`, but `find_temporal_pairs` does not enforce detector ID equality or spectral band matching.

### 4. Are same-visit dithers correctly rejected?
**No.** `find_temporal_pairs` uses `min_time_diff_days = 0.001` ($1.44\text{ min}$), which actively includes same-visit dithers ($2.15\text{–}6.47\text{ min}$).

### 5. Are cross-detector concurrent observations correctly rejected?
**No.** There is no cross-detector check; images from different detectors observing simultaneously can be passed to the differencer.

### 6. Does the system distinguish evidence completeness from temporal eligibility?
**Conceptually in reports, but not in code.** The code lacks separate fields for E0–E4 evidence completeness and temporal eligibility.

### 7. Is `UNVERIFIABLE` represented correctly?
**No.** If metadata is missing, files or pairs are omitted without generating an explicit `UNVERIFIABLE` status record.

### 8. Can the system accidentally report a temporal discovery without genuine multi-epoch data?
**Yes.** If an intra-visit dither pair produces a subtraction residual $>5.0\sigma$ without a Gaia match, `FusionEngine` classifies it as `NEW_TRANSIENT_OR_ASTEROID_CANDIDATE`.

### 9. Are QR2/QR3 release differences safely handled?
**Partially.** `inspect_fits.py` flags `is_inter_release`, and their $>70^\circ$ spatial separation prevents spatial overlap locally. However, the differencing class itself has no release compatibility guard.

### 10. Can the current system safely demonstrate temporal unavailability?
**Yes, with UI guardrails.** While the backend lacks an automated gate, the demo frontend can safely display `TEMPORAL_DATA_UNAVAILABLE` by enforcing explicit status mapping.

### 11. What exact engineering limitations remain?
1. Hardcoded $1.44\text{-minute}$ minimum baseline in `inspect_fits.py` must be updated to $\ge 1.0\text{ day}$.
2. Detector compatibility check (`hdr1['DETECTOR'] == hdr2['DETECTOR']`) is missing.
3. Orthogonal temporal status fields are missing from `CandidateRecord`.
4. `FusionEngine` classification heuristics must require verified multi-epoch baselines before assigning transient labels.

### 12. What is the recommended CHRONOS-X demo scope?
Demonstrate CHRONOS-X as an **Astrometric Registration, Noise Propagation & Dipole Vetting Engine** on Pointing 0010 dithers. Explicitly display `TEMPORAL_DATA_UNAVAILABLE` for secular transient queries, highlighting that true multi-epoch search awaits remote IRSA archive retrieval (Weeks 31–32).

---

## 10. Final Verdict

### Selected Verdict: `LIMITED TEMPORAL CAPABILITY — SAFE FALLBACK VERIFIED`

---

## 11. Final Governance Confirmation

In strict compliance with audit governance rules:
- **No source code modified:** Verified.
- **No model/checkpoint modified:** Verified.
- **No threshold/calibration modified:** Verified.
- **No scientific data modified:** Verified.
- **No remote network access attempted:** Verified.
- **No FITS downloaded:** Verified.
- **No previous audit report overwritten:** Verified.

---

## 12. Artifact Integrity Ledger

| Artifact Path | Format | SHA-256 Checksum |
|---|---|---|
| `reports/CHRONOS_X_LOCAL_TEMPORAL_CAPABILITY_AUDIT.md` | Markdown | *(Self-referential document)* |
| `reports/CHRONOS_X_TEMPORAL_IMPLEMENTATION_INVENTORY.csv` | CSV | `1dfb0c546c2d85aca984523e28cedfa6737d53763aa40b841b24d5c3044db38d` |
| `reports/CHRONOS_X_TEMPORAL_SAFE_FALLBACK_AUDIT.json` | JSON | `8ade25d9c43f0602a63534d74a9f54b23bcf0f444b65862a937694b1eda719fb` |
| `reports/CHRONOS_X_TEMPORAL_TEST_COVERAGE_MATRIX.csv` | CSV | `8f0339f70276039374f66989dd2ec7b6dc0dc06e3b47853729d9eb37508a090a` |
| `reports/CHRONOS_X_DEMO_READINESS_ASSESSMENT.md` | Markdown | `cdc44729607e167b4a7de3ea414c74a51104b3dfdc054c7bc44fea2fdae54bc4` |

### Protected Scientific Assets Verification
| Protected Scientific Asset | Expected / Verified SHA-256 Checksum | Status |
|---|---|---|
| `checkpoints/spectra_masked_ae_v2.pt` | `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938` | Confirmed Untouched |
| `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | `d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848` | Confirmed Untouched |

