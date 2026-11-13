
from pathlib import Path
from astropy.io import fits
import numpy as np

files = sorted(Path("data").rglob("*level2*.fits"))

selected = []

for release in ("qr2", "qr3"):
    matches = [
        f for f in files
        if release in str(f).lower()
    ]
    if matches:
        selected.append(matches[0])

for path in selected:
    print("\n" + "=" * 90)
    print("FILE:", path)

    with fits.open(path, memmap=True) as hdul:

        for hdu in hdul:
            if hdu.name not in ("WCS-WAVE", "EPSF", "PSF"):
                continue

            print("\nHDU:", hdu.name)
            print("TYPE:", type(hdu).__name__)

            if not isinstance(hdu, fits.BinTableHDU):
                print("SHAPE:", hdu.data.shape)
                continue

            print("\nCOLUMN NAMES:", hdu.columns.names)

            for col in hdu.columns:
                print(
                    "COLUMN:", col.name,
                    "| FORMAT:", col.format,
                    "| UNIT:", col.unit
                )

            if hdu.data is None:
                continue

            print("\nTABLE ROWS:", len(hdu.data))

            for name in hdu.columns.names:
                values = hdu.data[name]

                print("\nFIELD:", name)
                print("TYPE:", values.dtype)
                print("SHAPE:", values.shape)

                first = np.asarray(values[0]).ravel()
                print("FIRST ROW SAMPLE:", first[:15])

                if np.issubdtype(first.dtype, np.number):
                    finite = first[np.isfinite(first)]
                    if finite.size:
                        print("MIN:", finite.min())
                        print("MAX:", finite.max())
