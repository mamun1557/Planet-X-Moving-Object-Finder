# SPECTRA-X / F1 — Phase 4, Task 4.10
# Unknown-Provenance Fail-Closed Allowlist & Immutable Evidence Contract Remediation Report

**Task Type:** CONTROLLED SCIENTIFIC GOVERNANCE REMEDIATION  
**Pipeline Build:** `l2b-v27-2026-222`  
**Parent Audit:** Phase 4, Task 4.9  
**Authoritative Contract:** `CONTINUUM_SIDECAR_EVIDENCE_V1`  
**Target Environment:** `SPECTRA-X/.venv_validation` (Isolated Python 3.12.10)  
**Governance Protocol:** Strict Provenance / Explicit Calibration Allowlist / Immutable Evidence / Frozen Asset Protection  
**Remediation Timestamp:** 2026-11-07T19:38:59Z  
**Final Remediation Verdict:** **`REMEDIATION_SUCCESSFUL`**

---

## 1. Executive Summary

This controlled scientific governance remediation resolves the two vulnerabilities identified in the Phase 4, Task 4.9 Adversarial Audit:

1. **`FIND-4.9-01` (Denylist vs Allowlist Asymmetry on Pointing Identity):**  
   Unknown pointing identifiers (such as `P9999`) previously bypassed blind-cohort restrictions because the engine used an explicit blind denylist (`["P0002", "P0009", "P0010"]`), defaulting to permissive non-blind evaluation.  
   **Remediation:** Inverted the pointing governance to a centralized, explicit calibration allowlist (`CANONICAL_CALIBRATION_POINTING = "P0008"`). Every unknown, missing, empty, malformed, untrusted, or conflicting pointing identity now strictly fails closed to `evidence_state = "UNVERIFIABLE"` and `color_excess_detected = False`.
2. **`FIND-4.9-02` (Dataclass Post-Validation Mutability):**  
   `ContinuumEvidenceRecord` was previously an open `@dataclass`, permitting caller attributes and nested collections (`limitation_codes`, `metadata`) to be mutated in Python memory after contract validation.  
   **Remediation:** Converted `ContinuumEvidenceRecord` to a `@dataclass(frozen=True)` backed by recursive deep-freezing of limitation codes via `ReadOnlyList` and metadata/color indices via `ReadOnlyDict`. Direct field reassignment raises `FrozenInstanceError`, and in-place collection mutations raise `TypeError`.

All 26 targeted safety requirements were validated, all 25 real P0008 pilot records preserved 100% identical outputs, FUSION-X anomaly score invariance remained exactly zero ($\max |\Delta| = 0.000000$ with 0 rank shifts), all 3 frozen scientific assets remained cryptographically pristine, and the entire 250-test regression suite passed.

### Key Remediation Metrics
| Metric | Value / Result | Evaluation Status |
| :--- | :--- | :--- |
| **Final Remediation Verdict** | **`REMEDIATION_SUCCESSFUL`** | **VERIFIED CLEAN** |
| **`FIND-4.9-01` Allowlist Remediation** | 14/14 Scenarios Enforced Fail-Closed | **REMEDIATED** |
| **`FIND-4.9-02` Immutability Remediation** | 16/16 Mutation Vectors Blocked | **REMEDIATED** |
| **P0008 Real Pilot Record Preservation** | 25/25 Sources Identical Outputs | **100% PRESERVED** |
| **FUSION-X Maximum Score Delta** | **$\max \|\Delta\| = 0.000000$** | **EXACT INVARIANCE** |
| **FUSION-X Rank Shift Count** | **0 Rank Shifts** | **EXACT ORDERING** |
| **Targeted Safety Suite Execution** | 26/26 Tests Passed | **100% PASSED** |
| **Total Project Regression Suite** | 250/250 Tests Passed | **100% PASSED** |
| **Protected Scientific Asset Integrity** | 3 Assets Verified via SHA-256 | **100% PRISTINE (0 Changes)** |

