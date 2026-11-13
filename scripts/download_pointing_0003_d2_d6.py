"""
SPECTRA-X / F1 — Phase 2, Task 1
Resumable, Atomic Downloader for Pointing 0003 Detectors D2-D6 Level-2 Science FITS

Downloads the 19 verified Level-2 science exposures from NASA IRSA SPHEREx S3 bucket:
https://nasa-irsa-spherex.s3.amazonaws.com/qr3/level2/2026W30_1B/l2b-v27-2026-222/
"""

import os
import sys
import time
import requests
import pandas as pd
from pathlib import Path
from astropy.io import fits

BASE_URL = "https://nasa-irsa-spherex.s3.amazonaws.com/qr3/level2/2026W30_1B/l2b-v27-2026-222/"
DEST_DIR = Path("data/spherex/qr3/level2")
MANIFEST_OUT = Path("data/manifests/f1_phase2_download_manifest.csv")

TARGET_FILES = [
    # D2: 4 dithers
    {"detector": "D2", "dither": 1, "dir": "2", "filename": "level2_2026W30_1B_0003_1D2_spx_l2b-v27-2026-222.fits"},
    {"detector": "D2", "dither": 2, "dir": "2", "filename": "level2_2026W30_1B_0003_2D2_spx_l2b-v27-2026-222.fits"},
    {"detector": "D2", "dither": 3, "dir": "2", "filename": "level2_2026W30_1B_0003_3D2_spx_l2b-v27-2026-222.fits"},
    {"detector": "D2", "dither": 4, "dir": "2", "filename": "level2_2026W30_1B_0003_4D2_spx_l2b-v27-2026-222.fits"},
    # D3: 3 dithers (1, 3, 4)
    {"detector": "D3", "dither": 1, "dir": "3", "filename": "level2_2026W30_1B_0003_1D3_spx_l2b-v27-2026-222.fits"},
    {"detector": "D3", "dither": 3, "dir": "3", "filename": "level2_2026W30_1B_0003_3D3_spx_l2b-v27-2026-222.fits"},
    {"detector": "D3", "dither": 4, "dir": "3", "filename": "level2_2026W30_1B_0003_4D3_spx_l2b-v27-2026-222.fits"},
    # D4: 4 dithers
    {"detector": "D4", "dither": 1, "dir": "4", "filename": "level2_2026W30_1B_0003_1D4_spx_l2b-v27-2026-222.fits"},
    {"detector": "D4", "dither": 2, "dir": "4", "filename": "level2_2026W30_1B_0003_2D4_spx_l2b-v27-2026-222.fits"},
    {"detector": "D4", "dither": 3, "dir": "4", "filename": "level2_2026W30_1B_0003_3D4_spx_l2b-v27-2026-222.fits"},
    {"detector": "D4", "dither": 4, "dir": "4", "filename": "level2_2026W30_1B_0003_4D4_spx_l2b-v27-2026-222.fits"},
    # D5: 4 dithers
    {"detector": "D5", "dither": 1, "dir": "5", "filename": "level2_2026W30_1B_0003_1D5_spx_l2b-v27-2026-222.fits"},
    {"detector": "D5", "dither": 2, "dir": "5", "filename": "level2_2026W30_1B_0003_2D5_spx_l2b-v27-2026-222.fits"},
    {"detector": "D5", "dither": 3, "dir": "5", "filename": "level2_2026W30_1B_0003_3D5_spx_l2b-v27-2026-222.fits"},
    {"detector": "D5", "dither": 4, "dir": "5", "filename": "level2_2026W30_1B_0003_4D5_spx_l2b-v27-2026-222.fits"},
    # D6: 4 dithers
    {"detector": "D6", "dither": 1, "dir": "6", "filename": "level2_2026W30_1B_0003_1D6_spx_l2b-v27-2026-222.fits"},
    {"detector": "D6", "dither": 2, "dir": "6", "filename": "level2_2026W30_1B_0003_2D6_spx_l2b-v27-2026-222.fits"},
    {"detector": "D6", "dither": 3, "dir": "6", "filename": "level2_2026W30_1B_0003_3D6_spx_l2b-v27-2026-222.fits"},
    {"detector": "D6", "dither": 4, "dir": "6", "filename": "level2_2026W30_1B_0003_4D6_spx_l2b-v27-2026-222.fits"},
]

