# TASK 4.29B — Backend Session Isolation, Motion Analysis Engine & Sample Library API Verification Report

**Project:** Planet X: Moving Object Finder / SPECTRA-X  
**Team:** VU_VioNux (NASA Space Apps Challenge)  
**Task:** Task 4.29B Backend Foundation Implementation  
**Execution Timestamp:** 2026-11-13T12:30:00+06:00  
**Status:** COMPLETE — BACKEND_FOUNDATION_IMPLEMENTED_PENDING_SCIENTIFIC_VALIDATION  

---

## 1. Executive Summary & Verdict

Under Task 4.29B, the foundational backend services required for the new clean, input-driven SPECTRA-X analysis workspace were implemented, isolated, and verified:

1. **SessionManager:** Cryptographically secure UUID-based user session isolation with dedicated ephemeral directory storage under `scratch/sessions/<session_id>/`, 2-hour TTL expiration, and automatic orphan/reaper sweeps.
2. **AstronomicalMotionEngine:** A standalone astronomical motion analysis engine supporting WCS coordinate conversion, periodic Right Ascension wraparound across the $0^\circ/360^\circ$ boundary, spherical great-circle displacement (Haversine/Vincenty), directional position angles, and formal coordinate uncertainty propagation ($\sigma_{\Delta \theta} = \sqrt{\sigma_1^2 + \sigma_2^2}$).
3. **Temporal Eligibility Safeguard:** Strict governance enforcing `INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY` for $\Delta t < 1.0\text{ day}$ and `TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION` for $\Delta t \ge 1.0\text{ day}$.
4. **Sample Library API Contract:** A structured REST catalog interface exposing metadata schemas for future observation pairs, rigorously separating `REAL_INTRA_VISIT` from `SYNTHETIC_ENGINEERING_TEST`.
5. **No Frontend Modifications:** The React frontend was completely untouched in accordance with task instructions.
6. **Bitwise Scientific Immutability:** All frozen weights and calibration thresholds remain 100% unaltered.

### Final Implementation Verdict
```text
================================================================================
FINAL VERDICT: BACKEND_FOUNDATION_IMPLEMENTED_PENDING_SCIENTIFIC_VALIDATION
Status:
  - Backend Architecture: 100% IMPLEMENTED & PASS (19/19 Session/Motion Tests)
  - Full Test Suite: 348/348 PASSED (Zero Regressions)
  - Protected Checkpoint Hashes: 100% BITWISE IDENTICAL
  - Scientific Validation: PENDING (Multi-epoch asteroid recovery remains pending
    acquisition of long-baseline multi-visit flight data in future releases)
================================================================================
```

---

## 2. SessionManager Architecture

Implemented in `observatory/session_manager.py`:

### 2.1 Technical Specifications
- **Identifier Generation:** Cryptographically secure `uuid.uuid4()` strings.
- **State Storage:** In-memory dictionary `_sessions[session_id]` guarded by reentrant thread locking (`threading.RLock()`).
- **Disk Isolation:** Each session receives an isolated ephemeral workspace at:
  ```text
  scratch/sessions/<session_id>/
  ```
- **Time-to-Live (TTL):** Default $7200.0\text{ seconds}$ (2 hours). Every active request automatically calls `.touch()`, updating `last_accessed`.
- **Defensive Deletion & Path-Traversal Guard:** `_is_safe_session_path()` enforces that deletion targets must strictly be subdirectories of `scratch/sessions/` and never the root directory or permanent scientific repositories.
- **Automatic Sweeper:** `cleanup_expired_sessions()` automatically sweeps registered expired sessions as well as unindexed orphan directories older than TTL.

### 2.2 Session Data Structure
```python
@dataclass
class SessionState:
    session_id: str
    created_at: float
    last_accessed: float
    ttl_seconds: float = 7200.0
    dataset_mode: str = "EMPTY"  # "EMPTY" | "SAMPLE" | "USER_UPLOAD"
    sample_pair_id: Optional[str] = None
    target_coordinates: Optional[Dict[str, float]] = None
    uploaded_files: List[Dict[str, Any]] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    selected_candidate_id: Optional[str] = None
    reviews: List[Dict[str, Any]] = field(default_factory=list)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    session_dir: str = ""
```

