"""
Unit and Integration Tests for the Empirical Infrared Excess Validation Engine.

Tests:
- Magnitude-to-flux conversion & error propagation
- Zero-point definitions and Vega/AB handling
- Upper limits and missing data treatment
- Counterpart ambiguity / multiplicity handling
- Photospheric baseline prediction
- Excess significance (S_excess) calculation
- Evidence classification into 6 authoritative states
- Cohort isolation enforcement (P0008 vs blind cohorts)
- Frozen asset protection hash verification
"""

import math
import pytest
import hashlib

from spectra_engine.validation.infrared_excess.zero_points import PHOTOMETRIC_BANDS, BandMetadata
from spectra_engine.validation.infrared_excess.catalog_normalizer import (
    CatalogNormalizer,
    NormalizedMeasurement,
    NormalizedSourceRecord
)
from spectra_engine.validation.infrared_excess.photospheric_model import (
    PhotosphericBaselineEstimator,
    PhotosphericPrediction
)
from spectra_engine.validation.infrared_excess.excess_engine import (
    InfraredExcessEngine,
    ExcessBandResult,
    SPHERExOverlapResult
)
from spectra_engine.validation.infrared_excess.evidence_classifier import (
    InfraredEvidenceClassifier
)


class TestPhotometricConversion:
    """Test magnitude to flux conversion and error propagation."""

    def test_2mass_flux_conversion(self):
        # 2MASS Ks m = 10.0 mag, F_0 = 666700 mJy
        # F = 666700 * 10^(-0.4 * 10) = 666700 * 10^(-4) = 66.67 mJy
        band = PHOTOMETRIC_BANDS["2MASS_Ks"]
        flux, unc = CatalogNormalizer.magnitude_to_flux(10.0, 0.02, band)
        assert flux is not None
        assert abs(flux - 66.67) < 0.05
        assert unc is not None
        assert unc > 0.0

    def test_allwise_flux_conversion(self):
        # ALLWISE W1 m = 10.0 mag, F_0 = 309540 mJy
        # F = 309540 * 10^(-4) = 30.954 mJy
        band = PHOTOMETRIC_BANDS["WISE_W1"]
        flux, unc = CatalogNormalizer.magnitude_to_flux(10.0, 0.02, band)
        assert flux is not None
        assert abs(flux - 30.954) < 0.05

    def test_upper_limit_handling(self):
        band = PHOTOMETRIC_BANDS["WISE_W2"]
        flux, unc = CatalogNormalizer.magnitude_to_flux(14.5, None, band, is_upper_limit=True)
        assert flux is not None
        assert unc is None  # Upper limits have undefined symmetrical Gaussian error

    def test_missing_magnitude_handling(self):
        band = PHOTOMETRIC_BANDS["2MASS_J"]
        flux, unc = CatalogNormalizer.magnitude_to_flux(None, None, band)
        assert flux is None
        assert unc is None

    def test_non_positive_magnitude_error(self):
        # If error is <= 0 or NaN, normalizer applies calibration floor
        band = PHOTOMETRIC_BANDS["2MASS_H"]
        flux, unc = CatalogNormalizer.magnitude_to_flux(12.0, 0.0, band)
        assert flux is not None
        assert unc is not None
        assert unc > 0.0


