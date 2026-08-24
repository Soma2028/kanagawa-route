import type { AreasResponse, RouteRequest, RouteResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {}

export async function fetchAreas(): Promise<string[]> {
  const res = await fetch(`${API_BASE_URL}/api/areas`);
  if (!res.ok) throw new ApiError("エリア一覧の取得に失敗しました");
  const body = (await res.json()) as AreasResponse;
  return body.areas;
}

export async function fetchRoute(req: RouteRequest): Promise<RouteResponse> {
  const res = await fetch(`${API_BASE_URL}/api/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (res.status === 422) {
    throw new ApiError("条件に合うルートが見つかりませんでした。持ち時間を延ばしてみてください。");
  }
  if (!res.ok) throw new ApiError("ルートの計算に失敗しました");
  return (await res.json()) as RouteResponse;
}
