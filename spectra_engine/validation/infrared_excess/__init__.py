"""
SPECTRA-X Infrared Excess Validation & SED Evidence Engine.

Provides independent empirical verification of SPECTRA infrared anomaly candidates
using multi-catalog astronomical evidence (Gaia DR3, 2MASS, ALLWISE, and SPHEREx).
"""

from spectra_engine.validation.infrared_excess.zero_points import (
    PHOTOMETRIC_BANDS,
    BandMetadata
)
from spectra_engine.validation.infrared_excess.catalog_normalizer import (
    CatalogNormalizer,
    NormalizedMeasurement,
    NormalizedSourceRecord
)
from spectra_engine.validation.infrared_excess.photospheric_model import (
    PhotosphericBaselineEstimator,
    PhotosphericPrediction
)
from spectra_engine.validation.infrared_excess.excess_engine import (
    InfraredExcessEngine,
    ExcessBandResult,
    SPHERExOverlapResult,
    SourceExcessEvaluation
)
from spectra_engine.validation.infrared_excess.evidence_classifier import (
    InfraredEvidenceClassifier
)

__all__ = [
    "PHOTOMETRIC_BANDS",
    "BandMetadata",
    "CatalogNormalizer",
    "NormalizedMeasurement",
    "NormalizedSourceRecord",
    "PhotosphericBaselineEstimator",
    "PhotosphericPrediction",
    "InfraredExcessEngine",
    "ExcessBandResult",
    "SPHERExOverlapResult",
    "SourceExcessEvaluation",
    "InfraredEvidenceClassifier"
]

