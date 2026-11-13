import React, { useState } from 'react';
import { Sun, Moon, Globe, Menu, X, Sparkles } from 'lucide-react';

/**
 * TopHeader Component
 * Cosmic nebula banner spanning the top of the observatory:
 * - Slogan: "A Human-AI Co-Pilot for Exploring the Changing Infrared Sky"
 * - Quick action controls: Theme toggle, Language/Coordinate system, User profile avatar
 */
export default function TopHeader({ onToggleMobileNav, mobileNavOpen = false }) {
  const [theme, setTheme] = useState('dark');

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  };

  return (
    <header className="spectra-top-header" role="banner">
      {/* Mobile Drawer Toggle */}
      <button
        className="mobile-nav-toggle md:hidden"
        onClick={onToggleMobileNav}
        aria-label={mobileNavOpen ? 'Close Navigation' : 'Open Navigation'}
      >
        {mobileNavOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Slogan */}
      <div className="header-slogan-wrap">
        <Sparkles size={14} className="slogan-sparkle text-cyan" />
        <span className="header-slogan">
          A Human-AI Co-Pilot for Exploring the Changing Infrared Sky
        </span>
      </div>

      {/* Header Utilities */}
      <div className="header-actions">
        <button
          className="header-action-btn"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          aria-label="Toggle Theme"
        >
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>

        <button
          className="header-action-btn"
          title="Catalog Coordinate System (ICRS / J2000)"
          aria-label="Coordinate System"
        >
          <Globe size={17} />
        </button>

        <div className="user-profile-badge" title="SPECTRA-X Lead Investigator" aria-label="User Profile">
          <span className="user-avatar-text font-mono">S</span>
          <span className="user-online-pip"></span>
        </div>
      </div>
    </header>
  );
}
