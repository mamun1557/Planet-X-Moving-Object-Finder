# SPECTRA-X: Scientific Flag Policy & Quality-Control Validation

## 1. The Critical Failure of the Blanket `FLAGS != 0` Masking Rule

In earlier exploratory pipelines, a blanket filtering condition was used:
```python
valid_mask = (flags == 0)
```
### Empirical Finding:
- In QR2 sample: 943,310 pixels have `FLAGS != 0`. However, only 20,993 pixels are genuinely fatal defects! Furthermore, **822,376 pixels are tagged with `MP_SOURCE` (Bit 21, value 2,097,152)** indicating real astronomical stars and galaxies!
- In QR3 sample: 2,032,360 pixels have `FLAGS != 0`, whereas only 26,063 pixels are fatal errors, and **1,935,346 pixels represent detected astronomical sources**!

> [!CAUTION]
> Applying `FLAGS != 0` discards the very stars, galaxies, and transients SPECTRA-X was built to discover! It also discards high-fidelity `MP_FULLSAMPLE` pixels (Bit 12, value 4096) and properly calibrated `MP_NONLINEAR` pixels (Bit 15, value 32768).

## 2. Documented Classification of SPHEREx Quality Flags

| Bit | Numeric Value | Official Name | Category | Scientific Impact | Recommended Policy |
| :---: | :---: | :--- | :---: | :--- | :--- |
| 0 | `1` | `MP_TRANSIENT` | **Fatal** | Uncalibrated high flux discontinuity. Corrupts spatial autoencoder and causes severe temporal false positives. | Mask completely. Pixel must be excluded from differencing and spatial training. |
| 1 | `2` | `MP_OVERFLOW` | **Fatal** | Flux truncated at non-linear saturation limit; variance is invalid. | Mask completely. Do not attempt photometric extraction or temporal differencing. |
| 2 | `4` | `MP_SUR_ERROR` | **Fatal** | Slope/flux estimate is invalid; large unpredictable errors. | Mask completely. |
| 4 | `16` | `MP_PHANTOM` | **Informational** | Mild stray-light artifact; background flux may have slight elevation. | Usable with warning. Note potential ghosting in anomaly ranking. |
| 5 | `32` | `MP_REFERENCE` | **Fatal** | No celestial photons. Carries baseline electronics bias only. | Mask completely from celestial analysis. |
| 6 | `64` | `MP_NONFUNC` | **Fatal** | Zero sensitivity or open circuit; random noise or constant value. | Mask completely. |
| 7 | `128` | `MP_DICHROIC` | **Informational** | Slightly reduced transmission or steeper spectral gradient. | Usable for spatial detection; apply calibration correction for SED extraction. |
| 9 | `512` | `MP_MISSING_DATA` | **Fatal** | Flux cannot be reliably computed. | Mask completely. |
| 10 | `1024` | `MP_HOT` | **Warning** | Slightly higher dark noise, but linear response may still be valid. | Usable with variance inflation factor (e.g. 2x variance). |
| 11 | `2048` | `MP_COLD` | **Warning** | Reduced signal-to-noise ratio. | Usable with flat-field correction; weight down in inverse-variance loss. |
| 12 | `4096` | `MP_FULLSAMPLE` | **Informational** | High-fidelity readout mode. Completely normal and desirable. | DO NOT MASK. Retain pixel. |
| 14 | `16384` | `MP_PHANMISS` | **Informational** | Ghost correction not subtracted. | Usable. Keep pixel active. |
| 15 | `32768` | `MP_NONLINEAR` | **Warning** | Higher calibration uncertainty at high counts. | Usable; propagate polynomial correction error into variance. |
| 17 | `131072` | `MP_PERSIST` | **Warning** | Spurious residual flux can mimic a transient. | Down-weight in CHRONOS-X temporal differencing. Exclude from transient discovery candidates. |
| 19 | `524288` | `MP_OUTLIER` | **Warning** | Slight residual uncertainty. | Usable with warning. |
| 21 | `2097152` | `MP_SOURCE` | **Source-Related** | Indicates a real celestial star or galaxy! | NEVER MASK! Masking this bit discards the astronomical objects of interest! |

## 3. Recommended Mathematical Bitmasks

```python
# Fatal Mask (Cosmic rays, Saturation, SUR error, Reference, Nonfunctional, Missing data)
FATAL_FLAG_MASK = 0x267  # Numeric: 615

# Warning Mask (Hot, Cold, Non-linear, Persistence, Outlier)
WARNING_FLAG_MASK = 0xA8C00  # Numeric: 691200

# Source Mask (Astronomical sources - preserve!)
SOURCE_FLAG_MASK = 0x200000  # Numeric: 2097152

# Recommended Scientifically Correct Usable Pixel Mask:
usable_pixels = (flags & FATAL_FLAG_MASK) == 0
```

## 4. Existing Script Audit & Proposed Corrections

The following existing scripts were identified as utilizing uncalibrated blanket flag masking. In accordance with the **Strict Read-Only Policy**, these scripts were **NOT modified**. The proposed scientific corrections are documented below for future implementation:

### Script: `[scripts/inspect_fits.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/scripts/inspect_fits.py)`
- **Current Implementation**: Uses blanket `flags != 0` or `flags > 0`.
- **Scientific Flaw**: Masks detected celestial sources and full-sample pixels.
- **Proposed Code Replacement**:
```python
# PROPOSED CORRECTION (Do not edit existing file during audit):
FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615
valid_mask = (flags & FATAL_FLAG_MASK) == 0
```

### Script: `[models/astrovision/train_astrovision.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/astrovision/train_astrovision.py)`
- **Current Implementation**: Uses blanket `flags != 0` or `flags > 0`.
- **Scientific Flaw**: Masks detected celestial sources and full-sample pixels.
- **Proposed Code Replacement**:
```python
# PROPOSED CORRECTION (Do not edit existing file during audit):
FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615
valid_mask = (flags & FATAL_FLAG_MASK) == 0
```

### Script: `[models/chronos_x/run_temporal_differencing.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/chronos_x/run_temporal_differencing.py)`
- **Current Implementation**: Uses blanket `flags != 0` or `flags > 0`.
- **Scientific Flaw**: Masks detected celestial sources and full-sample pixels.
- **Proposed Code Replacement**:
```python
# PROPOSED CORRECTION (Do not edit existing file during audit):
FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615
valid_mask = (flags & FATAL_FLAG_MASK) == 0
```

### Script: `[models/motion_x/validate_motion.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/motion_x/validate_motion.py)`
- **Current Implementation**: Uses blanket `flags != 0` or `flags > 0`.
- **Scientific Flaw**: Masks detected celestial sources and full-sample pixels.
- **Proposed Code Replacement**:
```python
# PROPOSED CORRECTION (Do not edit existing file during audit):
FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615
valid_mask = (flags & FATAL_FLAG_MASK) == 0
```

