"""
SPECTRA-X / F1 — Phase 3, Task 1.3B
Backward Compatibility Re-Export Shim for Continuum Sidecar Evidence Interface

Authoritative implementation has been relocated to `spectra_engine.continuum_sidecar_interface`.
This module is maintained strictly for backward compatibility with existing callers.
"""

from spectra_engine.continuum_sidecar_interface import (
    SIDECAR_CONTRACT_VERSION,
    ContinuumEvidenceRecord,
    ContinuumSidecarInterface,
)

__all__ = [
    "SIDECAR_CONTRACT_VERSION",
    "ContinuumEvidenceRecord",
    "ContinuumSidecarInterface",
]
