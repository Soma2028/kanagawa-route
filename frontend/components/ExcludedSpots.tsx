import type { ExcludedSpot } from "@/lib/types";
import { areaColor } from "@/lib/areaStyles";

// 事実の提示に留める（不採用の理由の断定はしない）。数値は「このルートに
// そのまま追加した場合」の試算であることを excluded_note 側で明記している。
function statusLabel(e: ExcludedSpot): string {
  switch (e.status) {
    case "closed":
      return `到着${e.earliest_arrival}想定（${e.closes_at}閉門）`;
    case "over_budget":
      return `+${e.shortfall_minutes}分 超過`;
    case "fits":
      return `+${e.extra_minutes}分で収まる`;
  }
}

export default function ExcludedSpots({
  excluded,
  note,
}: {
  excluded: ExcludedSpot[];
  note: string;
}) {
  if (excluded.length === 0) return null;
  const sorted = [...excluded].sort((a, b) => b.score - a.score);

  return (
    <details className="rounded-card border border-[#e9dcc4] bg-[#fffcf5] p-4 shadow-soft">
      <summary className="cursor-pointer text-lg font-bold text-[#3a3230]">外した候補</summary>
      <p className="mt-1 text-xs text-[#9b9086]">{note}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {sorted.map((e) => (
          <div
            key={e.name}
            className="rounded-chip border border-[#e9dcc4] bg-[#faf4e8] px-3 py-2 text-xs"
          >
            <div className="flex items-center gap-1.5">
              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{ background: areaColor(e.area) }}
              />
              <span className="font-bold text-[#3a3230]">{e.name}</span>
              <span className="ml-auto pl-2 text-[#9b9086]">スコア{e.score}</span>
            </div>
            <div className="mt-1 text-[#9b9086]">{statusLabel(e)}</div>
          </div>
        ))}
      </div>
    </details>
  );
}
