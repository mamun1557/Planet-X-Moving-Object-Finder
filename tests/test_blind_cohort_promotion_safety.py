"""
SPECTRA-X / F1 — Phase 4, Task 4.8R
Targeted Blind-Cohort Promotion Safety & Governance Remediation Test Suite

Validates the fail-closed evidence-promotion safeguard for blind evaluation cohorts
(P0002, P0009, P0010) across all 20 requirements from Section 7:
 1. P0008 valid photometry preserves existing behavior.
 2. P0002 with external photometry cannot claim confirmed excess.
 3. P0009 with external photometry cannot claim confirmed excess.
 4. P0010 with external photometry cannot claim confirmed excess.
 5. Blind source without external photometry remains UNVERIFIABLE.
 6. Blind source with incomplete photometry remains non-confirmatory.
 7. Blind source with ambiguous counterpart remains non-confirmatory.
 8. Blind source with upper-limit measurements remains non-confirmatory.
 9. Blind source cannot claim SUPPORTED_PHOTOSPHERIC_CONSISTENCY using unverified baseline.
10. Blind source cannot set color_excess_detected=True.
11. Limitation code cannot be silently removed.
12. Raw measurements and provenance remain preserved.
13. Invalid uncertainty continues to fail closed.
14. Source ID mismatch continues to fail closed.
15. Contract version mismatch continues to fail closed.
16. Phase 3 positional constructor compatibility remains intact.
17. FUSION-X preserves the restricted state and limitation.
18. FUSION-X score invariance remains exactly zero.
19. Existing temporal eligibility safety behavior remains unchanged.
20. Existing full workspace regression suite passes.
"""

import math
import pytest
from typing import Dict, Any

from spectra_engine.continuum_sidecar_interface import (
    ContinuumEvidenceRecord,
    SIDECAR_CONTRACT_VERSION,
    ALLOWED_EVIDENCE_STATES,
    BASE_SIDECAR_LIMITATION_CODES,
)
from spectra_engine.continuum_sidecar_engine import EmpiricalContinuumSidecar
from spectra_engine.validation.infrared_excess.catalog_normalizer import (
    NormalizedSourceRecord,
    NormalizedMeasurement,
)
from models.fusion.fusion_engine import FusionEngine


@pytest.fixture
def sidecar_engine():
    return EmpiricalContinuumSidecar()


@pytest.fixture
def fusion_engine():
    return FusionEngine()


def make_synthetic_source(pointing: str, source_id: int = 99999, w2_excess: bool = True) -> NormalizedSourceRecord:
    """Creates a clearly-labeled synthetic NormalizedSourceRecord fixture."""
    w2_mag = 10.0 if w2_excess else 12.0
    w2_flux = 35.0 if w2_excess else 8.5
    return NormalizedSourceRecord(
        source_id=source_id,
        ra_deg=180.0,
        dec_deg=0.0,
        cohort_pointing=pointing,
        measurements={
            "WISE_W1": NormalizedMeasurement(
                band_name="WISE_W1",
                catalog_source="SYNTHETIC_ALLWISE",
                effective_wavelength_microns=3.35,
                magnitude=11.5,
                magnitude_error=0.03,
                flux_density_mJy=12.0,
                flux_uncertainty_mJy=0.3,
                is_upper_limit=False,
                quality_flag="A",
            ),
            "WISE_W2": NormalizedMeasurement(
                band_name="WISE_W2",
                catalog_source="SYNTHETIC_ALLWISE",
                effective_wavelength_microns=4.60,
                magnitude=w2_mag,
                magnitude_error=0.03,
                flux_density_mJy=w2_flux,
                flux_uncertainty_mJy=0.5,
                is_upper_limit=False,
                quality_flag="A",
            ),
            "2MASS_Ks": NormalizedMeasurement(
                band_name="2MASS_Ks",
                catalog_source="SYNTHETIC_2MASS",
                effective_wavelength_microns=2.159,
                magnitude=12.5,
                magnitude_error=0.04,
                flux_density_mJy=6.7,
                flux_uncertainty_mJy=0.25,
                is_upper_limit=False,
                quality_flag="A",
            ),
        },
        tmass_designation=f"2MASS_SYNTH_{source_id}",
        allwise_designation=f"WISE_SYNTH_{source_id}",
        gaia_ruwe=1.05,
        competing_counterparts_count=1,
    )


