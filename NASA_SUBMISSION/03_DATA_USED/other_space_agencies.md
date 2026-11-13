# Other Space Agency Datasets Used

**Mission / Agency:** European Space Agency (ESA) Gaia Mission  
**Catalogue Release:** Gaia Data Release 3 (Gaia DR3)  

---

## 1. ESA Gaia DR3 Astrometric Reference Catalogue

### Mission Overview
- **Agency:** European Space Agency (ESA).
- **Core Purpose:** High-precision optical astrometric, photometric, and spectrophotometric survey of over 1.8 billion celestial sources across the Milky Way and beyond.

### Usage in SPECTRA-X
1. **Stationary Background Star Filtering:**
   - In any deep moving-object search, fixed background stars, high proper motion stars, and stellar flare transients can create false moving signals or blending artifacts.
   - SPECTRA-X integrates Gaia DR3 cross-matching within a configurable cone-search radius (default: $3.0^{\prime\prime}$).
   - Candidates with a stationary Gaia DR3 cross-match ($p_{\text{match}} > 0.95$) are flagged as known stellar sources, preventing false classification as Solar System bodies.

2. **Astrometric Calibration & Precision Verification:**
   - Gaia DR3 provides sub-milliarcsecond astrometric positions ($\alpha, \delta$), proper motions ($\mu_\alpha^*, \mu_\delta$), and parallaxes ($\varpi$).
   - Used by the MOTION-X module as the ground-truth celestial reference frame to validate WCS coordinates extracted from user-uploaded FITS images.

### Data Access
- **Endpoint:** ESA Gaia Archive (`https://gea.esac.esa.int/archive/`) and CDS VizieR (`I/355/gaiadr3`).
- **Format:** Ingested via standard IVOA Cone Search and cached tabular parquet/CSV structures.

