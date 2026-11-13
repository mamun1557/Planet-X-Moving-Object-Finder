"""
SPECTRA-X / F1 — Phase 3, Task 1.3B
Backward Compatibility Re-Export Shim for SPECTRA Evidence Adapter

Authoritative implementation has been relocated to `spectra_engine.spectra_evidence_adapter`.
This module is maintained strictly for backward compatibility with existing callers.
"""

from spectra_engine.spectra_evidence_adapter import SpectraEvidenceAdapter

__all__ = [
    "SpectraEvidenceAdapter",
]
