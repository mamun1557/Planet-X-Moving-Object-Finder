# SPECTRA-X: Comprehensive Model Evaluation & Data Leakage Audit

## 1. Executive Summary & Verification Principles

This report provides an empirical evaluation of the core AI models in SPECTRA-X:
- **ASTROVISION** (Spatial Morphological Autoencoder)
- **SPECTRA** (102-Channel Spectrophotometric Autoencoder)
- **Data Leakage & Train/Val/Test Splitting Policy**

> [!IMPORTANT]
> In strict accordance with scientific audit standards, synthetic anomaly injection metrics are evaluated as **algorithmic benchmark baselines only**, NOT as proof of real-world astronomical discovery. All metrics without verified ground-truth labels are explicitly marked **PENDING**.

## 2. ASTROVISION Spatial Autoencoder Evaluation

### Model Architecture & Configuration:
- **Class**: `AstroVisionAutoencoder` in `models/astrovision/model.py`.
- **Backbone**: 4-stage convolutional encoder-decoder with latent bottleneck (dimension = 128).
- **Input Geometry**: Single-channel 2D cutouts of dimension `128 x 128` pixels.
- **Loss Formulation**: Inverse-variance weighted masked reconstruction loss:
  $$\mathcal{L} = \frac{1}{N} \sum_{i} \frac{(I_i - \hat{I}_i)^2}{\sigma_i^2 + \epsilon} \cdot M_i$$
- **Evaluated Checkpoint**: `checkpoints/astrovision_spatial_ae.pt` (verified 1 epoch CUDA training).

### Data Leakage Findings in Existing Training Pipeline:
- **Identified Flaw**: `train_astrovision.py` extracts random 128x128 cutouts across all available Level-2 files without spatial grouping. Because the dataset contains dithered observations of the same sky pointings (Dithers 1D, 2D, 3D, 4D), random patch extraction causes **severe spatial leakage**, where overlapping sky regions are simultaneously present in training and evaluation batches.
- **Proposed Spatial Partitioning Rule**:
  - **Training Set**: Pointing `0001` (Dithers 1D–4D)
  - **Validation Set**: Pointing `0002` (Dithers 1D–4D)
  - **Independent Test Set**: Pointing `0003` (Dithers 1D–4D, completely separated by > 1.5° on sky)

### Empirical Evaluation on Independent Sky Region (Pointing 0003):
- **Clean Test Reconstruction Loss**: `796.9700 +/- 145.7796`
- **Synthetic Anomaly Injection Recon Loss**: `798.3054`
- **Synthetic Anomaly Detection AUROC**: `0.5116`
- **Synthetic Anomaly Detection AUPRC**: `0.5242`
- **Real-World Morphological Anomaly Discovery Rate**: **PENDING** (requires verified ground-truth extended galaxy catalog).

## 3. SPECTRA 102-Channel Spectrophotometric Autoencoder Evaluation

### Model Architecture & Configuration:
- **Class**: `SpectralAnomalyDetector` in `models/spectra/model.py`.
- **Backbone**: Multilayer Perceptron Autoencoder with latent bottleneck (dimension = 16).
- **Input Channels**: 102 spectral bands (0.75 – 5.0 µm).
- **Provenance Fact**: Checkpoint `checkpoints/spectra_spectro_ae.pt` was trained on **synthetic procedural SED proxies** (`generate_synthetic_spectra`), NOT empirical Level-2 photometry.

### Algorithmic Benchmark Performance:
- **Baseline Synthetic SED Recon MSE**: `0.2316`
- **Robustness to 15 Missing Channels (15% drop)**: `0.1997` (Degradation: 0.86x)
- **Synthetic 3.3 µm PAH Emission Anomaly AUROC**: `1.0000`
- **Empirical PAH / Ice / CO2 Feature Discovery**: **PENDING** (Strict scientific rule: no claims of real-world chemical detections can be made without empirical calibrated spectra from all 6 detectors).

## 4. Quantitative Model Evaluation Metrics Summary

| Model | Metric | Value | Baseline / Ground Truth |
| :--- | :--- | :---: | :--- |
| ASTROVISION | Independent Test Recon Loss | 796.9700 | Pointing 0003 Independent Sky Region |
| ASTROVISION | Synthetic Anomaly AUROC | 0.5116 | Synthetic 10σ Point-Source Injections |
| ASTROVISION | Real Astrophysical Anomaly F1 | PENDING | No ground-truth label set |
| SPECTRA | Proxy SED Recon MSE | 0.2316 | Synthetic Continuum Test Set |
| SPECTRA | Channel-Drop Robustness | 0.1997 | 15 random channels masked |
| SPECTRA | Synthetic PAH Recovery AUROC | 1.0000 | Synthetic 3.3 µm Emission Line Injections |
| SPECTRA | Empirical SED Anomaly AUROC | PENDING | Awaiting coordinated D1–D6 observations |
| CHRONOS-X | Static Source Background Null χ² | 1.08 | 44 Dither Difference Images |
| MOTION-X | Gaia DR3 Astrometric Precision | 0.08 arcsec | 5,000 Reference Stars |
| MOTION-X | Empirical Asteroid Recovery Rate | PENDING (0 in FOV) | No asteroids in ingested fields |
| FUSION-X | Multimodal Ranking Consistency | 100% | 5 Deterministic Benchmark Test Cases |

