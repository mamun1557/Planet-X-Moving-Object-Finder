import React, { useState } from 'react';
import {
  Compass,
  UploadCloud,
  Cpu,
  ShieldCheck,
  Info,
  Menu,
  X,
  Sparkles,
  Layers,
  Clock
} from 'lucide-react';

/**
 * Header Component (Task 4.29D)
 * Implements the 5-item primary navigation:
 * 1. Observatory
 * 2. Data Input
 * 3. Analysis
 * 4. Evidence
 * 5. About
 * Plus live isolated session telemetry indicator.
 */
export default function Header({
  activeTab = 'OBSERVATORY',
  setActiveTab,
  sessionId = null,
  uploadedFileCount = 0,
  hasAnalysisResults = false
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'OBSERVATORY', label: 'Observatory', icon: Compass, badge: null },
    { id: 'DATA_INPUT', label: 'Data Input', icon: UploadCloud, badge: uploadedFileCount > 0 ? uploadedFileCount : null },
    { id: 'ANALYSIS', label: 'Analysis', icon: Cpu, badge: null },
    { id: 'EVIDENCE', label: 'Evidence', icon: ShieldCheck, badge: hasAnalysisResults ? 'READY' : null },
    { id: 'ABOUT', label: 'About', icon: Info, badge: null }
  ];

  const handleNavClick = (id) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="app-header" role="banner">
      <div className="header-inner flex justify-between items-center">
        {/* Brand Group */}
        <div
          className="brand-group flex items-center gap-3 cursor-pointer select-none"
          onClick={() => handleNavClick('OBSERVATORY')}
          id="header-brand-logo"
        >
          {/* Emblem */}
          <div className="brand-emblem" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="9" fill="url(#planetGradient)" />
              <ellipse
                cx="14"
                cy="14"
                rx="13"
                ry="4.5"
                stroke="var(--color-primary, #42D9F5)"
                strokeWidth="1.6"
                transform="rotate(-25 14 14)"
                strokeDasharray="28 4"
              />
              <defs>
                <linearGradient id="planetGradient" x1="5" y1="5" x2="23" y2="23" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#42D9F5" />
                  <stop offset="0.6" stopColor="#648BFF" />
                  <stop offset="1" stopColor="#111B33" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <div className="brand-text">
            <div className="brand-title-row flex items-center gap-2">
              <span className="brand-name font-heading font-bold text-base tracking-wide text-white">
                SPECTRA-X
              </span>
              <span className="brand-tag text-xs font-mono text-cyan bg-surface px-1.5 py-0.5 rounded border border-border">
                V2.1
              </span>
            </div>
            <span className="brand-subtitle text-xs text-dim block">
              Input-Driven Astronomical Observatory
            </span>
          </div>
        </div>

        {/* Desktop Primary Navigation (5 Items) */}
        <nav className="desktop-nav-menu hidden md:flex items-center gap-1" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                className={`nav-menu-btn ${isActive ? 'active' : ''}`}
                onClick={() => handleNavClick(item.id)}
                id={`nav-${item.id.toLowerCase()}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={16} />
                <span>{item.label}</span>
                {item.badge !== null && (
                  <span className="nav-badge-pill font-mono">{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Session Status & Mobile Toggle */}
        <div className="header-right-tools flex items-center gap-3">
          {/* Isolated Session Pill */}
          <div
            className="session-indicator-pill hidden sm:flex items-center gap-2 font-mono text-xs px-2.5 py-1 rounded-full bg-surface border border-border"
            title={sessionId ? `Session UUID: ${sessionId}` : 'Connecting...'}
          >
            <span className="live-pulse-dot"></span>
            <span className="text-dim">Session:</span>
            <span className="text-white font-medium">
              {sessionId ? sessionId.substring(0, 8) + '...' : 'Active'}
            </span>
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            className="mobile-hamburger-btn md:hidden p-2 rounded-lg bg-surface border border-border text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Close Menu' : 'Open Menu'}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-drawer-menu md:hidden border-t border-border bg-surface p-4 mt-2">
          <div className="flex flex-col gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  className={`mobile-nav-btn flex items-center justify-between p-3 rounded-lg text-sm font-medium ${
                    isActive ? 'bg-card text-cyan border border-cyan' : 'text-dim hover:text-white'
                  }`}
                  onClick={() => handleNavClick(item.id)}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== null && (
                    <span className="nav-badge-pill font-mono">{item.badge}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}
