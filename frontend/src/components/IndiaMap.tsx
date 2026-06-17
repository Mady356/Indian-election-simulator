import { useEffect, useRef, useCallback } from "react";
import maplibregl from "maplibre-gl";
import type { FeatureCollection } from "geojson";
import { COLORS, GEO_URLS, INDIA_BOUNDS, type MapColorMode } from "@/lib/constants";
import { bboxFromFeatures } from "@/lib/geo";
import {
  coverageColor,
  normalizeKey,
  partyColor,
  swingColor,
  titleCase,
} from "@/lib/format";
import {
  matchGeoConstituency,
  type ConstituencyRecord,
  type DashboardData,
} from "@/lib/data";

interface IndiaMapProps {
  data: DashboardData;
  colorMode: MapColorMode;
  stateFilter: string | null;
  selected?: ConstituencyRecord | null;
  onConstituencyClick: (record: ConstituencyRecord) => void;
  className?: string;
}

const EMPTY_FC: FeatureCollection = { type: "FeatureCollection", features: [] };

function mapFillColor(record: ConstituencyRecord | undefined, mode: MapColorMode): string {
  if (!record) return "#1f2937";
  if (mode === "winner_2024") return partyColor(record.winner_party_2024);
  if (mode === "bjp_swing") return swingColor(record.bjp_swing_2019_2024);
  if (mode === "inc_swing") return swingColor(record.inc_swing_2019_2024);
  return coverageColor(record.data_quality_label);
}

export function IndiaMap({
  data,
  colorMode,
  stateFilter,
  selected,
  onConstituencyClick,
  className,
}: IndiaMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const onClickRef = useRef(onConstituencyClick);

  onClickRef.current = onConstituencyClick;

  const enrichGeo = useCallback(
    (raw: FeatureCollection): FeatureCollection => {
      const stateNorm = stateFilter ? normalizeKey(stateFilter) : null;
      const features = raw.features
        .filter((f) => {
          if (!stateNorm) return true;
          const st = String(f.properties?.st_name || "");
          return normalizeKey(st) === stateNorm;
        })
        .map((f) => {
          const props = f.properties || {};
          const record = matchGeoConstituency(
            String(props.st_name || ""),
            String(props.pc_name || ""),
            data.constituencyByKey,
          );
          return {
            ...f,
            properties: {
              ...props,
              map_color: mapFillColor(record, colorMode),
              matched: record ? 1 : 0,
              constituency_key: record?.constituency_key || "",
              state_key: record?.state_key || "",
            },
          };
        });
      return { type: "FeatureCollection", features };
    },
    [colorMode, data.constituencyByKey, stateFilter],
  );

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [{ id: "background", type: "background", paint: { "background-color": COLORS.bg } }],
      },
      center: [78.9, 22.5],
      zoom: 4.2,
      minZoom: 3,
      maxZoom: 12,
      dragRotate: false,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("india", { type: "geojson", data: EMPTY_FC, generateId: true });
      map.addLayer({
        id: "india-fill",
        type: "fill",
        source: "india",
        paint: {
          "fill-color": ["coalesce", ["get", "map_color"], "#1f2937"],
          "fill-opacity": 0.8,
        },
      });
      map.addLayer({
        id: "india-outline",
        type: "line",
        source: "india",
        paint: {
          "line-color": COLORS.border,
          "line-width": ["case", ["boolean", ["feature-state", "hover"], false], 1.5, 0.5],
        },
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    let hoveredId: string | number | undefined;
    let cancelled = false;

    const load = async () => {
      try {
        const res = await fetch(GEO_URLS.constituencies);
        if (!res.ok) throw new Error("GeoJSON missing");
        const raw: FeatureCollection = await res.json();
        if (cancelled) return;
        const enriched = enrichGeo(raw);
        const source = map.getSource("india") as maplibregl.GeoJSONSource | undefined;
        source?.setData(enriched);
        const bounds = bboxFromFeatures(enriched);
        if (bounds) map.fitBounds(bounds, { padding: 48, duration: 700, maxZoom: stateFilter ? 8 : 5 });
        else map.fitBounds(INDIA_BOUNDS, { padding: 40 });
      } catch {
        const source = map.getSource("india") as maplibregl.GeoJSONSource | undefined;
        source?.setData(EMPTY_FC);
      }
    };

    if (map.isStyleLoaded()) load();
    else map.once("load", load);

    const onMove = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
      if (!e.features?.length) return;
      if (hoveredId !== undefined) {
        map.setFeatureState({ source: "india", id: hoveredId }, { hover: false });
      }
      hoveredId = e.features[0].id;
      if (hoveredId !== undefined) {
        map.setFeatureState({ source: "india", id: hoveredId }, { hover: true });
      }
      map.getCanvas().style.cursor = "pointer";
      const props = e.features[0].properties || {};
      const name = String(props.pc_name || "");
      const popup = popupRef.current || new maplibregl.Popup({ closeButton: false, closeOnClick: false });
      popupRef.current = popup;
      popup.setLngLat(e.lngLat).setHTML(`<strong>${titleCase(name)}</strong>`).addTo(map);
    };

    const onLeave = () => {
      if (hoveredId !== undefined) {
        map.setFeatureState({ source: "india", id: hoveredId }, { hover: false });
      }
      hoveredId = undefined;
      map.getCanvas().style.cursor = "grab";
      popupRef.current?.remove();
    };

    const onClick = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
      if (!e.features?.length) return;
      const props = e.features[0].properties || {};
      const record = matchGeoConstituency(
        String(props.st_name || ""),
        String(props.pc_name || ""),
        data.constituencyByKey,
      );
      if (record) onClickRef.current(record);
    };

    map.on("mousemove", "india-fill", onMove);
    map.on("mouseleave", "india-fill", onLeave);
    map.on("click", "india-fill", onClick);

    return () => {
      cancelled = true;
      map.off("mousemove", "india-fill", onMove);
      map.off("mouseleave", "india-fill", onLeave);
      map.off("click", "india-fill", onClick);
    };
  }, [data, enrichGeo, stateFilter, colorMode]);

  return (
    <div className={`relative overflow-hidden rounded-xl border border-border ${className || "h-full min-h-[420px]"}`}>
      <div ref={containerRef} className="h-full w-full min-h-[420px]" />
      {selected ? (
        <div className="pointer-events-none absolute left-3 top-3 rounded-lg border border-border bg-card/90 px-3 py-1.5 text-xs backdrop-blur">
          Selected: <strong>{selected.constituency}</strong>
        </div>
      ) : null}
    </div>
  );
}
