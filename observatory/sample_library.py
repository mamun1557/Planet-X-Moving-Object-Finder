"""
SPECTRA-X / Planet X Sample Library Catalog & API Contract
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline

Defines:
1. Sample pair metadata schema distinguishing REAL_INTRA_VISIT from SYNTHETIC_ENGINEERING_TEST.
2. Ground-truth motion vector separation (synthetic only, never for real data).
3. Authoritative query registry and metadata serialization.
4. Extensible catalog architecture for Task 4.29C 50-pair library ingestion.
"""

import os
import json
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


class SampleDatasetClass(str, Enum):
    REAL_INTRA_VISIT = "REAL_INTRA_VISIT"
    SYNTHETIC_ENGINEERING_TEST = "SYNTHETIC_ENGINEERING_TEST"


@dataclass
class SamplePairMetadata:
    """Metadata schema defining an observation pair in the sample library."""
    pair_id: str
    dataset_class: str  # "REAL_INTRA_VISIT" | "SYNTHETIC_ENGINEERING_TEST"
    pointing_id: str
    detector: str
    wavelength_band_um: List[float]
    obs_a_id: str
    obs_b_id: str
    obs_a_timestamp: str
    obs_b_timestamp: str
    time_separation_minutes: float
    time_separation_days: float
    wcs_available: bool
    scientific_eligibility: str
    intended_test_purpose: str
    has_ground_truth_motion: bool
    synthetic_ground_truth_motion: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Defensive enforcement: real intra-visit data must NEVER expose synthetic ground truth
        if self.dataset_class == SampleDatasetClass.REAL_INTRA_VISIT.value:
            d["synthetic_ground_truth_motion"] = None
            d["has_ground_truth_motion"] = False
        return d


