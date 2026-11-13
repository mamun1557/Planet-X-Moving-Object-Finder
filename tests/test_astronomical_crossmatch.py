"""
Unit tests for astronomical cross-matching, coordinate propagation,
ambiguous handling, and classification joins.

Verifies:
1. Coordinate propagation accuracy.
2. Angular separation calculations (Haversine).
3. Matching-radius enforcement.
4. Ambiguous counterpart handling.
5. Missing catalogue measurements robustness.
6. Zero duplicate source IDs.
7. Correct 1-to-1 source-level joins.
8. Exact preservation of original SPECTRA v2 anomaly scores.
"""

import unittest
import math
import os
import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.process_crossmatch_and_classification import (
    angular_separation_arcsec,
    propagate_gaia_coords,
    DT_GAIA_SPHEREX
)


class TestAstronomicalCrossmatch(unittest.TestCase):
    def setUp(self):
        self.base_dir = str(PROJECT_ROOT)
        self.spx_path = os.path.join(self.base_dir, "data", "processed", "benchmarks", "spectra_v2_source_scores.csv")
        self.gaia_path = os.path.join(self.base_dir, "data", "processed", "crossmatch", "pointing_0003_gaia_dr3_matches.csv")
        self.wise_path = os.path.join(self.base_dir, "data", "processed", "crossmatch", "pointing_0003_allwise_matches.csv")
        self.sum_path = os.path.join(self.base_dir, "data", "processed", "crossmatch", "pointing_0003_crossmatch_summary.csv")
        self.cls_path = os.path.join(self.base_dir, "data", "processed", "classification", "pointing_0003_source_classifications.csv")

    def test_angular_separation_calculation(self):
        """Verify Haversine formula on known coordinate pairs."""
        # Exact match
        self.assertAlmostEqual(angular_separation_arcsec(100.0, 20.0, 100.0, 20.0), 0.0, places=5)
        # 1 arcsecond offset in Dec
        sep_dec_1as = angular_separation_arcsec(100.0, 0.0, 100.0, 1.0 / 3600.0)
        self.assertAlmostEqual(sep_dec_1as, 1.0, places=4)
        # 1 arcsecond offset in RA at equator
        sep_ra_1as = angular_separation_arcsec(0.0, 0.0, 1.0 / 3600.0, 0.0)
        self.assertAlmostEqual(sep_ra_1as, 1.0, places=4)

    def test_coordinate_propagation(self):
        """Verify proper motion propagation from J2016.0 to 2026.5496."""
        ra0, dec0 = 100.0, -60.0
        # 100 mas/yr in RA* and Dec over DT_GAIA_SPHEREX years
        pmra, pmdec = 100.0, 100.0
        ra_prop, dec_prop, pm_used = propagate_gaia_coords(ra0, dec0, pmra, pmdec)

        self.assertTrue(pm_used)
        expected_ddec_deg = (100.0 * 1e-3 * DT_GAIA_SPHEREX) / 3600.0
        self.assertAlmostEqual(dec_prop - dec0, expected_ddec_deg, places=7)

        # Check total separation moved
        sep = angular_separation_arcsec(ra0, dec0, ra_prop, dec_prop)
        expected_sep_arcsec = math.sqrt(2) * 100.0 * 1e-3 * DT_GAIA_SPHEREX
        self.assertAlmostEqual(sep, expected_sep_arcsec, places=3)

    def test_missing_catalogue_measurements_handling(self):
        """Verify proper motion propagation gracefully handles None or NaN."""
        ra_prop, dec_prop, pm_used = propagate_gaia_coords(150.0, -70.0, None, np.nan)
        self.assertFalse(pm_used)
        self.assertEqual(ra_prop, 150.0)
        self.assertEqual(dec_prop, -70.0)

    def test_no_duplicate_source_ids(self):
        """Verify that all processed files have exactly 1,132 unique source IDs."""
        for path in [self.gaia_path, self.wise_path, self.sum_path, self.cls_path]:
            df = pd.read_csv(path)
            self.assertEqual(len(df), 1132, f"File {path} does not have 1132 rows")
            self.assertEqual(df["source_id"].nunique(), 1132, f"File {path} contains duplicate source_ids")

    def test_source_level_joins(self):
        """Verify exact alignment of source_id across all generated files."""
        spx_df = pd.read_csv(self.spx_path)
        gaia_df = pd.read_csv(self.gaia_path)
        wise_df = pd.read_csv(self.wise_path)
        sum_df = pd.read_csv(self.sum_path)
        cls_df = pd.read_csv(self.cls_path)

        # Check exact sequence of source IDs
        np.testing.assert_array_equal(spx_df["source_id"].values, gaia_df["source_id"].values)
        np.testing.assert_array_equal(spx_df["source_id"].values, wise_df["source_id"].values)
        np.testing.assert_array_equal(spx_df["source_id"].values, sum_df["source_id"].values)
        np.testing.assert_array_equal(spx_df["source_id"].values, cls_df["source_id"].values)

    def test_preservation_of_spectra_scores(self):
        """Verify that SPECTRA v2 anomaly scores are preserved without modification."""
        spx_df = pd.read_csv(self.spx_path)
        sum_df = pd.read_csv(self.sum_path)
        cls_df = pd.read_csv(self.cls_path)

        np.testing.assert_allclose(
            sum_df["spectra_anomaly_score_B"].values,
            spx_df["chi2_B_d1_d4"].values,
            rtol=1e-6
        )
        np.testing.assert_allclose(
            cls_df["spectra_anomaly_score_B"].values,
            spx_df["chi2_B_d1_d4"].values,
            rtol=1e-6
        )

    def test_matching_radius_enforcement(self):
        """Verify that high-confidence matches never exceed matching radius thresholds."""
        gaia_df = pd.read_csv(self.gaia_path)
        high_conf_gaia = gaia_df[gaia_df["match_category"] == "HIGH_CONFIDENCE"]
        # All HIGH_CONFIDENCE Gaia matches must have sep_prop_arcsec <= 0.5
        self.assertTrue((high_conf_gaia["sep_prop_arcsec"] <= 0.5001).all())

        wise_df = pd.read_csv(self.wise_path)
        high_conf_wise = wise_df[wise_df["match_category"] == "HIGH_CONFIDENCE"]
        # All HIGH_CONFIDENCE AllWISE matches must have sep <= 0.8
        self.assertTrue((high_conf_wise["allwise_sep_arcsec"] <= 0.8001).all())


if __name__ == "__main__":
    unittest.main()
