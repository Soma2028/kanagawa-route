"""制限時間内で満足度が最大になる周遊ルートを求める（OR-Tools Routing版）"""
import numpy as np
import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

START_NAME = "鎌倉駅"
START_LAT, START_LON = 35.3192, 139.5500

LUNCH_NAME = "昼食"
LUNCH_STAY_MIN = 60
LUNCH_OPEN_HOUR = 11.0
LUNCH_CLOSE_HOUR = 14.0
# 実スポット1件分の最大ペナルティ（スコア10×penalty_scale100=1000）より
# 十分大きくし、正午をまたぐ行程では時間が許す限り優先して組み込まれるようにする
LUNCH_PENALTY = 5000

START_HOUR = 9.0        # 出発時刻
BUDGET_MIN = 360        # 持ち時間（分）
SEARCH_SEC = 15         # 探索時間


def crosses_lunch(start_hour, budget_min):
    """観光時間帯が正午をまたぐかどうか（またがないなら昼食休憩は不要）"""
    end_hour = start_hour + budget_min / 60
    return start_hour < 12.0 < end_hour


def load_data():
    """スポット、移動時間行列、移動手段を読み込み、起点と昼食休憩を追加する"""
    df = pd.read_csv("spots_master.csv")
    matrix = pd.read_csv("travel_matrix.csv", index_col=0).values

    start = pd.DataFrame([{
        "name": START_NAME, "area": "起点",
        "lat": START_LAT, "lon": START_LON,
        "stay_min": 0, "open_hour": 0, "close_hour": 24, "fee": 0, "score": 0, "description": "",
    }])
    df = pd.concat([start, df], ignore_index=True)

    from travel_time import walk_min, nearest_station, rail_min, WAIT_MIN

    n = len(df)
    full = np.zeros((n, n))
    modes = np.empty((n, n), dtype=object)
    modes[:] = "徒歩"
    full[1:, 1:] = matrix

    # 各スポットの最寄駅を先に求めておく
    stations = [nearest_station(r["lat"], r["lon"]) for _, r in df.iterrows()]

    # 既存区間について、徒歩より速ければ鉄道利用と判定する
    for i in range(1, n):
        for j in range(1, n):
            if i == j:
                continue
            a, b = df.iloc[i], df.iloc[j]
            only_walk = walk_min(a["lat"], a["lon"], b["lat"], b["lon"])
            if full[i, j] < only_walk - 0.5:
                modes[i, j] = f"鉄道:{stations[i][0]}→{stations[j][0]}"

    # 起点から各スポットへの移動時間を計算する
    st_a, to_a = nearest_station(START_LAT, START_LON)
    for k in range(1, n):
        r = df.iloc[k]
        m = walk_min(START_LAT, START_LON, r["lat"], r["lon"])
        st_b, to_b = stations[k]
        if st_a != st_b:
            via = to_a + WAIT_MIN + rail_min(st_a, st_b) + to_b
            if via < m:
                m = via
                modes[0, k] = f"鉄道:{st_a}→{st_b}"
                modes[k, 0] = f"鉄道:{st_b}→{st_a}"
        full[0, k] = full[k, 0] = m

    # 昼食休憩ノードを追加する。特定の店は指定せず、全スポットの重心を仮の位置
    # とする。移動時間を単純に0にすると、挿入した区間の本来の移動時間が
    # まるごと消えてしまう（A→昼食→Bが実質0分になる）ため、起点と同じ方法
    # （徒歩 or 最寄駅経由の鉄道、短い方）で他ノードとの移動時間を計算する。
    lunch_lat = df.loc[1:, "lat"].mean()
    lunch_lon = df.loc[1:, "lon"].mean()
    lunch = pd.DataFrame([{
        "name": LUNCH_NAME, "area": "昼食",
        "lat": lunch_lat, "lon": lunch_lon,
        "stay_min": LUNCH_STAY_MIN, "open_hour": LUNCH_OPEN_HOUR, "close_hour": LUNCH_CLOSE_HOUR,
        "fee": 0, "score": 0, "description": "",
    }])
    df = pd.concat([df, lunch], ignore_index=True)
    lunch_idx = len(df) - 1

    full = np.pad(full, ((0, 1), (0, 1)))
    modes = np.pad(modes, ((0, 1), (0, 1)), constant_values="徒歩")

    lunch_st, lunch_to_st = nearest_station(lunch_lat, lunch_lon)
    for k in range(lunch_idx):
        r = df.iloc[k]
        m = walk_min(lunch_lat, lunch_lon, r["lat"], r["lon"])
        st_b, to_b = stations[k]
        if lunch_st != st_b:
            via = lunch_to_st + WAIT_MIN + rail_min(lunch_st, st_b) + to_b
            if via < m:
                m = via
                modes[lunch_idx, k] = f"鉄道:{lunch_st}→{st_b}"
                modes[k, lunch_idx] = f"鉄道:{st_b}→{lunch_st}"
        full[lunch_idx, k] = full[k, lunch_idx] = m

    return df, full, modes


