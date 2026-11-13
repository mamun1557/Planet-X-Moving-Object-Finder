# CHRONOS-X Demo Readiness Assessment & UI Boundary Specification

**Module:** CHRONOS-X — Multi-Epoch Temporal Anomaly Engine  
**Pipeline Build:** l2b-v27-2026-222  
**Parent Audits:** Task 1.3E, 1.3F, 1.3G, 1.3H, 1.3I, 1.3J  
**Assessment Date:** 2026-11-07  
**Governance Mode:** STRICT READ-ONLY SCIENTIFIC AUDIT  

---

## 1. Executive Summary & Verdict Selection

Based on the rigorous audit of the repository's mathematical codebase, local SPHEREx Level-2 FITS files, and candidate evaluation heuristics, the status of CHRONOS-X is determined as:

### Verdict: `LIMITED TEMPORAL CAPABILITY — SAFE FALLBACK VERIFIED`

#### Justification:
1. **Mathematical & CV Mechanics are Genuinely Implemented:** The core differencing engine in `models/chronos_x/model.py` (`ChronosTemporalDifferencer`) implements genuine astrometric reprojection (`reproject.reproject_interp`), SPHEREx fatal flag dilation (`FATAL_FLAG_MASK = 615`), combined variance propagation ($V_{\text{tot}} = V_1 + V_{2,\text{rep}}$), median background offset matching, and 5x5 stamp dipole vetoing.
2. **Zero Local Multi-Epoch Observations:** Local storage contains 171 science Level-2 FITS files spanning QR2 and QR3. All 599 overlapping image pairs are intra-visit dithers with separations of $2.15$ to $6.47$ minutes. There are exactly **zero multi-epoch repeat observations** ($\Delta t \ge 1\text{ day}$) on local disk.
3. **Severe Risk of False Transient Promotion if Ungated:** In `models/fusion/fusion_engine.py` (lines 315–319), any anomaly with $\text{significance} > 5.0\sigma$ lacking a Gaia counterpart is automatically classified as `NEW_TRANSIENT_OR_ASTEROID_CANDIDATE`. Feeding short-cadence dithers directly into this engine without a minimum temporal baseline filter creates fabricated transient discoveries.
4. **Feasibility of Safe Limited Demo:** CHRONOS-X can be safely and compellingly demonstrated if its operational scope is restricted to **Astrometric Registration & Noise Verification**, while all secular transient queries trigger an honest **Safe Fallback UI** (`TEMPORAL_DATA_UNAVAILABLE`).

---

## 2. Evaluation of Demo Outcome Scenarios

| Outcome | Assessment | Determination |
|---|---|---|
| **A. Real Multi-Epoch Demo Ready** | Requires verified independent observation epochs ($\Delta t \ge 1\text{ day}$), verified detector compatibility, and absence of fabrication risks. | **DISQUALIFIED.** No multi-epoch data exists locally. |
| **B. Limited Capability Demo Ready** | System demonstrates WCS alignment, dither discrimination, variance tracking, dipole rejection, and honest temporal fallback without claiming long-term variability. | **RECOMMENDED & VERIFIED.** Differencing mechanics are sound; safe boundaries prevent scientific fabrication. |
| **C. Not Demo Ready** | Unmitigated risk of presenting noise or intra-visit dithers as astrophysical transients, or inability to communicate missing data to users. | **AVOIDED.** Feasible under strict UI and API guardrails defined herein. |

---

## 3. Safe Frontend UI & Candidate Explorer Boundaries

To ensure scientific integrity during live demos, the React frontend and Co-Pilot Candidate Explorer must adhere to the following guardrails:

### 3.1 Status Badges & Nomenclature
The interface must never display an unqualified "Temporal Score" or "Transient Candidate" for local SPHEREx files. Instead, the UI must render explicit, mutually exclusive status badges:

1. `TEMPORAL_DATA_UNAVAILABLE` (Default for secular transient queries on local data):
   - **Visual Cue:** Neutral grey / slate badge.
   - **Tooltip / Drawer Copy:** *"No independent multi-epoch repeat observations exist in the local SPHEREx archive for this sky coordinate. Multi-epoch transient search requires remote IRSA archive retrieval (Weeks 31–32)."*
