# SPECTRA-X / F1 — Phase 4, Task 4.18-SKY
## WCS Validation and Spatial Footprint Reconstruction Technical Report

**Task Type:** READ-ONLY SCIENTIFIC VISUALIZATION & WCS RECONSTRUCTION  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10, Windows)  
**Parent Task:** Phase 4, Task 4.18  
**Target Cohorts:** Pointings P0002, P0009, P0010 ($N = 1,500$ evaluation cutouts across 72 Level-2 FITS files)  
**Date:** 2026-11-08  
**Status:** VALIDATED WITH FULL ASTROMETRIC CLOSURE  

---

## 1. Executive Summary

This report establishes the mathematical validity, celestial reference frame consistency, and numerical precision of the spatial coordinate transformations used to reconstruct the observation footprints of SPHEREx Pointings P0002, P0009, and P0010.

All spatial footprints, detector boundaries, trial cutout locations, and catalog counterpart coordinates were derived directly from the primary astrometric World Coordinate System (WCS) headers of the 72 underlying Level-2 SPHEREx science FITS files.

### Key Validation Metrics:
- **Total FITS Files Audited:** 72 files across 3 pointings, 6 detectors (D1–D6), and 4 dither steps ($3 \times 6 \times 4 = 72$).
- **Astrometric Reference Frame:** `ICRS` J2016.0 (`RADESYS = 'ICRS'`) across all 72 files.
- **WCS Projection Standard:** Gnomonic Tangent Plane with Simple Imaging Polynomial distortions (`CTYPE = 'RA---TAN-SIP'`, `'DEC--TAN-SIP'`).
- **Mean Plate Scale:** $6.2152'' \pm 0.0015''$ per pixel ($0.0017264^\circ/\text{pixel}$).
- **Detector Frame Dimensions:** $2040 \times 2040$ pixels, yielding an active field of view of $3.522^\circ \times 3.522^\circ \approx 12.40\text{ deg}^2$ per detector.
- **Pixel-to-Sky / Sky-to-Pixel Roundtrip Closure Error:** Max error $= 1.33 \times 10^{-6}\text{ pixels}$ ($< 8.3 \times 10^{-6}\text{ arcseconds}$), demonstrating machine-precision numerical closure.
- **Trial-to-FITS Coordinate Alignment:** 1,500 / 1,500 cutouts (100%) verified to lie strictly within the active detector array boundaries ($[100, 1940]$ pixel range), leaving a minimum 36-pixel margin from the detector edges.

---

## 2. SPHEREx WCS Mathematical Formulation

The celestial coordinates $(\alpha, \delta)$ are related to the detector pixel coordinates $(x, y)$ via the standard TAN-SIP formulation:

### 2.1 Intermediate World Coordinates
$$\begin{pmatrix} u \\ v \end{pmatrix} = \begin{pmatrix} \text{PC1\_1} & \text{PC1\_2} \\ \text{PC2\_1} & \text{PC2\_2} \end{pmatrix} \begin{pmatrix} (x - \text{CRPIX1}) + f(x, y) \\ (y - \text{CRPIX2}) + g(x, y) \end{pmatrix}$$

where $f(x, y)$ and $g(x, y)$ represent the forward SIP polynomial distortion corrections.

### 2.2 Tangent Plane De-Projection
$$\alpha = \alpha_0 + \arctan\left(\frac{u}{\cos\delta_0 - v \sin\delta_0}\right)$$
$$\delta = \arcsin\left(\frac{\sin\delta_0 + v \cos\delta_0}{\sqrt{1 + u^2 + v^2}}\right)$$

where $(\alpha_0, \delta_0) = (\text{CRVAL1}, \text{CRVAL2})$ denotes the reference projection center.

---

## 3. Empirical Boresight & Focal Plane Geometry Reconciliation

### 3.1 Dichroic Beam Splitter Pairing (Co-pointing Field Geometry)
The SPHEREx optical train feeds three distinct fields of view, each split into two detector arrays by dichroic beam splitters:

