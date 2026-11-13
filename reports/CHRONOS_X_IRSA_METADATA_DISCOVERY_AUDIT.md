# Authoritative SPHEREx Archive Metadata Discovery & NEP Revisit Search
## Phase 3, Task 1.3H — IRSA SIA2 Metadata Discovery & Temporal Evidence Audit Report

**Execution Status:** COMPLETED  
**Task Type:** READ-ONLY OFFICIAL ARCHIVE METADATA DISCOVERY & SCIENTIFIC AUDIT  
**Module:** CHRONOS-X — Multi-Epoch Temporal Anomaly Engine  
**Parent Audits:** Task 1.3E, Task 1.3F, Task 1.3G  
**Primary Archive Endpoint:** NASA/IPAC Infrared Science Archive (IRSA) Simple Image Access v2 (`https://irsa.ipac.caltech.edu/SIA?`)  
**Target Collections:** `spherex_qr3` (Wide Survey), `spherex_qr3_deep` (Deep Survey), `spherex_qr2` (Investigation)  
**Governance Standard:** Zero FITS download / Zero network bypass / Zero scientific asset modification  
**Date:** 2026-11-07  

---

### Executive Verdict

```
+-------------------------------------------------------------------------------+
|                             FINAL AUDIT VERDICT:                              |
|               ARCHIVE QUERY FAILED — NEP REVISITS REMAIN UNVERIFIED           |
|                                                                               |
|  1. IRSA SIA2 Query Outcome:                                                  |
|     Official HTTP SIA2 queries to https://irsa.ipac.caltech.edu/SIA failed    |
|     with URLError: [Errno 11001] getaddrinfo failed due to environment        |
|     sandbox network isolation. In strict accordance with Section 2 governance |
|     rules, querying terminated immediately without network bypass attempts.    |
|                                                                               |
|  2. Revisit Verification Status:                                              |
|     Zero metadata records were retrieved from the remote archive. The         |
|     previously hypothesized 7-, 14-, and 18-day NEP revisit baselines across   |
|     QR3 Weeks 31 and 32 remain UNVERIFIABLE candidates.                       |
|                                                                               |
|  3. CHRONOS-X Temporal Eligibility:                                           |
|     TEMPORAL_ELIGIBLE = FALSE across all 281 evaluated pairs. Exactly zero     |
|     pairs meet Tier E4 or possess a valid multi-epoch temporal baseline.     |
+-------------------------------------------------------------------------------+
```

---

## 1. Mission Objectives & Authorized Scope

The mission of Task 1.3H was to execute an independent, read-only metadata discovery audit against the official NASA/IPAC Infrared Science Archive (IRSA) Simple Image Access (SIAv2) service. The specific objective was to search the `spherex_qr3` (Wide Survey) and `spherex_qr3_deep` (Deep Survey) collections to determine whether observations taken during Planning Periods `2026W31` and `2026W32` cover the North Ecliptic Pole (NEP) reference region observed locally in `2026W30_1B_0010`.

### Non-Negotiable Governance Directives:
- Query only documented public IRSA SIAv2 endpoints.
- Retrieve metadata only; do not follow `access_url` or `cloud_access` links.
- Download zero binary FITS, cutout, mosaic, or preview products.
- Do not bypass DNS, firewall, or sandbox boundaries.
- If the endpoint is unreachable, document the exact error and stop remote querying immediately.
- Never manufacture or assume unreturned archive metadata.

---

## 2. Authoritative Archive Interface & Query Specification

The query protocol strictly followed the official NASA/IPAC SPHEREx Archive Data Access documentation ([caltech-ipac.github.io/spherex-archive-documentation](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/)).

### Service Specification:
- **Base Service Endpoint:** `https://irsa.ipac.caltech.edu/SIA`
- **Protocol:** IVOA Simple Image Access Version 2.0 (SIAv2)
- **Primary Collections:**
  - `spherex_qr3`: SPHEREx Quick Release 3 Wide Survey Level-2 Images
  - `spherex_qr3_deep`: SPHEREx Quick Release 3 Deep Survey Level-2 Images
  - `spherex_qr2`: SPHEREx Quick Release 2 Wide Survey (Investigative collection)

