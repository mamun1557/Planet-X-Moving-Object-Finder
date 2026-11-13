"""
SPECTRA-X Model 5: FUSION-X
Multimodal Anomaly Ranking & Human-AI Co-Pilot Decision Engine

Inputs:
- Spatial Anomaly Score (ASTROVISION)
- Spectral Outlier Score (SPECTRA)
- Temporal Significance (CHRONOS-X)
- Kinematic / Proper Motion Flag (MOTION-X)
- Known Transient Match (ZTF BTS / TNS Catalog)

Architecture:
- Multimodal Attention & Bayesian Fusion Ranker
- Outputs calibrated anomaly confidence [0.0 - 1.0] and scientific explanation tag:
  ['TRANSIENT_SUPERNOVA', 'ASTEROID_CANDIDATE', 'SPECTRAL_OUTLIER', 'VARIABLE_STAR', 'INSTRUMENTAL_ARTIFACT']
"""

import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional


class FusionRanker(nn.Module):
    def __init__(self, input_features: int = 8, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_features, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Outputs anomaly score between 0.0 (nominal) and 1.0 (highest scientific priority)."""
        return self.net(features)

    @staticmethod
    def classify_candidate(
        spatial_score: float,
        spectral_score: float,
        temporal_sig: float,
        is_known_star: bool,
        is_known_asteroid: bool,
        is_known_transient: bool,
        chronos_temporal_eligibility: Optional[str] = None
    ) -> str:
        """
        [DEPRECATED] Prototype rule-based co-pilot scientific classification.
        Migrate to production FUSION-X engine: `models.fusion.fusion_engine.FusionEngine`.
        
        Task 1.3M Safety Remediation:
        Enforces temporal eligibility gate. NEW_TRANSIENT_OR_ASTEROID_CANDIDATE
        is strictly prohibited unless chronos_temporal_eligibility == "TRUE".
        """
        if is_known_asteroid:
            return "KNOWN_SOLAR_SYSTEM_OBJECT"
        if is_known_transient:
            return "CONFIRMED_ASTRONOMICAL_TRANSIENT"
            
        # Temporal anomaly gate (Task 1.3M Safety Synchronization)
        if temporal_sig > 5.0 and not is_known_star:
            if chronos_temporal_eligibility == "TRUE":
                return "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
            else:
                return "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"
                
        if spectral_score > 3.0:
            return "INFRARED_SPECTRAL_ANOMALY"
        if spatial_score > 3.0 and is_known_star:
            return "STELLAR_VARIABILITY_OR_FLARE"
            
        if temporal_sig > 5.0 and is_known_star:
            if chronos_temporal_eligibility == "TRUE":
                return "STELLAR_VARIABILITY_OR_FLARE"
            else:
                return "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"
                
        return "BACKGROUND_OR_INSTRUMENTAL_RESIDUAL"
