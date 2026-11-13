import React from 'react';
import {
  Home,
  Search,
  Eye,
  Layers,
  Activity,
  ShieldCheck,
  UserCheck,
  Download,
  Cpu,
  Radio
} from 'lucide-react';

/**
 * Sidebar Navigation Component
 * Matches the SPECTRA-X Interactive Observatory layout:
 * - NASA Brand & Title
 * - Primary Observatory Views
 * - Powered by NASA SPHEREx footer card
 * - Live System & GPU Status indicator
 */
export default function Sidebar({
  activeView = 'HOME',
  setActiveView,
  candidateCount = 47,
  gpuStatus = 'Available (CUDA)',
  systemReady = true,
  mobileOpen = false
}) {
  const navItems = [
    { id: 'HOME', label: 'Home', icon: Home },
    { id: 'EXPLORER', label: 'Candidate Explorer', icon: Search, badge: candidateCount },
    { id: 'BLINK', label: 'Blink Observatory', icon: Eye },
    { id: 'DIFFERENCE', label: 'Difference View', icon: Layers },
    { id: 'SPECTRAL', label: 'Spectral Viewer', icon: Activity },
    { id: 'EVIDENCE', label: 'Evidence Inspector', icon: ShieldCheck },
    { id: 'REVIEW', label: 'Human Review', icon: UserCheck },
    { id: 'EXPORT', label: 'Export Results', icon: Download }
  ];

  return (
    <aside className={`spectra-sidebar ${mobileOpen ? 'mobile-open' : ''}`} aria-label="Main Navigation">
      {/* Brand Header */}
      <div className="sidebar-brand" onClick={() => setActiveView('HOME')}>
        <div className="nasa-insignia" aria-label="NASA Logo">
          <svg viewBox="0 0 100 100" className="nasa-svg" width="40" height="40">
            <circle cx="50" cy="50" r="46" fill="#0B3D91" />
            {/* Stars */}
            <circle cx="28" cy="30" r="1.5" fill="#FFFFFF" />
            <circle cx="36" cy="44" r="1.2" fill="#FFFFFF" />
            <circle cx="22" cy="56" r="1.8" fill="#FFFFFF" />
            <circle cx="68" cy="26" r="1.4" fill="#FFFFFF" />
            <circle cx="76" cy="42" r="1.6" fill="#FFFFFF" />
            <circle cx="62" cy="72" r="1.5" fill="#FFFFFF" />
            <circle cx="40" cy="74" r="1.2" fill="#FFFFFF" />
            {/* Red Chevron Vector */}
            <path
              d="M18 58 L52 24 L56 24 L24 64 Z"
              fill="#FC3D21"
            />
            <path
              d="M48 26 L82 66 L78 70 L46 32 Z"
              fill="#FC3D21"
            />
            {/* Orbit ellipse */}
            <ellipse
              cx="50"
              cy="50"
              rx="42"
              ry="16"
              fill="none"
              stroke="#E0E8F5"
              strokeWidth="2.5"
              transform="rotate(-28 50 50)"
            />
            {/* NASA Text */}
            <text
              x="50"
              y="58"
              fontFamily="'Space Grotesk', 'Arial Black', sans-serif"
              fontSize="22"
              fontWeight="900"
              letterSpacing="2"
              fill="#FFFFFF"
              textAnchor="middle"
            >
              NASA
            </text>
          </svg>
        </div>

        <div className="brand-titles">
          <div className="brand-main-title">SPECTRA-X</div>
          <div className="brand-subtitle">Interactive Observatory</div>
          <div className="brand-tagline">Explore • Analyze • Discover</div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              className={`sidebar-nav-btn ${isActive ? 'active' : ''}`}
              onClick={() => setActiveView(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="nav-btn-icon-wrap">
                <Icon size={18} className="nav-icon" />
              </div>
              <span className="nav-label">{item.label}</span>
              {item.badge !== undefined && item.badge !== null && (
                <span className="nav-badge font-mono">{item.badge}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer Cards */}
      <div className="sidebar-footer">
        {/* Powered by NASA SPHEREx card */}
        <div className="spherex-card">
          <div className="spherex-card-content">
            <span className="powered-text">Powered by</span>
            <span className="spherex-name">NASA SPHEREx</span>
          </div>
          <div className="satellite-render" aria-hidden="true">
            <svg viewBox="0 0 120 70" className="satellite-svg">
              {/* Earth curvature with blue atmospheric glow */}
              <defs>
                <linearGradient id="earthGlow" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#42D9F5" stopOpacity="0.8" />
                  <stop offset="30%" stopColor="#1E40AF" stopOpacity="0.9" />
                  <stop offset="100%" stopColor="#0B1224" stopOpacity="1" />
                </linearGradient>
                <linearGradient id="telescopeGold" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#F59E0B" />
                  <stop offset="50%" stopColor="#D97706" />
                  <stop offset="100%" stopColor="#78350F" />
                </linearGradient>
              </defs>
              <path d="M-10,70 Q60,35 130,70 L130,75 L-10,75 Z" fill="url(#earthGlow)" />
              {/* Satellite Cone / Sunshade */}
              <polygon points="65,18 90,8 80,32 58,26" fill="#334155" stroke="#94A3B8" strokeWidth="0.8" />
              <polygon points="65,18 80,32 68,38 52,24" fill="#1E293B" stroke="#64748B" strokeWidth="0.8" />
              <polygon points="52,24 68,38 60,44 45,30" fill="url(#telescopeGold)" />
              {/* Solar Array / Panels */}
              <polygon points="38,28 46,34 32,46 25,40" fill="#3B82F6" stroke="#93C5FD" strokeWidth="0.6" />
              <circle cx="85" cy="12" r="1.2" fill="#42D9F5" />
            </svg>
          </div>
        </div>

        {/* System & Hardware Status */}
        <div className="system-status-card">
          <div className="status-header">
            <span className="status-label">System Status</span>
            <div className="status-indicator">
              <span className={`status-dot ${systemReady ? 'ready' : 'busy'}`}></span>
              <span className="status-text">{systemReady ? 'Ready' : 'Analyzing'}</span>
            </div>
          </div>
          <div className="gpu-telemetry">
            <div className="gpu-icon-wrap">
              <Cpu size={15} className="gpu-icon" />
            </div>
            <div className="gpu-details">
              <span className="gpu-title">GPU: {gpuStatus}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
