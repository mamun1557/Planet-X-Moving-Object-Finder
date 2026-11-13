"""
Unit and Regression Test Suite for Benchmark Engine v2
NASA Space Apps Challenge 2026 — SPECTRA-X / F1 Phase 3 Task 1.1B

Focus Areas:
1. FITS HDU discovery and schema validation across detectors.
2. Detector-specific gain (AGM) selection and pixel-level lookup.
3. In-file ePSF prioritization, bin finding, and exact flux conservation.
4. Physical unit conversion (MJy/sr*pix to Jansky and electrons).
5. Poisson noise realism and physical variance propagation.
6. Mask and quality flag preservation.
7. Injection boundary and margin rejection.
8. Separation of point-source and extended-source injection paths.
9. Truth / prediction isolation (no circular input difference measurement).
10. Actual ASTROVISION model output recovery interface.
11. Reproducible detector-stratified sampling mechanics.
12. Benchmark v1 assets cryptographic immutability.
"""

import os
import glob
import math
import hashlib
import numpy as np
import pytest
import torch
from astropy.io import fits

from scripts.validation.astrovision_injection_benchmark_v2 import (
    SPHERExFITSValidatorV2,
    AbsoluteGainProviderV2,
    InFilePSFProviderV2,
    PhysicalSpatialInjectionEngineV2,
    AstroVisionEvaluatorV2,
    StratifiedDetectorSamplerV2,
    MatchedCutoutPairV2,
    ModelOutputRecoveryRecordV2,
    FootprintGeometryV2,
    GroupAwarePartitionManagerV2,
    PartitionAssignmentResultV2,
    FATAL_FLAG_MASK,
    DEFAULT_PIXEL_SCALE_ARCSEC,
    NOMINAL_PIXEL_SOLID_ANGLE_SR
)

SAMPLE_L2_FILE = "data/spherex/qr3/level2/level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits"
FROZEN_CHECKPOINT = "checkpoints/astrovision_spatial_v2.pt"
EXPECTED_CHECKPOINT_SHA256 = "f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557"
BENCHMARK_V1_RESULTS = "data/processed/validation/astrovision_injection_results.csv"
EXPECTED_V1_RESULTS_SHA256 = "22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c"


