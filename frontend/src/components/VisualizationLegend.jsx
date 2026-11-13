import React from 'react';

/**
 * VisualizationLegend component
 * Implements Section 6.2 and Section 14 of Planet X UI Documentation:
 * Explains every visual role, color, and line style clearly.
 */
export default function VisualizationLegend({ className = '' }) {
  const legendItems = [
    { label: 'Selected Object', color: 'var(--vis-selected, #42D9F5)', style: 'solid-dot', desc: 'Active target under inspection' },
    { label: 'Track / Trajectory', color: 'var(--vis-track, #9B8CFF)', style: 'solid-line', desc: 'Measured or estimated motion vector' },
    { label: 'Historical Position', color: 'var(--vis-historical, #648BFF)', style: 'dashed-dot', desc: 'Prior observation epoch position' },
    { label: 'Reference Grid', color: 'var(--vis-grid, #344563)', style: 'grid-line', desc: 'Celestial equatorial coordinate grid (RA/Dec)' },
    { label: 'Uncertain / Dither Segment', color: 'var(--vis-uncertain, #FFC66D)', style: 'dashed-line', desc: 'Intra-visit pointing displacement' },
    { label: 'Other Detected Objects', color: 'var(--vis-inactive, #8493AD)', style: 'muted-dot', desc: 'Cataloged infrared sources' },
  ];

  return (
    <div className={`vis-legend-card ${className}`}>
      <div className="vis-legend-header">
        <span className="vis-legend-title">Sky Map Legend</span>
        <span className="badge badge-demo">Demo Data: Field P0003</span>
      </div>
      <div className="vis-legend-grid">
        {legendItems.map((item, idx) => (
          <div key={idx} className="legend-item" title={item.desc}>
            <span
              className={`legend-swatch swatch-${item.style}`}
              style={{ backgroundColor: item.color }}
            />
            <div className="legend-text">
              <span className="legend-label">{item.label}</span>
              <span className="legend-desc">{item.desc}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

