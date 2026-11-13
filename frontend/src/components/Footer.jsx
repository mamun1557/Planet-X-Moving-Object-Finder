import React from 'react';
import { ShieldCheck, ExternalLink, Heart } from 'lucide-react';

/**
 * Footer component
 * Implements Section 4.5, 12, & 14 of Planet X UI Documentation:
 * Provenance disclaimer, event accreditation, and scientific trust rules.
 */
export default function Footer({ onNavigate }) {
  return (
    <footer className="app-footer">
      <div className="footer-container">
        <div className="footer-top-row">
          <div className="footer-brand-col">
            <div className="footer-brand-name">
              <span className="text-cyan">Planet X</span>: Moving Object Finder
            </div>
            <p className="footer-description">
              Find what moved. Understand what you are seeing. An evidence-backed moving-object discovery experience built with NASA SPHEREx Level-2 infrared data.
            </p>
            <div className="footer-team-meta">
              <strong>Team VU_VioNux</strong> • Rajshahi, Bangladesh • NASA Space Apps Challenge 2026
            </div>
          </div>

          <div className="footer-links-col">
            <h4 className="footer-heading">Navigation</h4>
            <ul className="footer-link-list">
              <li><button type="button" onClick={() => onNavigate('EXPLORE')}>Explore Sky</button></li>
              <li><button type="button" onClick={() => onNavigate('OBJECTS')}>Detected Objects</button></li>
              <li><button type="button" onClick={() => onNavigate('HOW_IT_WORKS')}>How It Works</button></li>
              <li><button type="button" onClick={() => onNavigate('ABOUT')}>About & Team</button></li>
            </ul>
          </div>

          <div className="footer-links-col">
            <h4 className="footer-heading">NASA Data Sources</h4>
            <ul className="footer-link-list">
              <li>
                <a href="https://irsa.ipac.caltech.edu/Missions/spherex.html" target="_blank" rel="noopener noreferrer">
                  SPHEREx Mission (IPAC) <ExternalLink size={12} className="inline ml-1" />
                </a>
              </li>
              <li>
                <a href="https://gea.esac.esa.int/archive/" target="_blank" rel="noopener noreferrer">
                  Gaia DR3 Astrometry <ExternalLink size={12} className="inline ml-1" />
                </a>
              </li>
              <li>
                <a href="https://science.nasa.gov/mission/spherex/" target="_blank" rel="noopener noreferrer">
                  NASA Science Directorate <ExternalLink size={12} className="inline ml-1" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Mandatory Disclaimer (Section 4.5 & 12) */}
        <div className="footer-disclaimer-box">
          <div className="disclaimer-header">
            <ShieldCheck size={14} className="text-info mr-1 flex-shrink-0" />
            <span className="font-semibold text-xs text-info">NASA Space Apps Challenge Notice & Scientific Trust</span>
          </div>
          <p className="disclaimer-text">
            This project was developed by Team VU_VioNux for the NASA Space Apps Challenge. It utilizes open NASA SPHEREx Level-2 astronomical survey data and open-source scientific software (PyTorch, Astropy, React). This project is not officially endorsed by or an official product of NASA or the Jet Propulsion Laboratory. All demonstrated detections in Field P0003 distinguish observed fluxes from calculated motion vectors and model predictions.
          </p>
        </div>

        <div className="footer-bottom-row">
          <span className="text-xs text-muted">
            © 2026 VU_VioNux. Open-source educational scientific tool.
          </span>
          <span className="text-xs text-muted">
            Pipeline Build: <code className="font-mono text-cyan">l2b-v27-2026-222</code>
          </span>
        </div>
      </div>
    </footer>
  );
}

