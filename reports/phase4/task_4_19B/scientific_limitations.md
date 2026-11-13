# Scientific Limitations & Systematic Uncertainties Audit
## Phase 4, Task 4.19B — External Catalog Acquisition & Exact-Footprint Crossmatch
**Module:** ASTROVISION + Spatial Evidence Audit  
**Pipeline Build:** `l2b-v27-2026-222`  
**Parent Tasks:** Phase 4 Tasks 4.17, 4.18, 4.18-SKY, 4.19A, 4.19B  
**Target Cohort:** 1,500 Blind Evaluation Cutouts (Pointings P0002, P0009, P0010)

---

### 1. Executive Overview

This document establishes the scientific limitations, astrometric systematic uncertainties, catalog completeness boundaries, and resolution mismatches inherent to external catalog ingestion (Gaia DR3, 2MASS PSC, and CatWISE2020) across SPHEREx Level-2 evaluation cutouts. While Task 4.19B empirically proves that expanding the search geometry from the restricted detector-centered cone of Task 4.17 ($r=0.85^\circ$) to the true cutout footprints expands evaluation cohort coverage to 100%, external catalogs do not provide an exhaustive or unbiased ground-truth census of all astrophysical sources in the infrared sky.

---

### 2. Catalog Completeness Limits & Sensitivity Thresholds

| Catalog | Primary Bands | Completeness Limit (Vega / AB) | Typical Flux Sensitivity | Primary Sensitivity Regime | Missing Population |
|:---|:---|:---|:---|:---|:---|
| **Gaia DR3** | $G, G_{\rm BP}, G_{\rm RP}$ (Optical $0.33-1.05\,\mu\text{m}$) | $G \approx 20.7\text{ mag}$ (completeness)<br>$G \approx 21.5\text{ mag}$ (detection limit) | $\sim 10^{-6}\text{ Jy}$ (optical) | Main sequence stars, white dwarfs, optical transients, blue stars | Heavily reddened giants, deeply embedded protostars, cool T/Y brown dwarfs ($T_{\rm eff} < 800\text{ K}$), diffuse dust |
| **2MASS PSC** | $J, H, K_s$ (Near-IR $1.25-2.17\,\mu\text{m}$) | $J \approx 15.8\text{ mag}$<br>$H \approx 15.1\text{ mag}$<br>$K_s \approx 14.3\text{ mag}$ ($10\sigma$) | $\sim 1\text{ mJy}$ ($K_s$) | Galactic stars, bright near-IR sources, red giants | Faint infrared background stars, low-mass brown dwarfs, extragalactic faint sources |
| **CatWISE2020** | $W1, W2$ (Mid-IR $3.4\,\mu\text{m}, 4.6\,\mu\text{m}$) | $W1 \approx 17.7\text{ mag}$<br>$W2 \approx 17.5\text{ mag}$ (AB) | $\sim 15\,\mu\text{Jy}$ ($W1$)<br>$\sim 25\,\mu\text{Jy}$ ($W2$) | Cool low-mass stars, brown dwarfs, AGN, infrared dust emission | Very faint optical sources with zero infrared excess |
| **SPHEREx Level-2** | 102 Spectral Channels ($0.75-5.00\,\mu\text{m}$) | $5\sigma$ point-source sensitivity: $\sim 19-19.5\text{ mag}$ ($AB$) | $\sim 5-10\,\mu\text{Jy}$ per spectral channel | Full continuous spectral energy distribution ($R \approx 35-130$) | Sources below SPHEREx single-exposure SNR threshold |

#### Critical Implication:
A significant fraction of astrophysical sources detected by SPHEREx at wavelengths $\lambda > 3.0\,\mu\text{m}$ (especially cold brown dwarfs, obscured asymptotic giant branch [AGB] stars, and young stellar objects [YSOs] with severe circumstellar extinction $A_V > 10\text{ mag}$) fall well below the Gaia DR3 optical detection threshold ($G > 21.5$). Consequently, an absence of a Gaia counterpart within a SPHEREx cutout **cannot** be scientifically interpreted as proof that a detected feature is a detector artifact or non-astronomical anomaly.

---

### 3. Spatial Resolution Mismatch & Beam Confusion

