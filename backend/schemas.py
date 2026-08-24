"""FastAPI のリクエスト/レスポンススキーマ"""
from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    start_hour: float = Field(9.0, ge=7.0, le=12.0, description="出発時刻")
    budget_hours: float = Field(6.0, ge=3.0, le=10.0, description="持ち時間")
    areas: list[str] = Field(default_factory=list, description="行きたいエリア（空なら全域）")
    search_sec: int = Field(5, ge=1, le=60, description="計算時間（秒）")
    max_wait: int = Field(60, ge=0, le=90, description="開門待ちの許容（分）")


class Stop(BaseModel):
    order: int
    name: str
    area: str
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
    detail: str | None  # 鉄道の場合の "始発駅→終着駅"
    minutes: int


class Summary(BaseModel):
    total_score: int
    visited_count: int
    total_fee: int
    stay_total_min: int
    move_total_min: int
    end_min: int
    end_clock: str


class RouteResponse(BaseModel):
    stops: list[Stop]
    segments: list[Segment]
    summary: Summary


class AreasResponse(BaseModel):
    areas: list[str]
