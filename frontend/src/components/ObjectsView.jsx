import React, { useState } from 'react';
import {
  Search,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Layers,
  Activity,
  Sliders,
  CheckCircle,
  AlertTriangle,
  FileText,
  Download,
  Eye
} from 'lucide-react';
import BlinkViewer from './BlinkViewer';
import FitsViewer from './FitsViewer';
import DifferenceViewer from './DifferenceViewer';
import SpectralViewer from './SpectralViewer';
import EvidenceInspector from './EvidenceInspector';
import ReviewPanel from './ReviewPanel';
import ExportPanel from './ExportPanel';

/**
 * ObjectsView component
 * Implements Section 4.2 & 4.3 of Planet X UI Documentation:
 * Searchable, filterable catalogue of detected objects with comprehensive Object Detail view.
 */
export default function ObjectsView({
  candidates = [],
  totalCandidates = 1392,
  page = 1,
  pageSize = 25,
  setPage,
  search = '',
  setSearch,
  validity = 'ALL',
  setValidity,
  sortBy = 'anomaly_score',
  setSortBy,
  sortOrder = 'desc',
  setSortOrder,
  selectedCandidate = null,
  onSelectCandidate,
  cutoutData = null,
  spectrumData = null,
  onReviewSaved
}) {
  const [detailTab, setDetailTab] = useState('BLINK'); // BLINK, DIFFERENCE, SPECTRUM, EVIDENCE, REVIEW, EXPORT
  const totalPages = Math.ceil(totalCandidates / pageSize) || 1;

  const handleClearFilters = () => {
    setSearch('');
    setValidity('ALL');
    setSortBy('anomaly_score');
    setSortOrder('desc');
    setPage(1);
  };

  const currentCand = selectedCandidate || (candidates.length > 0 ? candidates[0] : null);

  return (
    <div className="objects-view-wrapper">
      {/* Page Title & Search/Filter Bar (Section 4.2) */}
      <section className="objects-control-section card">
        <div className="objects-header-row">
          <div>
            <h2 className="section-title">Detected Infrared Objects & Transients</h2>
            <p className="section-subtitle">
              {totalCandidates.toLocaleString()} cataloged sources in SPHEREx Field P0003 • Filter and inspect astrometric evidence
            </p>
          </div>

          <div className="provenance-badges">
            <span className="badge badge-observed">Observed: SPHEREx L2</span>
            <span className="badge badge-calculated">Calculated: MOTION-X</span>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="filter-controls-bar">
          {/* Search Input */}
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by object name (e.g. SPX-J163...)"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              aria-label="Search candidate objects"
            />
            {search && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => setSearch('')}
                title="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Classification Filter Dropdown */}
          <div className="filter-select-wrapper">
            <Filter size={14} className="filter-select-icon" />
            <select
              className="filter-select"
              value={validity}
              onChange={(e) => {
                setValidity(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by classification"
            >
              <option value="ALL">All Categories</option>
              <option value="VALID">High Priority Candidates</option>
              <option value="SUSPECT">Suspect / Needs Review</option>
              <option value="ARTIFACT">Known Artifacts / Dithers</option>
            </select>
          </div>

          {/* Sort By Dropdown */}
          <div className="filter-select-wrapper">
            <select
              className="filter-select"
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
              }}
              aria-label="Sort objects by"
            >
              <option value="anomaly_score">Sort: Anomaly Score</option>
              <option value="ra">Sort: Right Ascension (RA)</option>
              <option value="dec">Sort: Declination (Dec)</option>
            </select>
          </div>

          {/* Sort Order Toggle */}
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            title="Toggle sort direction"
          >
            {sortOrder === 'desc' ? 'Desc ↓' : 'Asc ↑'}
          </button>

          {/* Clear All Filters */}
          {(search || validity !== 'ALL' || sortBy !== 'anomaly_score') && (
            <button
              type="button"
              className="btn btn-subtle btn-sm text-cyan"
              onClick={handleClearFilters}
            >
              Clear Filters
            </button>
          )}
        </div>
      </section>

      {/* Main Split Layout: Objects List Table (Left) + Detailed Object Inspector (Right) */}
      <div className="objects-split-layout">
        {/* Left Column: Accessible Object Catalog Table */}
        <div className="objects-table-container card">
          <div className="table-top-status">
            <span className="text-sm font-semibold">
              Showing Page {page} of {totalPages}
            </span>
            <span className="text-xs text-muted">
              {totalCandidates} total sources
            </span>
          </div>

          <div className="table-scroll-wrapper">
            <table className="objects-table" aria-label="Detected Objects List">
              <thead>
                <tr>
                  <th>Object Identifier</th>
                  <th>Category</th>
                  <th>RA (J2000)</th>
                  <th>Dec (J2000)</th>
                  <th>Priority</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-8 text-muted">
                      No objects match these filters. Try clearing a filter.
                    </td>
                  </tr>
                ) : (
                  candidates.map((cand) => {
                    const isSelected = currentCand && cand.candidate_id === currentCand.candidate_id;
                    const ra = Number(cand.ra) || 163.6309;
                    const dec = Number(cand.dec) || -69.4422;
                    const score = cand.anomaly_score !== undefined ? Number(cand.anomaly_score).toFixed(2) : '—';
                    const cat = cand.classification || 'Transient Candidate';

                    return (
                      <tr
                        key={cand.candidate_id}
                        className={`object-table-row ${isSelected ? 'row-selected' : ''}`}
                        onClick={() => onSelectCandidate(cand)}
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') onSelectCandidate(cand);
                        }}
                      >
                        <td className="font-mono text-cyan font-semibold">
                          {cand.candidate_id}
                        </td>
                        <td>
                          <span className="object-type-badge">{cat}</span>
                        </td>
                        <td className="font-mono">{ra.toFixed(4)}°</td>
                        <td className="font-mono">{dec.toFixed(4)}°</td>
                        <td>
                          <span className="badge badge-surface font-mono">{score}</span>
                        </td>
                        <td className="text-xs text-muted">SPHEREx P0003</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="table-pagination-row">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
            >
              <ChevronLeft size={14} className="mr-1" />
              Previous
            </button>
            <span className="text-xs text-muted font-mono">
              Page {page} / {totalPages}
            </span>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            >
              Next
              <ChevronRight size={14} className="ml-1" />
            </button>
          </div>
        </div>

        {/* Right Column: Object Detail & Scientific Evidence View (Section 4.3) */}
        <div className="object-detail-container card">
          {currentCand ? (
            <>
              {/* Detail Header */}
              <div className="detail-header-row">
                <div>
                  <div className="provenance-badges mb-1">
                    <span className="badge badge-observed">Observed</span>
                    <span className="badge badge-calculated">Calculated</span>
                    <span className="badge badge-predicted">Predicted (AE)</span>
                  </div>
                  <h3 className="detail-object-title font-mono text-cyan">{currentCand.candidate_id}</h3>
                  <p className="detail-object-subtitle">
                    RA: {Number(currentCand.ra).toFixed(4)}° • Dec: {Number(currentCand.dec).toFixed(4)}° • SPHEREx Survey Field P0003
                  </p>
                </div>

                <div className="detail-action-badges">
                  <a
                    href="https://irsa.ipac.caltech.edu/Missions/spherex.html"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-subtle btn-sm text-cyan"
                    title="View NASA Archive Record"
                  >
                    NASA Archive <ExternalLink size={12} className="inline ml-1" />
                  </a>
                </div>
              </div>

              {/* Evidence Navigation Tabs */}
              <div className="detail-subtabs-nav" role="tablist">
                {[
                  { id: 'BLINK', label: 'Blink Comparator' },
                  { id: 'DIFFERENCE', label: 'Difference Maps' },
                  { id: 'SPECTRUM', label: '102-ch SED' },
                  { id: 'EVIDENCE', label: 'AI Diagnostics' },
                  { id: 'REVIEW', label: 'Human Review' },
                  { id: 'EXPORT', label: 'Export Data' }
                ].map(tab => (
                  <button
                    key={tab.id}
                    type="button"
                    role="tab"
                    aria-selected={detailTab === tab.id}
                    className={`detail-subtab-btn ${detailTab === tab.id ? 'active' : ''}`}
                    onClick={() => setDetailTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content Panels */}
              <div className="detail-tab-body">
                {detailTab === 'BLINK' && (
                  <div className="detail-subview">
                    <BlinkViewer cutoutData={cutoutData} candidate={currentCand} />
                    <FitsViewer cutoutData={cutoutData} candidate={currentCand} />
                  </div>
                )}

                {detailTab === 'DIFFERENCE' && (
                  <div className="detail-subview">
                    <DifferenceViewer cutoutData={cutoutData} candidate={currentCand} />
                  </div>
                )}

                {detailTab === 'SPECTRUM' && (
                  <div className="detail-subview">
                    <SpectralViewer spectrumData={spectrumData} candidate={currentCand} />
                  </div>
                )}

                {detailTab === 'EVIDENCE' && (
                  <div className="detail-subview">
                    <EvidenceInspector
                      candidate={currentCand}
                      cutoutData={cutoutData}
                      spectrumData={spectrumData}
                    />
                  </div>
                )}

                {detailTab === 'REVIEW' && (
                  <div className="detail-subview">
                    <ReviewPanel
                      candidate={currentCand}
                      onReviewSaved={onReviewSaved}
                      onNavigateToExport={() => setDetailTab('EXPORT')}
                    />
                  </div>
                )}

                {detailTab === 'EXPORT' && (
                  <div className="detail-subview">
                    <ExportPanel selectedCandidate={currentCand} />
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="detail-empty-state">
              <p className="text-muted">Select an object from the catalog to inspect its scientific evidence.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

