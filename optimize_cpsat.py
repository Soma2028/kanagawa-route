"""制限時間内で満足度が最大になる周遊ルートを求める"""
import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

START_NAME = "鎌倉駅"
START_LAT, START_LON = 35.3192, 139.5500

START_HOUR = 9.0        # 出発時刻
BUDGET_MIN = 360        # 持ち時間（分）


def load_data():
    """スポットと移動時間行列を読み込み、起点を先頭に追加する"""
    df = pd.read_csv("spots_master.csv")
    matrix = pd.read_csv("travel_matrix.csv", index_col=0).values

    # 起点（鎌倉駅）を index 0 として挿入する
    start = pd.DataFrame([{
        "name": START_NAME, "area": "起点",
        "lat": START_LAT, "lon": START_LON,
        "stay_min": 0, "open_hour": 0, "close_hour": 24, "fee": 0, "score": 0,
    }])
    df = pd.concat([start, df], ignore_index=True)

    # 起点から各スポットへの移動時間を計算して行列を1行1列拡張する
    from travel_time import walk_min, nearest_station, rail_min, WAIT_MIN

    n = len(df)
    full = np.zeros((n, n))
    full[1:, 1:] = matrix
    for k in range(1, n):
        r = df.iloc[k]
        m = walk_min(START_LAT, START_LON, r["lat"], r["lon"])
        st_a, to_a = nearest_station(START_LAT, START_LON)
        st_b, to_b = nearest_station(r["lat"], r["lon"])
        if st_a != st_b:
            m = min(m, to_a + WAIT_MIN + rail_min(st_a, st_b) + to_b)
        full[0, k] = full[k, 0] = m

    return df, full


def solve(df, travel, budget_min, start_hour):
    """満足度スコアの合計を最大化するルートを求める"""
    n = len(df)
    model = cp_model.CpModel()

    # visit[i]: スポットiを訪問するか
    visit = [model.NewBoolVar(f"v{i}") for i in range(n)]
    model.Add(visit[0] == 1)   # 起点は必ず含む

    # x[i][j]: iの直後にjへ移動するか
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.NewBoolVar(f"x{i}_{j}")

    # 訪問するスポットは入次数・出次数がちょうど1
    for i in range(n):
        model.Add(sum(x[i, j] for j in range(n) if i != j) == visit[i])
        model.Add(sum(x[j, i] for j in range(n) if i != j) == visit[i])

    # 到着時刻（分単位、起点からの経過）
    T = [model.NewIntVar(0, budget_min, f"t{i}") for i in range(n)]
    model.Add(T[0] == 0)

    BIG = budget_min * 2
    for i in range(n):
        for j in range(1, n):
            if i == j:
                continue
            stay = int(df.iloc[i]["stay_min"])
            move = int(round(travel[i, j]))
            # jへ行くなら、jの到着時刻はiの到着＋滞在＋移動 以上
            model.Add(T[j] >= T[i] + stay + move - BIG * (1 - x[i, j]))

    # 拝観時間の制約
    for i in range(1, n):
        open_min = int((df.iloc[i]["open_hour"] - start_hour) * 60)
        close_min = int((df.iloc[i]["close_hour"] - start_hour) * 60)
        stay = int(df.iloc[i]["stay_min"])
        model.Add(T[i] >= open_min).OnlyEnforceIf(visit[i])
        model.Add(T[i] + stay <= close_min).OnlyEnforceIf(visit[i])

    # 最後に起点へ戻る時間も持ち時間に収める
    for i in range(1, n):
        stay = int(df.iloc[i]["stay_min"])
        move = int(round(travel[i, 0]))
        model.Add(T[i] + stay + move <= budget_min).OnlyEnforceIf(x[i, 0])

    # 目的関数: 満足度スコアの合計を最大化
    scores = [int(df.iloc[i]["score"]) for i in range(n)]
    model.Maximize(sum(scores[i] * visit[i] for i in range(1, n)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    # 解の質を確認する（時間切れか、真の最適解かを切り分ける）
    print("解の状態:", solver.StatusName(status))
    print("経過時間:", f"{solver.WallTime():.1f}秒")
    print("目的関数値:", solver.ObjectiveValue())
    print("上界:", solver.BestObjectiveBound())
    print()

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, None

    # 経路を順に辿る
    route, cur = [0], 0
    while True:
        nxt = next(
            (j for j in range(n) if j != cur and solver.Value(x[cur, j])), None
        )
        if nxt is None or nxt == 0:
            break
        route.append(nxt)
        cur = nxt

    total = sum(scores[i] for i in route)
    return [(i, solver.Value(T[i])) for i in route], total


if __name__ == "__main__":
    df, travel = load_data()
    result, total_score = solve(df, travel, BUDGET_MIN, START_HOUR)

    if result is None:
        print("解が見つかりませんでした")
    else:
        print(f"出発 {START_HOUR:.0f}時 / 持ち時間 {BUDGET_MIN}分")
        print(f"訪問数: {len(result) - 1}件 / 満足度合計: {total_score}\n")
        for i, t in result:
            r = df.iloc[i]
            hh = START_HOUR + t / 60
            print(f"{int(hh):02d}:{int((hh % 1) * 60):02d}  {r['name']}"
                  f"（滞在{int(r['stay_min'])}分, スコア{int(r['score'])}）")