### Query Parameters Constructed:
1. **Positional Constraint (`POS`):**
   - Centered on the North Ecliptic Pole: $\alpha = 270.0000^\circ, \delta = +66.5607^\circ$.
   - Search Radius: $5.0^\circ$ circular cone (`POS=CIRCLE+270.0+66.56+5.0`).
   - This conservative cone encompasses the entire $3.5^\circ \times 3.5^\circ$ SPHEREx focal plane across all six detectors and dither offsets.
2. **Temporal Constraint (`TIME`):**
   - Target Planning Periods: Weeks 31 and 32 (nominal interval: July 27, 2026 to August 10, 2026 UTC).
   - Parameter: `TIME=2026-07-27/2026-08-10`.
3. **Format & Response Constraints:**
   - `FORMAT=image/fits`
   - `RESPONSEFORMAT=votable`

---

## 3. Week 30 Reference Region Parameters

The reference celestial region was authoritatively derived from the 24 local Level-2 science FITS files in [`data/spherex/multipointing_pilot/level2/0010/`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/data/spherex/multipointing_pilot/level2/0010/):

### Table 3.1: Authoritative Week 30 Reference Field Parameters

| Parameter | Verified Reference Value | Source / Methodology |
| :--- | :--- | :--- |
| **Observation Set** | `2026W30_1B_0010_1D1` through `4D6` (24 files) | Intact Level-2 FITS files on local disk |
| **Observation Epoch (UTC)** | `2026-07-20T01:20:41.531` to `01:27:08.323` | FITS `IMAGE` header `DATE-OBS` |
| **Observation Epoch (MJD)** | `61241.056036` to `61241.060513` | FITS `IMAGE` header `MJD-OBS` |
| **Coordinate System** | ICRS J2000 (`RADESYS = 'ICRS'`) | FITS primary and WCS headers |
| **Mean Focal-Plane Center** | $\alpha = 272.9433^\circ, \quad \delta = +66.5712^\circ$ | WCS `pixel_to_world_values` midpoint |
| **Central Detector (D2, D5) Center** | $\alpha = 273.048^\circ, \quad \delta = +66.573^\circ$ | Central detector footprint midpoint |
| **Recalculated Ecliptic Latitude ($\beta$)** | **$\beta = +88.788^\circ$ (Central D2, D5); $+85.94^\circ \text{ to } +85.98^\circ$ (Outer)** | Barycentric True Ecliptic ($\epsilon = 23.439291^\circ$) |
| **Angular Distance to North Ecliptic Pole** | **$1.212^\circ$ (Central D2, D5); $3.088^\circ$ (Focal-plane mean)** | Spherical distance to $(\alpha=270^\circ, \delta=+66.5607^\circ)$ |
| **Continuous Viewing Zone Status** | **CONFIRMED** | Within SPHEREx Continuous Viewing Zone ($|\beta| \ge 66.5^\circ$) |

---

## 4. SIA2 Metadata Discovery Execution & Query Results

Systematic HTTP queries were executed against the official IRSA SIAv2 service in standard sandbox execution mode.

### Table 4.1: IRSA SIA2 Query Log Summary

| Query ID | Target Collection | Parameter String | Execution Timestamp (UTC) | HTTP Status | Error Type & Root Cause | Records Retrieved | Query Result |
| :--- | :---: | :--- | :---: | :---: | :--- | :---: | :---: |
| `IRSA_SIA2_QR3_WIDE` | `spherex_qr3` | `COLLECTION=spherex_qr3&POS=CIRCLE+270.0+66.56+5.0&TIME=2026-07-27/2026-08-10` | 2026-11-07T07:21:06Z | `None` | `URLError: [Errno 11001] getaddrinfo failed` | **0** | **FAILED** |
| `IRSA_SIA2_QR3_DEEP` | `spherex_qr3_deep` | `COLLECTION=spherex_qr3_deep&POS=CIRCLE+270.0+66.56+5.0&TIME=2026-07-27/2026-08-10` | 2026-11-07T07:21:06Z | `None` | `URLError: [Errno 11001] getaddrinfo failed` | **0** | **FAILED** |
| `IRSA_SIA2_QR2_WIDE` | `spherex_qr2` | `COLLECTION=spherex_qr2&POS=CIRCLE+270.0+66.56+5.0&TIME=2025-04-20/2025-05-20` | 2026-11-07T07:21:06Z | `None` | `URLError: [Errno 11001] getaddrinfo failed` | **0** | **FAILED** |

