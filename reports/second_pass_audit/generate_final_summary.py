import os
import json
from datetime import datetime, timezone

def generate_summary():
    base_dir = os.path.abspath(".")
    audit_dir = os.path.join(base_dir, "reports", "second_pass_audit")
    
    # 1. Machine-readable JSON summary
    summary_data = {
        "audit_name": "SPECTRA-X Second-Pass Scientific Audit & Validation",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "total_bytes": 5577836001,
            "total_gb": 5.1948,
            "data_files_count": 205,
            "level2_fits_count": 32,
            "calibration_files_count": 151,
            "external_catalogs_count": 8,
            "corrupted_files": 0,
            "zero_byte_files": 0,
            "duplicates": 0
        },
        "model_readiness": {
            "ASTROVISION": {"level": 6, "status": "INDEPENDENTLY_EVALUATED", "first_pass_claim": "READY", "real_world_discovery": "PENDING"},
            "SPECTRA": {"level": 4, "status": "BASELINE_TRAINED_PROXY_DATA", "first_pass_claim": "READY", "real_world_discovery": "PENDING"},
            "CHRONOS-X": {"level": 5, "status": "PIPELINE_IMPLEMENTED_VAL_PENDING", "first_pass_claim": "READY", "real_world_discovery": "PENDING"},
            "MOTION-X": {"level": 5, "status": "PIPELINE_IMPLEMENTED_VAL_PENDING", "first_pass_claim": "READY", "real_world_discovery": "PENDING"},
            "FUSION-X": {"level": 5, "status": "PIPELINE_IMPLEMENTED_HEURISTIC_FUNCTIONAL", "first_pass_claim": "READY", "real_world_discovery": "PENDING"}
        },
        "critical_scientific_corrections": [
            {
                "topic": "152.2 Sigma Residual",
                "first_pass_claim": "Potential temporal transient significance (152.4 sigma)",
                "second_pass_finding": "Instrumental dead-pixel defect (MP_OVERFLOW + MP_NONFUNC, flag 655426) in epoch 2 smeared by bilinear reprojection and unmasked due to nearest-neighbor mask interpolation mismatch.",
                "scientific_status": "PROVEN_INSTRUMENTAL_ARTIFACT"
            },
            {
                "topic": "Flag Policy",
                "first_pass_claim": "Blanket rejection rule: FLAGS != 0",
                "second_pass_finding": "Rejection of all non-zero flags erroneously discards astronomical sources (MP_SOURCE, Bit 21), full telemetry sampling (MP_FULLSAMPLE, Bit 12), and calibrated non-linear pixels (MP_NONLINEAR, Bit 15).",
                "scientific_status": "REPLACED_WITH_FATAL_MASK_615"
            },
            {
                "topic": "SPECTRA 102-Band SED Extraction",
                "first_pass_claim": "Ready for 102-channel spectrophotometric anomaly detection",
                "second_pass_finding": "Each downloaded pointing contains exactly 1 detector (D1 in QR3, D2 in QR2). Assembling 102 channels across 0.75-5.0 um requires D1-D6 coordinated pointings. Current model was trained on synthetic proxy SEDs.",
                "scientific_status": "CORRECTED_TO_BASELINE_PROXY_LEVEL_4"
            },
            {
                "topic": "Horizons Solar System Ephemerides",
                "first_pass_claim": "Ceres, Pallas, Vesta ephemerides downloaded",
                "second_pass_finding": "Horizons query syntax without ';' returned Mercury, Venus, Mars. Apophis and Eros are correct. Zero small bodies fell in SPHEREx fields on observation dates.",
                "scientific_status": "CORRECTED_NO_EMPIRICAL_ASTEROID_RECOVERY"
            }
        ],
        "strict_read_only_compliance": {
            "existing_files_modified": 0,
            "existing_files_deleted": 0,
            "existing_files_overwritten": 0,
            "new_data_downloaded_bytes": 0
        }
    }
    
    json_path = os.path.join(audit_dir, "audit_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Machine-readable JSON summary written to {json_path}")

    # 2. Comprehensive final_audit_summary.md
    summary_md_path = os.path.join(audit_dir, "final_audit_summary.md")
    with open(summary_md_path, "w", encoding="utf-8") as out:
        out.write("# SPECTRA-X: Second-Pass Scientific Audit & Validation — Final Executive Summary\n\n")
        out.write(f"**Audit Execution Timestamp**: `{datetime.now(timezone.utc).isoformat()}`\n\n")
        out.write("## 1. Project Context and Audit Mandate\n\n")
        out.write("This second-pass scientific audit was conducted under a **Strict Read-Only Policy** on the existing **5.195 GB dataset** (205 data files, 32 Level-2 SPHEREx FITS products, QR2/QR3 wide & deep observations, calibration maps, templates, and external catalogues).\n\n")
        out.write("The mandate: **Evidence over claims. Scientific correctness over model count. Real observations over synthetic demonstrations.**\n\n")

        out.write("## 2. Key Audit Deliverables Generated\n\n")
        out.write("| # | Deliverable File | Description |\n")
        out.write("| :-: | :--- | :--- |\n")
        out.write("| 1 | `[project_inventory.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/project_inventory.md)` | Complete directory, file, script, checkpoint, and environment inventory. |\n")
        out.write("| 2 | `[corrected_fits_audit.csv](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/corrected_fits_audit.csv)` | 224-row HDU-by-HDU verification across all 32 Level-2 files. |\n")
        out.write("| 3 | `[flag_policy.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/flag_policy.md)` | Documented classification of SPHEREx flags (Fatal, Warning, Info, Source). |\n")
        out.write("| 4 | `[spectral_extraction_audit.csv](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/spectral_extraction_audit.csv)` | Standalone spectral WCS and channel definition catalog audit. |\n")
        out.write("| 5 | `[spectral_extraction_report.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/spectral_extraction_report.md)` | Deep dive into 102-channel extraction and single-detector limitations. |\n")
        out.write("| 6 | `[temporal_validation_report.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/temporal_validation_report.md)` | Investigation of 44 dither pairs and complete dissection of the 152.2σ artifact. |\n")
        out.write("| 7 | `[temporal_pair_audit.csv](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/temporal_pair_audit.csv)` | Catalog of all 44 intra-release dither pairs with separations and timestamps. |\n")
        out.write("| 8 | `[motion_validation_report.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/motion_validation_report.md)` | Astrometric verification, Gaia DR3 accuracy, and Horizons ephemerides audit. |\n")
        out.write("| 9 | `[motion_crossmatch_audit.csv](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/motion_crossmatch_audit.csv)` | 35 cross-match evaluations between Horizons bodies and SPHEREx pointings. |\n")
        out.write("| 10 | `[fusion_validation_report.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/fusion_validation_report.md)` | Multimodal ranking logic, heuristic scoring audit, and co-pilot tagging. |\n")
        out.write("| 11 | `[model_evaluation_report.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/model_evaluation_report.md)` | ASTROVISION independent test, SPECTRA feature test, and data leakage audit. |\n")
        out.write("| 12 | `[corrected_readiness_matrix.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/corrected_readiness_matrix.md)` | Official 7-level readiness matrix replacing unverified claims with evidence. |\n")
        out.write("| 13 | `[final_audit_summary.md](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/final_audit_summary.md)` | This comprehensive summary document. |\n")
        out.write("| 14 | `[audit_summary.json](file:///" + base_dir.replace('\\', '/') + "/reports/second_pass_audit/audit_summary.json)` | Machine-readable JSON summary for automated pipelines. |\n\n")

        out.write("## 3. Top Five Critical Scientific Corrections\n\n")
        out.write("### 1. The 152.2σ Signal is an Instrumental Artifact, NOT an Astronomical Transient\n")
        out.write("- **Investigation Result**: In Epoch 2, raw pixel $(1779, 1415)$ had flux $110.73\\,\\text{MJy/sr}$ with flag `655426` (`MP_OVERFLOW` + `MP_NONFUNC` + `MP_PERSIST` + `MP_OUTLIER`).\n")
        out.write("- **Mechanism**: During `reproject_interp`, bilinear image interpolation smeared this flux spike across adjacent coordinates, while nearest-neighbor mask interpolation failed to mask the smeared footprint, creating an artificial $152.21\\sigma$ peak.\n")
        out.write("- **Correction**: Must NOT be claimed as a transient discovery. Reprojection masks must use morphological dilation.\n\n")

        out.write("### 2. Blanket `FLAGS != 0` Masking Discarded Real Astronomical Sources\n")
        out.write("- **Investigation Result**: Flag `2097152` (`MP_SOURCE`, Bit 21) marks real celestial stars and galaxies. Blanket filtering (`flags == 0`) discarded the astronomical targets!\n")
        out.write("- **Correction**: Replaced with fatal defect mask: `FATAL_FLAG_MASK = 615` (Bits 0, 1, 2, 5, 6, 9).\n\n")

        out.write("### 3. SPECTRA 102-Channel SEDs Were Trained on Synthetic Proxies\n")
        out.write("- **Investigation Result**: Every downloaded pointing contains only 1 detector array (D1 in QR3, D2 in QR2). Covering all 102 channels ($0.75 - 5.0\\,\\mu\\text{m}$) requires D1–D6 coordinated sets.\n")
        out.write("- **Correction**: Checkpoint `spectra_spectro_ae.pt` is classified as **Level 4 (Baseline Trained on Proxy Data)**. No claims of empirical PAH or ice feature detection are permitted until empirical D1–D6 photometry is extracted.\n\n")

        out.write("### 4. Horizons Ephemerides Numbering Syntax Bug Identified\n")
        out.write("- **Investigation Result**: Querying Horizons with bare integers `1`, `2`, `4` fetched Mercury, Venus, and Mars instead of Ceres, Pallas, Vesta. Apophis and Eros are correct. Zero small bodies were in the FOV.\n")
        out.write("- **Correction**: Fix query syntax to append `;`. Do not claim asteroid recovery without empirical in-FOV targets.\n\n")

        out.write("### 5. FUSION-X Scores are Heuristics, NOT Calibrated Probabilities\n")
        out.write("- **Investigation Result**: Fused ranking scores are computed from an uncalibrated linear network with manual weights on synthetic demo inputs.\n")
        out.write("- **Correction**: Must be reported as heuristic priority scores, not probabilities.\n\n")

        out.write("## 4. Final Scientific Decision and Development Roadmap\n\n")
        out.write("Based on the audit findings, the recommended next development phase is prioritized as follows:\n\n")
        out.write("1. **First Priority: Choice C — Repair the Scientific Validation Pipeline Before Further Model Work**\n")
        out.write("   - Update `reproject_interp` masking with morphological dilation to eliminate false transient artifacts.\n")
        out.write("   - Replace blanket `flags != 0` with `(flags & 615) == 0` across all pipeline scripts.\n")
        out.write("   - Implement PSF-matching convolution (Alard-Lupton or Bramich) before differencing to eliminate dither dipoles.\n")
        out.write("2. **Second Priority: Choice D — Improve Spectral Extraction Before SPECTRA Development**\n")
        out.write("   - Build a verified aperture photometry extraction engine (`extract_photometry.py`) using `photutils` and `spectral_wcs_D*.fits` to extract real monochromatic SED points from available Level-2 science files.\n")
        out.write("3. **Third Priority: Choice E — Improve Independent Evaluation Before Model Integration**\n")
        out.write("   - Establish strict spatial train/val/test splits (Pointing 0001 = Train, Pointing 0002 = Val, Pointing 0003 = Test) to eliminate spatial leakage.\n")
        out.write("4. **Fourth Priority: Choice B — Acquire Targeted Additional SPHEREx Data (When Budget is Expanded)**\n")
        out.write("   - Acquire coordinated D1–D6 exposures for identical pointings to enable complete 102-channel SEDs.\n")
        out.write("   - Acquire repeat multi-month QR3 visits covering identical sky areas for genuine temporal baselines.\n")

    print(f"Final executive summary written to {summary_md_path}")

if __name__ == '__main__':
    generate_summary()
