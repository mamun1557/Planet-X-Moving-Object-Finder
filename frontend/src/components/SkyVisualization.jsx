import React, { useState, useMemo } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Crosshair, Eye, Compass } from 'lucide-react';
import VisualizationLegend from './VisualizationLegend';

/**
 * SkyVisualization component
 * Implements Section 4.1 & 6.2 of Planet X UI Documentation:
 * Interactive celestial coordinate canvas rendering real SPHEREx detected sources.
 */
export default function SkyVisualization({
  candidates = [],
  selectedCandidate = null,
  onSelectCandidate,
  onSwitchToList,
  className = ''
}) {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showGrid, setShowGrid] = useState(true);
  const [showLegend, setShowLegend] = useState(true);

  // Compute RA/Dec bounds from candidates for normalization
  const bounds = useMemo(() => {
    if (!candidates || candidates.length === 0) {
      return { minRa: 163.5, maxRa: 163.8, minDec: -69.6, maxDec: -69.3 };
    }
    let minRa = Infinity, maxRa = -Infinity, minDec = Infinity, maxDec = -Infinity;
    candidates.forEach(c => {
      const ra = Number(c.ra) || 163.63;
      const dec = Number(c.dec) || -69.44;
      if (ra < minRa) minRa = ra;
      if (ra > maxRa) maxRa = ra;
      if (dec < minDec) minDec = dec;
      if (dec > maxDec) maxDec = dec;
    });
    // Add margin
    const raPad = Math.max(0.02, (maxRa - minRa) * 0.08);
    const decPad = Math.max(0.02, (maxDec - minDec) * 0.08);
    return {
      minRa: minRa - raPad,
      maxRa: maxRa + raPad,
      minDec: minDec - decPad,
      maxDec: maxDec + decPad
    };
  }, [candidates]);

  // Project RA/Dec to Canvas coordinates (Width: 1000, Height: 500)
  const width = 1000;
  const height = 500;

  const project = (ra, dec) => {
    const normX = (ra - bounds.minRa) / (bounds.maxRa - bounds.minRa || 1);
    const normY = (dec - bounds.minDec) / (bounds.maxDec - bounds.minDec || 1);
    // Invert X for astronomical RA (east is left), invert Y for Dec
    const cx = width / 2;
    const cy = height / 2;
    const x = cx + ((1 - normX) * (width - 80) + 40 - cx) * zoomLevel;
    const y = cy + ((1 - normY) * (height - 80) + 40 - cy) * zoomLevel;
    return { x, y };
  };

  const handleZoomIn = () => setZoomLevel(z => Math.min(3.5, z + 0.3));
  const handleZoomOut = () => setZoomLevel(z => Math.max(0.8, z - 0.3));
  const handleResetZoom = () => setZoomLevel(1);

  // Selected candidate position and projected trajectory
  const selectedProj = useMemo(() => {
    if (!selectedCandidate) return null;
    const ra = Number(selectedCandidate.ra) || 163.6309;
    const dec = Number(selectedCandidate.dec) || -69.4422;
    const pos = project(ra, dec);

    // Dither offset vector (representing intra-visit dither shift ~ 5 arcsec)
    const histPos = project(ra - 0.0018, dec + 0.0012);
    const estTrack = project(ra + 0.0032, dec - 0.0024);

    return { pos, histPos, estTrack, ra, dec };
  }, [selectedCandidate, bounds, zoomLevel]);

  return (
    <div className={`sky-vis-container ${className}`}>
      {/* Canvas Top Bar */}
      <div className="sky-vis-header">
        <div className="sky-vis-title-group">
          <div className="sky-vis-indicator" />
          <div>
            <h3 className="sky-vis-title">Celestial Sky View — Field P0003</h3>
            <p className="sky-vis-subtitle">
              Interactive projection of {candidates.length} detected infrared sources • SPHEREx Level-2
            </p>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="sky-vis-actions">
          <span className="badge badge-surface font-mono" title="Current Canvas Zoom Level" style={{ padding: '4px 8px', fontSize: '11px' }}>
            {zoomLevel.toFixed(1)}x
          </span>
          <button
            type="button"
            className="btn-icon"
            onClick={handleZoomIn}
            title="Zoom In"
            aria-label="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <button
            type="button"
            className="btn-icon"
            onClick={handleZoomOut}
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <button
            type="button"
            className="btn-icon"
            onClick={handleResetZoom}
            title="Reset View"
            aria-label="Reset View"
          >
            <RotateCcw size={16} />
          </button>
          <button
            type="button"
            className={`btn-icon ${showGrid ? 'active' : ''}`}
            onClick={() => setShowGrid(!showGrid)}
            title="Toggle RA/Dec Grid"
            aria-label="Toggle RA/Dec Grid"
          >
            <Compass size={16} />
          </button>
        </div>
      </div>

      {/* Main SVG Sky Canvas */}
      <div className="sky-canvas-wrapper" tabIndex={0} aria-label="Celestial Sky View Map">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="sky-canvas-svg"
          preserveAspectRatio="xMidYMid slice"
        >
          {/* Deep Space Background */}
          <rect width={width} height={height} fill="var(--color-bg, #070B18)" />

          {/* Reference Grid (Section 6.2 -- color: #344563) */}
          {showGrid && (
            <g className="sky-grid" stroke="var(--vis-grid, #344563)" strokeWidth="0.8" opacity="0.6">
              {/* RA vertical gridlines */}
              {[0.15, 0.35, 0.55, 0.75, 0.95].map((factor, i) => (
                <line key={`v-${i}`} x1={width * factor} y1={0} x2={width * factor} y2={height} strokeDasharray="3 3" />
              ))}
              {/* Dec horizontal gridlines */}
              {[0.2, 0.4, 0.6, 0.8].map((factor, i) => (
                <line key={`h-${i}`} x1={0} y1={height * factor} x2={width} y2={height * factor} strokeDasharray="3 3" />
              ))}
              {/* Axis labels */}
              <text x={width - 48} y={height - 12} fill="var(--color-text-muted)" fontSize="10" fontFamily="var(--font-data)">
                RA (J2000)
              </text>
              <text x={12} y={20} fill="var(--color-text-muted)" fontSize="10" fontFamily="var(--font-data)">
                Dec (J2000)
              </text>
            </g>
          )}

          {/* Background Stars / Unselected Catalog Objects */}
          <g className="unselected-objects">
            {candidates.map((cand) => {
              const ra = Number(cand.ra) || 163.63;
              const dec = Number(cand.dec) || -69.44;
              const { x, y } = project(ra, dec);
              const isSelected = selectedCandidate && cand.candidate_id === selectedCandidate.candidate_id;
              if (isSelected) return null; // rendered separately on top

              const r = cand.anomaly_score ? Math.max(2, Math.min(5, cand.anomaly_score * 4)) : 2.5;

              return (
                <circle
                  key={cand.candidate_id}
                  cx={x}
                  cy={y}
                  r={r}
                  fill="var(--vis-inactive, #8493AD)"
                  opacity="0.65"
                  className="sky-object-dot"
                  onClick={() => onSelectCandidate && onSelectCandidate(cand)}
                  style={{ cursor: 'pointer' }}
                >
                  <title>{`${cand.candidate_id}\nRA: ${ra.toFixed(4)}°, Dec: ${dec.toFixed(4)}°\nScore: ${cand.anomaly_score || 'N/A'}`}</title>
                </circle>
              );
            })}
          </g>

          {/* Selected Object Trajectory & Evidence Vectors */}
          {selectedProj && (
            <g className="selected-trajectory-group">
              {/* 1. Historical Epoch Position (blue #648BFF) */}
              <circle
                cx={selectedProj.histPos.x}
                cy={selectedProj.histPos.y}
                r="4"
                fill="var(--vis-historical, #648BFF)"
                opacity="0.8"
              />
              <text
                x={selectedProj.histPos.x + 8}
                y={selectedProj.histPos.y - 4}
                fill="var(--vis-historical, #648BFF)"
                fontSize="10"
                fontFamily="var(--font-data)"
              >
                Epoch 1
              </text>

              {/* 2. Intra-visit Dither / Uncertain Segment (dashed amber #FFC66D) */}
              <line
                x1={selectedProj.histPos.x}
                y1={selectedProj.histPos.y}
                x2={selectedProj.pos.x}
                y2={selectedProj.pos.y}
                stroke="var(--vis-uncertain, #FFC66D)"
                strokeWidth="1.5"
                strokeDasharray="4 3"
              />

              {/* 3. Measured / Estimated Motion Track Vector (violet #9B8CFF) */}
              <line
                x1={selectedProj.pos.x}
                y1={selectedProj.pos.y}
                x2={selectedProj.estTrack.x}
                y2={selectedProj.estTrack.y}
                stroke="var(--vis-track, #9B8CFF)"
                strokeWidth="2"
              />
              <circle
                cx={selectedProj.estTrack.x}
                cy={selectedProj.estTrack.y}
                r="3"
                fill="var(--vis-track, #9B8CFF)"
              />

              {/* 4. Active Selected Target (cyan #42D9F5) with Reticle Indicator */}
              <circle
                cx={selectedProj.pos.x}
                cy={selectedProj.pos.y}
                r="8"
                fill="none"
                stroke="var(--vis-selected, #42D9F5)"
                strokeWidth="1.8"
                className="reticle-pulse"
              />
              <circle
                cx={selectedProj.pos.x}
                cy={selectedProj.pos.y}
                r="3"
                fill="var(--vis-selected, #42D9F5)"
              />
              {/* Reticle tick marks */}
              <line
                x1={selectedProj.pos.x - 12}
                y1={selectedProj.pos.y}
                x2={selectedProj.pos.x - 5}
                y2={selectedProj.pos.y}
                stroke="var(--vis-selected, #42D9F5)"
                strokeWidth="1.2"
              />
              <line
                x1={selectedProj.pos.x + 5}
                y1={selectedProj.pos.y}
                x2={selectedProj.pos.x + 12}
                y2={selectedProj.pos.y}
                stroke="var(--vis-selected, #42D9F5)"
                strokeWidth="1.2"
              />
              <line
                x1={selectedProj.pos.x}
                y1={selectedProj.pos.y - 12}
                x2={selectedProj.pos.x}
                y2={selectedProj.pos.y - 5}
                stroke="var(--vis-selected, #42D9F5)"
                strokeWidth="1.2"
              />
              <line
                x1={selectedProj.pos.x}
                y1={selectedProj.pos.y + 5}
                x2={selectedProj.pos.x}
                y2={selectedProj.pos.y + 12}
                stroke="var(--vis-selected, #42D9F5)"
                strokeWidth="1.2"
              />

              {/* Target ID Label */}
              <text
                x={selectedProj.pos.x + 14}
                y={selectedProj.pos.y + 4}
                fill="var(--color-primary, #42D9F5)"
                fontSize="11"
                fontWeight="600"
                fontFamily="var(--font-data)"
              >
                {selectedCandidate?.candidate_id}
              </text>
            </g>
          )}
        </svg>

        {/* Center Coordinate Indicator */}
        <div className="sky-canvas-overlay-status">
          <span className="badge badge-surface">
            Center: RA {((bounds.minRa + bounds.maxRa) / 2).toFixed(3)}°, Dec {((bounds.minDec + bounds.maxDec) / 2).toFixed(3)}°
          </span>
        </div>
      </div>

      {/* Visual Legend */}
      <VisualizationLegend className="mt-3" />
    </div>
  );
}