---

## 2. Mandatory Pre-Implementation Audit

Prior to applying code changes, the environment, contracts, and test suites were audited:
- **Interpreter Environment:** Verified isolated virtual environment `SPECTRA-X/.venv_validation` with Python 3.12.10 (`include-system-site-packages = false`).
- **Baseline Test Suite:** Executed full workspace test suite prior to changes: 224/224 tests passing in 40.60s.
- **Pre-Change SHA-256 Hashes:**
  - `checkpoints/spectra_masked_ae_v2.pt`: `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938`
  - `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json`: `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848`
  - `checkpoints/astrovision_spatial_v3.pt`: `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99`
  - `spectra_engine/continuum_sidecar_interface.py`: `DEF9B72A5AA7F43B8FC6E51CE061400A09BDCC4926AC41EF42DF2E78EFF58FB0`
  - `spectra_engine/continuum_sidecar_engine.py`: `ABB794DEC086AF66FD7BE142B393D9CB76C71B902562D150C0AC6C8953E8B9A3`
  - `models/fusion/fusion_engine.py`: `390AA6A9E1EFECBE3D0357CCEAC010E53C1717480651F7240B0B169B28AF0923`
  - `tests/test_blind_cohort_promotion_safety.py`: `19669F27810BE307B8F16552D6315BD96FF467DD5B5FF311AC70C83B78C4BECC`

---

## 3. Centralized Explicit Calibration Allowlist (`FIND-4.9-01`)

Full data recorded in [`reports/PHASE_4_10_POINTING_ELIGIBILITY_MATRIX.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_POINTING_ELIGIBILITY_MATRIX.csv).

### 3.1 Architectural Design
The flawed denylist approach in `spectra_engine/continuum_sidecar_interface.py` and `spectra_engine/continuum_sidecar_engine.py` was replaced by a single, authoritative provenance-resolution policy:

```python
CANONICAL_CALIBRATION_POINTING = "P0008"
AUTHORIZED_CALIBRATION_POINTINGS = frozenset({"P0008"})

def normalize_pointing_id(pointing_id: Any) -> Optional[str]:
    """Resolves string pointing IDs and legacy alias '8' to canonical 'P0008'."""
    ...

def is_trusted_calibration_provenance(
    pointing_id: Any,
    metadata: Optional[Dict[str, Any]] = None,
    secondary_pointing: Optional[Any] = None
) -> bool:
    """Enforces strict calibration allowlist: ONLY canonical P0008 with trusted provenance is eligible."""
    ...
```

### 3.2 Pointing Eligibility Matrix Evaluation
All 14 provenance scenarios required by Section 3 were tested and passed:

| Scenario Description | Pointing Input | Metadata Input | Eligible? | Enforced State | Color Excess | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Canonical P0008, trusted provenance** | `P0008` | `{}` | **True** | `POSSIBLE_IR_EXCESS` | **True** | **PASS** |
| **P0002 blind evaluation cohort** | `P0002` | `{}` | **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **P0009 blind evaluation cohort** | `P0009` | `{}` | **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **P0010 blind evaluation cohort** | `P0010` | `{}` | **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **P9999 unknown pointing identifier** | `P9999` | `{}` | **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **Missing pointing ID (None)** | `None` | `{}` | **False** | `REJECTED_VALUE_ERROR` | **False** | **PASS** |
| **Empty pointing ID string ('')** | `""` | `{}` | **False** | `REJECTED_VALUE_ERROR` | **False** | **PASS** |
| **Malformed pointing ID (int 12345)** | `12345` | `{}` | **False** | `REJECTED_VALUE_ERROR` | **False** | **PASS** |
| **Conflicting pointing/cohort metadata** | `P0008` | `cohort="P0002"` | **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **Caller calibration metadata spoofing** | `P0002` | `role="CALIBRATION"`| **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **Unknown cohort ('UNKNOWN_FIELD')** | `UNKNOWN` | `{}` | **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **Untrusted legacy alias ('8')** | `8` | `untrusted=True` | **False** | `UNVERIFIABLE` | **False** | **PASS** |
| **Trusted legacy alias ('8')** | `8` | Clean provenance | **True** | `POSSIBLE_IR_EXCESS` | **True** | **PASS** |
| **Missing provenance (unattached meta)** | `P0008` | `cohort=None` | **True** | `POSSIBLE_IR_EXCESS` | **True** | **PASS** |

**Remediation Verdict on `FIND-4.9-01`:** Unknown pointing IDs no longer default to permissive behavior. P9999 and all unverified pointings fail closed fail-safe to `UNVERIFIABLE` with `BLIND_COHORT_UNVERIFIED_BASELINE`.

---

## 4. Deep Immutability Contract Architecture (`FIND-4.9-02`)

Full data recorded in [`reports/PHASE_4_10_IMMUTABILITY_TEST_MATRIX.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_IMMUTABILITY_TEST_MATRIX.csv).

