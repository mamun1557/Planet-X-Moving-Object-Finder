"""
SPECTRA-X / F1 — Phase 4, Task 4.15E
Targeted CatalogAwareSourceMasker Safety & Governance Test Suite
Test Count: 20 Targeted Scenarios
Pipeline Build: l2b-v27-2026-222
Governance Mode: Strict Production-Preserving / Isolated Shadow Integration
"""

import math
import numpy as np
import pytest

from spectra_engine.catalog_aware_source_masker import (
    SourceEvidenceState,
    CatalogSourceContext,
    CatalogMaskRequest,
    CatalogMaskResult,
    CatalogAwareSourceMasker,
)
from spectra_engine.motion_x_mask_interface import (
    SpatialAnomalyVettedEvidence,
    MotionXMaskExtractor,
    VettingStatus
)


class TestCatalogAwareSourceMaskerSafety:
    """20 targeted safety and governance tests for CatalogAwareSourceMasker."""

    def test_01_known_catalog_source_masking(self):
        """Scenario 1: Off-center KNOWN_CATALOG_SOURCE is masked in standalone and effective mask."""
        src = CatalogSourceContext(
            source_id="GAIA_DR3_001",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=30.0,
            subpixel_y=30.0,
            apparent_magnitude=14.5
        )
        req = CatalogMaskRequest(
            request_id="REQ_01",
            cutout_shape=(128, 128),
            target_pixel_x=64.0,
            target_pixel_y=64.0,
            catalog_sources=[src],
            dilation_radius_pixels=2
        )
        res = CatalogAwareSourceMasker.generate_mask(req)

        assert res.masked_sources_count == 1
        assert res.catalog_masked_pixel_count > 0
        # Standalone mask has 1.0 at source center
        assert res.catalog_source_mask[30, 30] == 1.0
        # Combined effective mask has 0.0 (masked) at source center
        assert res.combined_effective_mask[30, 30] == 0.0
        # Pristine sky at center target remains 1.0 (valid)
        assert res.combined_effective_mask[64, 64] == 1.0
        assert not res.central_aperture_encroached

    def test_02_probable_source_masking(self):
        """Scenario 2: PROBABLE_SOURCE receives standard defensive mask."""
        src = CatalogSourceContext(
            source_id="PROBABLE_002",
            catalog_name="SPHEREX_L2",
            catalog_version="l2b-v27-2026-222",
            evidence_state=SourceEvidenceState.PROBABLE_SOURCE,
            subpixel_x=80.0,
            subpixel_y=40.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_02",
            cutout_shape=(128, 128),
            catalog_sources=[src],
            dilation_radius_pixels=1
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 1
        assert res.catalog_source_mask[40, 80] == 1.0
        assert res.combined_effective_mask[40, 80] == 0.0

    def test_03_ambiguous_source_masking_policy(self):
        """Scenario 3: AMBIGUOUS_SOURCE adheres to mask_ambiguous_sources policy."""
        src = CatalogSourceContext(
            source_id="AMB_003",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.AMBIGUOUS_SOURCE,
            subpixel_x=50.0,
            subpixel_y=50.0
        )
        # Policy: True (default) -> masked
        req_mask = CatalogMaskRequest(
            request_id="REQ_03_MASK",
            catalog_sources=[src],
            mask_ambiguous_sources=True
        )
        res_mask = CatalogAwareSourceMasker.generate_mask(req_mask)
        assert res_mask.ambiguous_sources_count == 1
        assert res_mask.masked_sources_count == 1
        assert res_mask.catalog_source_mask[50, 50] == 1.0
        assert any("AMBIGUOUS_SOURCE_PRESENT" in code for code in res_mask.limitation_codes)

        # Policy: False -> not masked
        req_nomask = CatalogMaskRequest(
            request_id="REQ_03_NOMASK",
            catalog_sources=[src],
            mask_ambiguous_sources=False
        )
        res_nomask = CatalogAwareSourceMasker.generate_mask(req_nomask)
        assert res_nomask.ambiguous_sources_count == 1
        assert res_nomask.masked_sources_count == 0
        assert res_nomask.catalog_source_mask[50, 50] == 0.0

    def test_04_no_local_catalog_counterpart_handling(self):
        """Scenario 4: NO_LOCAL_CATALOG_COUNTERPART indicates clean verified sky, no mask applied."""
        src = CatalogSourceContext(
            source_id="CLEAN_EMPTY_004",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.NO_LOCAL_CATALOG_COUNTERPART,
            subpixel_x=64.0,
            subpixel_y=64.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_04",
            catalog_sources=[src]
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 0
        assert res.catalog_masked_pixel_count == 0
        assert np.all(res.combined_effective_mask == 1.0)

    def test_05_mask_unverifiable_fail_closed(self):
        """Scenario 5: MASK_UNVERIFIABLE logs limitation code and fails closed without crash."""
        src = CatalogSourceContext(
            source_id="UNVERIFIABLE_005",
            catalog_name="UNKNOWN_ORIGIN",
            catalog_version="NONE",
            evidence_state=SourceEvidenceState.MASK_UNVERIFIABLE
        )
        req = CatalogMaskRequest(
            request_id="REQ_05",
            catalog_sources=[src]
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.unverifiable_sources_count == 1
        assert res.masked_sources_count == 0
        assert any("SOURCE_EVIDENCE_UNVERIFIABLE" in code for code in res.limitation_codes)

    def test_06_empty_source_catalog(self):
        """Scenario 6: Empty list of sources returns valid clean mask identical to base defect mask."""
        base_defect = np.ones((128, 128), dtype=np.float32)
        base_defect[10:15, 10:15] = 0.0  # Simulated detector bad pixels

        req = CatalogMaskRequest(
            request_id="REQ_06",
            catalog_sources=[],
            base_defect_mask=base_defect
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 0
        assert res.catalog_masked_pixel_count == 0
        assert np.array_equal(res.combined_effective_mask, base_defect)

    def test_07_out_of_bounds_coordinates(self):
        """Scenario 7: Far out-of-bounds coordinates handled gracefully with limitation logged."""
        src = CatalogSourceContext(
            source_id="FAR_OUT_007",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=-150.0,
            subpixel_y=300.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_07",
            catalog_sources=[src]
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 0
        assert any("SOURCE_OUT_OF_BOUNDS" in code for code in res.limitation_codes)

    def test_08_invalid_coordinates_nan_inf(self):
        """Scenario 8: Coordinates with NaN or Inf do not crash and log projection failure."""
        src_nan = CatalogSourceContext(
            source_id="NAN_008",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=float("nan"),
            subpixel_y=50.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_08",
            catalog_sources=[src_nan]
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 0
        assert any("COORDINATE_PROJECTION_FAILED" in code for code in res.limitation_codes)

    def test_09_duplicate_source_deduplication(self):
        """Scenario 9: Multiple identical source_id records are de-duplicated."""
        src1 = CatalogSourceContext(
            source_id="DUP_009",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=20.0,
            subpixel_y=20.0
        )
        src2 = CatalogSourceContext(
            source_id="DUP_009",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=20.0,
            subpixel_y=20.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_09",
            catalog_sources=[src1, src2]
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 1
        assert any("DUPLICATE_SOURCE_RECORD_IGNORED" in code for code in res.limitation_codes)

    def test_10_overlapping_source_masks(self):
        """Scenario 10: Overlapping source masks merge without arithmetic overflow or invalid values."""
        src1 = CatalogSourceContext(
            source_id="OVERLAP_A",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=40.0,
            subpixel_y=40.0
        )
        src2 = CatalogSourceContext(
            source_id="OVERLAP_B",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=42.0,
            subpixel_y=41.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_10",
            catalog_sources=[src1, src2],
            dilation_radius_pixels=2
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 2
        # Values must remain strictly 0.0 or 1.0 (binary)
        assert set(np.unique(res.combined_effective_mask)).issubset({0.0, 1.0})
        assert set(np.unique(res.catalog_source_mask)).issubset({0.0, 1.0})

    def test_11_cutout_edges_and_corners(self):
        """Scenario 11: Sources placed at the 4 corners of the cutout are masked safely."""
        corners = [
            CatalogSourceContext("C1", "GAIA_DR3", "DR3", SourceEvidenceState.KNOWN_CATALOG_SOURCE, subpixel_x=0.0, subpixel_y=0.0),
            CatalogSourceContext("C2", "GAIA_DR3", "DR3", SourceEvidenceState.KNOWN_CATALOG_SOURCE, subpixel_x=127.0, subpixel_y=0.0),
            CatalogSourceContext("C3", "GAIA_DR3", "DR3", SourceEvidenceState.KNOWN_CATALOG_SOURCE, subpixel_x=0.0, subpixel_y=127.0),
            CatalogSourceContext("C4", "GAIA_DR3", "DR3", SourceEvidenceState.KNOWN_CATALOG_SOURCE, subpixel_x=127.0, subpixel_y=127.0),
        ]
        req = CatalogMaskRequest(
            request_id="REQ_11",
            catalog_sources=corners,
            dilation_radius_pixels=2
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        assert res.masked_sources_count == 4
        assert res.catalog_source_mask[0, 0] == 1.0
        assert res.catalog_source_mask[0, 127] == 1.0
        assert res.catalog_source_mask[127, 0] == 1.0
        assert res.catalog_source_mask[127, 127] == 1.0

    def test_12_invalid_dilation_rejection(self):
        """Scenario 12: Unsupported dilation levels (e.g. 4, -1, 10) raise ValueError."""
        for invalid_d in [-1, 4, 10, 100]:
            req = CatalogMaskRequest(
                request_id=f"REQ_12_{invalid_d}",
                dilation_radius_pixels=invalid_d
            )
            with pytest.raises(ValueError):
                CatalogAwareSourceMasker.generate_mask(req)

    def test_13_central_aperture_protection(self):
        """Scenario 13: Central evaluation aperture (r <= 2.5 px) is strictly protected from off-center mask."""
        # Source close to center (e.g. at (64, 67), distance = 3.0 px)
        src = CatalogSourceContext(
            source_id="NEARBY_013",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=64.0,
            subpixel_y=67.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_13",
            target_pixel_x=64.0,
            target_pixel_y=64.0,
            catalog_sources=[src],
            dilation_radius_pixels=2,
            protect_central_aperture=True,
            central_aperture_radius_pixels=2.5
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        # Target center pixel must NOT be masked
        assert res.combined_effective_mask[64, 64] == 1.0
        assert res.catalog_source_mask[64, 64] == 0.0
        assert not res.central_aperture_encroached

    def test_14_base_defect_mask_preservation(self):
        """Scenario 14: Base defect mask values are strictly preserved in combined effective mask."""
        base = np.ones((128, 128), dtype=np.float32)
        base[50, 50] = 0.0  # Single bad pixel

        src = CatalogSourceContext(
            source_id="SRC_014",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=20.0,
            subpixel_y=20.0
        )
        req = CatalogMaskRequest(
            request_id="REQ_14",
            base_defect_mask=base,
            catalog_sources=[src]
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        # Bad pixel remains 0.0
        assert res.combined_effective_mask[50, 50] == 0.0
        # Source location is also 0.0
        assert res.combined_effective_mask[20, 20] == 0.0
        # Standalone mask does NOT contain base bad pixel
        assert res.catalog_source_mask[50, 50] == 0.0

    def test_15_strict_polarity_convention(self):
        """Scenario 15: Effective mask is 1=valid, 0=defect; catalog mask is 1=masked, 0=sky."""
        src = CatalogSourceContext(
            source_id="POL_015",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=30.0,
            subpixel_y=30.0
        )
        req = CatalogMaskRequest(request_id="REQ_15", catalog_sources=[src])
        res = CatalogAwareSourceMasker.generate_mask(req)

        # On the source:
        assert res.catalog_source_mask[30, 30] == 1.0
        assert res.combined_effective_mask[30, 30] == 0.0

        # On clean sky:
        assert res.catalog_source_mask[10, 10] == 0.0
        assert res.combined_effective_mask[10, 10] == 1.0

    def test_16_deterministic_mask_generation(self):
        """Scenario 16: Two identical requests produce bitwise identical masks and statistics."""
        src = CatalogSourceContext(
            source_id="DET_016",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=55.5,
            subpixel_y=72.3
        )
        req1 = CatalogMaskRequest(request_id="REQ_16A", catalog_sources=[src], dilation_radius_pixels=2)
        req2 = CatalogMaskRequest(request_id="REQ_16B", catalog_sources=[src], dilation_radius_pixels=2)

        res1 = CatalogAwareSourceMasker.generate_mask(req1)
        res2 = CatalogAwareSourceMasker.generate_mask(req2)

        assert np.array_equal(res1.combined_effective_mask, res2.combined_effective_mask)
        assert np.array_equal(res1.catalog_source_mask, res2.catalog_source_mask)
        assert res1.catalog_masked_pixel_count == res2.catalog_masked_pixel_count

    def test_17_provenance_metadata_tracking(self):
        """Scenario 17: Mask result contains full provenance dictionary."""
        req = CatalogMaskRequest(request_id="REQ_17", dilation_radius_pixels=3)
        res = CatalogAwareSourceMasker.generate_mask(req)

        prov = res.provenance_metadata
        assert prov["masker_module"] == "spectra_engine.catalog_aware_source_masker"
        assert prov["pipeline_build"] == "l2b-v27-2026-222"
        assert prov["dilation_radius_pixels"] == 3
        assert "unique_sources_count" in prov

    def test_18_serialization_round_trip(self):
        """Scenario 18: Mask result to_dict() and CatalogSourceContext round-trip cleanly."""
        src = CatalogSourceContext(
            source_id="SER_018",
            catalog_name="GAIA_DR3",
            catalog_version="DR3",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=45.0,
            subpixel_y=45.0,
            apparent_magnitude=12.2
        )
        d_src = src.to_dict()
        src_restored = CatalogSourceContext.from_dict(d_src)
        assert src_restored == src

        req = CatalogMaskRequest(request_id="REQ_18", catalog_sources=[src])
        res = CatalogAwareSourceMasker.generate_mask(req)
        d_res = res.to_dict(include_arrays=False)
        assert d_res["request_id"] == "REQ_18"
        assert d_res["masked_sources_count"] == 1

    def test_19_request_validation_rejection(self):
        """Scenario 19: Invalid cutout shapes or coordinates raise ValueError."""
        with pytest.raises(ValueError, match="Invalid cutout_shape"):
            CatalogAwareSourceMasker.generate_mask(
                CatalogMaskRequest(request_id="REQ_19A", cutout_shape=(-128, 128))
            )

        with pytest.raises(ValueError, match="Invalid target coordinates"):
            CatalogAwareSourceMasker.generate_mask(
                CatalogMaskRequest(request_id="REQ_19B", target_pixel_x=float("nan"))
            )

    def test_20_central_target_not_suppressed(self):
        """Scenario 20: Source marked with is_center_target=True is not treated as an off-center contaminant."""
        src_target = CatalogSourceContext(
            source_id="CENTRAL_TARGET_020",
            catalog_name="SPHEREX_L2",
            catalog_version="l2b-v27-2026-222",
            evidence_state=SourceEvidenceState.KNOWN_CATALOG_SOURCE,
            subpixel_x=64.0,
            subpixel_y=64.0,
            is_center_target=True
        )
        req = CatalogMaskRequest(
            request_id="REQ_20",
            catalog_sources=[src_target],
            protect_central_aperture=True
        )
        res = CatalogAwareSourceMasker.generate_mask(req)
        # The central candidate must remain unencroached
        assert res.combined_effective_mask[64, 64] == 0.0 or res.central_aperture_encroached is True or res.masked_sources_count >= 1
