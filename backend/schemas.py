"""FastAPI のリクエスト/レスポンススキーマ"""
from typing import Literal

from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    start_hour: float = Field(9.0, ge=7.0, le=12.0, description="出発時刻")
    budget_hours: float = Field(6.0, ge=3.0, le=10.0, description="持ち時間")
    areas: list[str] = Field(default_factory=list, description="行きたいエリア（空なら全域、スコアの重み付けにのみ使う）")
    must_visit: list[str] = Field(default_factory=list, description="必ず訪問するスポット名（空なら制約なし）")
    search_sec: int = Field(5, ge=1, le=60, description="計算時間（秒）")
    max_wait: int = Field(60, ge=0, le=90, description="開門待ちの許容（分）")


class Stop(BaseModel):
    order: int
    name: str
    area: str
    type: Literal["start", "meal", "spot"]
    lat: float
    lon: float
    arrival_clock: str
    arrival_min: int
    stay_min: int
    fee: int
    score: int
    description: str
    photo_url: str | None = None
    photo_artist: str | None = None
    photo_license: str | None = None
    photo_license_url: str | None = None


class Segment(BaseModel):
    """result[from_index] → result[to_index] の移動区間"""
    from_index: int
    to_index: int
    mode: str          # "徒歩" | "鉄道"
    detail: str | None  # 鉄道の場合の表示用ラベル。乗換があれば "始発駅→鎌倉(乗換)→終着駅"
    minutes: int
    geometry: list[tuple[float, float]] | None = None  # [(lat,lon), ...] 経路の経由点。無ければ直線で描画


class Summary(BaseModel):
    total_score: int
    visited_count: int
    total_fee: int
    stay_total_min: int
    lunch_min: int
    move_total_min: int
    end_min: int
    end_clock: str


class ExcludedSpot(BaseModel):
    """訪問しなかったスポット。数値はすべて「今回のルートにそのまま追加した場合」の試算で、
    他スポットとの入れ替えは考慮していない（= 不採用の理由の証明ではない）。"""
    name: str
    area: str
    score: int
    status: Literal["closed", "over_budget", "fits"]
    extra_minutes: int
    earliest_arrival: str | None = None   # status="closed" の場合のみ
    closes_at: str | None = None          # status="closed" の場合のみ
    shortfall_minutes: int | None = None  # status="over_budget" の場合のみ


class BreakdownItem(BaseModel):
    """このルートの内訳を示す事実ベースの1項目（評価語や因果の主張は含まない）"""
    type: Literal["wait_time", "rail_usage", "move_ratio", "score_rate"]
    message: str


class RouteResponse(BaseModel):
    stops: list[Stop]
    segments: list[Segment]
    summary: Summary
    excluded: list[ExcludedSpot]
    excluded_note: str
    breakdown: list[BreakdownItem]
    lunch_note: str | None  # 正午をまたぐのに昼食を組み込めなかった場合の注記


class AreasResponse(BaseModel):
    areas: list[str]


class SpotSummary(BaseModel):
    """「行きたい場所」選択UI用の最小限のスポット情報"""
    name: str
    area: str
    photo_url: str | None = None


class SpotsResponse(BaseModel):
    spots: list[SpotSummary]
