import type { BreakdownItem } from "@/lib/types";

const ICONS: Record<BreakdownItem["type"], string> = {
  wait_time: "⏱️",
  rail_usage: "🚃",
  move_ratio: "🚶",
  score_rate: "⭐",
};

export default function RouteBreakdown({ items }: { items: BreakdownItem[] }) {
  return (
    <details className="rounded-[24px] border border-[#e9dcc4] bg-[#fffcf5] p-4 shadow-soft">
      <summary className="cursor-pointer text-lg font-bold text-[#3a3230]">
        このルートの内訳
      </summary>
      <ul className="mt-3 flex flex-col gap-2">
        {items.map((item) => (
          <li key={item.type} className="flex items-start gap-2 text-sm text-[#5d534c]">
            <span aria-hidden>{ICONS[item.type]}</span>
            <span>{item.message}</span>
          </li>
        ))}
      </ul>
    </details>
  );
}
