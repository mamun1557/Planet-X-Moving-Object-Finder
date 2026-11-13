# SPECTRA-X / F1 — ASTROVISION CONTROLLED PILOT BENCHMARK PROTOCOL (VERSION 3.0)

**Document ID:** `SPX-F1-P3-PROTO-V3.0`  
**Date:** 2026-11-06  
**Status:** FROZEN DRAFT — PENDING INDEPENDENT SCIENTIFIC AUDIT  
**Benchmark Campaign Status:** STRICTLY BLOCKED — AUTHORIZED FOR PILOT DESIGN ONLY  
**Parent Framework:** SPHEREx QR3 Level-2 Multi-Pointing Controlled Pilot Benchmark  

---

## 1. Executive Summary & Purpose

This protocol specifies the execution framework, algorithmic boundaries, statistical procedures, and governance requirements for conducting a controlled pilot benchmark of the frozen ASTROVISION spatial model (`checkpoints/astrovision_spatial_v2.pt`).

The protocol addresses historical methodological vulnerabilities identified in Phase 3 Audits 1.1F through 1.1N:
1. **Exposure-Level Spatial Leakage:** Elimination of intra-pointing residual contamination by enforcing pointing-level clustering.
2. **Detector-Aware Calibration:** Transition from an uncalibrated scalar threshold ($\tau = 169.10$) to detector-stratified empirical transfer curves $\beta(\text{SNR}, \text{det})$.
3. **Cluster-Degeneracy Realism:** Explicit mathematical accounting of bootstrap clustering limitations with $G_{\text{eval}} = 3$ evaluation clusters (10 unique multisets).

> [!CAUTION]
> **Zero-Execution Mandate:** This document defines the protocol for a future authorized benchmark campaign. It does NOT authorize model inference, synthetic injection trials, campaign execution, model retraining, or scientific certification. ASTROVISION remains scientifically **UNCERTIFIED** (`FAIL — NOT CERTIFIED`).

---

## 2. Authoritative Dataset & Provenance

The controlled pilot benchmark shall execute exclusively against the 120 verified FITS products from the audited five-pointing cohort:

- **Pointings:** `0001`, `0002`, `0008`, `0009`, `0010`
- **Total Products:** 120 FITS files (24 per pointing across 6 detectors and 4 dithers)
- **Pipeline Build:** `l2b-v27-2026-222`
- **Planning Period:** `2026W30_1B`
- **Observation Epoch:** SPHEREx Observation Epoch $2026.5496$ (MJD 61241.018)
- **Archive Authority:** IPAC / IRSA SPHEREx QR3 Level-2 Science Archive

```
data/spherex/multipointing_pilot/level2/
├── 0001/ (24 FITS: 1D1..4D6) — Calibration Cohort
├── 0008/ (24 FITS: 1D1..4D6) — Calibration Cohort
├── 0002/ (24 FITS: 1D1..4D6) — Evaluation Cohort
├── 0009/ (24 FITS: 1D1..4D6) — Evaluation Cohort
└── 0010/ (24 FITS: 1D1..4D6) — Evaluation Cohort
```

---

## 3. Reference Source Catalogues & Astrometric Propagation

### 3.1 Catalogue Construction
Reference catalogues are generated using official Gaia DR3 data cross-matched with 2MASS PSC/XSC via Heidelberg ARI TAP:
- **Spatial Coverage:** 3 distinct focal-plane fields per pointing ($R = 2.50^\circ$ cone searches) matching detector pairs (D1/D4, D2/D5, D3/D6).
- **Proper Motion Propagation:** Astrometric positions are propagated from Gaia epoch $J2016.0$ to SPHEREx epoch $2026.5496$ ($\Delta t = 10.5496$ years) using:
  $$\Delta\alpha = \frac{\mu_{\alpha*} \Delta t}{\cos\delta}, \quad \Delta\delta = \mu_\delta \Delta t$$
  Propagation achieved $98.4\% - 99.3\%$ coverage across all pointings.
- **2MASS Cross-Matching:** Match radius $\le 2.0''$ ($\approx 0.32$ SPHEREx pixels).

