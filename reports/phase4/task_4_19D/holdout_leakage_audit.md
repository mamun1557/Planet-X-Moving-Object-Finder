# Independent Holdout Leakage and Provenance Audit
## Phase 4, Task 4.19D — Adaptive Catalog-Aware Masking

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Audit Date:** 2026-11-08  
**Parent Tasks:** Phase 4 Tasks 4.15–4.19C  
**Auditor:** Antigravity Autonomous Scientific Auditor  

---

### 1. Executive Summary & Authoritative Leakage Determination

$$\mathbf{EVALUATION\_COHORT\_DATA\_LEAKAGE\_CONFIRMED}$$

The audit has conclusively determined that **all 1,500 evaluation cutouts** (and specifically the **45 baseline ASTROVISION false alarms**) from Pointings P0002, P0009, and P0010 **directly influenced policy development and parameter selection** in Task 4.19C. 

Consequently, **no independent real-sky holdout dataset was used** to evaluate the performance numbers reported in Task 4.19C. The reported false-positive reductions (Adaptive-A: 2.20%, Adaptive-B: 1.80%) represent **in-sample optimization on previously observed evaluation trials**, not validated out-of-sample generalization.

---

### 2. Answers to the 5 Mandated Audit Questions

#### Question 1: Which records influenced policy development?
**Answer:**  
All **1,500 blind evaluation trials** (500 controls, 500 point injections, 500 extended injections) across Pointings P0002, P0009, and P0010, and specifically the **45 baseline false-positive cutouts** identified in Task 4.11 and Task 4.12. The specific separation distributions and nearest-source distance tables generated from these 45 cutouts directly shaped the concept of catalog-aware dilation.

#### Question 2: Which records influenced parameter selection?
**Answer:**  
The magnitude tiers of Adaptive-A ($G \ge 18.0$, $15.0 \le G < 18.0$, $12.0 \le G < 15.0$, $G < 12.0$) and the radius scaling of Adaptive-B were **explicitly derived from inspecting the optical/infrared brightness and positional separations of the 45 baseline false positives**. Specifically, observing that bright stars ($G < 15$) produced extended residuals beyond 2 pixels led directly to setting $r = 3.0-4.0\text{ px}$ for that specific magnitude range.

#### Question 3: Which records were used for final performance reporting?
**Answer:**  
The exact same **1,500 evaluation trials** from Pointings P0002, P0009, and P0010 were used to report the final metrics (Baseline FPR: 9.00%, Fixed 2px: 3.20%, Adaptive-A: 2.20%, Adaptive-B: 1.80%, Point recovery: 34.80%, Extended recovery: 17.40%).

#### Question 4: Were Adaptive-A or Adaptive-B tuned using the same evaluation cohort?
**Answer:**  
**Yes, conclusively.** There was no separation between parameter development/tuning data and performance reporting data. The evaluation cohort served simultaneously as the training/tuning set and the test set for both adaptive policies.

#### Question 5: Were any thresholds selected after examining evaluation outcomes?
**Answer:**  
**Yes.** The central aperture protection radius ($r_{\rm core} = 1.2\text{ pixels}$) was introduced after observing that unconstrained 3-pixel dilation (Fixed 3px) encroached into the central target aperture of the evaluation injections and degraded genuine anomaly recovery from 34.80% to 34.60%.

---

### 3. Comprehensive Dataset Lineage and Accounting

| Pointing | Partition Role | Subsets | Trial Count | Level-2 FITS WCS | Catalog Crossmatch Available | Historical Usage |
|:---:|:---:|:---:|---:|:---:|:---:|:---|
| **P0001** | `CALIBRATION` | Control (260), Injection (260) | 520 | Yes (72 files) | Pilot Catalogue only (No Task 4.19B WCS) | Used in Task 4.11/4.12 for model threshold calibration ($\tau$) |
| **P0008** | `CALIBRATION` | Control (240), Injection (240) | 480 | Yes (72 files) | Pilot Catalogue only (No Task 4.19B WCS) | Used in Task 4.11/4.12 for model threshold calibration ($\tau$) |
| **P0002** | `EVALUATION` | Control (168), Point (168), Ext (168) | 504 | Yes (72 files) | Full Gaia/2MASS/CatWISE ($N=682,713$) | Evaluated in 4.11-4.19C; used to formulate Adaptive-A/B |
| **P0009** | `EVALUATION` | Control (168), Point (168), Ext (168) | 504 | Yes (72 files) | Full Gaia/2MASS/CatWISE ($N=584,571$) | Evaluated in 4.11-4.19C; used to formulate Adaptive-A/B |
| **P0010** | `EVALUATION` | Control (164), Point (164), Ext (164) | 492 | Yes (72 files) | Full Gaia/2MASS/CatWISE ($N=256,285$) | Evaluated in 4.11-4.19C; used to formulate Adaptive-A/B |
| **TOTAL** | — | — | **2,500** | — | — | **Zero Unused Observations** |

---

### 4. Scientific Conclusion of Phase A
Because every available Level-2 SPHEREx observation in build `l2b-v27-2026-222` has already been utilized—either for model calibration (P0001, P0008) or evaluation benchmarking and masking policy design (P0002, P0009, P0010)—**no independent, unobserved real-sky holdout exists within the active codebase**.

In accordance with mandatory Phase A governance rules:
> *"If all available records have already influenced policy development, declare that no independent holdout exists. Do not relabel previously observed records as independent."*

This audit formally records that **no independent holdout exists** for real-sky observations under build `l2b-v27-2026-222`.
