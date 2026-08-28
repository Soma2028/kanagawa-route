"use client";

import Image from "next/image";
import type { SpotSummary } from "@/lib/types";
import { areaColor } from "@/lib/areaStyles";

interface Props {
  areas: string[];
  spots: SpotSummary[];
  pickedAreas: string[];
  onToggleArea: (area: string) => void;
  mustVisit: string[];
  onToggleSpot: (name: string) => void;
}

export default function SpotPicker({
  areas,
  spots,
  pickedAreas,
  onToggleArea,
  mustVisit,
  onToggleSpot,
}: Props) {
  // エリアで絞り込む → その中から場所を選ぶ、の2段階（未選択なら全域を表示）
  const visible =
    pickedAreas.length > 0 ? spots.filter((s) => pickedAreas.includes(s.area)) : spots;

  return (
    <section className="rounded-card border border-[#e9dcc4] bg-[#fffcf5] p-5 shadow-soft">
      <h2 className="text-lg font-bold text-[#3a3230]">行きたい場所を選ぶ</h2>
      <p className="mt-1 text-xs text-[#9b9086]">
        選んだ場所は必ずルートに含めます（未選択なら自動で選びます）
      </p>

      <fieldset className="mt-4 flex flex-col gap-1 text-sm text-[#5d534c]">
        <legend className="mb-1">エリアで絞り込む（未選択なら全域）</legend>
        <div className="flex flex-wrap gap-2">
          {areas.map((area) => (
            <button
              type="button"
              key={area}
              onClick={() => onToggleArea(area)}
              className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                pickedAreas.includes(area)
                  ? "border-[#3d7a6f] bg-[#3d7a6f] text-white"
                  : "border-[#e9dcc4] bg-[#f4ecdb] text-[#5d534c]"
              }`}
            >
              {area}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {visible.map((spot) => {
          const picked = mustVisit.includes(spot.name);
          const color = areaColor(spot.area);
          return (
            <button
              type="button"
              key={spot.name}
              onClick={() => onToggleSpot(spot.name)}
              className={`flex flex-col overflow-hidden rounded-tile border text-left transition-colors ${
                picked ? "border-[#3d7a6f] ring-2 ring-[#3d7a6f]" : "border-[#e9dcc4]"
              }`}
            >
              <div className="relative h-20 w-full bg-[#f4ecdb]">
                {spot.photo_url && (
                  <Image
                    src={spot.photo_url}
                    alt={spot.name}
                    fill
                    unoptimized
                    className="object-cover"
                  />
                )}
                {picked && (
                  <span className="absolute top-1 right-1 flex h-5 w-5 items-center justify-center rounded-full bg-[#3d7a6f] text-[0.7rem] font-bold text-white">
                    ✓
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1 px-1.5 py-1">
                <span
                  className="h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{ background: color }}
                />
                <span className="truncate text-[0.72rem] text-[#3a3230]">{spot.name}</span>
              </div>
            </button>
          );
        })}
      </div>

      {mustVisit.length > 0 && (
        <p className="mt-3 text-xs text-[#5d534c]">
          選択中（{mustVisit.length}件）: {mustVisit.join(" / ")}
        </p>
      )}
    </section>
  );
}
