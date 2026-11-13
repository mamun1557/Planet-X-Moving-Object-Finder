# SPECTRA-X / F1 — PHASE 1: TEMPORAL REPEAT OBSERVATION AUDIT
**Lead Astronomy Data Engineer & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE (Data Foundation Audit)

---

## 1. Executive Summary

A core promise of the SPECTRA-X Observatory and CHRONOS-X temporal anomaly detection engine is the identification of multi-month, multi-epoch celestial transients, variable stars, and proper motion objects.

Earlier project claims suggested that differences between Quick Release 2 (QR2) and Quick Release 3 (QR3) data products could serve as temporal baseline pairs. This audit conducted an empirical geometric and temporal verification of all candidate pairs in the repository.

### Core Audit Verdicts:
1. **Genuine Multi-Month Temporal Repeats:** **`NOT_FOUND`** in the local 32-file repository.
2. **Cross-Release (QR2 vs QR3) Pairs:** **`SPATIALLY_INCOMPATIBLE`** and **`DETECTOR_INCOMPATIBLE`**. The QR2 and QR3 footprints are located in completely different sectors of the celestial sphere (separated by $42.6^\circ$ to $105.8^\circ$), and observe entirely different wavelength regimes (QR2 is D2, $1.20-1.95\,\mu\text{m}$; QR3 is D1, $0.75-1.20\,\mu\text{m}$).
3. **Intra-Pointing Pairs:** All 44 local observation pairs are **`INTRA_VISIT_DITHER_ONLY`** with time separations of only $\Delta t = 2.15\text{ to }6.45\text{ minutes}$. These represent spacecraft dithers for cosmic ray rejection and pixel sub-sampling, not temporal variability baselines.
4. **Machine-Readable Manifest:** Cataloged in [`data/manifests/f1_temporal_repeat_pairs.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_temporal_repeat_pairs.csv).

---

## 2. Classification Criteria for Temporal Pairs

To prevent scientific misrepresentation in the Blink / Video player and CHRONOS-X differential imaging pipeline, every candidate observation pair $(A, B)$ must be evaluated against five rigorous astronomical criteria:

1. **Spatial Footprint Overlap:** Angular separation between pointing boresights must satisfy $\theta \le 3.5^\circ$, and WCS polygon intersection area must be $> 10\%$.
2. **Detector & Bandpass Compatibility:** Both exposures must originate from the same detector array (e.g., $D_A = D_B$) and sample overlapping wavelength channels ($\Delta \lambda_A \cap \Delta \lambda_B \ne \emptyset$). Differencing D1 ($0.75-1.20\,\mu\text{m}$) against D2 ($1.20-1.95\,\mu\text{m}$) produces chromatic flux differences, not physical variability.
3. **Temporal Baseline ($\Delta t$):**
   - $\Delta t < 1\text{ hour}$: **`INTRA_VISIT_DITHER_ONLY`** (Rapid spacecraft jitter/dither).
   - $1\text{ day} \le \Delta t \le 30\text{ days}$: Short-cadence orbital revisits.
   - $\Delta t \ge 30\text{ days}$ (typically 6 months): **`VALID_TEMPORAL_PAIR`** (Semi-annual survey passes).
4. **WCS & Astrometric Alignment:** Pointing solutions must share compatible tangent plane projections and distortions capable of sub-pixel re-projection.
5. **Data Quality Integrity:** Both frames must pass quality filtering (`DQ_FLAGS == 0` for nominal science pixels).

---

## 3. Detailed Audit of Repository Pair Candidates

### A. Cross-Release Spatial Incompatibility (QR2 vs QR3)
The table below documents the celestial separation between the QR2 test pointings and QR3 pointings:

| Observation A (QR2, D2) | Observation B (QR3, D1) | Coord A ($\alpha, \delta$) | Coord B ($\alpha, \delta$) | Separation ($\theta$) | Scientific Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Pointing 0001 (QR2) | Pointing 0001 (QR3) | $187.32^\circ, +7.98^\circ$ | $265.82^\circ, +44.38^\circ$ | **82.35°** | **SPATIALLY_INCOMPATIBLE** |
| Pointing 0001 (QR2) | Pointing 0003 (QR3) | $187.32^\circ, +7.98^\circ$ | $165.69^\circ, -69.57^\circ$ | **79.62°** | **SPATIALLY_INCOMPATIBLE** |
| Pointing 0002 (QR2) | Pointing 0003 (QR3) | $147.38^\circ, +7.98^\circ$ | $165.69^\circ, -69.57^\circ$ | **78.41°** | **SPATIALLY_INCOMPATIBLE** |
| Pointing 0005 (QR2) | Pointing 0003 (QR3) | $352.02^\circ, -56.78^\circ$ | $165.69^\circ, -69.57^\circ$ | **56.12°** | **SPATIALLY_INCOMPATIBLE** |
| Pointing 0006 (QR2) | Pointing 0001 (QR3) | $352.16^\circ, -56.78^\circ$ | $265.82^\circ, +44.38^\circ$ | **105.81°** | **SPATIALLY_INCOMPATIBLE** |

*Scientific Conclusion:* Any attempt to run image differencing, blinking, or cross-epoch correlation between QR2 and QR3 files in the current repository compares disjoint patches of the sky separated by up to $105^\circ$. They cannot be used as temporal pairs.

### B. Intra-Pointing Dither Audit
Within each individual pointing in `data/spherex/qr2` and `data/spherex/qr3`, four dither exposures exist:
- **Dither 1 to Dither 2:** $\Delta t \approx 129\text{ s}$ ($2.15\text{ min}$)
- **Dither 1 to Dither 3:** $\Delta t \approx 258\text{ s}$ ($4.30\text{ min}$)
- **Dither 1 to Dither 4:** $\Delta t \approx 386\text{ s}$ ($6.43\text{ min}$)

All 44 pair permutations within the repository exhibit:
- Identical sky coordinates ($\theta < 0.05^\circ$, sub-pixel offset).
- Identical detector array.
- $\Delta t \le 6.45\text{ minutes}$.
- Status: **`INTRA_VISIT_DITHER_ONLY`**.

---

## 4. Required Conditions for Genuine Temporal Science

SPHEREx scans the sky in great circles synchronized with its 97-minute sun-synchronous polar orbit. 
- Over the course of 6 months, the orbit precesses by $360^\circ$, mapping the entire celestial sphere.
- **Survey Pass 1:** Months 0 to 6.
- **Survey Pass 2:** Months 6 to 12 (semi-annual revisit, $\Delta t \approx 180\text{ days}$).
- **Survey Pass 3:** Months 12 to 18.
- **Survey Pass 4:** Months 18 to 24.

To demonstrate genuine CHRONOS-X temporal differencing:
1. SPECTRA-X must acquire a matching Pointing visit from **Survey Pass 2** overlapping Pointing 0003 ($\alpha \approx 165.69^\circ, \delta \approx -69.57^\circ$).
2. Pointing 0003 is located at high ecliptic latitude ($\beta \approx -64^\circ$), meaning it is observed multiple times per year, providing rapid revisit opportunities.
3. The specific acquisition steps are outlined in [`reports/F1_PHASE1_DATA_ACQUISITION_PLAN.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/F1_PHASE1_DATA_ACQUISITION_PLAN.md).
