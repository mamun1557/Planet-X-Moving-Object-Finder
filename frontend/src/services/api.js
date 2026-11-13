/**
 * SPECTRA-X Interactive Observatory — API Service
 * Input-driven, session-isolated client interface connecting to Python REST API backend.
 * Task 4.29D Implementation.
 */

const API_BASE = '';

/**
 * Session Management APIs (Task 4.29B)
 */

export async function createSession() {
  const resp = await fetch(`${API_BASE}/api/session/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to create session`);
  return resp.json();
}

export async function getSessionInfo(sessionId) {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const resp = await fetch(`${API_BASE}/api/session/info${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`, {
    method: 'GET',
    headers
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to fetch session info`);
  return resp.json();
}

export async function resetSession(sessionId) {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const resp = await fetch(`${API_BASE}/api/session/reset`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ session_id: sessionId })
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to reset session`);
  return resp.json();
}

export async function deleteSession(sessionId) {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const resp = await fetch(`${API_BASE}/api/session${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`, {
    method: 'DELETE',
    headers
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to delete session`);
  return resp.json();
}

/**
 * Astronomical Motion Engine API (Task 4.29B)
 */
export async function analyzeMotion({ obsA, obsB, sigmaA = null, sigmaB = null, sessionId = null }) {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const payload = {
    obs_a: obsA,
    obs_b: obsB,
    sigma_a_arcsec: sigmaA,
    sigma_b_arcsec: sigmaB
  };
  const resp = await fetch(`${API_BASE}/api/motion/analyze`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  });
  const data = await resp.json().catch(() => ({ status: 'ERROR', message: 'Failed to parse JSON' }));
  return { ok: resp.ok, status: resp.status, data };
}

/**
 * Optional Sample Library APIs (Task 4.29B / 4.29C)
 */
export async function fetchSampleList() {
  const resp = await fetch(`${API_BASE}/api/samples/list`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to fetch sample library list`);
  return resp.json();
}

export async function fetchSample(pairId) {
  const resp = await fetch(`${API_BASE}/api/samples/get?pair_id=${encodeURIComponent(pairId)}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to fetch sample pair`);
  return resp.json();
}

export async function loadSampleIntoSession(sessionId, pairId) {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const resp = await fetch(`${API_BASE}/api/samples/load`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ pair_id: pairId, session_id: sessionId })
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ message: 'Failed to load sample' }));
    throw new Error(err.message || `HTTP ${resp.status}`);
  }
  return resp.json();
}

/**
 * Input Validation & Ingestion APIs
 */
export async function validateAstronomicalData({ filename, content, fileType }) {
  const resp = await fetch(`${API_BASE}/api/data/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename,
      content,
      file_type: fileType
    })
  });
  return resp.json();
}

export async function uploadCustomDataset(datasetPayload, sessionId = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const resp = await fetch(`${API_BASE}/api/data/upload`, {
    method: 'POST',
    headers,
    body: JSON.stringify(datasetPayload)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ message: 'Upload failed' }));
    throw new Error(err.message || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export async function clearCustomDataset(sessionId = null) {
  const headers = {};
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const resp = await fetch(`${API_BASE}/api/data/upload`, {
    method: 'DELETE',
    headers
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to clear custom dataset`);
  return resp.json();
}

export async function fetchSystemStatus() {
  const resp = await fetch(`${API_BASE}/api/status`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to fetch system status`);
  return resp.json();
}

export async function searchTargetCoordinates({ ra, dec, radiusArcsec = 30 }) {
  const resp = await fetch(`${API_BASE}/api/target/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ra, dec, radius_arcsec: radiusArcsec })
  });
  return resp.json();
}

export async function fetchCutout(candidateId) {
  const resp = await fetch(`${API_BASE}/api/cutout/${encodeURIComponent(candidateId)}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to fetch FITS cutout`);
  return resp.json();
}

export async function fetchSpectrum(candidateId) {
  const resp = await fetch(`${API_BASE}/api/spectrum/${encodeURIComponent(candidateId)}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to fetch spectrum`);
  return resp.json();
}

export async function postReview(reviewPayload) {
  const resp = await fetch(`${API_BASE}/api/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reviewPayload)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ message: 'Submission failed' }));
    throw new Error(err.message || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export async function fetchReviews() {
  const resp = await fetch(`${API_BASE}/api/reviews`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: Failed to fetch reviews`);
  return resp.json();
}
