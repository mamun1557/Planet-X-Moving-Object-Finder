# SPECTRA-X / F1 — Phase 4, Task 4.15
# Masking Safety & Governance Test Suite Audit

**Test Suite File:** [`tests/test_catalog_aware_source_masker.py`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/tests/test_catalog_aware_source_masker.py)  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10)  
**Total Safety Scenarios:** 20  
**Pass Rate:** **20 / 20 (100.0%)**  
**Full Pipeline Regression Test Status:** **270 / 270 (100.0%) Passed in 30.48s**  
**Pipeline Build:** `l2b-v27-2026-222`  

---

## 1. Safety Test Matrix & Execution Results

| # | Test Method Name | Scenario Description & Governance Invariant | Expected Behavior | Observed Result | Status |
|---|---|---|---|---|:---:|
| 01 | `test_01_known_catalog_source_masking` | Off-center confirmed star in FOV | Source masked; `M_eff` = 0.0 at $(30, 30)$; center target unaffected | Effective mask 0.0 at source, 1.0 at center | **PASS** |
| 02 | `test_02_probable_source_masking` | Secondary detection without deep astrometry | Generates standard defensive mask | Mask correctly applied at $(80, 40)$ | **PASS** |
| 03 | `test_03_ambiguous_source_masking_policy` | High RUWE / confused source | Masked when policy is True; omitted when False; limitation attached | Both policy branches validated; limitation logged | **PASS** |
| 04 | `test_04_no_local_catalog_counterpart_handling` | Clean verified sky area | Zero pixels added to source mask; valid sky untouched | 0 masked pixels; mask remains 1.0 | **PASS** |
| 05 | `test_05_mask_unverifiable_fail_closed` | Missing survey footprint | Fails closed; logs `SOURCE_EVIDENCE_UNVERIFIABLE` | Limitation logged; count incremented; no crash | **PASS** |
| 06 | `test_06_empty_source_catalog` | No catalog records in request | Returns pristine base defect mask without alteration | Output matches input base defect mask exactly | **PASS** |
| 07 | `test_07_out_of_bounds_coordinates` | Source coordinates far outside cutout ($x=-150$) | Handled safely without exception; logs `SOURCE_OUT_OF_BOUNDS` | Skipped gracefully with limitation recorded | **PASS** |
| 08 | `test_08_invalid_coordinates_nan_inf` | NaN / Inf subpixel coordinates | Rejects corrupted coordinate; logs `COORDINATE_PROJECTION_FAILED` | Zero masked pixels; failure recorded | **PASS** |
| 09 | `test_09_duplicate_source_deduplication` | Multiple records with same `source_id` | De-duplicates; only masks footprint once; logs warning | Masked count = 1; warning code logged | **PASS** |
| 10 | `test_10_overlapping_source_masks` | Two sources separated by 2 pixels | Merges binary masks; no arithmetic overflow ($>1.0$) | Strict binary values $\{0.0, 1.0\}$ preserved | **PASS** |
| 11 | `test_11_cutout_edges_and_corners` | Sources placed at $(0,0), (127,0), (0,127), (127,127)$ | Boundary clipping handles edges without indexing errors | All 4 corner pixels correctly masked | **PASS** |
| 12 | `test_12_invalid_dilation_rejection` | Dilation radius outside $\{0, 1, 2, 3, 5\}$ | Strict parameter rejection; raises `ValueError` | `ValueError` raised for $-1, 4, 10, 100$ | **PASS** |
| 13 | `test_13_central_aperture_protection` | Source close to center ($d=3.0\text{ px}$) | Central evaluation aperture ($r \le 2.5\text{ px}$) shielded | Central target pixel $(64, 64)$ remains 1.0 | **PASS** |
| 14 | `test_14_base_defect_mask_preservation` | Base defect mask contains hardware dead pixels | Base defect mask zeros strictly preserved ($M_{\text{eff}} = M_{\text{base}} \land \neg M_{\text{src}}$) | Hardware dead pixel remains 0.0 | **PASS** |
| 15 | `test_15_strict_polarity_convention` | Verification of ASTROVISION vs standalone polarity | Effective: 1=valid, 0=defect; Standalone: 1=masked, 0=sky | Polarities strictly validated | **PASS** |
| 16 | `test_16_deterministic_mask_generation` | Identical requests executed sequentially | Bitwise identical masks and identical pixel counts | Bitwise array equality verified | **PASS** |
| 17 | `test_17_provenance_metadata_tracking` | Complete provenance metadata audit | Contains module name, build, dilation, and source counts | Metadata dictionary fully populated | **PASS** |
| 18 | `test_18_serialization_round_trip` | Dataclass to/from dictionary serialization | Lossless reconstruction of `CatalogSourceContext` & results | Round-trip object equivalence confirmed | **PASS** |
| 19 | `test_19_request_validation_rejection` | Negative cutout shapes or invalid target coords | Raises `ValueError` on malformed request parameters | `ValueError` raised on bad shape / NaN coords | **PASS** |
| 20 | `test_20_central_target_not_suppressed` | Central target record marked with `is_center_target=True` | Engine distinguishes target candidate from off-center contaminant | Central candidate protected from self-suppression | **PASS** |

---

## 2. Regression & Production Stability Audit

Running the entire SPECTRA-X validation test suite demonstrates complete non-interference with all existing scientific modules:

```powershell
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X
collected 270 items

tests/test_astrovision_benchmark_v3.py ..........                         [  3%]
tests/test_astrovision_v3_remediation.py .........................       [ 12%]
tests/test_catalog_aware_source_masker.py ....................           [ 20%]
tests/test_continuum_sidecar_engine.py ................................... [ 33%]
tests/test_continuum_sidecar_governance.py .............................  [ 44%]
tests/test_continuum_sidecar_interface.py ............................... [ 55%]
tests/test_fusion_contract.py .........................................  [ 70%]
tests/test_phase_4_8_audit.py ........................................... [ 85%]
tests/test_spectra_evidence_adapter.py .................................. [ 98%]
tests/test_spectra_v2_mask_benchmark.py .....                            [100%]

270 passed in 30.48s
```

All 250 previously certified tests across FUSION-X, ASTROVISION V3, and Continuum Sidecar passed with zero regressions.

