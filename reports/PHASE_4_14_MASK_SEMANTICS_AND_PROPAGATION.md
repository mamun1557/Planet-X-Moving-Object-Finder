# SPECTRA-X / F1 — Phase 4, Task 4.14C
# Catalog Mask Semantics & Mask Propagation Mechanics

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Target Module:** ASTROVISION Preprocessing & Mask-Aware Layers  

---

## 1. Comparison of Catalog Mask Sources

| Attribute | 1. SPHEREx Level 2 Mask (Bit 21) | 2. Gaia DR3 Crossmatch Mask | 3. Combined Catalog Mask |
|---|---|---|---|
| **Authoritative Definition** | `MSKN0021 = 'SOURCE'` (`Pixel mapped to a known source`) | External astrometric catalog crossmatch | Boolean union of Level 2 source flag and Gaia DR3 positional mask |
| **Pipeline Origin** | SPHEREx Science Data Center (`SSDC-MS-019 v3.5`) | Ground-truth astrometry ($G \le 20.5\,	ext{mag}$) | Integrated FUSION-X catalog vetting module |
| **Spatial Geometry** | Broad pre-computed aperture / footprint | Precision point-source centroid + dilated radius | Core catalog footprint with calibrated dilation |
| **Coverage in Evaluation Cohort** | Full array coverage (62.3% to 79.7% active pixels) | Local cone searches only (Field 1, 2, 3) | Array-wide Level 2 flag supplemented by local Gaia |
| **Astrophysical Ambiguity** | High (flags diffuse galaxies, blended pairs, faint stars) | Low (precision parallax and proper motion) | Calibrated uncertainty states |

---

## 2. Mask Propagation Through Preprocessing & Inference

```
Raw FITS Image [128, 128] + FLAGS
  │
  ├── [Step 1: RobustLocalNormalizer]
  │   - Valid mask: (flags & FATAL_MASK == 0) & isfinite & (I < 5000)
  │   - Invalid/masked pixels imputed with local median background
  │   - Median & MAD computed strictly on valid unmasked pixels
  │
  ├── [Step 2: MaskAwareConv2d Encoder]
  │   - Zero out invalid pixels: x_masked = x * mask
  │   - Raw partial convolution: raw_out = Conv2d(x_masked)
  │   - Coverage ratio: ratio = (k*k) / clamp(Conv2d(mask), min=1.0)
  │   - Scaled feature map: out = raw_out * ratio
  │   - Propagated mask: new_mask = (Conv2d(mask) > 0)
  │
  ├── [Step 3: Decoder Feature Generation]
  │   - ConvTranspose2d operates on uncorrupted latent features
  │
  └── [Step 4: Anomaly Scoring & Mask Multiplication]
      - Residual: residual_sq = (I_norm - Recon)^2
      - Masked anomaly: anom_map = residual_sq * input_mask
      - Centered scoring: ApertureAnomalyScorer evaluates r <= 2.5 on unmasked pixels
```

---

## 3. Mask Propagation Guarantees

1. **Non-Contamination Guarantee:** Setting `mask[y, x] = 0` completely zeroes out the source pixel before the first convolution layer (`x * mask`).
2. **Reconstruction Protection:** The dynamic coverage ratio prevents edge artifacts along mask boundaries.
3. **Score Extinction:** In `compute_anomaly_map`, the residual map is explicitly multiplied by `mask`. Masked pixels receive an anomaly score of EXACTLY zero.
4. **Consistency Requirement:** Masking must be applied identically to the input image, normalizer background estimator, and anomaly scoring aperture.
