import React, { useState, useEffect } from 'react';
import { ClipboardCheck, Download, Save, History, CheckCircle2, AlertCircle } from 'lucide-react';
import { postReview, fetchReviews } from '../services/api';

export default function ReviewPanel({ candidate, onReviewSaved, onNavigateToExport }) {
  const [disposition, setDisposition] = useState('NEEDS_FOLLOWUP');
  const [confidence, setConfidence] = useState(85);
  const [reviewer, setReviewer] = useState('NASA_INVESTIGATOR_01');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState(null);
  const [reviewsList, setReviewsList] = useState([]);

  useEffect(() => {
    loadReviews();
  }, [candidate]);

  const loadReviews = async () => {
    try {
      const res = await fetchReviews();
      if (res && res.reviews) {
        setReviewsList(res.reviews);
      }
    } catch (e) {
      console.error('Failed to load reviews:', e);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!candidate) return;
    setSubmitting(true);
    setSubmitMsg(null);

    const payload = {
      candidate_id: candidate.candidate_id,
      ra_deg: candidate.ra_deg || candidate.ra,
      dec_deg: candidate.dec_deg || candidate.dec,
      disposition,
      confidence_pct: confidence,
      reviewer_id: reviewer,
      notes,
      spatial_score: candidate.spatial_score,
      spectral_score: candidate.spectral_score,
      anomaly_score: candidate.anomaly_score || candidate.fusion_score
    };

    try {
      const res = await postReview(payload);
      setSubmitMsg({ type: 'success', text: `Review saved for ${candidate.candidate_id}` });
      setNotes('');
      await loadReviews();
      if (onReviewSaved) onReviewSaved();
    } catch (err) {
      setSubmitMsg({ type: 'error', text: err.message || 'Failed to submit review' });
    } finally {
      setSubmitting(false);
    }
  };

  if (!candidate) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
        <p>Select a candidate to access the Scientific Review & Disposition Panel.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">
            <ClipboardCheck size={18} color="#38bdf8" />
            <span>Scientific Review & Expert Disposition Panel</span>
          </div>
          <div className="card-subtitle font-mono">
            Candidate: {candidate.candidate_id} | Authoritative human-in-the-loop classification
          </div>
        </div>

        <div>
          {onNavigateToExport && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onNavigateToExport}
              title="Open full Export Data Station"
            >
              <Download size={14} className="mr-1" />
              <span>Export Station ↗</span>
            </button>
          )}
        </div>
      </div>

      <div className="grid-2">
        {/* Review Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#cbd5e1', marginBottom: '6px' }}>
              Scientific Disposition
            </label>
            <select
              className="select-input"
              style={{ width: '100%' }}
              value={disposition}
              onChange={(e) => setDisposition(e.target.value)}
            >
              <option value="NEEDS_FOLLOWUP">NEEDS_FOLLOWUP (Flag for High-Cadence Re-observation)</option>
              <option value="CONFIRMED_CANDIDATE">CONFIRMED_CANDIDATE (Candidate Astrophysical Anomaly)</option>
              <option value="INSTRUMENTAL_ARTIFACT">INSTRUMENTAL_ARTIFACT (Pointing Jitter / Glint / Dipole)</option>
              <option value="ASTROPHYSICAL_TRANSIENT">ASTROPHYSICAL_TRANSIENT (High-Confidence Transient)</option>
              <option value="REJECTED">REJECTED (Spurious / Noise Fluctuation)</option>
            </select>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.78rem', color: '#cbd5e1' }}>Confidence Assessment</label>
              <span className="font-mono" style={{ fontSize: '0.8rem', color: '#38bdf8' }}>{confidence}%</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={confidence}
              onChange={(e) => setConfidence(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: '#38bdf8' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#cbd5e1', marginBottom: '6px' }}>
              Investigator / Operator ID
            </label>
            <input
              type="text"
              className="input-text"
              style={{ width: '100%' }}
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
              placeholder="e.g. NASA_SPACEAPPS_TEAM_01"
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#cbd5e1', marginBottom: '6px' }}>
              Scientific Notes & Observations
            </label>
            <textarea
              className="textarea-input"
              style={{ width: '100%', height: '90px', resize: 'vertical' }}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record morphological notes, SED peculiarities, or telescope dither alignment commentary..."
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
            style={{ width: '100%', padding: '10px' }}
          >
            <Save size={16} />
            <span>{submitting ? 'Saving Review...' : 'Record Scientific Review'}</span>
          </button>

          {submitMsg && (
            <div
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: submitMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                color: submitMsg.type === 'success' ? '#6ee7b7' : '#fda4af',
                border: `1px solid ${submitMsg.type === 'success' ? '#10b981' : '#f43f5e'}`
              }}
            >
              {submitMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
              <span>{submitMsg.text}</span>
            </div>
          )}
        </form>

        {/* Review Log History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: 600, color: '#94a3b8' }}>
            <History size={16} />
            <span>Audit Trail & Historical Dispositions ({reviewsList.length})</span>
          </div>

          <div
            style={{
              maxHeight: '340px',
              overflowY: 'auto',
              background: '#080c14',
              borderRadius: '8px',
              border: '1px solid #1e293b',
              padding: '8px'
            }}
          >
            {reviewsList.map((r, i) => (
              <div
                key={i}
                style={{
                  padding: '8px 12px',
                  borderBottom: i < reviewsList.length - 1 ? '1px solid #141b29' : 'none',
                  fontSize: '0.78rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span className="font-mono" style={{ fontWeight: 700, color: '#38bdf8' }}>
                    {r.candidate_id}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                    {r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : 'Recent'}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', margin: '4px 0' }}>
                  <span
                    style={{
                      background: 'rgba(56, 189, 248, 0.15)',
                      color: '#38bdf8',
                      padding: '1px 6px',
                      borderRadius: '4px',
                      fontSize: '0.68rem',
                      fontFamily: 'monospace'
                    }}
                  >
                    {r.disposition}
                  </span>
                  <span style={{ color: '#94a3b8', fontSize: '0.7rem' }}>
                    Conf: {r.confidence_pct}% &bull; By: {r.reviewer_id}
                  </span>
                </div>
                {r.notes && (
                  <div style={{ color: '#cbd5e1', fontStyle: 'italic', fontSize: '0.74rem', marginTop: '2px' }}>
                    "{r.notes}"
                  </div>
                )}
              </div>
            ))}
            {reviewsList.length === 0 && (
              <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '0.8rem' }}>
                No reviews recorded yet in this session.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

