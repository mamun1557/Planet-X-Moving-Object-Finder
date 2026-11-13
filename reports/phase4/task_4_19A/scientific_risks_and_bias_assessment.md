# SPECTRA-X / F1 — Phase 4, Task 4.19A Technical Assessment
## Scientific Risks, Bias Governance & Methodological Pitfalls in Catalog Expansion

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Parent Tasks:** Phase 4 Tasks 4.17, 4.18, 4.18-SKY  
**Date:** 2026-11-08  
**Status:** FORMAL SCIENTIFIC RISK & GOVERNANCE CHARTER  

---

## 1. Executive Summary

Expanding catalog counterpart coverage beyond the current 33.20% baseline is scientifically desirable to resolve the physical nature of ASTROVISION false positives. However, careless catalog expansion introduces severe risks of **selection bias, astrometric confusion, epoch drift, and circular reasoning**.

This assessment establishes five mandatory risk boundaries that must govern any subsequent acquisition or validation tasks (including Phase 4 Task 4.19B).

---

## 2. Matrix of Critical Scientific Risks

| Risk ID | Risk Domain | Description & Mechanism | Severity | Mitigation & Governance Boundary |
|:---:|---|---|:---:|---|
| **RISK-19A-01** | **Evaluation Circularity** | Using native SPHEREx source extraction on the blind control cutouts to explain away false alarms | **FATAL** | **Strictly Prohibited:** Native extraction cannot alter the ground-truth status of blind evaluation controls. Only independent external catalogs are permitted. |
| **RISK-19A-02** | **Spatial Beam Confusion** | Blending of multiple stars into a single unresolved source in WISE W1/W2 (FWHM $\approx 6.1''$) in crowded fields (P0009) | **HIGH** | Crossmatch isolation filter: Flag any candidate with competing counterparts within $\le 3.0''$ as `AMBIGUOUS_MULTI_MATCH`. |
| **RISK-19A-03** | **Epoch & Motion Drift** | 16.5-year baseline drift between AllWISE (J2010.0) and SPHEREx (2026.55). High-proper-motion stars move $> 1''$ | **MEDIUM-HIGH** | Prefer CatWISE2020 (includes measured proper motions). Propagate positions to epoch 2026.55 before spatial crossmatching. |
| **RISK-19A-04** | **Over-Masking Artifacts** | Masking hundreds of catalog sources in dense fields removes $> 15\%$ of image area, inducing boundary residuals | **HIGH** | Implement max masked area limit ($\le 12.0\%$) and crowding thresholds; do not mask faint background stars ($G > 20.0$) in dense cutouts. |
| **RISK-19A-05** | **Calibration Leakage** | Conflating calibration cohort (P0008) thresholds or parameter tuning with the blind evaluation cohort (P0002, P0009, P0010) | **FATAL** | Strict cohort separation: Zero model retraining or threshold adjustment based on blind cohort outcomes. |

---

## 3. Deep-Dive Analysis of Primary Risks

### 3.1 Circularity & Selection Bias (RISK-19A-01)
The defining characteristic of an independent false-positive audit is that **the truth labels of the evaluation controls must remain immutable**.
If a control cutout is classified as a false positive by ASTROVISION ($\chi^2 \ge \tau_{\text{peak}}$), that outcome is an empirical fact of the model's performance on that patch of sky.
- If an **independent external catalog** (Gaia DR3 or CatWISE2020) recorded an optical/infrared source at those coordinates years prior, we can legitimately conclude that the cutout suffered from benchmark label contamination (i.e., a real star was inadvertently included in the null set).
- If **no external catalog** recorded a source, and we run our own source finder on that exact image and find a flux peak, we cannot claim benchmark label contamination. The flux peak could be a persistent detector hot pixel, a readout glitch, or electronic banding. Excusing model false alarms using self-detections is circular reasoning.

