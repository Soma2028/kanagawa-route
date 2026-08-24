"""スポット間の徒歩経路のジオメトリ（道なりの座標列）を ORS Directions API から取得する

travel_time.build_matrix() が実際に「徒歩」を採用しているペアだけを対象にする
（561ペア中362ペア、鉄道の199ペアは対象外）。ORS無料枠は40req/分・2500req/日
なので、362回の呼び出しは間隔を空けても十分収まる。

キーはスポット名をソートした順の "名前A|名前B" にする（順序に依存しない）。
逆方向で使う場合は、呼び出し側（backend/service.py の _walk_geometry）で
点列を反転する。
"""
import json
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

from travel_time import build_matrix

load_dotenv()
API_KEY = os.getenv("ORS_API_KEY")

URL = "https://api.openrouteservice.org/v2/directions/foot-walking/geojson"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}


def fetch_geometry(lon1, lat1, lon2, lat2, max_retry=5):
    """2点間の道なり経路を [(lat, lon), ...] で返す"""
    body = {"coordinates": [[lon1, lat1], [lon2, lat2]]}
    wait = 3.0
    for _ in range(max_retry):
        res = requests.post(URL, json=body, headers=HEADERS, timeout=30)
        if res.status_code == 429:
            print(f"    制限中… {wait:.0f}秒待機")
            time.sleep(wait)
            wait *= 2
            continue
        res.raise_for_status()
        coords = res.json()["features"][0]["geometry"]["coordinates"]
        return [[lat, lon] for lon, lat in coords]  # ORSは[lon,lat]で返すため入れ替える
    raise RuntimeError("再試行の上限に達しました")


def walk_pairs(df):
    """travel_matrix上で実際に「徒歩」が採用されているペア（i<j）を列挙する"""
    _, modes = build_matrix(df)
    n = len(df)
    return [
        (i, j) for i in range(n) for j in range(i + 1, n)
        if not modes[i, j].startswith("鉄道")
    ]


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("ORS_API_KEY が読めません。.env を確認してください")

    df = pd.read_csv("spots_master.csv")
    pairs = walk_pairs(df)
    print(f"徒歩経路を取得します: {len(pairs)}ペア")

    geometry = {}
    failed = []
    for k, (i, j) in enumerate(pairs, 1):
        a, b = df.iloc[i], df.iloc[j]
        name_lo, name_hi = sorted([a["name"], b["name"]])
        row_lo = a if a["name"] == name_lo else b
        row_hi = b if row_lo is a else a
        key = f"{name_lo}|{name_hi}"

        try:
            geometry[key] = fetch_geometry(
                row_lo["lon"], row_lo["lat"], row_hi["lon"], row_hi["lat"],
            )
        except Exception as e:
            print(f"  失敗: {name_lo} - {name_hi} ({e})")
            failed.append(key)

        if k % 20 == 0:
            print(f"  {k}/{len(pairs)} 完了")
        time.sleep(1.5)  # 40req/分の枠に余裕を持たせる

    with open("walk_geometry.json", "w", encoding="utf-8") as f:
        json.dump(geometry, f, ensure_ascii=False)

    size_kb = os.path.getsize("walk_geometry.json") / 1024
    print(f"\n保存しました: walk_geometry.json（{len(geometry)}/{len(pairs)}件、{size_kb:.0f}KB）")
    if failed:
        print(f"失敗した{len(failed)}件: {failed}")
