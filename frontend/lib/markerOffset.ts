import type { Stop } from "./types";

/**
 * app.py の地図マーカー重なり回避ロジックの移植（表示上の都合なのでフロント側に置く）。
 * 近接する（0.004度以内の）マーカーが重なるたびに少しずつ回転させてずらす。
 */
export function offsetMarkerPositions(
  stops: Stop[]
): { lat: number; lon: number }[] {
  const seen: { lat: number; lon: number }[] = [];
  return stops.map((stop) => {
    let { lat, lon } = stop;
    const offset = seen.filter(
      (p) => Math.abs(p.lat - lat) < 0.004 && Math.abs(p.lon - lon) < 0.004
    ).length;
    seen.push({ lat: stop.lat, lon: stop.lon });
    if (offset) {
      const angle = offset * 2.4;
      lat += 0.0022 * Math.cos(angle);
      lon += 0.0022 * Math.sin(angle);
    }
    return { lat, lon };
  });
}
