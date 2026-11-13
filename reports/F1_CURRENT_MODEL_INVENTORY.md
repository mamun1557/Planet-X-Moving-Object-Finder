# SPECTRA-X / F1: Current Model & Checkpoint Inventory

**Role:** Senior ML Engineer, Scientific Data Auditor, and Astronomical ML Research Engineer  
**Project:** SPECTRA-X / F1  
**Phase:** 1 — Repository & Checkpoint Forensic Audit  
**Execution Timestamp:** `2026-11-03T03:12:00+00:00`  
**Execution Environment:** Python 3.12, PyTorch 2.15.0+cu132 (NVIDIA GeForce RTX 5060, CUDA enabled)

---

## 1. Executive Summary

In strict compliance with Global Rule 9 ("Use actual repository files as the source of truth; never infer a checkpoint's existence from an old report"), we audited all potential checkpoint storage locations across the entire repository.

### Key Inventory Findings:
1. Exactly **three PyTorch checkpoint files** exist on disk, all located in `checkpoints/`.
2. Zero checkpoint files exist for **CHRONOS-X** (deterministic WCS differencer), **MOTION-X** (deterministic astrometric cross-matcher), or **FUSION-X** (heuristic rule-based ranker).
3. All three existing checkpoints load cleanly into their respective model classes in PyTorch.
4. The legacy checkpoint `spectra_latest.pt` (procedural proxy data) was preserved intact, while the retrained masked-channel autoencoder `spectra_masked_ae_v2.pt` (trained on real SPHEREx Level-2 photometry) is verified and operational.

---

## 2. Checkpoint Verification Matrix

| Checkpoint Name | Relative Path | Size (Bytes) | Size (KB) | Last Modified (UTC) | Architecture Class | Total Parameters | Loading Status | Training Data Source |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| `astrovision_latest.pt` | `checkpoints/astrovision_latest.pt` | 3,437,397 | 3,356.8 KB | `2026-11-02T04:01:27` | `AstroVisionAutoencoder` | 855,367 | **LOAD_SUCCESS** | 160 real image patches ($128 \times 128$) across 32 Level-2 files. |
| `spectra_latest.pt` | `checkpoints/spectra_latest.pt` | 100,805 | 98.4 KB | `2026-11-02T04:01:43` | `SpectralAnomalyDetector` | 23,798 | **LOAD_SUCCESS** | 500 procedural Planck synthetic curves (no real SPHEREx data). |
| `spectra_masked_ae_v2.pt` | `checkpoints/spectra_masked_ae_v2.pt` | 382,177 | 373.2 KB | `2026-11-03T01:14:16` | `MaskedSpectralAutoencoder` | 30,326 | **LOAD_SUCCESS** | 2,416 real SPHEREx Level-2 sources (Pointing 0001) with masked chi2 loss. |

---

## 3. Detailed Checkpoint Forensic Evidence

### 3.1 `checkpoints/astrovision_latest.pt`
- **Absolute Path**: `C:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X\checkpoints\astrovision_latest.pt`
- **File Size**: 3,437,397 bytes
- **File System MTime**: `2026-11-02T04:01:27.505350`
- **Container Structure**: Raw `state_dict` dictionary (18 tensor keys).
- **Architecture**: `models.astrovision.model.AstroVisionAutoencoder`
  * Encoder: 4 stages of `nn.Conv2d` with `nn.BatchNorm2d` and `LeakyReLU(0.2)`.
  * Decoder: 4 stages of `nn.ConvTranspose2d` with `nn.BatchNorm2d` and `ReLU`.
  * Input Channels: 1 ($128 \times 128$ infrared surface brightness map).
  * Latent Bottleneck: 128 dimensions ($8 \times 8 \times 128$).
- **Parameter Breakdown**:
  * Trainable weight and bias parameters: 854,465
  * Running mean and variance parameters in BatchNorm: 902
  * Total parameters stored: **855,367**
- **Architecture Compatibility Tests**:
  * `AstroVisionAutoencoder`: **LOAD_SUCCESS**
  * `SpectralAnomalyDetector`: `INCOMPATIBLE` (tensor dimension mismatch)
  * `MaskedSpectralAutoencoder`: `INCOMPATIBLE` (tensor dimension mismatch)
- **Scientific Audit Finding**:
  * In the earlier evaluation script `reports/second_pass_audit/task6_7_9_10_evaluation.py:36`, the script looked for `checkpoints/astrovision_spatial_ae.pt`. Because that exact filename did not exist, the evaluation script failed to load weights and tested an uninitialized random network. The actual trained weights reside in `astrovision_latest.pt`.

---

### 3.2 `checkpoints/spectra_latest.pt` (Legacy Proxy Model)
- **Absolute Path**: `C:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X\checkpoints\spectra_latest.pt`
- **File Size**: 100,805 bytes
- **File System MTime**: `2026-11-02T04:01:43.816300`
- **Container Structure**: Raw `state_dict` dictionary (12 tensor keys).
- **Architecture**: `models.spectra.model.SpectralAnomalyDetector`
  * Encoder: Linear(102, 64) $\rightarrow$ LayerNorm(64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 16).
  * Decoder: Linear(16, 64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 102).
  * Latent Bottleneck: 16 dimensions.
  * Total parameters: **23,798**.
