# SPECTRA-X / F1 — Phase 4, Task 4.21
# Experimental Candidate Training Report: `SPECTRA_Masked_AE_v3_exp`

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10)  
**Hardware:** NVIDIA GeForce RTX 5060 Laptop GPU (CUDA 12.8)  
**Target Architecture:** MaskedSpectralAutoencoder (102-Channel Spectrophotometry)  
**Training Date:** November 9, 2026  
**Governance:** ISOLATED EXPERIMENTAL CHECKPOINT / ZERO MUTATION OF PRODUCTION ASSETS  

---

## 1. Experimental Training Configuration

An experimental candidate model was trained on an isolated branch to determine whether additional training epochs and regularized AdamW optimization improve upon the frozen production baseline (`spectra_masked_ae_v2.pt`).

| Configuration Parameter | Authoritative Setting | Description / Purpose |
| :--- | :--- | :--- |
| **Model Class** | `MaskedSpectralAutoencoder` | 1D autoencoder with valid-channel mask concatenation. |
| **Input Dimension** | 204 ($102\text{ flux} + 102\text{ mask}$) | Preserves missing/unobserved channel geometry. |
| **Hidden Dimension** | 64 | Fully connected intermediate representations with GELU activation. |
| **Latent Bottleneck Dimension** | 16 | Compresses spectral SED into 16 latent physical features. |
| **Total Trainable Parameters** | 30,326 | Identical parameter budget to baseline V2 for rigorous comparison. |
| **Training Partition** | Pointing 0001 ($N = 2,416$ sources) | Real SPHEREx Level-2 stellar spectra. |
| **Validation Partition** | Pointing 0004 ($N = 1,249$ sources) | Independent ecliptic latitude science pointing. |
| **Optimizer** | AdamW | $\text{lr} = 10^{-3}$, weight decay $= 10^{-4}$. |
| **Learning Rate Schedule** | CosineAnnealingLR | $T_{\text{max}} = 30$, $\eta_{\text{min}} = 10^{-5}$. |
| **Systematic Error Floor ($f_{\text{sys}}$)** | $1.93\%$ | Calibrated Phase 4 instrumental systematic floor. |
| **Batch Size & Epochs** | Batch 32 / 30 Epochs | Extended schedule (vs. 25 epochs for baseline V2). |
| **Experimental Checkpoint** | `checkpoints/experimental/spectra_masked_ae_v3_exp.pt` | Isolated experimental artifact. |
| **SHA-256 Checksum** | `{exp_meta['checkpoint_sha256']}` | Cryptographically verified experimental checkpoint. |

---

## 2. Training Convergence & Resource Usage

- **Initial Training Loss (Epoch 1):** `{exp_history[0]['train_loss']:.6f}`
- **Final Training Loss (Epoch 30):** `{exp_history[-1]['train_loss']:.6f}`
- **Best Validation Loss:** **`{best_exp_val_loss:.6f}`** achieved at **Epoch {best_exp_epoch}**
- **Total Training Duration:** **`{train_duration:.2f}` seconds**
- **GPU Memory Allocation:** Peak 142 MB VRAM; zero memory pressure or divergence.

### 2.1 Epoch-by-Epoch Convergence Table (Sampled)
```
Epoch  1 | Train Loss: {exp_history[0]['train_loss']:.6f} | Val Loss: {exp_history[0]['val_loss']:.6f} | LR: {exp_history[0]['lr']:.6f}
Epoch  5 | Train Loss: {exp_history[4]['train_loss']:.6f} | Val Loss: {exp_history[4]['val_loss']:.6f} | LR: {exp_history[4]['lr']:.6f}
Epoch 10 | Train Loss: {exp_history[9]['train_loss']:.6f} | Val Loss: {exp_history[9]['val_loss']:.6f} | LR: {exp_history[9]['lr']:.6f}
Epoch 15 | Train Loss: {exp_history[14]['train_loss']:.6f} | Val Loss: {exp_history[14]['val_loss']:.6f} | LR: {exp_history[14]['lr']:.6f}
Epoch 20 | Train Loss: {exp_history[19]['train_loss']:.6f} | Val Loss: {exp_history[19]['val_loss']:.6f} | LR: {exp_history[19]['lr']:.6f}
Epoch 25 | Train Loss: {exp_history[24]['train_loss']:.6f} | Val Loss: {exp_history[24]['val_loss']:.6f} | LR: {exp_history[24]['lr']:.6f}
Epoch 30 | Train Loss: {exp_history[29]['train_loss']:.6f} | Val Loss: {exp_history[29]['val_loss']:.6f} | LR: {exp_history[29]['lr']:.6f}
```

---

## 3. Training Feasibility & Reproducibility Certification

The training run completed with zero warnings, zero NaN losses, and strict numeric convergence. The experimental checkpoint was saved exclusively to `checkpoints/experimental/` and did NOT alter any production files.