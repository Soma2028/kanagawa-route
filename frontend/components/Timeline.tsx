import Image from "next/image";
import type { RouteResponse } from "@/lib/types";
import { areaColor, areaIcon, stars } from "@/lib/areaStyles";

export default function Timeline({ route }: { route: RouteResponse }) {
  const { stops, segments } = route;

  return (
    <div>
      <h2 className="mb-3 text-lg font-bold text-[#2c2c2c]">行程</h2>
      {stops.map((stop, order) => {
        const color = areaColor(stop.area);
        const segment = segments[order]; // stops[order] → stops[order+1] の区間

        return (
          <div key={stop.name + order}>
            {order === 0 ? (
              <div
                className="mb-3 rounded-[10px] border border-[#e0d9cc] bg-white p-3.5 shadow-sm"
                style={{ borderLeft: `4px solid ${color}` }}
              >
                <div className="flex items-baseline gap-2.5">
                  <span
                    className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full text-[0.85rem] font-bold text-white"
                    style={{ background: color }}
                  >
                    S
                  </span>
                  <span className="text-[1.15rem] font-bold text-[#2c2c2c]">
                    {stop.name}
                  </span>
                  <span className="ml-auto text-[0.9rem] text-[#8a8a8a]">
                    {stop.arrival_clock} 出発
                  </span>
                </div>
              </div>
            ) : (
              <div
                className="mb-3 rounded-[10px] border border-[#e0d9cc] bg-white p-3.5 shadow-sm"
                style={{ borderLeft: `4px solid ${color}` }}
              >
                <div className="flex items-baseline gap-2.5">
                  <span
                    className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full text-[0.85rem] font-bold text-white"
                    style={{ background: color }}
                  >
                    {order}
                  </span>
                  <span className="text-[1.15rem] font-bold text-[#2c2c2c]">
                    {areaIcon(stop.area)} {stop.name}
                  </span>
                  <span className="ml-auto text-[0.9rem] text-[#8a8a8a]">
                    {stop.arrival_clock}
                  </span>
                </div>

                <div
                  className="mt-2 text-[0.9rem]"
                  style={{ color, letterSpacing: "1px" }}
                >
                  {stars(stop.score)}{" "}
                  <span className="text-[0.8rem] text-[#8a8a8a]">
                    スコア {stop.score}
                  </span>
                </div>

                <div className="mt-2">
                  <span
                    className="mr-1.5 mb-1 inline-block rounded-full px-2.5 py-0.5 text-[0.78rem] text-white"
                    style={{ background: color }}
                  >
                    {stop.area}
                  </span>
                  <span className="mr-1.5 mb-1 inline-block rounded-full border border-[#e0d9cc] bg-[#f2ede3] px-2.5 py-0.5 text-[0.78rem] text-[#4a4a4a]">
                    滞在 {stop.stay_min}分
                  </span>
                  <span className="mr-1.5 mb-1 inline-block rounded-full border border-[#e0d9cc] bg-[#f2ede3] px-2.5 py-0.5 text-[0.78rem] text-[#4a4a4a]">
                    {stop.fee ? `¥${stop.fee}` : "無料"}
                  </span>
                </div>

                {stop.photo_url && (
                  <div className="mt-2.5">
                    <Image
                      src={stop.photo_url}
                      alt={stop.name}
                      width={400}
                      height={160}
                      unoptimized
                      className="h-40 w-full rounded-lg object-cover"
                    />
                    <div className="mt-0.5 overflow-hidden text-ellipsis whitespace-nowrap text-[0.68rem] text-[#a0a0a0]">
                      {stop.photo_artist} / {stop.photo_license}
                    </div>
                  </div>
                )}

                {stop.description && (
                  <div className="mt-2.5 text-[0.85rem] leading-relaxed text-[#5a5a5a]">
                    {stop.description}
                  </div>
                )}
              </div>
            )}

            {segment && (
              <div className="-mt-1.5 mb-2 ml-3.5 text-[0.82rem] text-[#8a8a8a]">
                ↓{" "}
                {segment.mode === "鉄道"
                  ? `🚃 ${segment.detail} ${segment.minutes}分`
                  : `🚶 徒歩 ${segment.minutes}分`}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
