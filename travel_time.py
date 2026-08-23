"""スポット間の移動時間行列を作る（徒歩＋鉄道の併用を考慮）"""
import numpy as np
import pandas as pd

WALK_SPEED_KMH = 4.0
DETOUR_RATIO = 1.4
WAIT_MIN = 6.0          # 江ノ電・横須賀線の平均待ち時間

# 主要駅の座標
STATIONS = {
    "北鎌倉": (35.3365, 139.5470),
    "鎌倉": (35.3192, 139.5500),
    "和田塚": (35.3155, 139.5470),
    "由比ヶ浜": (35.3126, 139.5432),
    "長谷": (35.3141, 139.5344),
    "極楽寺": (35.3095, 139.5301),
    "稲村ヶ崎": (35.3050, 139.5245),
    "七里ヶ浜": (35.3055, 139.5136),
    "鎌倉高校前": (35.3067, 139.5007),
}

# 鎌倉駅を基準とした各駅までの乗車時間（分）
RAIL_FROM_KAMAKURA = {
    "北鎌倉": 4, "鎌倉": 0, "和田塚": 2, "由比ヶ浜": 3, "長谷": 5,
    "極楽寺": 8, "稲村ヶ崎": 10, "七里ヶ浜": 13, "鎌倉高校前": 16,
}


def haversine(lat1, lon1, lat2, lon2):
    """2地点間の大円距離をkmで返す"""
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def walk_min(lat1, lon1, lat2, lon2):
    """2地点間の徒歩所要時間（分）"""
    km = haversine(lat1, lon1, lat2, lon2)
    return km * DETOUR_RATIO / WALK_SPEED_KMH * 60


def nearest_station(lat, lon):
    """最寄り駅とそこまでの徒歩時間を返す"""
    best, best_min = None, float("inf")
    for st, (slat, slon) in STATIONS.items():
        m = walk_min(lat, lon, slat, slon)
        if m < best_min:
            best, best_min = st, m
    return best, best_min


def rail_min(st_a, st_b):
    """駅間の乗車時間（鎌倉駅基準の差分で近似）"""
    return abs(RAIL_FROM_KAMAKURA[st_a] - RAIL_FROM_KAMAKURA[st_b])


def build_matrix(df):
    """徒歩のみと鉄道利用を比較し、短いほうを採用した行列を返す"""
    n = len(df)
    minutes = np.zeros((n, n))
    modes = np.empty((n, n), dtype=object)

    stations = [nearest_station(r["lat"], r["lon"]) for _, r in df.iterrows()]

    for i in range(n):
        for j in range(n):
            if i == j:
                modes[i, j] = "-"
                continue

            a, b = df.iloc[i], df.iloc[j]
            only_walk = walk_min(a["lat"], a["lon"], b["lat"], b["lon"])

            st_a, to_a = stations[i]
            st_b, to_b = stations[j]
            if st_a == st_b:
                via_rail = float("inf")   # 同じ駅なら乗る意味がない
            else:
                via_rail = to_a + WAIT_MIN + rail_min(st_a, st_b) + to_b

            if via_rail < only_walk:
                minutes[i, j] = via_rail
                modes[i, j] = f"鉄道({st_a}→{st_b})"
            else:
                minutes[i, j] = only_walk
                modes[i, j] = "徒歩"

    return minutes, modes


if __name__ == "__main__":
    df = pd.read_csv("spots_master.csv")
    matrix, modes = build_matrix(df)

    pd.DataFrame(matrix, index=df["name"], columns=df["name"]).to_csv(
        "travel_matrix.csv"
    )

    rail_count = (modes == "-").sum()
    print(f"{len(df)}×{len(df)} の行列を作成しました")
    print(f"平均移動時間: {matrix[matrix > 0].mean():.1f}分")
    print(f"最長: {matrix.max():.1f}分")
    print()

    print("--- 検算1：鶴岡八幡宮からの移動時間 ---")
    idx = df[df["name"] == "鶴岡八幡宮"].index[0]
    s = pd.Series(matrix[idx], index=df["name"]).sort_values()
    print(s.head(6).round(1))
    print()

    print("--- 検算2：鎌倉高校前駅 → 瑞泉寺 ---")
    i = df[df["name"] == "鎌倉高校前駅"].index[0]
    j = df[df["name"] == "瑞泉寺"].index[0]
    print(f"{matrix[i, j]:.1f}分 / 手段: {modes[i, j]}")