### 4.1 Structural Immutability Implementation
`ContinuumEvidenceRecord` was made deeply immutable through three cooperating mechanisms:
1. **Frozen Dataclass:** Declared as `@dataclass(frozen=True)`. Python directly prevents field assignment (`rec.color_excess_detected = True` raises `FrozenInstanceError`).
2. **`ReadOnlyList` Wrapper:** Replaces standard Python lists for `limitation_codes`. Any mutating method call (`append`, `extend`, `insert`, `remove`, `pop`, `clear`, `__setitem__`, `__delitem__`) raises `TypeError`. Implements `__deepcopy__` to allow transparent cloning into standard lists.
3. **`ReadOnlyDict` Wrapper:** Replaces standard dictionaries for `metadata` and `color_indices`. Any mutating method call (`__setitem__`, `__delitem__`, `pop`, `update`, `clear`) raises `TypeError`.
4. **Deep-Freeze Recursive Freezing:** A helper `_deep_freeze_payload()` recursively traverses nested dictionaries and lists upon `__post_init__`, ensuring nested metadata structures cannot be mutated from caller references.
5. **Defensive Serialization:** `rec.to_dict()` clones the record into a completely detached dictionary containing native `list` and `dict` instances. Mutating the serialized dictionary has zero effect on the internal record.

### 4.2 Immutability Test Evaluation
All 16 mutation attack vectors were tested and passed:

