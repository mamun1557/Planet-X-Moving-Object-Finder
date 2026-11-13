import React from 'react';
import { MinusSquare, AlertCircle, ShieldX, CheckCircle, Compass } from 'lucide-react';

export default function DifferenceViewer({ cutoutData, candidate }) {
  if (!cutoutData || cutoutData.status !== 'SUCCESS') {
    return null;
  }

  const d = cutoutData.data;
  const diffImg = d.diff_base64;
  const sigImg = d.sig_base64;
  const elig = d.temporal_eligibility || {};
  const isExcluded = elig.status === 'FALSE';

  return (
    <div className="card" style={{ marginTop: '20px' }}>
      <div className="card-header">
        <div>
          <div className="card-title">
            <MinusSquare size={18} color="#38bdf8" />
            <span>Calibrated Difference & Astrometric Significance Analysis</span>
          </div>
          <div className="card-subtitle font-mono">
            Direct residual subtraction $(E_2 - E_1)$ with Poisson significance mapping
          </div>
        </div>

        <div>
          {isExcluded ? (
            <span className="badge" style={{ background: 'rgba(244, 63, 94, 0.2)', borderColor: '#f43f5e', color: '#fda4af' }}>
              <ShieldX size={14} />
              <span>CHRONOS-X: REJECTED (DITHER)</span>
            </span>
          ) : (
            <span className="badge badge-status">
              <CheckCircle size={14} />
              <span>TEMPORALLY ELIGIBLE</span>
            </span>
          )}
        </div>
      </div>

      <div className="grid-2">
        {/* Difference Map */}
        <div style={{ background: '#080c14', borderRadius: '8px', padding: '16px', border: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#f59e0b' }}>
              CALIBRATED DIFFERENCE MAP $(E_2 - E_1)$
            </span>
            <span className="font-mono" style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Linear stretch [5%, 95%]
            </span>
          </div>

          <div className="blinker-frame-container">
            {diffImg ? (
              <img
                src={`data:image/png;base64,${diffImg}`}
                alt="Difference Map"
                className="blinker-image"
              />
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>No Difference Map</div>
            )}
            <div className="blinker-overlay-tag" style={{ color: '#f59e0b', borderColor: '#f59e0b' }}>
              RESIDUAL MAP
            </div>
          </div>
          <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '8px' }}>
            A true transient appears as a monopolar point source. Dipole features (adjacent bright and dark lobes) indicate sub-pixel pointing misregistration between dithers.
          </div>
        </div>

        {/* Significance Map */}
        <div style={{ background: '#080c14', borderRadius: '8px', padding: '16px', border: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#a855f7' }}>
              POISSON SIGNIFICANCE MAP $(\sigma)$
            </span>
            <span className="font-mono" style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              &Delta;I / &radic;(&sigma;1&sup2; + &sigma;2&sup2;)
            </span>
          </div>

          <div className="blinker-frame-container">
            {sigImg ? (
              <img
                src={`data:image/png;base64,${sigImg}`}
                alt="Significance Map"
                className="blinker-image"
              />
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>No Significance Map</div>
            )}
            <div className="blinker-overlay-tag" style={{ color: '#a855f7', borderColor: '#a855f7' }}>
              SIGNIFICANCE $(\sigma)$
            </div>
          </div>
          <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '8px' }}>
            Pixel-wise signal-to-noise detection significance. Pixels exceeding $5\sigma$ trigger ASTROVISION anomaly screening.
          </div>
        </div>
      </div>
    </div>
  );
}