### 3.2 Beam Confusion in Crowded Fields (RISK-19A-02)
SPHEREx has a $6.215''$ pixel scale with an optical beam FWHM of $\sim 2.5\text{ pixels}$ ($15.5''$).
WISE W1 ($3.4\,\mu\text{m}$) and W2 ($4.6\,\mu\text{m}$) have an optical beam FWHM of $\sim 6.1''$.
In Pointing P0009 (Perseus Molecular Cloud), the stellar surface density reaches $> 50,000\text{ stars/deg}^2$.
- At this density, the mean separation between adjacent stars drops below $8''$.
- Multiple faint stars frequently blend into a single unresolved CatWISE2020 / AllWISE detection.
- **Rule:** When crossmatching AllWISE or CatWISE2020 against SPHEREx cutouts in P0009, the matching engine must check competing candidate counts within an ambiguity radius of $3.0''$. Blended sources must be flagged with `cc_flags` or `ab_flags` and classified as `AMBIGUOUS_CATALOG_ASSOCIATION`.

### 3.3 Proper Motion Drift Over 16.5 Years (RISK-19A-03)
The SPHEREx observation epoch for the evaluation cohort is:
$$\text{Epoch}_{\text{SPHEREx}} = 2026.5496 \quad (\text{July 20, 2026})$$
Reference epochs of candidate catalogs:
- **AllWISE:** Epoch J2010.0 (baseline $\Delta t = +16.55\text{ years}$).
- **Gaia DR3:** Epoch J2016.0 (baseline $\Delta t = +10.55\text{ years}$).
- **CatWISE2020:** Mid-epoch J2014.5 (includes measured proper motions $\mu_\alpha, \mu_\delta$).

For a typical nearby M-dwarf with total proper motion $\mu = 150\text{ mas/yr}$:
$$\Delta \theta_{\text{drift}} = 0.150''/\text{yr} \times 16.55\text{ yr} \approx 2.48'' \approx 0.40\text{ SPHEREx pixels}!$$
Without proper motion propagation, an uncorrected J2010.0 AllWISE position can fall outside the tight $2.0''$ crossmatch radius, causing a false crossmatch miss.
- **Rule:** CatWISE2020 is strongly preferred over AllWISE because CatWISE2020 includes motion modeling. All catalog positions must be propagated to epoch 2026.55 before computing cutout-level distances.

### 3.4 Over-Masking Artifacts in Dense Fields (RISK-19A-04)
In Task 4.18, we discovered that in cutouts with $> 300$ catalog sources (such as `PILOT_001301`, `PILOT_001340`, `PILOT_001408`), unconstrained masking of all catalog stars removed up to $15 - 25\%$ of the image area.
- Masking dozens of circular holes creates sharp artificial boundaries in the input tensor fed into the autoencoder.
- This boundary effect can distort the median background estimation and induce edge ringing, causing the central aperture score to **increase** and generating new false alarms.
- **Rule:** `CatalogAwareSourceMasker` must enforce a maximum masked area fraction ceiling ($\le 12.0\%$) and apply magnitude filtering so that only sources bright enough to cause receptive-field leakage ($G \le 19.0$ or $W1 \le 16.0$) are masked in dense fields.

---

## 4. Governance Protocol for Task 4.19B Execution

Before any data acquisition or shadow re-evaluation is authorized:
1. **Pre-Registration:** The exact query boundaries, ADQL scripts, and crossmatch tolerances must be pre-registered and cryptographically locked.
2. **Immutable Reference Denominators:** The baseline 45 false positives and 500 null controls must remain immutable.
3. **External Independence Verification:** Only external catalog counterparts (CatWISE2020 / AllWISE / Gaia DR3) with verified astronomical provenance can be used for catalog-aware masking.
4. **Frozen Checkpoint Protection:** Checkpoints `astrovision_spatial_v3.pt` and `spectra_masked_ae_v2.pt` must remain strictly untouched.

