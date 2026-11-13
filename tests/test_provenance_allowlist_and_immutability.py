"""
SPECTRA-X / F1 — Phase 4, Task 4.10
Targeted Calibration Provenance Allowlist & Immutability Contract Safety Test Suite

Validates the remediation of FIND-4.9-01 and FIND-4.9-02 across all 26 requirements:
Calibration Identity:
 1. Trusted canonical P0008 retains authorized behavior.
 2. P0002 fails closed.
 3. P0009 fails closed.
 4. P0010 fails closed.
 5. P9999 fails closed (remediates FIND-4.9-01).
 6. Missing pointing ID fails closed.
 7. Empty pointing ID fails closed.
 8. Malformed pointing ID fails closed.
 9. Conflicting pointing and cohort metadata fails closed.
10. Caller-supplied calibration metadata cannot authorize calibration.
11. Unknown cohort fails closed.
12. Untrusted legacy alias cannot authorize P0008.

Immutability:
13. Direct mutation of color_excess_detected is rejected (remediates FIND-4.9-02).
14. Direct mutation of evidence_state is rejected.
15. Limitation-code mutation is rejected.
16. Nested metadata mutation is rejected or cannot affect internal state.
17. Serialization output mutation cannot alter the original record.
18. Reconstructed records undergo full validation.
19. Mutation attempts after validation cannot bypass ingestion safeguards.
20. Existing Phase 3 positional constructors still work.

Integration and Regression:
21. FUSION-X receives restricted blind evidence correctly.
22. Unknown provenance cannot be promoted downstream.
23. FUSION-X score invariance remains exactly zero.
24. Candidate-level indications remain non-confirmatory.
25. Existing temporal safety behavior is unchanged.
26. All existing Task 4.8R safety tests pass.
"""

import math
import copy
import pytest
from dataclasses import FrozenInstanceError

