import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import ObservatoryWorkspace from './components/ObservatoryWorkspace';
import DataInputWorkspace from './components/DataInputWorkspace';
import AnalysisWorkspace from './components/AnalysisWorkspace';
import EvidenceWorkspace from './components/EvidenceWorkspace';
import AboutView from './components/AboutView';

import {
  createSession,
  getSessionInfo,
  resetSession,
  fetchSystemStatus
} from './services/api';

/**
 * App Root Component (Task 4.29D Complete UI Replacement)
 * Clean, general-purpose, input-driven astronomical analysis workspace.
 * Starts strictly with EMPTY_WORKSPACE on load.
 * 
 * Primary Navigation:
 * 1. Observatory — Initial landing workspace & session telemetry
 * 2. Data Input — FITS, CSV, JSON ingestion & validation table
 * 3. Analysis — 5-module readiness matrix & execution
 * 4. Evidence — Real motion vectors, kinematics, and scientific safeguards
 * 5. About — Methodology, team, and scientific limitations
 */
export default function App() {
  // Session State (Task 4.29B integration)
  const [sessionId, setSessionId] = useState(null);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);

  // Active View: 'OBSERVATORY' | 'DATA_INPUT' | 'ANALYSIS' | 'EVIDENCE' | 'ABOUT'
  const [activeTab, setActiveTab] = useState('OBSERVATORY');

  // Input & Analysis State (Empty on start)
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Initialize Isolated User Session on Mount (Strictly NO preloading of P0003 or legacy candidates)
  useEffect(() => {
    initSession();
    loadSystemStatus();
  }, []);

  const initSession = async () => {
    try {
      // Check existing browser session token in sessionStorage
      let storedSid = window.sessionStorage?.getItem('spectra_x_session_id');
      if (!storedSid) {
        const res = await createSession();
        if (res && res.session_id) {
          storedSid = res.session_id;
          window.sessionStorage?.setItem('spectra_x_session_id', storedSid);
        }
      }
      setSessionId(storedSid);

      if (storedSid) {
        const info = await getSessionInfo(storedSid);
        setSessionInfo(info);
      }
    } catch (err) {
      console.warn('Session initialization:', err);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const status = await fetchSystemStatus();
      setSystemStatus(status);
    } catch (err) {
      console.warn('System status check:', err);
    }
  };

  const handleResetSession = async () => {
    if (sessionId) {
      try {
        await resetSession(sessionId);
        const info = await getSessionInfo(sessionId);
        setSessionInfo(info);
      } catch (err) {
        console.warn('Session reset:', err);
      }
    }
    setUploadedFiles([]);
    setAnalysisResults(null);
    setActiveTab('OBSERVATORY');
  };

  const handleNavigate = (tabId) => {
    setActiveTab(tabId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="app-container input-driven-workspace" role="application">
      {/* 1. Primary Header Navigation (5 Items) */}
      <Header
        activeTab={activeTab}
        setActiveTab={handleNavigate}
        sessionId={sessionId}
        uploadedFileCount={uploadedFiles.length}
        hasAnalysisResults={!!analysisResults}
      />

      {/* 2. Main Content Workspace */}
      <main className="main-content-layout max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 flex-1">
        {errorMessage && (
          <div className="alert-box error mb-4">
            <span>{errorMessage}</span>
          </div>
        )}

        {/* VIEW 1: OBSERVATORY (Landing / Empty Workspace) */}
        {activeTab === 'OBSERVATORY' && (
          <ObservatoryWorkspace
            sessionId={sessionId}
            sessionInfo={sessionInfo}
            uploadedFiles={uploadedFiles}
            onNavigate={handleNavigate}
          />
        )}

        {/* VIEW 2: DATA INPUT STATION */}
        {activeTab === 'DATA_INPUT' && (
          <DataInputWorkspace
            sessionId={sessionId}
            uploadedFiles={uploadedFiles}
            setUploadedFiles={setUploadedFiles}
            onProceedToAnalysis={() => handleNavigate('ANALYSIS')}
            onResetSession={handleResetSession}
          />
        )}

        {/* VIEW 3: ANALYSIS READINESS & EXECUTION */}
        {activeTab === 'ANALYSIS' && (
          <AnalysisWorkspace
            sessionId={sessionId}
            uploadedFiles={uploadedFiles}
            analysisResults={analysisResults}
            setAnalysisResults={setAnalysisResults}
            onNavigateToEvidence={() => handleNavigate('EVIDENCE')}
            onNavigateToInput={() => handleNavigate('DATA_INPUT')}
          />
        )}

        {/* VIEW 4: SCIENTIFIC EVIDENCE INSPECTOR */}
        {activeTab === 'EVIDENCE' && (
          <EvidenceWorkspace
            analysisResults={analysisResults}
            uploadedFiles={uploadedFiles}
            onNavigateToAnalysis={() => handleNavigate('ANALYSIS')}
            onNavigateToInput={() => handleNavigate('DATA_INPUT')}
          />
        )}

        {/* VIEW 5: ABOUT & METHODOLOGY */}
        {activeTab === 'ABOUT' && (
          <AboutView />
        )}
      </main>

      {/* 3. Footer with Scientific Provenance & Disclaimers */}
      <Footer onNavigate={handleNavigate} />
    </div>
  );
}
