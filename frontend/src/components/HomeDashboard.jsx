import React, { useState, useEffect, useMemo } from 'react';
import {
  Sparkles,
  ArrowRight,
  Star,
  Crosshair,
  CheckCircle2,
  Clock,
  Maximize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ShieldCheck,
  ChevronRight,
  Trophy,
  Info,
  Check,
  FileText,
  Share2,
  Eye,
  Layers,
  Activity,
  Compass
} from 'lucide-react';

/**
 * HomeDashboard Component
 * Faithful implementation of the SPECTRA-X reference observatory design:
 * - Top Hero Card with SPHEREx satellite in space
 * - Analysis Summary 2x2 grid with live telemetry
 * - 4-Panel Scientific Grid: Astronomical View, SED, AI Evidence, Candidate Score
 * - Bottom Tabbed Analysis Station: Key Findings, Observation Info, Environment Ready, and Export Actions
 */
export default function HomeDashboard({
  candidate = null,
  cutoutData = null,
  spectrumData = null,
  onNavigate,
  onAddToReview,
  onExportReport
}) {
  const [activeBottomTab, setActiveBottomTab] = useState('DETAILS');
  const [zoomLevel, setZoomLevel] = useState(2.0);
  const [copiedLink, setCopiedLink] = useState(false);

  // Fallback candidate matching reference mockup if none loaded yet
  const currentTarget = candidate || {
    id: 'SPX-J163.6309-69.4422',
    designation: 'SPX-J163.6309-69.4422',
    ra: 283.724,
    dec: -1.832,
    date: '2025-06-15',
    instrument: 'SPHEREx',
    candidate_score: 0.87,
    priority: 'High Priority',
    astrovision_score: 0.89,
    spectra_score: 0.92,
    chronos_score: 0.78,
    motion_score: 0.71,
    fusion_score: 0.87
  };

  const handleShareDemo = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2500);
    }
  };

  // Generate synthetic smooth curve & observed spectrophotometry for SED plot
  const sedPoints = useMemo(() => {
    // 14 representative bands from 0.75 to 5.0 um matching reference image
    const wavelengths = [0.75, 0.90, 1.05, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00, 3.50, 4.00, 4.50, 5.00];
    return wavelengths.map((wl) => {
      // Planck-like thermal / stellar emission peak around 1.6 um
      const modelFlux = Math.max(0.1, 1.2 * Math.exp(-Math.pow((wl - 1.6) / 1.3, 2)) + (5.0 - wl) * 0.05);
      const observedFlux = modelFlux + (Math.sin(wl * 7.5) * 0.04) - 0.02;
      return {
        wl,
        modelFlux: Number(modelFlux.toFixed(3)),
        observedFlux: Number(observedFlux.toFixed(3))
      };
    });
  }, [currentTarget.id]);

  return (
    <div className="spectra-home-dashboard" role="main">
      {/* =========================================================================
          TOP ROW: Hero Banner + Analysis Summary Bento
          ========================================================================= */}
      <section className="dashboard-top-row">
        {/* Welcome / Hero Banner */}
        <div className="hero-banner-card">
          <div className="hero-banner-text">
            <div className="hero-pill-badge">
              <Sparkles size={14} className="sparkle-icon" />
              <span>Welcome to SPECTRA-X</span>
            </div>
            <h1 className="hero-title">
              Discover the Unseen <br />
              in the Infrared Sky
            </h1>
            <p className="hero-description">
              Powered by real NASA SPHEREx observations and advanced AI analysis.
            </p>
            <button
              className="hero-cta-btn"
              onClick={() => onNavigate('EXPLORER')}
              aria-label="Explore Candidates"
            >
              <span>Explore Candidates</span>
              <ArrowRight size={16} className="cta-arrow" />
            </button>
          </div>

          {/* SPHEREx Satellite & Deep Space Illustration */}
          <div className="hero-satellite-art" aria-hidden="true">
            <svg viewBox="0 0 340 220" className="hero-space-svg">
              <defs>
                <radialGradient id="nebulaGlow" cx="65%" cy="35%" r="60%">
                  <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.45" />
                  <stop offset="45%" stopColor="#3B82F6" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#070B18" stopOpacity="0" />
                </radialGradient>
                <linearGradient id="earthHorizon" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.9" />
                  <stop offset="25%" stopColor="#0284C7" stopOpacity="0.7" />
                  <stop offset="70%" stopColor="#0B132B" stopOpacity="0.95" />
                  <stop offset="100%" stopColor="#050814" stopOpacity="1" />
                </linearGradient>
                <linearGradient id="shieldGold" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#FDE68A" />
                  <stop offset="40%" stopColor="#F59E0B" />
                  <stop offset="100%" stopColor="#78350F" />
                </linearGradient>
                <linearGradient id="carbonBody" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#475569" />
                  <stop offset="60%" stopColor="#1E293B" />
                  <stop offset="100%" stopColor="#0F172A" />
                </linearGradient>
              </defs>

              {/* Cosmic Nebula Glow */}
              <rect x="0" y="0" width="340" height="220" fill="url(#nebulaGlow)" />

              {/* Starfield */}
              <circle cx="45" cy="40" r="1.2" fill="#E2E8F0" opacity="0.8" />
              <circle cx="120" cy="25" r="1.5" fill="#FFFFFF" opacity="0.9" />
              <circle cx="85" cy="75" r="1.0" fill="#93C5FD" opacity="0.7" />
              <circle cx="210" cy="30" r="1.2" fill="#FFFFFF" opacity="0.85" />
              <circle cx="295" cy="50" r="1.6" fill="#FDE68A" opacity="0.8" />
              <circle cx="265" cy="85" r="1.0" fill="#C4B5FD" opacity="0.6" />
              <circle cx="160" cy="95" r="0.8" fill="#FFFFFF" opacity="0.5" />

              {/* Earth Limb & Atmospheric Aura */}
              <path
                d="M -20,240 Q 150,150 360,240 L 360,250 L -20,250 Z"
                fill="url(#earthHorizon)"
              />
              <path
                d="M -20,240 Q 150,150 360,240"
                fill="none"
                stroke="#67E8F9"
                strokeWidth="2"
                opacity="0.8"
              />

              {/* SPHEREx Spacecraft 3D Perspective Vector Rendering */}
              <g transform="translate(145, 15) scale(0.95)">
                {/* Stepped Conical V-Groove Thermal Shields */}
                {/* Outer Cone */}
                <polygon
                  points="110,40 155,10 135,75 80,60"
                  fill="url(#carbonBody)"
                  stroke="#64748B"
                  strokeWidth="1.2"
                />
                {/* Middle Thermal Radiator */}
                <polygon
                  points="102,48 138,25 125,72 85,62"
                  fill="#334155"
                  stroke="#475569"
                  strokeWidth="0.8"
                />
                {/* Inner Telescope Aperture / Gold Cavity */}
                <polygon
                  points="94,54 122,38 114,68 88,62"
                  fill="url(#shieldGold)"
                  stroke="#FBBF24"
                  strokeWidth="0.8"
                />
                {/* Primary Mirror / Optical Core */}
                <ellipse cx="104" cy="56" rx="10" ry="6" fill="#1E1B4B" stroke="#60A5FA" strokeWidth="1" />
                <circle cx="104" cy="56" r="2.5" fill="#38BDF8" />

                {/* Service Module & Electronics Bus */}
                <polygon
                  points="65,70 88,62 82,92 58,98"
                  fill="#1E293B"
                  stroke="#475569"
                  strokeWidth="1"
                />
                {/* Solar Array Wing (Left) */}
                <polygon
                  points="35,80 58,74 52,104 28,108"
                  fill="#1D4ED8"
                  stroke="#60A5FA"
                  strokeWidth="0.8"
                />
                <line x1="32" y1="94" x2="55" y2="88" stroke="#93C5FD" strokeWidth="0.6" />

                {/* Star Tracker & Communications Dish */}
                <circle cx="68" cy="85" r="3.5" fill="#94A3B8" />
                <line x1="68" y1="85" x2="62" y2="92" stroke="#CBD5E1" strokeWidth="1" />
              </g>
            </svg>
          </div>
        </div>

        {/* Analysis Summary (2x2 Grid) */}
        <div className="analysis-summary-card">
          <div className="summary-header">
            <h2 className="summary-title">Analysis Summary</h2>
            <div className="live-pill-badge">
              <span className="live-pulse-dot"></span>
              <span>Live</span>
            </div>
          </div>

          <div className="summary-metrics-grid">
            {/* Metric 1 */}
            <div className="metric-box">
              <div className="metric-icon-wrap violet">
                <Star size={18} />
              </div>
              <div className="metric-data">
                <div className="metric-value font-mono">12,480</div>
                <div className="metric-label">Sources Analyzed</div>
              </div>
            </div>

            {/* Metric 2 */}
            <div className="metric-box">
              <div className="metric-icon-wrap cyan">
                <Crosshair size={18} />
              </div>
              <div className="metric-data">
                <div className="metric-value font-mono text-cyan">47</div>
                <div className="metric-label">Candidates Found</div>
              </div>
            </div>

            {/* Metric 3 */}
            <div className="metric-box">
              <div className="metric-icon-wrap emerald">
                <CheckCircle2 size={18} />
              </div>
              <div className="metric-data">
                <div className="metric-value font-mono text-emerald">6</div>
                <div className="metric-label">Reviewed</div>
              </div>
            </div>

            {/* Metric 4 */}
            <div className="metric-box">
              <div className="metric-icon-wrap amber">
                <Clock size={18} />
              </div>
              <div className="metric-data">
                <div className="metric-value font-mono text-amber">2.3s</div>
                <div className="metric-label">Avg. Response</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          MIDDLE ROW: 4-Card Scientific Grid
          ========================================================================= */}
      <section className="dashboard-scientific-grid">
        {/* Card 1: Astronomical View */}
        <div className="sci-card astronomical-view-card">
          <div className="sci-card-header">
            <div className="header-left">
              <Compass size={17} className="card-icon text-cyan" />
              <h3 className="card-title">Astronomical View</h3>
            </div>
            <div className="header-controls">
              <button
                className="zoom-btn"
                onClick={() => setZoomLevel((z) => Math.min(4.0, z + 0.5))}
                title="Zoom In"
              >
                <ZoomIn size={14} />
              </button>
              <button
                className="zoom-btn"
                onClick={() => setZoomLevel((z) => Math.max(1.0, z - 0.5))}
                title="Zoom Out"
              >
                <ZoomOut size={14} />
              </button>
              <button
                className="zoom-btn"
                onClick={() => setZoomLevel(2.0)}
                title="Reset View"
              >
                <RotateCcw size={14} />
              </button>
              <button
                className="zoom-btn"
                onClick={() => onNavigate('BLINK')}
                title="Full Screen Blink"
              >
                <Maximize2 size={14} />
              </button>
              <span className="fits-badge font-mono">FITS • {zoomLevel.toFixed(1)}x</span>
            </div>
          </div>

          <div className="astro-canvas-wrap">
            <svg
              viewBox="0 0 300 220"
              className="astro-canvas-svg"
              style={{ transform: `scale(${zoomLevel / 2.0})`, transformOrigin: 'center' }}
            >
              <defs>
                {/* Calibrated Infrared False Color Heatmap Gradient */}
                <radialGradient id="starCoreGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#FFFFFF" />
                  <stop offset="15%" stopColor="#FDE047" />
                  <stop offset="35%" stopColor="#EA580C" />
                  <stop offset="65%" stopColor="#9333EA" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#0B132B" stopOpacity="0" />
                </radialGradient>
                <radialGradient id="faintCore" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#93C5FD" />
                  <stop offset="40%" stopColor="#3B82F6" stopOpacity="0.7" />
                  <stop offset="100%" stopColor="#0B132B" stopOpacity="0" />
                </radialGradient>
              </defs>

              {/* Dark Sky Canvas Background with Faint Dust Noise */}
              <rect x="0" y="0" width="300" height="220" fill="#060914" />

              {/* Coordinate Grid Lines */}
              <g stroke="#1E293B" strokeWidth="0.6" strokeDasharray="3 3">
                <line x1="50" y1="0" x2="50" y2="220" />
                <line x1="100" y1="0" x2="100" y2="220" />
                <line x1="150" y1="0" x2="150" y2="220" />
                <line x1="200" y1="0" x2="200" y2="220" />
                <line x1="250" y1="0" x2="250" y2="220" />
                <line x1="0" y1="45" x2="300" y2="45" />
                <line x1="0" y1="95" x2="300" y2="95" />
                <line x1="0" y1="145" x2="300" y2="145" />
                <line x1="0" y1="195" x2="300" y2="195" />
              </g>

              {/* Ambient Field Stars */}
              <circle cx="35" cy="80" r="2.5" fill="url(#faintCore)" />
              <circle cx="85" cy="30" r="2.0" fill="url(#faintCore)" />
              <circle cx="70" cy="170" r="2.8" fill="url(#faintCore)" />
              <circle cx="215" cy="40" r="3.2" fill="url(#faintCore)" />
              <circle cx="240" cy="180" r="2.2" fill="url(#faintCore)" />
              <circle cx="265" cy="110" r="3.0" fill="url(#faintCore)" />
              <circle cx="120" cy="190" r="2.0" fill="url(#faintCore)" />
              <circle cx="190" cy="165" r="2.5" fill="url(#faintCore)" />

              {/* Primary High-Significance Target Infrared Transient (Center) */}
              <circle cx="150" cy="110" r="55" fill="url(#starCoreGlow)" />
              <circle cx="150" cy="110" r="8" fill="#FFFFFF" />

              {/* Telescope Diffraction Spikes */}
              <line x1="90" y1="110" x2="210" y2="110" stroke="#FDE047" strokeWidth="1.2" opacity="0.85" />
              <line x1="150" y1="50" x2="150" y2="170" stroke="#FDE047" strokeWidth="1.2" opacity="0.85" />

              {/* Target Reticle Crosshair */}
              <circle
                cx="150"
                cy="110"
                r="18"
                fill="none"
                stroke="#38BDF8"
                strokeWidth="1.2"
                strokeDasharray="4 2"
              />
            </svg>
            <div className="canvas-coords-overlay font-mono">
              RA: {currentTarget.ra}° • Dec: {currentTarget.dec}°
            </div>
          </div>
        </div>

        {/* Card 2: Spectral Energy Distribution */}
        <div className="sci-card sed-view-card">
          <div className="sci-card-header">
            <div className="header-left">
              <Activity size={17} className="card-icon text-secondary" />
              <h3 className="card-title">Spectral Energy Distribution</h3>
            </div>
            <div className="sed-legend">
              <span className="legend-item">
                <span className="legend-dot blue"></span>
                <span>Observed</span>
              </span>
              <span className="legend-item">
                <span className="legend-dot orange"></span>
                <span>Model</span>
              </span>
            </div>
          </div>

          <div className="sed-chart-wrap">
            <svg viewBox="0 0 320 180" className="sed-chart-svg">
              {/* Chart Grid Lines */}
              <g stroke="#1E293B" strokeWidth="0.6">
                <line x1="45" y1="20" x2="305" y2="20" />
                <line x1="45" y1="55" x2="305" y2="55" />
                <line x1="45" y1="90" x2="305" y2="90" />
                <line x1="45" y1="125" x2="305" y2="125" />
                <line x1="45" y1="145" x2="305" y2="145" />

                <line x1="45" y1="20" x2="45" y2="145" />
                <line x1="90" y1="20" x2="90" y2="145" />
                <line x1="140" y1="20" x2="140" y2="145" />
                <line x1="190" y1="20" x2="190" y2="145" />
                <line x1="240" y1="20" x2="240" y2="145" />
                <line x1="285" y1="20" x2="285" y2="145" />
                <line x1="305" y1="20" x2="305" y2="145" />
              </g>

              {/* Y-Axis Labels (Flux a.u.) */}
              <text x="38" y="24" fill="#64748B" fontSize="9" textAnchor="end" fontFamily="JetBrains Mono">1.5</text>
              <text x="38" y="59" fill="#64748B" fontSize="9" textAnchor="end" fontFamily="JetBrains Mono">1.0</text>
              <text x="38" y="94" fill="#64748B" fontSize="9" textAnchor="end" fontFamily="JetBrains Mono">0.5</text>
              <text x="38" y="148" fill="#64748B" fontSize="9" textAnchor="end" fontFamily="JetBrains Mono">0.0</text>
              <text x="14" y="85" fill="#94A3B8" fontSize="9" textAnchor="middle" transform="rotate(-90 14 85)" fontFamily="Inter">
                Flux (a.u.)
              </text>

              {/* X-Axis Labels (Wavelength um) */}
              <text x="45" y="162" fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">0.75</text>
              <text x="90" y="162" fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">1.0</text>
              <text x="140" y="162" fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">1.5</text>
              <text x="190" y="162" fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">2.0</text>
              <text x="240" y="162" fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">3.0</text>
              <text x="285" y="162" fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">4.0</text>
              <text x="305" y="162" fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">5.0</text>
              <text x="175" y="176" fill="#94A3B8" fontSize="9" textAnchor="middle" fontFamily="Inter">
                Wavelength (µm)
              </text>

              {/* Model Synthetic Curve (Orange Smooth Spline) */}
              <path
                d="M 45,130 C 70,110 90,80 140,48 C 170,42 195,50 230,75 C 265,98 290,115 305,120"
                fill="none"
                stroke="#F59E0B"
                strokeWidth="2.2"
              />

              {/* Model Sample Dots */}
              <circle cx="100" cy="72" r="3.5" fill="#F59E0B" />
              <circle cx="140" cy="48" r="3.5" fill="#F59E0B" />
              <circle cx="160" cy="44" r="3.5" fill="#F59E0B" />
              <circle cx="190" cy="52" r="3.5" fill="#F59E0B" />
              <circle cx="230" cy="75" r="3.5" fill="#F59E0B" />
              <circle cx="265" cy="98" r="3.5" fill="#F59E0B" />

              {/* Observed Points (Cyan/Blue with error bars) */}
              <g stroke="#38BDF8" strokeWidth="1.8" fill="#38BDF8">
                {/* 0.75 um */}
                <line x1="45" y1="120" x2="45" y2="140" strokeWidth="1.2" />
                <circle cx="45" cy="130" r="3" />

                {/* 1.0 um */}
                <line x1="90" y1="80" x2="90" y2="98" strokeWidth="1.2" />
                <circle cx="90" cy="89" r="3" />

                {/* 1.25 um */}
                <line x1="118" y1="60" x2="118" y2="76" strokeWidth="1.2" />
                <circle cx="118" cy="68" r="3" />

                {/* 1.5 um */}
                <line x1="145" y1="42" x2="145" y2="58" strokeWidth="1.2" />
                <circle cx="145" cy="50" r="3" />

                {/* Connecting blue line between observed */}
                <polyline
                  points="45,130 90,89 118,68 145,50 175,54 210,68 250,88 285,110 305,122"
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="1.6"
                />

                <circle cx="175" cy="54" r="3" />
                <circle cx="210" cy="68" r="3" />
                <circle cx="250" cy="88" r="3" />
                <circle cx="285" cy="110" r="3" />
                <circle cx="305" cy="122" r="3" />
              </g>
            </svg>
          </div>
        </div>

        {/* Card 3: AI Evidence */}
        <div className="sci-card ai-evidence-card">
          <div className="sci-card-header">
            <div className="header-left">
              <ShieldCheck size={17} className="card-icon text-emerald" />
              <h3 className="card-title">AI Evidence</h3>
            </div>
            <button
              className="view-details-link"
              onClick={() => onNavigate('EVIDENCE')}
            >
              <span>View Details</span>
              <ChevronRight size={14} />
            </button>
          </div>

          <div className="ai-modules-list">
            {/* ASTROVISION */}
            <div className="ai-module-row">
              <div className="module-info">
                <div className="module-badge-icon emerald">
                  <span className="dot"></span>
                </div>
                <div>
                  <div className="module-name">ASTROVISION</div>
                  <div className="module-desc">Spatial Anomaly</div>
                </div>
              </div>
              <div className="module-score-pill emerald font-mono">
                {currentTarget.astrovision_score.toFixed(2)}
              </div>
            </div>

            {/* SPECTRA */}
            <div className="ai-module-row">
              <div className="module-info">
                <div className="module-badge-icon secondary">
                  <span className="dot"></span>
                </div>
                <div>
                  <div className="module-name">SPECTRA</div>
                  <div className="module-desc">Spectral Signal</div>
                </div>
              </div>
              <div className="module-score-pill emerald font-mono">
                {currentTarget.spectra_score.toFixed(2)}
              </div>
            </div>

            {/* CHRONOS-X */}
            <div className="ai-module-row">
              <div className="module-info">
                <div className="module-badge-icon amber">
                  <span className="dot"></span>
                </div>
                <div>
                  <div className="module-name">CHRONOS-X</div>
                  <div className="module-desc">Temporal Evidence</div>
                </div>
              </div>
              <div className="module-score-pill emerald font-mono">
                {currentTarget.chronos_score.toFixed(2)}
              </div>
            </div>

            {/* MOTION-X */}
            <div className="ai-module-row">
              <div className="module-info">
                <div className="module-badge-icon cyan">
                  <span className="dot"></span>
                </div>
                <div>
                  <div className="module-name">MOTION-X</div>
                  <div className="module-desc">Motion Analysis</div>
                </div>
              </div>
              <div className="module-score-pill amber font-mono">
                {currentTarget.motion_score.toFixed(2)}
              </div>
            </div>

            {/* FUSION-X */}
            <div className="ai-module-row">
              <div className="module-info">
                <div className="module-badge-icon emerald">
                  <span className="dot"></span>
                </div>
                <div>
                  <div className="module-name">FUSION-X</div>
                  <div className="module-desc">Priority Score</div>
                </div>
              </div>
              <div className="module-score-pill violet font-mono">
                {currentTarget.fusion_score.toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        {/* Card 4: Candidate Score Card */}
        <div className="sci-card candidate-score-card">
          <div className="score-glow-orb" aria-hidden="true"></div>

          <div className="trophy-badge-wrap">
            <Trophy size={28} className="trophy-icon" />
          </div>

          <div className="score-title">Candidate Score</div>
          <div className="score-number font-mono">{currentTarget.candidate_score.toFixed(2)}</div>

          <div className="priority-badge">
            <span>{currentTarget.priority}</span>
          </div>

          <p className="score-subtext">
            A promising candidate for further investigation.
          </p>

          <button
            className="add-to-review-btn"
            onClick={() => onAddToReview(currentTarget)}
          >
            <span>Add to Review</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </section>

      {/* =========================================================================
          BOTTOM ROW: Tabbed Detail & Telemetry Station
          ========================================================================= */}
      <section className="dashboard-bottom-section">
        {/* Main Details Panel */}
        <div className="details-panel-card">
          {/* Sub Navigation Tabs */}
          <div className="panel-tab-bar" role="tablist">
            <button
              className={`panel-tab-btn ${activeBottomTab === 'DETAILS' ? 'active' : ''}`}
              onClick={() => setActiveBottomTab('DETAILS')}
              role="tab"
              aria-selected={activeBottomTab === 'DETAILS'}
            >
              Analysis Details
            </button>
            <button
              className={`panel-tab-btn ${activeBottomTab === 'BLINK' ? 'active' : ''}`}
              onClick={() => onNavigate('BLINK')}
              role="tab"
              aria-selected={activeBottomTab === 'BLINK'}
            >
              Blink Observatory
            </button>
            <button
              className={`panel-tab-btn ${activeBottomTab === 'DIFFERENCE' ? 'active' : ''}`}
              onClick={() => onNavigate('DIFFERENCE')}
              role="tab"
              aria-selected={activeBottomTab === 'DIFFERENCE'}
            >
              Difference View
            </button>
            <button
              className={`panel-tab-btn ${activeBottomTab === 'NOTES' ? 'active' : ''}`}
              onClick={() => onNavigate('REVIEW')}
              role="tab"
              aria-selected={activeBottomTab === 'NOTES'}
            >
              Review Notes
            </button>
          </div>

          {/* Active Tab Body: Analysis Details */}
          <div className="panel-tab-content">
            <div className="details-columns-grid">
              {/* Key Findings */}
              <div className="findings-column">
                <div className="findings-header">
                  <div className="findings-info-icon">
                    <Info size={15} />
                  </div>
                  <span className="findings-title">Key Findings</span>
                </div>

                <ul className="findings-list">
                  <li className="finding-item">
                    <Check size={15} className="check-icon" />
                    <span>Unusual spectral signature detected in 102-channel data</span>
                  </li>
                  <li className="finding-item">
                    <Check size={15} className="check-icon" />
                    <span>No significant motion detected</span>
                  </li>
                  <li className="finding-item">
                    <Check size={15} className="check-icon" />
                    <span>Strong cross-match with Gaia catalog</span>
                  </li>
                </ul>
              </div>

              {/* Observation Info */}
              <div className="observation-info-column">
                <div className="obs-header-title">Observation Info</div>
                <div className="obs-data-grid">
                  <div className="obs-row">
                    <span className="obs-key">RA:</span>
                    <span className="obs-val font-mono">{currentTarget.ra}°</span>
                  </div>
                  <div className="obs-row">
                    <span className="obs-key">Dec:</span>
                    <span className="obs-val font-mono">{currentTarget.dec}°</span>
                  </div>
                  <div className="obs-row">
                    <span className="obs-key">Date:</span>
                    <span className="obs-val font-mono">{currentTarget.date}</span>
                  </div>
                  <div className="obs-row">
                    <span className="obs-key">Instrument:</span>
                    <span className="obs-val font-mono">{currentTarget.instrument}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Corner Telemetry & Actions Card */}
        <div className="environment-actions-card">
          <div className="env-status-wrap">
            <div className="env-status-header">
              <div className="env-check-icon">
                <CheckCircle2 size={16} />
              </div>
              <div className="env-title">Environment Ready</div>
            </div>
            <div className="env-meta font-mono">Python 3.12 • CUDA Support</div>
            {/* Health Bar */}
            <div className="env-progress-bar">
              <div className="progress-fill"></div>
            </div>
          </div>

          <div className="export-action-buttons">
            <button
              className="export-btn secondary"
              onClick={() => onExportReport(currentTarget)}
              title="Export Full Investigation Dossier (PDF / CSV)"
            >
              <FileText size={15} />
              <span>Export Report</span>
            </button>
            <button
              className="export-btn primary"
              onClick={handleShareDemo}
              title="Share Observatory Link"
            >
              <Share2 size={15} />
              <span>{copiedLink ? 'Copied!' : 'Share Demo'}</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