| Test ID | Target Attribute | Attack Vector | Expected Exception | Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TEST-IMM-01` | `color_excess_detected` | `rec.color_excess_detected = True` | `FrozenInstanceError` | Blocked: cannot assign to field | **PASSED** |
| `TEST-IMM-02` | `evidence_state` | `rec.evidence_state = 'POSSIBLE_IR'` | `FrozenInstanceError` | Blocked: cannot assign to field | **PASSED** |
| `TEST-IMM-03` | `source_id` | `rec.source_id = 'SRC_SPOOFED'` | `FrozenInstanceError` | Blocked: cannot assign to field | **PASSED** |
| `TEST-IMM-04` | `pointing_id` | `rec.pointing_id = 'P0008'` | `FrozenInstanceError` | Blocked: cannot assign to field | **PASSED** |
| `TEST-IMM-05` | `limitation_codes` | `rec.limitation_codes.clear()` | `TypeError` | Blocked: ReadOnlyList does not support clear | **PASSED** |
| `TEST-IMM-06` | `limitation_codes` | `rec.limitation_codes.remove(...)` | `TypeError` | Blocked: ReadOnlyList does not support remove | **PASSED** |
| `TEST-IMM-07` | `limitation_codes` | `rec.limitation_codes.append(...)` | `TypeError` | Blocked: ReadOnlyList does not support append | **PASSED** |
| `TEST-IMM-08` | `limitation_codes` | `rec.limitation_codes[0] = '...'` | `TypeError` | Blocked: ReadOnlyList does not support assign | **PASSED** |
| `TEST-IMM-09` | `metadata` | `rec.metadata['k'] = v` | `TypeError` | Blocked: ReadOnlyDict does not support assign | **PASSED** |
| `TEST-IMM-10` | `metadata` | `rec.metadata.pop('...')` | `TypeError` | Blocked: ReadOnlyDict does not support pop | **PASSED** |
| `TEST-IMM-11` | `metadata` | `rec.metadata.update(...)` | `TypeError` | Blocked: ReadOnlyDict does not support update | **PASSED** |
| `TEST-IMM-12` | `metadata` | `rec.metadata.clear()` | `TypeError` | Blocked: ReadOnlyDict does not support clear | **PASSED** |
| `TEST-IMM-13` | `metadata.sub_dict` | `rec.metadata['sub_dict']['k'] = v` | `TypeError` | Blocked: ReadOnlyDict does not support assign | **PASSED** |
| `TEST-IMM-14` | `metadata.sub_list` | `rec.metadata['sub_list'].append()` | `TypeError` | Blocked: ReadOnlyList does not support append | **PASSED** |
| `TEST-IMM-15` | `to_dict() copy` | Mutate serialized dictionary | Original Unaltered | Original record strictly unaltered | **PASSED** |
| `TEST-IMM-16` | Deserialization | `ContinuumEvidenceRecord(**d_bad)`| `ValueError` | Reconstruction blocked by `validate()` | **PASSED** |

**Remediation Verdict on `FIND-4.9-02`:** Post-validation mutation of `ContinuumEvidenceRecord` is strictly prohibited across all scalar fields, collections, and nested metadata structures.

---

## 5. Authoritative Validation Boundaries

Full data recorded in [`reports/PHASE_4_10_VALIDATION_BOUNDARY_AUDIT.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_VALIDATION_BOUNDARY_AUDIT.csv).

All 5 authoritative boundaries enforce strict fail-closed validation:
1. **Direct Constructor Boundary (`BOUND-01`):** `ContinuumEvidenceRecord.__post_init__()` validates every instance upon instantiation. Attempting to create an unverified excess record raises `ValueError`.
2. **Deserialization Boundary (`BOUND-02`):** When constructing from a dictionary (`ContinuumEvidenceRecord(**d)`), `__post_init__()` executes and catches tampered payloads.
3. **Scientific Engine Output Boundary (`BOUND-03`):** `EmpiricalContinuumSidecar.evaluate_continuum()` automatically checks `is_trusted_calibration_provenance()`, preventing any non-P0008 source from generating an unverified excess claim.
4. **FUSION-X Multi-Modal Ingestion Boundary (`BOUND-04`):** `FusionEngine.evaluate_source()` calls `continuum_sidecar.validate()` directly at its ingestion gate, blocking invalid instances before multimodal synthesis.
5. **Serializer / Export Boundary (`BOUND-05`):** `rec.to_dict()` safely detaches records, returning isolated clones while preserving immutable internal state.

---

## 6. P0008 Calibration Behavior Preservation

Full data recorded in [`reports/PHASE_4_10_P0008_BEHAVIOR_PRESERVATION.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_P0008_BEHAVIOR_PRESERVATION.csv).

All 25 real P0008 pilot sources acquired in Task 4.5R and classified in Task 4.6 were evaluated before and after remediation:
- **Evidence States:** 100% matched across all 25 sources (`SUPPORTED_PHOTOSPHERIC_CONSISTENCY`, `QUALITY_FLAGGED`, `INSUFFICIENT_PHOTOMETRY`).
- **Confirmation Flags (`color_excess_detected`):** 100% matched (all False for standard stellar locus sources in P0008 pilot).
- **Observed Fluxes ($W2$):** 100% identical.
- **FUSION-X Anomaly Scores:** Identical down to 5 decimal places ($\Delta = 0.000000$).
- **Overall Behavior Identical Flag:** **25/25 Sources (100.0%) Identical**.

---

## 7. FUSION-X Score Invariance & Ranking Stability

Full data recorded in [`reports/PHASE_4_10_FUSION_INVARIANCE.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_FUSION_INVARIANCE.csv).

