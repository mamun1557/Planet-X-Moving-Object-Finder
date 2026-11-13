import os
import sys
import glob
import json
import torch
import astropy
import numpy as np
import pandas as pd
import scipy
import reproject
from datetime import datetime, timezone

def run_inventory():
    print("Executing Task 1: Comprehensive Project Inventory...")
    base_dir = os.path.abspath(".")
    
    # Environment
    py_ver = sys.version.replace("\n", " ")
    torch_ver = torch.__version__
    cuda_avail = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "None"
    astropy_ver = astropy.__version__
    numpy_ver = np.__version__
    pandas_ver = pd.__version__
    scipy_ver = scipy.__version__
    reproject_ver = reproject.__version__
    
    # Count files and sizes
    all_files = []
    total_bytes = 0
    fits_files = []
    checkpoint_files = []
    manifest_files = []
    script_files = []
    
    for root, dirs, files in os.walk(base_dir):
        # Exclude .git and .system_generated
        if '.git' in root or '.system_generated' in root:
            continue
        for f in files:
            p = os.path.join(root, f)
            rel_p = os.path.relpath(p, base_dir)
            try:
                sz = os.path.getsize(p)
            except Exception:
                sz = 0
            total_bytes += sz
            all_files.append((rel_p, sz))
            
            ext = os.path.splitext(f)[1].lower()
            if ext == '.fits':
                fits_files.append((rel_p, sz))
            elif ext in ['.pt', '.pth', '.ckpt']:
                checkpoint_files.append((rel_p, sz))
            elif ext == '.py':
                script_files.append((rel_p, sz))
            elif 'manifests' in rel_p.replace('\\', '/') and ext in ['.csv', '.json']:
                manifest_files.append((rel_p, sz))

    # Calculate data/ specific statistics
    data_files = [f for f in all_files if f[0].startswith('data') or f[0].startswith('data\\') or f[0].startswith('data/')]
    data_bytes = sum(f[1] for f in data_files)
    
    # Categorize data files
    qr2_l2 = [f for f in data_files if 'qr2' in f[0] and 'level2' in f[0] and 'deep' not in f[0]]
    qr2_deep = [f for f in data_files if 'qr2' in f[0] and 'deep' in f[0]]
    qr2_cal = [f for f in data_files if 'qr2' in f[0] and 'calibration' in f[0]]
    qr3_l2 = [f for f in data_files if 'qr3' in f[0] and 'level2' in f[0] and 'deep' not in f[0]]
    qr3_deep = [f for f in data_files if 'qr3' in f[0] and 'deep' in f[0]]
    qr3_cal = [f for f in data_files if 'qr3' in f[0] and 'calibration' in f[0]]
    qr3_tpl = [f for f in data_files if 'qr3' in f[0] and 'templates' in f[0]]
    external = [f for f in data_files if 'external' in f[0]]
    processed = [f for f in data_files if 'processed' in f[0]]

    # Inspect scripts
    script_analyses = {}
    for sf, sz in script_files:
        norm_sf = sf.replace('\\', '/')
        if norm_sf.startswith('reports/'):
            continue
        try:
            with open(sf, 'r', encoding='utf-8', errors='ignore') as fp:
                lines = fp.readlines()
            script_analyses[norm_sf] = {
                'lines': len(lines),
                'size': sz,
                'has_blanket_flags': any('flags != 0' in l.lower() or 'flags > 0' in l.lower() for l in lines),
                'imports': [l.strip() for l in lines if l.startswith('import ') or l.startswith('from ')][:5]
            }
        except Exception as e:
            script_analyses[norm_sf] = {'error': str(e)}

    # Generate project_inventory.md
    report_path = os.path.join(base_dir, "reports", "second_pass_audit", "project_inventory.md")
    with open(report_path, "w", encoding="utf-8") as out:
        out.write("# SPECTRA-X: Initial Project Inventory & Environment Audit\n\n")
        out.write(f"**Audit Execution Timestamp**: `{datetime.now(timezone.utc).isoformat()}`\n\n")
        
        out.write("## 1. System and Scientific Environment\n\n")
        out.write(f"- **Operating System**: Windows (AMD64)\n")
        out.write(f"- **Python Version**: `{py_ver}`\n")
        out.write(f"- **PyTorch Version**: `{torch_ver}`\n")
        out.write(f"- **CUDA Available**: `{cuda_avail}`\n")
        out.write(f"- **GPU Hardware**: `{gpu_name}`\n")
        out.write(f"- **Astropy Version**: `{astropy_ver}`\n")
        out.write(f"- **NumPy Version**: `{numpy_ver}`\n")
        out.write(f"- **SciPy Version**: `{scipy_ver}`\n")
        out.write(f"- **Pandas Version**: `{pandas_ver}`\n")
        out.write(f"- **Reproject Version**: `{reproject_ver}`\n\n")

        out.write("## 2. Quantitative Summary\n\n")
        out.write(f"- **Total Project Volume**: {total_bytes / (1024**3):.4f} GB ({total_bytes:,} bytes)\n")
        out.write(f"- **Total Data Directory Volume**: {data_bytes / (1024**3):.4f} GB ({data_bytes:,} bytes)\n")
        out.write(f"- **Total Data Files**: {len(data_files)}\n")
        out.write(f"- **Total FITS Files**: {len(fits_files)}\n")
        out.write(f"- **Total Checkpoint Files**: {len(checkpoint_files)}\n")
        out.write(f"- **Total Existing Scripts Inspected**: {len(script_analyses)}\n")
        out.write(f"- **Total Manifest Files**: {len(manifest_files)}\n\n")

        out.write("## 3. Data Storage Breakdown by Release and Category\n\n")
        out.write("| Category | Subdirectory | File Count | Size (MB) | Size (GB) |\n")
        out.write("| :--- | :--- | :---: | :---: | :---: |\n")
        
        def row(cat, sub, flist):
            cnt = len(flist)
            mb = sum(f[1] for f in flist) / (1024**2)
            gb = sum(f[1] for f in flist) / (1024**3)
            return f"| {cat} | `{sub}` | {cnt} | {mb:.2f} | {gb:.4f} |\n"
            
        out.write(row("QR2 Level-2 Wide", "data/spherex/qr2/level2/", qr2_l2))
        out.write(row("QR2 Level-2 Deep", "data/spherex/qr2_deep/level2/", qr2_deep))
        out.write(row("QR2 Calibration", "data/spherex/qr2/calibration/", qr2_cal))
        out.write(row("QR3 Level-2 Wide", "data/spherex/qr3/level2/", qr3_l2))
        out.write(row("QR3 Level-2 Deep", "data/spherex/qr3_deep/level2/", qr3_deep))
        out.write(row("QR3 Calibration", "data/spherex/qr3/calibration/", qr3_cal))
        out.write(row("QR3 Templates", "data/spherex/qr3/templates/", qr3_tpl))
        out.write(row("External Catalogs", "data/external/", external))
        out.write(row("Processed Data", "data/processed/", processed))
        out.write(f"| **Total Data** | `data/` | **{len(data_files)}** | **{data_bytes/(1024**2):.2f}** | **{data_bytes/(1024**3):.4f}** |\n\n")

        out.write("## 4. Checkpoints and Model Artifacts\n\n")
        for ckpt, sz in checkpoint_files:
            out.write(f"- `[{ckpt}](file:///{base_dir.replace('\\', '/')}/{ckpt.replace('\\', '/')})` ({sz/(1024**2):.2f} MB)\n")
        out.write("\n")

        out.write("## 5. Existing Python Scripts and Preprocessing Pipelines\n\n")
        out.write("| Script Path | Lines | Size (KB) | Blanket Flag Masking (`FLAGS != 0`) |\n")
        out.write("| :--- | :---: | :---: | :---: |\n")
        for sname, info in sorted(script_analyses.items()):
            bf = "YES (Needs scientific refinement)" if info.get('has_blanket_flags') else "No"
            sz_kb = info.get('size', 0) / 1024
            out.write(f"| `[{sname}](file:///{base_dir.replace('\\', '/')}/{sname})` | {info.get('lines', 0)} | {sz_kb:.1f} | {bf} |\n")
        out.write("\n")

        out.write("## 6. Manifests and Logs Inspected\n\n")
        for mf, sz in manifest_files:
            out.write(f"- `[{mf}](file:///{base_dir.replace('\\', '/')}/{mf.replace('\\', '/')})` ({sz/1024:.1f} KB)\n")
        out.write("\n")

    print(f"Project inventory successfully written to {report_path}")

if __name__ == '__main__':
    run_inventory()
