# SPECTRA-X / F1 — Phase 4, Task 4.19A Technical Audit
## Native SPHEREx Source Extraction Feasibility, Pipeline Readiness & Bias Assessment

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Parent Tasks:** Phase 4 Tasks 4.17, 4.18, 4.18-SKY  
**Date:** 2026-11-08  
**Audit Status:** STRICT READ-ONLY ARCHITECTURAL & METHODOLOGICAL AUDIT  

---

## 1. Executive Summary

This technical audit investigates the feasibility, readiness, and scientific governance implications of utilizing native source extraction on Level-2 SPHEREx science FITS images to discover infrared source candidates across the blind evaluation cohort (Pointings P0002, P0009, and P0010).

### Core Audit Verdict:
- **Technical Feasibility:** **`HIGHLY_FEASIBLE_AND_FUNCTIONAL`**  
  An audited, production-grade extraction engine ([`models/spectra/extract_photometry.py`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/spectra/extract_photometry.py)) is already fully implemented, tested, and operational. It successfully extracts calibrated point sources using `photutils.detection.DAOStarFinder` with local annulus background estimation and rigorous variance propagation in $\sim 1.2\text{ seconds}$ per $2040 \times 2040$ detector frame.
- **Scientific Governance & Blind Evaluation Verdict:** **`STRICTLY_BLOCKED_FOR_EVALUATION_LABELING`**  
  Applying native source detection to the *same* evaluation cutouts being evaluated by ASTROVISION introduces fatal **methodological circularity and selection bias**. Detecting an uncataloged flux peak on an evaluation control cutout with DAOStarFinder and using that detection to retroactively explain away an ASTROVISION false alarm is post-hoc label rationalization. Native source extraction cannot serve as an independent ground truth for the blind evaluation cohort.
- **Permitted Operational Role:**  
  Native extraction is valid and recommended exclusively as an **exploratory astronomical catalog generator** for full unmasked exposures, science target discovery, and multi-band spectral extraction outside the blind evaluation verification loop.

---

## 2. Level-2 SPHEREx FITS Product Architecture Audit

All 72 Level-2 FITS files in `data/spherex/multipointing_pilot/level2/` were inspected across their complete Multi-Extension FITS (MEF) structure:

| HDU Index | HDU Name | Data Type | Dimensions | Scientific Content & Integrity Audit |
|:---:|:---:|:---:|:---:|---|
| **0** | `PRIMARY` | PrimaryHDU | `()` | Contains observatory metadata, `OBSID`, `VERSION`, `DATE-OBS`, pipeline version `l2b-v27-2026-222`. |
| **1** | `IMAGE` | ImageHDU | $2040 \times 2040$ (float32) | Calibrated surface brightness in $\text{MJy/sr}$. Clean background subtraction, stable median levels. |
| **2** | `FLAGS` | CompImageHDU | $2040 \times 2040$ (int32) | Comprehensive pixel-level defect flags adhering to `FATAL_FLAG_MASK = 615` (bits 0, 1, 2, 5, 6, 9). |
| **3** | `VARIANCE` | ImageHDU | $2040 \times 2040$ (float32) | Per-pixel statistical variance $(\text{MJy/sr})^2$, propagating detector read noise, dark current, and Poisson variance. |
| **4** | `ZODI` | ImageHDU | $2040 \times 2040$ (float32) | Modeled zodiacal light foreground emission for background reference. |
| **5** | `EPSF` | BinTableHDU | 441 rows $\times$ 11 cols | Effective Point Spread Function empirical model grid sampled across the focal plane. |
| **6** | `WCS-WAVE` | BinTableHDU | 1 row $\times$ 3 cols | Monochromatic wavelength calibration table mapping detector pixel coordinates to channel wavelength. |

### Calibrated Intensity & Variance Sufficiency:
All 72 files possess intact, uncorrupted `IMAGE`, `FLAGS`, and `VARIANCE` extensions. The nominal background variance is strictly positive ($> 0$), providing complete statistical support for sigma-clipped background estimation and signal-to-noise ratio calculation.

---

## 3. Existing Extraction Pipeline Audit (`models/spectra/extract_photometry.py`)

The SPECTRA-X codebase already contains an audited, tested extraction module: [`SPHERExPhotometryExtractor`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/models/spectra/extract_photometry.py).

### 3.1 Algorithmic Architecture
1. **Defect Masking:** Applies `FATAL_FLAG_MASK = 615` to exclude transient glitches, overflows, non-functional pixels, and reference pixels.
2. **Robust Global Background Estimation:** Computes 3-sigma clipped mean, median, and dispersion on the central $1840 \times 1840$ region to avoid detector edge effects.
3. **Point-Source Detection:** Employs `photutils.detection.DAOStarFinder` with:
   - FWHM $= 2.5\text{ pixels}$ (matching the calibrated optical beam).
   - Detection threshold $= 5.0\,\sigma_{\text{bkg}}$.
   - Minimum peak separation $= 4.0\text{ pixels}$ ($24.8''$) to prevent double-counting blended sources.
