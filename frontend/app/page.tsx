"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import Hero from "@/components/Hero";
import SearchForm from "@/components/SearchForm";
import Timeline from "@/components/Timeline";
import { ApiError, fetchAreas, fetchRoute } from "@/lib/api";
import type { RouteRequest, RouteResponse } from "@/lib/types";

// Leaflet は window/document に依存するためサーバーではレンダリングしない
const RouteMap = dynamic(() => import("@/components/RouteMap"), { ssr: false });

export default function Home() {
  const [areas, setAreas] = useState<string[]>([]);
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [lastRequest, setLastRequest] = useState<RouteRequest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAreas()
      .then(setAreas)
      .catch(() => setError("エリア一覧の取得に失敗しました。バックエンドが起動しているか確認してください。"));
  }, []);

  async function handleSubmit(req: RouteRequest) {
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

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <Hero route={route} request={lastRequest} />

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
        <aside>
          <SearchForm areas={areas} loading={loading} onSubmit={handleSubmit} />
        </aside>

        <main>
          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {!route && !error && (
            <div className="rounded-lg border border-[#e0d9cc] bg-[#f2ede3] p-4 text-sm text-[#4a4a4a]">
              左のサイドバーで条件を設定して「ルートを計算」を押してください
            </div>
          )}

          {loading && (
            <div className="mb-4 text-sm text-[#6b6b6b]">最適なルートを探しています...</div>
          )}

          {route && (
            <div className="flex flex-col gap-6">
              <Timeline route={route} />
              <RouteMap route={route} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