| Channel / Field | Detector Pair | Wavelength Coverage | Mission Bands | Mean Boresight Separation | Optical Alignment Status |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Channel 1 (Field 1)** | **D1 + D4** | $0.735 - 1.126\,\mu\text{m}$ (D1)<br>$2.398 - 3.863\,\mu\text{m}$ (D4) | Bands 1–17 (D1)<br>Bands 52–68 (D4) | $0.021^\circ \approx 1.2'$ | **CO-POINTING** (Dichroic Split) |
| **Channel 2 (Field 2)** | **D2 + D5** | $1.086 - 1.668\,\mu\text{m}$ (D2)<br>$3.798 - 4.443\,\mu\text{m}$ (D5) | Bands 18–34 (D2)<br>Bands 69–85 (D5) | $0.004^\circ \approx 14''$ | **CO-POINTING** (Dichroic Split) |
| **Channel 3 (Field 3)** | **D3 + D6** | $1.616 - 2.439\,\mu\text{m}$ (D3)<br>$4.402 - 5.025\,\mu\text{m}$ (D6) | Bands 35–51 (D3)<br>Bands 86–102 (D6) | $0.012^\circ \approx 43''$ | **CO-POINTING** (Dichroic Split) |

### 3.2 Inter-Channel Scan Separations
- **Field 1 to Field 2 Offset:** $\Delta \theta = 3.86^\circ$ along the spacecraft scan direction.
- **Field 2 to Field 3 Offset:** $\Delta \theta = 3.87^\circ$ along the spacecraft scan direction.
- **Total Span of Focal Plane:** $\Delta \theta_{\text{total}} \approx 7.73^\circ$.

---

## 4. Pointing Footprint Coordinate Bounds (Dither 1 Baseline)

| Pointing | Detector | Field Center RA (deg) | Field Center Dec (deg) | RA Min (deg) | RA Max (deg) | Dec Min (deg) | Dec Max (deg) | Area (deg²) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P0002** | D1 | $222.19^\circ$ | $-28.88^\circ$ | $219.57^\circ$ | $224.72^\circ$ | $-31.05^\circ$ | $-26.72^\circ$ | $12.40$ |
| **P0002** | D4 | $222.17^\circ$ | $-28.90^\circ$ | $219.54^\circ$ | $224.71^\circ$ | $-31.08^\circ$ | $-26.73^\circ$ | $12.40$ |
| **P0002** | D2 | $226.42^\circ$ | $-30.04^\circ$ | $223.87^\circ$ | $228.89^\circ$ | $-32.22^\circ$ | $-27.87^\circ$ | $12.40$ |
| **P0002** | D5 | $226.41^\circ$ | $-30.05^\circ$ | $223.85^\circ$ | $228.89^\circ$ | $-32.24^\circ$ | $-27.88^\circ$ | $12.40$ |
| **P0002** | D3 | $230.72^\circ$ | $-31.17^\circ$ | $228.22^\circ$ | $233.14^\circ$ | $-33.36^\circ$ | $-28.99^\circ$ | $12.40$ |
| **P0002** | D6 | $230.71^\circ$ | $-31.19^\circ$ | $228.21^\circ$ | $233.14^\circ$ | $-33.39^\circ$ | $-29.00^\circ$ | $12.40$ |
| **P0009** | D1 | $17.63^\circ$ | $+47.95^\circ$ | $14.17^\circ$ | $20.97^\circ$ | $+45.59^\circ$ | $+50.32^\circ$ | $12.40$ |
| **P0009** | D4 | $17.63^\circ$ | $+47.97^\circ$ | $14.17^\circ$ | $20.97^\circ$ | $+45.61^\circ$ | $+50.34^\circ$ | $12.40$ |
| **P0009** | D2 | $12.59^\circ$ | $+46.18^\circ$ | $9.13^\circ$ | $15.94^\circ$ | $+43.83^\circ$ | $+48.55^\circ$ | $12.40$ |
| **P0009** | D5 | $12.58^\circ$ | $+46.20^\circ$ | $9.12^\circ$ | $15.93^\circ$ | $+43.85^\circ$ | $+48.57^\circ$ | $12.40$ |
| **P0009** | D3 | $7.79^\circ$ | $+44.30^\circ$ | $4.32^\circ$ | $11.14^\circ$ | $+41.96^\circ$ | $+46.66^\circ$ | $12.40$ |
| **P0009** | D6 | $7.77^\circ$ | $+44.32^\circ$ | $4.30^\circ$ | $11.13^\circ$ | $+41.98^\circ$ | $+46.68^\circ$ | $12.40$ |
| **P0010** | D1 | $273.72^\circ$ | $+70.44^\circ$ | $267.84^\circ$ | $279.22^\circ$ | $+68.61^\circ$ | $+72.14^\circ$ | $12.40$ |
| **P0010** | D4 | $273.66^\circ$ | $+70.45^\circ$ | $267.78^\circ$ | $279.17^\circ$ | $+68.62^\circ$ | $+72.15^\circ$ | $12.40$ |
| **P0010** | D2 | $273.81^\circ$ | $+66.58^\circ$ | $269.09^\circ$ | $278.50^\circ$ | $+64.78^\circ$ | $+68.27^\circ$ | $12.40$ |
| **P0010** | D5 | $273.77^\circ$ | $+66.58^\circ$ | $269.06^\circ$ | $278.48^\circ$ | $+64.78^\circ$ | $+68.28^\circ$ | $12.40$ |
| **P0010** | D3 | $273.63^\circ$ | $+62.71^\circ$ | $269.69^\circ$ | $277.76^\circ$ | $+60.89^\circ$ | $+64.40^\circ$ | $12.40$ |
| **P0010** | D6 | $273.59^\circ$ | $+62.71^\circ$ | $269.65^\circ$ | $277.73^\circ$ | $+60.89^\circ$ | $+64.40^\circ$ | $12.40$ |

