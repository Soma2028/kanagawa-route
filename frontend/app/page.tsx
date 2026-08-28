"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import ExcludedSpots from "@/components/ExcludedSpots";
import Hero from "@/components/Hero";
import LoadingMessage from "@/components/LoadingMessage";
import RouteBreakdown from "@/components/RouteBreakdown";
import SearchForm from "@/components/SearchForm";
import SpotPicker from "@/components/SpotPicker";
import Timeline from "@/components/Timeline";
import { ApiError, fetchAreas, fetchRoute, fetchSpots } from "@/lib/api";
import type { RouteRequest, RouteResponse, SpotSummary } from "@/lib/types";

// Leaflet は window/document に依存するためサーバーではレンダリングしない
const RouteMap = dynamic(() => import("@/components/RouteMap"), { ssr: false });

export default function Home() {
  const [view, setView] = useState<"input" | "result">("input");
  const [areas, setAreas] = useState<string[]>([]);
  const [spots, setSpots] = useState<SpotSummary[]>([]);
  const [pickedAreas, setPickedAreas] = useState<string[]>([]);
  const [mustVisit, setMustVisit] = useState<string[]>([]);
  const [startHour, setStartHour] = useState(9.0);
  const [budgetHours, setBudgetHours] = useState(6.0);
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [lastRequest, setLastRequest] = useState<RouteRequest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAreas()
      .then(setAreas)
      .catch(() => setError("エリア一覧の取得に失敗しました。バックエンドが起動しているか確認してください。"));
    fetchSpots()
      .then(setSpots)
      .catch(() => setError("スポット一覧の取得に失敗しました。バックエンドが起動しているか確認してください。"));
  }, []);

  function toggleArea(area: string) {
    setPickedAreas((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
    );
  }

  function toggleSpot(name: string) {
    setMustVisit((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  }

  async function handleSubmit(req: RouteRequest) {
    setView("result");
    setLastRequest(req);
    setLoading(true);
    setError(null);
    try {
      const result = await fetchRoute(req);
      setRoute(result);
    } catch (e) {
      setRoute(null);
      setError(e instanceof ApiError ? e.message : "予期しないエラーが発生しました");
    } finally {
      setLoading(false);
    }
  }

  if (view === "result") {
    return (
      <div className="mx-auto max-w-6xl px-6 py-8">
        <Hero route={route} request={lastRequest} />

        <button
          type="button"
          onClick={() => setView("input")}
          className="mt-4 rounded-full border border-[#e9dcc4] bg-[#fffcf5] px-4 py-2 shadow-soft text-sm font-medium text-[#5d534c] transition-colors hover:bg-[#f4ecdb]"
        >
          ← 条件を変える
        </button>

        <div className="mt-6">
          {error && (
            <div className="mb-4 rounded-inset border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {loading && <LoadingMessage />}

          {route && (
            <div className="flex flex-col gap-6">
              {route.lunch_note && (
                <div className="rounded-inset border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  {route.lunch_note}
                </div>
              )}
              <Timeline route={route} />
              <RouteMap route={route} />
              <RouteBreakdown items={route.breakdown} />
              <ExcludedSpots excluded={route.excluded} note={route.excluded_note} />
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <section className="rounded-band bg-[#3d7a6f] px-5 py-4 shadow-hero sm:px-8 sm:py-5">
        <h1 className="text-xl font-bold text-white sm:text-2xl">⛩️ 鎌倉 周遊ルート最適化</h1>
        <p className="mt-0.5 text-xs text-white/80 sm:text-sm">
          持ち時間と好みに合わせて、満足度が最大になる順路を提案します
        </p>
      </section>

      <div className="mt-6">
        <SpotPicker
          areas={areas}
          spots={spots}
          pickedAreas={pickedAreas}
          onToggleArea={toggleArea}
          mustVisit={mustVisit}
          onToggleSpot={toggleSpot}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="sticky top-4 self-start">
          <SearchForm
            startHour={startHour}
            onStartHourChange={setStartHour}
            budgetHours={budgetHours}
            onBudgetHoursChange={setBudgetHours}
            pickedAreas={pickedAreas}
            mustVisit={mustVisit}
            loading={loading}
            onSubmit={handleSubmit}
          />
        </aside>

        <main className="min-w-0">
          {error && (
            <div className="rounded-inset border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
