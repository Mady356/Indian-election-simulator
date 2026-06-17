"""
Build DHS cluster geospatial layer from GE shapefiles and export public map data.

Run as:
    python -m src.demographics.dhs.build_dhs_geospatial_layer
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import shapefile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import DHS_DOWNLOADS_DIR, DHS_EXTRACTED_DIR
from src.demographics.dhs.filename_parser import parse_dhs_filename
from src.demographics.dhs.paths import DHS_CLUSTER_GEOSPATIAL, DHS_GEOSPATIAL_PUBLIC


def extract_ge_shapefile(zip_path: Path, out_dir: Path) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = zip_path.stem.upper().replace(".ZIP", "")
    shp = out_dir / f"{stem}.shp"
    if shp.exists():
        return shp
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            target = out_dir / Path(name).name
            if not target.exists():
                with zf.open(name) as src, open(target, "wb") as dst:
                    dst.write(src.read())
    return shp if shp.exists() else None


def anonymize_cluster_id(cluster_id: int, survey: str) -> str:
    digest = hashlib.sha256(f"{survey}:{cluster_id}".encode()).hexdigest()
    return digest[:12]


def build_from_shapefile(shp_path: Path, survey: str, version_code: str, source_file: str) -> pd.DataFrame:
    sf = shapefile.Reader(str(shp_path))
    fields = [f[0] for f in sf.fields[1:]]
    rows = []
    for rec in sf.records():
        d = dict(zip(fields, rec))
        lat = float(d.get("LATNUM", np.nan)) if d.get("LATNUM") not in (None, "", " ") else None
        lon = float(d.get("LONGNUM", np.nan)) if d.get("LONGNUM") not in (None, "", " ") else None
        if lat is None or lon is None:
            continue
        cluster = int(float(d["DHSCLUST"]))
        urban = str(d.get("URBAN_RURA", "")).strip()
        rows.append(
            {
                "survey": survey,
                "survey_version_code": version_code,
                "cluster_id": cluster,
                "state_or_region": str(d.get("ADM1NAME", "")).strip(),
                "district_if_available": str(d.get("DHSREGNA", "")).strip(),
                "latitude": lat,
                "longitude": lon,
                "urban_rural": "urban" if urban.upper().startswith("U") else "rural",
                "source_file": source_file,
                "gps_displaced": True,
                "safe_for_exact_matching": False,
            }
        )
    return pd.DataFrame(rows)


def export_public(df: pd.DataFrame) -> pd.DataFrame:
    pub = df.copy()
    pub["cluster_id"] = pub.apply(
        lambda r: anonymize_cluster_id(int(r["cluster_id"]), str(r["survey"])),
        axis=1,
    )
    pub["latitude"] = pub["latitude"].round(2)
    pub["longitude"] = pub["longitude"].round(2)
    keep = [
        "cluster_id",
        "survey",
        "survey_version_code",
        "state_or_region",
        "district_if_available",
        "latitude",
        "longitude",
        "urban_rural",
        "gps_displaced",
        "safe_for_exact_matching",
    ]
    return pub[keep]


def main() -> None:
    ge_zips = []
    for path in sorted(DHS_DOWNLOADS_DIR.glob("IAGE*.zip")):
        info = parse_dhs_filename(path.name)
        if info.parse_ok and info.dataset_type_code == "GE":
            ge_zips.append((path, info))

    if not ge_zips:
        print(f"No GE zips in {DHS_DOWNLOADS_DIR}")
        return

    frames = []
    for zip_path, info in ge_zips:
        out_dir = DHS_EXTRACTED_DIR / f"ge_{zip_path.stem.upper()}"
        shp = extract_ge_shapefile(zip_path, out_dir)
        if not shp:
            print(f"  SKIP: no shapefile in {zip_path.name}")
            continue
        print(f"  Reading {shp.name}...")
        frame = build_from_shapefile(shp, info.survey, info.version_code, zip_path.name)
        frames.append(frame)
        print(f"    clusters: {len(frame)}")

    if not frames:
        return

    df = pd.concat(frames, ignore_index=True)
    DHS_CLUSTER_GEOSPATIAL.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DHS_CLUSTER_GEOSPATIAL, index=False)

    pub = export_public(df)
    DHS_GEOSPATIAL_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    pub.to_csv(DHS_GEOSPATIAL_PUBLIC, index=False)

    print(f"\nSaved: {DHS_CLUSTER_GEOSPATIAL} ({len(df)} clusters)")
    print(f"Saved: {DHS_GEOSPATIAL_PUBLIC} (public-safe)")
    print(f"  States/regions: {df['state_or_region'].nunique()}")
    print(f"  Districts     : {df['district_if_available'].nunique()}")


if __name__ == "__main__":
    main()
