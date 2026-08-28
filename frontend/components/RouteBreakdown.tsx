import type { BreakdownItem } from "@/lib/types";

const ICONS: Record<BreakdownItem["type"], string> = {
  wait_time: "⏱️",
  rail_usage: "🚃",
  move_ratio: "🚶",
  score_rate: "⭐",
};

// 箇条書きの文章だと4項目が地続きに読めてしまうため、種類ごとに見出しを与えて
// 「数えられる4枚」に分解する
const LABELS: Record<BreakdownItem["type"], string> = {
  wait_time: "開門待ち",
  rail_usage: "電車の利用",
  move_ratio: "移動の割合",
  score_rate: "満足度",
};

export default function RouteBreakdown({ items }: { items: BreakdownItem[] }) {
  return (
    <details className="rounded-card border border-[#e9dcc4] bg-[#fffcf5] p-4 shadow-soft">
      <summary className="cursor-pointer text-lg font-bold text-[#3a3230]">
        このルートの内訳
      </summary>
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div
            key={item.type}
            className="flex items-start gap-3 rounded-panel border border-[#e9dcc4] bg-[#faf4e8] p-3"
          >
            <span
              aria-hidden
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#e9dcc4] bg-[#f4ecdb] text-base"
            >
              {ICONS[item.type]}
            </span>
            <div className="min-w-0">
              <div className="text-xs font-bold text-[#9b9086]">{LABELS[item.type]}</div>
              <div className="mt-0.5 text-sm leading-snug text-[#5d534c]">{item.message}</div>
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}
