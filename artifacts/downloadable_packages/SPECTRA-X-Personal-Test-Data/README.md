# SPECTRA-X Personal Test Dataset (50 Pairs / 100 Samples)

**Version:** 1.0.0  
**Release Date:** 2026-11-13  
**Package:** `SPECTRA-X-Personal-Test-Data.zip`  
**License / Terms:** NASA Space Apps Challenge 2026 Engineering Dataset  

---

## 1. Important Product Architecture Note

SPECTRA-X is a general-purpose, input-driven astronomical analysis platform. Researchers and astronomers provide their own observation data (FITS cutouts, 102-channel spectrophotometry CSVs, or target catalogs) directly into the workspace.

This dataset is an **OPTIONAL, SEPARATELY DOWNLOADABLE PERSONAL TEST DATASET** for offline development, algorithm verification, and demonstration.

The SPECTRA-X Observatory application:
- Does **NOT** depend on this test dataset.
- Does **NOT** preload this dataset automatically into analysis sessions.
- Does **NOT** treat synthetic engineering scenarios as real astronomical discoveries.

---

## 2. Dataset Composition (50 Pairs / 100 Observation Samples)

| Dataset Class | Pair Count | Samples | Baseline Separation (Δt) | Scientific Classification |
|:---|:---:|:---:|:---:|:---|
| **REAL_INTRA_VISIT** | 25 | 50 | $\Delta t < 1.0\text{ day}$ ($2.15 - 6.45\text{ min}$) | `INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY` |
| **SYNTHETIC_ENGINEERING_TEST** | 25 | 50 | $\Delta t = 1.0 - 90.0\text{ days}$ | `TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION` |
| **TOTAL** | **50** | **100** | — | — |

---

## 3. Package Structure

```text
SPECTRA-X-Personal-Test-Data/
├── README.md                  # This documentation
├── dataset_manifest.json      # Complete dataset catalog manifest
├── SHA256SUMS.txt             # Bitwise SHA-256 checksums of all 100 FITS files and metadata
├── real_intra_visit/          # 25 Real SPHEREx flight observation dither pairs
│   ├── manifest.json
│   └── pairs/
│       ├── REAL_PAIR_001/     # (P0003, D1, Dither 1 vs Dither 4, Primary Candidate)
│       │   ├── obs_a.fits
│       │   ├── obs_b.fits
│       │   └── pair_metadata.json
│       └── ... (REAL_PAIR_001 through REAL_PAIR_025)
└── synthetic_engineering_test/ # 25 Deterministic synthetic motion pairs
    ├── manifest.json
    └── pairs/
        ├── SYNTH_PAIR_001/    # (Main Belt Asteroid-like slow shift)
        │   ├── obs_a.fits
        │   ├── obs_b.fits
        │   ├── ground_truth_motion.json
        │   └── pair_metadata.json
        └── ... (SYNTH_PAIR_001 through SYNTH_PAIR_025)
```

---

## 4. Extraction & Usage Instructions

### 4.1 Extracting the Package
Extract the ZIP archive into any convenient location on your workstation:
```bash
unzip SPECTRA-X-Personal-Test-Data.zip -d personal_test_data/
```

### 4.2 Inspecting a Real Intra-Visit Pair
Every real pair contains:
- `obs_a.fits`: Multi-extension FITS file (SCI, VAR, FLAGS) with WCS.
- `obs_b.fits`: Subsequent intra-visit dither FITS file taken minutes later.
- `pair_metadata.json`: Provenance metadata recording original FITS filenames and SHA-256 hashes.

### 4.3 Inspecting a Synthetic Engineering Pair
Every synthetic pair contains:
- `obs_a.fits` & `obs_b.fits`: Simulated FITS frames with synthetic point spread functions.
- `ground_truth_motion.json`: Known ground-truth trajectory, angular displacement, and rates.
- `pair_metadata.json`: Scenario category and parameter details.

### 4.4 Using with the SPECTRA-X Motion Analysis API
You can run automated motion analysis on any pair using the REST API:
```bash
curl -X POST http://127.0.0.1:8050/api/motion/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "obs_a": {"ra": 150.0, "dec": 10.0, "timestamp": "2026-07-02T00:00:00Z"},
    "obs_b": {"ra": 150.001, "dec": 10.001, "timestamp": "2026-07-04T00:00:00Z"}
  }'
```

---

## 5. Scientific Limitations & Governance

1. **Intra-Visit Dither Restriction:** Real pairs feature baselines $\Delta t < 1.0\text{ day}$ and must NEVER be used to claim moving object discoveries. They are intended strictly for astrometric alignment, PSF subtraction null tests, and registration diagnostics.
2. **Synthetic Data Labeling:** All synthetic observations are artificially synthesized test patterns with known ground-truth motion vectors. They must NEVER be presented as real astronomical discoveries.
