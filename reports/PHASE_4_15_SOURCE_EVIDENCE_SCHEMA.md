# SPECTRA-X / F1 — Phase 4, Task 4.15
# Source Evidence Schema Specification

**Target Contract:** `SourceEvidenceState` & `CatalogSourceContext`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Governance:** Strict Provenance / Fail-Closed Separation / Calibrated Catalog Integrity  
**File Link:** [`catalog_aware_source_masker.py`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/spectra_engine/catalog_aware_source_masker.py#L36-L80)  

---

## 1. Source Evidence States

To prevent unvetted assumptions regarding astronomical catalogs from propagating into spatial anomaly detection, five explicit, non-overlapping evidence states are defined:

```python
class SourceEvidenceState(str, Enum):
    KNOWN_CATALOG_SOURCE = "KNOWN_CATALOG_SOURCE"
    PROBABLE_SOURCE = "PROBABLE_SOURCE"
    AMBIGUOUS_SOURCE = "AMBIGUOUS_SOURCE"
    NO_LOCAL_CATALOG_COUNTERPART = "NO_LOCAL_CATALOG_COUNTERPART"
    MASK_UNVERIFIABLE = "MASK_UNVERIFIABLE"
```

### Detailed Semantics

| Evidence State | Criteria & Astrophysical Meaning | Masking Engine Action | Limitation Code Emitted |
|---|---|---|---|
| `KNOWN_CATALOG_SOURCE` | Source is crossmatched with high astrometric confidence against Gaia DR3, 2MASS, or SPHEREx Level-2 Catalog. Parallax, proper motion, or verified magnitude available. | Generates circular core ($R=2.5\text{ px}$) + 2 px dilation covering PSF footprint. | None (Nominal Vetting) |
| `PROBABLE_SOURCE` | Secondary detection within cutout cone ($d \le 400''$) with consistent flux but limited astrometric epochs. | Generates defensive circular core ($R=2.5\text{ px}$) + dilation. | `PROBABLE_SOURCE_MASKED` |
| `AMBIGUOUS_SOURCE` | Multiple catalog matches within matching tolerance, or RUWE $> 1.40$ indicating unresolved binary or severe astrometric excess noise. | Masked if `mask_ambiguous_sources=True` (default); skipped if False. | `AMBIGUOUS_SOURCE_PRESENT_<id>` |
| `NO_LOCAL_CATALOG_COUNTERPART` | Targeted search conducted within verified catalog footprint, but no cataloged source exists within search radius. | **Zero pixels masked.** Preserves clean background sky. | None |
| `MASK_UNVERIFIABLE` | Cutout lies outside catalog survey footprint, catalog table is missing/corrupted, or WCS projection failed. | **Zero source pixels masked.** Falls back to base Level-2 defect mask. | `SOURCE_EVIDENCE_UNVERIFIABLE_<id>` |

> [!IMPORTANT]
> **Task 4.15B Critical Governance Rule:**  
> A non-detection in Gaia DR3 (`NO_LOCAL_CATALOG_COUNTERPART`) does **NOT** prove that the sky is astrophysically empty. It only indicates that no source above Gaia's limiting magnitude ($G \approx 20.7$) exists in the catalog. True unverified background areas are strictly flagged as `MASK_UNVERIFIABLE`.

---

## 2. CatalogSourceContext Dataclass Specification

The `CatalogSourceContext` is an immutable, frozen dataclass that encapsulates all positional, photometric, and astrometric metadata for a single source:

```python
@dataclass(frozen=True)
class CatalogSourceContext:
    source_id: str                              # Authoritative catalog identifier (e.g., Gaia DR3 source_id)
    catalog_name: str                           # 'GAIA_DR3', 'SPHEREX_L2', '2MASS', 'ALLWISE'
    catalog_version: str                        # 'DR3', 'l2b-v27-2026-222'
    evidence_state: SourceEvidenceState         # One of the 5 enumerated states above
    ra_deg: Optional[float] = None              # Right Ascension (ICRS, degrees)
    dec_deg: Optional[float] = None             # Declination (ICRS, degrees)
    subpixel_x: Optional[float] = None          # 0-indexed cutout X pixel coordinate [0.0, 128.0)
    subpixel_y: Optional[float] = None          # 0-indexed cutout Y pixel coordinate [0.0, 128.0)
    angular_separation_arcsec: Optional[float] = None # Separation from central target
    apparent_magnitude: Optional[float] = None  # G-band or SPHEREx band apparent magnitude
    parallax_mas: Optional[float] = None        # Trigonometric parallax in milliarcseconds
    pmra_mas_yr: Optional[float] = None         # Proper motion in RA * cos(Dec) (mas/yr)
    pmdec_mas_yr: Optional[float] = None        # Proper motion in Dec (mas/yr)
    match_reliability: float = 1.0              # Reliability score [0.0, 1.0]
    is_center_target: bool = False              # TRUE if this record is the central candidate target
    custom_core_radius_pixels: Optional[float] = None # Override PSF radius for extended sources
    notes: str = ""                             # Free-text audit annotations
```

---

## 3. CatalogMaskRequest & CatalogMaskResult Schemas

### CatalogMaskRequest
```python
@dataclass
class CatalogMaskRequest:
    request_id: str                             # Unique tracking ID (e.g., trial_id or candidate_id)
    cutout_shape: Tuple[int, int] = (128, 128)  # Dimensions of input cutout
    target_pixel_x: float = 64.0                # Central evaluation aperture center X
    target_pixel_y: float = 64.0                # Central evaluation aperture center Y
    target_ra_deg: Optional[float] = None       # Central sky coordinates
    target_dec_deg: Optional[float] = None
    base_defect_mask: Optional[np.ndarray] = None # 1=valid, 0=defect (ASTROVISION polarity)
    catalog_sources: List[CatalogSourceContext] = field(default_factory=list)
    dilation_radius_pixels: int = 2             # Supported: 0, 1, 2, 3, 5 px
    core_mask_radius_pixels: float = 2.5        # Base PSF core radius
    protect_central_aperture: bool = True       # Enforces central candidate shield (r <= 2.5 px)
    central_aperture_radius_pixels: float = 2.5 # Radius of central protected aperture
    mask_ambiguous_sources: bool = True         # Policy for AMBIGUOUS_SOURCE
    wcs: Optional[Any] = None                   # Optional Astropy WCS instance
```

### CatalogMaskResult
```python
@dataclass(frozen=True)
class CatalogMaskResult:
    request_id: str
    combined_effective_mask: np.ndarray         # ASTROVISION polarity: 1=valid sky, 0=masked
    catalog_source_mask: np.ndarray             # Standalone source mask: 1=source masked, 0=sky
    original_defect_mask: np.ndarray            # Preserved pristine base defect mask
    cutout_shape: Tuple[int, int]               # (128, 128)
    total_pixels: int                           # 16,384
    original_defect_pixel_count: int            # Bad detector pixels
    catalog_masked_pixel_count: int             # Additional pixels masked by catalog sources
    effective_valid_pixel_count: int            # Net valid photosensitive pixels
    masked_area_fraction_pct: float             # Total masked fraction (%)
    central_aperture_encroached: bool           # True if any central aperture pixel masked
    central_aperture_masked_fraction_pct: float # Percent of central aperture masked
    masked_sources_count: int                   # Number of sources masked
    unverifiable_sources_count: int             # Number of unverifiable sources
    ambiguous_sources_count: int                # Number of ambiguous sources
    dilation_radius_pixels: int                 # Applied dilation level
    limitation_codes: List[str]                 # Advisory and limitation codes
    provenance_metadata: Dict[str, Any]         # Execution environment and timing
```

---

## 4. Serialization & Round-Trip Governance

All dataclasses provide lossless JSON and dictionary serialization:
- `CatalogSourceContext.to_dict()` and `from_dict()`
- `CatalogMaskResult.to_dict(include_arrays=False)` for audit reporting and logging
- Bitwise reproducibility across operating systems and hardware configurations.