class TestAstroVisionBenchmarkEngineV2:

    def test_benchmark_v1_immutability(self):
        """Verifies that Benchmark v1 results and frozen checkpoint remain untouched."""
        assert os.path.exists(FROZEN_CHECKPOINT)
        with open(FROZEN_CHECKPOINT, "rb") as f:
            ckpt_hash = hashlib.sha256(f.read()).hexdigest()
        assert ckpt_hash == EXPECTED_CHECKPOINT_SHA256, "Frozen checkpoint hash changed!"

        assert os.path.exists(BENCHMARK_V1_RESULTS)
        with open(BENCHMARK_V1_RESULTS, "rb") as f:
            v1_hash = hashlib.sha256(f.read()).hexdigest()
        assert v1_hash == EXPECTED_V1_RESULTS_SHA256, "Benchmark v1 results file modified!"

    def test_fits_hdu_discovery_and_validation(self):
        """Validates robust HDU discovery on genuine Level-2 SPHEREx FITS."""
        v = SPHERExFITSValidatorV2.verify_and_inspect(SAMPLE_L2_FILE)
        assert v.is_valid is True
        assert v.detector_id == 1
        assert v.has_image is True
        assert v.has_variance is True
        assert v.has_flags is True
        assert v.has_epsf is True
        assert v.epsf_num_bins == 441
        assert v.exptime_sec > 100.0
        assert 6.0 <= v.pixel_scale_arcsec <= 6.3

        # Test failure on non-existent file
        v_bad = SPHERExFITSValidatorV2.verify_and_inspect("data/spherex/non_existent.fits")
        assert v_bad.is_valid is False
        assert "not found" in v_bad.error_message.lower()

    def test_detector_specific_gain_selection(self):
        """Verifies detector-specific AGM gain maps for all 6 detectors (D1 to D6)."""
        gain_provider = AbsoluteGainProviderV2()
        expected_medians = {
            1: 0.1168,
            2: 0.1124,
            3: 0.1085,
            4: 0.0894,
            5: 0.3373,
            6: 0.4580
        }

        for det_id, exp_med in expected_medians.items():
            agm_info = gain_provider.get_agm_data(det_id)
            assert agm_info["detector_id"] == det_id
            assert agm_info["agm_map"].shape == (2040, 2040)
            assert "MJy s / (electron sr)" in agm_info["bunit"]
            # Verify median within 2% tolerance of audited value
            assert abs(agm_info["median_gain"] - exp_med) / exp_med < 0.02, (
                f"Detector {det_id} gain mismatch: {agm_info['median_gain']} vs {exp_med}"
            )

        # Test localized pixel query
        d6_gain_center = gain_provider.get_pixel_gain(6, 1020, 1020)
        assert d6_gain_center > 0.35, f"Detector 6 center gain too low: {d6_gain_center}"

    def test_infile_epsf_prioritization_and_flux_conservation(self):
        """Verifies in-file ePSF extraction and exact subpixel flux conservation."""
        psf_provider = InFilePSFProviderV2()
        test_flux = 15.75  # MJy/sr*pix
        xs, ys, flux_2d, meta = psf_provider.render_point_source(
            fits_path=SAMPLE_L2_FILE,
            detector_id=1,
            det_x=1020.0,
            det_y=1020.0,
            sub_x=64.35,
            sub_y=64.65,
            total_flux_mjy_sr_pix=test_flux,
            kernel_radius=5
        )

        assert meta["epsf_provenance"] == "IN_FILE_HDU_EPSF"
        assert meta["epsf_total_bins"] == 441
        assert meta["actual_kernel_peak_fraction"] > 0.20
        # Strict flux conservation check
        rendered_sum = float(np.sum(flux_2d))
        np.testing.assert_allclose(rendered_sum, test_flux, rtol=1e-6)

    def test_physical_variance_propagation_with_true_agm(self):
        """Verifies that physical photon shot noise scales with detector-specific AGM."""
        engine = PhysicalSpatialInjectionEngineV2()
        patch_size = 64
        base_var_val = 0.0010
        img = np.full((patch_size, patch_size), 0.5, dtype=np.float32)
        var = np.full((patch_size, patch_size), base_var_val, dtype=np.float32)
        flags = np.zeros((patch_size, patch_size), dtype=np.int32)

        test_flux = 20.0  # MJy/sr*pix
        exptime = 115.12

        # Inject on Detector 6 (MWIR, AGM ~ 0.458)
        res_d6 = engine.inject_point_source(
            cutout_img=img,
            cutout_var=var,
            cutout_flags=flags,
            fits_path=SAMPLE_L2_FILE,
            detector_id=6,
            det_x0=500,
            det_y0=500,
            det_cx=532.0,
            det_cy=532.0,
            sub_x=32.0,
            sub_y=32.0,
            total_flux_mjy_sr_pix=test_flux,
            exptime=exptime,
            add_poisson_noise=False
        )

        assert res_d6["rejected"] is False
        assert res_d6["applied_agm_median"] > 0.40
        # Verify shot variance corresponds to D6 pixel gain (~0.458-0.50), NOT D1 gain (0.1168)
        # Check variance propagation at the peak flux pixel
        fy, fx = np.unravel_index(np.argmax(res_d6["signal_map"]), res_d6["signal_map"].shape)
        actual_added_var_at_peak = float(res_d6["injected_variance"][fy, fx] - var[fy, fx])
        pixel_agm = engine.gain_provider.get_pixel_gain(6, 500 + fy, 500 + fx)
        expected_var_at_peak = float(res_d6["peak_flux_mjy_sr"] * pixel_agm / exptime)
        np.testing.assert_allclose(actual_added_var_at_peak, expected_var_at_peak, rtol=1e-4)

    def test_physical_unit_conversions(self):
        """Verifies physical conversions between MJy/sr*pix, electrons, and Jansky."""
        engine = PhysicalSpatialInjectionEngineV2()
        patch_size = 64
        img = np.zeros((patch_size, patch_size), dtype=np.float32)
        var = np.ones((patch_size, patch_size), dtype=np.float32) * 1e-4
        flags = np.zeros((patch_size, patch_size), dtype=np.int32)

        test_flux_mjy_sr_pix = 10.0
        solid_angle = NOMINAL_PIXEL_SOLID_ANGLE_SR

        res = engine.inject_point_source(
            cutout_img=img,
            cutout_var=var,
            cutout_flags=flags,
            fits_path=SAMPLE_L2_FILE,
            detector_id=1,
            det_x0=1000,
            det_y0=1000,
            det_cx=1032.0,
            det_cy=1032.0,
            sub_x=32.0,
            sub_y=32.0,
            total_flux_mjy_sr_pix=test_flux_mjy_sr_pix,
            exptime=100.0,
            pixel_solid_angle_sr=solid_angle,
            add_poisson_noise=False
        )

        # Expected flux in Jy: 10.0 [MJy/sr*pix] * 1e6 [Jy/MJy] * 8.8963e-10 [sr]
        expected_jy = test_flux_mjy_sr_pix * 1e6 * solid_angle
        np.testing.assert_allclose(res["flux_jy"], expected_jy, rtol=1e-5)

    def test_injection_boundary_rejection(self):
        """Verifies that injections close to image boundaries are properly rejected."""
        engine = PhysicalSpatialInjectionEngineV2()
        patch_size = 128
        img = np.zeros((patch_size, patch_size), dtype=np.float32)
        var = np.ones((patch_size, patch_size), dtype=np.float32) * 1e-4
        flags = np.zeros((patch_size, patch_size), dtype=np.int32)

        # Point source too close to boundary (sub_x = 3.0 < 6.0)
        res_pt = engine.inject_point_source(
            cutout_img=img,
            cutout_var=var,
            cutout_flags=flags,
            fits_path=SAMPLE_L2_FILE,
            detector_id=1,
            det_x0=500,
            det_y0=500,
            det_cx=503.0,
            det_cy=564.0,
            sub_x=3.0,
            sub_y=64.0,
            total_flux_mjy_sr_pix=10.0,
            exptime=115.12
        )
        assert res_pt["rejected"] is True
        assert "margin" in res_pt["rejection_reason"].lower()

        # Extended source footprint exceeding margin (FWHM = 36 arcsec -> radius ~ 24 px)
        res_ext = engine.inject_extended_source(
            cutout_img=img,
            cutout_var=var,
            cutout_flags=flags,
            detector_id=1,
            det_x0=500,
            det_y0=500,
            det_cx=510.0,
            det_cy=564.0,
            sub_x=10.0,
            sub_y=64.0,
            total_flux_mjy_sr_pix=10.0,
            fwhm_arcsec=36.0,
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            exptime=115.12
        )
        assert res_ext["rejected"] is True
        assert "exceeds cutout margin" in res_ext["rejection_reason"].lower()

    def test_actual_model_output_recovery_interface(self):
        """
        Validates non-circular model evaluation interface.
        Confirms that residual flux is derived from the model reconstruction,
        NOT from input image subtraction (injected - original).
        """
        evaluator = AstroVisionEvaluatorV2(checkpoint_path=FROZEN_CHECKPOINT)
        patch_size = 128

        # Create synthetic background + point source
        img = np.full((patch_size, patch_size), 0.25, dtype=np.float32)
        var = np.full((patch_size, patch_size), 0.0004, dtype=np.float32)
        mask = np.ones((patch_size, patch_size), dtype=np.float32)

        # Add strong 30 sigma source at center (64, 64)
        yy, xx = np.ogrid[:patch_size, :patch_size]
        dist_sq = (xx - 64.0)**2 + (yy - 64.0)**2
        src = 5.0 * np.exp(-dist_sq / (2.0 * 1.5**2))
        inj_img = img + src.astype(np.float32)
        inj_var = var + (src * (0.1168 / 115.12)).astype(np.float32)

        record = evaluator.evaluate_model_output(
            trial_id="TEST_0001",
            partition="EVALUATION_INJECTION",
            injected_image=inj_img,
            injected_variance=inj_var,
            mask=mask,
            target_true_x=64.0,
            target_true_y=64.0,
            injected_flux_sum=float(np.sum(src)),
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            threshold_tau=150.0
        )

        assert record.trial_id == "TEST_0001"
        assert record.partition == "EVALUATION_INJECTION"
        assert record.model_target_peak_chi2 > 0.0
        assert not math.isnan(record.model_position_error_pix)
        assert record.model_position_error_pix < 1.0  # Well localized
        assert record.is_detected_at_tau is True
        # Verify that model_residual_flux_mjy_sr is populated from model output
        assert record.model_residual_flux_mjy_sr > 0.0

    def test_stratified_detector_sampling_mechanics(self):
        """Verifies detector-stratified sampling across Pointing 0003 files."""
        l2_files = sorted(glob.glob("data/spherex/qr3/level2/*0003*.fits"))
        sampler = StratifiedDetectorSamplerV2(pointing_files=l2_files)

        # Harvest small test quota (3 cutouts per detector)
        quota = 3
        harvested = sampler.harvest_stratified_safe_cutouts(
            cutouts_per_detector=quota,
            patch_size=128,
            random_seed=123
        )

        # Check that all detectors present in pointing files were sampled
        assert len(harvested) == 6
        for det_id in range(1, 7):
            assert len(harvested[det_id]) <= quota
            for item in harvested[det_id]:
                assert item["detector_id"] == det_id
                assert item["sub_img"].shape == (128, 128)
                assert item["sub_var"].shape == (128, 128)
                assert item["sub_mask"].shape == (128, 128)
                # Confirm valid pixel fraction >= 88%
                assert np.mean(item["sub_mask"]) >= 0.88

    def test_paired_residual_differencing_zero_injection_identity(self):
        """
        Validates Audit D Remediation:
        When an un-injected control cutout is paired with itself (zero injection),
        differential residual flux MUST cancel out identically to 0.0 MJy/sr (< 1e-6).
        """
        evaluator = AstroVisionEvaluatorV2(checkpoint_path=FROZEN_CHECKPOINT)
        patch_size = 128
        img = np.full((patch_size, patch_size), 0.25, dtype=np.float32)
        var = np.full((patch_size, patch_size), 0.0004, dtype=np.float32)
        mask = np.ones((patch_size, patch_size), dtype=np.float32)

        pair = MatchedCutoutPairV2(
            pair_id="PAIR_ZERO_001",
            control_trial_id="CTRL_001",
            injected_trial_id="INJ_ZERO_001",
            partition="CALIBRATION",
            filename="synthetic_test.fits",
            detector_id=1,
            obs_id="TEST_001",
            det_x0=500,
            det_y0=500,
            det_cx=564.0,
            det_cy=564.0,
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            pixel_solid_angle_sr=NOMINAL_PIXEL_SOLID_ANGLE_SR,
            exptime_sec=115.12,
            applied_agm=0.1168,
            control_image=img.copy(),
            control_variance=var.copy(),
            injected_image=img.copy(),  # Zero injection: identical to control
            injected_variance=var.copy(),
            mask=mask,
            sub_x_inj=64.0,
            sub_y_inj=64.0,
            injected_flux_sum_mjy_sr_pix=0.0,
            injected_flux_jy=0.0,
            source_type="ZERO_INJECTION_CONTROL"
        )

        record = evaluator.evaluate_paired_model_output(pair, threshold_tau=169.10)

        # Baseline autoencoder reconstruction artifact is non-zero in raw fluxes
        assert record.raw_injected_residual_flux > 0.0
        assert record.raw_control_residual_flux > 0.0
        # But differential residual flux perfectly cancels out
        assert abs(record.differential_residual_flux) < 1e-6
        assert abs(record.differential_residual_flux_jy) < 1e-12
        assert record.is_detected_at_tau is False
        assert record.checkpoint_sha256 == EXPECTED_CHECKPOINT_SHA256
        assert record.valid_aperture_pixels > 30

    def test_paired_residual_differencing_blank_sky_artifact_cancellation(self):
        """
        Validates that the baseline autoencoder artifact on blank sky discovered in Audit D
        is completely eliminated via Paired Residual Differencing.
        """
        evaluator = AstroVisionEvaluatorV2(checkpoint_path=FROZEN_CHECKPOINT)
        patch_size = 128

        # Real SPHEREx Level-2 blank sky cutout with natural background (~0.35 MJy/sr)
        with fits.open(SAMPLE_L2_FILE) as hdul:
            blank_sky = hdul["IMAGE"].data[500:500+patch_size, 500:500+patch_size].astype(np.float32)
            blank_var = hdul["VARIANCE"].data[500:500+patch_size, 500:500+patch_size].astype(np.float32)
        mask = np.ones((patch_size, patch_size), dtype=np.float32)

        # 1. Unpaired evaluation shows significant baseline reconstruction artifact (> 1.0 MJy/sr)
        unpaired_record = evaluator.evaluate_model_output(
            trial_id="UNPAIRED_BLANK",
            partition="EVALUATION",
            injected_image=blank_sky,
            injected_variance=blank_var,
            mask=mask,
            target_true_x=64.0,
            target_true_y=64.0,
            injected_flux_sum=0.0,
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            threshold_tau=169.10
        )
        assert unpaired_record.raw_injected_residual_flux > 1.0  # Baseline artifact present

        # 2. Paired evaluation cancels out the baseline artifact
        paired_record = evaluator.evaluate_model_output(
            trial_id="PAIRED_BLANK",
            partition="EVALUATION",
            injected_image=blank_sky,
            injected_variance=blank_var,
            mask=mask,
            target_true_x=64.0,
            target_true_y=64.0,
            injected_flux_sum=0.0,
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            threshold_tau=169.10,
            control_image=blank_sky,
            control_variance=blank_var,
            pair_id="PAIR_BLANK_001"
        )
        assert paired_record.pair_id == "PAIR_BLANK_001"
        assert abs(paired_record.differential_residual_flux) < 1e-6
        assert abs(paired_record.differential_residual_flux_jy) < 1e-12
        assert abs(paired_record.raw_injected_residual_flux - unpaired_record.raw_injected_residual_flux) < 1e-6
        assert abs(paired_record.raw_control_residual_flux - unpaired_record.raw_injected_residual_flux) < 1e-6

    def test_paired_residual_differencing_structured_sky_cancellation(self):
        """
        Validates that structured sky background artifacts (~1.66 MJy/sr) cancel out
        when paired control differencing is applied.
        """
        evaluator = AstroVisionEvaluatorV2(checkpoint_path=FROZEN_CHECKPOINT)
        patch_size = 128

        # Create structured sky: linear gradient across cutout + smooth fluctuation
        yy, xx = np.mgrid[:patch_size, :patch_size]
        gradient = (xx * 0.005 + yy * 0.003).astype(np.float32)
        fluctuation = (0.05 * np.sin(xx / 10.0) * np.cos(yy / 10.0)).astype(np.float32)
        structured_sky = 0.20 + gradient + fluctuation
        structured_var = np.full((patch_size, patch_size), 0.0005, dtype=np.float32)
        mask = np.ones((patch_size, patch_size), dtype=np.float32)

        pair = MatchedCutoutPairV2(
            pair_id="PAIR_STRUCT_001",
            control_trial_id="CTRL_STRUCT_001",
            injected_trial_id="INJ_STRUCT_001",
            partition="EVALUATION",
            filename="structured_sky.fits",
            detector_id=1,
            obs_id="OBS_STRUCT",
            det_x0=800,
            det_y0=800,
            det_cx=864.0,
            det_cy=864.0,
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            pixel_solid_angle_sr=NOMINAL_PIXEL_SOLID_ANGLE_SR,
            exptime_sec=115.12,
            applied_agm=0.1168,
            control_image=structured_sky.copy(),
            control_variance=structured_var.copy(),
            injected_image=structured_sky.copy(),
            injected_variance=structured_var.copy(),
            mask=mask,
            sub_x_inj=64.0,
            sub_y_inj=64.0,
            injected_flux_sum_mjy_sr_pix=0.0,
            injected_flux_jy=0.0,
            source_type="ZERO_INJECTION_CONTROL"
        )

        record = evaluator.evaluate_paired_model_output(pair, threshold_tau=169.10)
        assert record.raw_control_residual_flux > 1.0  # Structured baseline artifact
        assert abs(record.differential_residual_flux) < 1e-6  # Differential cancellation

    def test_paired_residual_differencing_nonzero_synthetic_injection(self):
        """
        Validates Paired Residual Differencing on genuine synthetic source injection.
        Differential flux must be positive, signed, and isolated from background error.
        Does NOT assume or require differential flux == ground truth injected flux.
        """
        engine = PhysicalSpatialInjectionEngineV2()
        evaluator = AstroVisionEvaluatorV2(checkpoint_path=FROZEN_CHECKPOINT)
        patch_size = 128

        img = np.full((patch_size, patch_size), 0.25, dtype=np.float32)
        var = np.full((patch_size, patch_size), 0.0004, dtype=np.float32)
        flags = np.zeros((patch_size, patch_size), dtype=np.int32)

        # Inject realistic ePSF point source (flux = 15.0 MJy/sr*pix)
        pair, inj_meta = engine.create_matched_point_source_pair(
            cutout_img=img,
            cutout_var=var,
            cutout_flags=flags,
            fits_path=SAMPLE_L2_FILE,
            detector_id=1,
            det_x0=500,
            det_y0=500,
            det_cx=564.0,
            det_cy=564.0,
            sub_x=64.0,
            sub_y=64.0,
            total_flux_mjy_sr_pix=15.0,
            exptime=115.12,
            pair_id="PAIR_NONZERO_001",
            control_trial_id="CTRL_NZ_001",
            injected_trial_id="INJ_NZ_001",
            partition="EVALUATION",
            add_poisson_noise=False  # Deterministic for test
        )

        assert pair is not None
        assert inj_meta["rejected"] is False

        record = evaluator.evaluate_paired_model_output(pair, threshold_tau=169.10)

        # Injected member must have larger raw residual flux than un-injected control
        assert record.raw_injected_residual_flux > record.raw_control_residual_flux
        # Differential residual flux is strictly positive
        assert record.differential_residual_flux > 0.0
        # Arithmetic identity: diff == inj - ctrl
        expected_diff = record.raw_injected_residual_flux - record.raw_control_residual_flux
        assert abs(record.differential_residual_flux - expected_diff) < 1e-6
        # Model does NOT circularly return exact injected flux
        assert record.differential_residual_flux != pair.injected_flux_sum_mjy_sr_pix
        # Astrometric localization
        assert not math.isnan(record.model_position_error_pix)
        assert record.model_position_error_pix < 1.0

    def test_paired_residual_differencing_mask_consistency(self):
        """
        Validates that masked bad pixels are identically excluded from both
        control and injected integrations, and that pixel counts are verified.
        """
        evaluator = AstroVisionEvaluatorV2(checkpoint_path=FROZEN_CHECKPOINT)
        patch_size = 128
        img = np.full((patch_size, patch_size), 0.25, dtype=np.float32)
        var = np.full((patch_size, patch_size), 0.0004, dtype=np.float32)
        mask = np.ones((patch_size, patch_size), dtype=np.float32)

        # Flag 5 pixels inside the aperture around (64, 64)
        mask[64, 64] = 0.0
        mask[64, 65] = 0.0
        mask[65, 64] = 0.0
        mask[63, 64] = 0.0
        mask[64, 63] = 0.0

        pair = MatchedCutoutPairV2(
            pair_id="PAIR_MASK_001",
            control_trial_id="CTRL_MASK_001",
            injected_trial_id="INJ_MASK_001",
            partition="EVALUATION",
            filename="test_mask.fits",
            detector_id=1,
            obs_id="OBS_MASK",
            det_x0=500,
            det_y0=500,
            det_cx=564.0,
            det_cy=564.0,
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            pixel_solid_angle_sr=NOMINAL_PIXEL_SOLID_ANGLE_SR,
            exptime_sec=115.12,
            applied_agm=0.1168,
            control_image=img.copy(),
            control_variance=var.copy(),
            injected_image=img.copy(),
            injected_variance=var.copy(),
            mask=mask,
            sub_x_inj=64.0,
            sub_y_inj=64.0,
            injected_flux_sum_mjy_sr_pix=0.0,
            injected_flux_jy=0.0
        )

        record = evaluator.evaluate_paired_model_output(pair)
        assert record.masked_aperture_pixels == 5
        assert record.valid_aperture_pixels > 30
        assert abs(record.differential_residual_flux) < 1e-6

    def test_paired_residual_differencing_deterministic_inference(self):
        """Validates that paired evaluation is 100% numerically deterministic."""
        evaluator = AstroVisionEvaluatorV2(checkpoint_path=FROZEN_CHECKPOINT)
        patch_size = 128
        img = np.full((patch_size, patch_size), 0.30, dtype=np.float32)
        var = np.full((patch_size, patch_size), 0.0005, dtype=np.float32)
        mask = np.ones((patch_size, patch_size), dtype=np.float32)

        pair = MatchedCutoutPairV2(
            pair_id="PAIR_DET_001",
            control_trial_id="CTRL_DET_001",
            injected_trial_id="INJ_DET_001",
            partition="EVALUATION",
            filename="test_det.fits",
            detector_id=2,
            obs_id="OBS_DET",
            det_x0=500,
            det_y0=500,
            det_cx=564.0,
            det_cy=564.0,
            pixel_scale_arcsec=DEFAULT_PIXEL_SCALE_ARCSEC,
            pixel_solid_angle_sr=NOMINAL_PIXEL_SOLID_ANGLE_SR,
            exptime_sec=115.12,
            applied_agm=0.1124,
            control_image=img.copy(),
            control_variance=var.copy(),
            injected_image=img.copy(),
            injected_variance=var.copy(),
            mask=mask,
            sub_x_inj=64.0,
            sub_y_inj=64.0,
            injected_flux_sum_mjy_sr_pix=0.0,
            injected_flux_jy=0.0
        )

        r1 = evaluator.evaluate_paired_model_output(pair)
        r2 = evaluator.evaluate_paired_model_output(pair)

        assert r1.raw_injected_residual_flux == r2.raw_injected_residual_flux
        assert r1.raw_control_residual_flux == r2.raw_control_residual_flux
        assert r1.differential_residual_flux == r2.differential_residual_flux
        assert r1.model_target_peak_chi2 == r2.model_target_peak_chi2

    def test_matched_cutout_pair_validation_and_mismatch_rejection(self):
        """
        Validates defensive pair validation:
        Mismatched dimensions, masks, invalid detector IDs, or negative exposure times
        must be rejected with ValueError.
        """
        patch_size = 128
        img = np.zeros((patch_size, patch_size), dtype=np.float32)
        var = np.ones((patch_size, patch_size), dtype=np.float32) * 1e-4
        mask = np.ones((patch_size, patch_size), dtype=np.float32)

        # 1. Image shape mismatch
        with pytest.raises(ValueError, match="Control image shape"):
            MatchedCutoutPairV2(
                pair_id="P_BAD_1", control_trial_id="C1", injected_trial_id="I1", partition="CALIBRATION",
                filename="f.fits", detector_id=1, obs_id="O1", det_x0=0, det_y0=0, det_cx=64.0, det_cy=64.0,
                pixel_scale_arcsec=6.15, pixel_solid_angle_sr=8.8e-10, exptime_sec=100.0, applied_agm=0.11,
                control_image=np.zeros((64, 64), dtype=np.float32), injected_image=img, injected_variance=var,
                control_variance=np.ones((64, 64), dtype=np.float32), mask=mask, sub_x_inj=32.0, sub_y_inj=32.0,
                injected_flux_sum_mjy_sr_pix=0.0, injected_flux_jy=0.0
            )

        # 2. Invalid detector ID (7)
        with pytest.raises(ValueError, match="Invalid detector ID"):
            MatchedCutoutPairV2(
                pair_id="P_BAD_2", control_trial_id="C1", injected_trial_id="I1", partition="CALIBRATION",
                filename="f.fits", detector_id=7, obs_id="O1", det_x0=0, det_y0=0, det_cx=64.0, det_cy=64.0,
                pixel_scale_arcsec=6.15, pixel_solid_angle_sr=8.8e-10, exptime_sec=100.0, applied_agm=0.11,
                control_image=img, injected_image=img, control_variance=var, injected_variance=var,
                mask=mask, sub_x_inj=64.0, sub_y_inj=64.0, injected_flux_sum_mjy_sr_pix=0.0, injected_flux_jy=0.0
            )

        # 3. Non-positive exposure time
        with pytest.raises(ValueError, match="Non-positive exposure time"):
            MatchedCutoutPairV2(
                pair_id="P_BAD_3", control_trial_id="C1", injected_trial_id="I1", partition="CALIBRATION",
                filename="f.fits", detector_id=1, obs_id="O1", det_x0=0, det_y0=0, det_cx=64.0, det_cy=64.0,
                pixel_scale_arcsec=6.15, pixel_solid_angle_sr=8.8e-10, exptime_sec=-10.0, applied_agm=0.11,
                control_image=img, injected_image=img, control_variance=var, injected_variance=var,
                mask=mask, sub_x_inj=64.0, sub_y_inj=64.0, injected_flux_sum_mjy_sr_pix=0.0, injected_flux_jy=0.0
            )

        # 4. Out of bounds coordinates
        with pytest.raises(ValueError, match="outside bounds"):
            MatchedCutoutPairV2(
                pair_id="P_BAD_4", control_trial_id="C1", injected_trial_id="I1", partition="CALIBRATION",
                filename="f.fits", detector_id=1, obs_id="O1", det_x0=0, det_y0=0, det_cx=64.0, det_cy=64.0,
                pixel_scale_arcsec=6.15, pixel_solid_angle_sr=8.8e-10, exptime_sec=100.0, applied_agm=0.11,
                control_image=img, injected_image=img, control_variance=var, injected_variance=var,
                mask=mask, sub_x_inj=150.0, sub_y_inj=64.0, injected_flux_sum_mjy_sr_pix=0.0, injected_flux_jy=0.0
            )

    def test_disjoint_partition_assignment(self):
        """
        Validates Audit E / Audit F Remediation:
        Enforces automated, deterministic disjoint partition assignment
        (CALIBRATION vs EVALUATION) with exposure-level grouping and detector balance.
        """
        mock_harvested = {}
        for det_id in range(1, 7):
            mock_harvested[det_id] = [
                {
                    "id": f"D{det_id}_{i}",
                    "detector_id": det_id,
                    "obs_id": f"EXP_{i % 4}",
                    "filename": f"l2_EXP_{i % 4}_D{det_id}.fits",
                    "cx_det": 200.0 + i * 200.0,
                    "cy_det": 200.0
                }
                for i in range(8)
            ]

        partitions = StratifiedDetectorSamplerV2.assign_disjoint_partitions(
            mock_harvested, calibration_fraction=0.5, seed=42
        )

        assert "CALIBRATION" in partitions
        assert "EVALUATION" in partitions
        cal = partitions["CALIBRATION"]
        eval_ = partitions["EVALUATION"]

        # Disjoint verification (zero cutout ID overlap)
        cal_ids = {it["id"] for it in cal}
        eval_ids = {it["id"] for it in eval_}
        assert cal_ids.isdisjoint(eval_ids)

        # Strict exposure independence: no obs_id may appear in both partitions
        cal_obs = {it["obs_id"] for it in cal}
        eval_obs = {it["obs_id"] for it in eval_}
        assert cal_obs.isdisjoint(eval_obs)

        # Strict FITS file independence: no file may cross partitions
        cal_files = {it["filename"] for it in cal}
        eval_files = {it["filename"] for it in eval_}
        assert cal_files.isdisjoint(eval_files)


