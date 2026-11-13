# SPECTRA-X: CHRONOS-X Temporal Validation & 152.4σ Residual Investigation

## 1. Executive Summary & Pair Classification

**Logical Classification**: All 44 identified candidate multi-epoch pairs are strictly classified as **`short_cadence_dither_pairs`**.
- **Intra-Release QR2 Pairs**: 20 pairs spanning Dithers 1D through 4D ($\Delta t = 2.15$ to $6.45$ minutes; separation $0.20^\circ$ to $1.02^\circ$).
- **Intra-Release QR3 Pairs**: 24 pairs spanning Dithers 1D through 4D ($\Delta t = 2.15$ to $6.45$ minutes; separation $0.20^\circ$ to $1.59^\circ$).
- **Cross-Release Pairs (QR2 vs QR3)**: **0 pairs included**. Cross-release comparisons between April 2025 (Pipeline v20) and July 2026 (Pipeline v27) are strictly excluded from temporal transient analysis to avoid systematic calibration contamination.

## 2. In-Depth Scientific Investigation of the 152.2σ / 152.4σ Residual

In the first-pass audit, image differencing on the pair:
- Epoch 1: `level2_2025W17_4B_0001_2D2_spx_l2b-v20-2025-240.fits`
- Epoch 2: `level2_2025W17_4B_0001_3D2_spx_l2b-v20-2025-240.fits`
reported a peak residual of **152.21σ** and was tentatively flagged. In this second-pass audit, we dissected the exact pixels, raw arrays, headers, and WCS mappings.

### Empirical Findings at the Residual Location:
- **Sky Coordinates**: $\alpha = 164.59037^\circ$, $\delta = +27.31893^\circ$.
- **Pixel Coordinates in Epoch 1 Grid**: $(y=1894, x=1415)$.
- **Unprojected Coordinates in Raw Epoch 2**: $(y=1779.14, x=1414.55)$.
- **Raw Flux in Epoch 1**: $0.2535\,\text{MJy/sr}$ (nominal zodiacal/background level). Flag: `0` (clean pixel).
- **Raw Flux in Epoch 2**: Sits directly adjacent to a single isolated pixel having **$110.73\,\text{MJy/sr}$** surrounded by $0.24\,\text{MJy/sr}$ background.
- **Raw Flag in Epoch 2**: The high pixel has flag value **`655426`**!
  - Bit 1 (`MP_OVERFLOW`, value 2): ADC saturation overflow.
  - Bit 6 (`MP_NONFUNC`, value 64): Nonfunctional / unbonded dead detector element.
  - Bit 17 (`MP_PERSIST`, value 131072): Latent charge persistence.
  - Bit 19 (`MP_OUTLIER`, value 524288): Statistical fit outlier.
- **Mechanism of the False Transient Artifact**:
  1. In raw Epoch 2, the pixel $(1779, 1415)$ was an unbonded/saturated dead pixel flagged with `MP_NONFUNC` and `MP_OVERFLOW`.
  2. During `reproject_interp`, the science image `img2` was reprojected using default **bilinear interpolation**, smearing the $110.73\,\text{MJy/sr}$ spike into neighboring fractional coordinates with interpolated fluxes of $42.96$ and $52.67\,\text{MJy/sr}$.
  3. Simultaneously, `mask2` was reprojected using `order='nearest-neighbor'`. Because the sub-pixel coordinate $(.14, .55)$ was offset, the nearest-neighbor mask evaluation picked an adjacent zero-flag pixel, assigning `mask2_reproj = 0.0` to the interpolated flux spike!
  4. The unmasked interpolated flux ($42.96\,\text{MJy/sr}$) divided by the local background uncertainty ($\sigma = 0.28\,\text{MJy/sr}$) created an artificial difference peak of $152.21\sigma$!

### Scientific Ruling on the 152.2σ Signal:
> [!CAUTION]
> **THE 152.2σ RESIDUAL IS NOT AN ASTRONOMICAL TRANSIENT.**
> It is an instrumental bad-pixel defect (ADC overflow on a dead detector pixel) that leaked into the difference image due to an interpolation mismatch between bilinear image reprojection and nearest-neighbor mask sampling. It must NOT be labeled an astronomical discovery.

## 3. Static-Source Control Experiments & Systematic Residual Origins

We evaluated the six physical origins of subtraction residuals across the 44 dither pairs:

1. **Bad-Pixel Leakage Across Interpolation**: As proven above, isolated 1-pixel defects smear during bilinear reprojection. **Proposed Fix**: Reproject masks with morphological dilation (binary dilation by 1 pixel) or use flux-conserving exact polygonal clipping.
2. **Dither Centroid Shifts & Sub-pixel Sampling**: Between dithers (e.g. 1D vs 2D), the optical point spread function shifts by sub-pixel fractions. Subtracting two un-convolved point source profiles yields a characteristic dipolar residual (positive on one side, negative on the other) with amplitudes up to $15–30\sigma$ on bright stars ($G < 14$).
3. **Optical PSF Variation**: SPHEREx focal plane optical distortion changes across the 11x11 or 21x21 grid. Subtracting a source at detector coordinate $(100, 100)$ against its dithered position at $(350, 400)$ produces shape mismatches without Alard-Lupton PSF convolution.
4. **Zodiacal Background Matching**: The large-scale zodiacal background is stable over 2-minute dither timescales ($\Delta \text{ZODI} < 0.005\,\text{MJy/sr}$), so background drift is negligible for short-cadence dither pairs.
5. **WCS Misregistration**: SIP distortion polynomials provide astrometric registration accurate to $\sim 0.05$ pixels, but sub-pixel interpolation artifacts remain without higher-order kernel matching.

## 4. Quantitative Temporal Validation Metrics

| Metric | Calculated Value | Status / Notes |
| :--- | :---: | :--- |
| Total Intra-Release Pairs Audited | 44 | Verified on disk |
| Median Dither Time Separation | 2.15 minutes | Range: 2.15 to 6.45 minutes |
| Median Pointing Center Separation | 0.45 deg | Well within 3.5° FOV |
| Median Astrometric WCS Residual | 0.06 pixels | Based on SIP polynomials |
| Maximum Astrometric WCS Residual | 0.22 pixels | Near focal plane edge |
| Static Source Dipole Rate on Bright Stars | ~100% | Expected without PSF matching convolution |
| Real Astrophysical Transient Candidates | 0 Confirmed | All tested residuals trace to defects or dither dipoles |
| Long-Baseline Multi-Month Pairs (Same Release) | 0 Available | PENDING (Requires future data acquisition) |
| True Transient Recovery Completeness | PENDING | Cannot be computed without long-baseline ground truth |
| Variance-Normalized Difference Null $\chi^2/\text{dof}$ | 1.08 | Clean background pixels follow Gaussian noise |

## 5. Corrected CHRONOS-X Readiness Status

**Status**: **`PIPELINE IMPLEMENTED / DITHER DIFFERENCING FUNCTIONAL / SCIENTIFIC TRANSIENT VALIDATION PENDING`**.
- The WCS reprojection and variance propagation mechanics are operational.
- **Mandatory Scientific Upgrades Before Discovery Claims**:
  1. Implement mask dilation to prevent defect flux leakage.
  2. Implement PSF-matching kernel convolution (e.g. Bramich or Alard-Lupton algorithm) before image subtraction to eliminate dither dipoles.
  3. Acquire genuine multi-month repeat observations processed under the same calibration release.
