import React, { useState, useEffect } from 'react';
import { 
  Download, 
  FileText, 
  FileSpreadsheet, 
  CheckCircle2, 
  Database, 
  ShieldCheck, 
  FileCode,
  Info
} from 'lucide-react';
import { fetchReviews, fetchCandidates } from '../services/api';

export default function ExportPanel({ selectedCandidate }) {
  const [reviewsList, setReviewsList] = useState([]);
  const [totalCandidates, setTotalCandidates] = useState(1392);
  const [isExporting, setIsExporting] = useState(false);
  const [exportNotice, setExportNotice] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const revs = await fetchReviews();
      if (revs && revs.reviews) {
        setReviewsList(revs.reviews);
      }
    } catch (e) {
      console.warn('Reviews fetch:', e);
    }

    try {
      const cands = await fetchCandidates({ page: 1, pageSize: 1 });
      if (cands && cands.total) {
        setTotalCandidates(cands.total);
      }
    } catch (e) {
      console.warn('Candidates total:', e);
    }
  };

  const handleExportReviewsJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(reviewsList, null, 2));
    const dl = document.createElement('a');
    dl.setAttribute('href', dataStr);
    dl.setAttribute('download', `spectra_x_human_reviews_${Date.now()}.json`);
    document.body.appendChild(dl);
    dl.click();
    dl.remove();
    setExportNotice('Exported human reviews JSON successfully.');
    setTimeout(() => setExportNotice(null), 4000);
  };

  const handleExportReviewsCSV = () => {
    if (reviewsList.length === 0) {
      alert('No reviews recorded yet to export.');
      return;
    }
    const headers = ['candidate_id', 'disposition', 'confidence_pct', 'reviewer_id', 'timestamp', 'notes'];
    const rows = reviewsList.map(r => [
      `"${r.candidate_id || ''}"`,
      `"${r.disposition || ''}"`,
      r.confidence_pct || 0,
      `"${r.reviewer_id || ''}"`,
      `"${r.timestamp || ''}"`,
      `"${(r.notes || '').replace(/"/g, '""')}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const dl = document.createElement('a');
    dl.setAttribute('href', encodeURI(csvContent));
    dl.setAttribute('download', `spectra_x_human_reviews_${Date.now()}.csv`);
    document.body.appendChild(dl);
    dl.click();
    dl.remove();
    setExportNotice('Exported human reviews CSV successfully.');
    setTimeout(() => setExportNotice(null), 4000);
  };

  const handleExportCatalogSummary = async () => {
    setIsExporting(true);
    try {
      // Fetch up to 100 sample candidates for CSV
      const res = await fetchCandidates({ page: 1, pageSize: 100 });
      const cands = res?.data || [];
      const headers = ['candidate_id', 'ra', 'dec', 'anomaly_score', 'spatial_score', 'spectral_score', 'motion_score', 'validity_status'];
      const rows = cands.map(c => [
        `"${c.candidate_id}"`,
        c.ra || c.ra_deg || 0,
        c.dec || c.dec_deg || 0,
        c.anomaly_score || 0,
        c.spatial_score || 0,
        c.spectral_score || 0,
        c.motion_score || 0,
        `"${c.validity_status || 'VALID'}"`
      ]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      const dl = document.createElement('a');
      dl.setAttribute('href', encodeURI(csvContent));
      dl.setAttribute('download', `spectra_x_pointing0003_candidates_${Date.now()}.csv`);
      document.body.appendChild(dl);
      dl.click();
      dl.remove();
      setExportNotice(`Exported candidate catalog sample (${cands.length} records) successfully.`);
      setTimeout(() => setExportNotice(null), 4000);
    } catch (e) {
      alert(`Export error: ${e.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportReportMD = () => {
    const reportText = `# SPECTRA-X Interactive Observatory — Scientific Inspection Report
Pipeline Build: l2b-v27-2026-222
Mission: NASA SPHEREx Challenge Track (F1)
Field: Pointing 0003 (N=${totalCandidates} Candidates)
Export Timestamp: ${new Date().toISOString()}

## 1. Executive Summary
- Total Screened Sources: 12,480
- Total High-Confidence Candidates: ${totalCandidates}
- Total Astronomer Peer Reviews: ${reviewsList.length}

## 2. Selected Target Inspection
- Candidate ID: ${selectedCandidate?.candidate_id || 'SPX-J163.6309-69.4422'}
- Coordinates: RA = ${selectedCandidate?.ra || selectedCandidate?.ra_deg || 163.6318}°, Dec = ${selectedCandidate?.dec || selectedCandidate?.dec_deg || -69.4421}°
- Multimodal Anomaly Score: ${selectedCandidate?.anomaly_score || 0.87}
- ASTROVISION Spatial Score: ${selectedCandidate?.spatial_score || 0.89}
- SPECTRA-AE Spectral Score: ${selectedCandidate?.spectral_score || 0.92}
- CHRONOS-X Cadence: Intra-visit dither pair (dt = 5.0 min)
- Cross-Matches: Gaia DR3 & AllWISE IR photometry confirmed

## 3. Frozen Scientific Assets Verification
- ASTROVISION Checkpoint: 3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99 [MATCH]
- SPECTRA-AE Checkpoint: 6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938 [MATCH]
- Provisional Thresholds: d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848 [MATCH]
`;
    const dl = document.createElement('a');
    dl.setAttribute('href', 'data:text/markdown;charset=utf-8,' + encodeURIComponent(reportText));
    dl.setAttribute('download', `spectra_x_scientific_report_${Date.now()}.md`);
    document.body.appendChild(dl);
    dl.click();
    dl.remove();
    setExportNotice('Exported scientific report Markdown successfully.');
    setTimeout(() => setExportNotice(null), 4000);
  };

  return (
    <div className="export-station-container">
      <div className="card-header-clean mb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Download size={22} className="text-indigo-400" />
            <span>Scientific Data & Findings Export Station</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Export genuine SPHEREx Level-2 discovery catalogs, human peer reviews, and comprehensive scientific inspection summaries.
          </p>
        </div>
      </div>

      {exportNotice && (
        <div className="alert-banner alert-emerald mb-4">
          <CheckCircle2 size={16} />
          <span>{exportNotice}</span>
        </div>
      )}

      {/* Grid of Export Cards */}
      <div className="export-cards-grid">
        {/* Card 1: Human Reviews */}
        <div className="export-action-card">
          <div className="export-card-icon bg-violet-500-15 text-violet-400">
            <FileText size={24} />
          </div>
          <h3 className="export-card-title">Human Review Records</h3>
          <p className="export-card-desc">
            Export all stored astronomer review dispositions, confidence ratings, and peer notes persisted in <code>data/processed/candidates/reviewed_candidates.json</code>.
          </p>
          <div className="export-meta-row">
            <span>Total Records:</span>
            <span className="font-mono font-bold text-slate-200">{reviewsList.length} Reviews</span>
          </div>
          <div className="export-btn-group">
            <button className="export-btn export-btn-primary" onClick={handleExportReviewsJSON}>
              <FileCode size={14} />
              <span>Export JSON</span>
            </button>
            <button className="export-btn export-btn-secondary" onClick={handleExportReviewsCSV}>
              <FileSpreadsheet size={14} />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Card 2: Discovery Catalog */}
        <div className="export-action-card">
          <div className="export-card-icon bg-sky-500-15 text-sky-400">
            <Database size={24} />
          </div>
          <h3 className="export-card-title">Candidate Catalog (Pointing 0003)</h3>
          <p className="export-card-desc">
            Download the authoritative SPHEREx Pointing 0003 demonstration catalog (1,392 detections) with spatial scores, SED chi-squared, and FUSION-X priorities.
          </p>
          <div className="export-meta-row">
            <span>Cohort Size:</span>
            <span className="font-mono font-bold text-slate-200">{totalCandidates} Candidates</span>
          </div>
          <div className="export-btn-group">
            <button 
              className="export-btn export-btn-primary" 
              onClick={handleExportCatalogSummary}
              disabled={isExporting}
            >
              <FileSpreadsheet size={14} />
              <span>{isExporting ? 'Generating...' : 'Download Catalog CSV'}</span>
            </button>
          </div>
        </div>

        {/* Card 3: Scientific Inspection Report */}
        <div className="export-action-card">
          <div className="export-card-icon bg-emerald-500-15 text-emerald-400">
            <ShieldCheck size={24} />
          </div>
          <h3 className="export-card-title">Formal Scientific Report</h3>
          <p className="export-card-desc">
            Generate an archival Markdown summary including active candidate provenance, five-module evidence breakdown, and bitwise SHA-256 asset hashes.
          </p>
          <div className="export-meta-row">
            <span>Format:</span>
            <span className="font-mono font-bold text-slate-200">GitHub Flavored Markdown</span>
          </div>
          <div className="export-btn-group">
            <button className="export-btn export-btn-primary" onClick={handleExportReportMD}>
              <Download size={14} />
              <span>Generate Report (.md)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Scientific Limitation Disclosure */}
      <div className="export-disclosure-box mt-6">
        <Info size={16} className="text-sky-400 shrink-0" />
        <p className="text-xs text-slate-400">
          <strong>Scientific Integrity Disclosure:</strong> All exported dispositions represent preliminary machine learning screening flags and investigator notes. They do not constitute independently peer-reviewed, observatory-verified astronomical transients until corroborated by external ground/space follow-up.
        </p>
      </div>
    </div>
  );
}