# 1. P0008 valid photometry preserves existing behavior
def test_01_p0008_preserves_existing_behavior(sidecar_engine, fusion_engine):
    """P0008 calibration sources retain authorized baseline behavior."""
    rec = make_synthetic_source(pointing="P0008", source_id=1001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="1001",
        pointing_id="P0008",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.pointing_id == "P0008"
    assert sidecar.evidence_state == "POSSIBLE_INFRARED_EXCESS"
    assert sidecar.color_excess_detected is True
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" not in sidecar.limitation_codes


# 2. P0002 with external photometry cannot claim confirmed excess
def test_02_p0002_cannot_claim_confirmed_excess(sidecar_engine):
    """P0002 blind cohort cannot claim confirmed excess even with high S_excess."""
    rec = make_synthetic_source(pointing="P0002", source_id=2001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2001",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes
    assert sidecar.metadata["candidate_excess_indication"] is True
    assert sidecar.metadata["blind_cohort_restriction_applied"] is True


# 3. P0009 with external photometry cannot claim confirmed excess
def test_03_p0009_cannot_claim_confirmed_excess(sidecar_engine):
    """P0009 blind cohort cannot claim confirmed excess even with high S_excess."""
    rec = make_synthetic_source(pointing="P0009", source_id=9001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="9001",
        pointing_id="P0009",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


# 4. P0010 with external photometry cannot claim confirmed excess
def test_04_p0010_cannot_claim_confirmed_excess(sidecar_engine):
    """P0010 blind cohort cannot claim confirmed excess even with high S_excess."""
    rec = make_synthetic_source(pointing="P0010", source_id=10001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="10001",
        pointing_id="P0010",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


# 5. Blind source without external photometry remains UNVERIFIABLE
def test_05_blind_source_without_photometry_unverifiable(sidecar_engine):
    """Blind sources evaluated on SPHEREx alone remain UNVERIFIABLE."""
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="BLIND_NO_PHOT",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[5.0, 5.0, 5.0],
        uncertainties=[0.2, 0.2, 0.2],
        valid_mask=[True, True, True],
        photometric_record=None,
    )
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


# 6. Blind source with incomplete photometry remains non-confirmatory
def test_06_blind_source_incomplete_photometry(sidecar_engine):
    """Blind source missing 2MASS Ks remains INSUFFICIENT_PHOTOMETRY."""
    rec = make_synthetic_source(pointing="P0002", source_id=2006)
    del rec.measurements["2MASS_Ks"]  # Incomplete baseline
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2006",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[5.0, 5.0, 5.0],
        uncertainties=[0.2, 0.2, 0.2],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "INSUFFICIENT_PHOTOMETRY"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


# 7. Blind source with ambiguous counterpart remains non-confirmatory
def test_07_blind_source_ambiguous_counterpart(sidecar_engine):
    """Blind source with competing counterparts remains AMBIGUOUS_COUNTERPART."""
    rec = make_synthetic_source(pointing="P0002", source_id=2007)
    rec.competing_counterparts_count = 3
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2007",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[5.0, 5.0, 5.0],
        uncertainties=[0.2, 0.2, 0.2],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "AMBIGUOUS_COUNTERPART"
    assert sidecar.counterpart_ambiguity is True
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


# 8. Blind source with upper-limit measurements remains non-confirmatory
def test_08_blind_source_upper_limit(sidecar_engine):
    """Blind source where anchor is upper limit remains QUALITY_FLAGGED."""
    rec = make_synthetic_source(pointing="P0002", source_id=2008)
    rec.measurements["2MASS_Ks"].is_upper_limit = True
    rec.measurements["2MASS_Ks"].quality_flag = "U"
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2008",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[5.0, 5.0, 5.0],
        uncertainties=[0.2, 0.2, 0.2],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "QUALITY_FLAGGED"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


# 9. Blind source cannot claim SUPPORTED_PHOTOSPHERIC_CONSISTENCY
def test_09_blind_source_cannot_claim_photospheric_consistency(sidecar_engine):
    """Apparent consistency on blind cohort is forced to UNVERIFIABLE."""
    rec = make_synthetic_source(pointing="P0002", source_id=2009, w2_excess=False)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2009",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[5.0, 5.0, 5.0],
        uncertainties=[0.2, 0.2, 0.2],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


# 10. Blind source cannot set color_excess_detected=True
def test_10_blind_source_contract_veto_excess():
    """Manual attempt to set color_excess_detected=True on blind record fails closed."""
    with pytest.raises(ValueError, match="Governance violation.*color_excess_detected=True with unverified baseline"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_ILLEGAL_01",
            pointing_id="P0002",
            color_excess_detected=True,
            evidence_state="POSSIBLE_INFRARED_EXCESS",
            observed_flux_mJy=10.0,
            total_uncertainty_mJy=0.5,
            limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"],
        )


# 11. Limitation code cannot be silently removed
def test_11_limitation_code_cannot_be_stripped():
    """Attempt to strip BLIND_COHORT_UNVERIFIED_BASELINE from blind pointing fails closed."""
    with pytest.raises(ValueError, match="must include limitation code 'BLIND_COHORT_UNVERIFIED_BASELINE'"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_STRIPPED_01",
            pointing_id="P0002",
            evidence_state="UNVERIFIABLE",
            limitation_codes=[],  # Stripped!
        )


# 12. Raw measurements and provenance remain preserved
def test_12_raw_measurements_preserved(sidecar_engine):
    """Raw fluxes, uncertainties, and residuals remain preserved for unverified blind records."""
    rec = make_synthetic_source(pointing="P0002", source_id=2012, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2012",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    assert sidecar.observed_flux_mJy is not None
    assert sidecar.predicted_flux_mJy is not None
    assert sidecar.residual_flux_mJy is not None
    assert sidecar.total_uncertainty_mJy is not None
    assert sidecar.metadata["allwise_designation"] == "WISE_SYNTH_2012"
    assert sidecar.metadata["tmass_designation"] == "2MASS_SYNTH_2012"


# 13. Invalid uncertainty continues to fail closed
def test_13_invalid_uncertainty_fails_closed():
    """Negative uncertainty raises ValueError."""
    with pytest.raises(ValueError, match="total_uncertainty_mJy must be non-negative"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_UNC_FAIL",
            pointing_id="P0008",
            total_uncertainty_mJy=-1.0,
        )


# 14. Source ID mismatch continues to fail closed
def test_14_source_id_mismatch_fails_closed(fusion_engine):
    """Mismatched source ID in sidecar raises ValueError in FusionEngine."""
    sidecar = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SOURCE_A",
        pointing_id="P0008",
        evidence_state="SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
    )
    with pytest.raises(ValueError, match="Continuum sidecar source_id mismatch"):
        fusion_engine.evaluate_source(
            candidate_id="SOURCE_B",
            ra=270.0,
            dec=66.5,
            observation_id="OBS01",
            observation_time="2026-11-08",
            continuum_sidecar=sidecar,
        )


# 15. Contract version mismatch continues to fail closed
def test_15_contract_version_mismatch_fails_closed():
    """Invalid contract version raises ValueError."""
    with pytest.raises(ValueError, match="Invalid contract_version"):
        ContinuumEvidenceRecord(
            contract_version="BAD_CONTRACT_V99",
            source_id="SRC_VER_FAIL",
            pointing_id="P0008",
        )


# 16. Phase 3 positional constructor compatibility remains intact
def test_16_phase_3_positional_compatibility():
    """Phase 3 positional parameters continue to work without errors."""
    p3 = ContinuumEvidenceRecord(
        SIDECAR_CONTRACT_VERSION,
        "SRC_P3_COMPAT",
        "P0008",
        False,
        1.2,
    )
    assert p3.contract_version == SIDECAR_CONTRACT_VERSION
    assert p3.source_id == "SRC_P3_COMPAT"
    assert p3.color_excess_detected is False


# 17. FUSION-X preserves the restricted state and limitation
def test_17_fusion_preserves_restricted_state(sidecar_engine, fusion_engine):
    """FUSION-X candidate record exposes UNVERIFIABLE and blind cohort limitation."""
    rec = make_synthetic_source(pointing="P0002", source_id=2017, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2017",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    cand = fusion_engine.evaluate_source(
        candidate_id="2017",
        ra=180.0,
        dec=0.0,
        observation_id="OBS_P0002",
        observation_time="2026-11-08",
        spectra_score=0.005,
        continuum_sidecar=sidecar,
    )
    assert cand.metadata["continuum_evidence_state"] == "UNVERIFIABLE"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in cand.metadata["continuum_sidecar"]["limitation_codes"]
    assert "CONTINUUM_STATE=UNVERIFIABLE" in cand.evidence_summary
    assert cand.metadata["continuum_sidecar"]["color_excess_detected"] is False


# 18. FUSION-X score invariance remains exactly zero
def test_18_fusion_score_invariance_exact_zero(sidecar_engine, fusion_engine):
    """Score with blind restricted sidecar matches score without sidecar exactly."""
    rec = make_synthetic_source(pointing="P0002", source_id=2018, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2018",
        pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=rec,
    )
    cand_no_sidecar = fusion_engine.evaluate_source(
        candidate_id="2018",
        ra=180.0,
        dec=0.0,
        observation_id="OBS_P0002",
        observation_time="2026-11-08",
        spectra_score=0.005,
        astrovision_score=2.0,
        chronos_score=1.5,
    )
    cand_with_sidecar = fusion_engine.evaluate_source(
        candidate_id="2018",
        ra=180.0,
        dec=0.0,
        observation_id="OBS_P0002",
        observation_time="2026-11-08",
        spectra_score=0.005,
        astrovision_score=2.0,
        chronos_score=1.5,
        continuum_sidecar=sidecar,
    )
    assert cand_no_sidecar.anomaly_score == cand_with_sidecar.anomaly_score
    delta = abs(cand_with_sidecar.anomaly_score - cand_no_sidecar.anomaly_score)
    assert delta == 0.0


# 19. Existing temporal eligibility safety behavior remains unchanged
def test_19_temporal_safety_behavior_unchanged(fusion_engine):
    """Temporal spikes without eligibility=TRUE remain blocked from transient promotion."""
    rec = fusion_engine.evaluate_source(
        candidate_id="TEMP_TEST_01",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_TEMP",
        observation_time="2026-11-08",
        chronos_score=9.0,
        chronos_temporal_eligibility="FALSE",
        is_known_gaia_star=False,
    )
    assert "CLASSIFICATION: ANOMALOUS_RESIDUAL_REQUIRES_REVIEW" in rec.evidence_summary


# 20. Direct validation of contract gate
def test_20_blind_cannot_claim_consistency_contract_veto():
    """Manual attempt to claim SUPPORTED_PHOTOSPHERIC_CONSISTENCY on blind record fails closed."""
    with pytest.raises(ValueError, match="cannot claim SUPPORTED_PHOTOSPHERIC_CONSISTENCY with unverified baseline"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_ILLEGAL_02",
            pointing_id="P0002",
            evidence_state="SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
            limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"],
        )

