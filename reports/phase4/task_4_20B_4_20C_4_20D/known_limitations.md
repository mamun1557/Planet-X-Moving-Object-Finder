# Known Scientific & Operational Limitations
## Phase 4 Combined Engineering Sprint (Tasks 4.20B + 4.20C + 4.20D)

**Pipeline Build:** `l2b-v27-2026-222`  
**Audit Date:** 2026-11-08  

---

### 1. MOTION-X Keplerian Ephemeris Engine Limitations

1. **Unperturbed Two-Body Assumption:**
   The `KeplerianEphemerisEngine` solves the classic 2-body Kepler problem (Sun + Minor Planet). It does **not** integrate:
   - Gravitational perturbations from Jupiter, Saturn, or the Earth-Moon system.
   - Non-gravitational forces (cometary outgassing, Yarkovsky diurnal thermal recoil).
   - Relativistic perihelion advance.
   *Operational Boundary:* High accuracy ($\Delta \theta < 1\text{ arcsec}$) near the osculating epoch $t_0$. Ephemeris error grows to $\sim 10-20\text{ arcmin}$ over multi-year baselines ($5\text{ years}$).
2. **Zero In-FOV Asteroids in Ingested Pointings:**
   No known asteroids, comets, or NEOs fell within the $3.5^\circ \times 3.5^\circ$ fields of view of the downloaded QR2 and QR3 pointings. Real-sky asteroid recovery remains scientifically pending on-orbit observations of ecliptic fields.

---

### 2. SPECTRA Multi-Catalog Infrared Evidence Limitations

1. **Photometric Color $\ne$ Spectroscopic Confirmation:**
   Broadband excess ($Ks - W2 > 0.5\text{ mag}$) indicates infrared excess consistent with circumstellar dust, cool stellar companions, or active galactic nuclei (AGN). It cannot replace 102-channel continuous SPHEREx spectroscopy.
2. **Upper-Limit and Detection Thresholds:**
   In faint sources ($W1 > 17\text{ mag}$, $W2 > 16.5\text{ mag}$), non-detections in ALLWISE or 2MASS must be treated as upper limits, preventing spurious excess claims.
3. **Beam Confusion at Low Spatial Resolution:**
   SPHEREx's $6.2''/\text{pixel}$ beam can blend multiple optical/infrared stars. Positional separations $\Delta \theta > 1.5''$ between Gaia and WISE may represent confused blends.

---

### 3. CHRONOS-X Sub-Pixel Registration Limitations

1. **Dither Alignment is NOT Secular Variability:**
   Sub-pixel phase correlation remediates intra-visit pointing jitter ($2.15-6.47\text{ minute}$ dither cadences) to suppress false subtraction dipoles. It does **not** provide temporal validation for long-term astrophysical transients (supernovae, novae, secular variables).
2. **Absence of Multi-Epoch Repeat Observations:**
   The repository contains **zero multi-day or multi-week repeat visits**. Real-sky transient discovery cannot be claimed until true multi-epoch revisit datasets are downlinked and calibrated.
3. **Maximum Shift Gating:**
   Displacements $>8.0\text{ pixels}$ are rejected fail-closed to prevent phase wrap-around aliasing.

---

### 4. Summary of Scientific Governance Rules

- Never claim asteroid recovery from ephemeris propagation alone.
- Never convert missing catalog photometry to zero flux.
- Never promote upper limits to excess detections.
- Never describe intra-visit dithers as secular transients.
- Never modify frozen model checkpoints (`astrovision_spatial_v3.pt`, `spectra_masked_ae_v2.pt`).