def download_file(url: str, dest_path: Path, expected_size: int = None, max_retries: int = 3):
    """Downloads a file atomically using a .part temporary file with retries."""
    part_path = dest_path.with_suffix(".fits.part")
    
    # Check if already completed and valid
    if dest_path.exists():
        actual_size = dest_path.stat().st_size
        if expected_size is None or actual_size == expected_size:
            try:
                with fits.open(dest_path) as hdul:
                    _ = hdul[0].header
                return "ALREADY_EXISTS_VALID", actual_size, 0.0
            except Exception:
                print(f"Existing file {dest_path.name} is corrupt; re-downloading...")
                dest_path.unlink()
        else:
            print(f"Existing file size mismatch ({actual_size} != {expected_size}); re-downloading...")
            dest_path.unlink()

    for attempt in range(1, max_retries + 1):
        t0 = time.time()
        try:
            print(f"Downloading {dest_path.name} (Attempt {attempt}/{max_retries})...")
            with requests.get(url, stream=True, timeout=(10, 120)) as r:
                r.raise_for_status()
                total_len = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(part_path, "wb") as f_out:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                        if chunk:
                            f_out.write(chunk)
                            downloaded += len(chunk)
                
                # Verify size
                if total_len > 0 and downloaded != total_len:
                    raise IOError(f"Incomplete download: received {downloaded}/{total_len} bytes")
                
                # Atomic rename
                if part_path.exists():
                    part_path.replace(dest_path)
                
                elapsed = time.time() - t0
                speed_mb_s = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                print(f"Successfully downloaded {dest_path.name}: {downloaded:,} bytes in {elapsed:.1f}s ({speed_mb_s:.2f} MB/s)")
                return "DOWNLOADED_SUCCESS", downloaded, elapsed

        except Exception as e:
            print(f"Attempt {attempt} failed for {dest_path.name}: {e}")
            if part_path.exists():
                part_path.unlink()
            if attempt < max_retries:
                time.sleep(2 * attempt)
            else:
                return f"FAILED: {str(e)}", 0, time.time() - t0

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("SPECTRA-X / F1 — Phase 2 Task 1: Level-2 Science FITS Download")
    print(f"Target Destination: {DEST_DIR.resolve()}")
    print(f"Total Targets: {len(TARGET_FILES)} files across D2-D6")
    print("=" * 70)

    records = []
    total_downloaded_bytes = 0
    t_start = time.time()

    for i, item in enumerate(TARGET_FILES, 1):
        fname = item["filename"]
        det = item["detector"]
        dither = item["dither"]
        d_dir = item["dir"]
        url = f"{BASE_URL}{d_dir}/{fname}"
        dest_path = DEST_DIR / fname

        print(f"\n[{i}/{len(TARGET_FILES)}] Processing {det} Dither {dither}: {fname}")
        
        # HEAD request first for metadata verification
        head_status = "UNKNOWN"
        remote_size = 0
        try:
            r_head = requests.head(url, timeout=10)
            head_status = str(r_head.status_code)
            remote_size = int(r_head.headers.get("Content-Length", 0))
            etag = r_head.headers.get("ETag", "").strip('"')
            last_mod = r_head.headers.get("Last-Modified", "")
        except Exception as e:
            etag = ""
            last_mod = ""
            print(f"Warning: HEAD request failed: {e}")

        status, size_bytes, elapsed = download_file(url, dest_path, expected_size=remote_size)
        total_downloaded_bytes += size_bytes

        records.append({
            "detector": det,
            "dither": dither,
            "pointing": "0003",
            "filename": fname,
            "local_path": str(dest_path),
            "remote_url": url,
            "remote_size_bytes": remote_size,
            "local_size_bytes": size_bytes,
            "download_status": status,
            "elapsed_seconds": round(elapsed, 2),
            "etag": etag,
            "last_modified": last_mod
        })

    # Save manifest
    df = pd.DataFrame(records)
    df.to_csv(MANIFEST_OUT, index=False)
    print("\n" + "=" * 70)
    print(f"Download complete! Saved manifest to {MANIFEST_OUT}")
    print(f"Total files: {len(records)}")
    print(f"Successful / Existing: {(df['download_status'].str.contains('SUCCESS') | df['download_status'].str.contains('ALREADY')).sum()}")
    print(f"Failed: {df['download_status'].str.contains('FAILED').sum()}")
    print(f"Total Volume: {total_downloaded_bytes:,} bytes ({total_downloaded_bytes / (1024**3):.3f} GB)")
    print(f"Total Duration: {time.time() - t_start:.1f}s")
    print("=" * 70)

if __name__ == "__main__":
    main()