4. **Annulus-Corrected Aperture Photometry:**
   - Circular aperture radius: $r_{\text{ap}} = 3.0\text{ pixels}$ ($18.6''$).
   - Annulus background: $r_{\text{in}} = 6.0\text{ pixels}$, $r_{\text{out}} = 10.0\text{ pixels}$ with iterative sigma-clipping.
5. **Exact Spectral Coordinate Mapping:**
   - Queries cached calibration maps (`CWAVE` and `CBAND`) for the corresponding detector array, outputting exact central wavelength $\lambda_{\text{cen}}$ and bandpass width $\Delta\lambda$.

### 3.2 Empirical Extraction Benchmark
Execution on `level2_2026W30_1B_0002_1D1_spx_l2b-v27-2026-222.fits` (Pointing P0002, Detector D1, Dither 1):
- **Runtime:** $1.19\text{ seconds}$ for full $2040 \times 2040$ array.
- **Detected Sources:** $500$ source candidates at $5\sigma$ significance.
- **SNR Range:** $\text{SNR} = 111.8$ to $413.2$ on top sources.
- **Astrometric Precision:** Coordinates computed via verified `RA---TAN-SIP` WCS.

---

## 4. Distinguishing Point Sources vs. Diffuse Emission & Systematics

While `DAOStarFinder` is highly capable, native extraction faces critical physical ambiguities in SPHEREx imagery:

1. **Diffuse Cirrus & Dust Structure:**  
   In Pointing P0009 (Perseus Molecular Cloud), cold dust filaments and infrared cirrus exhibit localized high-spatial-frequency knots. Without multi-band spatial decomposition, morphological star finders can misidentify cirrus knots as point-source candidates.
2. **Detector Persistence Ghosts & Latent Charge:**  
   Bright stars in previous dithers leave latent charge trails on HgCdTe arrays (flagged under bit 0 in some pipelines). Unflagged latent charge can mimic faint point sources ($3\sigma - 6\sigma$).
3. **Cosmic Ray Remnants & Glitches:**  
   Single-pixel cosmic ray strikes that survive Level-2 flagging can trigger detection if their spatial profile approximates the $2.5\text{ px}$ FWHM kernel.
4. **Conclusion on Point vs. Diffuse Separation:**  
   Native extraction on a single Level-2 dither cannot definitively distinguish a genuine astrophysical star from a persistent electronic artifact or dust knot without multi-dither co-addition and independent catalog confirmation.

---

## 5. Selection Bias & Governance Invariant in Blind Evaluation

The central question is whether native source extraction can be used to resolve the 33 uncataloged ASTROVISION false positives.

### The Scientific Risk of Circular Post-Hoc Labeling:
$$\begin{array}{rcl}
\text{ASTROVISION False Alarm} & \longrightarrow & \text{High residual } \chi^2 \text{ detected in aperture} \\
\text{DAOStarFinder Native Run} & \longrightarrow & \text{High flux peak detected in same aperture} \\
\text{Flawed Circular Conclusion} & \longrightarrow & \text{"A source is present, so this is no longer a false alarm!"}
\end{array}$$

### Why this is scientifically invalid:
1. **Identical Pixel Data:** Both the autoencoder and DAOStarFinder operate on the exact same digital image array. Any instrumental glitch, readout spike, framing pattern, or unmodeled point spread function wing that fools the autoencoder will also produce a flux excess for DAOStarFinder.
2. **Destruction of Blind Evaluation Independence:** The 500 null controls were selected as representative blank-sky apertures. If we selectively remove or reclassify control cutouts whenever a local source finder detects flux, we bias the control cohort toward abnormally quiet, sub-noise sky, artificially and fraudulently deflating the reported false-positive rate.
3. **Requirement for External Independence:** Only a detection in a completely separate observatory's catalog (Gaia DR3, 2MASS PSC, AllWISE, CatWISE2020) provides an independent astrophysical proof that a celestial object existed at those coordinates prior to SPHEREx observation.

---

## 6. Audit Verdict & Strategic Recommendations

### Verdict:
`TECHNICALLY_FEASIBLE_BUT_GOVERNANCE_BLOCKED_FOR_EVALUATION`

### Recommendations:
1. **Prohibit Native Extraction as Control Ground Truth:** Maintain the strict rule that native SPHEREx extraction cannot reclassify or excuse blind evaluation false alarms.
2. **Prioritize Independent External Catalogs:** Focus coverage expansion efforts entirely on external mid-infrared catalogs (CatWISE2020 and AllWISE), which provide true independent astrophysical validation.
3. **Retain Native Extraction for Survey Discovery:** Utilize `SPHERExPhotometryExtractor` for full-field spectrophotometric catalog generation, where independent catalog cross-validation can be applied post-extraction.