### 3.2 Source Categorization
Every reference source is classified into mutually exclusive categories:
1. `RELIABLE_ISOLATED_POINT_SOURCE`: $G \in [13.0, 19.5]$, nearest neighbor $d_{\text{nn}} > 12.0''$ (no blend within 2 pixels), $\text{RUWE} \le 1.40$, astrometric excess noise $\le 2.0$, distance to nearest saturated star $> 185''$.
2. `BLENDED_CROWDED`: $d_{\text{nn}} \le 12.0''$.
3. `SATURATED_OR_CONTAMINATED`: $G < 11.5$ mag.
4. `EXTENDED`: Astrometric excess noise $> 2.0$ or 2MASS extended source flag.
5. `UNCERTAIN_OR_LOW_QUALITY`: $\text{RUWE} > 1.40$, $G > 19.5$, or proximity to saturated core.

---

## 4. Scientifically Defensible Source Masks

To avoid synthetic injections into real astrophysical sources or contaminated regions:
- **Detector Edge Margin:** 50-pixel border exclusion on all 4 detector edges ($[1..50]$ and $[1991..2040]$).
- **Point-Source Exclusion Radius:** $R_{\text{ps}} = 3$ pixels ($18.5''$).
- **Crowded Region Exclusion Radius:** $R_{\text{cr}} = 6$ pixels ($37.0''$).
- **Extended Source Exclusion Radius:** $R_{\text{ext}} = 15$ pixels ($92.3''$).
- **Saturated Core Exclusion Radius:** $R_{\text{sat}} = 30$ pixels ($184.7''$).
- **Usable Unmasked Area:** Empirically verified at $84.6\% - 90.3\%$ (mean $87.7\%$) across all detectors, providing ample unmasked background area for null and injection sampling.

---

## 5. Five-Partition Allocation & Zero Cross-Boundary Leakage

The campaign allocation is frozen in `reports/manifests/astrovision_five_partition_pilot_manifest.csv`:

| Partition ID | Partition Name | Role | Assigned Pointings | Trial Count | Target SNR | Source Type |
|---|---|---|---|---|---|---|
| 1 | `CALIBRATION_CONTROL` | Calibration | `0001`, `0008` | 500 | 0.0 | Null Background |
| 2 | `CALIBRATION_INJECTION` | Calibration | `0001`, `0008` | 500 | 3.0–20.0 | Synthetic Point Source |
| 3 | `EVALUATION_CONTROL` | Evaluation | `0002`, `0009`, `0010` | 500 | 0.0 | Null Background |
| 4 | `EVALUATION_POINT_SOURCE_INJECTION` | Evaluation | `0002`, `0009`, `0010` | 500 | 3.0–25.0 | Synthetic Point Source |
| 5 | `EVALUATION_EXTENDED_SOURCE_INJECTION` | Evaluation | `0002`, `0009`, `0010` | 500 | 3.0–25.0 | Synthetic Extended Source |

### Strict Allocation Rules:
1. **Total Isolation:** Calibration pointings (`0001`, `0008`) and FITS files shall NEVER be used for evaluation scoring.
2. **Evaluation Purity:** Evaluation pointings (`0002`, `0009`, `0010`) shall NEVER be used to estimate null thresholds $\tau$ or fit transfer parameters $\beta$.
3. **Dither Integrity:** Dithers 1 through 4 of any exposure remain bound to the same partition family.
4. **Deterministic Seed:** All coordinate selections and SNR assignments are frozen with `seed = 42`.

---

## 6. Calibration Methodology & Transfer Curve Fitting

### 6.1 Historical Threshold Deprecation
The historical scalar threshold $\tau = 169.10$ (derived from P0003 uncalibrated evaluation) is **STRICTLY INVALIDATED** for the multi-pointing pilot. It must not be silently retained or applied.

### 6.2 Detector-Stratified Null Threshold Estimation
Using Partition 1 (`CALIBRATION_CONTROL`):
- For each detector $d \in \{1, 2, 3, 4, 5, 6\}$, estimate the empirical null score distribution $S_{0, d}$.
- Set the detector operating threshold $\tau_d$ at false positive rate $\alpha_{\text{target}} = 0.05$ (or $\alpha_{\text{target}} = 0.01$):
  $$\tau_d = \text{Quantile}(S_{0, d}, 1 - \alpha_{\text{target}})$$

