import React from 'react';
import {
  UploadCloud,
  FileCheck,
  Cpu,
  ShieldCheck,
  Layers,
  ArrowRight,
  Database,
  Info,
  Clock,
  Sparkles,
  AlertCircle
} from 'lucide-react';

/**
 * ObservatoryWorkspace Component (Task 4.29D)
 * Initial landing workspace: starts strictly with EMPTY_WORKSPACE.
 * Displays:
 * - Platform identity & mission.
 * - Current isolated session status.
 * - Primary "Add Observations" action.
 * - Supported astronomical file formats.
 * - Step-by-step scientific analysis workflow.
 */
export default function ObservatoryWorkspace({
  sessionId,
  sessionInfo,
  uploadedFiles = [],
  onNavigate
}) {
  const isWorkspaceEmpty = uploadedFiles.length === 0 && (!sessionInfo || sessionInfo.dataset_mode === 'EMPTY');

  return (
    <div className="observatory-workspace-container" role="main">
      {/* Platform Hero / Mission Strip */}
      <section className="obs-hero-banner">
        <div className="obs-hero-content">
          <div className="obs-hero-badge">
            <Sparkles size={14} className="text-cyan mr-1.5" />
            <span>SPECTRA-X • NASA Space Apps Challenge 2026</span>
          </div>
          <h1 className="obs-hero-title">
            The Human-AI Co-Pilot for Exploring the Changing Infrared Sky
          </h1>
          <p className="obs-hero-subtitle">
            A general-purpose, input-driven astronomical analysis workspace. Provide calibrated FITS observations,
            catalog coordinates, or spectrophotometric data to inspect transient candidates, evaluate spatial
            morphology, and measure astronomical motion across multi-epoch baselines.
          </p>

          <div className="obs-hero-actions">
            <button
              className="btn btn-primary"
              onClick={() => onNavigate('DATA_INPUT')}
              id="btn-add-observations-hero"
            >
              <UploadCloud size={16} />
              <span>Add Observations</span>
              <ArrowRight size={15} />
            </button>
            <button
              className="btn btn-outline"
              onClick={() => onNavigate('ABOUT')}
            >
              <Info size={16} />
              <span>Methodology & Limitations</span>
            </button>
          </div>
        </div>
      </section>

      {/* Session Isolation & Operational State */}
      <section className="obs-session-status-card">
        <div className="session-status-header">
          <div className="flex items-center gap-2">
            <span className="session-pulse-dot"></span>
            <span className="session-card-title">Isolated Workspace Session</span>
          </div>
          <span className="session-id-badge font-mono">
            {sessionId ? `UUID: ${sessionId}` : 'Initializing Session...'}
          </span>
        </div>

        <div className="session-telemetry-grid">
          <div className="session-telemetry-item">
            <span className="telemetry-key">Session Mode:</span>
            <span className="telemetry-val font-mono">
              {isWorkspaceEmpty ? 'EMPTY_WORKSPACE' : sessionInfo?.dataset_mode || 'LOADED'}
            </span>
          </div>
          <div className="session-telemetry-item">
            <span className="telemetry-key">Session TTL:</span>
            <span className="telemetry-val font-mono">
              <Clock size={12} className="inline mr-1" />
              2 Hours (Ephemeral Scratch)
            </span>
          </div>
          <div className="session-telemetry-item">
            <span className="telemetry-key">Observations Loaded:</span>
            <span className="telemetry-val font-mono text-cyan">
              {uploadedFiles.length} File{uploadedFiles.length === 1 ? '' : 's'}
            </span>
          </div>
          <div className="session-telemetry-item">
            <span className="telemetry-key">Historical Preloading:</span>
            <span className="telemetry-val font-mono text-emerald">PROHIBITED (Clean State)</span>
          </div>
        </div>

        {isWorkspaceEmpty && (
          <div className="empty-workspace-notice">
            <AlertCircle size={16} className="text-cyan flex-shrink-0" />
            <span>
              <strong>Empty Workspace:</strong> No astronomical observation data is currently preloaded.
              Upload FITS or tabular epochs under <em>Data Input</em> to begin analysis.
            </span>
          </div>
        )}
      </section>

      {/* Supported Astronomical Formats */}
      <section className="obs-formats-grid">
        <div className="format-card">
          <div className="format-icon-wrap cyan">
            <FileCheck size={22} />
          </div>
          <h3 className="format-title">FITS Calibrated Images</h3>
          <p className="format-desc">
            Supports single and multi-extension 2D/3D FITS files with valid celestial WCS (CRVAL, CRPIX, CDELT/CD/PC)
            and observation timestamps (DATE-OBS / MJD-OBS).
          </p>
          <div className="format-tags font-mono">
            <span>.fits</span>
            <span>.fit</span>
            <span>.fts</span>
            <span>WCS Required for Motion</span>
          </div>
        </div>

        <div className="format-card">
          <div className="format-icon-wrap violet">
            <Database size={22} />
          </div>
          <h3 className="format-title">Astrometric Catalogs (CSV)</h3>
          <p className="format-desc">
            Tabular coordinate files containing celestial positions (RA, Dec in J2000 degrees), observation epochs,
            astrometric uncertainties, and optional 102-channel spectrophotometry.
          </p>
          <div className="format-tags font-mono">
            <span>.csv</span>
            <span>ICRS Coordinates</span>
            <span>Uncertainty Columns</span>
          </div>
        </div>

        <div className="format-card">
          <div className="format-icon-wrap amber">
            <Layers size={22} />
          </div>
          <h3 className="format-title">Observation Records (JSON)</h3>
          <p className="format-desc">
            Structured JSON observation epochs containing paired epoch vectors, flux arrays, and candidate
            disposition records.
          </p>
          <div className="format-tags font-mono">
            <span>.json</span>
            <span>Multi-Epoch Records</span>
            <span>Spectral Arrays</span>
          </div>
        </div>
      </section>

      {/* 4-Step Analysis Workflow */}
      <section className="obs-workflow-section">
        <h2 className="workflow-title">Scientific Analysis Workflow</h2>
        <div className="workflow-steps-grid">
          <div className="workflow-step">
            <div className="step-num font-mono">01</div>
            <h4 className="step-heading">Add Observations</h4>
            <p className="step-text">
              Provide your own FITS files or observation epochs. Optionally select from the 50-pair engineering test library.
            </p>
          </div>

          <div className="workflow-step">
            <div className="step-num font-mono">02</div>
            <h4 className="step-heading">Validate & Inspect</h4>
            <p className="step-text">
              The engine verifies WCS validity, astrometric projection, temporal baseline, and channel coverage.
            </p>
          </div>

          <div className="workflow-step">
            <div className="step-num font-mono">03</div>
            <h4 className="step-heading">Run Module Matrix</h4>
            <p className="step-text">
              Evaluate eligibility across ASTROVISION, SPECTRA, CHRONOS-X, MOTION-X, and FUSION-X pipelines.
            </p>
          </div>

          <div className="workflow-step">
            <div className="step-num font-mono">04</div>
            <h4 className="step-heading">Review Evidence</h4>
            <p className="step-text">
              Inspect angular displacement, motion rates, dither safeguards, and comprehensive multi-channel evidence.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

