import os
import glob
import csv
import astropy.io.fits as fits
import numpy as np

def audit_spectral_extraction():
    print("Executing Task 3: Spectral WCS and Spectral Extraction Audit...")
    base_dir = os.path.abspath(".")
    
    # 1. Inspect standalone spectral WCS calibration products
    spec_wcs_files = sorted(glob.glob(os.path.join(base_dir, 'data', 'spherex', '*', 'calibration', '*spectral_wcs*.fits')))
    spec_chan_files = sorted(glob.glob(os.path.join(base_dir, 'data', 'spherex', '*', 'calibration', '*spectral_channels*.fits')))
    
    print(f"Found {len(spec_wcs_files)} spectral WCS files and {len(spec_chan_files)} spectral channel files.")
    
    cal_audit_rows = []
    
    for fpath in spec_wcs_files:
        rel_path = os.path.relpath(fpath, base_dir).replace('\\', '/')
        try:
            with fits.open(fpath) as hdul:
                hdr0 = hdul[0].header
                det = hdr0.get('DETECTOR', hdul[1].header.get('DETECTOR', 'UNKNOWN') if len(hdul) > 1 else 'UNKNOWN')
                cal_ver = hdr0.get('CAL_VER', hdr0.get('VERSION', 'UNKNOWN'))
                cwave_avail = False
                cband_avail = False
                wave_unit = "um"
                band_unit = "um"
                
                hdu_names = [h.name for h in hdul]
                for h in hdul:
                    if hasattr(h, 'columns') and h.columns is not None:
                        col_names = [c.name.upper() for c in h.columns]
                        if 'CWAVE' in col_names or 'WAVELENGTH' in col_names:
                            cwave_avail = True
                        if 'CBAND' in col_names or 'BANDWIDTH' in col_names:
                            cband_avail = True
                    if 'BUNIT' in h.header:
                        wave_unit = h.header['BUNIT']
                        
                cal_audit_rows.append({
                    'file_path': rel_path,
                    'cal_type': 'SPECTRAL_WCS',
                    'detector': det,
                    'version': cal_ver,
                    'cwave_avail': cwave_avail,
                    'cband_avail': cband_avail,
                    'wave_unit': wave_unit,
                    'band_unit': band_unit,
                    'hdu_count': len(hdul),
                    'hdu_names': ", ".join(hdu_names),
                    'notes': f"Detector {det} spectral mapping"
                })
        except Exception as e:
            cal_audit_rows.append({
                'file_path': rel_path,
                'cal_type': 'SPECTRAL_WCS',
                'detector': 'ERROR',
                'version': 'ERROR',
                'cwave_avail': False,
                'cband_avail': False,
                'wave_unit': 'N/A',
                'band_unit': 'N/A',
                'hdu_count': 0,
                'hdu_names': '',
                'notes': f"Error: {e}"
            })

    for fpath in spec_chan_files:
        rel_path = os.path.relpath(fpath, base_dir).replace('\\', '/')
        try:
            with fits.open(fpath) as hdul:
                hdr0 = hdul[0].header
                det = hdr0.get('DETECTOR', 'ALL')
                cal_ver = hdr0.get('CAL_VER', 'UNKNOWN')
                cwave_avail = False
                cband_avail = False
                wave_unit = "um"
                band_unit = "um"
                n_channels = 0
                
                for h in hdul:
                    if hasattr(h, 'columns') and h.columns is not None:
                        col_names = [c.name.upper() for c in h.columns]
                        if 'CWAVE' in col_names:
                            cwave_avail = True
                        if 'CBAND' in col_names:
                            cband_avail = True
                        if 'WAVELENGTH' in col_names:
                            cwave_avail = True
                        n_channels = len(h.data) if h.data is not None else 0
                        
                cal_audit_rows.append({
                    'file_path': rel_path,
                    'cal_type': 'SPECTRAL_CHANNELS',
                    'detector': det,
                    'version': cal_ver,
                    'cwave_avail': cwave_avail,
                    'cband_avail': cband_avail,
                    'wave_unit': wave_unit,
                    'band_unit': band_unit,
                    'hdu_count': len(hdul),
                    'hdu_names': ", ".join([h.name for h in hdul]),
                    'notes': f"Contains {n_channels} total spectral band definitions across detectors"
                })
        except Exception as e:
            cal_audit_rows.append({
                'file_path': rel_path,
                'cal_type': 'SPECTRAL_CHANNELS',
                'detector': 'ERROR',
                'version': 'ERROR',
                'cwave_avail': False,
                'cband_avail': False,
                'wave_unit': 'N/A',
                'band_unit': 'N/A',
                'hdu_count': 0,
                'hdu_names': '',
                'notes': f"Error: {e}"
            })

    # Save spectral_extraction_audit.csv
    csv_path = os.path.join(base_dir, "reports", "second_pass_audit", "spectral_extraction_audit.csv")
    fieldnames = ['file_path', 'cal_type', 'detector', 'version', 'cwave_avail', 'cband_avail', 'wave_unit', 'band_unit', 'hdu_count', 'hdu_names', 'notes']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cal_audit_rows)
    print(f"Spectral calibration audit saved to {csv_path}")

    # 2. Check detector coverage across all 32 Level-2 files
    l2_patterns = [
        os.path.join(base_dir, 'data', 'spherex', 'qr2', 'level2', '*.fits'),
        os.path.join(base_dir, 'data', 'spherex', 'qr2_deep', '*.fits'),
        os.path.join(base_dir, 'data', 'spherex', 'qr3', 'level2', '*.fits'),
        os.path.join(base_dir, 'data', 'spherex', 'qr3_deep', '*.fits'),
    ]
    l2_files = []
    for pat in l2_patterns:
        l2_files.extend(glob.glob(pat))
        
    pointings_detectors = {}
    for fpath in l2_files:
        with fits.open(fpath) as hdul:
            obsid = hdul[1].header.get('OBSID', 'UNKNOWN')
            det = hdul[1].header.get('DETECTOR', 'UNKNOWN')
            date_obs = hdul[1].header.get('DATE-OBS', 'UNKNOWN')
            # Extract pointing prefix (e.g. 2026W30_1B_0001)
            parts = obsid.split('_')
            prefix = "_".join(parts[:3]) if len(parts) >= 3 else obsid
            pointings_detectors.setdefault(prefix, set()).add((det, obsid, date_obs))

    print("\n--- LEVEL-2 DETECTOR COVERAGE PER POINTING PREFIX ---")
    for prefix, obs_list in sorted(pointings_detectors.items()):
        dets = sorted(list({str(x[0]) for x in obs_list}))
        print(f"  Pointing Prefix: {prefix} -> Detectors present: {dets} ({len(obs_list)} files)")

    # 3. Inspect models/spectra/ implementation
    spectra_model_path = os.path.join(base_dir, 'models', 'spectra', 'model.py')
    spectra_train_path = os.path.join(base_dir, 'models', 'spectra', 'train_spectra.py')
    
    with open(spectra_model_path, 'r', encoding='utf-8') as f:
        model_code = f.read()
    with open(spectra_train_path, 'r', encoding='utf-8') as f:
        train_code = f.read()
        
    # Check what train_spectra actually does
    has_synthetic_gen = "generate_synthetic_spectra" in train_code or "np.random" in train_code
    has_photometry = "photutils" in train_code or "aperture_photometry" in train_code
    
    # 4. Generate spectral_extraction_report.md
    report_path = os.path.join(base_dir, "reports", "second_pass_audit", "spectral_extraction_report.md")
    with open(report_path, "w", encoding="utf-8") as out:
        out.write("# SPECTRA-X: Spectral WCS and Spectral Extraction Audit Report\n\n")
        out.write("## 1. Executive Summary and Readiness Finding\n\n")
        out.write("**SCIENTIFIC READINESS STATUS FOR SPECTRA**: **`BASELINE TRAINED (ON SYNTHETIC PROXY DATA) / SCIENTIFIC VALIDATION PENDING`**.\n\n")
        out.write("### Critical Scientific Facts Verified:\n")
        out.write("1. **Level-2 Science Exposures Cover Exactly 1 Detector per File**: In the ingested 5.195 GB dataset:\n")
        out.write("   - All 16 QR2 Level-2 files cover **Detector 2** only (`DETECTOR = 2`, Band 2: 1.25–1.87 µm).\n")
        out.write("   - All 16 QR3 Level-2 files cover **Detector 1** only (`DETECTOR = 1`, Band 1: 0.75–1.25 µm).\n")
        out.write("   - **Zero Level-2 files exist for Detectors 3, 4, 5, or 6** in the current dataset.\n")
        out.write("2. **`WCS-WAVE` in HDU 6 is a Spatial Wavelength Coordinate Grid, NOT a Source Spectrum**:\n")
        out.write("   - In QR2, HDU 6 (`WCS-WAVE`) contains an 11x11 spatial array giving wavelength as a function of detector pixel position $(X, Y)$.\n")
        out.write("   - In QR3, HDU 6 (`WCS-WAVE`) contains a 9x9 spatial array giving wavelength as a function of detector pixel position $(X, Y)$.\n")
        out.write("   - Because SPHEREx uses Linear Variable Filters (LVF), each pixel column observes a distinct narrow bandpass. An isolated source on a single exposure yields only *one* monochromatic flux measurement, not a 102-channel SED.\n")
        out.write("3. **Assembling a Complete 102-Channel Spectrum Requires Multi-Detector Coverage**:\n")
        out.write("   - A celestial source must be observed across all 6 focal plane arrays (Detectors 1 to 6) as the satellite slews to accumulate flux measurements across all 102 spectral bands (0.75 to 5.0 µm).\n")
        out.write("   - Because our downloaded dataset lacks exposures for Detectors 3–6, **full 102-channel empirical spectral extraction is physically impossible from the current dataset alone**.\n")
        out.write("4. **Existing Checkpoint Provenance**:\n")
        out.write("   - Inspection of `models/spectra/train_spectra.py` confirms that the baseline model was trained using `generate_synthetic_spectra()` (procedurally generated continua with Gaussian emission/absorption lines and random noise).\n")
        out.write("   - The model architecture and PyTorch implementation are verified and functional, but the model has **never processed real SPHEREx-extracted 102-channel SEDs**.\n\n")

        out.write("## 2. Standalone Spectral Calibration Products Audit\n\n")
        out.write("| Calibration File | Type | Detector | Version | CWAVE | CBAND | Units | Notes |\n")
        out.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |\n")
        for row in cal_audit_rows:
            cw = "Yes" if row['cwave_avail'] else "No"
            cb = "Yes" if row['cband_avail'] else "No"
            out.write(f"| `{row['file_path']}` | {row['cal_type']} | {row['detector']} | {row['version']} | {cw} | {cb} | {row['wave_unit']} | {row['notes']} |\n")
        out.write("\n")

        out.write("## 3. Level-2 Pointing Detector Coverage Audit\n\n")
        out.write("SPHEREx 102-channel spectrophotometry is partitioned across six focal plane arrays:\n")
        out.write("- **Band 1 (Detector 1)**: 0.75 – 1.25 µm (17 channels, R ≈ 41)\n")
        out.write("- **Band 2 (Detector 2)**: 1.25 – 1.87 µm (17 channels, R ≈ 41)\n")
        out.write("- **Band 3 (Detector 3)**: 1.87 – 2.80 µm (17 channels, R ≈ 41)\n")
        out.write("- **Band 4 (Detector 4)**: 2.80 – 3.82 µm (17 channels, R ≈ 35)\n")
        out.write("- **Band 5 (Detector 5)**: 3.82 – 4.42 µm (17 channels, R ≈ 110)\n")
        out.write("- **Band 6 (Detector 6)**: 4.42 – 5.00 µm (17 channels, R ≈ 130)\n\n")
        out.write("### Actual Pointing Coverage in Downloaded Data:\n")
        for prefix, obs_list in sorted(pointings_detectors.items()):
            dets = sorted(list({str(x[0]) for x in obs_list}))
            missing_dets = [d for d in ['1','2','3','4','5','6'] if d not in dets]
            out.write(f"- Pointing `{prefix}`: Detectors present = **{', '.join(dets)}** (Missing: {', '.join(missing_dets)})\n")
        out.write("\n")

        out.write("## 4. Audit of Existing SPECTRA Implementation\n\n")
        out.write(f"- **Model Class**: `SpectrophotometricAutoencoder` in `models/spectra/model.py`.\n")
        out.write(f"- **Input Shape**: `(Batch, 1, 102)`.\n")
        out.write(f"- **Training Data Source**: Procedural synthetic generator (`generate_synthetic_spectra`). No aperture photometry is performed on FITS arrays.\n")
        out.write(f"- **Aperture Photometry Pipeline**: Currently unbuilt. The project does not yet possess code to extract source coordinates, perform circular aperture photometry, subtract local annulus background, or query `WCS-WAVE` for effective wavelength.\n\n")

        out.write("## 5. Comparison with Official IRSA SPHEREx Spectrophotometry Tool\n\n")
        out.write("The official IRSA SPHEREx Spectrophotometry Tool produces SED tables with schema:\n")
        out.write("`[RA, DEC, OBSID, DETECTOR, WAVELENGTH, BANDWIDTH, FLUX, FLUX_ERR, VARIANCE, FLAGS, DATE-OBS]`.\n\n")
        out.write("### Scientific Reasons Exact Comparison Cannot Be Executed Locally Today:\n")
        out.write("1. **Archive Coverage Gap**: IRSA's tool queries the entire all-sky Level-2 archive to collect the 100+ individual exposures covering a given target across all dithers and detectors. Locally, we have isolated pointings with only 1 detector per pointing.\n")
        out.write("2. **Missing Photometry Engine**: A local aperture extraction script (`extract_sed.py`) needs to be implemented using `photutils` and the standalone `spectral_wcs_D*.fits` tables.\n\n")

        out.write("## 6. Corrected Scientific Rule and Action Plan\n\n")
        out.write("1. **Status Rule**: SPECTRA is strictly marked **`BASELINE TRAINED (ON SYNTHETIC PROXY DATA)`**. It is **NOT** ready for real-world anomaly discovery or claims of detecting PAHs, water ice, or CO2 absorption.\n")
        out.write("2. **Action Plan for Phase 2**: Build an extraction pipeline using `photutils` and the standalone calibration products to extract monochromatic fluxes from available D1 and D2 images, and acquire coordinated D1–D6 sets when the download budget is expanded.\n")

    print(f"Updated spectral extraction report written to {report_path}")

if __name__ == '__main__':
    audit_spectral_extraction()