---

## 3. Standalone Astronomical Motion Analysis Engine

Implemented in `observatory/motion_analysis/`:
- `coordinates.py`: Spherical geometry, RA unwrapping, coordinate validation, WCS transformations.
- `engine.py`: Authoritative `AstronomicalMotionEngine` coordinating astrometric metrics, error propagation, and dither safeguards.

### 3.1 Mathematical Formulations & Physical Units

| Metric | Mathematical Formula | Physical Units | Assumptions / Conventions |
|:---|:---|:---:|:---|
| **RA Wraparound Difference** | $\Delta \alpha_{\text{wrapped}} = ((\alpha_2 - \alpha_1 + 180^\circ) \pmod{360^\circ}) - 180^\circ$ | Degrees ($^\circ$) | Bounded to $[-180^\circ, +180^\circ]$. |
| **Spherical Angular Separation** | $a = \sin^2\left(\frac{\Delta \delta}{2}\right) + \cos(\delta_1)\cos(\delta_2)\sin^2\left(\frac{\Delta \alpha_{\text{wrapped}}}{2}\right)$<br>$\Delta \theta = 2 \arcsin(\min(1, \sqrt{a})) \times \frac{180}{\pi} \times 3600$ | Arcseconds ($''$) | Great-circle Haversine formula on celestial sphere. |
| **Position Angle (Bearing)** | $\theta_{\text{PA}} = \text{atan2}\left(\sin \Delta \alpha \cos \delta_2, \cos \delta_1 \sin \delta_2 - \sin \delta_1 \cos \delta_2 \cos \Delta \alpha\right)$ | Degrees ($^\circ$) | Measured North through East $[0.0^\circ, 360.0^\circ)$. |
| **Time Baseline** | $\Delta t_{\text{hours}} = \vert MJD_2 - MJD_1 \vert \times 24.0$<br>$\Delta t_{\text{days}} = \vert MJD_2 - MJD_1 \vert$ | Hours / Days | Modified Julian Date or ISO 8601 UTC. |
| **Angular Motion Rate (Hourly)** | $\omega_{\text{hour}} = \frac{\Delta \theta}{\Delta t_{\text{hours}}}$ | $\text{arcsec/hour}$ | Standard Near-Earth Object / fast transient unit. |
| **Angular Motion Rate (Daily)** | $\omega_{\text{day}} = \frac{\Delta \theta}{\Delta t_{\text{days}}}$ | $\text{arcsec/day}$ | Standard Main-Belt Asteroid / KBO / secular unit. |
| **Coordinate Uncertainty** | $\sigma_{\Delta \theta} = \sqrt{\sigma_1^2 + \sigma_2^2}$ | Arcseconds ($''$) | Standard Gaussian error propagation of centroid errors. |
| **Significance SNR** | $\text{SNR} = \frac{\Delta \theta}{\sigma_{\Delta \theta}}$ | Dimensionless | Significance of measured displacement above noise. |

---

## 4. Temporal Eligibility & Fail-Closed Safeguard Behavior

### 4.1 Temporal Boundary Governance
The engine strictly evaluates the observation baseline $\Delta t$:
1. **Intra-Visit Dither ($\Delta t < 1.0\text{ day}$):**
   - **Status:** `INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY`
   - **`is_secular_motion_eligible`:** `False`
   - **Limitation Codes:** `["INTRA_VISIT_DITHER", "SECULAR_MOTION_INELIGIBLE"]`
   - **Scientific Rationale:** High-cadence SPHEREx dither steps ($\Delta t \approx 2.15\text{ to }6.45\text{ minutes}$) induce sub-pixel shifts that mimic moving sources. The engine reports the measured displacement strictly for registration and PSF diagnostics, refusing to label it as astronomical movement.
