import React, { useState, useEffect } from 'react';
import { Play, Pause, SkipForward, Sliders, ShieldAlert, Crosshair, SplitSquareVertical } from 'lucide-react';

export default function BlinkViewer({ cutoutData, candidate }) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentFrame, setCurrentFrame] = useState(1); // 1 = Epoch 1, 2 = Epoch 2
  const [blinkSpeedHz, setBlinkSpeedHz] = useState(2.0); // 2.0 Hz = 500ms cycle
  const [showCrosshairs, setShowCrosshairs] = useState(true);

  const d = cutoutData?.data;
  const ditherPair = d?.dither_pair || { e1: '1D1', e2: '4D1', dt_minutes: 5.04 };
  const e1Img = d?.cutout_e1_base64;
  const e2Img = d?.cutout_e2_base64;

  useEffect(() => {
    if (!isPlaying) return;
    const intervalMs = (1.0 / blinkSpeedHz) * 1000;
    const timer = setInterval(() => {
      setCurrentFrame((prev) => (prev === 1 ? 2 : 1));
    }, intervalMs);
    return () => clearInterval(timer);
  }, [isPlaying, blinkSpeedHz]);

  const toggleFrame = () => {
    setIsPlaying(false);
    setCurrentFrame((prev) => (prev === 1 ? 2 : 1));
  };

  if (!cutoutData || cutoutData.status !== 'SUCCESS') {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
        <p>Select a candidate from the catalog to activate the Optical Blink Engine.</p>
      </div>
    );
  }

  const activeImg = currentFrame === 1 ? e1Img : e2Img;
  const activeLabel = currentFrame === 1 
    ? `EPOCH 1 (Dither ${ditherPair.e1}) — Reference (t = 0m)` 
    : `EPOCH 2 (Dither ${ditherPair.e2}) — Follow-up (t = +${Number(ditherPair.dt_minutes || 5.04).toFixed(1)}m)`;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">
            <SplitSquareVertical size={18} color="#38bdf8" />
            <span>Interactive Optical Blink Comparator</span>
          </div>
          <div className="card-subtitle font-mono">
            Candidate: {candidate?.candidate_id} | High-cadence dither pair blink analysis
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className={`btn ${isPlaying ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause Auto-Blink' : 'Play Auto-Blink'}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
            <span>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>

          <button
            className="btn btn-secondary"
            onClick={toggleFrame}
            title="Step to Alternative Frame"
          >
            <SkipForward size={14} />
            <span>Step</span>
          </button>

          <button
            className={`btn ${showCrosshairs ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setShowCrosshairs(!showCrosshairs)}
            title="Toggle Astrometric Crosshair"
          >
            <Crosshair size={14} />
          </button>
        </div>
      </div>

      <div className="compact-notice-badge mb-3">
        <ShieldAlert size={14} className="text-warning flex-shrink-0" />
        <span>
          <strong>Intra-Visit Dither (Δt ≈ {Number(ditherPair.dt_minutes || 5.04).toFixed(1)}m):</strong> Blink frames reflect pointing dither offsets. Fail-closed CHRONOS-X governance excludes intra-visit dithers from transient confirmation.
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
        {/* Frame Screen */}
        <div className="blinker-frame-container" style={{ width: '380px', height: '380px' }}>
          {activeImg ? (
            <img
              src={`data:image/png;base64,${activeImg}`}
              alt={activeLabel}
              className="blinker-image"
            />
          ) : (
            <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>No Frame Loaded</div>
          )}

          {showCrosshairs && (
            <>
              <div className="blinker-crosshair" />
              <div className="blinker-reticle" />
            </>
          )}

          <div
            className="blinker-overlay-tag"
            style={{
              borderColor: currentFrame === 1 ? '#38bdf8' : '#c084fc',
              color: currentFrame === 1 ? '#38bdf8' : '#c084fc'
            }}
          >
            {currentFrame === 1 ? 'FRAME 1 (DITHER 1)' : 'FRAME 2 (DITHER 4)'}
          </div>
        </div>

        {/* Frame Label & Status */}
        <div style={{ textAlign: 'center' }}>
          <div className="font-mono" style={{ fontSize: '0.85rem', fontWeight: 600, color: currentFrame === 1 ? '#38bdf8' : '#c084fc' }}>
            {activeLabel}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>
            Current Status: {isPlaying ? `Blinking at ${blinkSpeedHz.toFixed(1)} Hz` : 'Paused on single frame'}
          </div>
        </div>

        {/* Speed Slider Control */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', background: '#0a0e17', padding: '10px 18px', borderRadius: '8px', border: '1px solid #1e293b' }}>
          <Sliders size={16} color="#94a3b8" />
          <span style={{ fontSize: '0.78rem', color: '#cbd5e1' }}>Blink Speed:</span>
          <input
            type="range"
            min="0.5"
            max="4.0"
            step="0.25"
            value={blinkSpeedHz}
            onChange={(e) => setBlinkSpeedHz(parseFloat(e.target.value))}
            style={{ width: '160px', accentColor: '#38bdf8' }}
          />
          <span className="font-mono" style={{ fontSize: '0.8rem', color: '#38bdf8', minWidth: '50px' }}>
            {blinkSpeedHz.toFixed(1)} Hz
          </span>
        </div>
      </div>
    </div>
  );
}