def solve(df, travel, budget_min, start_hour,
          search_sec=SEARCH_SEC, penalty_scale=100, max_wait=60):
    """満足度スコアの合計を最大化するルートを求める"""
    n = len(df)
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)   # n地点, 1経路, 起点0
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        """移動時間＋出発地での滞在時間を返す"""
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return int(round(travel[i, j])) + int(df.iloc[i]["stay_min"])

    transit_idx = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    # 時間次元: 開門待ちを許しつつ、累積時間が持ち時間を超えないようにする
    routing.AddDimension(
        transit_idx,
        max_wait,      # 開門待ちを許す上限（分）
        budget_min,    # 上限
        True,          # 起点で0から開始
        "Time",
    )
    time_dim = routing.GetDimensionOrDie("Time")

    # 拝観時間を時間枠として設定する
    for i in range(1, n):
        r = df.iloc[i]
        open_min = max(0, int((r["open_hour"] - start_hour) * 60))
        close_min = int((r["close_hour"] - start_hour) * 60) - int(r["stay_min"])
        close_min = min(max(close_min, open_min), budget_min)
        index = manager.NodeToIndex(i)
        time_dim.CumulVar(index).SetRange(open_min, close_min)

    # 訪問を省略できるようにする（スコアが高いほど省略ペナルティが大きい）。
    # 昼食休憩はスコアを持たないため通常の式では省略され放題になってしまう。
    # 正午をまたぐ行程では大きな固定ペナルティを課して優先的に組み込ませ、
    # またがない行程では省略前提（ペナルティ0）にする。
    needs_lunch = crosses_lunch(start_hour, budget_min)
    for i in range(1, n):
        r = df.iloc[i]
        if r["name"] == LUNCH_NAME:
            penalty = LUNCH_PENALTY if needs_lunch else 0
        else:
            penalty = int(r["score"]) * penalty_scale
        routing.AddDisjunction([manager.NodeToIndex(i)], penalty)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.FromSeconds(search_sec)

    solution = routing.SolveWithParameters(params)
    if solution is None:
        return None, None

    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append((node, solution.Value(time_dim.CumulVar(index))))
        index = solution.Value(routing.NextVar(index))

    total = sum(int(df.iloc[i]["score"]) for i, _ in route)
    return route, total


def show(label, df, result, total_score, start_hour):
    """結果を1件表示する"""
    print(f"===== {label} =====")
    if result is None:
        print("解が見つかりませんでした\n")
        return
    print(f"訪問数: {len(result) - 1}件 / 満足度合計: {total_score}")
    for i, t in result:
        r = df.iloc[i]
        hh = start_hour + t / 60
        print(f"  {int(hh):02d}:{int((hh % 1) * 60):02d}  {r['name']}"
              f"（スコア{int(r['score'])}）")
    print()


if __name__ == "__main__":
    df, travel, modes = load_data()
    result, total = solve(df, travel, BUDGET_MIN, START_HOUR)
    show(f"持ち時間 {BUDGET_MIN}分", df, result, total, START_HOUR)