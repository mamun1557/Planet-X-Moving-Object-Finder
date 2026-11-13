
from pathlib import Path
from astropy.io import fits

files = sorted(Path("data").rglob("*level2*.fits"))

print("Found Level-2 FITS:", len(files))

# One representative QR2 and one QR3 file
selected = []
for release in ("QR2", "QR3"):
    matches = [
        f for f in files
        if release.lower() in str(f).lower()
    ]
    if matches:
        selected.append(matches[0])

# If release is not in folder paths, use filename prefixes
if len(selected) < 2:
    selected = files[:2]

for path in selected:
    print("\n" + "=" * 80)
    print("FILE:", path)

    with fits.open(path, memmap=True) as hdul:
        hdul.info()

        for i, hdu in enumerate(hdul):
            print(f"\nHDU {i}")
            print("EXTNAME:", hdu.header.get("EXTNAME"))
            print("SHAPE:", getattr(hdu, "shape", None))
            print("BITPIX:", hdu.header.get("BITPIX"))

            keys = [
                "DATE-OBS", "MJD-OBS", "RA", "DEC",
                "CRVAL1", "CRVAL2", "CTYPE1", "CTYPE2",
                "WAVELMIN", "WAVELMAX", "BUNIT"
            ]

            for key in keys:
                if key in hdu.header:
                    print(f"{key}: {hdu.header[key]}")