2. **Multi-Day Temporal Baseline ($\Delta t \ge 1.0\text{ day}$):**
   - **Status:** `TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION`
   - **`is_secular_motion_eligible`:** `True`
   - **Limitation Codes:** `["REQUIRES_ASTROMETRIC_VETTING"]`
   - **Scientific Rationale:** Meets the minimum temporal threshold for secular motion testing.

### 4.2 Fail-Closed Error Codes
| Condition | Error Code | HTTP Status | Response Behavior |
|:---|:---|:---:|:---|
| Coordinate Dec out of $[-90^\circ, +90^\circ]$ or non-finite | `INVALID_COORDINATES` | 422 | Execution halts; returns explicit diagnostic. |
| Missing or unparseable timestamps | `INVALID_TIMESTAMP` | 422 | Fails closed; zero fabricated time differences. |
| Missing or uncalibrated WCS | `MISSING_WCS` | 422 | Fails closed; requires calibrated astrometry. |
| Missing observation epoch | `INSUFFICIENT_OBSERVATIONS` | 422 | Requires two valid epochs for comparison. |
| Non-positive or NaN uncertainty | `UNCERTAINTY_UNAVAILABLE` | 422 | Refuses to calculate uncalibrated SNR. |

---

## 5. Sample Library API Contract

Implemented in `observatory/sample_library.py`:

### 5.1 Dataset Classification Separation
- **`REAL_INTRA_VISIT`:** Real observations from SPHEREx Level-2 pointings (P0001, P0003). Never exposes synthetic ground truth.
- **`SYNTHETIC_ENGINEERING_TEST`:** Injected test cases with explicit ground truth for algorithmic calibration. Must have `has_ground_truth_motion = True` and `is_synthetic = True`.

### 5.2 API Routes Added to `observatory/server.py`
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/session/create` | Spawns a new isolated session and scratch directory. |
| `GET` | `/api/session/info` | Retrieves session status, active files, and TTL remaining. |
| `POST` | `/api/session/reset` | Clears session workspace back to `EMPTY`. |
| `DELETE` | `/api/session` | Terminates session and permanently deletes scratch files. |
| `POST` | `/api/motion/analyze` | Computes motion displacement, rates, and dither eligibility. |
| `GET` | `/api/samples/list` | Returns list of available sample pairs (filtered by class). |
| `GET` | `/api/samples/get` | Retrieves metadata for a specific sample pair ID. |
| `POST` | `/api/samples/load` | Loads a sample pair into the caller's isolated session. |

---

## 6. Automated Test Results & Verification Metrics

A dedicated test suite was implemented in `tests/test_session_and_motion_engine.py` featuring 19 comprehensive unit and integration tests.

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X
collected 19 items

tests/test_session_and_motion_engine.py::TestSessionManager::test_cross_session_file_access_prevention PASSED [  5%]
tests/test_session_and_motion_engine.py::TestSessionManager::test_path_traversal_defense PASSED [ 10%]
tests/test_session_and_motion_engine.py::TestSessionManager::test_session_creation_and_isolation PASSED [ 15%]
tests/test_session_and_motion_engine.py::TestSessionManager::test_session_ttl_expiration_and_cleanup PASSED [ 21%]
tests/test_session_and_motion_engine.py::TestCoordinateAndMotionCalculations::test_coordinate_uncertainty_propagation PASSED [ 26%]
tests/test_session_and_motion_engine.py::TestCoordinateAndMotionCalculations::test_motion_rate_unit_conversions PASSED [ 31%]
tests/test_session_and_motion_engine.py::TestCoordinateAndMotionCalculations::test_ra_wraparound_at_meridian PASSED [ 36%]
tests/test_session_and_motion_engine.py::TestCoordinateAndMotionCalculations::test_spherical_angular_separation PASSED [ 42%]
tests/test_session_and_motion_engine.py::TestIntraVisitSafeguardAndFailClosed::test_intra_visit_dither_safeguard PASSED [ 47%]
tests/test_session_and_motion_engine.py::TestIntraVisitSafeguardAndFailClosed::test_invalid_coordinates_fail_closed PASSED [ 52%]
tests/test_session_and_motion_engine.py::TestIntraVisitSafeguardAndFailClosed::test_missing_timestamp_fails_closed PASSED [ 57%]
tests/test_session_and_motion_engine.py::TestIntraVisitSafeguardAndFailClosed::test_missing_wcs_fails_closed PASSED [ 63%]
tests/test_session_and_motion_engine.py::TestIntraVisitSafeguardAndFailClosed::test_temporally_eligible_multi_day_baseline PASSED [ 68%]
tests/test_session_and_motion_engine.py::TestSampleLibraryCatalog::test_real_intra_visit_has_no_synthetic_vector PASSED [ 73%]
tests/test_session_and_motion_engine.py::TestSampleLibraryCatalog::test_synthetic_engineering_sample_has_explicit_ground_truth PASSED [ 78%]
tests/test_session_and_motion_engine.py::TestHTTPServerSessionAndMotionRoutes::test_http_motion_analysis_intra_visit PASSED [ 84%]
tests/test_session_and_motion_engine.py::TestHTTPServerSessionAndMotionRoutes::test_http_motion_analysis_multi_day PASSED [ 89%]
tests/test_session_and_motion_engine.py::TestHTTPServerSessionAndMotionRoutes::test_http_sample_library_endpoints PASSED [ 94%]
tests/test_session_and_motion_engine.py::TestHTTPServerSessionAndMotionRoutes::test_http_session_lifecycle PASSED [100%]

============================= 19 passed in 6.39s ==============================
```