### 6.3 Empirical Transfer Curve Estimation
Using Partition 2 (`CALIBRATION_INJECTION`):
- For each detector $d$, fit a logistic or Gompertz transfer curve $\beta_d(\text{SNR})$:
  $$P(\text{Detect} \mid \text{SNR}, d) = \frac{1}{1 + \exp\left(-k_d (\text{SNR} - \text{SNR}_{50, d})\right)}$$
- Verify calibration convergence before proceeding to evaluation scoring. If any detector fails convergence or calibration support, mark that detector as `UNSUPPORTED_CALIBRATION`.

---

## 7. Evaluation Performance Metrics & Statistical Limitations

### 7.1 Metrics Measured Exclusively on Partitions 3, 4, 5
- **AUROC / AUPRC:** Receiver operating characteristics measured per detector and pooled across evaluation pointings (`0002`, `0009`, `0010`).
- **Completeness ($C_{50}, C_{90}$):** Effective SNR thresholds achieving 50% and 90% recovery.
- **Prevalence-Standardized Precision:** Evaluated at realistic survey prevalence $\pi \in [10^{-4}, 10^{-2}]$.

### 7.2 Cluster-Bootstrap Resampling Limitations
With $P_{\text{eval}} = 3$ evaluation clusters ($G_{\text{eval}} = 3$), resampling clusters with replacement yields exactly:
$$\binom{G_{\text{eval}} + G_{\text{eval}} - 1}{G_{\text{eval}}} = \binom{5}{3} = 10 \text{ unique bootstrap multisets}$$
Namely:
1. $\{0002, 0002, 0002\}$
2. $\{0002, 0002, 0009\}$
3. $\{0002, 0002, 0010\}$
4. $\{0002, 0009, 0009\}$
5. $\{0002, 0009, 0010\}$
6. $\{0002, 0010, 0010\}$
7. $\{0009, 0009, 0009\}$
8. $\{0009, 0009, 0010\}$
9. $\{0009, 0010, 0010\}$
10. $\{0010, 0010, 0010\}$

> [!WARNING]
> **Statistical Limitation Notice:** Because only 10 unique cluster multisets exist, cluster-bootstrap confidence intervals will exhibit coarse, step-like empirical distributions. No claim of high-precision confidence interval half-width (e.g. $\pm 0.03$) can be justified. Results from this pilot campaign must be characterized strictly as **pilot exploratory bounds**, not production flight-level statistical guarantees. Strong statistical power requires expansion to $G \ge 15-20$ independent pointings.

---

## 8. Artifact Rejection & Invalid-Trial Handling

Any trial exhibiting any of the following conditions shall be marked `INVALID_TRIAL` and rejected prior to model scoring:
1. `VARIANCE_NAN_OR_NEGATIVE`: Cutout contains non-positive variance pixels.
2. `CORE_CONTAMINATION`: Proximity $< 10$ pixels to an uncatalogued high-gradient defect or cosmic ray.
3. `TRUNCATED_CUTOUT`: Cutout boundaries extend outside the active detector pixel coordinates $[1..2040] \times [1..2040]$.
All rejected trials must be recorded in the final execution manifest with rejection reason and checksum.

---

## 9. Governance & Verification Protocol Checklist

Prior to any authorized execution run:
- [x] Input manifest SHA-256 verified against Task 1.1M ingestion manifest.
- [x] All 120 FITS products verified present with authentic WCS and variance extensions.
- [x] All 16 historical benchmark assets confirmed non-mutated.
- [x] Source catalogues generated with Gaia DR3 + 2MASS and proper-motion propagation.
- [x] Mask diagnostics verified across all 6 detectors and 4 dithers.
- [x] Five-partition manifest frozen with deterministic seed (`seed = 42`).
- [ ] Independent scientific audit of preparation deliverables (Task 1.1P).
- [ ] Formal authorization by benchmark governance authority.