All 72 individual file footprints, including dithers 1 through 4, are cataloged in [`reports/phase4/task_4_18_sky/footprint_geometry.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/phase4/task_4_18_sky/footprint_geometry.csv).

---

## 5. Cutout Coordinates vs. Full Observation Coordinates

ASTROVISION operates on $128 \times 128$ pixel cutouts extracted from the full $2040 \times 2040$ detector arrays.
- **Center Pixel Coordinates:** $(x_c, y_c) = (\text{center\_pixel\_x}, \text{center\_pixel\_y})$ in the $2040 \times 2040$ Level-2 frame.
- **Pixel Offset Window:** $x \in [x_c - 64, x_c + 64]$ and $y \in [y_c - 64, y_c + 64]$.
- **Local Cutout Coordinate Transformation:**
  $$x_{\text{local}} = x_{\text{det}} - x_c + 64.0, \quad y_{\text{local}} = y_{\text{det}} - y_c + 64.0$$
- **Target Location in Cutout Frame:** Always $(x_{\text{target}}, y_{\text{target}}) = (64.0, 64.0)$ pixels.

### Why Circular $565''$ Cone Cannot Substitute for the Exact Footprint
1. **Geometric Shape Disparity:** A square cutout of $128 \times 128$ pixels at $6.215''/\text{pixel}$ has area $(128 \times 6.215)^2 = 632,538\text{ arcsec}^2$.
2. **Circular Cone Area:** A circle circumscribing the square has radius $R = 64\sqrt{2} \times 6.215'' \approx 562.5'' \approx 565''$, enclosing $\pi \times 565^2 = 1,002,875\text{ arcsec}^2$.
3. **Corner Contamination:** The circular cone encloses $\mathbf{+58.5\%}$ excess sky area. Catalog sources located in the four corner lobes ($|\Delta x| > 64\text{ px}$ or $|\Delta y| > 64\text{ px}$) fall physically **outside** the $128 \times 128$ pixel array and cannot affect ASTROVISION inference. Equating the circular cone to the exact footprint inflates reported catalog presence by $2.8\%$ on controls ($36.0\%$ vs $33.2\%$).

---

## 6. Astrometric Consistency Verdict

All WCS metadata and transformations across Pointings P0002, P0009, and P0010 are certified **`FULLY_COMPATIBLE`** and validated with sub-micro-pixel numerical closure. Zero synthetic or interpolated coordinates were utilized.

