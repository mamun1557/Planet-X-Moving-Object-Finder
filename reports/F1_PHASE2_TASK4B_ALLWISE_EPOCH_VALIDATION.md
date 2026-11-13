# SPECTRA-X / F1 — PHASE 2, TASK 4B: ALLWISE EPOCH & ASTROMETRY VALIDATION
## Independent Audit of Mid-Infrared Epoch Baselines, Spatial Confusion, & Beam Blending

**Role:** Independent Scientific Validation Engineer  
**Date:** 2026-11-04  
**Audit Status:** **INCORRECT (EPOCH PROPAGATION OMISSION) / CORRECTED**  

---

## 1. Executive Summary

In Phase 2, Task 4, the 1,132 Pointing 0003 SPHEREx sources were cross-matched against the AllWISE source catalog ([`data/external/allwise/pointing_0003_allwise_candidates.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/allwise/pointing_0003_allwise_candidates.csv)) to secure independent mid-infrared flux in W1 ($3.4\,\mu\text{m}$) and W2 ($4.6\,\mu\text{m}$).

This independent audit investigated:
1. The actual astrometric reference epoch of the AllWISE catalog.
2. How the Task 4 cross-matching script handled the epoch baseline between AllWISE and SPHEREx.
3. The impact of applying Gaia DR3 proper motions to AllWISE positions over the $\mathbf{16.55\text{-year}}$ baseline.
4. WISE point-spread function (PSF) beam confusion and spatial blending.
5. The justification for the chosen matching radii ($0.8''$ and $2.0''$).

### Critical Audit Findings:
- **Major Methodological Omission:** AllWISE positions are referenced to **J2010.0**. The SPHEREx observations took place in **July 2026** ($\Delta t = +16.5496\,\text{years}$). In Task 4, **zero epoch propagation was performed for AllWISE**. Unpropagated 2010.0 positions were matched directly against 2026.55 SPHEREx positions.
- **Consequence for High Proper Motion Stars:** Stars with significant proper motion were artificially displaced. The fastest mover (`SPX-J165.3661-71.1267`, $|\mu| = 215.6\,\text{mas/yr}$) had an unpropagated AllWISE separation of **$3.41''$** and was downgraded to `PROBABLE`. When propagated with Gaia proper motion over the 16.55-year baseline, its separation drops to **$0.37''$**, qualifying as `HIGH_CONFIDENCE`.
- **Cohort-Wide Impact:** When Gaia proper motions are applied to AllWISE coordinates, **678 sources improve in separation**, and **58 sources** erroneously classified as `PROBABLE` move into `HIGH_CONFIDENCE`.
- **Undercounted WISE Beam Blending:** Due to the $6.1''$ WISE PSF, **7 AllWISE designations were matched to 2 separate SPHEREx sources** (14 sources total). Task 4 documented only 1 blend, failing to flag the other 6 dual-matched source pairs.

---

## 2. AllWISE Reference Epoch & Temporal Baseline

The AllWISE source catalog (`allwise.source`) combines data from the 2010 cryogenic WISE mission and 2010 NEOWISE post-cryogenic survey. The astrometric reference epoch is formally defined as **J2010.0** (MJD 55197.0).

SPHEREx Level-2 images were acquired at MJD 61241.018 (**2026.5476 – 2026.5496**).

$$\Delta t_{\text{WISE}\rightarrow\text{SPX}} = 2026.5496 - 2010.0 = \mathbf{+16.5496\,\text{years}}$$

This temporal baseline is **57% longer** than the Gaia DR3 baseline ($\Delta t = 10.55\,\text{yr}$). Over 16.55 years:
- A star with a median proper motion of $|\mu| = 8.77\,\text{mas/yr}$ moves by **$145.1\,\text{mas}$** ($0.145''$).
- Moderate movers ($|\mu| \sim 30 - 50\,\text{mas/yr}$) move by **$0.50'' - 0.83''$**, directly crossing the $0.8''$ `HIGH_CONFIDENCE` threshold.
- Fast movers ($|\mu| > 100\,\text{mas/yr}$) move by **$1.65'' - 3.57''$**, risking misclassification as `AMBIGUOUS` or non-detection.

---

## 3. Forensic Inspection of Task 4 Implementation

In `scripts/process_crossmatch_and_classification.py` (lines 267–276):
```python
candidates = []
for _, w_row in sub.iterrows():
    w_ra = w_row["ra"]
    w_dec = w_row["dec"]
    d_wise = angular_separation_arcsec(s_ra, s_dec, w_ra, w_dec)
    if d_wise <= 4.0:
        candidates.append({"w_row": w_row, "d_wise": d_wise})
```

**Audit Verdict:**
- The script uses raw `w_row["ra"]` and `w_row["dec"]` from the 2010 AllWISE table without proper-motion propagation.
- Although `scripts/crossmatch_gaia_allwise.py` defined `ALLWISE_EPOCH = 2010.0` at line 25, this constant was never utilized in the matching loops.
- No attempt was made to look up the counterpart's Gaia proper motion to project coordinates to 2026.55.
- Therefore, the claim in Task 4 reports of a "rigorous spatial cross-match" is **INCORRECT** regarding AllWISE astrometry.

---

## 4. Independent Recalculation: Propagating AllWISE with Gaia Proper Motions

To correct this deficiency, an independent algorithm was executed across all 1,132 sources:
$$\Delta\alpha_{\text{WISE}} = \frac{\mu_{\alpha*, \text{Gaia}} \cdot 10^{-3} \cdot 16.5496}{3600 \cdot \cos\delta_{\text{WISE}}} \quad [\text{deg}]$$
$$\Delta\delta_{\text{WISE}} = \frac{\mu_{\delta, \text{Gaia}} \cdot 10^{-3} \cdot 16.5496}{3600} \quad [\text{deg}]$$

### Results of AllWISE Epoch Correction:
- **Total Sources with Both AllWISE & Gaia Counterparts:** 1,029 sources.
- **Separation Improved:** **678 sources (65.9%)**.
- **Separation Worsened:** 351 sources (34.1%) (predominantly very low PM stars where sub-pixel centroid noise dominates).
- **Transitions from `PROBABLE` ($0.8'' < d \le 2.0''$) to `HIGH_CONFIDENCE` ($d \le 0.8''$):** **58 sources**.
- **Transitions from `HIGH_CONFIDENCE` to `PROBABLE`:** 9 sources.
- **Net Gain in High-Confidence Mid-IR Matches:** **+49 sources**.

### Highlight Case Study: `SPX-J165.3661-71.1267`
- **Gaia DR3:** $\mu_{\alpha*} = -215.54\,\text{mas/yr}$, $\mu_\delta = +5.55\,\text{mas/yr}$ ($|\mu| = 215.61\,\text{mas/yr}$).
- **Unpropagated AllWISE Separation:** **$3.411''$** (Relegated by Task 4 to `PROBABLE` with note *"Wide AllWISE match at sep=3.41as"*).
- **Propagated AllWISE Separation (16.55 yr):** **$0.370''$**!
- **Outcome:** What appeared to be a poor, wide match is actually an astrometrically pristine counterpart matching the SPHEREx centroid to sub-arcsecond precision.

---

## 5. WISE Beam Confusion & Beam Blending Audit

The AllWISE resolution is diffraction-limited with FWHM $\approx 6.08''$ in W1 ($3.4\,\mu\text{m}$) and $\approx 6.84''$ in W2 ($4.6\,\mu\text{m}$). The SPHEREx Level-2 pixel scale is $6.2''$.

### Blending Analysis:
When scanning the 1,103 matched AllWISE records for identical catalog identifiers:
- **Unique AllWISE Designations:** 1,096.
- **Designations Matched to Multiple SPHEREx Targets:** **7 AllWISE sources** (14 SPHEREx targets).

| AllWISE Designation | SPHEREx Target 1 | Sep 1 | SPHEREx Target 2 | Sep 2 | Pair Separation | Status in Task 4 |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| **`J110056.56-691134.9`** | SPX-J165.2329-69.1932 | $3.84''$ | SPX-J165.2348-69.1928 | $1.44''$ | $2.55''$ | Both labeled `PROBABLE`, blend unflagged |
| **`J111609.58-704211.8`** | SPX-J169.0396-70.7034 | $2.26''$ | SPX-J169.0416-70.7034 | $2.75''$ | $2.35''$ | Both labeled `PROBABLE`, blend unflagged |
| **`J111218.31-701403.4`** | SPX-J168.0755-70.2342 | $0.65''$ | SPX-J168.0747-70.2335 | $2.21''$ | $2.44''$ | `HIGH_CONF` & `PROBABLE`, blend unflagged |
| **`J105851.15-685815.1`** | SPX-J164.7118-68.9708 | $1.39''$ | SPX-J164.7139-68.9710 | $1.98''$ | $2.82''$ | Both labeled `PROBABLE`, blend unflagged |
| **`J110033.56-675323.6`** | SPX-J165.1386-67.8899 | $1.43''$ | SPX-J165.1409-67.8898 | $2.02''$ | $3.07''$ | Both labeled `PROBABLE`, blend unflagged |
| **`J110101.34-700026.3`** | SPX-J165.2558-70.0075 | $1.51''$ | SPX-J165.2549-70.0071 | $1.76''$ | $1.90''$ | Both labeled `PROBABLE`, blend unflagged |
| **`J105507.14-680251.8`** | SPX-J163.7802-68.0474 | $0.51''$ | SPX-J163.7821-68.0477 | $3.04''$ | $3.55''$ | Only pair acknowledged in Task 4 |

**Scientific Consequence:**
In 6 of these 7 cases, Task 4 failed to flag the presence of a shared mid-IR counterpart. If two SPHEREx extractions are separated by $< 3''$, the AllWISE point source measures the **composite blended flux** of both stars. Assigning the entire W1/W2 flux to both SPHEREx sources artificially inflates the infrared brightness of the fainter star.

---

## 6. Justification of Matching Radii

Task 4 adopted:
- $d \le 0.8''$: `HIGH_CONFIDENCE`
- $0.8'' < d \le 2.0''$: `PROBABLE`
- $d > 2.0''$: `PROBABLE` (isolated) or `AMBIGUOUS`

**Audit Assessment:**
1. Given the SPHEREx centroiding uncertainty of $\sigma \sim 0.2'' - 0.3''$ and WISE positional error $\sigma_{\text{WISE}} \sim 0.03''$, a $3\sigma$ match radius of $0.8''$ is physically well-justified for stationary stars.
2. However, applying this $0.8''$ radius to **unpropagated 2010 coordinates** penalizes stars with proper motions $\ge 50\,\text{mas/yr}$, moving genuine physical counterparts into `PROBABLE`.
3. With 16.55-year proper-motion propagation applied, the $0.8''$ threshold is robust and recovers 914 high-confidence matches.

---

## 7. Corrected Dataset Generation

To rectify these deficiencies without modifying original files, a fully corrected dataset has been persisted to:
[`data/processed/validation/pointing_0003_allwise_propagated_matches.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/validation/pointing_0003_allwise_propagated_matches.csv)

This dataset incorporates:
1. `allwise_ra_prop` and `allwise_dec_prop` propagated to 2026.5496 using Gaia proper motions.
2. `allwise_sep_prop_arcsec` recalculated against SPHEREx centroids.
3. Updated `validated_match_category` reflecting the 58 newly promoted high-confidence matches.
4. `is_wise_beam_blend = True` flagging the 14 sources affected by the 7 shared AllWISE detections.

---

## 8. AllWISE Astrometry Audit Conclusion

The Task 4 AllWISE cross-matching contained a major astrometric flaw: failure to propagate coordinates over the 16.55-year temporal baseline from J2010.0 to 2026.55. This flaw has been isolated, mathematically corrected, and validated.

**Status:** **INCORRECT in original Task 4 implementation; FULLY CORRECTED in Task 4B validation dataset.**

