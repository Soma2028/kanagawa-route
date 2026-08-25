"use client";

import { useState } from "react";
import type { RouteRequest } from "@/lib/types";

interface Props {
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

export default function SearchForm({ pickedAreas, mustVisit, loading, onSubmit }: Props) {
  const [startHour, setStartHour] = useState(9.0);
  const [budgetHours, setBudgetHours] = useState(6.0);

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
      className="flex flex-col gap-5 rounded-xl border border-[#e0d9cc] bg-white p-5 shadow-sm"
    >
      <h2 className="text-lg font-bold text-[#2c2c2c]">検索条件</h2>

      <label className="flex flex-col gap-1 text-sm text-[#4a4a4a]">
        出発時刻: {formatClock(startHour)}
        <input
          type="range"
          min={7}
          max={12}
          step={0.5}
          value={startHour}
          onChange={(e) => setStartHour(Number(e.target.value))}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm text-[#4a4a4a]">
        持ち時間: {formatDuration(budgetHours)}
        <input
          type="range"
          min={3}
          max={10}
          step={0.5}
          value={budgetHours}
          onChange={(e) => setBudgetHours(Number(e.target.value))}
        />
      </label>

      {mustVisit.length > 0 && (
        <p className="text-xs text-[#4a4a4a]">
          行きたい場所を{mustVisit.length}件選択中（上の一覧で変更できます）
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-[#3d7a6f] px-4 py-2 font-bold text-white transition-opacity disabled:opacity-50"
      >
        {loading ? "計算中..." : "ルートを計算"}
      </button>
    </form>
  );
}
