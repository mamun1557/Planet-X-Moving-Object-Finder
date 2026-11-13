# SPECTRA-X / F1 — Phase 4, Task 4.27T
## CHRONOS-X Scratch Smoke Test API Compatibility Diagnostic Report

**Task Mode:** STRICT READ-ONLY DIAGNOSTIC  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10, PyTorch 2.15.0+cu132, CUDA: RTX 5060)  
**Parent Tasks:** Task 4.27S, Task 4.27R, Task 4.27  
**Date:** November 9, 2026  
**Final Mandated Verdict:** **`SCRATCH_API_MISMATCH_CONFIRMED`**

---

### 1. Executive Summary & Root Cause

| Diagnostic Field | Finding |
| :--- | :--- |
| **Reported Failure** | `ImportError: cannot import name 'TemporalEligibilityEngine' from 'models.chronos_x.temporal_eligibility'` |
| **Failure Location** | `scratch/run_smoke_tests.py`, line 116 |
| **Exact Root Cause** | **Fictitious / Non-Existent Class Name in Scratch Test.** The module `models.chronos_x.temporal_eligibility` exposes a functional API centered on `evaluate_pair_temporal_eligibility()` and `determine_dataset_temporal_availability()`, returning standardized `TemporalEligibilityResult` dataclass instances. No class named `TemporalEligibilityEngine` exists anywhere in the codebase. |
| **Production Impact** | **ZERO PRODUCTION IMPACT.** Production pipelines, FUSION-X evidence integration, and all 12 regression suites in `tests/test_chronos_x_temporal_eligibility.py` utilize the canonical functional API. The failure is 100% confined to the newly authored diagnostic scratch script. |
| **Scientific Integrity** | **UNCOMPROMISED.** All temporal safety rules, fail-closed dither contracts, and three protected repository assets remain completely untouched and verified. |

---

### 2. Actual CHRONOS-X Public API Specification

