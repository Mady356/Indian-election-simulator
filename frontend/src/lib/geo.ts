import type { FeatureCollection } from "geojson";
import type { LngLatBoundsLike } from "maplibre-gl";

/** Compute bounding box [[west,south],[east,north]] from GeoJSON features. */
export function bboxFromFeatures(
  fc: FeatureCollection,
  padding = 0.15,
): LngLatBoundsLike | null {
  let minLng = Infinity;
  let minLat = Infinity;
  let maxLng = -Infinity;
  let maxLat = -Infinity;

  const extend = (lng: number, lat: number) => {
    minLng = Math.min(minLng, lng);
    minLat = Math.min(minLat, lat);
    maxLng = Math.max(maxLng, lng);
    maxLat = Math.max(maxLat, lat);
  };

  const walkCoords = (coords: unknown): void => {
    if (!coords) return;
    if (Array.isArray(coords) && typeof coords[0] === "number") {
      extend(coords[0], coords[1] as number);
      return;
    }
    if (Array.isArray(coords)) {
      coords.forEach(walkCoords);
    }
  };

  for (const feature of fc.features) {
    const geom = feature.geometry;
    if (!geom || geom.type === "GeometryCollection") continue;
    walkCoords((geom as { coordinates: unknown }).coordinates);
  }

  if (!Number.isFinite(minLng)) return null;

  const lngPad = (maxLng - minLng) * padding || 0.5;
  const latPad = (maxLat - minLat) * padding || 0.5;

  return [
    [minLng - lngPad, minLat - latPad],
    [maxLng + lngPad, maxLat + latPad],
  ];
}
