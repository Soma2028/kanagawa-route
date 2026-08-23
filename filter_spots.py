"""観光スポット候補を機械的に絞り込む"""
import pandas as pd

df = pd.read_csv("spots_kamakura.csv")

# 除外: 記念碑・道端の小祠など、目的地にならないもの
EXCLUDE_HISTORIC = ["memorial", "wayside_shrine", "tomb", "tree", "stone", "water_well"]
df = df[~df["historic"].isin(EXCLUDE_HISTORIC)]

# 飲食は別枠で扱うので、ここでは観光スポットだけ残す
sightseeing = df[
    df["tourism"].notna()
    | df["historic"].notna()
    | (df["amenity"] == "place_of_worship")
]

print("観光スポット候補:", len(sightseeing))
sightseeing[["name", "tourism", "historic", "amenity", "opening_hours"]].to_csv(
    "candidates.csv", index=False
)

# 全件を名前だけ一覧表示
for i, name in enumerate(sightseeing["name"], 1):
    print(i, name)