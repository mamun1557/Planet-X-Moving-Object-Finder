import React, { useState } from 'react';
import { Crosshair, ZoomIn, ZoomOut, Maximize2, Info } from 'lucide-react';

export default function FitsViewer({ cutoutData, candidate }) {
  const [showCrosshairs, setShowCrosshairs] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);

  if (!cutoutData || cutoutData.status !== 'SUCCESS') {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
        <p>Select a candidate to view dual-epoch SPHEREx Level-2 FITS cutouts.</p>
      </div>
    );
  }

  const d = cutoutData.data;
  const ditherPair = d.dither_pair || {};
  const coords = d.coordinates || {};
  const isDither = d.temporal_eligibility?.is_dither;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">
            <Maximize2 size={18} color="#38bdf8" />
            <span>Dual-Epoch SPHEREx Level-2 Calibrated Cutouts</span>
          </div>
          <div className="card-subtitle font-mono">
            Candidate: {candidate?.candidate_id} | RA: {Number(coords.ra || candidate?.ra_deg || 0).toFixed(4)}°, Dec: {Number(coords.dec || candidate?.dec_deg || 0).toFixed(4)}°
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className={`btn ${showCrosshairs ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setShowCrosshairs(!showCrosshairs)}
            title="Toggle Astrometric Crosshair"
          >
            <Crosshair size={14} />
            <span>Crosshair</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setZoomLevel((z) => Math.min(2.0, z + 0.25))}
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setZoomLevel((z) => Math.max(0.75, z - 0.25))}
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
        </div>
      </div>

      {isDither && (
        <div className="compact-notice-badge mb-3">
          <Info size={14} className="text-warning flex-shrink-0" />
          <span>
            <strong>Intra-Visit Dither:</strong> Epochs {ditherPair.e1} &amp; {ditherPair.e2} (Δt ≈ {Number(ditherPair.dt_minutes || 5.04).toFixed(1)}m) are subject to CHRONOS-X fail-closed temporal eligibility rules.
          </span>
        </div>
      )}

      <div className="grid-2">
        {/* Epoch 1 Cutout */}
        <div style={{ background: '#080c14', borderRadius: '8px', padding: '16px', border: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#38bdf8' }}>
              EPOCH 1: DITHER {ditherPair.e1 || '1D1'} (Reference)
            </span>
            <span className="font-mono" style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              $128 \times 128$ px | Pixel ({Number(coords.x_pixel || 0).toFixed(1)}, {Number(coords.y_pixel || 0).toFixed(1)})
            </span>
          </div>

          <div className="blinker-frame-container" style={{ transform: `scale(${zoomLevel})`, transition: 'transform 0.2s' }}>
            {d.cutout_e1_base64 ? (
              <img
                src={`data:image/png;base64,${d.cutout_e1_base64}`}
                alt="Epoch 1 Cutout"
                className="blinker-image"
              />
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>No Cutout Image</div>
            )}
            {showCrosshairs && (
              <>
                <div className="blinker-crosshair" />
                <div className="blinker-reticle" />
              </>
            )}
            <div className="blinker-overlay-tag">t = 0.0m</div>
          </div>
        </div>

        {/* Epoch 2 Cutout */}
        <div style={{ background: '#080c14', borderRadius: '8px', padding: '16px', border: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#c084fc' }}>
              EPOCH 2: DITHER {ditherPair.e2 || '4D1'} (+{Number(ditherPair.dt_minutes || 5.04).toFixed(1)}m)
            </span>
            <span className="font-mono" style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              $128 \times 128$ px | Pointing 0003
            </span>
          </div>

          <div className="blinker-frame-container" style={{ transform: `scale(${zoomLevel})`, transition: 'transform 0.2s' }}>
            {d.cutout_e2_base64 ? (
              <img
                src={`data:image/png;base64,${d.cutout_e2_base64}`}
                alt="Epoch 2 Cutout"
                className="blinker-image"
              />
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>No Cutout Image</div>
            )}
            {showCrosshairs && (
              <>
                <div className="blinker-crosshair" />
                <div className="blinker-reticle" />
              </>
            )}
            <div className="blinker-overlay-tag">t = +{Number(ditherPair.dt_minutes || 5.04).toFixed(1)}m</div>
          </div>
        </div>
      </div>
    </div>
  );
}

