import type { Summary } from "@/lib/types";

function Card({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="h-full rounded-xl border border-[#e0d9cc] bg-white p-5 shadow-sm">
      <div className="mb-1.5 text-[0.85rem] text-[#6b6b6b]">{label}</div>
      <div className="text-[1.9rem] font-bold leading-tight text-[#2c2c2c]">
        {value}
      </div>
      <div className="mt-1 text-[0.8rem] text-[#8a8a8a]">{sub}</div>
    </div>
  );
}

export default function SummaryCards({ summary }: { summary: Summary }) {
  const hours = (summary.end_min / 60).toFixed(1);
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Card
        label="満足度スコア"
        value={`${summary.total_score}`}
        sub={`訪問 ${summary.visited_count}件`}
      />
      <Card
        label="所要時間"
        value={`${hours}時間`}
        sub={`移動 ${summary.move_total_min}分 / 滞在 ${summary.stay_total_min}分`}
      />
      <Card
        label="拝観料合計"
        value={`¥${summary.total_fee.toLocaleString()}`}
        sub={`帰着 ${summary.end_clock}`}
      />
    </div>
  );
}
