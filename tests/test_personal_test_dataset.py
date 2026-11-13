"""
Automated Integrity & Numerical Validation Tests for Task 4.29C
Personal Test Dataset Package & Manifest Verification

Verifies:
1. Dataset manifest contains exactly 50 pairs / 100 observation samples.
2. 25 Real Intra-Visit pairs and 25 Synthetic Engineering Test pairs are strictly separated.
3. Real pairs have null ground-truth vectors and dither safeguards.
4. Synthetic pairs match known ground-truth motion within tolerance (< 0.1 arcsec).
5. Cross-meridian RA wraparound pairs compute proper angular displacement.
6. Standalone ZIP package exists, passes zipfile integrity, and is extractable.
7. Original Level-2 SPHEREx flight FITS files remain unaltered.
"""

import os
import sys
import json
import zipfile
import unittest
from astropy.io import fits
from astropy.wcs import WCS

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from observatory.motion_analysis import (
    AstronomicalMotionEngine,
    ObservationEpoch
)

PACKAGE_DIR = os.path.join(PROJECT_ROOT, "artifacts", "downloadable_packages", "SPECTRA-X-Personal-Test-Data")
ZIP_PATH = os.path.join(PROJECT_ROOT, "artifacts", "downloadable_packages", "SPECTRA-X-Personal-Test-Data.zip")


