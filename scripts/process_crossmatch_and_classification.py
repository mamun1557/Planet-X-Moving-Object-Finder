"""
SPECTRA-X / F1 — Phase 2, Task 4
Cross-Matching & Probabilistic Source Classification Pipeline

Matches 1,132 Pointing 0003 SPHEREx sources with simultaneous D1+D4 coverage against:
- Gaia DR3 (with proper-motion propagation to SPHEREx epoch 2026.5496)
- AllWISE (W1, W2 infrared photometry, quality & confusion flags)

Produces all required machine-readable outputs:
1. data/processed/crossmatch/pointing_0003_gaia_dr3_matches.csv
2. data/processed/crossmatch/pointing_0003_allwise_matches.csv
3. data/processed/crossmatch/pointing_0003_crossmatch_summary.csv
4. data/processed/classification/pointing_0003_classification_features.csv
5. data/processed/classification/pointing_0003_source_classifications.csv
"""

import os
import sys
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, BASE_DIR)

SPHEREx_EPOCH = 2026.5496  # Observation date: 2026-07-20T00:26:21 UTC (MJD 61241.018)
GAIA_EPOCH = 2016.0        # Gaia DR3 reference epoch J2016.0
DT_GAIA_SPHEREX = SPHEREx_EPOCH - GAIA_EPOCH  # 10.5496 years

SPX_SCORES_PATH = os.path.join(BASE_DIR, "data", "processed", "benchmarks", "spectra_v2_source_scores.csv")
GAIA_CAND_PATH = os.path.join(BASE_DIR, "data", "external", "gaia_dr3", "pointing_0003_gaia_dr3_candidates.csv")
WISE_CAND_PATH = os.path.join(BASE_DIR, "data", "external", "allwise", "pointing_0003_allwise_candidates.csv")

OUT_GAIA_MATCHES = os.path.join(BASE_DIR, "data", "processed", "crossmatch", "pointing_0003_gaia_dr3_matches.csv")
OUT_WISE_MATCHES = os.path.join(BASE_DIR, "data", "processed", "crossmatch", "pointing_0003_allwise_matches.csv")
OUT_SUMMARY = os.path.join(BASE_DIR, "data", "processed", "crossmatch", "pointing_0003_crossmatch_summary.csv")
OUT_FEATURES = os.path.join(BASE_DIR, "data", "processed", "classification", "pointing_0003_classification_features.csv")
OUT_CLASSIFICATIONS = os.path.join(BASE_DIR, "data", "processed", "classification", "pointing_0003_source_classifications.csv")


def angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Computes exact spherical angular separation in arcseconds using Haversine formula."""
    r1, d1, r2, d2 = map(math.radians, [ra1, dec1, ra2, dec2])
    d_ra = r2 - r1
    d_dec = d2 - d1
    a = math.sin(d_dec / 2.0) ** 2 + math.cos(d1) * math.cos(d2) * math.sin(d_ra / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    dist_rad = 2.0 * math.asin(math.sqrt(a))
    return math.degrees(dist_rad) * 3600.0


def propagate_gaia_coords(
    ra_deg: float,
    dec_deg: float,
    pmra_mas_yr: Optional[float],
    pmdec_mas_yr: Optional[float],
    dt_years: float = DT_GAIA_SPHEREX
) -> Tuple[float, float, bool]:
    """
    Propagates Gaia DR3 coordinates from J2016.0 to SPHEREx epoch using proper motion.
    pmra is pmra* = pmra * cos(dec) in mas/yr.
    """
    if pmra_mas_yr is None or pmdec_mas_yr is None or np.isnan(pmra_mas_yr) or np.isnan(pmdec_mas_yr):
        return ra_deg, dec_deg, False

    cos_dec = math.cos(math.radians(dec_deg))
    if abs(cos_dec) < 1e-6:
        return ra_deg, dec_deg, False

    delta_ra_deg = (pmra_mas_yr * 1e-3 * dt_years) / (3600.0 * cos_dec)
    delta_dec_deg = (pmdec_mas_yr * 1e-3 * dt_years) / 3600.0

    ra_prop = (ra_deg + delta_ra_deg) % 360.0
    dec_prop = dec_deg + delta_dec_deg
    return ra_prop, dec_prop, True


def run_crossmatching():
    print("=" * 80)
    print("SPECTRA-X / F1 — Phase 2, Task 4: Cross-Matching & Source Classification")
    print("=" * 80)

    # 1. Load inputs
    spx_df = pd.read_csv(SPX_SCORES_PATH)
    gaia_cand = pd.read_csv(GAIA_CAND_PATH)
    wise_cand = pd.read_csv(WISE_CAND_PATH)

    print(f"Loaded {len(spx_df)} SPHEREx matched sources.")
    print(f"Loaded {len(gaia_cand)} Gaia DR3 candidates.")
    print(f"Loaded {len(wise_cand)} AllWISE candidates.")

    # 2. Cross-match against Gaia DR3
    print("\nExecuting Gaia DR3 cross-matching with proper-motion propagation...")
    gaia_match_records = []

    for idx, s_row in spx_df.iterrows():
        s_id = s_row["source_id"]
        s_ra = s_row["ra"]
        s_dec = s_row["dec"]

        # Fast pre-filtering box (radius 6 arcsec in deg)
        box_r = 6.0 / 3600.0
        box_ra = box_r / 0.35
        sub = gaia_cand[
            (gaia_cand["ra"] >= s_ra - box_ra) & (gaia_cand["ra"] <= s_ra + box_ra) &
            (gaia_cand["dec"] >= s_dec - box_r) & (gaia_cand["dec"] <= s_dec + box_r)
        ].copy()

        candidates = []
        for _, g_row in sub.iterrows():
            g_ra_orig = g_row["ra"]
            g_dec_orig = g_row["dec"]
            pmra = g_row["pmra"]
            pmdec = g_row["pmdec"]

            g_ra_prop, g_dec_prop, pm_used = propagate_gaia_coords(g_ra_orig, g_dec_orig, pmra, pmdec)

            d_orig = angular_separation_arcsec(s_ra, s_dec, g_ra_orig, g_dec_orig)
            d_prop = angular_separation_arcsec(s_ra, s_dec, g_ra_prop, g_dec_prop)

            if d_prop <= 4.0 or d_orig <= 4.0:
                candidates.append({
                    "g_row": g_row,
                    "d_orig": d_orig,
                    "d_prop": d_prop,
                    "pm_used": pm_used,
                    "g_ra_prop": g_ra_prop,
                    "g_dec_prop": g_dec_prop
                })

        candidates.sort(key=lambda x: x["d_prop"])
        n_cands = len(candidates)

        if n_cands == 0:
            gaia_match_records.append({
                "source_id": s_id,
                "spx_ra": s_ra,
                "spx_dec": s_dec,
                "gaia_source_id": None,
                "gaia_ra_orig": None,
                "gaia_dec_orig": None,
                "gaia_ra_prop": None,
                "gaia_dec_prop": None,
                "pm_propagated": False,
                "sep_orig_arcsec": None,
                "sep_prop_arcsec": None,
                "ra_error_mas": None,
                "dec_error_mas": None,
                "pmra_mas_yr": None,
                "pmdec_mas_yr": None,
                "pmra_error_mas_yr": None,
                "pmdec_error_mas_yr": None,
                "total_pm_mas_yr": None,
                "pm_significance": None,
                "parallax_mas": None,
                "parallax_error_mas": None,
                "parallax_over_error": None,
                "phot_g_mean_mag": None,
                "phot_bp_mean_mag": None,
                "phot_rp_mean_mag": None,
                "bp_rp": None,
                "ruwe": None,
                "num_candidates_in_radius": 0,
                "competing_candidate_id": None,
                "competing_sep_arcsec": None,
                "match_category": "UNMATCHED",
                "match_notes": "No Gaia DR3 source detected within 4.0 arcsec"
            })
        else:
            best = candidates[0]
            g = best["g_row"]
            d1 = best["d_prop"]
            competing_id = candidates[1]["g_row"]["source_id"] if n_cands > 1 else None
            competing_sep = candidates[1]["d_prop"] if n_cands > 1 else None

            ruwe = g["ruwe"] if not np.isnan(g["ruwe"]) else 1.0
            pmra = g["pmra"] if not np.isnan(g["pmra"]) else 0.0
            pmdec = g["pmdec"] if not np.isnan(g["pmdec"]) else 0.0
            pm_err_ra = g["pmra_error"] if not np.isnan(g["pmra_error"]) else 1.0
            pm_err_dec = g["pmdec_error"] if not np.isnan(g["pmdec_error"]) else 1.0
            tot_pm = math.sqrt(pmra**2 + pmdec**2)
            tot_pm_err = math.sqrt(pm_err_ra**2 + pm_err_dec**2)
            pm_sig = tot_pm / tot_pm_err if tot_pm_err > 0 else 0.0

            # Match category determination
            if n_cands > 1 and competing_sep <= 2.0 and (competing_sep - d1) < 0.6:
                cat = "AMBIGUOUS"
                notes = f"Multiple competing Gaia sources within beam: d1={d1:.2f}as, d2={competing_sep:.2f}as"
            elif d1 <= 0.5:
                if ruwe > 2.0:
                    cat = "QUALITY_REJECTED"
                    notes = f"Astrometric disturbance: RUWE={ruwe:.2f} > 2.0"
                else:
                    cat = "HIGH_CONFIDENCE"
                    notes = f"Astrometrically clean match at sep={d1:.2f}as, RUWE={ruwe:.2f}"
            elif d1 <= 1.5:
                if ruwe > 2.0:
                    cat = "QUALITY_REJECTED"
                    notes = f"Astrometric disturbance at sep={d1:.2f}as, RUWE={ruwe:.2f}"
                else:
                    cat = "PROBABLE"
                    notes = f"Probable match at sep={d1:.2f}as within beam"
            else:
                if ruwe <= 1.4 and (competing_sep is None or competing_sep > 3.0):
                    cat = "PROBABLE"
                    notes = f"Isolated wide candidate at sep={d1:.2f}as"
                else:
                    cat = "AMBIGUOUS"
                    notes = f"Wide candidate with potential confusion: d1={d1:.2f}as"

            gaia_match_records.append({
                "source_id": s_id,
                "spx_ra": s_ra,
                "spx_dec": s_dec,
                "gaia_source_id": int(g["source_id"]),
                "gaia_ra_orig": g["ra"],
                "gaia_dec_orig": g["dec"],
                "gaia_ra_prop": best["g_ra_prop"],
                "gaia_dec_prop": best["g_dec_prop"],
                "pm_propagated": best["pm_used"],
                "sep_orig_arcsec": best["d_orig"],
                "sep_prop_arcsec": d1,
                "ra_error_mas": g["ra_error"],
                "dec_error_mas": g["dec_error"],
                "pmra_mas_yr": g["pmra"],
                "pmdec_mas_yr": g["pmdec"],
                "pmra_error_mas_yr": g["pmra_error"],
                "pmdec_error_mas_yr": g["pmdec_error"],
                "total_pm_mas_yr": tot_pm,
                "pm_significance": pm_sig,
                "parallax_mas": g["parallax"],
                "parallax_error_mas": g["parallax_error"],
                "parallax_over_error": g["parallax_over_error"],
                "phot_g_mean_mag": g["phot_g_mean_mag"],
                "phot_bp_mean_mag": g["phot_bp_mean_mag"],
                "phot_rp_mean_mag": g["phot_rp_mean_mag"],
                "bp_rp": g["bp_rp"],
                "ruwe": g["ruwe"],
                "num_candidates_in_radius": n_cands,
                "competing_candidate_id": int(competing_id) if competing_id is not None else None,
                "competing_sep_arcsec": competing_sep,
                "match_category": cat,
                "match_notes": notes
            })

    gaia_match_df = pd.DataFrame(gaia_match_records)
    gaia_match_df.to_csv(OUT_GAIA_MATCHES, index=False)
    print(f"Saved Gaia DR3 matches -> {OUT_GAIA_MATCHES}")

    # 3. Cross-match against AllWISE
    print("\nExecuting AllWISE cross-matching...")
    wise_match_records = []

    for idx, s_row in spx_df.iterrows():
        s_id = s_row["source_id"]
        s_ra = s_row["ra"]
        s_dec = s_row["dec"]

        box_r = 6.0 / 3600.0
        box_ra = box_r / 0.35
        sub = wise_cand[
            (wise_cand["ra"] >= s_ra - box_ra) & (wise_cand["ra"] <= s_ra + box_ra) &
            (wise_cand["dec"] >= s_dec - box_r) & (wise_cand["dec"] <= s_dec + box_r)
        ].copy()

        candidates = []
        for _, w_row in sub.iterrows():
            w_ra = w_row["ra"]
            w_dec = w_row["dec"]
            d_wise = angular_separation_arcsec(s_ra, s_dec, w_ra, w_dec)
            if d_wise <= 4.0:
                candidates.append({
                    "w_row": w_row,
                    "d_wise": d_wise
                })

        candidates.sort(key=lambda x: x["d_wise"])
        n_cands = len(candidates)

        if n_cands == 0:
            wise_match_records.append({
                "source_id": s_id,
                "spx_ra": s_ra,
                "spx_dec": s_dec,
                "allwise_designation": None,
                "allwise_ra": None,
                "allwise_dec": None,
                "allwise_sep_arcsec": None,
                "sigra_arcsec": None,
                "sigdec_arcsec": None,
                "w1mpro": None,
                "w1sigmpro": None,
                "w1snr": None,
                "w2mpro": None,
                "w2sigmpro": None,
                "w2snr": None,
                "w1_minus_w2": None,
                "cc_flags": None,
                "ext_flg": None,
                "ph_qual": None,
                "num_candidates_in_radius": 0,
                "competing_candidate_id": None,
                "competing_sep_arcsec": None,
                "match_category": "UNMATCHED",
                "match_notes": "No AllWISE source detected within 4.0 arcsec"
            })
        else:
            best = candidates[0]
            w = best["w_row"]
            d1 = best["d_wise"]
            competing_id = candidates[1]["w_row"]["designation"] if n_cands > 1 else None
            competing_sep = candidates[1]["d_wise"] if n_cands > 1 else None

            cc_flags = str(w["cc_flags"]) if pd.notna(w["cc_flags"]) else "0000"
            has_contamination = any(c in cc_flags for c in ["D", "P", "H", "O"])
            w1 = w["w1mpro"]
            w2 = w["w2mpro"]
            w1_w2 = (w1 - w2) if (pd.notna(w1) and pd.notna(w2)) else None

            if n_cands > 1 and competing_sep <= 2.5 and (competing_sep - d1) < 1.0:
                cat = "AMBIGUOUS"
                notes = f"Multiple AllWISE candidates in beam: d1={d1:.2f}as, d2={competing_sep:.2f}as"
            elif d1 <= 0.8:
                if has_contamination and cc_flags[0] != "0":
                    cat = "QUALITY_REJECTED"
                    notes = f"Severe photometric artifact in W1: cc_flags={cc_flags}"
                else:
                    cat = "HIGH_CONFIDENCE"
                    notes = f"Clean AllWISE point source match at sep={d1:.2f}as"
            elif d1 <= 2.0:
                if has_contamination and cc_flags[0] != "0":
                    cat = "QUALITY_REJECTED"
                    notes = f"Contaminated candidate at sep={d1:.2f}as, cc={cc_flags}"
                else:
                    cat = "PROBABLE"
                    notes = f"Probable match at sep={d1:.2f}as"
            else:
                cat = "PROBABLE" if n_cands == 1 else "AMBIGUOUS"
                notes = f"Wide AllWISE match at sep={d1:.2f}as"

            wise_match_records.append({
                "source_id": s_id,
                "spx_ra": s_ra,
                "spx_dec": s_dec,
                "allwise_designation": str(w["designation"]),
                "allwise_ra": w["ra"],
                "allwise_dec": w["dec"],
                "allwise_sep_arcsec": d1,
                "sigra_arcsec": w["sigra"],
                "sigdec_arcsec": w["sigdec"],
                "w1mpro": w1,
                "w1sigmpro": w["w1sigmpro"],
                "w1snr": w["w1snr"],
                "w2mpro": w2,
                "w2sigmpro": w["w2sigmpro"],
                "w2snr": w["w2snr"],
                "w1_minus_w2": w1_w2,
                "cc_flags": cc_flags,
                "ext_flg": int(w["ext_flg"]) if pd.notna(w["ext_flg"]) else 0,
                "ph_qual": str(w["ph_qual"]) if pd.notna(w["ph_qual"]) else "UUUU",
                "num_candidates_in_radius": n_cands,
                "competing_candidate_id": competing_id,
                "competing_sep_arcsec": competing_sep,
                "match_category": cat,
                "match_notes": notes
            })

    wise_match_df = pd.DataFrame(wise_match_records)
    wise_match_df.to_csv(OUT_WISE_MATCHES, index=False)
    print(f"Saved AllWISE matches -> {OUT_WISE_MATCHES}")

    # 4. Crossmatch Summary
    print("\nAssembling Cross-Match Summary...")
    summary_records = []
    for idx, s_row in spx_df.iterrows():
        s_id = s_row["source_id"]
        g_row = gaia_match_df.loc[gaia_match_df["source_id"] == s_id].iloc[0]
        w_row = wise_match_df.loc[wise_match_df["source_id"] == s_id].iloc[0]

        g_cat = g_row["match_category"]
        w_cat = w_row["match_category"]

        g_ok = g_cat in ["HIGH_CONFIDENCE", "PROBABLE"]
        w_ok = w_cat in ["HIGH_CONFIDENCE", "PROBABLE"]
        both_matched = g_ok and w_ok

        if both_matched:
            overall = "DUAL_CATALOG_MATCH"
        elif g_ok and not w_ok:
            overall = "GAIA_ONLY_MATCH"
        elif w_ok and not g_ok:
            overall = "ALLWISE_ONLY_MATCH"
        elif g_cat == "AMBIGUOUS" or w_cat == "AMBIGUOUS":
            overall = "AMBIGUOUS_MATCH"
        elif g_cat == "QUALITY_REJECTED" or w_cat == "QUALITY_REJECTED":
            overall = "QUALITY_REJECTED"
        else:
            overall = "UNMATCHED"

        summary_records.append({
            "source_id": s_id,
            "spx_ra": s_row["ra"],
            "spx_dec": s_row["dec"],
            "gaia_source_id": g_row["gaia_source_id"],
            "gaia_sep_arcsec": g_row["sep_prop_arcsec"],
            "gaia_match_category": g_cat,
            "allwise_designation": w_row["allwise_designation"],
            "allwise_sep_arcsec": w_row["allwise_sep_arcsec"],
            "allwise_match_category": w_cat,
            "both_matched": both_matched,
            "overall_match_status": overall,
            "spectra_anomaly_score_B": s_row["chi2_B_d1_d4"],
            "spectra_valid_channels_B": s_row["valid_channels_B_d1_d4"]
        })

    summary_df = pd.DataFrame(summary_records)
    summary_df.to_csv(OUT_SUMMARY, index=False)
    print(f"Saved Cross-Match Summary -> {OUT_SUMMARY}")

    # 5. Classification Features
    print("\nComputing Astrophysical Classification Features...")
    feature_records = []
    classification_records = []

    for idx, s_row in spx_df.iterrows():
        s_id = s_row["source_id"]
        g_row = gaia_match_df.loc[gaia_match_df["source_id"] == s_id].iloc[0]
        w_row = wise_match_df.loc[wise_match_df["source_id"] == s_id].iloc[0]

        g_ok = g_row["match_category"] in ["HIGH_CONFIDENCE", "PROBABLE"]
        w_ok = w_row["match_category"] in ["HIGH_CONFIDENCE", "PROBABLE"]

        g_mag = g_row["phot_g_mean_mag"] if g_ok else None
        bp_rp = g_row["bp_rp"] if g_ok else None
        plx = g_row["parallax_mas"] if g_ok else None
        plx_err = g_row["parallax_error_mas"] if g_ok else None
        plx_snr = g_row["parallax_over_error"] if g_ok else None
        tot_pm = g_row["total_pm_mas_yr"] if g_ok else None
        pm_sig = g_row["pm_significance"] if g_ok else None
        ruwe = g_row["ruwe"] if g_ok else None

        # Distance & Absolute Magnitude
        dist_pc = None
        abs_mag_g = None
        if plx is not None and pd.notna(plx) and plx > 0 and plx_snr is not None and plx_snr >= 3.0:
            dist_pc = 1000.0 / plx
            if g_mag is not None and pd.notna(g_mag):
                abs_mag_g = g_mag + 5.0 - 5.0 * math.log10(dist_pc)

        w1 = w_row["w1mpro"] if w_ok else None
        w2 = w_row["w2mpro"] if w_ok else None
        w1_w2 = w_row["w1_minus_w2"] if w_ok else None
        g_w1 = (g_mag - w1) if (g_mag is not None and w1 is not None and pd.notna(g_mag) and pd.notna(w1)) else None
        ext_flg = w_row["ext_flg"] if w_ok else None

        chi2_B = s_row["chi2_B_d1_d4"]
        chi2_d1 = s_row["chi2_d1_in_B"]
        chi2_d4 = s_row["chi2_d4_in_B"]

        feature_records.append({
            "source_id": s_id,
            "phot_g_mean_mag": g_mag,
            "phot_bp_mean_mag": g_row["phot_bp_mean_mag"] if g_ok else None,
            "phot_rp_mean_mag": g_row["phot_rp_mean_mag"] if g_ok else None,
            "bp_rp": bp_rp,
            "parallax_mas": plx,
            "parallax_error_mas": plx_err,
            "parallax_over_error": plx_snr,
            "distance_pc": dist_pc,
            "abs_mag_g": abs_mag_g,
            "total_pm_mas_yr": tot_pm,
            "pm_significance": pm_sig,
            "ruwe": ruwe,
            "w1mpro": w1,
            "w1sigmpro": w_row["w1sigmpro"] if w_ok else None,
            "w1snr": w_row["w1snr"] if w_ok else None,
            "w2mpro": w2,
            "w2sigmpro": w_row["w2sigmpro"] if w_ok else None,
            "w2snr": w_row["w2snr"] if w_ok else None,
            "w1_minus_w2": w1_w2,
            "g_minus_w1": g_w1,
            "cc_flags": w_row["cc_flags"] if w_ok else None,
            "ext_flg": ext_flg,
            "ph_qual": w_row["ph_qual"] if w_ok else None,
            "chi2_B_d1_d4": chi2_B,
            "chi2_d1_in_B": chi2_d1,
            "chi2_d4_in_B": chi2_d4,
            "valid_channels_B_d1_d4": s_row["valid_channels_B_d1_d4"]
        })

        # 6. Probabilistic Astronomical Source Classification
        # Decision tree using multi-band astrometric and photometric evidence
        cls_label = "UNCLASSIFIED"
        confidence = "NONE"
        evidence_list = []
        limitations_list = []

        if not g_ok and not w_ok:
            cls_label = "UNCLASSIFIED"
            confidence = "NONE"
            evidence_list.append("No high-confidence match in Gaia or AllWISE")
            limitations_list.append("Unmatched source; no external photometric or astrometric priors")
        elif w_ok and w1_w2 is not None and w1_w2 >= 0.8 and (plx_snr is None or plx_snr < 2.0) and (pm_sig is None or pm_sig < 2.5):
            # Extragalactic / AGN candidate (Jarrett et al. 2011 / Stern et al. 2012 WISE AGN criteria)
            cls_label = "EXTRAGALACTIC_OR_AGN_CANDIDATE"
            confidence = "HIGH" if (ext_flg is not None and ext_flg > 0) or (w1_w2 >= 1.0) else "MEDIUM"
            evidence_list.append(f"WISE W1-W2 = {w1_w2:.2f} >= 0.8 (AGN wedge)")
            evidence_list.append(f"Parallax SNR = {plx_snr if plx_snr is not None else 0.0:.1f} < 2.0 (consistent with extragalactic)")
            evidence_list.append(f"Proper motion SNR = {pm_sig if pm_sig is not None else 0.0:.1f} < 2.5 (zero motion)")
            limitations_list.append("Unconfirmed without optical/NIR spectroscopic redshift")
        elif w_ok and w1_w2 is not None and (w1_w2 >= 0.45 or (w1_w2 >= 0.25 and bp_rp is not None and bp_rp <= 1.2)):
            # Young Stellar Object / Circumstellar Dust Excess candidate
            cls_label = "YSO_OR_IR_EXCESS"
            confidence = "HIGH" if (w1_w2 >= 0.30 and (bp_rp is not None and bp_rp <= 0.8)) else "MEDIUM"
            evidence_list.append(f"Circumstellar dust / mid-IR excess: W1-W2 = {w1_w2:.2f} >= 0.25")
            if bp_rp is not None:
                evidence_list.append(f"Early-type stellar photosphere: BP-RP = {bp_rp:.2f}")
            if chi2_d4 >= 1.5:
                evidence_list.append(f"Elevated SPHEREx D4 anomaly score: chi2_d4 = {chi2_d4:.2f}")
            limitations_list.append("Requires mid-IR spectroscopy to confirm dust mineralogy/PAH vs debris disk")
        elif g_ok and bp_rp is not None and bp_rp >= 2.5 and ((abs_mag_g is not None and abs_mag_g <= 0.0) or (g_w1 is not None and g_w1 >= 3.8)) and (w1 is not None and w1 <= 10.0):
            # Asymptotic Giant Branch (AGB) / Late-M / Carbon Star Candidate
            cls_label = "AGB_CANDIDATE"
            confidence = "HIGH" if (bp_rp >= 2.8 and (abs_mag_g is not None and abs_mag_g <= -1.0)) else "MEDIUM"
            evidence_list.append(f"Extremely red optical color: BP-RP = {bp_rp:.2f} >= 2.5 (cool photosphere T < 3200 K)")
            if abs_mag_g is not None:
                evidence_list.append(f"High bolometric luminosity: M_G = {abs_mag_g:.2f} <= 0.0 (above RGB tip)")
            if g_w1 is not None:
                evidence_list.append(f"Strong optical-to-mid-IR color: G-W1 = {g_w1:.2f} >= 3.8")
            evidence_list.append(f"Bright mid-IR magnitude: W1 = {w1:.2f} <= 10.0")
            limitations_list.append("Pulsational variability (Mira/semiregular) may alter instantaneous photometry")
        elif g_ok and plx_snr is not None and plx_snr >= 3.0 and abs_mag_g is not None:
            # Calibrated Hertzsprung-Russell Diagram position
            if abs_mag_g >= 10.0 and bp_rp is not None and bp_rp <= 0.8:
                # White Dwarf Candidate
                cls_label = "WHITE_DWARF_CANDIDATE"
                confidence = "HIGH" if abs_mag_g >= 11.0 else "MEDIUM"
                evidence_list.append(f"Sub-luminous M_G = {abs_mag_g:.2f} >= 10.0")
                evidence_list.append(f"Blue optical color: BP-RP = {bp_rp:.2f} <= 0.8")
                evidence_list.append(f"Significant parallax: pi/sigma = {plx_snr:.1f}")
                limitations_list.append("Potential degenerate dwarf / subdwarf ambiguity")
            elif abs_mag_g <= 3.5 and bp_rp is not None and bp_rp >= 1.0:
                # Giant / Evolved Star
                cls_label = "GIANT_EVOLVED_STAR"
                confidence = "HIGH" if (abs_mag_g <= 2.0 and plx_snr >= 5.0) else "MEDIUM"
                evidence_list.append(f"High luminosity: M_G = {abs_mag_g:.2f} <= 3.5")
                evidence_list.append(f"Red giant color: BP-RP = {bp_rp:.2f} >= 1.0")
                evidence_list.append(f"Parallax SNR = {plx_snr:.1f} >= 3.0")
                if w1_w2 is not None:
                    evidence_list.append(f"Stellar Rayleigh-Jeans tail: W1-W2 = {w1_w2:.2f}")
                limitations_list.append("Subgiant vs red clump evolutionary stage unrefined")
            else:
                # Main Sequence Dwarf Star
                cls_label = "MAIN_SEQUENCE_STAR"
                confidence = "HIGH" if plx_snr >= 5.0 else "MEDIUM"
                evidence_list.append(f"Empirical main sequence: M_G = {abs_mag_g:.2f}, BP-RP = {bp_rp:.2f}")
                evidence_list.append(f"Parallax SNR = {plx_snr:.1f} >= 3.0 (d = {dist_pc:.0f} pc)")
                if w1_w2 is not None:
                    evidence_list.append(f"Stellar photospheric mid-IR continuum: W1-W2 = {w1_w2:.2f}")
                limitations_list.append("Spectral subclass (OBAFGKM) requires high-resolution spectrum")
        elif g_ok and bp_rp is not None and (plx_snr is None or plx_snr < 3.0):
            # Gaia matched, but distance uncalibrated
            if w_ok and w1_w2 is not None and abs(w1_w2) <= 0.25 and (g_w1 is not None and 0.5 <= g_w1 <= 4.0):
                cls_label = "MAIN_SEQUENCE_STAR"
                confidence = "LOW"
                evidence_list.append(f"Optical-IR stellar colors: BP-RP = {bp_rp:.2f}, G-W1 = {g_w1:.2f}, W1-W2 = {w1_w2:.2f}")
                limitations_list.append("Parallax SNR < 3.0; absolute magnitude unconstrained")
            else:
                cls_label = "UNCLASSIFIED"
                confidence = "NONE"
                evidence_list.append(f"Gaia match with G = {g_mag:.2f}, BP-RP = {bp_rp:.2f}")
                limitations_list.append("Parallax SNR < 3.0; uncalibrated distance and ambiguous colors")
        else:
            cls_label = "UNCLASSIFIED"
            confidence = "NONE"
            evidence_list.append("Insufficient reliable astrometric/photometric constraints")
            limitations_list.append("Requires deeper multi-band follow-up")

        classification_records.append({
            "source_id": s_id,
            "classification_label": cls_label,
            "confidence": confidence,
            "classification_method": "Multi-feature decision tree (HR diagram M_G vs BP-RP, plx_snr, pm_sig, WISE W1-W2)",
            "primary_evidence": " | ".join(evidence_list),
            "limitations": " | ".join(limitations_list),
            "spectra_anomaly_score_B": chi2_B,
            "chi2_d1_in_B": chi2_d1,
            "chi2_d4_in_B": chi2_d4
        })

    features_df = pd.DataFrame(feature_records)
    features_df.to_csv(OUT_FEATURES, index=False)
    print(f"Saved Classification Features -> {OUT_FEATURES}")

    class_df = pd.DataFrame(classification_records)
    class_df.to_csv(OUT_CLASSIFICATIONS, index=False)
    print(f"Saved Source Classifications -> {OUT_CLASSIFICATIONS}")

    # Summary Statistics
    print("\n" + "=" * 80)
    print("TASK 4 PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Sources Evaluated: {len(spx_df)}")
    print("\nGaia DR3 Match Categories:")
    print(gaia_match_df["match_category"].value_counts())
    print("\nAllWISE Match Categories:")
    print(wise_match_df["match_category"].value_counts())
    print("\nOverall Cross-Match Status:")
    print(summary_df["overall_match_status"].value_counts())
    print("\nSource Classification Distribution:")
    print(class_df["classification_label"].value_counts())
    print("\nConfidence Distribution:")
    print(class_df["confidence"].value_counts())


if __name__ == "__main__":
    run_crossmatching()
