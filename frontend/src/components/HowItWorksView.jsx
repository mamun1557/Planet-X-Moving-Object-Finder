import React from 'react';
import { ExternalLink, Database, Cpu, Search, Eye, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';

/**
 * HowItWorksView component
 * Implements Section 4.4 of Planet X UI Documentation:
 * Comprehensive 4-step pipeline description: Source, Retrieve, Process, Present.
 */
export default function HowItWorksView() {
  return (
    <div className="how-it-works-view-container">
      {/* Page Title & Vision */}
      <section className="card mb-4">
        <div className="how-it-works-header">
          <div className="badge badge-surface mb-2">Scientific Methodology & Architecture</div>
          <h1 className="section-title">How Planet X Works</h1>
          <p className="section-subtitle max-w-3xl">
            Planet X uses a transparent 4-stage pipeline that ingests real NASA SPHEREx Level-2 multi-band infrared survey data, aligns celestial coordinates, detects anomalies through deep learning and statistical methods, and delivers evidence to researchers.
          </p>
        </div>
      </section>

      {/* 4-Step Pipeline Cards Grid */}
      <div className="pipeline-steps-grid">
        {/* Step 1: Source */}
        <div className="pipeline-step-card card">
          <div className="step-badge-num">1</div>
          <div className="step-icon-wrap">
            <Database size={24} className="text-cyan" />
          </div>
          <h2 className="step-heading">1. Source: NASA Datasets</h2>
          <p className="step-summary">
            Identify and stream authoritative astronomical survey products from the NASA IPAC Infrared Science Archive and ESA Gaia DR3.
          </p>

          <div className="step-details-box">
            <h4 className="detail-subhead">Data Sources Used:</h4>
            <ul className="detail-bullet-list">
              <li>
                <strong>NASA SPHEREx Level-2 Public Preview:</strong> Calibrated multi-epoch 2D intensity and variance FITS maps for Field P0003.
              </li>
              <li>
                <strong>ESA Gaia DR3 Cross-Match:</strong> High-precision optical astrometric positions used to verify known stationary stars.
              </li>
              <li>
                <strong>Wavelength Coverage:</strong> Continuous 0.75 to 5.00 µm across 6 linear-variable filter (LVF) detector arrays.
              </li>
            </ul>

            <div className="mt-3">
              <a
                href="https://irsa.ipac.caltech.edu/Missions/spherex.html"
                target="_blank"
                rel="noopener noreferrer"
                className="metric-link"
              >
                NASA IPAC SPHEREx Archive ↗
              </a>
            </div>
          </div>
        </div>

        {/* Step 2: Retrieve */}
        <div className="pipeline-step-card card">
          <div className="step-badge-num">2</div>
          <div className="step-icon-wrap">
            <Search size={24} className="text-secondary" />
          </div>
          <h2 className="step-heading">2. Retrieve: Ingestion & Extraction</h2>
          <p className="step-summary">
            Extract targeted celestial cutouts, apply astrometric World Coordinate System (WCS) reprojection, and compile 102-channel spectrophotometry.
          </p>

          <div className="step-details-box">
            <h4 className="detail-subhead">Data Extraction Methods:</h4>
            <ul className="detail-bullet-list">
              <li>
                <strong>Sub-Pixel WCS Alignment:</strong> Uses Astropy WCS to reproject multi-epoch exposures onto a shared pixel coordinate grid ($128 \times 128$ px).
              </li>
              <li>
                <strong>102-Channel SED Assembly:</strong> Photometric fluxes extracted across all 6 detector arrays, normalized, and paired with Poisson variance estimates.
              </li>
              <li>
                <strong>Multi-Epoch Tracking:</strong> Synchronizes Epoch 1 (Dither 1) and Epoch 2 (Dither 4) observations (Δt ≈ 5.0 min).
              </li>
            </ul>
          </div>
        </div>

        {/* Step 3: Process */}
        <div className="pipeline-step-card card">
          <div className="step-badge-num">3</div>
          <div className="step-icon-wrap">
            <Cpu size={24} className="text-info" />
          </div>
          <h2 className="step-heading">3. Process: Multi-Module AI Engine</h2>
          <p className="step-summary">
            A 5-module statistical and deep-learning engine analyzes spatial morphology, spectral anomalies, centroid shifts, and temporal governance.
          </p>

          <div className="step-details-box">
            <h4 className="detail-subhead">Detection Modules:</h4>
            <ul className="detail-bullet-list">
              <li>
                <strong>ASTROVISION:</strong> Convolutional mask-aware spatial autoencoder trained on deep-sky cutouts to flag morphology anomalies.
              </li>
              <li>
                <strong>SPECTRA:</strong> Masked spectral autoencoder calculating reconstruction residuals across the 102-channel SED curve.
              </li>
              <li>
                <strong>CHRONOS-X:</strong> Fail-closed temporal governor rejecting intra-visit dithers (Δt &lt; 10 min) to prevent false transient claims.
              </li>
              <li>
                <strong>MOTION-X:</strong> Sub-pixel centroid displacement and proper-motion velocity estimator.
              </li>
              <li>
                <strong>FUSION-X:</strong> Cross-modal heuristic consensus ranking prioritization.
              </li>
            </ul>
          </div>
        </div>

        {/* Step 4: Present */}
        <div className="pipeline-step-card card">
          <div className="step-badge-num">4</div>
          <div className="step-icon-wrap">
            <Eye size={24} className="text-success" />
          </div>
          <h2 className="step-heading">4. Present: Interactive Evidence</h2>
          <p className="step-summary">
            Transform scientific data into actionable visual evidence, interactive blink comparators, and human review audit trails.
          </p>

          <div className="step-details-box">
            <h4 className="detail-subhead">Scientific Tools:</h4>
            <ul className="detail-bullet-list">
              <li>
                <strong>60 FPS Blink Comparator:</strong> Toggles multi-epoch FITS cutouts with step-by-step frame controls.
              </li>
              <li>
                <strong>Difference & Significance Maps:</strong> Calibrated residual ΔI = E₂ - E₁ and Poisson significance σ = ΔI / √(σ₁² + σ₂²).
              </li>
              <li>
                <strong>SED Reconstruction Plots:</strong> Interactive observed data points plotted alongside PyTorch model predictions.
              </li>
              <li>
                <strong>Human-in-the-Loop Review:</strong> Persisted classification logs, exportable in JSON and CSV formats.
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Dataset & Processing Specifications Table */}
      <section className="card mt-4">
        <h3 className="section-title">Technical Specifications & Field Metadata</h3>
        <div className="specs-table-wrapper mt-3">
          <table className="specs-table">
            <thead>
              <tr>
                <th>Parameter</th>
                <th>Specification</th>
                <th>Scientific Meaning / Role</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="font-semibold text-cyan">Survey Field</td>
                <td className="font-mono">P0003 (Near NEP/SEP)</td>
                <td>Low-confusion calibration field observed across multiple dither passes.</td>
              </tr>
              <tr>
                <td className="font-semibold text-cyan">Spectral Channels</td>
                <td className="font-mono">102 bands (0.75 – 5.00 µm)</td>
                <td>Spectrophotometric resolving power R ≈ 35 to 130.</td>
              </tr>
              <tr>
                <td className="font-semibold text-cyan">Spatial Resolution</td>
                <td className="font-mono">6.2 arcsec / pixel</td>
                <td>SPHEREx native pixel scale across 2048×2048 focal plane arrays.</td>
              </tr>
              <tr>
                <td className="font-semibold text-cyan">Temporal Baseline</td>
                <td className="font-mono">Δt ≈ 5.0 minutes (intra-visit)</td>
                <td>Dither offset spacing between consecutive exposures in a single visit.</td>
              </tr>
              <tr>
                <td className="font-semibold text-cyan">Coordinate System</td>
                <td className="font-mono">ICRS / J2000 (RA, Dec)</td>
                <td>Standard astronomical equatorial celestial coordinates.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Known Limitations & Failure Modes (Section 4.4 & 12) */}
      <section className="card mt-4 border-amber">
        <div className="limitations-header">
          <AlertTriangle size={20} className="text-warning mr-2 flex-shrink-0" />
          <h3 className="section-title text-warning">Known Limitations & Scientific Failure Cases</h3>
        </div>
        <div className="limitations-body">
          <p className="text-sm text-secondary mb-3">
            In accordance with Planet X scientific trust rules (Section 12), all known technical limitations are openly documented:
          </p>
          <ul className="limitations-list">
            <li>
              <strong>Intra-Visit Dither Ambiguity:</strong> SPHEREx Level-2 public preview data for Field P0003 consists of intra-visit dithers (Δt ≈ 5.0 min). While this tests the differential motion detection pipeline, genuine solar system moving objects (e.g. Kuiper Belt Objects, Asteroids) require multi-day observation baselines to compute Keplerian orbital arcs.
            </li>
            <li>
              <strong>Bright Star PSF Wings:</strong> Saturated stars in the field produce diffraction spikes and point spread function (PSF) residuals that can mimic transient flux changes if unmasked.
            </li>
            <li>
              <strong>Single-Field Demo Scope:</strong> The current demonstration environment is scoped to Field P0003 (1,392 cataloged candidate sources). Full all-sky coverage requires processing the complete multi-terabyte SPHEREx data releases upon mission survey execution.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
