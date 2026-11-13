"""
Scientific Evidence Classifier for Infrared Anomaly Validation.

Enforces strict, multi-dimensional classification of external photometric evidence
without conflating non-detections with physical consistency or single-band deviations
with confirmed astrophysical excess.
"""

from typing import Dict, Any, Optional
from spectra_engine.validation.infrared_excess.catalog_normalizer import NormalizedSourceRecord
from spectra_engine.validation.infrared_excess.excess_engine import ExcessBandResult


class InfraredEvidenceClassifier:
    """
    Assigns one of six authoritative evidence states:
    - SUPPORTED_PHOTOSPHERIC_CONSISTENCY
    - POSSIBLE_INFRARED_EXCESS
    - QUALITY_FLAGGED
    - AMBIGUOUS_COUNTERPART
    - INSUFFICIENT_PHOTOMETRY
    - UNVERIFIABLE
    """

    STATES = {
        "SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
        "POSSIBLE_INFRARED_EXCESS",
        "QUALITY_FLAGGED",
        "AMBIGUOUS_COUNTERPART",
        "INSUFFICIENT_PHOTOMETRY",
        "UNVERIFIABLE"
    }

    @classmethod
    def classify_source(
        cls,
        record: NormalizedSourceRecord,
        w1_result: ExcessBandResult,
        w2_result: ExcessBandResult
    ) -> tuple[str, str]:
        """
        Classifies an observed source into one primary evidence state.
        Returns: (evidence_state, explanation_summary)
        """
        # Rule 1: Counterpart Ambiguity
        if record.competing_counterparts_count > 1:
            return (
                "AMBIGUOUS_COUNTERPART",
                f"Multiple competing counterparts ({record.competing_counterparts_count}) detected within matching beam."
            )

        # Rule 2: Insufficient Photometric Baseline
        has_2mass = ("2MASS_Ks" in record.measurements)
        has_w1 = ("WISE_W1" in record.measurements) or ("CatWISE_W1" in record.measurements)
        has_w2 = ("WISE_W2" in record.measurements) or ("CatWISE_W2" in record.measurements)

        if not has_2mass and not has_w1 and not has_w2:
            return (
                "INSUFFICIENT_PHOTOMETRY",
                "Source below detection thresholds in both near-IR (2MASS) and mid-IR (ALLWISE/CatWISE)."
            )
        if not has_2mass:
            return (
                "INSUFFICIENT_PHOTOMETRY",
                "Near-IR anchor (2MASS Ks) absent; cannot establish empirical photospheric baseline."
            )
        if not has_w1 and not has_w2:
            return (
                "INSUFFICIENT_PHOTOMETRY",
                "Mid-IR measurements (ALLWISE/CatWISE W1/W2) absent; cannot evaluate excess."
            )

        # Rule 3: Quality Flags & Upper Limits
        ks_meas = record.measurements["2MASS_Ks"]
        if ks_meas.is_upper_limit or (ks_meas.quality_flag and ks_meas.quality_flag[-1] in ["U", "D", "X"]):
            return (
                "QUALITY_FLAGGED",
                f"2MASS Ks-band anchor is an upper limit or low-quality detection (ph_qual={ks_meas.quality_flag})."
            )

        w1_meas = record.measurements.get("WISE_W1", record.measurements.get("CatWISE_W1"))
        w2_meas = record.measurements.get("WISE_W2", record.measurements.get("CatWISE_W2"))

        if w1_meas and w1_meas.is_upper_limit and w2_meas and w2_meas.is_upper_limit:
            return (
                "QUALITY_FLAGGED",
                "Both mid-IR W1 and W2 are photometric upper limits; no physical detection in mid-IR."
            )

        # Check ALLWISE confusion / contamination flags
        for b_meas in [w1_meas, w2_meas]:
            if b_meas and b_meas.quality_flag:
                # Contamination flag != '0' (e.g. D, H, P, O) indicates diffraction spike, halo, or artifact
                q = b_meas.quality_flag
                if q not in ["0", "0000", ""] and any(c not in ["0", "U", "A", "B", "C"] for c in q):
                    return (
                        "QUALITY_FLAGGED",
                        f"ALLWISE contamination/confusion flags detected ({q}); photometry may be biased by artifacts."
                    )

        # Rule 4: Excess Significance Evaluation
        # Primary excess band is W2 (4.6 um), secondary is W1 (3.35 um)
        sig_w2 = w2_result.excess_significance_sigma if w2_result.is_evaluable else None
        sig_w1 = w1_result.excess_significance_sigma if w1_result.is_evaluable else None

        # Check for statistically significant excess (>= +3.0 sigma in W2 or both W1 & W2 >= +2.5 sigma)
        is_excess = False
        excess_notes = []

        if sig_w2 is not None and sig_w2 >= 3.0:
            is_excess = True
            excess_notes.append(f"Statistically significant excess in W2: S_excess = +{sig_w2:.2f} sigma (flux ratio = {w2_result.flux_ratio_obs_to_phot:.2f}).")
        elif sig_w1 is not None and sig_w2 is not None and sig_w1 >= 2.5 and sig_w2 >= 2.5:
            is_excess = True
            excess_notes.append(f"Statistically significant coherent excess in W1 (+{sig_w1:.2f} sigma) and W2 (+{sig_w2:.2f} sigma).")

        if is_excess:
            return (
                "POSSIBLE_INFRARED_EXCESS",
                " ".join(excess_notes)
            )

        # Rule 5: Supported Photospheric Consistency
        # Both or at least one mid-IR band is consistent with predicted photospheric baseline within +/- 3 sigma
        if (sig_w2 is not None and -3.0 <= sig_w2 < 3.0) or (sig_w1 is not None and -3.0 <= sig_w1 < 3.0):
            w1_sig_str = f"+{sig_w1:.2f}" if (sig_w1 is not None and sig_w1 >= 0) else (f"{sig_w1:.2f}" if sig_w1 is not None else "N/A")
            w2_sig_str = f"+{sig_w2:.2f}" if (sig_w2 is not None and sig_w2 >= 0) else (f"{sig_w2:.2f}" if sig_w2 is not None else "N/A")
            ratio_str = f"{w2_result.flux_ratio_obs_to_phot:.2f}" if w2_result.flux_ratio_obs_to_phot else "N/A"
            return (
                "SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
                f"Observed infrared fluxes match bare stellar photospheric prediction (S_W1={w1_sig_str} sigma, S_W2={w2_sig_str} sigma, W2 flux ratio={ratio_str})."
            )

        return (
            "UNVERIFIABLE",
            "Photometric measurements present but insufficient constraints to establish physical consistency or excess."
        )