A foundational challenge when crossmatching SPHEREx with high-resolution external catalogs is the substantial beam size and pixel scale divergence:

```
+-----------------------------------------------------------------------------+
| Beam Size Comparison (Full Width at Half Maximum / Pixel Scale)             |
|                                                                             |
| Gaia DR3 PSF FWHM:          ~0.10" - 0.12"  [Diffraction-limited optical]   |
| 2MASS PSC Seeing FWHM:      ~2.50" - 3.00"  [Ground-based near-IR]          |
| CatWISE2020 PSF FWHM:       ~6.10" (W1), ~6.40" (W2)  [Space mid-IR]        |
| SPHEREx Pixel Scale:        ~6.20" x 6.20"  [Instrumental native pixel]     |
| SPHEREx Effective PSF FWHM: ~6.00" - 8.00"  [Diffraction + optical blur]    |
+-----------------------------------------------------------------------------+
```

#### Systematic Effects:
1. **Source Blending (Beam Confusion):**
   Within a single SPHEREx pixel footprint ($6.2'' \times 6.2'' \approx 38.44\text{ arcsec}^2$), high stellar density fields (such as those in Galactic plane pointings or globular clusters) frequently contain between 2 and 15 distinct Gaia DR3 sources.
   - When ASTROVISION measures flux within a $128 \times 128$ pixel cutout ($13.2' \times 13.2'$), the measured spatial profile represents the linear superposition (convolution) of multiple unresolved stellar PSFs.
   - Masking individual point sources using a fixed circular radius (e.g., $r = 2\text{ pixels} \approx 12.4''$) centered on each Gaia position will result in overlapping mask regions that can unintentionally occult genuine background diffuse structures or real spatial anomalies.
2. **Astrometric Centroid Shifts:**
   If a single SPHEREx detection corresponds to an unresolved binary or multiple stellar group, the flux-weighted SPHEREx photocenter will reside at the center of light, which does not coincide with any individual Gaia DR3 coordinate. The resulting positional offset ($\Delta \theta \sim 1-3''$) is an expected consequence of resolution blending, not an astrometric error in either catalog.

---

### 4. Astrometric Epoch Propagation & Proper Motion Limitations

The temporal baseline between external catalog reference epochs and the SPHEREx mission flight epoch creates non-negligible astrometric displacement:

- **Gaia DR3 Reference Epoch:** $\text{J}2016.0$ ($2016.000$)
- **2MASS PSC Reference Epoch:** $\text{J}2000.0$ ($1997.5 - 2001.2$, nominal $\sim 1999.0$)
- **CatWISE2020 Reference Epoch:** $\text{J}2010.0 - \text{J}2019.0$ (nominal $\text{MJD} \approx 57100$, epoch $\sim 2015.2$)
- **SPHEREx Pipeline Observation Epoch:** $2026.5496$ ($\Delta t_{\rm Gaia} = +10.5496\text{ years}$, $\Delta t_{\rm 2MASS} \approx +26.5\text{ years}$)

#### Rigorous Propagation Model (Task 4.19B):
For all Gaia DR3 sources with non-null proper motions ($\mu_{\alpha*}, \mu_\delta$), coordinates were propagated to epoch $2026.5496$ via:
$$\Delta \alpha = \frac{\mu_{\alpha*} \cdot \Delta t}{\cos(\delta)} \times \frac{1}{3600 \times 1000}$$
$$\Delta \delta = \mu_\delta \cdot \Delta t \times \frac{1}{3600 \times 1000}$$

#### Unpropagated Catalogs & High Proper Motion (HPM) Bias:
1. **2MASS PSC and CatWISE2020 Missing Proper Motions:**
   While CatWISE2020 provides proper motions for a subset of bright sources, 2MASS PSC is an epoch $\sim 2000.0$ snapshot. A star with moderate Galactic disk proper motion ($\mu \approx 100\text{ mas/yr}$) travels:
   $$\Delta \theta_{\rm 2MASS} = 100\text{ mas/yr} \times 26.5\text{ yr} = 2.65\text{ arcsec} \approx 0.43\text{ SPHEREx pixels}$$
   High proper motion stars ($\mu > 500\text{ mas/yr}$) displace by $> 13\text{ arcsec}$ ($> 2.1\text{ SPHEREx pixels}$), shifting completely out of their initial single-pixel containment.
