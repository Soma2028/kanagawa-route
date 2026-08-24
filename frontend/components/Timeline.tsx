import Image from "next/image";
import type { Segment, RouteResponse } from "@/lib/types";
import { areaColor, areaIcon, stars } from "@/lib/areaStyles";

function Connector({ segment }: { segment: Segment }) {
  return (
    <div className="flex w-14 shrink-0 flex-col items-center justify-center gap-1 self-center text-center text-[0.72rem] text-[#8a8a8a]">
      <span className="text-base leading-none">{segment.mode === "鉄道" ? "🚃" : "🚶"}</span>
      <span>{segment.minutes}分</span>
    </div>
  );
}

export default function Timeline({ route }: { route: RouteResponse }) {
  const { stops, segments } = route;

  return (
    <div className="relative">
      <h2 className="mb-3 text-lg font-bold text-[#2c2c2c]">行程</h2>
      <div className="flex items-stretch gap-2 overflow-x-auto pb-3">
        {stops.map((stop, order) => {
          const color = areaColor(stop.area);
          const segment = segments[order]; // stops[order] → stops[order+1] の区間

          return (
            <div key={stop.name + order} className="flex shrink-0 items-stretch gap-2">
              <div
                className={
                  stop.type === "spot"
                    ? "w-56 shrink-0 rounded-[10px] border border-[#e0d9cc] bg-white p-3 shadow-sm"
                    : "w-32 shrink-0 self-start rounded-[10px] border border-[#e0d9cc] bg-white p-3 shadow-sm"
                }
                style={{
                  borderTop: `4px solid ${color}`,
                  animation: "card-fade-in 0.35s ease-out both",
                  animationDelay: `${order * 40}ms`,
                }}
              >
                {stop.type === "start" ? (
                  <>
                    <span
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[0.8rem] font-bold text-white"
                      style={{ background: color }}
                    >
                      S
                    </span>
                    <div className="mt-1.5 text-[0.9rem] font-bold text-[#2c2c2c]">{stop.name}</div>
                    <div className="mt-0.5 text-[0.75rem] text-[#8a8a8a]">{stop.arrival_clock} 出発</div>
                  </>
                ) : stop.type === "meal" ? (
                  <>
                    <span
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[0.9rem]"
                      style={{ background: color }}
                    >
                      {areaIcon(stop.area)}
                    </span>
                    <div className="mt-1.5 text-[0.9rem] font-bold text-[#2c2c2c]">昼食休憩</div>
                    <div className="mt-0.5 text-[0.75rem] text-[#8a8a8a]">
                      {stop.arrival_clock}〜{stop.stay_min}分
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      <span
                        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[0.8rem] font-bold text-white"
                        style={{ background: color }}
                      >
                        {order}
                      </span>
                      <span className="text-[0.95rem] font-bold text-[#2c2c2c]">
                        {areaIcon(stop.area)} {stop.name}
                      </span>
                    </div>
                    <div className="mt-1 text-[0.8rem] text-[#8a8a8a]">{stop.arrival_clock}</div>

                    <div className="mt-1.5 text-[0.85rem]" style={{ color, letterSpacing: "1px" }}>
                      {stars(stop.score)}{" "}
                      <span className="text-[0.72rem] text-[#8a8a8a]">スコア{stop.score}</span>
                    </div>

                    <div className="mt-1.5 flex flex-wrap gap-1">
                      <span
                        className="rounded-full px-2 py-0.5 text-[0.7rem] text-white"
                        style={{ background: color }}
                      >
                        {stop.area}
                      </span>
                      <span className="rounded-full border border-[#e0d9cc] bg-[#f2ede3] px-2 py-0.5 text-[0.7rem] text-[#4a4a4a]">
                        滞在{stop.stay_min}分
                      </span>
                      <span className="rounded-full border border-[#e0d9cc] bg-[#f2ede3] px-2 py-0.5 text-[0.7rem] text-[#4a4a4a]">
                        {stop.fee ? `¥${stop.fee}` : "無料"}
                      </span>
                    </div>

                    {stop.photo_url && (
                      <div className="mt-2">
                        <Image
                          src={stop.photo_url}
                          alt={stop.name}
                          width={300}
                          height={110}
                          unoptimized
                          className="h-24 w-full rounded-lg object-cover"
                        />
                        <div className="mt-0.5 truncate text-[0.62rem] text-[#a0a0a0]">
                          {stop.photo_artist} / {stop.photo_license}
                        </div>
                      </div>
                    )}

                    {stop.description && (
                      <div className="mt-2 line-clamp-3 text-[0.75rem] leading-snug text-[#5a5a5a]">
                        {stop.description}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* 0分の区間（丸め誤差等で稀に発生）は表示しても意味がないため出さない */}
              {segment && segment.minutes > 0 && <Connector segment={segment} />}
            </div>
          );
        })}
      </div>

      {/* 右端に続きがあることを示すグラデーション（横スクロール可能なことのヒント） */}
      <div className="pointer-events-none absolute top-9 right-0 bottom-3 w-10 bg-gradient-to-l from-[#faf7f0] to-transparent" />
    </div>
  );
}
