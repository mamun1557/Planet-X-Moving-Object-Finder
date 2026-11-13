"""
SPECTRA-X — Environment & Runtime Verification Engine
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline (l2b-v27-2026-222)

Verifies Python compatibility, required dependencies, PyTorch tensor engine,
CUDA GPU acceleration availability, frozen checkpoint integrity, and observatory data providers.
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_verification() -> bool:
    print("=" * 70)
    print("  SPECTRA-X ENVIRONMENT & SCIENTIFIC RUNTIME VERIFICATION")
    print("  Pipeline Build: l2b-v27-2026-222")
    print("=" * 70)

    all_passed = True

    # 1. Python Version Check
    py_ver = sys.version_info
    py_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    print(f"\n[1/6] Python Runtime:")
    print(f"      Executable: {sys.executable}")
    print(f"      Version:    {py_str} (64-bit: {sys.maxsize > 2**32})")
    if py_ver.major == 3 and py_ver.minor == 12:
        print("      Status:     PASS (Optimal Python 3.12 detected)")
    elif py_ver.major == 3 and py_ver.minor in (10, 11):
        print("      Status:     PASS (Compatible Python 3.10+ detected)")
    else:
        print(f"      Status:     FAIL (Python 3.12 preferred, got {py_str})")
        all_passed = False

    # 2. Critical Dependency Imports
    print("\n[2/6] Verifying Critical Dependency Imports:")
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pandas", "pandas"),
        ("astropy", "astropy"),
        ("matplotlib", "matplotlib"),
        ("PIL", "Pillow"),
        ("yaml", "PyYAML"),
        ("torch", "PyTorch"),
        ("pytest", "pytest")
    ]
    for mod_name, label in packages:
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "unknown")
            print(f"      [OK] {label:<15} version: {ver}")
        except ImportError as e:
            print(f"      [FAIL] {label:<15} Import failed: {e}")
            all_passed = False

    if not all_passed:
        print("\n[ERROR] Missing required packages. Please rerun SETUP_ENVIRONMENT.bat.")
        return False

    # 3. PyTorch Engine & Tensor Math Verification
    print("\n[3/6] Verifying PyTorch Tensor Math:")
    try:
        import torch
        t1 = torch.ones((3, 3), dtype=torch.float32)
        t2 = torch.eye(3, dtype=torch.float32) * 2.0
        t_res = torch.matmul(t1, t2)
        assert t_res.shape == (3, 3) and t_res[0, 0].item() == 2.0
        print(f"      [OK] Torch tensor operations verified: shape={t_res.shape}, sum={t_res.sum().item():.1f}")
    except Exception as e:
        print(f"      [FAIL] PyTorch tensor verification failed: {e}")
        all_passed = False

    # 4. Hardware Acceleration & CUDA Detection
    print("\n[4/6] Hardware Acceleration & CUDA Detection:")
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        if cuda_avail:
            device_name = torch.cuda.get_device_name(0)
            dev_count = torch.cuda.device_count()
            cuda_ver = torch.version.cuda or "built-in"
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"      Status:      CUDA GPU ACCELERATION ACTIVE")
            print(f"      Device:      {device_name} (Total Devices: {dev_count})")
            print(f"      VRAM:        {vram_gb:.2f} GB")
            print(f"      CUDA Build:  {cuda_ver}")
        else:
            print(f"      Status:      CPU TENSOR EXECUTION (CPU FALLBACK ACTIVE)")
            print(f"      Note:        No compatible NVIDIA CUDA GPU/driver detected.")
            print(f"                   All SPECTRA-X inference models run reliably on CPU.")
    except Exception as e:
        print(f"      [WARNING] CUDA detection exception: {e}")

    # 5. Model Checkpoint Loading & Architecture Instantiation
    print("\n[5/6] Scientific Checkpoint & Model Verification:")
    astro_ckpt = os.path.join(PROJECT_ROOT, "checkpoints", "astrovision_spatial_v3.pt")
    spectra_ckpt = os.path.join(PROJECT_ROOT, "checkpoints", "spectra_masked_ae_v2.pt")
    thresholds_json = os.path.join(PROJECT_ROOT, "data", "processed", "spectra", "spectra_v2_provisional_thresholds_v1.json")

    try:
        from models.astrovision.model_v3 import AstroVisionAutoencoderV3
        from models.spectra.train_masked_spectra import MaskedSpectralAutoencoder

        # AstroVision V3
        av = AstroVisionAutoencoderV3(in_channels=1, latent_dim=128)
        ckpt_av = torch.load(astro_ckpt, map_location="cpu", weights_only=False)
        av.load_state_dict(ckpt_av.get("model_state_dict", ckpt_av) if isinstance(ckpt_av, dict) else ckpt_av)
        av.eval()
        dummy_img = torch.zeros((1, 1, 64, 64), dtype=torch.float32)
        with torch.no_grad():
            recon_img = av(dummy_img)
        assert recon_img.shape == (1, 1, 64, 64)
        print(f"      [OK] ASTROVISION-X V3 Autoencoder loaded & verified: dummy pass {recon_img.shape}")

        # SPECTRA V2 Masked AE
        sm = MaskedSpectralAutoencoder(num_channels=102, hidden_dim=64, latent_dim=16)
        ckpt_sm = torch.load(spectra_ckpt, map_location="cpu", weights_only=False)
        sm.load_state_dict(ckpt_sm.get("model_state_dict", ckpt_sm) if isinstance(ckpt_sm, dict) else ckpt_sm)
        sm.eval()
        dummy_flux = torch.ones((1, 102), dtype=torch.float32)
        dummy_mask = torch.ones((1, 102), dtype=torch.float32)
        with torch.no_grad():
            recon_flux = sm(dummy_flux, dummy_mask)
        assert recon_flux.shape == (1, 102)
        print(f"      [OK] SPECTRA-X V2 Masked Autoencoder loaded & verified: dummy pass {recon_flux.shape}")

        # Thresholds
        assert os.path.exists(thresholds_json), f"Missing threshold file: {thresholds_json}"
        print(f"      [OK] Provisional Thresholds verified at: {os.path.basename(thresholds_json)}")

    except Exception as e:
        print(f"      [FAIL] Model instantiation error: {e}")
        all_passed = False

    # 6. Observatory Data Provider Verification
    print("\n[6/6] Observatory Data Provider Integration:")
    try:
        from observatory.data_provider import ObservatoryDataProvider
        dp = ObservatoryDataProvider(base_dir=PROJECT_ROOT)
        status = dp.get_system_status()
        cands = dp.list_candidates(page=1, page_size=5)
        total_cands = status.get("total_candidates", 0)
        print(f"      [OK] DataProvider initialized: total_candidates={total_cands}, build={status.get('pipeline_build')}")
        assert total_cands == 1392, f"Expected 1392 candidates, got {total_cands}"
        assert len(cands.get("items", [])) == 5, f"Expected 5 paged items, got {len(cands.get('items', []))}"
        print(f"      [OK] Candidate queries and Level-2 data access verified.")
    except Exception as e:
        print(f"      [FAIL] Observatory DataProvider integration error: {e}")
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  VERIFICATION RESULT: ALL CHECKS PASSED [SUCCESS]")
        print("  The SPECTRA-X portable environment is fully operational.")
    else:
        print("  VERIFICATION RESULT: FAILURES DETECTED")
        print("  Please review the errors above.")
    print("=" * 70 + "\n")

    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
