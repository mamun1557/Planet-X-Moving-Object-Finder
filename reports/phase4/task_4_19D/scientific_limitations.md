# Scientific Limitations & Methodological Constraints
## Phase 4, Task 4.19D — Independent Holdout Validation & Leakage Audit

**Pipeline Build:** `l2b-v27-2026-222`  
**Parent Tasks:** Phase 4 Tasks 4.15–4.19D  

---

### 1. Inherent Data Availability Bottleneck
The foremost scientific limitation governing ASTROVISION validation in pipeline build `l2b-v27-2026-222` is the finite volume of available Level-2 SPHEREx observations. The entire controlled pilot campaign comprises exactly five pointings:
- **P0001 & P0008:** Ingested during Phase 4 Task 4.11 and Task 4.12 as the designated CALIBRATION partition to calibrate detector-stratified anomaly thresholds $\tau$.
- **P0002, P0009 & P0010:** Ingested as the blind EVALUATION cohort to benchmark AUROC, precision, and empirical false-positive rate.

No additional unobserved pointings exist within this pipeline build. Consequently, true independent holdout validation—evaluating frozen adaptive masking policies on an observation cohort completely unobserved during both model training and policy formulation—is **physically impossible** without acquiring new external flight data.

---

### 2. Evaluation Set Overfitting and Parameter Leakage
In Task 4.19C, candidate adaptive masking policies (Adaptive-A and Adaptive-B) were developed by analyzing the nearest-source separations, Gaia $G$ magnitudes, and CatWISE/2MASS infrared flux distributions of the **45 baseline false alarms** residing in Pointings P0002, P0009, and P0010.

When the performance of Adaptive-A is reported as reducing FPR from $9.00\%$ to $2.20\%$ on that same cohort:
1. The reported metric measures **in-sample explanatory power**, not validated out-of-sample generalization.
2. The magnitude tiers ($G < 15, G < 18$) reflect the empirical stellar density and magnitude distribution of Pointings P0002, P0009, and P0010. In fields with fundamentally different stellar populations (e.g. dense Baade's Window in the Galactic Center or extremely sparse deep extragalactic fields), these specific magnitude thresholds may be suboptimal.

---

### 3. Cross-Pointing and Cross-Detector Sensitivities
1. **Galactic Density Variation:**
   Pointing P0009 (high stellar crowding) contains an average of $1,160$ catalog stars per cutout, whereas Pointing P0010 (deep Southern celestial hemisphere, $\delta \approx -60^\circ$) contains $521$ stars per cutout. In P0010, the baseline false-positive count is only 7, whereas in P0009 it is 24. While adaptive masking suppresses false alarms across all three pointings, the statistical power to verify generalization in low-density fields is constrained by small sample sizes ($N=7$).
2. **Detector-Specific Distribution Shift:**
   Detector 1 generates $42.2\%$ of all baseline false positives (19/45), whereas Detector 3 generates only 2. Detector 1 false alarms are strongly co-located with stars ($78.9\%$ within $1\text{ px}$), whereas Detector 5 exhibits weaker stellar co-location ($33.3\%$). A uniform masking policy cannot fully compensate for underlying detector-specific hardware noise variances without detector-specific mask scaling.

---

### 4. Policy Promotion Boundary
Promoting Adaptive-A or Adaptive-B to production ASTROVISION without independent holdout validation would violate strict production-preserving governance rules. The policies must remain strictly in shadow-evaluation mode until verified against Day-1 flight observations.
