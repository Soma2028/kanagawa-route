"""鎌倉エリアの観光スポットを Overpass API から取得する"""
import requests
import pandas as pd

# 鎌倉駅周辺の矩形範囲（南緯, 西経, 北緯, 東経）
BBOX = "35.29,139.51,35.34,139.57"

QUERY = f"""
[out:json][timeout:60];
(
  node["tourism"~"attraction|museum|viewpoint"]({BBOX});
  node["historic"]({BBOX});
  node["amenity"~"place_of_worship|cafe|restaurant"]({BBOX});
  way["tourism"~"attraction|museum"]({BBOX});
  way["historic"]({BBOX});
);
out center tags;
"""

def fetch():
    """Overpass API を叩いて生データを取得する"""
    url = "https://overpass-api.de/api/interpreter"
    headers = {
        # 公共APIなので、誰からのリクエストか分かるように名乗る
        "User-Agent": "kanagawa-route/0.1 (portfolio project; oobasouma0411@gmail.com)"
    }
    res = requests.post(url, data={"data": QUERY}, headers=headers, timeout=90)
    res.raise_for_status()
    return res.json()["elements"]

def to_dataframe(elements):
    """必要な属性だけ抜き出して DataFrame にする"""
    rows = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:          # 名前のない地点は使えないので除外
            continue
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        rows.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "tourism": tags.get("tourism"),
            "historic": tags.get("historic"),
            "amenity": tags.get("amenity"),
            "religion": tags.get("religion"),
            "opening_hours": tags.get("opening_hours"),
            "fee": tags.get("fee"),
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    elements = fetch()
    df = to_dataframe(elements)
    df.to_csv("spots_kamakura.csv", index=False)
    print(f"取得件数: {len(df)}")
    print(df.head(20))