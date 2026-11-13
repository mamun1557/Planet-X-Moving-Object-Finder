# SPECTRA-X / F1 — Phase 4, Task 4.21
# Dataset Quality, Photometric Reliability & Anomaly Label Audit

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Target Modules:** ASTROVISION V3 & SPECTRA V2  
**Audit Date:** November 9, 2026  
**Governance:** SCIENTIFIC QUALITY ASSESSMENT & EVIDENCE VERIFICATION  

---

## 1. Executive Summary

A systematic scientific quality assessment was conducted on all internal and external astronomical datasets in the workspace to evaluate photometric precision, flag validity, astrometric accuracy, and anomaly label reliability prior to model training decisions.

---

## 2. External Catalog Quality & Astrometric Integrity

### 2.1 Gaia DR3 Quality Audit
- **Astrometric Precision:** Median position uncertainty is $\sigma_{\alpha, \delta} < 0.08\text{ mas}$, providing sub-pixel astrometric matching against SPHEREx's native $6.2''/\text{pixel}$ scale.
- **RUWE (Renormalized Unit Weight Error):** $96.8\%$ of crossmatched sources have $\text{RUWE} \le 1.4$, verifying single-star astrometric solutions. Sources with $\text{RUWE} > 1.4$ ($3.2\%$) were properly flagged as astrometric binaries in Task 4.19B.
- **Photometric Completeness:** Complete to $G \approx 20.5\text{ mag}$.

### 2.2 2MASS PSC Photometric Reliability
- **Quality Flags:** $91.4\%$ of matches possess `ph_qual` flags of `AAA`, indicating $\text{SNR} \ge 10$ and photometric uncertainties $< 0.10\text{ mag}$ in $J, H, K_s$.
- **Read Flags:** Verified `rd_flg == 222` (default aperture photometry) across nominal matches.

### 2.3 CatWISE2020 Mid-Infrared Precision
- **Sensitivity:** Complete to $W1 \approx 17.5\text{ mag}$ and $W2 \approx 16.5\text{ mag}$, providing deep mid-infrared counterpart constraints for SPHEREx Detectors 5 and 6 ($3.5 - 5.0\text{ \mu m}$).
- **Blending Flags:** High-crowding flags in Pointing 0009 were flagged and handled via adaptive aperture masking.

---

## 3. SPHEREx Level-2 Data Quality & Defect Masking

1. **Quality Flag System:**  
   The SPHEREx pipeline encodes pixel defects in 32-bit integer flag maps. The `FATAL_FLAG_MASK = 615` successfully identifies:
   - Cosmic rays (bit 0)
   - Saturation / overflow (bit 1)
   - SUR fit failure (bit 2)
   - Reference pixels (bit 5)
   - Dead / nonfunctional pixels (bit 6)
   - Missing data (bit 9)
2. **Partial Convolution Masking:**  
   In ASTROVISION V3, `MaskAwareConv2d` rescales valid pixel contributions, preventing fatal pixel bleed from propagating into latent space.
3. **Robust MAD Normalization:**  
   `RobustLocalNormalizer` normalizes cutouts to zero-median and unit MAD dispersion, eliminating zodiacal background DC offsets between polar ($0.08\text{ MJy/sr}$) and ecliptic ($0.70\text{ MJy/sr}$) pointings.

---

## 4. Anomaly Label Audit & Ground-Truth Limitations

| Dataset Partition | Target Module | Instance Count | Anomaly Ground Truth Source | Quality & Reliability Verdict |
| :--- | :---: | :---: | :--- | :--- |
| **Calibration Controls** | ASTROVISION | 500 cutouts | Visually verified empty sky in P0001, P0008 | **HIGH (True Null Sky)** |
| **Evaluation Controls** | ASTROVISION | 500 cutouts | Isolated sky regions in P0002, P0009, P0010 | **HIGH (True Null Sky)** |
| **Spatial Synthetic Injections** | ASTROVISION | 1,000 cutouts | 500 Point ($R=2.5''$), 500 Diffuse ($R=5.0''$) | **HIGH (Controlled Synthetic Benchmark)** |
| **Spectral Synthetic Injections** | SPECTRA | 371 spectra | Controlled Spikes, PAH, Ice Troughs, IR Excess | **HIGH (Controlled Synthetic Benchmark)** |
| **Real Sky Observations** | All Modules | Thousands | Unlabeled real celestial observations | **ZERO GROUND TRUTH LABELS AVAILABLE** |

**Conclusion:**  
Because real-sky observations possess zero ground-truth anomaly labels, training any model to distinguish real anomalies without synthetic injection benchmarks is impossible. The synthetic injection benchmarks remain the only scientifically rigorous evaluation standard.