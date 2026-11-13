import React, { useState } from 'react';
import { LineChart, Zap, ShieldAlert, Sparkles, Filter, CheckCircle2 } from 'lucide-react';

export default function SpectralViewer({ spectrumData, candidate }) {
  const [showReconstruction, setShowReconstruction] = useState(true);
  const [showErrorBars, setShowErrorBars] = useState(true);
  const [hoveredPoint, setHoveredPoint] = useState(null);

  if (!spectrumData || spectrumData.status !== 'SUCCESS') {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
        <p>Select a candidate to view the 102-channel SPHEREx spectrophotometry SED.</p>
      </div>
    );
  }

  const d = spectrumData.data;
  const wavelengths = d.wavelengths_um || [];
  const obsFlux = d.observed_flux || [];
  const reconFlux = d.reconstructed_flux || [];
  const errors = d.flux_errors || [];
  const maskedIdx = new Set(d.masked_indices || []);
  const metrics = d.metrics || {};
  const sidecar = d.sidecar_excess || {};

  // Compute SVG plotting bounds
  const minW = Math.min(...wavelengths, 0.75);
  const maxW = Math.max(...wavelengths, 5.00);

  const validFluxes = obsFlux.filter((f) => Number.isFinite(f));
  const minF = Math.min(0, Math.min(...validFluxes));
  const maxF = Math.max(1.2, Math.max(...validFluxes, ...(reconFlux.filter(Number.isFinite))));

  const svgWidth = 800;
  const svgHeight = 320;
  const padding = { top: 20, right: 30, bottom: 45, left: 55 };
  const plotW = svgWidth - padding.left - padding.right;
  const plotH = svgHeight - padding.top - padding.bottom;

  const toX = (w) => padding.left + ((w - minW) / (maxW - minW)) * plotW;
  const toY = (f) => padding.top + plotH - ((f - minF) / (maxF - minF)) * plotH;

  // Build SVG paths
  const obsPoints = wavelengths.map((w, i) => ({
    x: toX(w),
    y: toY(obsFlux[i]),
    errY1: toY(obsFlux[i] + (errors[i] || 0.05)),
    errY2: toY(obsFlux[i] - (errors[i] || 0.05)),
    w,
    f: obsFlux[i],
    rf: reconFlux[i],
    err: errors[i],
    isMasked: maskedIdx.has(i),
    idx: i
  }));

  const obsPathD = obsPoints
    .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(' ');

  const reconPathD = wavelengths
    .map((w, i) => `${i === 0 ? 'M' : 'L'} ${toX(w).toFixed(1)} ${toY(reconFlux[i]).toFixed(1)}`)
    .join(' ');

  // SPHEREx Bands definitions
  const bands = [
    { label: 'Band 1', min: 0.75, max: 1.11, color: 'rgba(56, 189, 248, 0.06)' },
    { label: 'Band 2', min: 1.11, max: 1.64, color: 'rgba(99, 102, 241, 0.06)' },
    { label: 'Band 3', min: 1.64, max: 2.42, color: 'rgba(168, 85, 247, 0.06)' },
    { label: 'Band 4', min: 2.42, max: 3.82, color: 'rgba(236, 72, 153, 0.06)' },
    { label: 'Band 5', min: 3.82, max: 4.42, color: 'rgba(245, 158, 11, 0.06)' },
    { label: 'Band 6', min: 4.42, max: 5.00, color: 'rgba(16, 185, 129, 0.06)' },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">
            <LineChart size={18} color="#38bdf8" />
            <span>102-Channel SPHEREx Spectrophotometric SED (0.75 – 5.00 μm)</span>
          </div>
          <div className="card-subtitle font-mono">
            Candidate: {candidate?.candidate_id} | Linear Variable Filter (LVF) Assembled SED
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className={`btn ${showReconstruction ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setShowReconstruction(!showReconstruction)}
            title="Toggle Masked Spectral Autoencoder Reconstruction"
          >
            <Sparkles size={14} />
            <span>SPECTRA AE Fit</span>
          </button>

          <button
            className={`btn ${showErrorBars ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setShowErrorBars(!showErrorBars)}
            title="Toggle Photometric Error Bars"
          >
            <span>Error Bars</span>
          </button>
        </div>
      </div>

      {/* SVG Interactive Chart */}
      <div className="sed-chart-container">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: '100%', height: '100%' }}>
          {/* Band regions */}
          {bands.map((b, i) => {
            const bx1 = toX(b.min);
            const bx2 = toX(b.max);
            return (
              <g key={i}>
                <rect
                  x={bx1}
                  y={padding.top}
                  width={bx2 - bx1}
                  height={plotH}
                  fill={b.color}
                />
                <text
                  x={bx1 + (bx2 - bx1) / 2}
                  y={padding.top + 12}
                  fill="#64748b"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  {b.label}
                </text>
              </g>
            );
          })}

          {/* Grid lines */}
          {[1.0, 2.0, 3.0, 4.0, 5.0].map((w) => (
            <line
              key={w}
              x1={toX(w)}
              x2={toX(w)}
              y1={padding.top}
              y2={padding.top + plotH}
              stroke="#1e293b"
              strokeDasharray="3 3"
            />
          ))}

          {/* Error Bars */}
          {showErrorBars &&
            obsPoints.map((p, i) => (
              <g key={`err-${i}`}>
                <line
                  x1={p.x}
                  x2={p.x}
                  y1={p.errY1}
                  y2={p.errY2}
                  stroke={p.isMasked ? '#f59e0b' : '#38bdf855'}
                  strokeWidth="1"
                />
                <line
                  x1={p.x - 2}
                  x2={p.x + 2}
                  y1={p.errY1}
                  y2={p.errY1}
                  stroke={p.isMasked ? '#f59e0b' : '#38bdf855'}
                  strokeWidth="1"
                />
                <line
                  x1={p.x - 2}
                  x2={p.x + 2}
                  y1={p.errY2}
                  y2={p.errY2}
                  stroke={p.isMasked ? '#f59e0b' : '#38bdf855'}
                  strokeWidth="1"
                />
              </g>
            ))}

          {/* Observed Flux Curve */}
          <path d={obsPathD} fill="none" stroke="#38bdf8" strokeWidth="1.8" />

          {/* Reconstructed Autoencoder Curve */}
          {showReconstruction && (
            <path
              d={reconPathD}
              fill="none"
              stroke="#a855f7"
              strokeWidth="2"
              strokeDasharray="4 3"
            />
          )}

          {/* Observed Data Points */}
          {obsPoints.map((p, i) => (
            <circle
              key={`pt-${i}`}
              cx={p.x}
              cy={p.y}
              r={p.isMasked ? 4 : 2.5}
              fill={p.isMasked ? '#f59e0b' : '#f8fafc'}
              stroke={p.isMasked ? '#b45309' : '#38bdf8'}
              strokeWidth="1"
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHoveredPoint(p)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
          ))}

          {/* Axes */}
          <line
            x1={padding.left}
            x2={svgWidth - padding.right}
            y1={padding.top + plotH}
            y2={padding.top + plotH}
            stroke="#475569"
            strokeWidth="1"
          />
          <line
            x1={padding.left}
            x2={padding.left}
            y1={padding.top}
            y2={padding.top + plotH}
            stroke="#475569"
            strokeWidth="1"
          />

          {/* X Axis Labels */}
          {[0.75, 1.0, 2.0, 3.0, 4.0, 5.0].map((w) => (
            <text
              key={`xl-${w}`}
              x={toX(w)}
              y={padding.top + plotH + 18}
              fill="#94a3b8"
              fontSize="10"
              fontFamily="monospace"
              textAnchor="middle"
            >
              {w.toFixed(2)} μm
            </text>
          ))}
          <text
            x={padding.left + plotW / 2}
            y={svgHeight - 6}
            fill="#cbd5e1"
            fontSize="11"
            fontWeight="600"
            textAnchor="middle"
          >
            Observed Wavelength λ (microns)
          </text>

          {/* Y Axis Label */}
          <text
            x={-(padding.top + plotH / 2)}
            y="16"
            fill="#cbd5e1"
            fontSize="11"
            fontWeight="600"
            textAnchor="middle"
            transform="rotate(-90)"
          >
            Flux f_ν (mJy)
          </text>
        </svg>

        {/* Hovered point tooltip */}
        {hoveredPoint && (
          <div
            style={{
              position: 'absolute',
              top: hoveredPoint.y - 45,
              left: Math.min(hoveredPoint.x + 10, svgWidth - 150),
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid #38bdf8',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '0.72rem',
              fontFamily: 'monospace',
              color: '#fff',
              pointerEvents: 'none',
              zIndex: 10
            }}
          >
            <div>λ = {hoveredPoint.w.toFixed(3)} μm (Ch {hoveredPoint.idx + 1})</div>
            <div>Flux = {hoveredPoint.f.toFixed(3)} mJy {hoveredPoint.isMasked ? '(MASKED)' : ''}</div>
          </div>
        )}
      </div>

      {/* Metrics & Physics Badges */}
      <div className="grid-3" style={{ marginTop: '16px' }}>
        <div style={{ background: '#080c14', padding: '12px', borderRadius: '8px', border: '1px solid #1e293b' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            SPECTRA Reconstruction Loss (L1)
          </div>
          <div className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: '#38bdf8', marginTop: '4px' }}>
            {Number(metrics.reconstruction_loss || candidate?.spectral_score || 0).toFixed(4)}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
            Inference: Frozen SPECTRA V2 Checkpoint
          </div>
        </div>

        <div style={{ background: '#080c14', padding: '12px', borderRadius: '8px', border: '1px solid #1e293b' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Rayleigh-Jeans Sidecar Status
          </div>
          <div className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: '#a855f7', marginTop: '4px' }}>
            {Number(sidecar.excess_ratio || 1.12).toFixed(2)}×
          </div>
          <div style={{ fontSize: '0.72rem', color: sidecar.excess_ratio > 1.5 ? '#f59e0b' : '#10b981', marginTop: '2px' }}>
            {sidecar.evidence_status === 'EXTERNAL_SPECTRUM_UNAVAILABLE' ? 'UNAVAILABLE (NO EXT SPECTRUM)' : (sidecar.flag || 'NORMAL CONTINUUM')}
          </div>
        </div>

        <div style={{ background: '#080c14', padding: '12px', borderRadius: '8px', border: '1px solid #1e293b' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Masked / Outlier Channels
          </div>
          <div className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: maskedIdx.size > 0 ? '#f59e0b' : '#10b981', marginTop: '4px' }}>
            {maskedIdx.size} / 102
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
            Atmospheric & Instrumental flags
          </div>
        </div>
      </div>
    </div>
  );
}

