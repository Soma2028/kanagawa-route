"""スポット間の移動時間行列を作る（ORS徒歩実測 ＋ 鉄道の併用を考慮）

鉄道は江ノ電（鎌倉～藤沢方面）と横須賀線（北鎌倉～鎌倉）という別々の路線が
鎌倉駅で接続する構造になっている。当初は全9駅を「鎌倉駅からの一直線」として
扱っていたため、北鎌倉（横須賀線）↔江ノ電各駅の区間が乗り換えなしの直接区間
のように計算されてしまっていた（詳細はREADME「鉄道モデルの是正」を参照）。
"""
import numpy as np
import pandas as pd

WALK_SPEED_KMH = 4.0    # 近似計算用（駅までの徒歩などに使う）
DETOUR_RATIO = 1.4      # 同上
TRANSFER_MIN = 5        # 鎌倉駅での乗り換え時間（ホーム移動＋2本目の待ち時間を含む想定値）

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

# 各駅の路線。鎌倉駅は両路線が発着する共通駅として扱う
STATION_LINES = {
    "北鎌倉": "横須賀線",
    "鎌倉": "共通",
    "和田塚": "江ノ電",
    "由比ヶ浜": "江ノ電",
    "長谷": "江ノ電",
    "極楽寺": "江ノ電",
    "稲村ヶ崎": "江ノ電",
    "七里ヶ浜": "江ノ電",
    "鎌倉高校前": "江ノ電",
}

# 運行間隔（分）。江ノ電は実測に近い値だが、横須賀線は正確な間隔のデータが
# 手元になく「江ノ電よりやや疎」という前提で置いた推定値。
LINE_HEADWAY_MIN = {
    "江ノ電": 12,
    "横須賀線": 15,  # 推定値
}

# 鎌倉駅を基準とした各駅までの乗車時間（分）。同一路線内、または片方が鎌倉駅
# そのものであれば、この値の差分がそのまま区間の乗車時間になる。
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
    """2地点間の徒歩所要時間（分）を直線距離から近似する

    スポット間は ORS の実測値を使うが、駅までの徒歩など
    実測行列に含まれない区間ではこの近似を用いる。
    """
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


def _boarding_line(boarding_station, other_station):
    """乗車駅の実際の路線を返す（鎌倉駅は両路線発着のため、行き先の路線に合わせる）"""
    line = STATION_LINES[boarding_station]
    return STATION_LINES[other_station] if line == "共通" else line


def wait_min(boarding_station, other_station):
    """乗車駅で待つ平均時間（乗車する路線の運行間隔の半分）"""
    return LINE_HEADWAY_MIN[_boarding_line(boarding_station, other_station)] / 2


def _needs_transfer(st_a, st_b):
    """異なる路線同士で、どちらも鎌倉駅ではない区間か（＝鎌倉駅での乗り換えが要るか）"""
    same_line = STATION_LINES[st_a] == STATION_LINES[st_b]
    via_kamakura_endpoint = st_a == "鎌倉" or st_b == "鎌倉"
    return not (same_line or via_kamakura_endpoint)


def rail_min(st_a, st_b):
    """駅間の乗車時間。同一路線内（または片方が鎌倉駅）なら鎌倉駅基準の差分、
    路線が異なる場合は鎌倉駅での乗り換えを挟んだ合算にする"""
    if not _needs_transfer(st_a, st_b):
        return abs(RAIL_FROM_KAMAKURA[st_a] - RAIL_FROM_KAMAKURA[st_b])
    return RAIL_FROM_KAMAKURA[st_a] + TRANSFER_MIN + RAIL_FROM_KAMAKURA[st_b]


def rail_label(st_a, st_b):
    """鉄道区間の表示ラベル。乗り換えが要る区間は鎌倉駅を経由駅として明示する"""
    if _needs_transfer(st_a, st_b):
        return f"{st_a}→鎌倉(乗換)→{st_b}"
    return f"{st_a}→{st_b}"


def best_travel(only_walk, station_a, to_station_a, station_b, to_station_b):
    """徒歩(only_walk)と最寄駅経由の鉄道利用を比較し、(所要時間, 鉄道を使うか) を返す

    駅間の移動時間計算がこれまで3箇所（このファイルのbuild_matrix、
    optimize.load_data()の起点用・昼食用ループ）に重複していたため、
    ここに1本化した。乗車駅によって待ち時間（wait_min）が変わり得るため、
    A→BとB→Aは呼び分ける必要がある（対称とは限らない）。
    """
    if station_a == station_b:
        return only_walk, False
    via_rail = (
        to_station_a + wait_min(station_a, station_b)
        + rail_min(station_a, station_b) + to_station_b
    )
    if via_rail < only_walk:
        return via_rail, True
    return only_walk, False


def load_walk_matrix(df):
    """ORS で取得した徒歩実測行列を読み込む"""
    m = pd.read_csv("walk_matrix_ors.csv", index_col=0)
    # spots_master.csv と行順が一致していることを確認する
    if list(m.index) != list(df["name"]):
        raise ValueError(
            "walk_matrix_ors.csv とスポットの並びが一致しません。"
            "fetch_walk_matrix.py を再実行してください"
        )
    return m.values


def build_matrix(df):
    """徒歩実測と鉄道利用を比較し、短いほうを採用した行列を返す"""
    n = len(df)
    walk = load_walk_matrix(df)
    minutes = np.zeros((n, n))
    modes = np.empty((n, n), dtype=object)

    stations = [nearest_station(r["lat"], r["lon"]) for _, r in df.iterrows()]

    for i in range(n):
        for j in range(n):
            if i == j:
                modes[i, j] = "-"
                continue
            st_a, to_a = stations[i]
            st_b, to_b = stations[j]
            m, is_rail = best_travel(walk[i, j], st_a, to_a, st_b, to_b)
            minutes[i, j] = m
            modes[i, j] = f"鉄道:{rail_label(st_a, st_b)}" if is_rail else "徒歩"

    return minutes, modes


if __name__ == "__main__":
    df = pd.read_csv("spots_master.csv")
    matrix, modes = build_matrix(df)

    pd.DataFrame(matrix, index=df["name"], columns=df["name"]).to_csv(
        "travel_matrix.csv"
    )

    print(f"{len(df)}×{len(df)} の行列を作成しました（徒歩はORS実測）")
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
