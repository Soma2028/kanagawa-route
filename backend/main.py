"""FastAPI アプリ本体。optimize.py / travel_time.py は無改造で import する。

optimize.load_data() は spots_master.csv 等をカレントディレクトリ相対で読むため、
uvicorn がどのディレクトリから起動されても動くよう、import前にリポジトリ直下へ
sys.path を通し、カレントディレクトリもリポジトリ直下に固定する。
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if Path.cwd() != REPO_ROOT:
    os.chdir(REPO_ROOT)

import json

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from optimize import load_data

from .schemas import AreasResponse, RouteRequest, RouteResponse
from .service import build_route_response

STATE: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # スポット・移動時間行列は起動時に1回だけ読み込む（solve() のたびに読み直さない）
    df, travel, modes = load_data()
    try:
        photos_df = pd.read_csv("photos_selected.csv")
        photos = {
            row["name"]: {
                k: (None if pd.isna(v) else v) for k, v in row.items()
            }
            for row in photos_df.to_dict("records")
        }
    except FileNotFoundError:
        photos = {}
    try:
        with open("walk_geometry.json", encoding="utf-8") as f:
            walk_geometry = json.load(f)
    except FileNotFoundError:
        walk_geometry = {}
    STATE.update(df=df, travel=travel, modes=modes, photos=photos, walk_geometry=walk_geometry)
    yield
    STATE.clear()


app = FastAPI(title="kanagawa-route API", lifespan=lifespan)

# ローカル開発 (localhost:3000) と、Vercelにデプロイした本番/プレビュー環境
# (*.vercel.app) からのアクセスを許可する。認証・Cookieを使わない公開APIのため
# 個別ドメインを都度登録する必要がなく、プレビューデプロイのURLもこれで自動的に通る。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/areas", response_model=AreasResponse)
def get_areas() -> AreasResponse:
    df = STATE["df"]
    # 起点・昼食は選択可能な「行きたいエリア」ではないため除く
    areas = sorted(df[~df["area"].isin(["起点", "昼食"])]["area"].unique().tolist())
    return AreasResponse(areas=areas)


@app.post("/api/route", response_model=RouteResponse)
def post_route(req: RouteRequest) -> RouteResponse:
    result = build_route_response(
        STATE["df"], STATE["travel"], STATE["modes"], STATE["photos"], STATE["walk_geometry"], req,
    )
    if result is None:
        raise HTTPException(status_code=422, detail="条件に合うルートが見つかりませんでした")
    return result
