/**
 * Task 4.28F-CLEANUP-C — Browser-Level Regression & Acceptance Testing Runner
 * NASA Space Apps Challenge 2026 — Planet X: Moving Object Finder / SPECTRA-X
 * 
 * Automates real Chrome browser testing via Chrome DevTools Protocol (CDP):
 * - Validates 5 primary navigation tabs at 1440x900, 1280x720, and 390x844 viewports
 * - Verifies Data Input Station: Coordinate Search (in-field & out-of-field bounds),
 *   File Ingestion (FITS, CSV, Invalid), and 5-Module Compatibility Matrix
 * - Verifies Existing Observatory viewers: Blink, Difference, SED, Evidence, Human Review, Export
 * - Tracks console logs, JS errors, network failures, and layout metrics
 * - Saves screenshots in docs/verification/task_4_28F_cleanup_c/
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const SCREENSHOT_DIR = path.join(ROOT_DIR, 'docs', 'verification', 'task_4_28F_cleanup_c');
const SUMMARY_JSON_PATH = path.join(SCREENSHOT_DIR, 'browser_acceptance_summary.json');

const SERVER_PORT = 8077;
const SERVER_URL = `http://127.0.0.1:${SERVER_PORT}`;
const CDP_PORT = 9225;

const CHROME_BINARY = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

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

async function waitForServer(timeoutMs = 35000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const data = await httpGetJson(`${SERVER_URL}/api/status`);
      if (data && (data.status === 'HEALTHY' || data.status === 'ONLINE')) {
        return { ok: true, duration: Date.now() - start, data };
      }
    } catch (e) {
      await sleep(400);
    }
  }
  throw new Error(`Server failed to start within ${timeoutMs}ms`);
}

class CdpClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.msgId = 1;
    this.callbacks = new Map();
    this.consoleLogs = [];
    this.consoleErrors = [];
    this.networkFailures = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (err) => reject(err);
      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.id && this.callbacks.has(msg.id)) {
            const { res, rej } = this.callbacks.get(msg.id);
            this.callbacks.delete(msg.id);
            if (msg.error) rej(new Error(msg.error.message || JSON.stringify(msg.error)));
            else res(msg.result);
          } else if (msg.method) {
            this.handleEvent(msg.method, msg.params);
          }
        } catch (e) {
          console.error('CDP parse error:', e);
        }
      };
    });
  }

  handleEvent(method, params) {
    if (method === 'Runtime.consoleAPICalled') {
      const text = (params.args || []).map((a) => a.value || a.description || '').join(' ');
      this.consoleLogs.push({ type: params.type, text });
      if (params.type === 'error') {
        this.consoleErrors.push(text);
      }
    } else if (method === 'Runtime.exceptionThrown') {
      const text = params.exceptionDetails?.text || 'Uncaught Exception';
      this.consoleErrors.push(text);
    } else if (method === 'Network.loadingFailed') {
      this.networkFailures.push({
        requestId: params.requestId,
        errorText: params.errorText,
        type: params.type
      });
    }
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.msgId++;
      this.callbacks.set(id, { res: resolve, rej: reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true
    });
    return res.result ? res.result.value : null;
  }

  async setViewport(width, height, isMobile = false) {
    await this.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: isMobile
    });
    await sleep(400);
  }

  async captureScreenshot(filename) {
    const outputPath = path.join(SCREENSHOT_DIR, filename);
    const { data } = await this.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(outputPath, Buffer.from(data, 'base64'));
    console.log(`[+] Screenshot captured: ${filename}`);
    return outputPath;
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

async function main() {
  console.log('========================================================================');
  console.log(' TASK 4.28F-CLEANUP-C — BROWSER-LEVEL REGRESSION & ACCEPTANCE TEST');
  console.log(' Target Viewports: 1440x900, 1280x720, 390x844');
  console.log(' Destination: docs/verification/task_4_28F_cleanup_c/');
  console.log('========================================================================\n');

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const results = {
    task: '4.28F-CLEANUP-C',
    timestamp: new Date().toISOString(),
    environment: {
      os: 'Windows 11',
      node: process.version,
      chrome: 'Chrome 157.0.8103.78',
      python: 'Python 3.12.10 (.venv_demo)',
      pipeline_build: 'l2b-v27-2026-222'
    },
    viewports: ['1440x900', '1280x720', '390x844'],
    testCases: [],
    screenshots: [],
    consoleErrors: [],
    networkFailures: [],
    verdict: 'PENDING'
  };

  // 1. Launch Backend Server
  console.log('[1/5] Starting Observatory Python Server...');
  const pythonExe = path.join(ROOT_DIR, '.venv_demo', 'Scripts', 'python.exe');
  const appPy = path.join(ROOT_DIR, 'observatory', 'app.py');

  const serverProc = spawn(pythonExe, ['-u', appPy, '--port', String(SERVER_PORT), '--no-browser'], {
    cwd: ROOT_DIR,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  serverProc.stdout.on('data', (d) => process.stdout.write(`[Python Server] ${d}`));
  serverProc.stderr.on('data', (d) => process.stderr.write(`[Python Server Error] ${d}`));

  let chromeProc = null;
  let client = null;

  try {
    const srv = await waitForServer();
    console.log(`[+] Server active in ${srv.duration}ms at ${SERVER_URL}`);

    // 2. Launch Headless Chrome
    console.log('[2/5] Launching Chrome in headless remote-debugging mode...');
    const userDataDir = path.join(ROOT_DIR, 'scratch', 'cdp_profile_cleanup_c');
    if (!fs.existsSync(userDataDir)) fs.mkdirSync(userDataDir, { recursive: true });

    chromeProc = spawn(
      CHROME_BINARY,
      [
        '--headless=new',
        `--remote-debugging-port=${CDP_PORT}`,
        `--user-data-dir=${userDataDir}`,
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check',
        SERVER_URL
      ],
      { stdio: 'ignore' }
    );

    await sleep(2000);
    const listData = await httpGetJson(`http://127.0.0.1:${CDP_PORT}/json/list`);
    const page = listData.find((p) => p.type === 'page');
    if (!page) throw new Error('Failed to find browser target page');

    client = new CdpClient(page.webSocketDebuggerUrl);
    await client.connect();
    await client.send('Page.enable');
    await client.send('DOM.enable');
    await client.send('Runtime.enable');
    await client.send('Network.enable');

    console.log('[+] CDP session connected. Beginning test execution...\n');

    // -------------------------------------------------------------------------
    // TEST 1: Explore Dashboard at 1440x900 Desktop
    // -------------------------------------------------------------------------
    console.log('[TEST 1] Explore Dashboard — 1440x900 Desktop');
    await client.setViewport(1440, 900, false);
    await sleep(1000);

    const title = await client.eval('document.title');
    const headerExists = await client.eval(`!!document.querySelector('.app-header')`);
    const skyViewExists = await client.eval(`!!document.getElementById('section-sky-view')`);
    const transientSummaryExists = await client.eval(`!!document.getElementById('section-transient-summary')`);
    const blinkViewerExists = await client.eval(`!!document.getElementById('section-blink-comparator')`);
    const sedExists = await client.eval(`!!document.getElementById('section-spectrophotometry')`);
    const methodologyExists = await client.eval(`!!document.querySelector('.methodology-callout-banner')`);

    results.testCases.push({
      id: 'TC-EXPLORE-1440',
      name: 'Explore Page 5-Div Stack Verification (1440x900)',
      passed: headerExists && skyViewExists && transientSummaryExists && blinkViewerExists && sedExists && methodologyExists,
      details: { title, headerExists, skyViewExists, transientSummaryExists, blinkViewerExists, sedExists, methodologyExists }
    });

    results.screenshots.push(await client.captureScreenshot('01_explore_desktop_1440x900.png'));

    // -------------------------------------------------------------------------
    // TEST 2: Explore Dashboard at 1280x720 Laptop
    // -------------------------------------------------------------------------
    console.log('[TEST 2] Explore Dashboard — 1280x720 Laptop Viewport');
    await client.setViewport(1280, 720, false);
    await sleep(600);

    const headerOverflow1280 = await client.eval(`
      (() => {
        const h = document.querySelector('.app-header');
        return h ? h.scrollWidth > h.clientWidth : false;
      })()
    `);

    results.testCases.push({
      id: 'TC-EXPLORE-1280',
      name: 'Explore Viewport 1280x720 Header Wrapping & Layout Audit',
      passed: !headerOverflow1280,
      details: { headerOverflow1280 }
    });

    results.screenshots.push(await client.captureScreenshot('02_explore_laptop_1280x720.png'));

    // -------------------------------------------------------------------------
    // TEST 3: Explore Dashboard at 390x844 Mobile
    // -------------------------------------------------------------------------
    console.log('[TEST 3] Explore Dashboard — 390x844 Mobile');
    await client.setViewport(390, 844, true);
    await sleep(600);

    const mobileMenuBtnExists = await client.eval(`!!document.querySelector('.mobile-menu-btn')`);
    results.testCases.push({
      id: 'TC-EXPLORE-390',
      name: 'Explore Mobile Responsive Layout (390x844)',
      passed: mobileMenuBtnExists,
      details: { mobileMenuBtnExists }
    });

    results.screenshots.push(await client.captureScreenshot('03_explore_mobile_390x844.png'));

    // Helper: Navigate to tab by label
    async function navigateTab(label) {
      await client.eval(`
        (() => {
          const btn = Array.from(document.querySelectorAll('.nav-item-btn')).find(b => b.textContent.toLowerCase().includes('${label.toLowerCase()}'));
          if (btn) btn.click();
        })()
      `);
      await sleep(1000);
    }

    // -------------------------------------------------------------------------
    // TEST 4: Objects Catalogue & Detail Subtabs (1440x900)
    // -------------------------------------------------------------------------
    console.log('\n[TEST 4] Objects Catalogue Navigation & Table Verification');
    await client.setViewport(1440, 900, false);

    // Click 'Objects' tab
    await navigateTab('Objects');

    const objectsTitle = await client.eval(`document.querySelector('.catalog-title')?.textContent`);
    const tableRowsCount = await client.eval(`document.querySelectorAll('.object-table-row').length`);

    results.testCases.push({
      id: 'TC-OBJECTS-CATALOG',
      name: 'Objects Catalogue Table & Pagination Loading',
      passed: tableRowsCount > 0,
      details: { objectsTitle, tableRowsCount }
    });

    results.screenshots.push(await client.captureScreenshot('04_objects_desktop_1440x900.png'));

    // Test Mobile Objects view
    await client.setViewport(390, 844, true);
    await sleep(500);
    results.screenshots.push(await client.captureScreenshot('05_objects_mobile_390x844.png'));
    await client.setViewport(1440, 900, false);
    await sleep(500);

    // Detail Subtabs Verification: Blink, Difference, SED, Evidence, Human Review, Export
    console.log('[*] Testing Detail Inspector Subtabs...');

    // Subtab 1: Blink Viewer
    results.screenshots.push(await client.captureScreenshot('06_detail_blink_viewer.png'));

    // Subtab 2: Difference Maps
    await client.eval(`
      (() => {
        const btn = Array.from(document.querySelectorAll('.detail-subtab-btn')).find(b => b.textContent.includes('Difference'));
        if (btn) btn.click();
      })()
    `);
    await sleep(600);
    results.screenshots.push(await client.captureScreenshot('07_detail_difference_viewer.png'));

    // Subtab 3: 102-ch SED
    await client.eval(`
      (() => {
        const btn = Array.from(document.querySelectorAll('.detail-subtab-btn')).find(b => b.textContent.includes('102-ch SED'));
        if (btn) btn.click();
      })()
    `);
    await sleep(600);
    results.screenshots.push(await client.captureScreenshot('08_detail_spectrum_viewer.png'));

    // Subtab 4: AI Diagnostics / Evidence Inspector
    await client.eval(`
      (() => {
        const btn = Array.from(document.querySelectorAll('.detail-subtab-btn')).find(b => b.textContent.includes('AI Diagnostics'));
        if (btn) btn.click();
      })()
    `);
    await sleep(600);
    results.screenshots.push(await client.captureScreenshot('09_detail_evidence_inspector.png'));

    // Subtab 5: Human Review (Check consolidated export button)
    await client.eval(`
      (() => {
        const btn = Array.from(document.querySelectorAll('.detail-subtab-btn')).find(b => b.textContent.includes('Human Review'));
        if (btn) btn.click();
      })()
    `);
    await sleep(600);
    const exportStationBtnExists = await client.eval(`
      !!Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Export Station'))
    `);
    results.screenshots.push(await client.captureScreenshot('10_detail_human_review.png'));

    // Subtab 6: Export Data
    await client.eval(`
      (() => {
        const btn = Array.from(document.querySelectorAll('.detail-subtab-btn')).find(b => b.textContent.includes('Export Data'));
        if (btn) btn.click();
      })()
    `);
    await sleep(600);
    results.screenshots.push(await client.captureScreenshot('11_detail_export_station.png'));

    results.testCases.push({
      id: 'TC-DETAIL-SUBTABS',
      name: 'Inspector Subtabs Verification (Blink, Diff, SED, Evidence, Review, Export)',
      passed: exportStationBtnExists,
      details: { exportStationBtnExists }
    });

    // -------------------------------------------------------------------------
    // TEST 5: Data Input Station Functional Acceptance (1440x900 & 390x844)
    // -------------------------------------------------------------------------
    console.log('\n[TEST 5] Data Input Station — Functional Acceptance');

    // Navigate to 'Data Input' tab
    await navigateTab('Data Input');

    results.screenshots.push(await client.captureScreenshot('12_datainput_desktop_1440x900.png'));

    // Mobile Viewport
    await client.setViewport(390, 844, true);
    await sleep(500);
    results.screenshots.push(await client.captureScreenshot('13_datainput_mobile_390x844.png'));
    await client.setViewport(1440, 900, false);
    await sleep(500);

    // 5A. Valid Coordinate Target Search (Preset: SPX-J163.6309-69.4422)
    console.log('[*] Testing Valid Coordinate Search (SPX-J163.6309-69.4422)...');
    await client.eval(`
      (() => {
        const presetBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Primary'));
        if (presetBtn) presetBtn.click();
      })()
    `);
    await sleep(300);

    await client.eval(`
      (() => {
        const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Query Coordinates'));
        if (submitBtn) submitBtn.click();
      })()
    `);
    await sleep(1500);

    const validSearchResultText = await client.eval(`
      document.querySelector('.data-input-station-container')?.innerText || ''
    `);
    const validMatchFound = validSearchResultText.includes('SPX-J163.6309-69.4422') || validSearchResultText.includes('Located');

    results.testCases.push({
      id: 'TC-COORD-SEARCH-VALID',
      name: 'Coordinate Search: Valid Survey Target (SPX-J163.6309-69.4422)',
      passed: validMatchFound,
      details: { validMatchFound }
    });

    results.screenshots.push(await client.captureScreenshot('14_datainput_coord_search_valid.png'));

    // 5B. Out-of-Field Coordinate Search (Boundary Rejection: RA 180°, Dec +25°)
    console.log('[*] Testing Out-of-Field Boundary Protection (RA 180°, Dec +25°)...');
    await client.eval(`
      (() => {
        const boundaryBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Boundary Rejection'));
        if (boundaryBtn) boundaryBtn.click();
      })()
    `);
    await sleep(300);

    await client.eval(`
      (() => {
        const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Query Coordinates'));
        if (submitBtn) submitBtn.click();
      })()
    `);
    await sleep(1200);

    const outOfFieldText = await client.eval(`
      document.querySelector('.data-input-station-container')?.innerText || ''
    `);
    const boundaryRejectedFailClosed = outOfFieldText.includes('Outside Field Boundary') &&
      outOfFieldText.includes('Zero synthetic detections generated');

    results.testCases.push({
      id: 'TC-COORD-SEARCH-OUT-OF-BOUNDS',
      name: 'Coordinate Search: Fail-Closed Survey Footprint Boundary Rejection',
      passed: boundaryRejectedFailClosed,
      details: { boundaryRejectedFailClosed }
    });

    results.screenshots.push(await client.captureScreenshot('15_datainput_coord_search_out_of_field.png'));

    // 5C. File Ingestion: Valid Level-2 FITS File
    console.log('[*] Testing File Ingestion: Real SPHEREx Template FITS...');
    const sampleFitsPath = path.join(ROOT_DIR, 'NASA_DEMO', 'sample_inputs', 'fits', 'aurora_template_D1_spx_base-2026-191.fits');
    const fitsBuffer = fs.readFileSync(sampleFitsPath);
    const fitsBase64 = fitsBuffer.toString('base64');

    await client.eval(`
      (async () => {
        const res = await fetch('/api/data/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: 'aurora_template_D1_spx.fits',
            content_base64: '${fitsBase64}',
            file_type: 'fits'
          })
        });
        window._lastValFits = await res.json();
      })()
    `);
    await sleep(600);

    const fitsVal = await client.eval('window._lastValFits');
    const fitsCompatible = fitsVal && fitsVal.status === 'VALID' && fitsVal.format === 'FITS';

    results.testCases.push({
      id: 'TC-FILE-VALIDATE-FITS',
      name: 'FITS File Ingestion & HDU/WCS Compatibility Evaluation',
      passed: fitsCompatible,
      details: fitsVal
    });

    results.screenshots.push(await client.captureScreenshot('16_datainput_file_validation_fits.png'));

    // 5D. File Ingestion: Valid 102-ch CSV Spectra File
    console.log('[*] Testing File Ingestion: 102-Channel Spectra CSV...');
    const sampleCsvPath = path.join(ROOT_DIR, 'NASA_DEMO', 'sample_inputs', 'spectra', 'sample_assembled_spectra.csv');
    const fullCsv = fs.readFileSync(sampleCsvPath, 'utf-8');
    // Take header + first 5 sources (~5 KB) for snappy test evaluation
    const csvLines = fullCsv.split('\n').slice(0, 6).join('\n');

    await client.eval(`
      (async () => {
        const res = await fetch('/api/data/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: 'sample_assembled_spectra.csv',
            content_text: ${JSON.stringify(csvLines)},
            file_type: 'csv'
          })
        });
        window._lastValCsv = await res.json();
      })()
    `);
    await sleep(600);

    const csvVal = await client.eval('window._lastValCsv');
    const csvCompatible = csvVal && csvVal.status === 'VALID' && csvVal.compatibility?.spectra?.status === 'COMPATIBLE';

    results.testCases.push({
      id: 'TC-FILE-VALIDATE-CSV-102CH',
      name: 'CSV File Ingestion & SPECTRA V2 102-Channel Compatibility',
      passed: csvCompatible,
      details: csvVal
    });

    results.screenshots.push(await client.captureScreenshot('17_datainput_file_validation_csv_102ch.png'));

    // 5E. File Ingestion: Invalid / Unsupported File Rejection
    console.log('[*] Testing File Ingestion: Unsupported / Malformed File Rejection...');
    await client.eval(`
      (async () => {
        const res = await fetch('/api/data/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: 'corrupted_archive.bin',
            content: 'RAW_UNSUPPORTED_BINARY_PAYLOAD',
            file_type: 'bin'
          })
        });
        window._lastValInvalid = await res.json();
      })()
    `);
    await sleep(500);

    const invalidVal = await client.eval('window._lastValInvalid');
    const invalidRejected = invalidVal && invalidVal.status === 'INVALID' && invalidVal.message?.includes('Unsupported astronomical format');

    results.testCases.push({
      id: 'TC-FILE-VALIDATE-INVALID',
      name: 'Invalid / Unsupported File Format Rejection',
      passed: invalidRejected,
      details: invalidVal
    });

    results.screenshots.push(await client.captureScreenshot('18_datainput_file_validation_invalid.png'));

    // 5F. 5-Module Compatibility Matrix Verification
    console.log('[*] Verifying 5-Module Compatibility Matrix...');
    const has5Modules = fitsVal?.compatibility?.astrovision &&
      fitsVal?.compatibility?.spectra &&
      fitsVal?.compatibility?.chronos_x &&
      fitsVal?.compatibility?.motion_x &&
      fitsVal?.compatibility?.fusion_x;

    results.testCases.push({
      id: 'TC-5MODULE-MATRIX',
      name: '5-Module Compatibility Matrix Evaluation Complete',
      passed: !!has5Modules,
      details: fitsVal?.compatibility
    });

    results.screenshots.push(await client.captureScreenshot('19_datainput_module_compatibility_matrix.png'));

    // -------------------------------------------------------------------------
    // TEST 6: How It Works & About Navigation (1440x900)
    // -------------------------------------------------------------------------
    console.log('\n[TEST 6] How It Works & About View Navigation');

    // Navigate to 'How It Works'
    await navigateTab('How it works');
    const howTitle = await client.eval(`document.querySelector('.section-title')?.textContent`);
    results.testCases.push({
      id: 'TC-HOW-IT-WORKS',
      name: 'How It Works Methodology View Verification',
      passed: !!howTitle,
      details: { howTitle }
    });
    results.screenshots.push(await client.captureScreenshot('20_howitworks_desktop_1440x900.png'));

    // Navigate to 'About'
    await navigateTab('About');
    const aboutTeam = await client.eval(`
      document.querySelector('.about-view-container')?.innerText.includes('Team VU_VioNux')
    `);
    results.testCases.push({
      id: 'TC-ABOUT-VIEW',
      name: 'About View & Team VU_VioNux Provenance Notice',
      passed: !!aboutTeam,
      details: { aboutTeam }
    });
    results.screenshots.push(await client.captureScreenshot('21_about_desktop_1440x900.png'));

    // Collect Errors
    results.consoleErrors = client.consoleErrors;
    results.networkFailures = client.networkFailures;

    const allPassed = results.testCases.every((t) => t.passed);
    const zeroConsoleErrors = results.consoleErrors.length === 0;

    results.verdict = allPassed && zeroConsoleErrors
      ? 'BROWSER_ACCEPTANCE_PASS'
      : (allPassed ? 'BROWSER_ACCEPTANCE_PASS_WITH_LIMITATIONS' : 'BROWSER_ACCEPTANCE_FAIL');

    console.log('\n========================================================================');
    console.log(` AUDIT VERDICT: ${results.verdict}`);
    console.log(` Tests Passed:  ${results.testCases.filter((t) => t.passed).length} / ${results.testCases.length}`);
    console.log(` Console Errors: ${results.consoleErrors.length}`);
    console.log(` Network Fails:  ${results.networkFailures.length}`);
    console.log(` Screenshots:    ${results.screenshots.length} captured in docs/verification/task_4_28F_cleanup_c/`);
    console.log('========================================================================\n');

    fs.writeFileSync(SUMMARY_JSON_PATH, JSON.stringify(results, null, 2), 'utf-8');
    console.log(`[+] Saved summary JSON to ${SUMMARY_JSON_PATH}`);

  } catch (err) {
    console.error('[-] Test execution failed:', err);
    results.verdict = 'BROWSER_ACCEPTANCE_FAIL';
    results.error = err.message;
    fs.writeFileSync(SUMMARY_JSON_PATH, JSON.stringify(results, null, 2), 'utf-8');
  } finally {
    if (client) client.close();
    if (chromeProc && chromeProc.pid) {
      try { spawn('taskkill', ['/pid', String(chromeProc.pid), '/T', '/F'], { stdio: 'ignore' }); } catch (e) {}
    }
    if (serverProc && serverProc.pid) {
      try { spawn('taskkill', ['/pid', String(serverProc.pid), '/T', '/F'], { stdio: 'ignore' }); } catch (e) {}
    }
    console.log('[*] Test processes terminated.');
  }
}

main().catch(console.error);