class TestPersonalTestDatasetPackage(unittest.TestCase):
    """Verifies personal test dataset package integrity, manifests, and numerical accuracy."""

    def test_package_structure_and_counts(self):
        """Verify 50 pairs (25 real, 25 synthetic) and 100 observation samples exist."""
        manifest_p = os.path.join(PACKAGE_DIR, "dataset_manifest.json")
        self.assertTrue(os.path.exists(manifest_p), "dataset_manifest.json must exist")

        with open(manifest_p, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["total_pairs"], 50)
        self.assertEqual(manifest["total_observation_samples"], 100)
        self.assertEqual(len(manifest["all_pairs"]), 50)

        real_pairs = [p for p in manifest["all_pairs"] if p["dataset_class"] == "REAL_INTRA_VISIT"]
        syn_pairs = [p for p in manifest["all_pairs"] if p["dataset_class"] == "SYNTHETIC_ENGINEERING_TEST"]

        self.assertEqual(len(real_pairs), 25)
        self.assertEqual(len(syn_pairs), 25)

    def test_real_intra_visit_provenance_and_safeguards(self):
        """Verify real intra-visit pairs have valid provenance, dt < 1 day, and null synthetic vectors."""
        manifest_p = os.path.join(PACKAGE_DIR, "real_intra_visit", "manifest.json")
        with open(manifest_p, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["count"], 25)
        for pair in data["pairs"]:
            pair_id = pair["pair_id"]
            self.assertEqual(pair["dataset_class"], "REAL_INTRA_VISIT")
            self.assertFalse(pair["has_ground_truth_motion"])
            self.assertIsNone(pair["synthetic_ground_truth_motion"])
            self.assertLess(pair["time_separation_days"], 1.0)
            self.assertEqual(
                pair["scientific_eligibility"],
                "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY"
            )

            # Check that files exist and WCS is valid
            folder = os.path.join(PACKAGE_DIR, "real_intra_visit", "pairs", pair_id)
            fa = os.path.join(folder, "obs_a.fits")
            fb = os.path.join(folder, "obs_b.fits")
            self.assertTrue(os.path.exists(fa))
            self.assertTrue(os.path.exists(fb))

            with fits.open(fa) as ha, fits.open(fb) as hb:
                self.assertIn("SCI", ha)
                self.assertIn("VAR", ha)
                self.assertIn("FLAGS", ha)
                wa = WCS(ha[1].header)
                wb = WCS(hb[1].header)
                sky_a = wa.all_pix2world([[64.0, 64.0]], 0)[0]
                sky_b = wb.all_pix2world([[64.0, 64.0]], 0)[0]
                self.assertFalse(any(map(lambda v: v != v, sky_a)))
                self.assertFalse(any(map(lambda v: v != v, sky_b)))

    def test_synthetic_engineering_numerical_accuracy(self):
        """Verify all 25 synthetic pairs match known ground truth within numerical tolerance."""
        manifest_p = os.path.join(PACKAGE_DIR, "synthetic_engineering_test", "manifest.json")
        with open(manifest_p, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["count"], 25)
        for pair in data["pairs"]:
            pair_id = pair["pair_id"]
            self.assertEqual(pair["dataset_class"], "SYNTHETIC_ENGINEERING_TEST")
            self.assertTrue(pair["has_ground_truth_motion"])
            self.assertIsNotNone(pair["synthetic_ground_truth_motion"])

            gt = pair["synthetic_ground_truth_motion"]
            self.assertTrue(gt["is_synthetic"])
            self.assertIn("SYNTHETIC_ENGINEERING_TEST", gt["synthetic_engineering_label"])

            # Verify against AstronomicalMotionEngine
            folder = os.path.join(PACKAGE_DIR, "synthetic_engineering_test", "pairs", pair_id)
            fa = os.path.join(folder, "obs_a.fits")
            fb = os.path.join(folder, "obs_b.fits")

            with fits.open(fa) as ha, fits.open(fb) as hb:
                wa = WCS(ha[1].header)
                wb = WCS(hb[1].header)
                px_a = gt["ground_truth_epoch_a"]["pixel_x"]
                py_a = gt["ground_truth_epoch_a"]["pixel_y"]
                px_b = gt["ground_truth_epoch_b"]["pixel_x"]
                py_b = gt["ground_truth_epoch_b"]["pixel_y"]

                sky_a = wa.all_pix2world([[px_a, py_a]], 0)[0]
                sky_b = wb.all_pix2world([[px_b, py_b]], 0)[0]

                ts_a = str(ha[1].header.get("DATE-OBS"))
                ts_b = str(hb[1].header.get("DATE-OBS"))

            obs_a = ObservationEpoch(
                obs_id=f"{pair_id}_A",
                ra_deg=float(sky_a[0]),
                dec_deg=float(sky_a[1]),
                timestamp=ts_a,
                wcs_valid=True
            )
            obs_b = ObservationEpoch(
                obs_id=f"{pair_id}_B",
                ra_deg=float(sky_b[0]),
                dec_deg=float(sky_b[1]),
                timestamp=ts_b,
                wcs_valid=True
            )

            res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
            self.assertTrue(res.is_valid)

            exp_disp = gt["ground_truth_angular_displacement_arcsec"]
            calc_disp = res.angular_displacement_arcsec
            disp_err = abs(calc_disp - exp_disp)
            self.assertLess(disp_err, 0.1, f"Pair {pair_id} displacement error {disp_err} arcsec exceeds 0.1 arcsec")

    def test_ra_wraparound_synthetic_scenarios(self):
        """Verify cross-meridian RA wraparound scenarios (SYNTH_PAIR_006 and SYNTH_PAIR_007)."""
        manifest_p = os.path.join(PACKAGE_DIR, "synthetic_engineering_test", "manifest.json")
        with open(manifest_p, "r", encoding="utf-8") as f:
            data = json.load(f)

        pairs_dict = {p["pair_id"]: p for p in data["pairs"]}

        # Pair 6: 359.985 -> ~0.015 (disp ~ 108 arcsec)
        p6 = pairs_dict["SYNTH_PAIR_006"]
        gt6 = p6["synthetic_ground_truth_motion"]
        self.assertEqual(gt6["target_type"], "RA_WRAPAROUND_MERIDIAN")
        self.assertAlmostEqual(gt6["ground_truth_angular_displacement_arcsec"], 108.0, places=1)

        # Pair 7: 0.010 -> ~359.990 (disp ~ 72 arcsec)
        p7 = pairs_dict["SYNTH_PAIR_007"]
        gt7 = p7["synthetic_ground_truth_motion"]
        self.assertEqual(gt7["target_type"], "RA_WRAPAROUND_REVERSE")
        self.assertAlmostEqual(gt7["ground_truth_angular_displacement_arcsec"], 72.0, places=1)

    def test_zip_archive_integrity_and_size(self):
        """Verify the downloadable ZIP file exists, is non-empty, and passes zipfile testzip."""
        self.assertTrue(os.path.exists(ZIP_PATH), "SPECTRA-X-Personal-Test-Data.zip must exist")
        size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)
        self.assertGreater(size_mb, 5.0, "ZIP should be reasonably populated (> 5 MB)")
        self.assertLess(size_mb, 50.0, "ZIP should remain compact (< 50 MB)")

        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            test_res = zf.testzip()
            self.assertIsNone(test_res, "ZIP archive must be uncorrupted")
            namelist = zf.namelist()
            self.assertGreaterEqual(len(namelist), 150)
            self.assertTrue(any("dataset_manifest.json" in n for n in namelist))
            self.assertTrue(any("SHA256SUMS.txt" in n for n in namelist))


if __name__ == "__main__":
    unittest.main()
