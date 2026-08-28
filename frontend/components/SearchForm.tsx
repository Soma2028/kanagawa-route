"use client";

import type { RouteRequest } from "@/lib/types";

interface Props {
  startHour: number;
  onStartHourChange: (hour: number) => void;
  budgetHours: number;
  onBudgetHoursChange: (hours: number) => void;
  pickedAreas: string[];
  mustVisit: string[];
  loading: boolean;
  onSubmit: (req: RouteRequest) => void;
}

// 計算時間・開門待ちの許容は開発者向けの調整値のため、UIには出さず固定する
const SEARCH_SEC = 5;
const MAX_WAIT = 60;

function formatClock(hour: number): string {
  const h = Math.floor(hour);
  const m = Math.round((hour % 1) * 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function formatDuration(hours: number): string {
  const h = Math.floor(hours);
  const m = Math.round((hours % 1) * 60);
  return m === 0 ? `${h}時間` : `${h}時間${m}分`;
}

export default function SearchForm({
  startHour,
  onStartHourChange,
  budgetHours,
  onBudgetHoursChange,
  pickedAreas,
  mustVisit,
  loading,
  onSubmit,
}: Props) {
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      start_hour: startHour,
      budget_hours: budgetHours,
      areas: pickedAreas,
      must_visit: mustVisit,
      search_sec: SEARCH_SEC,
      max_wait: MAX_WAIT,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-5 rounded-[24px] border border-[#e9dcc4] bg-[#fffcf5] p-5 shadow-soft"
    >
      <h2 className="text-lg font-bold text-[#3a3230]">検索条件</h2>

      <label className="flex flex-col gap-1 text-sm text-[#5d534c]">
        出発時刻: {formatClock(startHour)}
        <input
          type="range"
          min={7}
          max={12}
          step={0.5}
          value={startHour}
          onChange={(e) => onStartHourChange(Number(e.target.value))}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm text-[#5d534c]">
        持ち時間: {formatDuration(budgetHours)}
        <input
          type="range"
          min={3}
          max={10}
          step={0.5}
          value={budgetHours}
          onChange={(e) => onBudgetHoursChange(Number(e.target.value))}
        />
      </label>

      {mustVisit.length > 0 && (
        <p className="text-xs text-[#5d534c]">
          行きたい場所を{mustVisit.length}件選択中（上の一覧で変更できます）
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="rounded-full bg-[#3d7a6f] px-4 py-2 font-bold text-white shadow-btn transition-opacity disabled:opacity-50"
      >
        {loading ? "計算中..." : "ルートを計算"}
      </button>
    </form>
  );
}