2. `TEMPORAL_NOT_ELIGIBLE` (For intra-visit dithers):
   - **Visual Cue:** Amber / warning badge.
   - **Tooltip / Drawer Copy:** *"Baseline $\Delta t = 2.15\text{–}6.47\text{ min}$ (intra-visit dither). Not eligible for secular astrophysical transient classification. Processed for astrometric registration and noise characterization only."*
3. `ASTROMETRIC_REGISTRATION_VERIFIED` (For successful dither difference):
   - **Visual Cue:** Cyan / technical badge.
   - **Display:** Shows difference image, residual histogram, and dipole rejection metrics without assigning a transient priority score.

### 3.2 Candidate Explorer Presentation
- **Prohibit Fused Ranking Promotion:** The candidate ranking table must not blend dither significance into the primary `fused_score` as if it were a transient indicator. In the demo mode, the temporal weight in `FusionEngine` ($w_{\text{chronos}} = 0.25$) should either be dynamically zeroed and renormalized across `spectra` (0.47) and `astrovision` (0.40), or marked with an asterisk indicating missing temporal modality.
- **Explainability Panel:** When inspecting a source, the Co-Pilot panel must explicitly show the temporal eligibility chain:
  - *Observation 1:* `OBSID: 0010_1D1` (MJD 60898.3411)
  - *Observation 2:* `OBSID: 0010_4D1` (MJD 60898.3456)
  - *Elapsed Baseline:* $6.47\text{ minutes}$ ($\Delta t < 1.0\text{ day}$)
  - *Eligibility Determination:* `INELIGIBLE_FOR_SECULAR_VARIABILITY`
  - *Astrometric Alignment:* RMS error $< 0.1\text{ pixel}$ (Reprojected via WCS)

---

## 4. Backend & API Contract Guardrails

Before running the demo server, the following API contracts must be enforced:

1. **Explicit Temporal Baseline Gate:**
   - Any API endpoint evaluating temporal pairs (`/api/chronos/difference` or batch evaluation) must require a metadata check:
     $$\Delta t = |\text{MJD}_2 - \text{MJD}_1| \ge 1.0\text{ day}$$
   - If $\Delta t < 1.0\text{ day}$, the API must set `is_temporal_eligible: false` and return `status: "INTRA_VISIT_DITHER"`.
2. **Zero Tolerance for Unflagged Synthetic Scores:**
   - The synthetic score generator in `models/fusion_x/rank_anomalies.py` must never be connected to the demo endpoint. If synthetic data is displayed, the API response must include `"score_type": "SYNTHETIC_BENCHMARK_SCORE"` and `"is_synthetic": true`.
3. **Cross-Detector Incompatibility Veto:**
   - Image pairs with differing `DETECTOR` header values (e.g., Det 1 vs Det 2 observing distinct passbands) must be rejected with `HTTP 422: Incompatible Spectral Channels`.

---

## 5. Recommended Live Demo Walkthrough

A compelling, scientifically rigorous demo script:

1. **Step 1: The Multi-Modal Challenge**  
   Explain that SPHEREx Level-2 images observe in scanning swathes with 2.15-minute intra-visit dithers.
2. **Step 2: Astrometric Registration & Dipole Vetoing**  
   Run `ChronosTemporalDifferencer` on Pointing 0010 dithers (Dither 1 vs Dither 4). Show the reprojected image, the variance-weighted difference map, and highlight how the 5x5 dipole veto correctly rejects astrometric misregistration spikes at star borders.
3. **Step 3: The Safe Fallback Principle**  
   Point out that despite high residual significance on certain pixel boundaries, the system **refuses to report a supernova or transient candidate** because the elapsed baseline is only 6.47 minutes (`TEMPORAL_NOT_ELIGIBLE`).
4. **Step 4: The Archive Discovery Roadmap**  
   Show the metadata manifest connecting Week 30 (local) to Weeks 31–32 (remote IRSA archive), illustrating how CHRONOS-X is architecturally prepared to ingest true multi-week repeat observations once retrieved from IPAC.

---

## 6. Conclusion
By strictly adhering to these boundaries, SPECTRA-X avoids scientific over-claiming and demonstrates enterprise-grade scientific safety, mathematical rigor, and trustworthy AI governance.