class SampleLibraryCatalog:
    """
    Catalog manager for paired observation sample library.
    Provides filtering and inspection endpoints for backend consumers.
    """

    def __init__(self):
        self._registry: Dict[str, SamplePairMetadata] = {}
        self._populate_initial_registry()
        self._load_package_manifest_if_available()

    def _load_package_manifest_if_available(self) -> None:
        """Loads optional 50-pair personal test dataset manifest if present on disk."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        manifest_path = os.path.join(base_dir, "artifacts", "downloadable_packages", "SPECTRA-X-Personal-Test-Data", "dataset_manifest.json")
        if not os.path.exists(manifest_path):
            return

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            pairs = data.get("all_pairs", [])
            for p in pairs:
                pid = p.get("pair_id")
                if not pid:
                    continue
                dclass = p.get("dataset_class", "REAL_INTRA_VISIT")
                is_real = (dclass == "REAL_INTRA_VISIT")

                detector = p.get("detector", "D1")
                det_bands = {
                    "D1": [0.75, 1.11], "D2": [1.11, 1.64], "D3": [1.64, 2.42],
                    "D4": [2.42, 3.82], "D5": [3.82, 4.42], "D6": [4.42, 5.00]
                }
                wband = det_bands.get(detector, [0.75, 5.00])

                syn_gt = None
                if not is_real:
                    syn_gt = dict(p.get("synthetic_ground_truth_motion") or p.get("ground_truth_motion") or {})
                    syn_gt["is_synthetic"] = True
                    if "simulation_notes" not in syn_gt or "NEVER claim as real astronomical discovery" not in syn_gt["simulation_notes"]:
                        syn_gt["simulation_notes"] = (syn_gt.get("simulation_notes", "") + " Artificially injected ePSF moving point source. NEVER claim as real astronomical discovery.").strip()

                meta = SamplePairMetadata(
                    pair_id=pid,
                    dataset_class=dclass,
                    pointing_id=p.get("pointing_id", "P0003"),
                    detector=detector,
                    wavelength_band_um=wband,
                    obs_a_id=f"{pid}_obs_a.fits",
                    obs_b_id=f"{pid}_obs_b.fits",
                    obs_a_timestamp=p.get("obs_a_timestamp", "2025-06-15T09:42:00Z"),
                    obs_b_timestamp=p.get("obs_b_timestamp", "2025-06-15T09:47:02Z"),
                    time_separation_minutes=float(p.get("time_separation_minutes", 5.0)),
                    time_separation_days=float(p.get("time_separation_days", 0.0035)),
                    wcs_available=True,
                    scientific_eligibility="INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY" if is_real else "TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION",
                    intended_test_purpose=p.get("scenario_name", p.get("target_name", "Astrometric registration / engineering test")),
                    has_ground_truth_motion=not is_real,
                    synthetic_ground_truth_motion=syn_gt
                )
                self._registry[pid] = meta
        except Exception:
            pass

    def _populate_initial_registry(self) -> None:
        """Seeds initial verified pairs illustrating the two formal dataset classes."""
        # 1. Real Intra-Visit Dither Reference Pair (Field P0003, Detector D1, Dither 1 vs Dither 4)
        p0003_real = SamplePairMetadata(
            pair_id="PAIR-REAL-P0003-D1-1D-4D",
            dataset_class=SampleDatasetClass.REAL_INTRA_VISIT.value,
            pointing_id="P0003",
            detector="D1",
            wavelength_band_um=[0.75, 1.11],
            obs_a_id="level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits",
            obs_b_id="level2_2026W30_1B_0003_4D1_spx_l2b-v27-2026-222.fits",
            obs_a_timestamp="2026-07-20T00:26:21.423Z",
            obs_b_timestamp="2026-07-20T00:32:48.216Z",
            time_separation_minutes=6.4465,
            time_separation_days=0.004477,
            wcs_available=True,
            scientific_eligibility="INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY",
            intended_test_purpose="Astrometric registration, PSF subtraction null-testing, intra-visit dither dipole verification.",
            has_ground_truth_motion=False,
            synthetic_ground_truth_motion=None
        )
        self._registry[p0003_real.pair_id] = p0003_real

        # 2. Real Intra-Visit Dither Reference Pair (Field P0001, Detector D2, Dither 1 vs Dither 2)
        p0001_real = SamplePairMetadata(
            pair_id="PAIR-REAL-P0001-D2-1D-2D",
            dataset_class=SampleDatasetClass.REAL_INTRA_VISIT.value,
            pointing_id="P0001",
            detector="D2",
            wavelength_band_um=[1.11, 1.64],
            obs_a_id="level2_2026W30_1B_0001_1D2_spx_l2b-v27-2026-222.fits",
            obs_b_id="level2_2026W30_1B_0001_2D2_spx_l2b-v27-2026-222.fits",
            obs_a_timestamp="2026-07-20T00:06:53.370Z",
            obs_b_timestamp="2026-07-20T00:09:02.300Z",
            time_separation_minutes=2.1488,
            time_separation_days=0.001492,
            wcs_available=True,
            scientific_eligibility="INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY",
            intended_test_purpose="Consecutive intra-visit dither step registration test.",
            has_ground_truth_motion=False,
            synthetic_ground_truth_motion=None
        )
        self._registry[p0001_real.pair_id] = p0001_real

        # 3. Synthetic Multi-Epoch Reference Pair (Simulated Near-Earth Object Injection)
        syn_neo = SamplePairMetadata(
            pair_id="PAIR-SYN-NEO-FAST-001",
            dataset_class=SampleDatasetClass.SYNTHETIC_ENGINEERING_TEST.value,
            pointing_id="SYNTHETIC_FIELD_A",
            detector="D1",
            wavelength_band_um=[0.75, 1.11],
            obs_a_id="synthetic_epoch1_neo_injection.fits",
            obs_b_id="synthetic_epoch2_neo_injection.fits",
            obs_a_timestamp="2026-07-01T00:00:00.000Z",
            obs_b_timestamp="2026-07-04T00:00:00.000Z",
            time_separation_minutes=4320.0,
            time_separation_days=3.0,
            wcs_available=True,
            scientific_eligibility="TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION",
            intended_test_purpose="Validation of multi-day temporal motion rate calculation (target rate ~15.0 arcsec/day).",
            has_ground_truth_motion=True,
            synthetic_ground_truth_motion={
                "is_synthetic": True,
                "target_type": "SYNTHETIC_NEO",
                "ground_truth_delta_ra_arcsec": 38.97,
                "ground_truth_delta_dec_arcsec": 22.50,
                "ground_truth_total_displacement_arcsec": 45.00,
                "ground_truth_motion_rate_arcsec_per_day": 15.00,
                "simulation_notes": "Artificially injected ePSF moving point source. NEVER claim as real astronomical discovery."
            }
        )
        self._registry[syn_neo.pair_id] = syn_neo

    def list_samples(self, dataset_class: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all registered sample pair metadata, optionally filtered by dataset_class."""
        results = []
        for pair in self._registry.values():
            if dataset_class and pair.dataset_class != dataset_class:
                continue
            results.append(pair.to_dict())
        return results

    def get_sample(self, pair_id: str) -> Optional[Dict[str, Any]]:
        """Returns metadata for a specific sample pair ID, or None if not found."""
        if not pair_id:
            return None
        pair = self._registry.get(pair_id.strip())
        return pair.to_dict() if pair else None

    def register_sample(self, sample: SamplePairMetadata) -> None:
        """Registers a new sample pair into the catalog."""
        self._registry[sample.pair_id] = sample