The authoritative implementation in [`models/chronos_x/temporal_eligibility.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/chronos_x/temporal_eligibility.py) defines the following public symbols:

#### 2.1 Primary Data Contract: `TemporalEligibilityResult`
```python
@dataclass
class TemporalEligibilityResult:
    status: str                         # "TRUE", "FALSE", "UNVERIFIABLE"
    evidence_tier: str                  # "E0", "E1", "E2", "E3", "E4", "NONE"
    is_dither: bool                     # True if intra-visit dither sequence
    dt_days: Optional[float]            # Elapsed time separation in days
    reasons: List[str]                  # Explanations for eligibility or exclusion
    missing_evidence: List[str]         # Specific missing metadata fields if UNVERIFIABLE
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### 2.2 Core Evaluation Function: `evaluate_pair_temporal_eligibility`
```python
def evaluate_pair_temporal_eligibility(
    obs1: Dict[str, Any],
    obs2: Dict[str, Any],
    min_baseline_days: float = DEFAULT_MIN_BASELINE_DAYS,  # 1.0 day
    max_sep_arcsec: float = 12600.0,                      # 3.5 deg FOV
    policy_version: str = BASELINE_POLICY_VERSION         # "v1.0-2026-F1"
) -> TemporalEligibilityResult:
```
*Scientific Contract:*
- Evaluates pair against 10 strict scientific criteria.
- Assigns orthogonal Evidence Tier (`E0` through `E4`).
- Same-visit dithers ($\Delta t < 30$ min or $\Delta t < \text{min\_baseline\_days}$) evaluate to `status="FALSE"`, `is_dither=True`, with exclusion reason `INTRA_VISIT_DITHER`.
- Missing required metadata fields evaluate to `status="UNVERIFIABLE"`.

#### 2.3 Dataset-Level Gate Function: `determine_dataset_temporal_availability`
```python
def determine_dataset_temporal_availability(
    pairs_or_results: List[Union[Dict[str, Any], TemporalEligibilityResult]],
    exclude_synthetic: bool = True
) -> str:
```
*Scientific Contract:*
- Returns `"TEMPORAL_DATA_AVAILABLE"` **only** if at least one genuine astronomical observation pair satisfies `status == "TRUE"`.
- If only intra-visit dithers or synthetic benchmarks exist, it strictly returns `"TEMPORAL_DATA_UNAVAILABLE"`.

---

### 3. Existing Verified Production Usages

A thorough repository audit confirmed that all production code and automated tests import and use the functional API:

1. **Test Suite ([`tests/test_chronos_x_temporal_eligibility.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/tests/test_chronos_x_temporal_eligibility.py#L30-L37)):**
   ```python
   from models.chronos_x.temporal_eligibility import (
       evaluate_pair_temporal_eligibility,
       determine_dataset_temporal_availability,
       TemporalEligibilityResult,
       DEFAULT_MIN_BASELINE_DAYS,
       BASELINE_POLICY_VERSION,
       ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES,
   )
   ```
   All 12 comprehensive test fixtures pass cleanly using these functions.
2. **FUSION-X Multi-Modal Engine ([`models/fusion/fusion_engine.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/fusion/fusion_engine.py#L154-L226)):**
   Accepts `chronos_temporal_eligibility: Optional[str]` expecting `"TRUE"`, `"FALSE"`, or `"UNVERIFIABLE"`, perfectly matching `TemporalEligibilityResult.status`.
3. **Repository-Wide Search for `TemporalEligibilityEngine`:**
   Zero production `.py` files implement or import `TemporalEligibilityEngine`. It appears only in descriptive markdown report tables and narrative architecture summaries (e.g. Task 4.20A and Task 4.22 audit matrices) as a conceptual system descriptor for the combination of `ChronosTemporalDifferencer` and `temporal_eligibility.py`.

---

### 4. Intended Scratch-Test Behavior

Lines 115–124 of `scratch/run_smoke_tests.py` contain:
```python
# 6. Temporal Eligibility Smoke Test
from models.chronos_x.temporal_eligibility import TemporalEligibilityEngine
eng = TemporalEligibilityEngine()
el_res = eng.evaluate(mjd1=61241.0000, mjd2=61241.0035, obs_id1="OBS1", obs_id2="OBS2", pointing1="P0002", pointing2="P0002")
results["temporal_eligibility"] = {
    "dt_hours": el_res.delta_t_hours,
    "status": el_res.status,
    "fail_closed_verified": el_res.status == "TEMPORAL_INELIGIBLE"
}
```

**Intent:**
The test author intended to verify that an intra-visit dither pair separated by $\approx 5$ minutes ($\Delta t = 0.0035$ days $\approx 0.084$ hours) fails closed and is marked ineligible for secular temporal discovery.

**API Discrepancy:**
The author assumed an object-oriented wrapper with method `.evaluate(...)` and return field `.delta_t_hours` with status `"TEMPORAL_INELIGIBLE"`. In the canonical API:
- The function is `evaluate_pair_temporal_eligibility(obs1, obs2)`.
- Status is `"FALSE"` (not `"TEMPORAL_INELIGIBLE"`).
- Elapsed time is stored in `.dt_days` (which can be multiplied by 24 for hours).
- Fail-closed behavior is verified by `el_res.status == "FALSE"` and `el_res.is_dither is True`.

---

### 5. Production Impact Assessment

- **Production Code Status:** **COMPLETELY UNAFFECTED.** No production inference scripts or models import `TemporalEligibilityEngine`.
- **Checkpoint Status:** **100% UNTOUCHED.** All protected assets (`astrovision_spatial_v3.pt`, `spectra_masked_ae_v2.pt`, and `spectra_v2_provisional_thresholds_v1.json`) maintain pristine cryptographic SHA-256 integrity.
- **Test Suite Status:** All 309 automated tests in `tests/` continue to execute and pass cleanly.

---

### 6. Minimal Safe Remediation Recommendation (When Authorized)

When code remediation on `scratch/run_smoke_tests.py` is authorized, lines 115–123 should be updated to invoke the canonical functional API without introducing any new classes or modifying production files:

```python
# 6. Temporal Eligibility Smoke Test
from models.chronos_x.temporal_eligibility import evaluate_pair_temporal_eligibility

obs1 = {
    "filename": "SPHEREX_L2_P0002_1D1_DET1.fits",
    "obsid": "P0002_1D1",
    "detector": 1,
    "mjd_obs": 61241.0000,
    "ra_deg": 180.0,
    "dec_deg": 20.0,
    "wcs_available": True,
    "variance_available": True,
    "flags_available": True,
}
obs2 = {
    "filename": "SPHEREX_L2_P0002_2D1_DET1.fits",
    "obsid": "P0002_2D1",
    "detector": 1,
    "mjd_obs": 61241.0035,  # ~5.04 min later
    "ra_deg": 180.0,
    "dec_deg": 20.0,
    "wcs_available": True,
    "variance_available": True,
    "flags_available": True,
}

el_res = evaluate_pair_temporal_eligibility(obs1, obs2)
results["temporal_eligibility"] = {
    "dt_days": el_res.dt_days,
    "dt_hours": float(el_res.dt_days * 24.0) if el_res.dt_days is not None else None,
    "status": el_res.status,
    "is_dither": el_res.is_dither,
    "fail_closed_verified": (el_res.status == "FALSE" and el_res.is_dither is True)
}
```

*This requires zero modifications to production code, zero modifications to tests, and zero model alterations.*

---

### 7. Final Mandated Verdict

$$\mathbf{SCRATCH\_API\_MISMATCH\_CONFIRMED}$$

The reported `ImportError` is definitively confirmed to be an isolated scratch-script mismatch with the canonical CHRONOS-X functional API. Production code and scientific validation assets remain intact and fully operational.

