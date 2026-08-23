"""主要スポットの緯度経度を Nominatim から取得してマスタCSVの雛形を作る"""
import time
import requests
import pandas as pd

# 手動で選定した鎌倉の主要スポット
SPOTS = [
    ("円覚寺", "北鎌倉"), ("明月院", "北鎌倉"), ("建長寺", "北鎌倉"),
    ("東慶寺", "北鎌倉"), ("浄智寺", "北鎌倉"),
    ("鶴岡八幡宮", "八幡宮"), ("小町通り", "八幡宮"),
    ("鎌倉国宝館", "八幡宮"), ("源頼朝の墓", "八幡宮"), ("宝戒寺", "八幡宮"),
    ("報国寺", "金沢街道"), ("杉本寺", "金沢街道"),
    ("浄妙寺", "金沢街道"), ("瑞泉寺", "金沢街道"),
    ("高徳院", "長谷"), ("長谷寺", "長谷"), ("御霊神社", "長谷"),
    ("鎌倉文学館", "長谷"), ("光則寺", "長谷"),
    ("極楽寺", "江ノ電"), ("成就院", "江ノ電"), ("稲村ヶ崎", "江ノ電"),
    ("七里ヶ浜", "江ノ電"), ("鎌倉高校前駅", "江ノ電"),
    ("銭洗弁財天宇賀福神社", "西鎌倉"), ("佐助稲荷神社", "西鎌倉"),
    ("寿福寺", "西鎌倉"), ("葛原岡神社", "西鎌倉"),
    ("妙本寺", "大町材木座"), ("安国論寺", "大町材木座"),
    ("光明寺", "大町材木座"), ("由比ヶ浜", "大町材木座"),
    ("荏柄天神社", "その他"), ("半僧坊", "その他"),
]

HEADERS = {"User-Agent": "kanagawa-route/0.1 (portfolio project)"}


def geocode(name):
    """スポット名から緯度経度を1件取得する"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": f"{name} 鎌倉", "format": "json", "limit": 1}
    res = requests.get(url, params=params, headers=HEADERS, timeout=30)
    res.raise_for_status()
    results = res.json()
    if not results:
        return None, None
    return float(results[0]["lat"]), float(results[0]["lon"])


if __name__ == "__main__":
    rows = []
    for name, area in SPOTS:
        lat, lon = geocode(name)
        status = "OK" if lat else "見つからず"
        print(f"{status}: {name}")
        rows.append({
            "name": name,
            "area": area,
            "lat": lat,
            "lon": lon,
            "stay_min": "",      # 想定滞在時間（手入力）
            "open_hour": "",     # 開門時刻（手入力）
            "close_hour": "",    # 閉門時刻（手入力）
            "fee": "",           # 拝観料（手入力）
        })
        time.sleep(1.1)  # Nominatim は秒1リクエストまで

    df = pd.DataFrame(rows)
    df.to_csv("spots_master.csv", index=False)
    print(f"\n保存しました: {len(df)}件（うち座標なし {df['lat'].isna().sum()}件）")