### 4.1 Root Cause Analysis of Endpoint Failure
- **Error:** `URLError: [Errno 11001] getaddrinfo failed`
- **Mechanism:** The execution environment operates under standard sandbox isolation, which enforces complete outbound network isolation (WAN blocked, external DNS lookup disabled).
- **Governance Compliance:** Section 2 of the task specification mandates:
  > *"If the endpoint is unreachable, record the exact error and stop remote querying. Do not attempt alternate routes to evade a failed connection."*
  In strict compliance, querying was terminated immediately. No proxy tunneling, credential spoofing, or unsanctioned routing was attempted.
- **Query Log Deliverable:** Full JSON query parameters, timestamps, and error responses were serialized to [`reports/CHRONOS_X_IRSA_QUERY_LOG.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/CHRONOS_X_IRSA_QUERY_LOG.json).

---

## 5. Candidate Metadata Catalog & Baseline Evaluation

Because the remote SIA2 endpoint was unreachable and no cached VOTable responses exist locally, all candidate revisit observations were compiled into [`reports/CHRONOS_X_IRSA_METADATA_CANDIDATES.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/CHRONOS_X_IRSA_METADATA_CANDIDATES.csv) based on authoritative repository records:

### Table 5.1: IRSA Metadata Candidates Census

| Candidate ID | Target Collection | Planning Period | Target Region | Nominal Baseline | Query Status | Records Retrieved | Evidence Tier | Temporal Eligible | Audit Limitation Reason |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `IRSA_CAND_0001` | `spherex_qr3` | `2026W31_1B` | NEP / CVZ | $\approx 7\text{ days}$ | `FAILED_UNREACHABLE` | 0 | `UNVERIFIABLE` | `FALSE` | Endpoint unreachable; zero metadata records retrieved. |
| `IRSA_CAND_0002` | `spherex_qr3` | `2026W31_2A` | NEP / CVZ | $\approx 10.5\text{ days}$ | `FAILED_UNREACHABLE` | 0 | `UNVERIFIABLE` | `FALSE` | Endpoint unreachable; zero metadata records retrieved. |
| `IRSA_CAND_0003` | `spherex_qr3` | `2026W32_1A` | NEP / CVZ | $\approx 14\text{ days}$ | `FAILED_UNREACHABLE` | 0 | `UNVERIFIABLE` | `FALSE` | Endpoint unreachable; zero metadata records retrieved. |
| `IRSA_CAND_0004` | `spherex_qr3_deep` | `2026W31_W32` | NEP / CVZ | $\approx 18\text{ days}$ | `FAILED_UNREACHABLE` | 0 | `UNVERIFIABLE` | `FALSE` | Deep survey query unreachable; zero metadata records retrieved. |
| `IRSA_CAND_0005` | `spherex_qr2` | `2025W19_2B` | Pointing 0010 | $\approx 434\text{ days}$ | `FAILED_UNREACHABLE` | 0 | `E0` | `FALSE` | Manifest row exists in `spherex_inventory.csv`; FITS unavailable locally; build incompatible. |

---

## 6. Corrected Evidence Hierarchy & Independent Temporal Eligibility

In accordance with Task 1.3G guidelines, evidence completeness (cumulative tiers E0–E4) and independent temporal eligibility (`TEMPORAL_ELIGIBLE`) are evaluated as **separate, orthogonal axes**:

