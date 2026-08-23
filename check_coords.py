"""取得した座標が鎌倉の範囲内にあるか検証する"""
import pandas as pd

df = pd.read_csv("spots_master.csv")

# 鎌倉市のおおよその範囲
LAT_MIN, LAT_MAX = 35.28, 35.36
LON_MIN, LON_MAX = 139.48, 139.58

outside = df[
    (df["lat"] < LAT_MIN) | (df["lat"] > LAT_MAX)
    | (df["lon"] < LON_MIN) | (df["lon"] > LON_MAX)
]

print("欠損:", df["lat"].isna().sum(), "件")
print("範囲外のスポット:")
print(outside[["name", "lat", "lon"]] if len(outside) else "なし")