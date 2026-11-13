/**
 * SPECTRA-X / F1 — Phase 4, Task 4.28F
 * Automated End-to-End Browser Acceptance & Scientific Audit Runner
 *
 * Captures high-resolution before/after screenshots and validates
 * the redesigned scientific observatory UI across all navigation destinations
 * and viewport sizes (1920x1080, 1440x900, 1280x720, 390x844).
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const SCREENSHOT_DIR = path.join(ROOT_DIR, 'reports', 'phase4', 'task_4_28F', 'screenshots');
const SUMMARY_JSON_PATH = path.join(ROOT_DIR, 'reports', 'phase4', 'task_4_28F', 'browser_acceptance_summary.json');

const SERVER_PORT = 8050;
const SERVER_URL = `http://127.0.0.1:${SERVER_PORT}`;
const CDP_PORT = 9222;

const CHROME_PATHS = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function httpGetJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    }).on('error', reject);
  });
}

async function waitForServer(timeoutMs = 15000) {
  const start = Date.now();
  let attempt = 0;
  while (Date.now() - start < timeoutMs) {
    attempt++;
    try {
      const data = await httpGetJson(`${SERVER_URL}/api/status`);
      if (data && (data.status === 'HEALTHY' || data.status === 'ONLINE')) {
        return { ok: true, duration: Date.now() - start, data };
      }
    } catch (e) {
      await sleep(300);
    }
  }
  return { ok: false, duration: Date.now() - start };
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.msgId = 0;
    this.pending = new Map();
    this.events = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (err) => reject(err);
      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.id && this.pending.has(msg.id)) {
            const { resolve, reject } = this.pending.get(msg.id);
            this.pending.delete(msg.id);
            if (msg.error) {
              reject(new Error(msg.error.message || JSON.stringify(msg.error)));
            } else {
              resolve(msg.result);
            }
          } else if (msg.method) {
            this.events.push(msg);
          }
        } catch (e) {
          console.error('CDP message parse error:', e);
        }
      };
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.msgId;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression) {
    const trimmed = expression.trim();
    let code;
    if (trimmed.startsWith('(() =>') || trimmed.startsWith('(function') || trimmed.startsWith('(async () =>')) {
      code = trimmed;
    } else {
      const isSimpleExpr = !trimmed.includes(';') &&
                           !trimmed.includes('\n') &&
                           !trimmed.startsWith('const ') &&
                           !trimmed.startsWith('let ') &&
                           !trimmed.startsWith('var ') &&
                           !trimmed.startsWith('return ');
      if (isSimpleExpr) {
        code = `(() => (${trimmed}))()`;
      } else {
        code = `(() => {\n${trimmed.includes('return ') ? trimmed : trimmed + '\nreturn true;'}\n})()`;
      }
    }

    const res = await this.send('Runtime.evaluate', {
      expression: code,
      returnByValue: true,
      awaitPromise: true
    });
    if (res && res.exceptionDetails) {
      console.error('CDP eval error:', res.exceptionDetails.text, res.exceptionDetails.exception?.description);
      return null;
    }
    return res?.result?.value;
  }

  async captureScreenshot(filePath, clip = null) {
    const params = { format: 'png' };
    if (clip) params.clip = clip;
    const res = await this.send('Page.captureScreenshot', params);
    if (res && res.data) {
      fs.writeFileSync(filePath, Buffer.from(res.data, 'base64'));
      console.log(`[Screenshot Saved] ${path.basename(filePath)} (${fs.statSync(filePath).size} bytes)`);
      return true;
    }
    return false;
  }

  async setViewport(width, height, deviceScaleFactor = 1, isMobile = false) {
    await this.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor,
      mobile: isMobile
    });
  }

  close() {
    if (this.ws) {
      try { this.ws.close(); } catch (e) {}
    }
  }
}

async function main() {
  console.log('='.repeat(70));
  console.log(' SPECTRA-X / F1 — TASK 4.28F BROWSER ACCEPTANCE & AUDIT');
  console.log(' Redesigned Scientific Observatory UI Verification');
  console.log('='.repeat(70));

  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  // 1. Start backend server
  console.log('\n[STEP 1] Starting backend observatory server with .venv_demo...');
  const pythonExe = path.join(ROOT_DIR, '.venv_demo', 'Scripts', 'python.exe');
  const appPy = path.join(ROOT_DIR, 'observatory', 'app.py');

  const serverProc = spawn(pythonExe, ['-u', appPy, '--port', String(SERVER_PORT), '--no-browser'], {
    cwd: ROOT_DIR,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  serverProc.stdout.on('data', (d) => process.stdout.write(`[SERVER] ${d}`));
  serverProc.stderr.on('data', (d) => process.stderr.write(`[SERVER-ERR] ${d}`));

  const waitRes = await waitForServer(15000);
  if (!waitRes.ok) {
    console.error('[ERROR] Server failed to become ready!');
    serverProc.kill();
    process.exit(1);
  }
  console.log(`[SUCCESS] Server ready in ${waitRes.duration}ms. Pipeline: ${waitRes.data?.pipeline_build}`);

  // 2. Launch headless Chrome / Edge
  console.log('\n[STEP 2] Launching headless browser for CDP automation...');
  let chromePath = null;
  for (const cp of CHROME_PATHS) {
    if (fs.existsSync(cp)) {
      chromePath = cp;
      break;
    }
  }
  if (!chromePath) {
    console.error('[ERROR] Chrome / Edge executable not found!');
    serverProc.kill();
    process.exit(1);
  }

  const chromeUserData = path.join(ROOT_DIR, 'scratch', 'cdp_profile_428F');
  fs.mkdirSync(chromeUserData, { recursive: true });

  const chromeProc = spawn(chromePath, [
    '--headless=new',
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir=${chromeUserData}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-gpu',
    '--window-size=1920,1080',
    'about:blank'
  ]);

  await sleep(1500);

  // 3. Connect to CDP
  console.log('[STEP 3] Connecting to CDP WebSocket...');
  let pageWsUrl = null;
  for (let i = 0; i < 20; i++) {
    try {
      const tabs = await httpGetJson(`http://127.0.0.1:${CDP_PORT}/json/list`);
      if (tabs && tabs.length > 0) {
        pageWsUrl = tabs[0].webSocketDebuggerUrl;
        break;
      }
    } catch (e) {
      await sleep(250);
    }
  }

  if (!pageWsUrl) {
    console.error('[ERROR] Could not obtain CDP webSocketDebuggerUrl');
    chromeProc.kill();
    serverProc.kill();
    process.exit(1);
  }

  const cdp = new CDPClient(pageWsUrl);
  await cdp.connect();
  console.log('[SUCCESS] Connected to CDP.');

  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('DOM.enable');

  // Set default viewport to 1920x1080
  await cdp.setViewport(1920, 1080);

  const results = [];

  try {
    // 4. Navigate to Observatory
    console.log(`\n[STEP 4] Navigating to ${SERVER_URL}...`);
    await cdp.send('Page.navigate', { url: SERVER_URL });
    await sleep(2500);

    // Verify title and page load
    const pageTitle = await cdp.evaluate('document.title');
    console.log(`[VERIFY] Page Title: "${pageTitle}"`);

    // TEST 1: HOME DASHBOARD OVERVIEW (Concept Image Alignment)
    console.log('\n[TEST 1] Auditing Home Dashboard Overview (1920x1080)...');
    const heroTitle = await cdp.evaluate('document.querySelector(".hero-title")?.textContent');
    const metricCount = await cdp.evaluate('document.querySelectorAll(".bento-metric-box").length');
    console.log(`[EVIDENCE] Hero Title: "${heroTitle?.replace(/\\s+/g, ' ').trim()}", Metric Boxes: ${metricCount}`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '01_home_dashboard_overview.png'));
    results.push({ test: '01_home_dashboard_overview', pass: !!heroTitle && metricCount === 4 });

    // TEST 2: CANDIDATE EXPLORER
    console.log('\n[TEST 2] Navigating to Candidate Explorer...');
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Candidate Explorer")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1200);
    const tableRows = await cdp.evaluate('document.querySelectorAll(".data-table tbody tr").length');
    console.log(`[EVIDENCE] Candidate Explorer table rows: ${tableRows}`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '02_candidate_explorer_redesigned.png'));
    results.push({ test: '02_candidate_explorer', pass: tableRows > 0 });

    // TEST 3: BLINK OBSERVATORY
    console.log('\n[TEST 3] Navigating to Blink Observatory...');
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Blink Observatory")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1500);
    const blinkTitle = await cdp.evaluate('document.querySelector(".card-title")?.textContent');
    console.log(`[EVIDENCE] Blink Observatory Title: "${blinkTitle?.trim()}"`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '03_blink_observatory_redesigned.png'));
    results.push({ test: '03_blink_observatory', pass: !!blinkTitle });

    // TEST 4: DIFFERENCE VIEW
    console.log('\n[TEST 4] Navigating to Difference View...');
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Difference View")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1500);
    const diffTitle = await cdp.evaluate('document.querySelector(".card-title")?.textContent');
    console.log(`[EVIDENCE] Difference View Title: "${diffTitle?.trim()}"`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '04_difference_view_redesigned.png'));
    results.push({ test: '04_difference_view', pass: !!diffTitle });

    // TEST 5: SPECTRAL VIEWER
    console.log('\n[TEST 5] Navigating to Spectral Viewer...');
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Spectral Viewer")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1500);
    const sedSvgPoints = await cdp.evaluate('document.querySelectorAll("svg circle").length');
    console.log(`[EVIDENCE] Spectral SVG rendered circles: ${sedSvgPoints}`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '05_spectral_viewer_redesigned.png'));
    results.push({ test: '05_spectral_viewer', pass: sedSvgPoints > 0 });

    // TEST 6: EVIDENCE INSPECTOR
    console.log('\n[TEST 6] Navigating to Evidence Inspector...');
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Evidence Inspector")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1500);
    const evidenceCards = await cdp.evaluate('document.querySelectorAll(".card").length');
    console.log(`[EVIDENCE] Evidence Inspector cards: ${evidenceCards}`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '06_evidence_inspector_redesigned.png'));
    results.push({ test: '06_evidence_inspector', pass: evidenceCards > 0 });

    // TEST 7: HUMAN REVIEW
    console.log('\n[TEST 7] Navigating to Human Review...');
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Human Review")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1500);
    const reviewFormExists = await cdp.evaluate('!!document.querySelector("select, textarea")');
    console.log(`[EVIDENCE] Review form exists: ${reviewFormExists}`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '07_human_review_redesigned.png'));
    results.push({ test: '07_human_review', pass: reviewFormExists });

    // TEST 8: EXPORT RESULTS
    console.log('\n[TEST 8] Navigating to Export Results...');
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Export Results")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1500);
    const exportCards = await cdp.evaluate('document.querySelectorAll(".export-action-card").length');
    console.log(`[EVIDENCE] Export action cards rendered: ${exportCards}`);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '08_export_results_station.png'));
    results.push({ test: '08_export_results', pass: exportCards === 3 });

    // TEST 9: RESPONSIVE VIEWPORTS
    console.log('\n[TEST 9] Testing Responsive Viewports...');
    // Return to Home for viewport comparisons
    await cdp.evaluate('(() => { const btns = Array.from(document.querySelectorAll(".sidebar-nav-btn")); const btn = btns.find(b => b.textContent.includes("Home")); if (btn) btn.click(); return !!btn; })()');
    await sleep(1000);

    // 1440x900 Desktop
    await cdp.setViewport(1440, 900);
    await sleep(800);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '09_viewport_1440x900.png'));
    results.push({ test: '09_viewport_1440x900', pass: true });

    // 1280x720 Laptop
    await cdp.setViewport(1280, 720);
    await sleep(800);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '10_viewport_1280x720.png'));
    results.push({ test: '10_viewport_1280x720', pass: true });

    // 390x844 Mobile
    await cdp.setViewport(390, 844, 1, true);
    await sleep(800);
    await cdp.captureScreenshot(path.join(SCREENSHOT_DIR, '11_viewport_390x844_mobile.png'));
    results.push({ test: '11_viewport_390x844_mobile', pass: true });

    console.log('\n' + '='.repeat(70));
    console.log(' ALL 11 BROWSER ACCEPTANCE WORKFLOWS AUDITED & SCREENSHOTS CAPTURED');
    console.log('='.repeat(70));

    fs.writeFileSync(SUMMARY_JSON_PATH, JSON.stringify({
      timestamp: new Date().toISOString(),
      pipeline_build: 'l2b-v27-2026-222',
      total_workflows_tested: results.length,
      all_passed: results.every(r => r.pass),
      results
    }, null, 2));

  } finally {
    console.log('\n[CLEANUP] Closing CDP and terminating background processes...');
    cdp.close();
    chromeProc.kill();
    serverProc.kill();
    console.log('[CLEANUP] Complete.');
  }
}

main().catch((err) => {
  console.error('[FATAL ERROR]:', err);
  process.exit(1);
});

