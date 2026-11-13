# SPECTRA-X: Comprehensive Project Details

**Project Title:** SPECTRA-X — The Human-AI Co-Pilot for Exploring the Changing Infrared Sky  
**Challenge:** Planet X: Moving Object Finder  
**Team Name:** VU_VioNux  
**Lead Track:** NASA International Space Apps Challenge  

---

## 1. System Overview & Problem Statement

The upcoming NASA SPHEREx (Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer) mission will survey the entire celestial sphere every six months across 102 near-infrared spectral bands (0.75–5.0 $\mu$m). While this survey offers unprecedented spectral depth, identifying moving Solar System objects (e.g., Kuiper Belt Objects, extreme trans-Neptunian objects, asteroids, and hypothetical Planet Nine/Planet X) presents severe computational and scientific challenges:

1. **Massive Data Volume:** Hundreds of gigabytes of spectral images per observation cycle.
2. **False Positives:** Dither offsets, detector artifacts, cosmic rays, and stationary stellar variability can mimic genuine orbital motion.
3. **Short-Baseline Ambiguity:** Intra-visit observations ($\Delta t \approx 5$ minutes) record small dithers rather than multi-hour or multi-day orbital arcs, requiring explicit physical safeguards to prevent false discovery claims.

SPECTRA-X solves this challenge by serving as an **input-driven, general-purpose astronomical observatory platform**. It begins in a clean, empty state without hardcoded candidate catalogues, allowing researchers to upload standard astronomical observations, validate astrometric WCS coordinates, execute multi-modal AI screening, and inspect physical evidence through interactive blink comparators and 102-channel spectral viewers.

---

## 2. Intended User Communities

SPECTRA-X is engineered with three user tiers in mind:

1. **NASA & Mission-Related Researchers:**
   - Ingestion of Level-2 pipeline products (FITS format with SIP/TAN WCS distortion matrices).
   - Rapid cross-epoch candidate triage with frozen, reproducible neural models.
   - Batch screening with strict provenance tracking and deterministic audit trails.

2. **Professional Astronomers & Planetary Scientists:**
   - Cross-matching against ESA Gaia DR3, 2MASS, and ALLWISE to rule out stationary stars and proper-motion contaminants.
   - Analysis of Spectral Energy Distributions (SED) across 0.75–5.0 $\mu$m to characterize surface composition, volatile ice absorption bands ($H_2O$, $CO_2$, $CO$), and photometric colors.
   - Extraction of astrometric position angles, angular speeds, and epoch offsets for orbital arc integration.

3. **Citizen Scientists & General Astronomy Enthusiasts:**
   - Intuitive, zero-setup browser interface featuring optical blink animation, sky canvas positioning, and interactive SED inspection.
   - Transparent AI confidence metrics explaining why a candidate was flagged.
   - Human-in-the-loop verification checklist enabling community-driven scientific validation.

---

## 3. Five-Module Scientific Architecture

The core analysis pipeline is decomposed into five specialized, decoupled modules:

### Module 1: ASTROVISION (Spatial Anomaly Detection)
- **Model:** Deep convolutional neural network (`astrovision_spatial_v3.pt`, 3.28 MB).
- **Function:** Inspects 2D image cutouts across spatial dimensions. Evaluates point spread function (PSF) symmetry, signal-to-noise ratio (SNR), and spatial morphology to reject cosmic-ray hits, diffraction spikes, and hot-pixel artifacts.

### Module 2: SPECTRA (Hyperspectral Signal Extraction)
- **Model:** Masked Autoencoder / 1D Spectral Transformer (`spectra_masked_ae_v2.pt`, 0.36 MB).
- **Function:** Analyzes the full 102-channel infrared spectrum ($0.75–5.0\ \mu\text{m}$). Detects anomalous spectral slopes, unusual absorption/emission profiles, or cold thermal continuum consistent with outer Solar System bodies.