### Full Project Regression Test Run
The entire pytest suite across the repository was executed:
- **Total Tests:** 348
- **Passed:** 348 (100%)
- **Failed:** 0
- **Regression Count:** 0

---

## 7. Protected Scientific Asset Hash Verification

All frozen model checkpoints and calibration thresholds were verified before and after implementation:

| Asset File Path | Baseline SHA-256 Hash | Post-Implementation SHA-256 Hash | Status |
|:---|:---|:---|:---:|
| `checkpoints/astrovision_spatial_v3.pt` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | **IDENTICAL** |
| `checkpoints/spectra_masked_ae_v2.pt` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | **IDENTICAL** |
| `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | **IDENTICAL** |

---

## 8. Modified & Newly Created File Inventory

| File Path | Status | Purpose / Changes |
|:---|:---:|:---|
| `observatory/session_manager.py` | `NEW` | UUID session manager, ephemeral storage isolation, TTL reaper. |
| `observatory/motion_analysis/__init__.py` | `NEW` | Astronomical motion analysis package root. |
| `observatory/motion_analysis/coordinates.py` | `NEW` | Spherical geometry, RA wraparound, coordinate validation, WCS mapping. |
| `observatory/motion_analysis/engine.py` | `NEW` | AstronomicalMotionEngine, rate calculations, dither safeguards. |
| `observatory/sample_library.py` | `NEW` | Sample pair metadata schema, registry, and catalog API. |
| `observatory/server.py` | `MODIFIED` | Integrated session manager, motion route, and sample library endpoints. |
| `tests/test_session_and_motion_engine.py` | `NEW` | 19 automated unit and mock HTTP integration tests. |
| `docs/verification/task_4_29B/task_4_29B_backend_foundation_report.md` | `NEW` | Authoritative verification report. |

---

## 9. Known Limitations

1. **Absence of Real Multi-Month Flight Data:** While the backend motion engine is fully operational and mathematically tested, all 283 overlapping same-detector pairs on disk remain intra-visit dither pairs. Multi-epoch secular motion testing currently requires the synthetic engineering pairs to be curated under Task 4.29C.
2. **Ephemeral Memory Storage:** The session registry resides in server process memory. A process restart terminates existing active sessions, automatically recreating clean empty sessions on subsequent user visits.

---

## 10. Explicit Declaration & Next Steps

Task 4.29B is complete. The backend foundation for session isolation, astronomical motion analysis, and sample library querying is fully functional, fail-closed, and covered by 100% passing tests.

**Implementation Verdict: BACKEND_FOUNDATION_IMPLEMENTED_PENDING_SCIENTIFIC_VALIDATION**  
*Execution halted. Task 4.29C will not commence until user instruction.*