### 6.1 Cumulative vs Exclusive Evidence Hierarchy Census (281 Pairs)
All 281 canonical pairs from the repository universe were evaluated in [`reports/CHRONOS_X_IRSA_REVISIT_EVIDENCE_LEDGER.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/CHRONOS_X_IRSA_REVISIT_EVIDENCE_LEDGER.csv):

### Table 6.1: Evidence Hierarchy Census Across Reconciled Ledger

| Tier | Tier Definition | Cumulative Count (Tier or Better) | Exclusive Count (Highest Tier Only) | Physical Membership |
| :---: | :--- | :---: | :---: | :--- |
| **E0** | Archive / manifest candidate exists | **277** | **1** | 276 local Week 30 pairs + 1 remote QR2 candidate |
| **E1** | Exact observation timestamps verified | **276** | **240** | 240 cross-detector concurrent pairs ($\Delta t \le 6.45\text{ min}$) |
| **E2** | E1 + same detector + compatible spectral band | **36** | **0** | All 36 advance to E3; 0 stop at E2 |
| **E3** | E2 + actual WCS footprint overlap verified | **36** | **36** | 36 same-detector intra-visit dither pairs ($f_{overlap} \ge 82.5\%$) |
| **E4** | E3 + calibration/uncertainty + multi-epoch | **0** | **0** | **Zero pairs meet Tier E4** |
| **< E0** | Unverifiable (Hypothesized candidates) | — | **4** | Hypothesized multi-week candidates with no manifest record |
| **Total** | — | — | **281** | **Fully Reconciled Universe** |

### 6.2 Independent Temporal Eligibility Axis (`TEMPORAL_ELIGIBLE`)
Under Section 10 rules, multi-epoch baseline separation is evaluated independently of Tier E4:
- **`TEMPORAL_ELIGIBLE = TRUE`:** **0 pairs.**
- **`TEMPORAL_ELIGIBLE = FALSE`:** **281 pairs (100%).**
  - **36 Dither Pairs:** Disqualified because baseline is intra-visit dither ($\Delta t = 2.15 - 6.45\text{ minutes} < 1\text{ hour}$). Sub-visit dithers measure detector flat-fielding and sub-pixel registration, providing zero sensitivity to astronomical transient or secular variability.
  - **240 Cross-Detector Pairs:** Disqualified because exposures are concurrent stares across disjoint spectral passbands.
  - **4 Hypothesized Multi-Week Pairs:** Disqualified because IRSA query failed; zero observation timestamps or records retrieved.
  - **1 Remote QR2 Candidate:** Disqualified because FITS file is unavailable locally and pipeline calibration builds diverge (`l2b-v20-2025-247` vs `l2b-v27-2026-222`).

---

## 7. QR2 Remote Candidate Investigation (`2025W19_2B_0010`)

The remote QR2 Pointing 0010 candidate was independently audited:
1. **Archive Status:** Cataloged in [`manifests/spherex_inventory.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/manifests/spherex_inventory.csv) as four Level-2 FITS files (`level2_2025W19_2B_0010_1D1_spx_l2b-v20-2025-247.fits` to `4D1`).
2. **Local Availability:** **None.** These files reside exclusively in the remote AWS S3 bucket.
3. **IRSA SIA Query:** Unreachable due to sandbox isolation.
4. **Calibration Divergence:** Processed under QR2 pipeline build `l2b-v20-2025-247`, which has incompatible gain calibrations and background subtractions relative to QR3 build `l2b-v27-2026-222`.
5. **Verdict:** Remains at Evidence Tier **E0**, with `TEMPORAL_ELIGIBLE = FALSE`. It offers no scientifically compatible comparison for CHRONOS-X temporal evaluation without full re-processing under build `v27`.

---

## 8. Direct Answers to the 15 Required Final Questions

1. **Did the official QR3 SIA2 metadata query succeed?**  
   **NO.** The query failed with `URLError: [Errno 11001] getaddrinfo failed` due to sandbox network isolation.
2. **How many records were returned from QR3 Wide?**  
   **0 records.**
3. **How many records were returned from QR3 Deep?**  
   **0 records.**
4. **Were the query results complete or truncated?**  
   The query did not execute remotely; zero records were returned.
5. **Are any Week 31 records mapped to the Week 30 NEP reference region?**  
   **NO.** No records were retrieved or mapped.
6. **Are any Week 32 records mapped to the Week 30 NEP reference region?**  
   **NO.** No records were retrieved or mapped.
7. **What are the exact observation IDs and timestamps?**  
   Observation IDs and timestamps for Weeks 31 and 32 are **UNRESOLVED / UNVERIFIABLE**.
