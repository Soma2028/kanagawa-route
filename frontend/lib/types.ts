// backend/schemas.py と対応する型定義

export interface RouteRequest {
  start_hour: number;
  budget_hours: number;
  areas: string[];
  search_sec: number;
  max_wait: number;
}

export interface Stop {
  order: number;
  name: string;
  area: string;
  type: "start" | "meal" | "spot";
  lat: number;
  lon: number;
  arrival_clock: string;
  arrival_min: number;
  stay_min: number;
  fee: number;
  score: number;
  description: string;
  photo_url: string | null;
  photo_artist: string | null;
  photo_license: string | null;
  photo_license_url: string | null;
}

export interface Segment {
  from_index: number;
  to_index: number;
  mode: "徒歩" | "鉄道";
  detail: string | null;
  minutes: number;
  geometry: [number, number][] | null; // [lat, lon] の経由点。無ければ直線で描画
}

export interface Summary {
  total_score: number;
  visited_count: number;
  total_fee: number;
  stay_total_min: number;
  lunch_min: number;
  move_total_min: number;
  end_min: number;
  end_clock: string;
}

export interface ExcludedSpot {
  name: string;
  area: string;
  score: number;
  status: "closed" | "over_budget" | "fits";
  extra_minutes: number;
  earliest_arrival: string | null;
  closes_at: string | null;
  shortfall_minutes: number | null;
}

export interface BreakdownItem {
  type: "wait_time" | "rail_usage" | "move_ratio" | "score_rate";
  message: string;
}

export interface RouteResponse {
  stops: Stop[];
  segments: Segment[];
  summary: Summary;
  excluded: ExcludedSpot[];
  excluded_note: string;
  breakdown: BreakdownItem[];
  lunch_note: string | null;
}

export interface AreasResponse {
  areas: string[];
}
