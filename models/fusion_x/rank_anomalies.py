"""
FUSION-X Anomaly Ranking Pipeline
Combines ASTROVISION, SPECTRA, CHRONOS-X, and MOTION-X scores with ZTF BTS transients.
"""

import os
import glob
import pandas as pd
import numpy as np
import torch
from model import FusionRanker


def run_fusion_ranking():
    out_dir = "data/processed/training_samples"
    os.makedirs(out_dir, exist_ok=True)

    # Check ZTF BTS
    ztf_path = "data/external/transient_catalogs/ztf_bright_transient_survey.csv"
    if os.path.exists(ztf_path):
        ztf_df = pd.read_csv(ztf_path)
        print(f"Loaded {len(ztf_df)} confirmed ZTF BTS transients.")
    else:
        ztf_df = None
        print("ZTF BTS catalog not found yet.")

    ranker = FusionRanker(input_features=6)
    print("FUSION-X Multi-modal Ranking Model initialized.")

    # Demonstration of multimodal ranking across synthetic & extracted candidates
    np.random.seed(42)
    demo_candidates = []
    for i in range(25):
        spatial = float(np.random.exponential(1.5))
        spectral = float(np.random.exponential(1.2))
        temporal = float(np.random.exponential(2.0))
        is_star = bool(np.random.rand() > 0.6)
        is_ast = bool(np.random.rand() > 0.85)
        is_trans = bool(np.random.rand() > 0.9)

        feat = torch.tensor([[spatial, spectral, temporal, float(is_star), float(is_ast), float(is_trans)]], dtype=torch.float32)
        with torch.no_grad():
            fused_score = float(ranker(feat).item())

        classification = FusionRanker.classify_candidate(
            spatial_score=spatial,
            spectral_score=spectral,
            temporal_sig=temporal,
            is_known_star=is_star,
            is_known_asteroid=is_ast,
            is_known_transient=is_trans,
            chronos_temporal_eligibility="FALSE"  # Synthetic simulation data is not secularly eligible
        )

        demo_candidates.append({
            "candidate_id": f"SPX-CAND-{i+1:04d}",
            "spatial_anomaly_score": round(spatial, 3),
            "spectral_outlier_score": round(spectral, 3),
            "temporal_significance": round(temporal, 3),
            "is_known_gaia_star": is_star,
            "is_known_asteroid": is_ast,
            "is_known_transient": is_trans,
            "fused_priority_score": round(fused_score, 4),
            "copilot_classification": classification
        })

    df_rank = pd.DataFrame(demo_candidates).sort_values("fused_priority_score", ascending=False)
    out_csv = os.path.join(out_dir, "fused_anomaly_rankings.csv")
    df_rank.to_csv(out_csv, index=False)
    print(f"Saved {len(df_rank)} ranked anomaly candidates to {out_csv}")
    print("\nTop 5 Co-Pilot Prioritized Infrared Anomalies:")
    print(df_rank[["candidate_id", "fused_priority_score", "copilot_classification"]].head(5).to_string(index=False))


if __name__ == "__main__":
    run_fusion_ranking()