class TestGroupAwarePartitioningAndLeakagePrevention:
    """
    Leakage Prevention Regression Suite for Task 1.1F.
    Proves that GroupAwarePartitionManagerV2 strictly prevents:
      1. Same exposure in both partitions.
      2. Same FITS file in both partitions.
      3. Overlapping spatial cutouts crossing partitions.
      4. Repeated source IDs crossing partitions.
      5. Missing exposure metadata.
      6. Non-deterministic assignment across runs.
      7. Detector imbalance under group constraints.
      8. Insufficient independent groups.
    """

    def test_leakage_rejection_same_exposure_both_partitions(self):
        """Proves that cutouts sharing the same pointing exposure (obs_id) are NEVER split across partitions."""
        manager = GroupAwarePartitionManagerV2(strict_metadata=True)
        items = [
            {"id": "C1", "obs_id": "EXP_001", "filename": "f1.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C2", "obs_id": "EXP_001", "filename": "f2.fits", "detector_id": 2, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C3", "obs_id": "EXP_001", "filename": "f3.fits", "detector_id": 3, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C4", "obs_id": "EXP_002", "filename": "f4.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C5", "obs_id": "EXP_002", "filename": "f5.fits", "detector_id": 2, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C6", "obs_id": "EXP_003", "filename": "f6.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C7", "obs_id": "EXP_004", "filename": "f7.fits", "detector_id": 2, "cx_det": 200.0, "cy_det": 200.0},
        ]

        res = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

        cal_obs = set(res.calibration_obs_ids)
        eval_obs = set(res.evaluation_obs_ids)

        assert cal_obs.isdisjoint(eval_obs), "Exposure leakage: obs_id present in both partitions!"
        assert len(cal_obs) >= 1
        assert len(eval_obs) >= 1

        # Check all cutouts for EXP_001 are in the same partition
        exp1_parts = {it["partition"] for it in res.calibration_items + res.evaluation_items if it["obs_id"] == "EXP_001"}
        assert len(exp1_parts) == 1, "EXP_001 cutouts were split across partitions!"

    def test_leakage_rejection_same_fits_file_both_partitions(self):
        """Proves that multiple cutouts extracted from the same FITS file belong strictly to the same partition."""
        manager = GroupAwarePartitionManagerV2(strict_metadata=True)
        items = [
            {"id": "C1", "obs_id": "EXP_001", "filename": "pointing_001.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C2", "obs_id": "EXP_001", "filename": "pointing_001.fits", "detector_id": 1, "cx_det": 600.0, "cy_det": 600.0},
            {"id": "C3", "obs_id": "EXP_002", "filename": "pointing_002.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C4", "obs_id": "EXP_003", "filename": "pointing_003.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
        ]

        res = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

        cal_files = set(res.calibration_filenames)
        eval_files = set(res.evaluation_filenames)

        assert cal_files.isdisjoint(eval_files), "FITS file leakage: filename present in both partitions!"
        # pointing_001.fits must be entirely in either CAL or EVAL
        p1_parts = {it["partition"] for it in res.calibration_items + res.evaluation_items if it["filename"] == "pointing_001.fits"}
        assert len(p1_parts) == 1

    def test_leakage_rejection_overlapping_spatial_cutouts(self):
        """Proves that spatially overlapping cutouts in the same file are detected and rejected to prevent background correlation."""
        manager = GroupAwarePartitionManagerV2(min_spatial_sep_pix=128.0, strict_metadata=True)
        items = [
            # C1 and C2 overlap (distance = 40 px < 128 px)
            {"id": "C1", "obs_id": "EXP_001", "filename": "overlap_test.fits", "detector_id": 1, "cx_det": 300.0, "cy_det": 300.0},
            {"id": "C2", "obs_id": "EXP_001", "filename": "overlap_test.fits", "detector_id": 1, "cx_det": 340.0, "cy_det": 300.0},
            # C3 is well separated (distance = 400 px)
            {"id": "C3", "obs_id": "EXP_001", "filename": "overlap_test.fits", "detector_id": 1, "cx_det": 700.0, "cy_det": 300.0},
            {"id": "C4", "obs_id": "EXP_002", "filename": "exp2.fits", "detector_id": 1, "cx_det": 300.0, "cy_det": 300.0},
        ]

        res = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

        # C2 should be in rejected_items
        rej_ids = [it["id"] for it in res.rejected_items]
        assert "C2" in rej_ids
        assert any("SPATIAL_OVERLAP" in it["rejection_reason"] for it in res.rejected_items if it["id"] == "C2")

        # C2 must NOT appear in either calibration or evaluation
        active_ids = [it["id"] for it in res.calibration_items + res.evaluation_items]
        assert "C2" not in active_ids
        assert "C1" in active_ids
        assert "C3" in active_ids

    def test_leakage_rejection_repeated_source_ids(self):
        """Proves that different pointing exposures targeting the same physical source ID are co-grouped and cannot cross partitions."""
        manager = GroupAwarePartitionManagerV2(strict_metadata=True)
        items = [
            # EXP_001 and EXP_002 observe the same source SRC_TARGET_ALPHA
            {"id": "C1", "obs_id": "EXP_001", "filename": "exp1.fits", "detector_id": 1, "source_id": "SRC_TARGET_ALPHA", "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C2", "obs_id": "EXP_002", "filename": "exp2.fits", "detector_id": 1, "source_id": "SRC_TARGET_ALPHA", "cx_det": 200.0, "cy_det": 200.0},
            # Independent exposures
            {"id": "C3", "obs_id": "EXP_003", "filename": "exp3.fits", "detector_id": 1, "source_id": "SRC_BETA", "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C4", "obs_id": "EXP_004", "filename": "exp4.fits", "detector_id": 1, "source_id": "SRC_GAMMA", "cx_det": 200.0, "cy_det": 200.0},
        ]

        res = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

        cal_sources = set(res.calibration_source_ids)
        eval_sources = set(res.evaluation_source_ids)

        assert cal_sources.isdisjoint(eval_sources), "Source leakage: source_id present in both partitions!"

        # EXP_001 and EXP_002 must be assigned to the exact same partition
        p1 = [it["partition"] for it in res.calibration_items + res.evaluation_items if it["obs_id"] == "EXP_001"][0]
        p2 = [it["partition"] for it in res.calibration_items + res.evaluation_items if it["obs_id"] == "EXP_002"][0]
        assert p1 == p2, "Exposures sharing source_id were split across partitions!"

    def test_leakage_rejection_missing_exposure_metadata(self):
        """Proves that cutouts with missing or unresolvable exposure metadata are strictly rejected."""
        # 1. Strict mode raises ValueError
        strict_mgr = GroupAwarePartitionManagerV2(strict_metadata=True)
        bad_items = [
            {"id": "C_BAD", "obs_id": "", "filename": "f1.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C_GOOD", "obs_id": "EXP_001", "filename": "f2.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C_GOOD2", "obs_id": "EXP_002", "filename": "f3.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
        ]
        with pytest.raises(ValueError, match="Missing or invalid 'obs_id' metadata"):
            strict_mgr.assign_partitions(bad_items)

        # 2. Non-strict mode rejects bad items into rejected_items
        lenient_mgr = GroupAwarePartitionManagerV2(strict_metadata=False)
        res = lenient_mgr.assign_partitions(bad_items)
        assert any(it["id"] == "C_BAD" for it in res.rejected_items)
        active_ids = [it["id"] for it in res.calibration_items + res.evaluation_items]
        assert "C_BAD" not in active_ids

    def test_deterministic_assignment_with_fixed_seed(self):
        """Proves that partition assignment is 100% numerically deterministic with a fixed random seed."""
        manager = GroupAwarePartitionManagerV2(strict_metadata=True)
        items = [
            {"id": f"C_{i}", "obs_id": f"EXP_{i % 6}", "filename": f"f_{i % 6}.fits", "detector_id": (i % 6) + 1, "cx_det": 200.0, "cy_det": 200.0}
            for i in range(24)
        ]

        r1 = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)
        r2 = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

        assert r1.calibration_obs_ids == r2.calibration_obs_ids
        assert r1.evaluation_obs_ids == r2.evaluation_obs_ids
        assert [it["id"] for it in r1.calibration_items] == [it["id"] for it in r2.calibration_items]
        assert [it["id"] for it in r1.evaluation_items] == [it["id"] for it in r2.evaluation_items]

    def test_detector_representation_under_group_constraints(self):
        """Proves that multi-detector representation is maintained across partitions where data availability permits."""
        manager = GroupAwarePartitionManagerV2(strict_metadata=True)
        # 6 exposures, each exposing all detectors D1-D6 (36 cutouts total)
        items = []
        for exp_idx in range(6):
            obs = f"OBS_POINTING_{exp_idx}"
            for det in range(1, 7):
                items.append({
                    "id": f"{obs}_D{det}",
                    "obs_id": obs,
                    "filename": f"{obs}_D{det}.fits",
                    "detector_id": det,
                    "cx_det": 500.0,
                    "cy_det": 500.0
                })

        res = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

        # Check detector representation in both partitions
        cal_dets = set()
        for it in res.calibration_items:
            cal_dets.add(it["detector_id"])

        eval_dets = set()
        for it in res.evaluation_items:
            eval_dets.add(it["detector_id"])

        assert cal_dets == {1, 2, 3, 4, 5, 6}, "Calibration partition missing detectors!"
        assert eval_dets == {1, 2, 3, 4, 5, 6}, "Evaluation partition missing detectors!"
        assert set(res.calibration_obs_ids).isdisjoint(set(res.evaluation_obs_ids))

    def test_insufficient_independent_groups_rejection(self):
        """Proves that attempting to partition a dataset with < 2 independent exposure groups raises ValueError."""
        manager = GroupAwarePartitionManagerV2(strict_metadata=True)
        # All cutouts from a single exposure EXP_ONLY_ONE
        items = [
            {"id": "C1", "obs_id": "EXP_ONLY_ONE", "filename": "f1.fits", "detector_id": 1, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C2", "obs_id": "EXP_ONLY_ONE", "filename": "f2.fits", "detector_id": 2, "cx_det": 200.0, "cy_det": 200.0},
            {"id": "C3", "obs_id": "EXP_ONLY_ONE", "filename": "f3.fits", "detector_id": 3, "cx_det": 200.0, "cy_det": 200.0},
        ]

        with pytest.raises(ValueError, match="Insufficient independent exposure groups"):
            manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

    def test_footprint_geometry_diagonal_overlap_rejection(self):
        """
        Proves that two 128x128 cutouts with diagonal center offset (dx=91, dy=91)
        are correctly identified as overlapping, despite having Euclidean center distance
        dr = sqrt(91^2 + 91^2) = 128.69 >= 128.0 (remediating Task 1.1G Audit B).
        """
        fp1 = FootprintGeometryV2(
            x0=0, y0=0, width=128, height=128,
            filename="pointing.fits", detector_id=1, obs_id="OBS_1"
        )
        fp2 = FootprintGeometryV2(
            x0=91, y0=91, width=128, height=128,
            filename="pointing.fits", detector_id=1, obs_id="OBS_1"
        )

        # Euclidean center distance is >= 128.0
        euclidean_dist = math.hypot(fp2.cx - fp1.cx, fp2.cy - fp1.cy)
        assert euclidean_dist >= 128.0, f"Expected dr >= 128, got {euclidean_dist}"

        # Chebyshev center distance is < 128.0
        assert FootprintGeometryV2.check_chebyshev_center_distance(fp1.cx, fp1.cy, fp2.cx, fp2.cy, 128.0) is True

        # Exact half-open 2D bounding box intersection must detect 37x37 = 1369 overlapping pixels
        is_inter, reason = fp1.intersects(fp2)
        assert is_inter is True
        assert "37x37" in reason
        assert "1369" in reason

    def test_footprint_geometry_edge_touching_acceptance(self):
        """
        Proves that edge-touching cutouts ([0, 128) and [128, 256)) share 0 interior pixels
        and are accepted as non-overlapping under half-open interval semantics.
        """
        fp1 = FootprintGeometryV2(
            x0=0, y0=0, width=128, height=128,
            filename="pointing.fits", detector_id=1, obs_id="OBS_1"
        )
        fp2 = FootprintGeometryV2(
            x0=128, y0=0, width=128, height=128,
            filename="pointing.fits", detector_id=1, obs_id="OBS_1"
        )

        assert FootprintGeometryV2.check_chebyshev_center_distance(fp1.cx, fp1.cy, fp2.cx, fp2.cy, 128.0) is False
        is_inter, reason = fp1.intersects(fp2)
        assert is_inter is False
        assert reason == "DISJOINT"

    def test_footprint_geometry_unequal_dimensions(self):
        """Proves that general non-square bounding boxes are rigorously checked for intersection."""
        fp1 = FootprintGeometryV2(
            x0=100, y0=100, width=64, height=128,
            filename="pointing.fits", detector_id=1
        )
        # Overlaps in X [100, 164) vs [150, 250), and in Y [100, 228) vs [120, 180)
        fp2 = FootprintGeometryV2(
            x0=150, y0=120, width=100, height=60,
            filename="pointing.fits", detector_id=1
        )
        is_inter, reason = fp1.intersects(fp2)
        assert is_inter is True
        assert "14x60" in reason  # (164-150) x (180-120) = 14 x 60

        # Disjoint in X: [100, 164) vs [164, 264)
        fp3 = FootprintGeometryV2(
            x0=164, y0=120, width=100, height=60,
            filename="pointing.fits", detector_id=1
        )
        assert fp1.intersects(fp3)[0] is False

    def test_footprint_geometry_cross_file_and_detector_isolation(self):
        """Proves that cutouts with identical pixel coordinates in different files or detectors never collide."""
        fp1 = FootprintGeometryV2(
            x0=100, y0=100, width=128, height=128,
            filename="file_a.fits", detector_id=1
        )
        fp2 = FootprintGeometryV2(
            x0=100, y0=100, width=128, height=128,
            filename="file_b.fits", detector_id=1
        )
        fp3 = FootprintGeometryV2(
            x0=100, y0=100, width=128, height=128,
            filename="file_a.fits", detector_id=2
        )

        assert fp1.intersects(fp2) == (False, "DIFFERENT_FILES_OR_DETECTORS")
        assert fp1.intersects(fp3) == (False, "DIFFERENT_FILES_OR_DETECTORS")

    def test_group_aware_partition_manager_diagonal_overlap_rejection(self):
        """
        Proves that GroupAwarePartitionManagerV2 rejects diagonally overlapping cutouts
        in the same FITS file that would have slipped past Euclidean distance checks.
        """
        manager = GroupAwarePartitionManagerV2(min_spatial_sep_pix=128.0, strict_metadata=True)
        items = [
            {"id": "C_BASE", "obs_id": "EXP_001", "filename": "test.fits", "detector_id": 1, "cx_det": 300.0, "cy_det": 300.0},
            # Diagonal offset dx=91, dy=91 -> Euclidean dist = 128.69 >= 128
            {"id": "C_DIAG", "obs_id": "EXP_001", "filename": "test.fits", "detector_id": 1, "cx_det": 391.0, "cy_det": 391.0},
            # Edge-touching dx=128, dy=0 -> Should be accepted
            {"id": "C_TOUCH", "obs_id": "EXP_001", "filename": "test.fits", "detector_id": 1, "cx_det": 428.0, "cy_det": 300.0},
            # Separate exposure
            {"id": "C_EXP2", "obs_id": "EXP_002", "filename": "test2.fits", "detector_id": 1, "cx_det": 300.0, "cy_det": 300.0},
        ]

        res = manager.assign_partitions(items, calibration_fraction=0.5, seed=42)

        rej_ids = [it["id"] for it in res.rejected_items]
        assert "C_DIAG" in rej_ids, "Diagonal overlap C_DIAG was NOT rejected by FootprintGeometryV2!"
        assert any("SPATIAL_OVERLAP" in it["rejection_reason"] for it in res.rejected_items if it["id"] == "C_DIAG")

        active_ids = [it["id"] for it in res.calibration_items + res.evaluation_items]
        assert "C_BASE" in active_ids
        assert "C_TOUCH" in active_ids
        assert "C_EXP2" in active_ids

    def test_detector_aware_harvesting_all_detectors_nonzero(self):
        """
        Proves that detector-aware harvesting successfully retrieves cutouts for all detectors D1-D6,
        resolving the D1/D2 zero-harvest attrition defect (Task 1.1G Audit C).
        """
        p3_files = sorted(glob.glob("data/spherex/qr3/level2/*0003*.fits"))
        sampler = StratifiedDetectorSamplerV2(
            pointing_files=p3_files,
            catalog_path="data/processed/validation/pointing_0003_final_validated_catalogue.csv"
        )
        harvested = sampler.harvest_stratified_safe_cutouts(
            cutouts_per_detector=10,
            patch_size=128,
            min_source_dist_pix=8.0,
            random_seed=42,
            num_probes_per_file=600
        )

        for det in range(1, 7):
            count = len(harvested.get(det, []))
            assert count >= 5, f"Detector {det} yielded insufficient cutouts: {count} < 5"
            # Verify noise metadata fields are present
            first = harvested[det][0]
            assert "bg_std" in first
            assert "bg_mad" in first
            assert "bg_std_eff" in first
            assert first["bg_std_eff"] >= first["bg_std"]

    def test_five_partition_campaign_schema_disjointness(self):
        """
        Proves that the controlled campaign driver prepares a five-partition manifest
        with strict out-of-sample calibration injections and zero cross-partition exposure leakage.
        """
        from scripts.validation.astrovision_controlled_campaign_driver import (
            AstroVisionControlledCampaignDriver,
            CAMPAIGN_EXECUTION_LOCKED
        )

        driver = AstroVisionControlledCampaignDriver()
        package = driver.prepare_campaign_manifest(cutouts_per_detector=15)

        assert package["governance"]["campaign_status"] == "PREPARED_LOCKED"
        assert package["governance"]["execution_permitted"] is False
        assert CAMPAIGN_EXECUTION_LOCKED is True

        trials_by_part = package["experimental_design"]["trials_by_partition"]
        expected_partitions = {
            "CALIBRATION_CONTROL",
            "CALIBRATION_INJECTION",
            "EVALUATION_CONTROL",
            "EVALUATION_POINT_SOURCE_INJECTION",
            "EVALUATION_EXTENDED_SOURCE_INJECTION"
        }
        assert set(trials_by_part.keys()) == expected_partitions

        # Every partition must have positive counts
        for p, count in trials_by_part.items():
            assert count > 0, f"Partition {p} has zero trials!"

        cal_obs = set(package["partition_summary"]["calibration_obs_ids"])
        eval_obs = set(package["partition_summary"]["evaluation_obs_ids"])
        assert cal_obs.isdisjoint(eval_obs), "Exposure leakage between calibration and evaluation obs_ids!"

        trials = package["trials_manifest"]
        for t in trials:
            part = t["partition"]
            obs = t["obs_id"]
            if part in ("CALIBRATION_CONTROL", "CALIBRATION_INJECTION"):
                assert obs in cal_obs, f"Trial {t['trial_id']} in {part} uses eval obs_id {obs}!"
            elif part in ("EVALUATION_CONTROL", "EVALUATION_POINT_SOURCE_INJECTION", "EVALUATION_EXTENDED_SOURCE_INJECTION"):
                assert obs in eval_obs, f"Trial {t['trial_id']} in {part} uses cal obs_id {obs}!"

            assert "parent_cutout_id" in t
            assert "matched_control_id" in t
            assert len(t["parent_cutout_id"]) > 0
            assert len(t["matched_control_id"]) > 0


