# Scientific Limitations & Systematic Uncertainties
## Phase 4, Task 4.19C — Controlled Spatial Null Models & PSF Contamination Audit

**Pipeline Build:** `l2b-v27-2026-222`  
**Parent Tasks:** Phase 4 Tasks 4.12–4.19C  

---

### 1. Catalog Completeness Limits vs. False-Positive Attribution
1. **Optical Sensitivity Thresholds:**
   Gaia DR3 completeness drops rapidly beyond $G \approx 20.7\text{ mag}$ (faintest sources $\sim 21.5\text{ mag}$). While 100% of the 45 baseline false positives contain catalog sources within their $128 \times 128$ pixel footprints, very faint stars ($G > 22$) or cold, dust-obscured red sources that lack CatWISE detections may exist undetected.
2. **Infrared Color Mismatch:**
   SPHEREx observes between $0.75\,\mu\text{m}$ and $5.0\,\mu\text{m}$. Gaia DR3 measures optical flux ($0.33-1.05\,\mu\text{m}$). An optical magnitude $G$ cannot directly predict the infrared flux in SPHEREx channel 102 ($4.8-5.0\,\mu\text{m}$). For example, an AGB star or cool brown dwarf may be faint in Gaia ($G \approx 20$) but extremely bright in SPHEREx Band 4, causing substantial local infrared saturation that optical catalogs underestimate.

---

### 2. Beam Confusion and Spatial Resolution Limits
- **Pixel Scale Divergence:**
  SPHEREx's native pixel scale is $\approx 6.215''/\text{pixel}$ (effective PSF FWHM $\sim 6-8''$). Gaia DR3 astrometric precision is sub-milliarcsecond ($< 0.001''$).
- **Source Blending:**
  Because multiple stars can fall within a single $6.2''$ pixel, when ASTROVISION detects a spatial anomaly at $(x_{\rm rec}, y_{\rm rec})$, the measured flux may be the composite superposition of multiple unresolved catalog stars. Positional association with the nearest catalog star does not preclude blended flux contributions from neighboring secondary stars.

---

### 3. Spatial Null-Model Limitations
1. **Uniform Random-Position Model (D1):**
   Real astronomical fields exhibit non-Poisson spatial clustering, interstellar extinction gradients, and stellar density variations. While the uniform random null model provides a baseline for random geometric coincidence, it underestimates the chance probability of hitting a star in high-density clustered sub-regions.
2. **Shifted-Coordinate Model (D2):**
   The shifted-coordinate model preserves local crowding and extinction gradients by shifting the reference point within the same cutout. However, shifts $\Delta r \in [5, 20]\text{ pixels}$ may sample adjacent stellar clusters or bright star halos, introducing minor correlation with large-scale structures.

---

### 4. Masking Radius Trade-Offs
- A uniform large dilation radius ($r \ge 3\text{ pixels}$) eliminates 73% of false alarms, but encroaches into the central evaluation aperture, reducing genuine point-source anomaly recovery from $34.80\%$ to $34.60\%$ and extended recovery from $17.40\%$ to $17.20\%$.
- Magnitude-adaptive masking (Adaptive-A) solves this trade-off by scaling mask radius to catalog flux, achieving $75.6\%$ suppression without any degradation in genuine anomaly recovery ($34.80\% / 17.40\%$ preserved).