Twelve sources spanning P0008, P0002, P0009, P0010, P9999, and control sources without sidecars were evaluated in pairs through `FusionEngine`:

$$\max |\Delta| = \max \left| \text{Score}_{\text{with\_sidecar}} - \text{Score}_{\text{without\_sidecar}} \right| = \mathbf{0.000000}$$

- **Score Invariance:** Maintained across all 12 evaluated sources.
- **Rank Shift Count:** Exactly **0** rank shifts.
- **Modality Weights:** Exactly preserved (`spectra=0.35, astrovision=0.30, chronos=0.25, motion=0.10`).
- **Missing Modality Penalties:** Zero unexpected penalties incurred.

---

## 8. Targeted Safety Suite & Full Workspace Regression

Full regression records documented in `tests/test_provenance_allowlist_and_immutability.py` and test run logs:
- **Targeted Remediation Test Suite (`tests/test_provenance_allowlist_and_immutability.py`):** 26 tests covering all Section 7 requirements (Calibration Identity 1-12, Immutability 13-20, Integration & Regression 21-26). **All 26 passed in 2.07s.**
- **Existing Blind Cohort Safety Suite (`tests/test_blind_cohort_promotion_safety.py`):** All 20 Task 4.8R safety tests passed without modification.
- **Existing Continuum Integration Suite (`tests/test_continuum_sidecar_integration.py`):** All 20 tests passed.
- **Full Workspace Test Suite:** 250 tests across 20 test suites:
  - `tests/test_astronomical_crossmatch.py`: 7 passed
  - `tests/test_astrovision_benchmark_v2_engine.py`: 32 passed
  - `tests/test_astrovision_injection_benchmark.py`: 11 passed
  - `tests/test_astrovision_v3_remediation.py`: 5 passed
  - `tests/test_blind_cohort_promotion_safety.py`: 20 passed
  - `tests/test_chronos_x_temporal_eligibility.py`: 17 passed
  - `tests/test_continuum_sidecar_integration.py`: 20 passed
  - `tests/test_infrared_excess_engine.py`: 18 passed
  - `tests/test_legacy_fusion_safety_cleanup.py`: 14 passed
  - `tests/test_multipointing_acquisition_pilot.py`: 10 passed
  - `tests/test_pilot_preparation_and_partitioning.py`: 10 passed
  - `tests/test_provenance_allowlist_and_immutability.py`: 26 passed
  - `tests/test_spectra_task_1_2b_extraction.py`: 8 passed
  - `tests/test_spectra_task_1_2br_audit.py`: 5 passed
  - `tests/test_spectra_task_1_2bs_reconciliation.py`: 6 passed
  - `tests/test_spectra_task_1_2c_calibration.py`: 6 passed
  - `tests/test_spectra_task_1_2d_evaluation.py`: 5 passed
  - `tests/test_spectra_task_1_3a_fusion_contract.py`: 18 passed
  - `tests/test_spectra_task_1_3b_engine_boundary.py`: 8 passed
  - `tests/test_spectra_v2_mask_benchmark.py`: 4 passed

**Total Tests:** **250 Passed / 0 Failed (100.0% Pass Rate)**

---

## 9. Protected Scientific Asset Cryptographic Integrity

Full data recorded in [`reports/PHASE_4_10_FROZEN_ASSET_INTEGRITY.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_FROZEN_ASSET_INTEGRITY.csv).

All 3 protected scientific assets were cryptographically audited before and after remediation:
1. `checkpoints/spectra_masked_ae_v2.pt`:  
   Pre-remediation: `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938`  
   Post-remediation: `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938`  
   Status: **MATCH_PRISTINE**
2. `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json`:  
   Pre-remediation: `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848`  
   Post-remediation: `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848`  
   Status: **MATCH_PRISTINE**
3. `checkpoints/astrovision_spatial_v3.pt`:  
   Pre-remediation: `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99`  
   Post-remediation: `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99`  
   Status: **MATCH_PRISTINE**

**Zero modifications detected across all frozen assets.**

---

## 10. Code Changes & Scope Integrity

Full data recorded in [`reports/PHASE_4_10_CODE_CHANGE_INTEGRITY.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_CODE_CHANGE_INTEGRITY.csv).