from spectra_engine.continuum_sidecar_interface import (
    ContinuumEvidenceRecord,
    SIDECAR_CONTRACT_VERSION,
    ALLOWED_EVIDENCE_STATES,
    BASE_SIDECAR_LIMITATION_CODES,
    CANONICAL_CALIBRATION_POINTING,
    normalize_pointing_id,
    is_trusted_calibration_provenance,
    ReadOnlyList,
    ReadOnlyDict,
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


# ==============================================================================
# CALIBRATION IDENTITY TESTS (1-12)
# ==============================================================================

def test_01_trusted_canonical_p0008_retains_authorized_behavior(sidecar_engine):
    """1. Trusted canonical P0008 retains authorized calibration behavior."""
    rec = make_synthetic_source(pointing="P0008", source_id=1001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="1001", pointing_id="P0008",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.pointing_id == "P0008"
    assert sidecar.evidence_state == "POSSIBLE_INFRARED_EXCESS"
    assert sidecar.color_excess_detected is True
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" not in sidecar.limitation_codes


def test_02_p0002_fails_closed(sidecar_engine):
    """2. P0002 fails closed: UNVERIFIABLE, color_excess_detected=False, manual excess raises ValueError."""
    rec = make_synthetic_source(pointing="P0002", source_id=2001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2001", pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes

    with pytest.raises(ValueError, match="Governance violation: Non-calibration pointing"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="2001", pointing_id="P0002",
            color_excess_detected=True, evidence_state="POSSIBLE_INFRARED_EXCESS",
            observed_flux_mJy=35.0, total_uncertainty_mJy=0.5,
            limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"]
        )


def test_03_p0009_fails_closed(sidecar_engine):
    """3. P0009 fails closed."""
    rec = make_synthetic_source(pointing="P0009", source_id=9001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="9001", pointing_id="P0009",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


def test_04_p0010_fails_closed(sidecar_engine):
    """4. P0010 fails closed."""
    rec = make_synthetic_source(pointing="P0010", source_id=10001, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="10001", pointing_id="P0010",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


def test_05_p9999_fails_closed(sidecar_engine):
    """5. P9999 unknown pointing fails closed (remediates FIND-4.9-01)."""
    rec = make_synthetic_source(pointing="P9999", source_id=99991, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="99991", pointing_id="P9999",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes

    with pytest.raises(ValueError, match="Governance violation: Non-calibration pointing 'P9999'"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="99991", pointing_id="P9999",
            color_excess_detected=True, evidence_state="POSSIBLE_INFRARED_EXCESS",
            observed_flux_mJy=35.0, total_uncertainty_mJy=0.5,
            limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"]
        )


def test_06_missing_pointing_id_fails_closed(sidecar_engine):
    """6. Missing pointing ID fails closed."""
    with pytest.raises(ValueError, match="Invalid pointing_id"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_MISSING_PT", pointing_id=None,
        )
    with pytest.raises(ValueError, match="Invalid pointing_id"):
        sidecar_engine.evaluate_continuum(
            source_id="SRC_MISSING_PT", pointing_id=None,
            wavelengths=[4.4], fluxes=[10.0],
            uncertainties=[0.5], valid_mask=[True]
        )


def test_07_empty_pointing_id_fails_closed(sidecar_engine):
    """7. Empty pointing ID fails closed."""
    with pytest.raises(ValueError, match="Invalid pointing_id"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_EMPTY_PT", pointing_id="",
        )
    with pytest.raises(ValueError, match="Invalid pointing_id"):
        sidecar_engine.evaluate_continuum(
            source_id="SRC_EMPTY_PT", pointing_id="",
            wavelengths=[4.4], fluxes=[10.0],
            uncertainties=[0.5], valid_mask=[True]
        )


def test_08_malformed_pointing_id_fails_closed(sidecar_engine):
    """8. Malformed pointing ID fails closed."""
    with pytest.raises(ValueError, match="Invalid pointing_id"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_MALFORMED_PT", pointing_id=12345,
        )
    with pytest.raises(ValueError, match="Invalid pointing_id"):
        sidecar_engine.evaluate_continuum(
            source_id="SRC_MALFORMED_PT", pointing_id=12345,
            wavelengths=[4.4], fluxes=[10.0],
            uncertainties=[0.5], valid_mask=[True]
        )


def test_09_conflicting_pointing_cohort_metadata_fails_closed(sidecar_engine):
    """9. Conflicting pointing and cohort metadata fails closed."""
    rec = make_synthetic_source(pointing="P0008", source_id=1009, w2_excess=True)
    # Inject conflicting cohort metadata into photometric record
    rec.metadata = {"cohort": "P0002", "role": "blind"}

    sidecar = sidecar_engine.evaluate_continuum(
        source_id="1009", pointing_id="P0008",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes

    # Manual conflicting record with color_excess=True raises ValueError
    with pytest.raises(ValueError, match="Governance violation: Non-calibration pointing"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="1009", pointing_id="P0008",
            color_excess_detected=True, evidence_state="POSSIBLE_INFRARED_EXCESS",
            observed_flux_mJy=35.0, total_uncertainty_mJy=0.5,
            metadata={"cohort": "P0002"}
        )


def test_10_caller_supplied_calibration_metadata_cannot_authorize(sidecar_engine):
    """10. Caller-supplied calibration metadata cannot authorize calibration for non-P0008 pointing."""
    rec = make_synthetic_source(pointing="P0002", source_id=2010, w2_excess=True)
    rec.metadata = {"cohort": "P0008", "role": "CALIBRATION", "calibration_eligible": True}

    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2010", pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


def test_11_unknown_cohort_fails_closed(sidecar_engine):
    """11. Unknown cohort fails closed."""
    rec = make_synthetic_source(pointing="UNKNOWN_FIELD", source_id=99011, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="99011", pointing_id="UNKNOWN_FIELD",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.evidence_state == "UNVERIFIABLE"
    assert sidecar.color_excess_detected is False
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in sidecar.limitation_codes


def test_12_untrusted_legacy_alias_cannot_authorize_p0008():
    """12. Untrusted legacy alias cannot authorize P0008."""
    # Untrusted provenance marker blocks calibration eligibility
    assert is_trusted_calibration_provenance("8", metadata={"untrusted": True}) is False
    assert is_trusted_calibration_provenance("8", metadata={"trusted_provenance": False}) is False
    assert is_trusted_calibration_provenance("8", metadata={"cohort": "P0002"}) is False

    with pytest.raises(ValueError, match="Governance violation: Non-calibration pointing"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_UNTRUSTED", pointing_id="8",
            color_excess_detected=True, evidence_state="POSSIBLE_INFRARED_EXCESS",
            observed_flux_mJy=35.0, total_uncertainty_mJy=0.5,
            metadata={"untrusted": True}
        )


# ==============================================================================
# IMMUTABILITY TESTS (13-20)
# ==============================================================================

def test_13_direct_mutation_color_excess_detected_rejected():
    """13. Direct mutation of color_excess_detected is rejected (remediates FIND-4.9-02)."""
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_MUT_01", pointing_id="P0008",
        color_excess_detected=False
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        rec.color_excess_detected = True  # type: ignore


def test_14_direct_mutation_evidence_state_rejected():
    """14. Direct mutation of evidence_state is rejected."""
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_MUT_02", pointing_id="P0008",
        evidence_state="UNVERIFIABLE",
        limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"]
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        rec.evidence_state = "POSSIBLE_INFRARED_EXCESS"  # type: ignore


def test_15_limitation_code_mutation_rejected():
    """15. Limitation-code mutation is rejected."""
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_MUT_03", pointing_id="P0002",
        evidence_state="UNVERIFIABLE",
        limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"]
    )
    with pytest.raises(TypeError, match="ReadOnlyList"):
        rec.limitation_codes.clear()
    with pytest.raises(TypeError, match="ReadOnlyList"):
        rec.limitation_codes.remove("BLIND_COHORT_UNVERIFIED_BASELINE")
    with pytest.raises(TypeError, match="ReadOnlyList"):
        rec.limitation_codes.append("NEW_CODE")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        rec.limitation_codes = []  # type: ignore


def test_16_nested_metadata_mutation_rejected():
    """16. Nested metadata mutation is rejected or cannot affect internal state."""
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_MUT_04", pointing_id="P0008",
        metadata={"nested_dict": {"auth": True}, "nested_list": [1, 2, 3]}
    )
    with pytest.raises(TypeError, match="ReadOnlyDict"):
        rec.metadata["candidate_excess_indication"] = True
    with pytest.raises(TypeError, match="ReadOnlyDict"):
        rec.metadata["nested_dict"]["auth"] = False
    with pytest.raises(TypeError, match="ReadOnlyList"):
        rec.metadata["nested_list"].append(4)


def test_17_serialization_output_mutation_cannot_alter_original():
    """17. Serialization output mutation cannot alter the original record."""
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_SERIAL_01", pointing_id="P0002",
        color_excess_detected=False,
        evidence_state="UNVERIFIABLE",
        limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"],
        metadata={"flag": False}
    )
    d = rec.to_dict()
    d["color_excess_detected"] = True
    d["limitation_codes"].clear()
    d["metadata"]["flag"] = True

    assert rec.color_excess_detected is False
    assert len(rec.limitation_codes) == 1
    assert rec.metadata["flag"] is False


def test_18_reconstructed_records_undergo_full_validation():
    """18. Reconstructed records undergo full validation upon instantiation."""
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_RECON_01", pointing_id="P0002",
        color_excess_detected=False,
        evidence_state="UNVERIFIABLE",
        limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"]
    )
    d = rec.to_dict()
    d["color_excess_detected"] = True  # Tamper with serialized dict

    with pytest.raises(ValueError, match="Governance violation"):
        ContinuumEvidenceRecord(**d)


def test_19_mutation_attempts_after_validation_cannot_bypass_ingestion(fusion_engine):
    """19. Mutation attempts after validation cannot bypass ingestion safeguards."""
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_BYPASS_01", pointing_id="P0002",
        color_excess_detected=False,
        evidence_state="UNVERIFIABLE",
        limitation_codes=["BLIND_COHORT_UNVERIFIED_BASELINE"]
    )
    # Direct field mutation raises FrozenInstanceError
    with pytest.raises((FrozenInstanceError, AttributeError)):
        rec.color_excess_detected = True  # type: ignore

    # Pass to FusionEngine
    cand = fusion_engine.evaluate_source(
        candidate_id="SRC_BYPASS_01",
        ra=180.0, dec=0.0,
        observation_id="OBS_BYPASS", observation_time="2026-11-08",
        spectra_score=40.0,
        continuum_sidecar=rec
    )
    assert cand.metadata["continuum_sidecar"]["color_excess_detected"] is False
    assert cand.metadata["continuum_evidence_state"] == "UNVERIFIABLE"


def test_20_existing_phase_3_positional_constructors_work():
    """20. Existing Phase 3 positional constructors still work."""
    p3 = ContinuumEvidenceRecord(
        SIDECAR_CONTRACT_VERSION,
        "SRC_P3_COMPAT",
        "P0008",
        False,
        1.2,
    )
    assert p3.contract_version == SIDECAR_CONTRACT_VERSION
    assert p3.source_id == "SRC_P3_COMPAT"
    assert p3.pointing_id == "P0008"
    assert p3.color_excess_detected is False
    assert p3.continuum_anomaly_score == 1.2


# ==============================================================================
# INTEGRATION AND REGRESSION TESTS (21-26)
# ==============================================================================

def test_21_fusion_receives_restricted_blind_evidence_correctly(sidecar_engine, fusion_engine):
    """21. FUSION-X receives restricted blind evidence correctly."""
    rec = make_synthetic_source(pointing="P0002", source_id=2021, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2021", pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    cand = fusion_engine.evaluate_source(
        candidate_id="2021", ra=180.0, dec=0.0,
        observation_id="OBS_2021", observation_time="2026-11-08",
        spectra_score=45.0, continuum_sidecar=sidecar
    )
    assert cand.metadata["continuum_evidence_state"] == "UNVERIFIABLE"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in cand.metadata["continuum_sidecar"]["limitation_codes"]
    assert cand.metadata["continuum_sidecar"]["color_excess_detected"] is False
    assert "CONTINUUM_STATE=UNVERIFIABLE" in cand.evidence_summary


def test_22_unknown_provenance_cannot_be_promoted_downstream(sidecar_engine, fusion_engine):
    """22. Unknown provenance cannot be promoted downstream (remediates FIND-4.9-01)."""
    rec = make_synthetic_source(pointing="P9999", source_id=99922, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="99922", pointing_id="P9999",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    cand = fusion_engine.evaluate_source(
        candidate_id="99922", ra=180.0, dec=0.0,
        observation_id="OBS_99922", observation_time="2026-11-08",
        spectra_score=45.0, continuum_sidecar=sidecar
    )
    assert cand.metadata["continuum_evidence_state"] == "UNVERIFIABLE"
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in cand.metadata["continuum_sidecar"]["limitation_codes"]
    assert cand.metadata["continuum_sidecar"]["color_excess_detected"] is False
    assert "CONTINUUM_STATE=UNVERIFIABLE" in cand.evidence_summary


def test_23_fusion_score_invariance_remains_exactly_zero(sidecar_engine, fusion_engine):
    """23. FUSION-X score invariance remains exactly zero across all cohorts."""
    for pt in ["P0008", "P0002", "P0009", "P0010", "P9999"]:
        rec = make_synthetic_source(pointing=pt, source_id=2300, w2_excess=True)
        sidecar = sidecar_engine.evaluate_continuum(
            source_id="2300", pointing_id=pt,
            wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
            uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
            photometric_record=rec
        )
        cand_with = fusion_engine.evaluate_source(
            candidate_id="2300", ra=180.0, dec=0.0,
            observation_id="OBS_INV", observation_time="2026-11-08",
            spectra_score=45.0, continuum_sidecar=sidecar
        )
        cand_without = fusion_engine.evaluate_source(
            candidate_id="2300", ra=180.0, dec=0.0,
            observation_id="OBS_INV", observation_time="2026-11-08",
            spectra_score=45.0, continuum_sidecar=None
        )
        score_delta = abs(cand_with.anomaly_score - cand_without.anomaly_score)
        assert score_delta == 0.0
        assert cand_with.validity_status == cand_without.validity_status


def test_24_candidate_level_indications_remain_non_confirmatory(sidecar_engine, fusion_engine):
    """24. Candidate-level indications remain strictly non-confirmatory."""
    rec = make_synthetic_source(pointing="P0002", source_id=2400, w2_excess=True)
    sidecar = sidecar_engine.evaluate_continuum(
        source_id="2400", pointing_id="P0002",
        wavelengths=[4.4, 4.5, 4.6], fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5], valid_mask=[True, True, True],
        photometric_record=rec
    )
    assert sidecar.metadata.get("candidate_excess_indication") is True
    assert sidecar.color_excess_detected is False
    assert sidecar.evidence_state == "UNVERIFIABLE"

    cand = fusion_engine.evaluate_source(
        candidate_id="2400", ra=180.0, dec=0.0,
        observation_id="OBS_2400", observation_time="2026-11-08",
        spectra_score=42.0, continuum_sidecar=sidecar
    )
    # Verification that candidate-level indication did not alter fused score
    cand_no_indication = fusion_engine.evaluate_source(
        candidate_id="2400", ra=180.0, dec=0.0,
        observation_id="OBS_2400", observation_time="2026-11-08",
        spectra_score=42.0, continuum_sidecar=None
    )
    assert cand.anomaly_score == cand_no_indication.anomaly_score


def test_25_existing_temporal_safety_behavior_unchanged(fusion_engine):
    """25. Existing temporal safety behavior is unchanged."""
    cand = fusion_engine.evaluate_source(
        candidate_id="SRC_TEMP_01",
        ra=180.0, dec=0.0,
        observation_id="OBS_TEMP", observation_time="2026-11-08",
        spectra_score=0.005,
        chronos_is_dipole=True
    )
    assert cand.validity_status == "REJECTED"
    assert "CHRONOS_DIPOLE_SUBTRACTION_ARTIFACT" in cand.metadata["rejection_reasons"]


def test_26_all_existing_task_4_8r_safety_tests_pass():
    """26. All existing Task 4.8R safety tests pass without modification."""
    import subprocess
    import sys
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_blind_cohort_promotion_safety.py"],
        capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "20 passed" in res.stdout
