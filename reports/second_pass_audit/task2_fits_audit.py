import os
import glob
import csv
import astropy.io.fits as fits
import numpy as np

def audit_fits_structures():
    print("Executing Task 2: FITS HDU Structure Verification (all 32 Level-2 files)...")
    base_dir = os.path.abspath(".")
    
    # Locate all 32 Level-2 FITS files
    l2_patterns = [
        os.path.join(base_dir, 'data', 'spherex', 'qr2', 'level2', '*.fits'),
        os.path.join(base_dir, 'data', 'spherex', 'qr2_deep', '*.fits'),
        os.path.join(base_dir, 'data', 'spherex', 'qr3', 'level2', '*.fits'),
        os.path.join(base_dir, 'data', 'spherex', 'qr3_deep', '*.fits'),
    ]
    
    l2_files = []
    for pat in l2_patterns:
        l2_files.extend(glob.glob(pat))
        
    print(f"Found {len(l2_files)} Level-2 FITS files to inspect.")
    assert len(l2_files) == 32, f"Expected 32 Level-2 files, found {len(l2_files)}"
    
    csv_rows = []
    hdu_structures = {}
    
    for fpath in sorted(l2_files):
        rel_path = os.path.relpath(fpath, base_dir).replace('\\', '/')
        release = 'QR2' if 'qr2' in rel_path.lower() else 'QR3'
        
        try:
            with fits.open(fpath, memmap=False) as hdul:
                # Find OBSID and DETECTOR across HDU 0 and HDU 1
                obs_id = hdul[0].header.get('OBS_ID', hdul[0].header.get('OBSID', ''))
                if not obs_id and len(hdul) > 1:
                    obs_id = hdul[1].header.get('OBSID', hdul[1].header.get('OBS_ID', 'UNKNOWN'))
                    
                detector_val = hdul[0].header.get('DETECTOR', '')
                if not detector_val and len(hdul) > 1:
                    detector_val = hdul[1].header.get('DETECTOR', 'UNKNOWN')
                
                # Record structure signature
                struct_sig = []
                for idx, hdu in enumerate(hdul):
                    extname = hdu.name if hasattr(hdu, 'name') else f"HDU_{idx}"
                    hdu_class = type(hdu).__name__
                    
                    dims = "None"
                    dtype_str = "None"
                    data_read_ok = True
                    err_msg = ""
                    
                    try:
                        if hdu.data is not None:
                            dims = str(hdu.data.shape)
                            dtype_str = str(hdu.data.dtype)
                            # Actually read/access data array to verify integrity
                            _ = np.nanmean(hdu.data) if hasattr(hdu.data, 'dtype') and np.issubdtype(hdu.data.dtype, np.number) else len(hdu.data)
                        else:
                            dims = "None (Header-only)"
                    except Exception as e:
                        data_read_ok = False
                        err_msg = f"Data read error: {str(e)}"
                        
                    header_summary = []
                    for k in ['NAXIS', 'BITPIX', 'BUNIT', 'CTYPE1', 'CTYPE2', 'DATE-OBS', 'DETECTOR', 'CHANNEL', 'OBSID']:
                        if k in hdu.header:
                            header_summary.append(f"{k}={hdu.header[k]}")
                    header_verif = "; ".join(header_summary) if header_summary else "OK"
                    
                    struct_sig.append((idx, extname, hdu_class, dims, dtype_str))
                    
                    csv_rows.append({
                        'file_path': rel_path,
                        'release': release,
                        'obs_id': obs_id,
                        'hdu_index': idx,
                        'extname': extname,
                        'hdu_class': hdu_class,
                        'dimensions': dims,
                        'data_type': dtype_str,
                        'header_verification': header_verif,
                        'data_read_ok': data_read_ok,
                        'error_message': err_msg
                    })
                    
                struct_key = tuple(struct_sig)
                hdu_structures.setdefault(struct_key, []).append(rel_path)
                
        except Exception as e:
            csv_rows.append({
                'file_path': rel_path,
                'release': release,
                'obs_id': 'ERROR',
                'hdu_index': -1,
                'extname': 'CORRUPT',
                'hdu_class': 'ERROR',
                'dimensions': 'N/A',
                'data_type': 'N/A',
                'header_verification': 'FAIL',
                'data_read_ok': False,
                'error_message': str(e)
            })

    # Save to CSV
    csv_path = os.path.join(base_dir, "reports", "second_pass_audit", "corrected_fits_audit.csv")
    fieldnames = ['file_path', 'release', 'obs_id', 'hdu_index', 'extname', 'hdu_class', 'dimensions', 'data_type', 'header_verification', 'data_read_ok', 'error_message']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"FITS HDU audit written to {csv_path} ({len(csv_rows)} rows across 32 files).")

    # Also inspect QR3 ePSF calibration files independently
    epsf_pat = os.path.join(base_dir, 'data', 'spherex', 'qr3', 'templates', '*epsf*.fits')
    epsf_cal_pat = os.path.join(base_dir, 'data', 'spherex', 'qr3', 'calibration', '*epsf*.fits')
    epsf_files = glob.glob(epsf_pat) + glob.glob(epsf_cal_pat)
    print(f"Found {len(epsf_files)} separate ePSF calibration files.")
    
    epsf_details = []
    for ep in epsf_files:
        rel_ep = os.path.relpath(ep, base_dir).replace('\\', '/')
        try:
            with fits.open(ep) as hdul:
                info_list = []
                for i, hdu in enumerate(hdul):
                    sh = getattr(hdu.data, 'shape', 'None') if hasattr(hdu, 'data') and hdu.data is not None else 'None'
                    info_list.append(f"HDU {i} ({hdu.name}, {type(hdu).__name__}, {sh})")
                epsf_details.append((rel_ep, "; ".join(info_list)))
        except Exception as e:
            epsf_details.append((rel_ep, f"Error: {e}"))
            
    print("\n--- LEVEL-2 FITS HDU SIGNATURES FOUND ---")
    for sig, flist in hdu_structures.items():
        print(f"\nSignature matched by {len(flist)} files (e.g. {flist[0]}):")
        for h in sig:
            print(f"  HDU {h[0]}: EXTNAME='{h[1]}', Class={h[2]}, Dims={h[3]}, Dtype={h[4]}")
            
    print("\n--- SEPARATE ePSF CALIBRATION PRODUCTS ---")
    for ep, desc in epsf_details:
        print(f"  {ep}: {desc}")

if __name__ == '__main__':
    audit_fits_structures()
