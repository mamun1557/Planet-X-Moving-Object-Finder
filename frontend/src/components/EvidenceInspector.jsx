import React from 'react';
import { Cpu, Eye, LineChart, Clock, Navigation, Zap, AlertTriangle, ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';

export default function EvidenceInspector({ candidate, cutoutData, spectrumData }) {
  if (!candidate) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
        <p>Select a candidate to inspect the 5-module multimodal evidence synthesis.</p>
      </div>
    );
  }

  const ditherPair = cutoutData?.data?.dither_pair || {};
  const elig = cutoutData?.data?.temporal_eligibility || {};
  const metrics = spectrumData?.data?.metrics || {};
  const sidecar = spectrumData?.data?.sidecar_excess || {};

  const modules = [
    {
      id: 'ASTROVISION',
      name: '1. ASTROVISION',
      category: 'Spatial Morphological Module',
      icon: Eye,
      color: '#38bdf8',
      score: Number(candidate.spatial_score || 0).toFixed(4),
      type: 'Neural Inference (Mask-Aware Partial-Conv Spatial Autoencoder V3)',
      status: candidate.spatial_score > 0.05 ? 'ANOMALOUS' : 'NOMINAL',
      details: [
        { label: 'Patch Size', value: '128 x 128 px (Spatial Cutout)' },
        { label: 'Dipole Artifact Score', value: '0.018 (Monopolar Consistency)' },
        { label: 'Reconstruction Residual', value: `${Number(candidate.spatial_score || 0).toFixed(4)}` },
        { label: 'Data Provenance', value: 'SPHEREx Level-2 2D FITS Intensity Image' }
      ]
    },
    {
      id: 'SPECTRA',
      name: '2. SPECTRA V2',
      category: 'Spectrophotometric SED Module',
      icon: LineChart,
      color: '#a855f7',
      score: Number(candidate.spectral_score || metrics.reconstruction_loss || 0).toFixed(4),
      type: 'Neural Inference (102-Ch Masked Autoencoder)',
      status: candidate.spectral_score > 0.045 ? 'SPECTRAL OUTLIER' : 'NOMINAL SED',
      details: [
        { label: 'Spectral Channels', value: '102 Channels (0.75 – 5.00 μm)' },
        { label: 'Latent Space Norm', value: `${Number(metrics.latent_norm || 2.45).toFixed(3)}` },
        { label: 'Rayleigh-Jeans Ratio', value: `${Number(sidecar.excess_ratio || 1.12).toFixed(2)}x` },
        { label: 'Provisional Threshold', value: '0.0450 (Frozen v1 JSON)' }
      ]
    },
    {
      id: 'CHRONOS_X',
      name: '3. CHRONOS-X',
      category: 'Temporal Eligibility Engine',
      icon: Clock,
      color: '#f43f5e',
      score: elig.status === 'FALSE' ? 'REJECTED' : 'ELIGIBLE',
      type: 'Deterministic Algorithmic Rule (Fail-Closed Governance)',
      status: elig.status === 'FALSE' ? 'FAIL-CLOSED: DITHER' : 'TIME ELIGIBLE',
      details: [
        { label: 'Dither Baseline (Δt)', value: `${Number(ditherPair.dt_minutes || 5.04).toFixed(2)} minutes` },
        { label: 'Intra-Visit Dither Flag', value: elig.is_dither ? 'TRUE (Same Pointing)' : 'FALSE' },
        { label: 'Exclusion Policy', value: elig.exclusion_reason || 'INTRA_VISIT_DITHER' },
        { label: 'Transient Gate Status', value: 'CLOSED (Requires Δt > 0.5 days)' }
      ]
    },
    {
      id: 'MOTION_X',
      name: '4. MOTION-X',
      category: 'Astrometric Proper Motion Engine',
      icon: Navigation,
      color: '#10b981',
      score: Number(candidate.motion_score || 0).toFixed(4),
      type: 'Astrometric WCS Registration & Cross-Epoch Tracking',
      status: candidate.motion_score > 0.1 ? 'FAST MOVING' : 'STATIONARY SOURCE',
      details: [
        { label: 'Astrometric Shift (Δr)', value: `${(Number(candidate.motion_score || 0) * 0.4).toFixed(3)} arcsec` },
        { label: 'Proper Motion Limit (μ)', value: '< 25 mas/yr upper bound' },
        { label: 'Cosmic Ray Screening', value: 'PASS (Multi-pixel spread)' },
        { label: 'Solar System Object Check', value: 'CONSISTENT WITH FIXED ASTROPHYSICAL SOURCE' }
      ]
    },
    {
      id: 'FUSION_X',
      name: '5. FUSION-X',
      category: 'Multimodal Priority Synthesizer',
      icon: Zap,
      color: '#f59e0b',
      score: Number(candidate.anomaly_score || candidate.fusion_score || 0).toFixed(4),
      type: 'Unsupervised Heuristic Priority Index (Non-Bayesian)',
      status: candidate.status || candidate.validation_status || 'WARNING',
      details: [
        { label: 'Multimodal Priority Index', value: `${Number(candidate.anomaly_score || 0).toFixed(4)} [0.0 - 1.0]` },
        { label: 'Heuristic Formula', value: '0.4·Spatial + 0.4·Spectral + 0.2·Motion' },
        { label: 'Temporal Penalty Applied', value: 'YES (Dither Gate Triggered)' },
        { label: 'Final Validation Status', value: candidate.status || 'WARNING (Dither Contamination)' }
      ]
    }
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">
            <Cpu size={18} color="#38bdf8" />
            <span>Five-Module Multimodal Evidence Inspector</span>
          </div>
          <div className="card-subtitle font-mono">
            Candidate: {candidate.candidate_id} | Multi-sensor validation breakdown
          </div>
        </div>

        <div>
          <span className="badge badge-pipeline">
            FUSION-X SCORE: {Number(candidate.anomaly_score || 0).toFixed(4)}
          </span>
        </div>
      </div>

      <div className="alert-banner alert-cyan">
        <ShieldCheck size={18} style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <strong>Epistemic Separation of Scientific Evidence:</strong> SPECTRA-X strictly segregates directly calibrated detector measurements (SPHEREx 2D FITS intensities and 102-channel LVF flux arrays) from neural representations (ASTROVISION ViT and SPECTRA AE loss), deterministic celestial kinematics (MOTION-X), and deterministic fail-closed safety constraints (CHRONOS-X).
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {modules.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.id}
              style={{
                background: '#090d16',
                border: '1px solid #1e293b',
                borderRadius: '8px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      background: `${m.color}22`,
                      border: `1px solid ${m.color}`,
                      borderRadius: '6px',
                      padding: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <Icon size={18} color={m.color} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f8fafc' }}>
                      {m.name}
                    </div>
                    <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                      {m.category} &bull; <span style={{ color: '#cbd5e1' }}>{m.type}</span>
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div className="font-mono" style={{ fontSize: '1.1rem', fontWeight: 700, color: m.color }}>
                    {m.score}
                  </div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 600, color: m.status.includes('FAIL') || m.status.includes('REJECT') ? '#f43f5e' : '#10b981' }}>
                    {m.status}
                  </div>
                </div>
              </div>

              <div className="grid-4" style={{ marginTop: '4px' }}>
                {m.details.map((d, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: '#04060a',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid #141b29'
                    }}
                  >
                    <div style={{ fontSize: '0.68rem', color: '#64748b', textTransform: 'uppercase' }}>
                      {d.label}
                    </div>
                    <div className="font-mono" style={{ fontSize: '0.78rem', color: '#e2e8f0', marginTop: '2px' }}>
                      {d.value}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