- **Architecture Compatibility Tests**:
  * `AstroVisionAutoencoder`: `INCOMPATIBLE`
  * `SpectralAnomalyDetector`: **LOAD_SUCCESS**
  * `MaskedSpectralAutoencoder`: `INCOMPATIBLE` (input dimension is 102 vs 204)
- **Scientific Audit Finding**:
  * This model was trained on 500 procedural Planck function curves (`bb = (c1 / (wavelengths**5)) / (np.exp(c2 / (wavelengths * temp)) - 1.0)`). It did not ingest real SPHEREx Level-2 photometry. It is preserved strictly as a historical benchmark.

---

### 3.3 `checkpoints/spectra_masked_ae_v2.pt` (Retrained Masked Model)
- **Absolute Path**: `C:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X\checkpoints\spectra_masked_ae_v2.pt`
- **File Size**: 382,177 bytes
- **File System MTime**: `2026-11-03T01:14:16.673869`
- **Associated Metadata**: `checkpoints/spectra_masked_ae_v2_training_meta.json` (4,023 bytes)
- **Container Structure**: Nested dictionary containing:
  * `epoch`: 23 (best validation epoch out of 25)
  * `val_loss`: 0.00104405
  * `model_state_dict`: 12 tensor keys
  * `optimizer_state_dict`: AdamW optimizer state
  * `config`: Hyperparameter and dataset manifest dictionary
- **Architecture**: `models.spectra.train_masked_spectra.MaskedSpectralAutoencoder`
  * Input Channels: 204 (102 normalized flux channels + 102 boolean mask channels).
  * Encoder: Linear(204, 64) $\rightarrow$ LayerNorm(64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 16).
  * Decoder: Linear(16, 64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 64) $\rightarrow$ GELU $\rightarrow$ Linear(64, 102).
  * Latent Bottleneck: 16 dimensions.
  * Total parameters: **30,326**.
- **Architecture Compatibility Tests**:
  * `AstroVisionAutoencoder`: `INCOMPATIBLE`
  * `SpectralAnomalyDetector`: `INCOMPATIBLE`
  * `MaskedSpectralAutoencoder`: **LOAD_SUCCESS**
- **Training Provenance**:
  * Trained on CUDA (NVIDIA GeForce RTX 5060) in 8.62 seconds.
  * Training Set: 2,416 real sources from Pointing 0001 (QR2 & QR3 Wide, Detectors 1 & 2).
  * Validation Set: 1,249 real sources from Pointing 0004 (QR3 Deep, Detector 1).
  * Masked chi2 loss formulation with empirical $f_{\text{sys}} = 1.93\%$ systematic error floor.

---

## 4. Audit of Missing Checkpoints (CHRONOS-X, MOTION-X, FUSION-X)

A recursive scan across the entire workspace for model files (`*.pt`, `*.pth`, `*.bin`, `*.h5`, `*.joblib`, `*.pkl`, `*.onnx`) confirmed:

```
Found model/weight files:
- checkpoints\astrovision_latest.pt
- checkpoints\spectra_latest.pt
- checkpoints\spectra_masked_ae_v2.pt
```

### Forensic Determination:

1. **CHRONOS-X (`checkpoints/chronos_*.pt`)**:
   - **Status**: **NOT APPLICABLE / DOES NOT EXIST**
   - **Evidence**: `models/chronos_x/model.py` defines `ChronosTemporalDifferencer`. It is a pure mathematical algorithm utilizing Astropy WCS reprojection, morphological dilation, and variance differencing. No neural network weights are used or saved.
2. **MOTION-X (`checkpoints/motion_*.pt`)**:
   - **Status**: **NOT APPLICABLE / DOES NOT EXIST**
   - **Evidence**: `models/motion_x/model.py` defines `MotionXValidator`. It is an astrometric coordinate matching class querying Gaia DR3 coordinates and JPL Horizons tables. It does not contain an ML model.
3. **FUSION-X (`checkpoints/fusion_*.pt`)**:
   - **Status**: **NOT AVAILABLE / UNTRAINED**
   - **Evidence**: `models/fusion_x/model.py` defines `FusionRanker` (a small 3-layer MLP) and `classify_candidate` (heuristic rule tree). In `rank_anomalies.py`, `FusionRanker` is instantiated with randomly initialized weights and has never undergone supervised training. No trained weights file exists on disk.

---

## 5. Summary Conclusion

The repository contains exactly three valid neural network checkpoints. Two are active production/development models (`astrovision_latest.pt` and `spectra_masked_ae_v2.pt`), while one is a preserved historical baseline (`spectra_latest.pt`). Claims in any legacy report that CHRONOS-X, MOTION-X, or FUSION-X have trained ML checkpoints are scientifically inaccurate; their current implementations are classical analytical pipelines or heuristic decision trees.
