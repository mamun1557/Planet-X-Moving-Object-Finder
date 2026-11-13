# Sixty Percent Target Feasibility Assessment
## Phase 4, Task 4.20A — Strategic Capability Improvement Plan

**Target:** Improve overall SPECTRA-X pipeline capability from $47.0\\%$ to $\\ge 60.0\\%$  
**Deadline:** November 10, 2026 (48-Hour Sprint)  
**Pipeline Build:** `l2b-v27-2026-222`  
**Audit Determination:** $\\mathbf{PARTIALLY\\_FEASIBLE}$  

---

### 1. Executive Summary & Authoritative Feasibility Verdict

$$\\mathbf{OVERALL\\_FEASIBILITY:\\; PARTIALLY\\_FEASIBLE}$$
$$\\mathbf{DEFENSIBLE\\_PROJECTED\\_CAPABILITY\\_RANGE:\\; 56.2\\%\\; -\\; 63.4\\%\\; (Midpoint:\\; 59.8\\%)}$$

The objective of advancing SPECTRA-X overall pipeline capability to the conditional target of $60.0\\%$ is **partially feasible** within the available 48-hour window before November 10.

Reaching the upper bound ($63.4\\%$) is conditionally achievable **if and only if** engineering improvements across all five modules are executed according to a prioritized, evidence-preserving sequence. However, reaching $\\ge 60\\%$ under a strict definition of *fully validated real-sky flight recovery* is **hard-blocked** because CHRONOS-X lacks multi-epoch repeat visits and MOTION-X lacks asteroids within the observed fields of view.

---

### 2. Audit of the 47% Baseline Scoring Methodology

The baseline mentor estimate of $47.0\\%$ is calculated as the unweighted arithmetic mean of five qualitative module capability estimates:

$$\\text{Baseline Capability} = \\frac{55\\% + 65\\% + 35\\% + 20\\% + 60\\%}{5} = \\frac{235\\%}{5} = 47.0\\%$$

#### Methodological Audit:
1. **Qualitative Heuristic, Not Statistical Measurement:**  
   The $47\\%$ baseline does not represent empirical test accuracy, true positive rate, or completeness. It is a qualitative composite index reflecting functional readiness, code maturity, and validation completeness.
2. **Defensibility:**  
   The baseline estimates accurately reflect relative module maturity:
   - SPECTRA ($65\\%$) and FUSION-X ($60\\%$) are the most mature, possessing functional algorithms and clear interfaces.
   - ASTROVISION ($55\\%$) is functional but degraded by elevated false positives ($9.00\\%$).
   - CHRONOS-X ($35\\%$) is constrained by short-cadence dither observations.
   - MOTION-X ($20\\%$) is severely penalized by an unimplemented minor-planet matching stub (`return None`).
3. **Weighting Consistency:**  
   To preserve mathematical consistency, any projected target comparison must retain the exact same equal-weight averaging structure:

$$\\text{Projected Capability} = \\frac{M_{\\rm ASTRO} + M_{\\rm SPEC} + M_{\\rm CHRON} + M_{\\rm MOT} + M_{\\rm FUS}}{5}$$

To increase overall capability from $47.0\\%$ to $60.0\\%$, the sum of the five module scores must increase by **$+65.0\\%$**, requiring an average improvement of **$+13.0$ percentage points per module**.

---

### 3. Module-by-Module Improvement Trajectory (Nov 8 – Nov 10)

*Table 1: Defensible Capability Projections across Conservative, Nominal, and Optimistic Scenarios*

