import React from 'react';
import { ArrowRight, CheckCircle2, Sparkles } from 'lucide-react';
import SkyVisualization from './SkyVisualization';
import ObjectSummaryCard from './ObjectSummaryCard';
import BlinkViewer from './BlinkViewer';
import SpectralViewer from './SpectralViewer';

/**
 * ExploreView component
 * Full-width stacked layout with 5 primary sections:
 * 1. Celestial Sky View — Field P0003
 * 2. High-Significance Transient (Target Summary & Astrometric Quantities)
 * 3. Interactive Optical Blink Comparator
 * 4. 102-Channel Infrared Spectrophotometry
 * 5. How Planet X Detects Moving Objects
 */
export default function ExploreView({
  candidates = [],
  totalCandidates = 1392,
  selectedCandidate = null,
  cutoutData = null,
  spectrumData = null,
  systemStatus = null,
  onSelectCandidate,
  onNavigate
}) {
  return (
    <div className="explore-view-wrapper">
      {/* Hero Heading Section */}
      <section className="explore-hero-section mb-6">
        <div className="hero-content">
          <div className="hero-badge">
            <Sparkles size={14} className="text-cyan mr-1.5" />
            <span>NASA Space Apps Challenge 2026 • SPHEREx Infrared Survey</span>
          </div>
          <h1 className="hero-heading">Find what moved in the sky.</h1>
          <p className="hero-explanation">
            Planet X detects moving objects and spectral transients across the changing infrared sky through calibrated NASA SPHEREx observations and multi-wavelength AI analysis.
          </p>
        </div>

        {/* Quick Analytical Bento Summary */}
        <div className="hero-summary-bento">
          <div className="bento-tile">
            <span className="bento-label">Sources Monitored</span>
            <span className="bento-value font-mono">12,480</span>
            <span className="bento-meta">Field P0003 Area</span>
          </div>
          <div className="bento-tile">
            <span className="bento-label">Detections Cataloged</span>
            <span className="bento-value font-mono text-cyan">{totalCandidates}</span>
            <span className="bento-meta">Multi-band Candidates</span>
          </div>
          <div className="bento-tile">
            <span className="bento-label">Spectral Channels</span>
            <span className="bento-value font-mono text-secondary">102</span>
            <span className="bento-meta">0.75 – 5.00 µm</span>
          </div>
          <div className="bento-tile">
            <span className="bento-label">Pipeline Latency</span>
            <span className="bento-value font-mono text-success">2.3s</span>
            <span className="bento-meta">Real-time Inference</span>
          </div>
        </div>
      </section>

      {/* Compact Status Row */}
      <div className="compact-status-row mb-6">
        <div className="status-item">
          <span className="status-label">Data Source:</span>
          <span className="status-val font-semibold">NASA SPHEREx Level-2 (Field P0003)</span>
          <span className="badge badge-demo ml-2">Sample Dataset</span>
        </div>
        <div className="status-divider" />
        <div className="status-item">
          <span className="status-label">Observation Timestamp:</span>
          <span className="status-val font-mono">2025-06-15 09:42:00 UTC</span>
        </div>
        <div className="status-divider" />
        <div className="status-item">
          <span className="status-label">Engine Status:</span>
          <span className="status-val text-success">
            <CheckCircle2 size={13} className="inline mr-1 text-success" />
            Nominal (CUDA Active)
          </span>
        </div>
      </div>

      {/* ============================================================
          DIV 1: Celestial Sky View — Field P0003 (Full-Width Div)
          ============================================================ */}
      <div className="explore-full-div mb-6" id="section-sky-view">
        <SkyVisualization
          candidates={candidates}
          selectedCandidate={selectedCandidate}
          onSelectCandidate={onSelectCandidate}
          onSwitchToList={() => onNavigate('OBJECTS')}
        />
      </div>

      {/* ============================================================
          DIV 2: High-Significance Transient (Full-Width Div)
          ============================================================ */}
      <div className="explore-full-div mb-6" id="section-transient-summary">
        <ObjectSummaryCard
          candidate={selectedCandidate}
          cutoutData={cutoutData}
          spectrumData={spectrumData}
          onOpenDetails={() => onNavigate('OBJECTS')}
          onOpenBlink={() => {
            const el = document.getElementById('section-blink-comparator');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }}
          onOpenReview={() => onNavigate('OBJECTS')}
        />
      </div>

      {/* ============================================================
          DIV 3: Interactive Optical Blink Comparator (Full-Width Div)
          ============================================================ */}
      <div className="explore-full-div mb-6" id="section-blink-comparator">
        <BlinkViewer
          cutoutData={cutoutData}
          candidate={selectedCandidate}
        />
      </div>

      {/* ============================================================
          DIV 4: 102-Channel Infrared Spectrophotometry (Full-Width Div)
          ============================================================ */}
      <div className="card explore-full-div mb-6" id="section-spectrophotometry">
        <div className="card-header-row">
          <div>
            <h3 className="card-title">102-Channel Infrared Spectrophotometry</h3>
            <p className="card-subtitle">
              Continuous 0.75 – 5.00 µm spectrophotometry vector extracted across 6 SPHEREx linear-variable filter arrays
            </p>
          </div>
          <div className="provenance-badges">
            <span className="badge badge-observed">Observed Flux (with σ errors)</span>
            <span className="badge badge-predicted">Masked AE Model Fit</span>
          </div>
        </div>
        <SpectralViewer
          spectrumData={spectrumData}
          candidate={selectedCandidate}
          compact={false}
        />
      </div>

      {/* ============================================================
          DIV 5: Methodology Callout Banner (Full-Width Div)
          ============================================================ */}
      <section className="card explore-full-div methodology-callout-banner mb-6" id="section-how-it-works">
        <div className="methodology-callout-inner">
          <div className="methodology-callout-text">
            <h3 className="card-title">How Planet X Detects Moving Objects</h3>
            <p className="card-subtitle">
              A transparent 4-stage scientific pipeline: <strong>Source</strong> (NASA SPHEREx L2 & Gaia DR3) → <strong>Retrieve</strong> (WCS cutouts & 102-ch SED) → <strong>Process</strong> (5-module AI inference) → <strong>Present</strong> (60 FPS blink comparator & human review).
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onNavigate('HOW_IT_WORKS')}
          >
            Read Full Methodology ↗
          </button>
        </div>
      </section>
    </div>
  );
}
