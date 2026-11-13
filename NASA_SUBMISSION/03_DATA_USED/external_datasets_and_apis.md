# External Astronomical Datasets, Catalogs & APIs

**Project:** SPECTRA-X  
**Challenge:** Planet X: Moving Object Finder  

---

## 1. Multi-Wavelength Reference Catalogs

### A. Two Micron All Sky Survey (2MASS)
- **Facility:** Mt. Hopkins, Arizona & Cerro Tololo, Chile (NASA/Caltech/IPAC).
- **Bands:** $J$ ($1.25\ \mu\text{m}$), $H$ ($1.65\ \mu\text{m}$), and $K_s$ ($2.17\ \mu\text{m}$).
- **Role:** Provides near-infrared baseline flux anchors. Used to calibrate the shorter-wavelength channels (Array 1 & Array 2) of the SPHEREx 102-channel spectrophotometry and verify historical stationary detections.

### B. Wide-field Infrared Survey Explorer (WISE / ALLWISE / NEOWISE)
- **Facility:** NASA Explorer Mission (Caltech/JPL).
- **Bands:** $W1$ ($3.4\ \mu\text{m}$), $W2$ ($4.6\ \mu\text{m}$), $W3$ ($12\ \mu\text{m}$), and $W4$ ($22\ \mu\text{m}$).
- **Role:** Mid-infrared thermal emission comparison. Thermal emissions of outer Solar System bodies rise significantly between 3.0 and 5.0 $\mu$m; ALLWISE catalog queries enable cross-validation of red spectral indices detected in SPHEREx Arrays 5 and 6.

---

## 2. Astronomical APIs & Software Libraries

### A. Astropy Astronomical Infrastructure
- **Package:** `astropy` (v6.0+)
- **Components:**
  - `astropy.io.fits`: Flexible Image Transport System parser and FITS header validation.
  - `astropy.wcs`: World Coordinate System transformations, tangent plane projections, and distortion handling.
  - `astropy.coordinates`: Celestial coordinate conversions (ICRS, Galactic, Ecliptic) and angular separation solvers (`SkyCoord.separation`).
  - `astropy.time`: High-precision Julian Date (`JD`) and barycentric dynamical time (`TDB`) calculations.

### B. Astrometry.net & CDS TAP Services
- **Standards:** IVOA Table Access Protocol (TAP) and Simple Cone Search (SCS) protocols.
- **Role:** Used for cross-identification of stationary point sources across astronomical archives without downloading multi-terabyte raw catalogues.