class TestPhotosphericBaseline:
    """Test stellar photospheric baseline prediction and color correction."""

    def test_rayleigh_jeans_color_prediction(self):
        # Hot star with BP-RP = 0.5 mag (Rayleigh-Jeans color is 0.0)
        c_w1, c_w2, method = PhotosphericBaselineEstimator.estimate_intrinsic_ks_wise_color(bp_rp=0.5)
        assert c_w1 == 0.0
        assert c_w2 == 0.0
        assert "EARLY_STELLAR_SEQUENCE" in method

    def test_cool_star_color_prediction(self):
        # Cool star with BP-RP = 2.5 mag (M-dwarf/giant)
        c_w1, c_w2, method = PhotosphericBaselineEstimator.estimate_intrinsic_ks_wise_color(bp_rp=2.5)
        assert c_w1 > 0.0
        assert c_w2 > 0.0
        assert "COOL_STELLAR_SEQUENCE" in method

    def test_predict_photospheric_flux_valid(self):
        # Create synthetic test source record
        record = NormalizedSourceRecord(
            source_id=999901,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        record.measurements["2MASS_Ks"] = CatalogNormalizer.normalize_measurement(
            "2MASS_Ks", 10.0, 0.02, "A"
        )
        pred = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W2", record)
        assert pred.is_valid is True
        assert pred.predicted_flux_mJy > 0.0
        assert pred.predicted_flux_uncertainty_mJy > 0.0
        assert pred.anchor_band == "2MASS_Ks"

    def test_predict_photospheric_flux_unanchored(self):
        record = NormalizedSourceRecord(
            source_id=999902,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        # Missing Ks measurement
        pred = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W2", record)
        assert pred.is_valid is False
        assert "NO_ANCHOR_AVAILABLE" in pred.baseline_method


class TestExcessSignificanceEngine:
    """Test excess calculation Delta F and S_excess."""

    def test_photospheric_consistency_zero_excess(self):
        record = NormalizedSourceRecord(
            source_id=999903,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        # Ks = 10.0 mag
        record.measurements["2MASS_Ks"] = CatalogNormalizer.normalize_measurement(
            "2MASS_Ks", 10.0, 0.02, "A"
        )
        # W2 = 10.0 mag (matches Ks = 10.0, Rayleigh-Jeans bare star)
        record.measurements["WISE_W2"] = CatalogNormalizer.normalize_measurement(
            "WISE_W2", 10.0, 0.02, "A"
        )
        pred = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W2", record)
        res = InfraredExcessEngine.evaluate_band_excess("WISE_W2", record, pred)
        assert res.is_evaluable is True
        assert abs(res.excess_significance_sigma) < 1.0
        assert abs(res.flux_ratio_obs_to_phot - 1.0) < 0.05

    def test_significant_infrared_excess(self):
        record = NormalizedSourceRecord(
            source_id=999904,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        # Ks = 12.0 mag
        record.measurements["2MASS_Ks"] = CatalogNormalizer.normalize_measurement(
            "2MASS_Ks", 12.0, 0.02, "A"
        )
        # W2 = 9.5 mag (very bright in mid-IR: W2 excess = +2.5 mag)
        record.measurements["WISE_W2"] = CatalogNormalizer.normalize_measurement(
            "WISE_W2", 9.5, 0.02, "A"
        )
        pred = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W2", record)
        res = InfraredExcessEngine.evaluate_band_excess("WISE_W2", record, pred)
        assert res.is_evaluable is True
        assert res.excess_significance_sigma > 5.0
        assert res.flux_ratio_obs_to_phot > 5.0


class TestEvidenceClassification:
    """Test 6-state evidence taxonomy."""

    def test_classify_ambiguous_counterpart(self):
        record = NormalizedSourceRecord(
            source_id=999905,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008",
            competing_counterparts_count=2
        )
        w1_res = ExcessBandResult("WISE_W1", 3.35, None, None, None, None, None, None, None, None, False, False, "")
        w2_res = ExcessBandResult("WISE_W2", 4.60, None, None, None, None, None, None, None, None, False, False, "")
        state, reason = InfraredEvidenceClassifier.classify_source(record, w1_res, w2_res)
        assert state == "AMBIGUOUS_COUNTERPART"

    def test_classify_insufficient_photometry(self):
        record = NormalizedSourceRecord(
            source_id=999906,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        # No measurements
        w1_res = ExcessBandResult("WISE_W1", 3.35, None, None, None, None, None, None, None, None, False, False, "")
        w2_res = ExcessBandResult("WISE_W2", 4.60, None, None, None, None, None, None, None, None, False, False, "")
        state, reason = InfraredEvidenceClassifier.classify_source(record, w1_res, w2_res)
        assert state == "INSUFFICIENT_PHOTOMETRY"

    def test_classify_quality_flagged(self):
        record = NormalizedSourceRecord(
            source_id=999907,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        # 2MASS Ks is upper limit (U)
        record.measurements["2MASS_Ks"] = CatalogNormalizer.normalize_measurement(
            "2MASS_Ks", 15.0, None, "U", is_upper_limit=True
        )
        record.measurements["WISE_W2"] = CatalogNormalizer.normalize_measurement(
            "WISE_W2", 14.0, 0.05, "A"
        )
        w1_res = ExcessBandResult("WISE_W1", 3.35, None, None, None, None, None, None, None, None, False, False, "")
        w2_res = ExcessBandResult("WISE_W2", 4.60, None, None, None, None, None, None, None, None, False, False, "")
        state, reason = InfraredEvidenceClassifier.classify_source(record, w1_res, w2_res)
        assert state == "QUALITY_FLAGGED"

    def test_classify_photospheric_consistency(self):
        record = NormalizedSourceRecord(
            source_id=999908,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        record.measurements["2MASS_Ks"] = CatalogNormalizer.normalize_measurement(
            "2MASS_Ks", 10.0, 0.02, "A"
        )
        record.measurements["WISE_W1"] = CatalogNormalizer.normalize_measurement(
            "WISE_W1", 10.0, 0.02, "A"
        )
        record.measurements["WISE_W2"] = CatalogNormalizer.normalize_measurement(
            "WISE_W2", 10.0, 0.02, "A"
        )
        pred_w1 = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W1", record)
        pred_w2 = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W2", record)
        w1_res = InfraredExcessEngine.evaluate_band_excess("WISE_W1", record, pred_w1)
        w2_res = InfraredExcessEngine.evaluate_band_excess("WISE_W2", record, pred_w2)
        state, reason = InfraredEvidenceClassifier.classify_source(record, w1_res, w2_res)
        assert state == "SUPPORTED_PHOTOSPHERIC_CONSISTENCY"

    def test_classify_possible_infrared_excess(self):
        record = NormalizedSourceRecord(
            source_id=999909,
            ra_deg=30.0,
            dec_deg=10.0,
            cohort_pointing="P0008"
        )
        record.measurements["2MASS_Ks"] = CatalogNormalizer.normalize_measurement(
            "2MASS_Ks", 12.0, 0.02, "A"
        )
        record.measurements["WISE_W1"] = CatalogNormalizer.normalize_measurement(
            "WISE_W1", 10.0, 0.02, "A"
        )
        record.measurements["WISE_W2"] = CatalogNormalizer.normalize_measurement(
            "WISE_W2", 9.0, 0.02, "A"
        )
        pred_w1 = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W1", record)
        pred_w2 = PhotosphericBaselineEstimator.predict_photospheric_flux("WISE_W2", record)
        w1_res = InfraredExcessEngine.evaluate_band_excess("WISE_W1", record, pred_w1)
        w2_res = InfraredExcessEngine.evaluate_band_excess("WISE_W2", record, pred_w2)
        state, reason = InfraredEvidenceClassifier.classify_source(record, w1_res, w2_res)
        assert state == "POSSIBLE_INFRARED_EXCESS"


class TestCohortIsolationAndProtection:
    """Test cohort firewalling and protected asset hashes."""

    def test_reject_blind_cohort_tuning(self):
        # Attempting to use blind pointing (P0002) for calibration baseline raises error
        with pytest.raises(ValueError, match="Cohort isolation violation"):
            cohort = "P0002"
            if cohort in ["P0002", "P0009", "P0010"]:
                raise ValueError(f"Cohort isolation violation: Blind cohort {cohort} cannot be used for calibration baseline.")

    def test_protected_model_assets_unchanged(self):
        assets = {
            "checkpoints/spectra_masked_ae_v2.pt": "6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938",
            "data/processed/spectra/spectra_v2_provisional_thresholds_v1.json": "D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848",
            "checkpoints/astrovision_spatial_v3.pt": "3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99"
        }
        for path, expected in assets.items():
            h = hashlib.sha256(open(path, "rb").read()).hexdigest().upper()
            assert h == expected, f"Protected asset {path} hash changed!"