8. **Are the 7-, 14- or 18-day baselines supported?**  
   **NO.** None are supported by archive metadata.
9. **Are any observations same-detector and spectrally compatible?**  
   **UNVERIFIED** for Weeks 31 and 32. (Verified only for local Week 30 intra-visit dithers).
10. **Is actual footprint overlap verified or only metadata-level candidate overlap?**  
    Footprint overlap for all candidate revisits remains **`CANDIDATE_ONLY — ACTUAL WCS OVERLAP NOT VERIFIED`**.
11. **Are calibration and quality metadata available?**  
    **NO** for Weeks 31 and 32.
12. **Does any pair reach E4?**  
    **NO.** Exactly 0 pairs reach Tier E4.
13. **Does any pair satisfy independent temporal eligibility?**  
    **NO.** `TEMPORAL_ELIGIBLE = FALSE` for 100% of the 281 evaluated pairs.
14. **Does the remote QR2 candidate offer any scientifically compatible comparison?**  
    **NO.** Calibration build divergence (`v20-2025-247` vs `v27-2026-222`) and absence of local FITS preclude compatible scientific comparison.
15. **What is the next exact evidence requirement before FITS acquisition?**  
    Authorized, network-enabled query of the IRSA SIAv2 endpoint outside the sandbox (or provision of cached VOTable query responses) to retrieve the official observation IDs, exact UTC timestamps, and footprint coordinates for SPHEREx NEP pointings in Weeks 31 and 32.

---

## 9. Deliverables & Cryptographic Integrity Ledger

All deliverables of Task 1.3H have been authored, validated, and placed in the project repository:

1. **Audit Report (this document):**  
   [`reports/CHRONOS_X_IRSA_METADATA_DISCOVERY_AUDIT.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/CHRONOS_X_IRSA_METADATA_DISCOVERY_AUDIT.md)
2. **Metadata Candidates Manifest (CSV):**  
   [`reports/CHRONOS_X_IRSA_METADATA_CANDIDATES.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/CHRONOS_X_IRSA_METADATA_CANDIDATES.csv)  
   *(SHA-256: `c8300276d49dd772e258661642878bf077eeb09a8eb71d2b0e6328a6fcf74619`)*
3. **Query Log Summary (JSON):**  
   [`reports/CHRONOS_X_IRSA_QUERY_LOG.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/CHRONOS_X_IRSA_QUERY_LOG.json)  
   *(SHA-256: `955d5aa61db4e3d3ddda7752e399c735d49603b5443fa7a57a1b07297e6443d3`)*
4. **Revisit Evidence Ledger (CSV):**  
   [`reports/CHRONOS_X_IRSA_REVISIT_EVIDENCE_LEDGER.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/CHRONOS_X_IRSA_REVISIT_EVIDENCE_LEDGER.csv)  
   *(SHA-256: `c00d41eb3fa15664177ee8e3b2e7960fa77cf2fcda0e0f85eb3d15ff1b5d63f0`)*

#### Protected Asset Verification:
- Model Checkpoint [`checkpoints/spectra_masked_ae_v2.pt`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/checkpoints/spectra_masked_ae_v2.pt): `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938` (**UNTOUCHED**)
- Calibration Thresholds [`data/processed/spectra/spectra_v2_provisional_thresholds_v1.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/data/processed/spectra/spectra_v2_provisional_thresholds_v1.json): `d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848` (**UNTOUCHED**)

---

## 10. Final Governance Verification & Verdict

In strict compliance with governance directives:
- Only official public IRSA SIAv2 endpoints were queried.
- No FITS files, cutouts, mosaics, or preview images were downloaded.
- No `access_url` or `cloud_access` destinations were accessed.
- No network sandbox boundaries were bypassed.
- No source manifests or historical audit reports were modified.
- No model, checkpoint, threshold, or calibration asset was modified.
- No candidate was promoted beyond its evidence-supported tier.
- All output cryptographic hashes were computed successfully.

**Final Scientific Verdict:**  
`ARCHIVE QUERY FAILED — NEP REVISITS REMAIN UNVERIFIED`