Changes were strictly confined to two implementation files and one new test suite:
1. `spectra_engine/continuum_sidecar_interface.py`: Introduced `ReadOnlyList`, `ReadOnlyDict`, `_deep_freeze_payload()`, centralized `normalize_pointing_id()`, `is_trusted_calibration_provenance()`, and converted `ContinuumEvidenceRecord` to a deeply frozen dataclass.
2. `spectra_engine/continuum_sidecar_engine.py`: Replaced denylist logic with `is_trusted_calibration_provenance()` to enforce fail-closed restriction on unknown pointings.
3. `tests/test_provenance_allowlist_and_immutability.py`: Authoritative 26-test safety suite validating calibration allowlist rules and deep immutability guarantees.

---

## 11. Final Verdict

### Verdict: `REMEDIATION_SUCCESSFUL`

Both Task 4.9 adversarial findings are completely resolved:
- `FIND-4.9-01` is eliminated: All unknown pointing identities (e.g. `P9999`) strictly fail closed to `UNVERIFIABLE` with zero promotion capability.
- `FIND-4.9-02` is eliminated: `ContinuumEvidenceRecord` is deeply immutable, prohibiting field mutations and collection alterations while preserving full backward compatibility and FUSION-X invariance.

---

## 12. Deliverable Artifacts Summary

| Deliverable Name | File Path | Purpose |
| :--- | :--- | :--- |
| **Remediation Narrative Report** | [`reports/PHASE_4_10_PROVENANCE_ALLOWLIST_REMEDIATION.md`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_PROVENANCE_ALLOWLIST_REMEDIATION.md) | Comprehensive engineering documentation |
| **Pointing Eligibility Matrix** | [`reports/PHASE_4_10_POINTING_ELIGIBILITY_MATRIX.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_POINTING_ELIGIBILITY_MATRIX.csv) | 14 pointing identity and provenance tests |
| **Immutability Test Matrix** | [`reports/PHASE_4_10_IMMUTABILITY_TEST_MATRIX.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_IMMUTABILITY_TEST_MATRIX.csv) | 16 mutation and collection attack vectors |
| **Validation Boundary Audit** | [`reports/PHASE_4_10_VALIDATION_BOUNDARY_AUDIT.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_VALIDATION_BOUNDARY_AUDIT.csv) | 5 authoritative validation boundaries |
| **P0008 Preservation Matrix** | [`reports/PHASE_4_10_P0008_BEHAVIOR_PRESERVATION.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_P0008_BEHAVIOR_PRESERVATION.csv) | 25 real P0008 pilot source comparisons |
| **FUSION Invariance Matrix** | [`reports/PHASE_4_10_FUSION_INVARIANCE.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_FUSION_INVARIANCE.csv) | Multi-cohort score invariance audit ($\Delta = 0$) |
| **Code Change Integrity** | [`reports/PHASE_4_10_CODE_CHANGE_INTEGRITY.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_CODE_CHANGE_INTEGRITY.csv) | SHA-256 integrity of modified files |
| **Frozen Asset Integrity** | [`reports/PHASE_4_10_FROZEN_ASSET_INTEGRITY.csv`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_FROZEN_ASSET_INTEGRITY.csv) | SHA-256 verification of 3 frozen assets |
| **Audit Manifest JSON** | [`reports/PHASE_4_10_AUDIT.json`](file:///c:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/reports/PHASE_4_10_AUDIT.json) | Structured machine-readable audit manifest |

