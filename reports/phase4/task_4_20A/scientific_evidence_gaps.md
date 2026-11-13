# Scientific Evidence Gaps and Verification Blockers
## Phase 4, Task 4.20A — Model Capability Improvement Audit

**Module:** SPECTRA-X Multimodal Discovery Pipeline (F1 Architecture)  
**Pipeline Build:** `l2b-v27-2026-222`  
**Audit Date:** 2026-11-08  

---

### 1. Executive Summary

This document establishes the scientific evidence gaps, observational limitations, and theoretical boundaries across all five SPECTRA-X discovery modules. It distinguishes between **pure engineering limitations** (which can be resolved prior to the November 10 deadline) and **fundamental scientific blockers** (which require new on-orbit observations, flight PSF characterization, or multi-epoch revisit data that do not exist in the current repository).

---

### 2. Module-by-Module Evidence Gaps

#### Module 1: ASTROVISION (Spatial Infrared Anomaly Detection)
- **Primary Scientific Gap: Beam Confusion at 6.215 arcsec/pixel:**  
  SPHEREx's native spatial resolution ($\sim 6.2''/\text{pixel}$, effective PSF FWHM $6-8''$) causes severe stellar blending in dense fields. Multiple optical stars fall within a single pixel footprint. A detected spatial anomaly at $(x, y)$ cannot be uniquely attributed to an individual catalog counterpart without sub-pixel deconvolution.
- **Detector 1 Dark-Current Drift & Zodi Fluctuation:**  
  Detector 1 generates $42.2\%$ of all baseline false positives ($19/45$). Task 4.12 demonstrated that D1 suffers from elevated background noise variance and zodiacal light gradients that inflate spatial reconstruction $\chi^2$.
- **Extended Anomaly Recovery Deficit:**  
  While point-source recovery is $34.80\%$ (AUROC: $0.8040$), extended-source recovery is only $17.40\%$ (AUROC: $0.7064$). The current $32 \times 32$ patch autoencoder with localized $3 \times 3$ kernels has a limited receptive field that struggles to distinguish broad, diffuse astrophysical emission from low-frequency background gradients.

#### Module 2: SPECTRA (102-Channel Spectral Anomaly Detection)
- **Primary Scientific Gap: Continuum Extraction Extrapolation Limits:**  
  The 102 spectral channels span $0.75\,\mu\text{m}$ to $5.00\,\mu\text{m}$. Fitting a Rayleigh-Jeans photospheric baseline requires at least 8 uncontaminated continuum channels. In heavily obscured young stellar objects (YSOs) or cool brown dwarfs ($T_{\rm eff} < 1000\text{ K}$), water and methane absorption bands blanket the continuum, making baseline definition degenerate.
- **Telluric & Edge Noise Covariance:**  
  Channels 1–5 ($0.75-0.85\,\mu\text{m}$) and channels 98–102 ($4.8-5.0\,\mu\text{m}$) exhibit elevated detector read noise and fringe variance. Treating spectral channel uncertainties as diagonal (independent) ignores inter-channel covariance introduced by the SPHEREx Linear Variable Filter (LVF).

#### Module 3: CHRONOS-X (Temporal Differencing & Transient Discovery)
- **CRITICAL HARD BLOCKER: Complete Absence of Multi-Epoch Repeat Visits:**  
  The repository contains **zero multi-day or multi-week repeat observations**. All available image pairs are short-cadence dithers separated by only $2.15$ to $6.45\text{ minutes}$.
  - *Implication:* CHRONOS-X **cannot be scientifically validated for secular variable stars, novae, or supernovae** using existing real-sky data. Any claim of transient discovery capability on real observations is scientifically invalid.
- **Dipole Residual Artifacts from Astrometric Jitter:**  
  Slight sub-pixel pointing errors between dither frames ($\Delta \theta \sim 0.2-0.5\text{ pixels}$) produce classic positive/negative dipole artifacts when differencing bright point sources. Without automated phase-correlation sub-pixel alignment, dipoles trigger false transient alerts.

#### Module 4: MOTION-X (Astrometric Motion & Ephemeris Validation)
- **CRITICAL HARD BLOCKER: Zero Solar System Small Bodies in Available FOVs:**  
  An exhaustive ephemeris query against NASA/JPL Horizons confirmed that **zero cataloged asteroids, comets, or near-Earth objects (NEOs) resided inside the field of view** of the five pilot pointings (all targets were $>40^\circ$ away).
  - *Implication:* Real-world asteroid detection cannot be verified on real-sky flight data.
- **Unimplemented Ephemeris Stub:**  
  The method `match_known_minor_planets()` is currently an empty placeholder returning `None`. While Gaia proper-motion propagation is verified ($0.08''$ precision), minor-planet identification is non-functional.
- **Single-Epoch Tracklet Limit:**  
  Detections from a single dither exposure cannot establish an orbital arc. A moving object requires associating detections across at least 3 dither frames separated by several minutes.

#### Module 5: FUSION-X (Multimodal Anomaly Prioritization)
- **Primary Scientific Gap: Heuristic Scores vs. Calibrated Probabilities:**  
  FUSION-X currently computes a weighted linear combination of normalized module scores. These scores reflect heuristic ranking metrics, **not true Bayesian posterior probabilities of astrophysical anomaly**.
- **Missing Modality Weight Renormalization:**  
  When a candidate lacks temporal differencing data (e.g. single-exposure pointing), FUSION-X re-normalizes weights across available modalities. However, because spatial and spectral anomaly scores have different dynamic ranges and noise tails, static linear reweighting distorts rank order between complete and incomplete candidates.

---

### 3. Summary of Feasibility Boundaries Before November 10

| Module | Core Gap | Solvable Before Nov 10? | Required Action |
|:---|:---|:---:|:---|
| **ASTROVISION** | D1 false alarms & thresholding | **YES (Engineering)** | Formalize detector-stratified thresholds and Adaptive-A shadow interface. |
| **ASTROVISION** | Extended source recovery (<20%) | **NO (Requires Training)** | Requires multi-scale patch retraining (post-freeze). |
| **SPECTRA** | Multi-catalog IR excess integration | **YES (Engineering)** | Automate 2MASS/CatWISE flux ingestion in continuum sidecar. |
| **CHRONOS-X** | Sub-pixel alignment dipoles | **YES (Engineering)** | Implement phase-correlation sub-pixel registration. |
| **CHRONOS-X** | Multi-epoch transient validation | **HARD BLOCKED (Data)** | Zero repeat observations in repository; require new survey pointings. |
| **MOTION-X** | Minor planet stub | **YES (Engineering)** | Replace stub with offline Keplerian ephemeris matcher. |
| **MOTION-X** | Real asteroid flight validation | **HARD BLOCKED (Data)** | Zero asteroids in pilot FOVs; require synthetic injection benchmark. |
| **FUSION-X** | Uncalibrated heuristic scores | **YES (Engineering)** | Implement empirical isotonic calibration and evidence provenance schema. |