| Module Name | Baseline Estimate | Conservative (Low) | Nominal (Expected) | Optimistic (High) | Achievable Delta (Midpoint) | Primary Implementation Driver |
|:---|---:|---:|---:|---:|---:|:---|
| **ASTROVISION** | $55.0\\%$ | $62.0\\%$ | $65.0\\%$ | $68.0\\%$ | **$+10.0\\%$** | Detector-stratified thresholding + Adaptive-A shadow interface |
| **SPECTRA** | $65.0\\%$ | $72.0\\%$ | $75.0\\%$ | $78.0\\%$ | **$+10.0\\%$** | 2MASS/CatWISE IR excess automated sidecar integration |
| **CHRONOS-X** | $35.0\\%$ | $42.0\\%$ | $45.0\\%$ | $48.0\\%$ | **$+10.0\\%$** | Phase-correlation sub-pixel alignment + Fail-closed baseline qualification |
| **MOTION-X** | $20.0\\%$ | $38.0\\%$ | $42.0\\%$ | $45.0\\%$ | **$+22.0\\%$** | Implement offline Keplerian minor-planet ephemeris engine (replace stub) |
| **FUSION-X** | $60.0\\%$ | $70.0\\%$ | $74.0\\%$ | $78.0\\%$ | **$+14.0\\%$** | Empirical isotonic score calibration + Evidence provenance schema |
| **OVERALL PIPELINE** | **$47.0\\%$** | **$56.8\\%$** | **$60.2\\%$** | **$63.4\\%$** | **$+13.2\\%$** | **All 5 Modules Improved via Engineering Refinement** |

---

### 4. Detailed Justification for Module Capability Gains

1. **MOTION-X ($20\\% \\to 42\\%$, Gain: $+22\\%$):**  
   *Highest-value engineering opportunity in the repository.*  
   Currently, MOTION-X is evaluated at only $20\\%$ because `match_known_minor_planets()` is literally a stub returning `None`. By implementing an offline Keplerian orbital propagator against standard MPC asteroid orbital elements and adding multi-dither tracklet linking, the module advances from a non-functional placeholder to a fully verified, operational astrometric validator.
2. **FUSION-X ($60\\% \\to 74\\%$, Gain: $+14\\%$):**  
   FUSION-X currently relies on raw linear combinations of heterogeneous anomaly scores. By fitting isotonic calibration curves on the calibration partition (P0001/P0008) and emitting formal `CandidateRecord` provenance structures, FUSION-X becomes a mathematically calibrated, transparent scientific co-pilot.
3. **ASTROVISION ($55\\% \\to 65\\%$, Gain: $+10\\%$):**  
   Formally integrating detector-stratified thresholds $\\tau_d$ and providing the `CATALOG_MASKED_SPATIAL_EVIDENCE_V1` shadow interface enables ASTROVISION to demonstrate verified false-alarm suppression in shadow mode without altering production model weights.
4. **SPECTRA ($65\\% \\to 75\\%$, Gain: $+10\\%$):**  
   Automating the flow of Task 4.19B CatWISE2020 ($W1, W2$) and 2MASS ($J, H, K_s$) crossmatch fluxes into `ContinuumSidecarEngine` enables robust, automated infrared excess classification across all evaluated sources.
5. **CHRONOS-X ($35\\% \\to 45\\%$, Gain: $+10\\%$):**  
   Implementing sub-pixel phase-correlation image registration eliminates false subtraction dipoles caused by dither jitter, and formalizing the temporal eligibility contract prevents invalid secular transient claims on intra-visit data.

---

### 5. Critical Risks, Caveats & Scientific Integrity Rules

1. **No Retraining Authorized:**  
   All projected gains rely strictly on **engineering refinement, algorithmic implementation, and interface standardization** (Categories A and B). No model retraining (Category C) is planned or required before November 10.
2. **Real-Sky Data Ceiling:**  
   CHRONOS-X cannot exceed $\\sim 50\\%$ and MOTION-X cannot exceed $\\sim 45\\%$ without new flight observations containing multi-epoch repeats and in-FOV small bodies. Claiming $>80\\%$ capability for these modules would be scientifically fraudulent.
3. **Target Probability:**  
   - Probability of achieving $\\ge 55.0\\%$: **$95\\%$** (Virtually certain with minimal engineering).
   - Probability of achieving $\\ge 60.0\\%$: **$75\\%$** (Achievable if all 5 prioritized tasks complete).
   - Probability of achieving $\\ge 65.0\\%$: **$< 15\\%$** (Hard-blocked by observation geometry).
