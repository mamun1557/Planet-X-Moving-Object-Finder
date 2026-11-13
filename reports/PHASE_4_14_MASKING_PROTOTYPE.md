# SPECTRA-X / F1 — Phase 4, Task 4.14D
# Mask Dilation Calibration & Isolated Prototype Validation

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Target Module:** ASTROVISION Catalog-Aware Source Masking Prototype  

---

## 1. Prototype Mask Dilation Performance Matrix

Evaluated on an off-center $500\,	ext{MJy/sr}$ stellar source at $d = 16	ext{ pixels}$ in Detector 1 ($	au_{	ext{peak}} = 186.29$):

| Mask Dilation Level | Mask Radius (px) | Total Masked Pixels | Central Score ($S_{	ext{center}}$) | Score Suppression (%) | False Alarm? | Genuine Anomaly Score | Genuine Recovery Retention (%) |
|---|---:|---:|---:|---:|:---:|---:|---:|
| **Baseline (Unmasked)** | 0 | 99 | 1,366.18 | 0.00% | **YES** | 13,563.48 (Corrupted) | 100.0% (Inflated) |
| **Dilation = 0 px** (Core only) | 2.5 | 120 | 17.81 | 98.70% | **NO** | 1,912.45 | **98.9%** |
| **Dilation = 1 px** | 3.5 | 136 | 3.55 | **99.74%** | **NO** | 1,908.10 | **98.7%** |
| **Dilation = 2 px** (Optimal) | 4.5 | 156 | **3.53** | **99.74%** | **NO** | **1,902.92** | **98.4%** |
| **Dilation = 3 px** | 5.5 | 180 | 3.47 | 99.75% | **NO** | 1,885.30 | 97.5% |
| **Dilation = 5 px** | 7.5 | 240 | 3.81 | 99.72% | **NO** | 1,820.15 | 94.1% |

*Pristine central anomaly alone (Ground Truth): $S_{	ext{center}} = 1,934.05$.*

---

## 2. Dilation Optimization Findings

1. **Why Dilation = 0 px is Insufficient:**
   - A core-only mask ($r = 2.5	ext{ px}$) suppresses the central score from $1366.18$ down to $17.81$. While this prevents threshold crossing, $17.81$ remains elevated above the $3.18$ background floor due to steep PSF wing leakage.
2. **Why Dilation = 2 px is Optimal:**
   - Dilation by 2 pixels ($r = 4.5	ext{ px}$) covers the primary Airy diffraction ring and PSF wings.
   - It reduces $S_{	ext{center}}$ down to **$3.53$** (essentially identical to clean sky $3.18$).
   - It retains **$98.4\%$ fidelity** on genuine central anomaly recovery ($1902.92$ vs. ground truth $1934.05$).
   - It masks only $156$ pixels out of $16,384$ ($0.95\%$ of the cutout area).
3. **Why Dilation $\ge 5$ px is Sub-Optimal:**
   - Dilation by 5 pixels masks excessive area ($240	ext{ px}$), encroaching toward nearby apertures and degrading genuine extended anomaly recovery by nearly $6\%$.

---

## 3. Uncertainty States for Catalog-Aware Masking

For production governance, the prototype preserves five explicit, non-overlapping uncertainty states:

```
Catalog Source Crossmatch
  │
  ├── High-fidelity Gaia match (dist <= 3.1", G <= 20.5) ──> [KNOWN_CATALOG_SOURCE] (Mask dilated r=4.5 px)
  │
  ├── Proximity match (3.1" < dist <= 12.4")             ──> [PROBABLE_SOURCE]      (Mask dilated r=3.5 px)
  │
  ├── Blended / confused match (12.4" < dist <= 31.0")   ──> [AMBIGUOUS_SOURCE]     (Flagged; advisory mask)
  │
  ├── In verified cone, no match within 31"              ──> [NO_CATALOG_COUNTERPART](Unmasked sky)
  │
  └── Outside catalog cone search footprint              ──> [MASK_UNVERIFIABLE]    (Preserve raw L2 flags)
```
