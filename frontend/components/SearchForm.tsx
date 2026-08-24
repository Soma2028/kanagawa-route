"use client";

import { useState } from "react";
import type { RouteRequest } from "@/lib/types";

interface Props {
  areas: string[];
  loading: boolean;
  onSubmit: (req: RouteRequest) => void;
}

const SEARCH_SEC_OPTIONS = [5, 15, 30];

export default function SearchForm({ areas, loading, onSubmit }: Props) {
  const [startHour, setStartHour] = useState(9.0);
  const [budgetHours, setBudgetHours] = useState(6.0);
  const [picked, setPicked] = useState<string[]>([]);
  const [searchSec, setSearchSec] = useState(5);
  const [maxWait, setMaxWait] = useState(60);

  function toggleArea(area: string) {
    setPicked((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      start_hour: startHour,
      budget_hours: budgetHours,
      areas: picked,
      search_sec: searchSec,
      max_wait: maxWait,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-5 rounded-xl border border-[#e0d9cc] bg-white p-5 shadow-sm"
    >
      <h2 className="text-lg font-bold text-[#2c2c2c]">検索条件</h2>

      <label className="flex flex-col gap-1 text-sm text-[#4a4a4a]">
        出発時刻: {startHour.toFixed(1)}時
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
        持ち時間: {budgetHours.toFixed(1)}時間
        <input
          type="range"
          min={3}
          max={10}
          step={0.5}
          value={budgetHours}
          onChange={(e) => setBudgetHours(Number(e.target.value))}
        />
      </label>

      <fieldset className="flex flex-col gap-1 text-sm text-[#4a4a4a]">
        <legend className="mb-1">行きたいエリア（未選択なら全域から選びます）</legend>
        <div className="flex flex-wrap gap-2">
          {areas.map((area) => (
            <button
              type="button"
              key={area}
              onClick={() => toggleArea(area)}
              className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                picked.includes(area)
                  ? "border-[#3d7a6f] bg-[#3d7a6f] text-white"
                  : "border-[#e0d9cc] bg-[#f2ede3] text-[#4a4a4a]"
              }`}
            >
              {area}
            </button>
          ))}
        </div>
      </fieldset>

      <details className="text-sm text-[#4a4a4a]">
        <summary className="cursor-pointer select-none">詳細設定</summary>
        <div className="mt-3 flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            計算時間（秒）
            <select
              value={searchSec}
              onChange={(e) => setSearchSec(Number(e.target.value))}
              className="rounded border border-[#e0d9cc] px-2 py-1"
            >
              {SEARCH_SEC_OPTIONS.map((sec) => (
                <option key={sec} value={sec}>
                  {sec}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            開門待ちの許容: {maxWait}分
            <input
              type="range"
              min={0}
              max={90}
              step={15}
              value={maxWait}
              onChange={(e) => setMaxWait(Number(e.target.value))}
            />
          </label>
        </div>
      </details>

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