2. **Gaia DR3 Sources Without 5-Parameter Astrometry:**
   Approximately $12-18\%$ of faint Gaia DR3 sources ($G > 20.0$) lack statistically significant proper motion determinations and possess only 2-parameter astrometry ($\alpha, \delta$). For these sources, coordinates remain at epoch J2016.0. However, faint distant stars rarely exhibit $\mu > 10\text{ mas/yr}$ ($\Delta \theta < 0.1'' \ll 6.2''$), keeping the astrometric propagation error well below $0.02\text{ SPHEREx pixels}$.

---

### 5. Spectral Energy Distribution (SED) & Color Selection Biases

Each catalog samples a fundamentally different optical/infrared regime, producing strong population-level selection biases:

```
0.3 um     0.7 um     1.0 um       2.2 um          3.4 um        5.0 um
|----------|----------|------------|---------------|-------------|
  [--- Gaia DR3 ---]
                      [-- 2MASS --]
                                      [---- CatWISE2020 ----]
           [------------------- SPHEREx ------------------------]
```

1. **Extreme Reddening ($A_V > 15\text{ mag}$):**
   In dense interstellar molecular clouds, optical light is attenuated by factors exceeding $10^6$. Stars readily detected in SPHEREx channel 102 ($4.8-5.0\,\mu\text{m}$) or CatWISE $W2$ ($4.6\,\mu\text{m}$) will have $G_{\rm app} > 25\text{ mag}$, dropping entirely out of Gaia DR3.
2. **Ultracool Dwarfs (T and Y Spectral Classes):**
   Atmospheres dominated by methane ($\text{CH}_4$) and water vapor absorb strongly in the optical and $K$-band, but exhibit bright emission windows at $4.6\,\mu\text{m}$ (SPHEREx Band 4 / CatWISE $W2$). Such objects are invisible to Gaia and 2MASS.
3. **Artifact Attribution Caveat:**
   When an ASTROVISION false positive coincides with a CatWISE2020 source but lacks a Gaia DR3 counterpart, the detection is almost certainly a genuine red/infrared astrophysical emitter (e.g., an AGB star or background AGN) rather than an instrumental anomaly.

---

### 6. External Catalog Footprint Coverage & Unqueried Catalogs

#### Why Pan-STARRS1 (PS1) Was Not Queried Globally:
- Pan-STARRS1 $3\pi$ Survey is strictly bounded in celestial declination to $\delta > -30^\circ$.
- SPHEREx evaluation pointing **P0010** is centered at:
  $$\alpha \approx 89.28^\circ, \quad \delta \approx -60.05^\circ$$
- Pointing P0010 is situated in the deep Southern celestial hemisphere, completely outside the physical coverage of Pan-STARRS1. Ingesting PS1 would have introduced severe pointing-dependent selection heterogeneity (covering P0002 and P0009, while leaving P0010 at 0% coverage).

#### unWISE Coadds vs. CatWISE2020:
- CatWISE2020 is derived directly from unWISE coadded images (incorporating 16 epochs of WISE/NEOWISE data through 2018), with advanced PSF-fitting photometry and motion modeling optimized specifically for faint point sources.
- For point-source counterpart matching, CatWISE2020 provides higher astrometric fidelity and fainter point-source completeness than the raw unWISE pixel coadds or AllWISE catalog.

---

### 7. Methodological Audit Summary & Recommendations

1. **Never equate "Unmatched to Gaia DR3" with "Artifact":**
   Multi-wavelength infrared coverage (CatWISE2020, 2MASS) is essential to avoid misclassifying real obscured stellar sources as detector noise.
2. **Account for Multi-Source Blending in Masking:**
   Any downstream catalog-aware masking module (such as `CatalogAwareSourceMasker`) must handle high source density without blanketing entire cutouts. Dynamic mask dilation radii scaled to catalog flux or magnitude are strongly recommended over uniform circular dilation.
3. **Astrometric Tolerances:**
   Given SPHEREx's $6.2''/\text{px}$ scale, a crossmatch matching radius of $r_{\rm match} = 3.1''$ (0.5 pixels) to $6.2''$ (1.0 pixel) represents the optimal compromise between association confidence and confusion contamination.

