# Artificial Intelligence & Machine Learning Disclosure

**Event:** NASA International Space Apps Challenge  
**Team:** VU_VioNux  
**Project:** SPECTRA-X  

---

## 1. Compliance Statement

In compliance with the official **NASA International Space Apps Challenge Rules** and open science guidelines, this document provides a full, transparent disclosure of all artificial intelligence, machine learning models, and automated coding assistants utilized in the conception, engineering, and execution of SPECTRA-X.

---

## 2. Machine Learning Models Embedded in the Product Architecture

The SPECTRA-X pipeline incorporates two specialized, offline-executable deep learning models designed specifically for infrared astronomical triage:

1. **ASTROVISION Spatial Anomaly Detector (`astrovision_spatial_v3.pt`):**
   - **Architecture:** Convolutional Neural Network (CNN) with 2D spatial feature extraction layers.
   - **Training Baseline:** Trained on astronomical cutouts from infrared survey pipelines to discriminate valid point-spread functions (PSFs) from cosmic rays, detector artifacts, and diffraction artifacts.
   - **Execution Mode:** Offline inference; fully embedded and deterministic.

2. **SPECTRA Masked Autoencoder (`spectra_masked_ae_v2.pt`):**
   - **Architecture:** 1D Transformer / Masked Autoencoder operating across 102 continuous spectral channels ($0.75–5.0\ \mu\text{m}$).
   - **Training Baseline:** Self-supervised reconstruction loss over synthetic and observed infrared spectrophotometric signatures.
   - **Execution Mode:** Offline inference; detects anomalous spectral deviations without external network calls.

3. **Deterministic Heuristic Models:**
   - **CHRONOS-X & MOTION-X:** Non-neural deterministic mathematical algorithms based on Astropy WCS coordinate transformations, spherical geometry, and flux variance analysis.

---

## 3. Generative AI & Developer Tools Used During Development

During the engineering, coding, and documentation process, the development team utilized generative AI assistants to accelerate software development:

| Tool / Assistant | Developer / Provider | Purpose & Role |
| :--- | :--- | :--- |
| **Google Gemini / Antigravity Agent** | Google / DeepMind | Architecture planning, rapid test suite authoring, automated code refactoring, Git configuration, and documentation drafting. |
| **OpenAI ChatGPT (GPT-4o)** | OpenAI | Brainstorming interface design patterns, assisting with React Tailwind component scaffolding, and reviewing LaTeX equations. |

### Human Authorship & Verification Notice
- All scientific logic, mathematical formulas, coordinate transformations, and astronomical safeguards were designed, verified, and audited by human team members.
- Every automated test (362 unit and integration tests) and end-to-end browser regression was executed and validated to ensure scientific integrity and functional correctness.
- No generative AI was used to fabricate scientific discoveries, synthetic moving objects, or astronomical claims.
