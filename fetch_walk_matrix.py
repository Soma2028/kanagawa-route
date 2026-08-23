"""OpenRouteService で徒歩の実測所要時間行列を取得する"""
import json
import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ORS_API_KEY")

URL = "https://api.openrouteservice.org/v2/matrix/foot-walking"


def fetch_matrix(df):
    """全スポット間の徒歩所要時間（秒）を1リクエストで取得する"""
    # ORS は [経度, 緯度] の順で受け取る
    locations = [[float(r["lon"]), float(r["lat"])] for _, r in df.iterrows()]

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }
    body = {"locations": locations, "metrics": ["duration"]}

    res = requests.post(URL, json=body, headers=headers, timeout=60)
    res.raise_for_status()
    return res.json()["durations"]


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("ORS_API_KEY が読めません。.env を確認してください")

    df = pd.read_csv("spots_master.csv")
    print(f"{len(df)}地点の徒歩所要時間を取得します...")

    durations = fetch_matrix(df)

    # 秒 → 分に変換して保存する
    minutes = [[round(v / 60, 1) if v is not None else None for v in row]
               for row in durations]
    out = pd.DataFrame(minutes, index=df["name"], columns=df["name"])
    out.to_csv("walk_matrix_ors.csv")

    print("保存しました: walk_matrix_ors.csv")
    print()
    print("--- 検算：鶴岡八幡宮からの徒歩時間 ---")
    s = out.loc["鶴岡八幡宮"].sort_values()
    print(s.head(8))