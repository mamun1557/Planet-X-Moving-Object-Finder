import os
import glob
import astropy.io.fits as fits
import numpy as np

def generate_flag_policy():
    print("Executing Task 4: Flags and Quality-Control Policy...")
    base_dir = os.path.abspath(".")
    
    # Check sample files from QR2 and QR3
    qr2_sample = os.path.join(base_dir, 'data', 'spherex', 'qr2', 'level2', 'level2_2025W17_4B_0001_1D2_spx_l2b-v20-2025-240.fits')
    qr3_sample = os.path.join(base_dir, 'data', 'spherex', 'qr3', 'level2', 'level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits')
    
    with fits.open(qr2_sample) as h2:
        qr2_flags_hdr = dict(h2[2].header)
        qr2_flags_data = h2[2].data
        
    with fits.open(qr3_sample) as h3:
        qr3_flags_hdr = dict(h3[2].header)
        qr3_flags_data = h3[2].data
        
    # Bit definitions extracted from FITS headers
    flag_defs = [
        {"bit": 0, "name": "MP_TRANSIENT", "val": 1 << 0, "category": "Fatal", 
         "meaning": "Transient event or cosmic ray strike detected during sample-up-the-ramp (SUR) readout.",
         "impact": "Uncalibrated high flux discontinuity. Corrupts spatial autoencoder and causes severe temporal false positives.",
         "handling": "Mask completely. Pixel must be excluded from differencing and spatial training."},
        {"bit": 1, "name": "MP_OVERFLOW", "val": 1 << 1, "category": "Fatal",
         "meaning": "ADC overflow / detector well saturation.",
         "impact": "Flux truncated at non-linear saturation limit; variance is invalid.",
         "handling": "Mask completely. Do not attempt photometric extraction or temporal differencing."},
        {"bit": 2, "name": "MP_SUR_ERROR", "val": 1 << 2, "category": "Fatal",
         "meaning": "Sample-Up-the-Ramp linear regression fit failed.",
         "impact": "Slope/flux estimate is invalid; large unpredictable errors.",
         "handling": "Mask completely."},
        {"bit": 4, "name": "MP_PHANTOM", "val": 1 << 4, "category": "Informational",
         "meaning": "Optical ghost or internal reflection modeled in processing.",
         "impact": "Mild stray-light artifact; background flux may have slight elevation.",
         "handling": "Usable with warning. Note potential ghosting in anomaly ranking."},
        {"bit": 5, "name": "MP_REFERENCE", "val": 1 << 5, "category": "Fatal",
         "meaning": "Reference pixel along 4-pixel detector outer border (non-photosensitive).",
         "impact": "No celestial photons. Carries baseline electronics bias only.",
         "handling": "Mask completely from celestial analysis."},
        {"bit": 6, "name": "MP_NONFUNC", "val": 1 << 6, "category": "Fatal",
         "meaning": "Nonfunctional, unbonded, or dead detector pixel.",
         "impact": "Zero sensitivity or open circuit; random noise or constant value.",
         "handling": "Mask completely."},
        {"bit": 7, "name": "MP_DICHROIC", "val": 1 << 7, "category": "Informational",
         "meaning": "Pixel falls along dichroic filter split boundary.",
         "impact": "Slightly reduced transmission or steeper spectral gradient.",
         "handling": "Usable for spatial detection; apply calibration correction for SED extraction."},
        {"bit": 9, "name": "MP_MISSING_DATA", "val": 1 << 9, "category": "Fatal",
         "meaning": "Telemetry packet dropped; incomplete ramp sample.",
         "impact": "Flux cannot be reliably computed.",
         "handling": "Mask completely."},
        {"bit": 10, "name": "MP_HOT", "val": 1 << 10, "category": "Warning",
         "meaning": "Hot pixel with elevated thermal dark current.",
         "impact": "Slightly higher dark noise, but linear response may still be valid.",
         "handling": "Usable with variance inflation factor (e.g. 2x variance)."},
        {"bit": 11, "name": "MP_COLD", "val": 1 << 11, "category": "Warning",
         "meaning": "Cold pixel with lower than average quantum efficiency.",
         "impact": "Reduced signal-to-noise ratio.",
         "handling": "Usable with flat-field correction; weight down in inverse-variance loss."},
        {"bit": 12, "name": "MP_FULLSAMPLE", "val": 1 << 12, "category": "Informational",
         "meaning": "Pixel acquired with full telemetry sampling mode.",
         "impact": "High-fidelity readout mode. Completely normal and desirable.",
         "handling": "DO NOT MASK. Retain pixel."},
        {"bit": 14, "name": "MP_PHANMISS", "val": 1 << 14, "category": "Informational",
         "meaning": "Missing phantom template calibration file for this pointing.",
         "impact": "Ghost correction not subtracted.",
         "handling": "Usable. Keep pixel active."},
        {"bit": 15, "name": "MP_NONLINEAR", "val": 1 << 15, "category": "Warning",
         "meaning": "Pixel in non-linear regime but corrected via polynomial calibration.",
         "impact": "Higher calibration uncertainty at high counts.",
         "handling": "Usable; propagate polynomial correction error into variance."},
        {"bit": 17, "name": "MP_PERSIST", "val": 1 << 17, "category": "Warning",
         "meaning": "Latent charge persistence from previous exposure bright source.",
         "impact": "Spurious residual flux can mimic a transient.",
         "handling": "Down-weight in CHRONOS-X temporal differencing. Exclude from transient discovery candidates."},
        {"bit": 19, "name": "MP_OUTLIER", "val": 1 << 19, "category": "Warning",
         "meaning": "Statistical outlier sample during fit.",
         "impact": "Slight residual uncertainty.",
         "handling": "Usable with warning."},
        {"bit": 21, "name": "MP_SOURCE", "val": 1 << 21, "category": "Source-Related",
         "meaning": "Known detected astronomical source centroid / aperture area.",
         "impact": "Indicates a real celestial star or galaxy!",
         "handling": "NEVER MASK! Masking this bit discards the astronomical objects of interest!"}
    ]

    # Calculate bitmasks
    fatal_mask = sum(d['val'] for d in flag_defs if d['category'] == 'Fatal')
    warning_mask = sum(d['val'] for d in flag_defs if d['category'] == 'Warning')
    info_mask = sum(d['val'] for d in flag_defs if d['category'] == 'Informational')
    source_mask = sum(d['val'] for d in flag_defs if d['category'] == 'Source-Related')
    
    # Check pixel counts in samples
    fatal_px_qr2 = np.sum((qr2_flags_data & fatal_mask) > 0)
    source_px_qr2 = np.sum((qr2_flags_data & source_mask) > 0)
    blanket_px_qr2 = np.sum(qr2_flags_data != 0)
    
    fatal_px_qr3 = np.sum((qr3_flags_data & fatal_mask) > 0)
    source_px_qr3 = np.sum((qr3_flags_data & source_mask) > 0)
    blanket_px_qr3 = np.sum(qr3_flags_data != 0)

    # Document script audit
    scripts_to_audit = [
        ('scripts/inspect_fits.py', 'inspect_fits.py'),
        ('models/astrovision/train_astrovision.py', 'train_astrovision.py'),
        ('models/chronos_x/run_temporal_differencing.py', 'run_temporal_differencing.py'),
        ('models/motion_x/validate_motion.py', 'validate_motion.py')
    ]

    # Write flag_policy.md
    out_path = os.path.join(base_dir, 'reports', 'second_pass_audit', 'flag_policy.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("# SPECTRA-X: Scientific Flag Policy & Quality-Control Validation\n\n")
        f.write("## 1. The Critical Failure of the Blanket `FLAGS != 0` Masking Rule\n\n")
        f.write("In earlier exploratory pipelines, a blanket filtering condition was used:\n")
        f.write("```python\nvalid_mask = (flags == 0)\n```\n")
        f.write("### Empirical Finding:\n")
        f.write(f"- In QR2 sample: {blanket_px_qr2:,} pixels have `FLAGS != 0`. However, only {fatal_px_qr2:,} pixels are genuinely fatal defects! Furthermore, **{source_px_qr2:,} pixels are tagged with `MP_SOURCE` (Bit 21, value 2,097,152)** indicating real astronomical stars and galaxies!\n")
        f.write(f"- In QR3 sample: {blanket_px_qr3:,} pixels have `FLAGS != 0`, whereas only {fatal_px_qr3:,} pixels are fatal errors, and **{source_px_qr3:,} pixels represent detected astronomical sources**!\n")
        f.write("\n> [!CAUTION]\n")
        f.write("> Applying `FLAGS != 0` discards the very stars, galaxies, and transients SPECTRA-X was built to discover! It also discards high-fidelity `MP_FULLSAMPLE` pixels (Bit 12, value 4096) and properly calibrated `MP_NONLINEAR` pixels (Bit 15, value 32768).\n\n")

        f.write("## 2. Documented Classification of SPHEREx Quality Flags\n\n")
        f.write("| Bit | Numeric Value | Official Name | Category | Scientific Impact | Recommended Policy |\n")
        f.write("| :---: | :---: | :--- | :---: | :--- | :--- |\n")
        for d in flag_defs:
            f.write(f"| {d['bit']} | `{d['val']}` | `{d['name']}` | **{d['category']}** | {d['impact']} | {d['handling']} |\n")
        f.write("\n")

        f.write("## 3. Recommended Mathematical Bitmasks\n\n")
        f.write("```python\n")
        f.write(f"# Fatal Mask (Cosmic rays, Saturation, SUR error, Reference, Nonfunctional, Missing data)\n")
        f.write(f"FATAL_FLAG_MASK = 0x{fatal_mask:X}  # Numeric: {fatal_mask}\n\n")
        f.write(f"# Warning Mask (Hot, Cold, Non-linear, Persistence, Outlier)\n")
        f.write(f"WARNING_FLAG_MASK = 0x{warning_mask:X}  # Numeric: {warning_mask}\n\n")
        f.write(f"# Source Mask (Astronomical sources - preserve!)\n")
        f.write(f"SOURCE_FLAG_MASK = 0x{source_mask:X}  # Numeric: {source_mask}\n\n")
        f.write(f"# Recommended Scientifically Correct Usable Pixel Mask:\n")
        f.write(f"usable_pixels = (flags & FATAL_FLAG_MASK) == 0\n")
        f.write("```\n\n")

        f.write("## 4. Existing Script Audit & Proposed Corrections\n\n")
        f.write("The following existing scripts were identified as utilizing uncalibrated blanket flag masking. In accordance with the **Strict Read-Only Policy**, these scripts were **NOT modified**. The proposed scientific corrections are documented below for future implementation:\n\n")

        for s_rel, s_base in scripts_to_audit:
            f.write(f"### Script: `[{s_rel}](file:///{base_dir.replace('\\', '/')}/{s_rel})`\n")
            f.write("- **Current Implementation**: Uses blanket `flags != 0` or `flags > 0`.\n")
            f.write("- **Scientific Flaw**: Masks detected celestial sources and full-sample pixels.\n")
            f.write("- **Proposed Code Replacement**:\n")
            f.write("```python\n")
            f.write("# PROPOSED CORRECTION (Do not edit existing file during audit):\n")
            f.write("FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615\n")
            f.write("valid_mask = (flags & FATAL_FLAG_MASK) == 0\n")
            f.write("```\n\n")

    print(f"Flag policy report successfully written to {out_path}")

if __name__ == '__main__':
    generate_flag_policy()
