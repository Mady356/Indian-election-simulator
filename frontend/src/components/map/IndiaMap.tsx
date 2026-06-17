import { useEffect, useRef, useCallback } from "react";
import maplibregl from "maplibre-gl";
import type { FeatureCollection } from "geojson";
import { COLORS, GEO_URLS, INDIA_BOUNDS } from "@/lib/constants";
import { bboxFromFeatures } from "@/lib/geo";
import { matchStateName, normalizeKey, titleCase } from "@/lib/utils";
import type { MapMode } from "@/types";

interface IndiaMapProps {
  mode: MapMode;
  selectedState: string | null;
  onStateClick: (stateName: string) => void;
  onDistrictClick: (districtName: string, stateName: string) => void;
  onConstituencyClick: (pcName: string, stateName: string) => void;
  className?: string;
  fillColor?: string | maplibregl.ExpressionSpecification;
}

const EMPTY_FC: FeatureCollection = { type: "FeatureCollection", features: [] };

const INDIA_MAX_BOUNDS: maplibregl.LngLatBoundsLike = [
  [60, 4],
  [100, 40],
];

export function IndiaMap({
  mode,
  selectedState,
  onStateClick,
  onDistrictClick,
  onConstituencyClick,
  className,
  fillColor,
}: IndiaMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const dataRef = useRef<FeatureCollection>(EMPTY_FC);

  const getGeoUrl = useCallback(() => {
    if (mode === "constituency") return GEO_URLS.constituencies;
    if (mode === "district") return GEO_URLS.districts;
    return GEO_URLS.states;
  }, [mode]);

  const filterFeatures = useCallback(
    (data: FeatureCollection): FeatureCollection => {
      if (!selectedState || mode === "state") return data;

      const stateKey = normalizeKey(selectedState);
      const features = data.features.filter((f) => {
        const props = f.properties || {};
        if (mode === "district") {
          const geoState = String(props.NAME_1 || "");
          return (
            normalizeKey(geoState).includes(stateKey) ||
            stateKey.includes(normalizeKey(geoState).split(" ")[0] || "")
          );
        }
        if (mode === "constituency") {
          return matchStateName(String(props.st_name || ""), selectedState);
        }
        return true;
      });
      return { type: "FeatureCollection", features };
    },
    [mode, selectedState],
  );

  const flyToData = useCallback((data: FeatureCollection) => {
    const map = mapRef.current;
    if (!map) return;
    const bounds = bboxFromFeatures(data);
    if (bounds) {
      map.fitBounds(bounds, { padding: 48, duration: 900, maxZoom: 10 });
    } else {
      map.fitBounds(INDIA_BOUNDS, { padding: 40, duration: 900 });
    }
  }, []);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: { "background-color": COLORS.bg },
          },
        ],
      },
      center: [78.9, 22.5],
      zoom: 4.2,
      minZoom: 3,
      maxZoom: 14,
      maxBounds: INDIA_MAX_BOUNDS,
      scrollZoom: true,
      boxZoom: true,
      dragRotate: false,
      pitchWithRotate: false,
      touchZoomRotate: true,
      doubleClickZoom: true,
      cooperativeGestures: false,
      attributionControl: false,
    });

    map.scrollZoom.setWheelZoomRate(1 / 200);
    map.scrollZoom.setZoomRate(1 / 100);

    map.addControl(
      new maplibregl.NavigationControl({ showCompass: false, visualizePitch: false }),
      "top-right",
    );
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 100, unit: "metric" }), "bottom-left");

    mapRef.current = map;

    map.on("load", () => {
      map.addSource("india", { type: "geojson", data: EMPTY_FC, generateId: true });
      map.addLayer({
        id: "india-fill",
        type: "fill",
        source: "india",
        paint: {
          "fill-color": fillColor || [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            COLORS.primary,
            ["boolean", ["feature-state", "hover"], false],
            "#3B6FD9",
            "#1A2744",
          ],
          "fill-opacity": 0.75,
        },
      });
      map.addLayer({
        id: "india-outline",
        type: "line",
        source: "india",
        paint: {
          "line-color": COLORS.border,
          "line-width": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            2,
            0.6,
          ],
        },
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [fillColor]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    let hoveredId: string | number | undefined;

    const loadData = async () => {
      const res = await fetch(getGeoUrl());
      const raw: FeatureCollection = await res.json();
      dataRef.current = filterFeatures(raw);
      const source = map.getSource("india") as maplibregl.GeoJSONSource;
      if (source) source.setData(dataRef.current);

      if (selectedState && mode !== "state") {
        flyToData(dataRef.current);
      } else if (mode === "state" && !selectedState) {
        map.fitBounds(INDIA_BOUNDS, { padding: 40, duration: 600 });
      }
    };

    loadData();

    const onMouseMove = (
      e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] },
    ) => {
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
      let name = "";
      if (mode === "state") name = titleCase(String(props.state_name || ""));
      else if (mode === "district") name = String(props.NAME_2 || "");
      else name = String(props.pc_name || "");

      const popup =
        popupRef.current ||
        new maplibregl.Popup({ closeButton: false, closeOnClick: false });
      popupRef.current = popup;
      popup.setLngLat(e.lngLat).setHTML(`<strong>${name}</strong>`).addTo(map);
    };

    const onMouseLeave = () => {
      if (hoveredId !== undefined) {
        map.setFeatureState({ source: "india", id: hoveredId }, { hover: false });
      }
      hoveredId = undefined;
      map.getCanvas().style.cursor = "grab";
      popupRef.current?.remove();
    };

    const onClick = (
      e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] },
    ) => {
      if (!e.features?.length) return;
      const props = e.features[0].properties || {};
      if (mode === "state") {
        onStateClick(titleCase(String(props.state_name || "")));
      } else if (mode === "district") {
        onDistrictClick(String(props.NAME_2 || ""), String(props.NAME_1 || ""));
      } else {
        onConstituencyClick(String(props.pc_name || ""), String(props.st_name || ""));
      }
    };

    map.getCanvas().style.cursor = "grab";

    map.on("mousemove", "india-fill", onMouseMove);
    map.on("mouseleave", "india-fill", onMouseLeave);
    map.on("click", "india-fill", onClick);

    return () => {
      map.off("mousemove", "india-fill", onMouseMove);
      map.off("mouseleave", "india-fill", onMouseLeave);
      map.off("click", "india-fill", onClick);
    };
  }, [
    mode,
    selectedState,
    getGeoUrl,
    filterFeatures,
    onStateClick,
    onDistrictClick,
    onConstituencyClick,
    flyToData,
  ]);

  useEffect(() => {
    if (fillColor && mapRef.current?.getLayer("india-fill")) {
      mapRef.current.setPaintProperty("india-fill", "fill-color", fillColor);
    }
  }, [fillColor]);

  return (
    <div className={`relative ${className || "h-full w-full rounded-xl overflow-hidden"}`}>
      <div ref={containerRef} className="h-full w-full" />
      <div className="pointer-events-none absolute bottom-3 right-3 rounded-lg border border-border/60 bg-card/80 px-2.5 py-1.5 text-[10px] text-muted backdrop-blur-sm">
        Scroll · pinch · +/- to zoom · drag to pan
      </div>
    </div>
  );
}
