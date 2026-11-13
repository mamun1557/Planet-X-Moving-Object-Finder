"""
Unit Tests for Multi-Pointing SPHEREx Data Acquisition & Scientific FITS Validation
Covers all 10 mandatory test scenarios specified in Task 1.1K Section 9.
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from scripts.acquisition.multipointing_pilot import (
    StorageSafetyGate,
    ScientificFITSValidator,
    AtomicFileHandler
)


@pytest.fixture
def temp_workdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def create_minimal_valid_fits(filepath: str, pointing: str = "0001", detector: int = 1):
    """Helper to create a fully valid SPHEREx Level-2 FITS file for testing."""
    # HDU 0: Primary
    pri_hdr = fits.Header()
    pri_hdr["OBSID"] = f"2026W30_1B_{pointing}_1"
    pri_hdr["EXPTIME"] = 115.118
    pri_hdu = fits.PrimaryHDU(header=pri_hdr)

    # HDU 1: IMAGE
    w = WCS(naxis=2)
    w.wcs.crpix = [1020, 1020]
    w.wcs.cdelt = [-0.00171, 0.00171]
    w.wcs.crval = [232.66, -10.72]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    img_hdr = w.to_header()
    img_hdr["DETECTOR"] = detector
    img_hdr["OBSID"] = f"2026W30_1B_{pointing}_1"
    img_hdr["TSAMP"] = 115.118
    img_data = np.ones((2040, 2040), dtype=np.float32) * 100.0
    img_hdu = fits.ImageHDU(data=img_data, header=img_hdr, name="IMAGE")

    # HDU 2: FLAGS
    flg_data = np.zeros((2040, 2040), dtype=np.int16)
    flg_hdu = fits.ImageHDU(data=flg_data, name="FLAGS")

    # HDU 3: VARIANCE
    var_data = np.ones((2040, 2040), dtype=np.float32) * 2.5
    var_hdu = fits.ImageHDU(data=var_data, name="VARIANCE")

    # HDU 4: ZODI
    zodi_data = np.ones((2040, 2040), dtype=np.float32) * 50.0
    zodi_hdu = fits.ImageHDU(data=zodi_data, name="ZODI")

    # HDU 5: EPSF
    epsf_data = np.ones((441, 15, 15), dtype=np.float32)
    epsf_hdu = fits.ImageHDU(data=epsf_data, name="EPSF")

    # HDU 6: WCS-WAVE
    wave_data = np.linspace(0.75, 1.0, 2040).astype(np.float32)
    wave_hdu = fits.ImageHDU(data=wave_data, name="WCS-WAVE")

    hdul = fits.HDUList([pri_hdu, img_hdu, flg_hdu, var_hdu, zodi_hdu, epsf_hdu, wave_hdu])
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    hdul.writeto(filepath, overwrite=True)
    return filepath


# 1. Test Checksum Mismatch Detection
def test_checksum_mismatch_detection(temp_workdir):
    staging = os.path.join(temp_workdir, "staging", "file.fits")
    dest = os.path.join(temp_workdir, "dest", "file.fits")
    os.makedirs(os.path.dirname(staging), exist_ok=True)
    with open(staging, "wb") as f:
        f.write(b"SAMPLE_FITS_DATA_12345")

    expected_sha = "0000000000000000000000000000000000000000000000000000000000000000"
    success, actual_sha, msg = AtomicFileHandler.promote_from_staging(staging, dest, expected_sha)
    assert not success
    assert "Checksum mismatch" in msg
    assert not os.path.exists(staging)  # Temporary corrupt file cleaned up


# 2. Test Incomplete Download Recovery (.part file handling)
def test_incomplete_download_recovery(temp_workdir):
    part_file = os.path.join(temp_workdir, "staging", "exposure.fits.part")
    os.makedirs(os.path.dirname(part_file), exist_ok=True)
    with open(part_file, "wb") as f:
        f.write(b"INCOMPLETE_PARTIAL_DATA")

    # Promotion should fail on non-existent final staging path and preserve/clean properly
    success, _, msg = AtomicFileHandler.promote_from_staging(part_file.replace(".part", ""), os.path.join(temp_workdir, "dest.fits"))
    assert not success
    assert "not found" in msg


# 3. Test Duplicate File Handling
def test_duplicate_file_handling(temp_workdir):
    staging = os.path.join(temp_workdir, "staging", "dup.fits")
    dest = os.path.join(temp_workdir, "dest", "dup.fits")
    os.makedirs(os.path.dirname(staging), exist_ok=True)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    content = b"IDENTICAL_FITS_CONTENT"
    with open(staging, "wb") as f:
        f.write(content)
    with open(dest, "wb") as f:
        f.write(content)

    success, actual_sha, msg = AtomicFileHandler.promote_from_staging(staging, dest)
    assert success
    assert "already exists and is identical" in msg
    assert not os.path.exists(staging)


# 4. Test FITS Corruption Detection
def test_fits_corruption_detection(temp_workdir):
    corrupt_file = os.path.join(temp_workdir, "corrupt.fits")
    with open(corrupt_file, "wb") as f:
        f.write(b"CORRUPTED_NON_FITS_HEADER_TRUNCATED")

    report = ScientificFITSValidator.validate_file(corrupt_file)
    assert not report["is_valid"]
    assert any("corruption" in err.lower() or "read failure" in err.lower() for err in report["errors"])


# 5. Test Missing HDU Detection
def test_missing_hdu_detection(temp_workdir):
    fits_path = os.path.join(temp_workdir, "missing_hdu.fits")
    # Create FITS with only PRIMARY and IMAGE, missing VARIANCE, FLAGS, etc.
    pri_hdu = fits.PrimaryHDU()
    img_hdu = fits.ImageHDU(data=np.ones((2040, 2040), dtype=np.float32), name="IMAGE")
    hdul = fits.HDUList([pri_hdu, img_hdu])
    hdul.writeto(fits_path)

    report = ScientificFITSValidator.validate_file(fits_path)
    assert not report["is_valid"]
    assert "VARIANCE" in report["missing_hdus"]
    assert "FLAGS" in report["missing_hdus"]


# 6. Test Incorrect Detector Metadata
def test_incorrect_detector_metadata(temp_workdir):
    fits_path = os.path.join(temp_workdir, "wrong_det.fits")
    create_minimal_valid_fits(fits_path, pointing="0001", detector=1)

    # Validate expecting detector 2
    report = ScientificFITSValidator.validate_file(fits_path, expected_pointing="0001", expected_detector=2)
    assert not report["is_valid"]
    assert any("Detector mismatch" in err for err in report["errors"])


# 7. Test Invalid WCS
def test_invalid_wcs(temp_workdir):
    fits_path = os.path.join(temp_workdir, "invalid_wcs.fits")
    create_minimal_valid_fits(fits_path)

    # Corrupt WCS keywords in IMAGE HDU
    with fits.open(fits_path, mode="update") as hdul:
        del hdul["IMAGE"].header["CTYPE1"]
        del hdul["IMAGE"].header["CTYPE2"]
        hdul.flush()

    report = ScientificFITSValidator.validate_file(fits_path)
    assert not report["is_valid"]
    assert not report["wcs_valid"]


# 8. Test Missing or Non-Finite / Negative Variance
def test_missing_or_invalid_variance(temp_workdir):
    fits_path = os.path.join(temp_workdir, "invalid_var.fits")
    create_minimal_valid_fits(fits_path)

    # Insert negative variance
    with fits.open(fits_path, mode="update") as hdul:
        hdul["VARIANCE"].data[10, 10] = -5.0
        hdul.flush()

    report = ScientificFITSValidator.validate_file(fits_path)
    assert not report["is_valid"]
    assert not report["variance_valid"]
    assert any("negative values" in err for err in report["errors"])


# 9. Test Incorrect Pointing Identity
def test_incorrect_pointing_identity(temp_workdir):
    fits_path = os.path.join(temp_workdir, "wrong_pointing.fits")
    create_minimal_valid_fits(fits_path, pointing="0001", detector=1)

    # Validate expecting Pointing 0002
    report = ScientificFITSValidator.validate_file(fits_path, expected_pointing="0002", expected_detector=1)
    assert not report["is_valid"]
    assert any("Pointing mismatch" in err for err in report["errors"])


# 10. Test Safe Abort on Insufficient Disk Space
def test_safe_abort_on_insufficient_disk_space():
    gate = StorageSafetyGate(target_path=".", min_margin_gb=10.0)
    # Require unrealistic 10,000 GB
    allowed, free_gb, msg = gate.check_space(required_gb=10000.0)
    assert not allowed
    assert "ABORT: Insufficient disk space" in msg

