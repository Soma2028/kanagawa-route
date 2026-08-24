"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect } from "react";
import { MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { RouteResponse } from "@/lib/types";
import { AREA_COLORS, areaColor } from "@/lib/areaStyles";
import { offsetMarkerPositions } from "@/lib/markerOffset";

const TILE_URL = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

function markerIcon(color: string, label: string) {
  return L.divIcon({
    className: "",
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    html: `<div style="background:${color};color:#fff;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);">${label}</div>`,
  });
}

function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 0) {
      map.fitBounds(L.latLngBounds(positions), { padding: [30, 30] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [positions.map((p) => p.join(",")).join("|")]);
  return null;
}

export default function RouteMap({ route }: { route: RouteResponse }) {
  const { stops, segments } = route;
  const rawPositions: [number, number][] = stops.map((s) => [s.lat, s.lon]);
  const markerPositions = offsetMarkerPositions(stops).map(
    (p): [number, number] => [p.lat, p.lon]
  );

  return (
    <div>
      <h2 className="mb-3 text-lg font-bold text-[#2c2c2c]">ルートマップ</h2>
      <div className="h-[620px] w-full overflow-hidden rounded-xl border border-[#e0d9cc]">
        <MapContainer
          center={rawPositions[0] ?? [35.3192, 139.55]}
          zoom={14}
          scrollWheelZoom
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
          <FitBounds positions={rawPositions} />

          {segments.map((seg, i) => (
            <Polyline
              key={i}
              positions={[rawPositions[seg.from_index], rawPositions[seg.to_index]]}
              pathOptions={
                seg.mode === "鉄道"
                  ? { color: "#ff9800", weight: 3, opacity: 0.9, dashArray: "8, 8" }
                  : { color: "#5a8a7a", weight: 4, opacity: 0.7 }
              }
            >
              <Tooltip>{seg.mode === "鉄道" ? "電車" : "徒歩"}</Tooltip>
            </Polyline>
          ))}

          {stops.map((stop, order) => (
            <Marker
              key={stop.name + order}
              position={markerPositions[order]}
              icon={markerIcon(areaColor(stop.area), order === 0 ? "S" : String(order))}
            >
              <Tooltip>
                {order === 0 ? "S" : order}. {stop.name} {stop.arrival_clock}
              </Tooltip>
            </Marker>
          ))}
        </MapContainer>
      </div>

      <div className="mt-3 flex flex-wrap gap-2.5">
        {Object.entries(AREA_COLORS)
          .filter(([area]) => area !== "起点")
          .map(([area, color]) => (
            <span key={area} className="inline-flex items-center text-[0.78rem]">
              <span
                className="mr-1 inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: color }}
              />
              {area}
            </span>
          ))}
      </div>
      <p className="mt-1 text-[0.8rem] text-[#8a8a8a]">
        実線＝徒歩 / オレンジの破線＝電車
      </p>
    </div>
  );
}