### Module 3: CHRONOS-X (Temporal Variability & Photometric Consistency)
- **Function:** Analyzes flux consistency across paired observation epochs. Evaluates whether brightness variations align with rotational modulation, solar phase curve changes, or non-astronomical detector transients.

### Module 4: MOTION-X (Astrometric Motion Engine)
- **Function:** Solves celestial angular displacement ($\Delta\theta$) between paired epochs ($t_A, t_B$) using rigorous spherical trigonometry on tangent planes:
  $$\Delta\theta = \sqrt{(\Delta\alpha \cos\delta)^2 + (\Delta\delta)^2}$$
- Computes position angle ($\theta_{PA}$) and apparent angular velocity ($\mu$ in arcseconds/hour or arcseconds/day).
- **Intra-Visit Dither Safeguard:** Explicitly flags any observation pair with baseline $\Delta t < 0.05$ days ($\approx 72$ minutes) as an intra-visit dither, preventing false classification of dither step offsets as physical orbital velocity.

### Module 5: FUSION-X (Multi-Modal Prioritization Engine)
- **Function:** Combines spatial, spectral, temporal, and motion confidence scores through calibrated heuristic weighting and threshold gating (`spectra_v2_provisional_thresholds_v1.json`). Outputs a normalized candidate priority score ($0.0–1.0$) alongside categorical classification tags (`High-Significance Transient`, `Astrometric Mover`, `Spectral Anomaly`).

---

## 4. Human-in-the-Loop Verification Workflow

Rather than acting as a black-box discovery algorithm, SPECTRA-X enforces human verification before any astronomical claim is accepted:

1. **Observatory Workspace:** System initializes in a clean, empty workspace with active system status and session telemetry.
2. **Data Input Station:** The user uploads paired observations (FITS/CSV/Parquet) into an ephemeral, UUID-isolated session sandbox.
3. **Target Selection & Compatibility:** Target coordinates and headers are parsed; WCS distortion and temporal baselines are validated.
4. **Analysis Execution:** The 5-module engine executes deterministically, producing calibrated confidence scores.
5. **Interactive Evidence Inspection:**
   - **Optical Blink Comparator:** Blinks Epoch A and Epoch B cutouts at adjustable speeds (0.5 Hz – 4.0 Hz) to allow human visual verification of apparent movement against the stationary background starfield.
   - **102-Channel SED Viewer:** Displays observed spectral flux against blackbody/solar continuum models across all SPHEREx bands.
   - **Astrometric Vector Plot:** Highlights the RA/Dec displacement vector and position angle relative to celestial north.
6. **Reviewer Decision & Export:** The analyst records a verdict (`Verified Mover`, `Probable Asteroid`, `Artifact / False Positive`, `Needs Follow-up`) with custom notes, exporting a tamper-evident, JSON/PDF audit package.

---

## 5. Security, Session Isolation, and Reproducibility

- **Session Isolation:** Every user session receives an ephemeral UUID (`SessionManager`). Files are sandboxed in per-session directories and automatically purged after a configurable TTL (1 hour default), ensuring zero data cross-talk between concurrent analysts.
- **Model Immutability:** Neural network checkpoints and threshold tables are cryptographically hashed (SHA-256) and verified prior to pipeline execution.
- **Clean Baseline:** The platform ships with zero embedded mock candidates or pre-loaded proprietary surveys, strictly respecting user data privacy and open-science protocols.

---

## 6. Future Expansion & Mission Readiness

- **SPHEREx Launch Ingestion:** Ready to ingest public SPHEREx data releases via NASA IPAC API endpoints upon satellite commissioning.
- **Orbital Arc Integration:** Planned integration of OpenOrb and NASA JPL Horizons API for automated initial orbit determination (IOD) from 3+ epoch detections.
- **Citizen Science Crowdsourcing:** Modular architecture permits seamless deployment as a public Zooniverse or NASA Citizen Science challenge node.
