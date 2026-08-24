"use client";

import { useSyncExternalStore } from "react";
import type { RouteRequest, RouteResponse } from "@/lib/types";
import { areaColor } from "@/lib/areaStyles";
import { useCountUp } from "@/lib/useCountUp";

interface Props {
  route: RouteResponse | null;
  request: RouteRequest | null;
}

function formatToday(): string {
  return new Date().toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "short",
  });
}

function subscribeNoop() {
  return () => {};
}

/**
 * 静的プリレンダー時にビルド日が固定表示されるのを避けるため、クライアントでの
 * 描画時にのみ日付を返す（サーバー/初回描画は null、以降は formatToday()）。
 */
function useToday(): string | null {
  return useSyncExternalStore(subscribeNoop, formatToday, () => null);
}

function HeroStat({
  label,
  target,
  format,
  sub,
}: {
  label: string;
  target: number;
  format: (value: number) => string;
  sub?: string;
}) {
  const value = useCountUp(target);
  return (
    <div className="rounded-xl bg-black/20 px-4 py-2.5">
      <div className="text-xs text-white/90">{label}</div>
      <div className="text-2xl font-bold text-white">{format(value)}</div>
      {sub && <div className="mt-0.5 text-xs text-white/90">{sub}</div>}
    </div>
  );
}

function Chip({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <span
      className="rounded-full px-3 py-1 text-xs font-medium text-white"
      style={{ background: color ?? "rgba(255,255,255,0.18)" }}
    >
      {children}
    </span>
  );
}

export default function Hero({ route, request }: Props) {
  const today = useToday();
  const startClock = route?.stops[0]?.arrival_clock;
  const endClock = route?.summary.end_clock;

  return (
    <section className="rounded-2xl bg-[#3d7a6f] px-5 py-4 sm:px-8 sm:py-5">
      <h1 className="text-xl font-bold text-white sm:text-2xl">
        ⛩️ 鎌倉 周遊ルート最適化
      </h1>
      <p className="mt-0.5 text-xs text-white/80 sm:text-sm">
        持ち時間と好みに合わせて、満足度が最大になる順路を提案します
      </p>

      {today && (
        <p className="mt-2 text-xs text-white/90 sm:text-sm">
          {today}
          {startClock && endClock ? ` ・ 出発 ${startClock} → 帰着 ${endClock}` : ""}
        </p>
      )}

      {route && (
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
          <HeroStat
            label="満足度スコア"
            target={route.summary.total_score}
            format={(v) => `${Math.round(v)}`}
            sub={`訪問 ${route.summary.visited_count}件`}
          />
          <HeroStat
            label="所要時間"
            target={route.summary.end_min / 60}
            format={(v) => `${v.toFixed(1)}時間`}
            sub={`移動 ${route.summary.move_total_min}分 / 滞在 ${route.summary.stay_total_min}分`}
          />
          <HeroStat
            label="拝観料合計"
            target={route.summary.total_fee}
            format={(v) => `¥${Math.round(v).toLocaleString()}`}
          />
        </div>
      )}

      {request && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Chip>出発 {request.start_hour.toFixed(1)}時</Chip>
          <Chip>持ち時間 {request.budget_hours.toFixed(1)}時間</Chip>
          {request.areas.length > 0 ? (
            request.areas.map((a) => (
              <Chip key={a} color={areaColor(a)}>
                {a}
              </Chip>
            ))
          ) : (
            <Chip>エリア: 全域</Chip>
          )}
        </div>
      )}
    </section>
  );
}
