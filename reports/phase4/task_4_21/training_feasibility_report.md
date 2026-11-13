# SPECTRA-X / F1 — Phase 4, Task 4.21
# Model Selection & Training Feasibility Assessment Report

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Evaluation Candidates:** ASTROVISION V3 vs. SPECTRA V2  
**Audit Date:** November 9, 2026  
**Final Phase B Decision:** **`SELECT_SPECTRA_FOR_EXPERIMENTAL_TRIAL`**  

---

## 1. Executive Summary & Selection Mandate

In strict accordance with **Phase B** of the Task 4.21 directive, both trained neural network modules—**ASTROVISION** (spatial autoencoder) and **SPECTRA** (masked spectrophotometric autoencoder)—were rigorously audited across all eight required criteria to select at most ONE primary candidate for controlled experimental training.

---

## 2. Comprehensive Eight-Criterion Comparative Assessment

| Selection Criterion | ASTROVISION V3 Spatial Autoencoder | SPECTRA V2 Masked Spectral Autoencoder | Primary Candidate Evaluation |
| :--- | :--- | :--- | :--- |
| **1. Current Baseline Metrics** | Point AUROC = 0.8040; Extended AUROC = 0.7064; FPR = 9.00% (2.20% with catalog masking). | Line Anomaly AUROC = 0.9995; Benchmark AUROC = 0.9398; Test loss $\chi^2 = 0.000365$. | Both models possess strong baseline performance. SPECTRA is near saturation. |
| **2. Existing Training Data** | 1,200 non-overlapping $128 \times 128$ patches from 35 Level-2 science files. | 2,416 real 102-channel spectra from Pointing 0001; 1,249 validation from Pointing 0004. | ASTROVISION trained on image patches; SPECTRA on extracted 1D spectrophotometry. |
| **3. New Data Availability** | **ZERO new unobserved Level-2 science files exist** outside quarantined cohorts. | **5,084 additional valid spectra exist in Pointing 0001** (`phase3_multpointing_spectra_v1.csv`). | **ADVANTAGE: SPECTRA** (Additional extracted spectra exist). |
| **4. Label Availability & Reliability** | Zero real anomaly labels; synthetic spatial injections only. | 371 controlled synthetic injection instances (lines, troughs, spikes, excess, controls). | Both models rely on synthetic anomaly benchmarks for quantitative AUROC evaluation. |
| **5. Distribution Compatibility** | Receptive-field sensitivity to image background and pixel scale ($6.2''/\text{px}$). | Exact 102-channel wavelength grid ($0.75 - 5.00\text{ \mu m}$) across all Level-2 spectra. | **ADVANTAGE: SPECTRA** (102-channel spectrophotometry has zero spatial domain shift). |
| **6. Expected Training Cost** | High: GPU patch extraction, normalizer computation, 15+ epochs (~15-20 min). | Extremely Low: 1D PyTorch DataLoader, 30 epochs completes in **< 10 seconds** on RTX 5060. | **ADVANTAGE: SPECTRA** (Fast, reproducible training cycle). |
| **7. Risk of Degradation** | **EXTREME:** Retraining risks breaking the delicate partial convolution weights and increasing FPR. | **LOW-TO-MODERATE:** Well-conditioned 1D autoencoder; masked loss prevents artifact propagation. | **ADVANTAGE: SPECTRA** (Significantly lower risk of catastrophic forgetting). |
| **8. Independent Evaluation Feasibility** | Evaluation pointings P0002, P0009, P0010 are quarantined. | Pointing 0003 ($N=1,392$ sources) is an **untouched independent test set** outside P0001 and P0004. | **ADVANTAGE: SPECTRA** (Clean independent test set P0003 available). |

---

## 3. Phase B Selection Verdict

1. **ASTROVISION Disqualification:**  
   ASTROVISION is categorically disqualified from retraining because zero new unobserved Level-2 science files exist outside the quarantined calibration and evaluation cohorts, and retraining carries an unacceptably high risk of degrading spatial anomaly detection.
2. **SPECTRA Selection:**  
   **SPECTRA** is selected as the single primary candidate for the final pre-freeze experimental trial. It possesses 5,084 additional valid spectra in Pointing 0001, exact 102-channel distribution compatibility, an isolated independent test set (Pointing 0003, $N=1,392$ sources), and a rapid, reproducible training cycle.