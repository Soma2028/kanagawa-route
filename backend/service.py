"""app.py の集計ロジックを optimize.solve() の結果から API レスポンスに組み立てる

summarize_route() は solve() の結果 (result, total) を受け取るだけの純粋な処理にし、
build_route_response() 側でだけ solve() を呼ぶ。こう分けておくことで、
solve() を再実行して探索結果が変わる（GUIDED_LOCAL_SEARCH は時間切れ判定に依存するため
同じ入力でも毎回同じ解になるとは限らない）ことの影響を受けずに、
集計ロジックだけを app.py の元の計算と突き合わせて検証できる。

excluded（外した候補）と breakdown（このルートの内訳）はどちらも、確定した
result に対する事後的な後付け計算であり、optimize.solve() 自身が「理由」を
返しているわけではない。特に excluded の extra_minutes は「このルートに
そのまま追加した場合の試算」であって、他スポットとの入れ替えは考慮しないため
「不採用の理由」の証明ではない（EXCLUDED_NOTE として明記し、API にも含める）。
"""
from optimize import LUNCH_NAME, crosses_lunch

from .schemas import (
    BreakdownItem,
    ExcludedSpot,
    RouteRequest,
    RouteResponse,
    Segment,
    Stop,
    Summary,
)

EXCLUDED_NOTE = (
    "ここでの数値は「今回のルートにそのまま追加した場合」の試算です。"
    "他のスポットとの入れ替えは考慮していないため、不採用の理由そのものではありません。"
)

LUNCH_NOT_INCLUDED_NOTE = "持ち時間が足りないため、昼食の時間を含めることができませんでした。"


def clock_str(hour_float: float) -> str:
    return f"{int(hour_float):02d}:{int((hour_float % 1) * 60):02d}"


def _rail_geometry(from_lat, from_lon, to_lat, to_lon, detail):
    """鉄道区間の経由点を「出発地→最寄駅→(鎌倉駅→)到着駅→到着地」の折れ線で組み立てる

    実際の線路データは使わず、既存の駅座標(travel_time.STATIONS)だけで近似する。
    """
    from travel_time import STATIONS, STATION_LINES

    st_a, st_b = detail.split("→")
    points = [(from_lat, from_lon), STATIONS[st_a]]

    same_line = STATION_LINES[st_a] == STATION_LINES[st_b]
    via_kamakura_endpoint = st_a == "鎌倉" or st_b == "鎌倉"
    if not (same_line or via_kamakura_endpoint):
        points.append(STATIONS["鎌倉"])  # 路線が異なる場合は鎌倉駅を経由点に挟む

    points.append(STATIONS[st_b])
    points.append((to_lat, to_lon))
    return points


def _walk_geometry(walk_geometry_cache, name_a, name_b):
    """事前取得した徒歩経路のキャッシュから、進行方向に合わせた点列を返す

    キーはスポット名をソートした順（"A|B"）で保存されているため、逆方向の場合は
    点列を反転する。起点・昼食ノードなど、キャッシュにないペアは None を返し、
    呼び出し側で直線にフォールバックさせる。
    """
    if not walk_geometry_cache:
        return None
    lo, hi = sorted([name_a, name_b])
    points = walk_geometry_cache.get(f"{lo}|{hi}")
    if points is None:
        return None
    return points if name_a == lo else list(reversed(points))


def _time_window(r, start_hour, budget_min):
    """optimize.solve() と同じ式で拝観時間の枠（分, start_hour起点）を求める"""
    open_min = max(0, int((r["open_hour"] - start_hour) * 60))
    close_min = int((r["close_hour"] - start_hour) * 60) - int(r["stay_min"])
    close_min = min(max(close_min, open_min), budget_min)
    return open_min, close_min


def compute_excluded(work, travel, result, start_hour, budget_min, max_wait, end_min):
    """訪問しなかった各スポットについて、確定ルートへの挿入試算を行う"""
    visited = {i for i, _ in result}
    route_nodes = [i for i, _ in result]
    route_times = [t for _, t in result]

    # 挿入位置の候補: 各訪問区間 ＋ 最後の訪問地から起点への帰路
    edges = [
        (route_nodes[k], route_nodes[k + 1], route_times[k])
        for k in range(len(route_nodes) - 1)
    ]
    edges.append((route_nodes[-1], 0, route_times[-1]))

    remaining_slack = budget_min - end_min
    excluded = []

    for c in range(1, len(work)):
        if c in visited:
            continue
        r = work.iloc[c]
        if r["name"] == LUNCH_NAME:
            continue  # 昼食は観光候補ではないため「外した候補」には含めない
        open_min, close_min = _time_window(r, start_hour, budget_min)
        stay_c = int(r["stay_min"])

        feasible_extra = []
        misses = []  # (超過幅, 最速到着分) : 拝観時間内に収まらない挿入位置
        for edge_i, edge_j, t_i in edges:
            stay_i = int(work.iloc[edge_i]["stay_min"])
            earliest_arrival = t_i + stay_i + travel[edge_i, c]
            if earliest_arrival > close_min:
                misses.append((earliest_arrival - close_min, earliest_arrival))
                continue
            wait_needed = max(0, open_min - earliest_arrival)
            if wait_needed > max_wait:
                misses.append((open_min - max_wait - earliest_arrival, earliest_arrival))
                continue
            extra = travel[edge_i, c] + wait_needed + stay_c + travel[c, edge_j] - travel[edge_i, edge_j]
            feasible_extra.append(extra)

        if not feasible_extra:
            _, earliest = min(misses, key=lambda m: m[0])
            excluded.append(ExcludedSpot(
                name=r["name"], area=r["area"], score=int(r["score"]),
                status="closed", extra_minutes=0,
                earliest_arrival=clock_str(start_hour + earliest / 60),
                closes_at=clock_str(float(r["close_hour"])),
            ))
            continue

        best_extra = min(feasible_extra)
        if best_extra > remaining_slack:
            excluded.append(ExcludedSpot(
                name=r["name"], area=r["area"], score=int(r["score"]),
                status="over_budget", extra_minutes=int(round(best_extra)),
                shortfall_minutes=int(round(best_extra - remaining_slack)),
            ))
        else:
            excluded.append(ExcludedSpot(
                name=r["name"], area=r["area"], score=int(r["score"]),
                status="fits", extra_minutes=int(round(best_extra)),
            ))

    return excluded


def compute_breakdown(work, travel, modes, result, total, summary):
    """このルートの内訳（事実の提示のみ、評価語や因果の主張は含まない）"""
    items = []

    # 待機時間: 各区間で「到着時刻」と「待たずに着いた場合の時刻」の差を合計する
    total_wait = 0.0
    for k in range(1, len(result)):
        i_prev, t_prev = result[k - 1]
        i_cur, t_cur = result[k]
        stay_prev = int(work.iloc[i_prev]["stay_min"])
        expected = t_prev + stay_prev + travel[i_prev, i_cur]
        total_wait += max(0.0, t_cur - expected)
    items.append(BreakdownItem(
        type="wait_time",
        message=f"待機時間は合計{int(round(total_wait))}分です",
    ))

    # 鉄道利用: 実際に使った移動時間を鉄道区間/徒歩区間で内訳表示する
    # （「全区間徒歩だったら」という仮定の比較はしない。迂回係数1.4での近似計算
    # になるうえ、実際にはあり得ない前提のため、比較として意味を持たせにくい）
    # 区間には最後の訪問地から起点への帰路も含める（summary.move_total_min と一致させるため）
    edges = [(result[k][0], result[k + 1][0]) for k in range(len(result) - 1)]
    edges.append((result[-1][0], 0))

    # summary.move_total_min（区間ごとに int(round()) した値の積み上げ）と
    # 一致させるため、ここでも生の浮動小数点値ではなく区間ごとに丸めてから合計する
    rail_count = 0
    rail_int = 0
    walk_int = 0
    for i, j in edges:
        mins = int(round(travel[i, j]))
        if modes[i, j].startswith("鉄道"):
            rail_count += 1
            rail_int += mins
        else:
            walk_int += mins
    if rail_count:
        total_int = rail_int + walk_int
        items.append(BreakdownItem(
            type="rail_usage",
            message=(
                f"移動時間{total_int}分のうち、"
                f"鉄道は{rail_int}分、徒歩は{walk_int}分です"
                f"（鉄道利用は{rail_count}区間）"
            ),
        ))
    else:
        items.append(BreakdownItem(type="rail_usage", message="全区間徒歩で移動しています"))

    # 移動時間の比率
    move_ratio = summary.move_total_min / summary.end_min * 100 if summary.end_min else 0.0
    items.append(BreakdownItem(
        type="move_ratio",
        message=f"移動時間は総所要時間の{move_ratio:.0f}%です",
    ))

    # スコア達成率（エリア選好で減点済みの work を基準にする＝ソルバーが実際に最大化した対象）。
    # 昼食は観光スポットではないため、母数からもスコア合計からも除く（スコアは
    # 元々0なので合計には影響しないが、件数表示から除くために明示的に絞り込む）
    real_spots = work[(work.index != 0) & (work["name"] != LUNCH_NAME)]
    all_score = int(real_spots["score"].sum())
    pct = total / all_score * 100 if all_score else 0.0
    items.append(BreakdownItem(
        type="score_rate",
        message=(
            f"全{len(real_spots)}スポット中{summary.visited_count}件、"
            f"獲得可能スコアの{pct:.0f}%（{total}/{all_score}点）を達成しています"
        ),
    ))

    return items


def summarize_route(work, travel, modes, photos, walk_geometry, result, total, start_hour, budget_min, max_wait) -> RouteResponse:
    spots = result[1:]                      # 起点を除いたスポット・昼食
    spots_real = [(i, t) for i, t in spots if work.iloc[i]["name"] != LUNCH_NAME]
    lunch_visits = [(i, t) for i, t in spots if work.iloc[i]["name"] == LUNCH_NAME]

    total_fee = sum(int(work.iloc[i]["fee"]) for i, _ in spots_real)
    last_i, last_t = result[-1]
    # 道中の区間はソルバー内部で int(round()) された整数分で積み上がっている
    # （time_callback参照）ため、最後の帰路区間もここで同じ丸め方にしないと、
    # compute_breakdown 側の区間合計（同じくint(round())で積み上げる）と
    # 端数のずれが生じる
    end_min = last_t + int(work.iloc[last_i]["stay_min"]) + int(round(travel[last_i, 0]))
    end_hour = start_hour + end_min / 60
    stay_total = sum(int(work.iloc[i]["stay_min"]) for i, _ in spots_real)
    lunch_min = sum(int(work.iloc[i]["stay_min"]) for i, _ in lunch_visits)
    move_total = int(end_min - stay_total - lunch_min)

    stops = []
    for order, (i, t) in enumerate(result):
        r = work.iloc[i]
        hh = start_hour + t / 60
        photo = photos.get(r["name"]) or {}
        desc = r["description"] if isinstance(r["description"], str) else ""

        if order == 0:
            stop_type = "start"
        elif r["name"] == LUNCH_NAME:
            stop_type = "meal"
        else:
            stop_type = "spot"

        # 昼食は場所を特定しないため、表示上は直前の訪問地と同じ座標にする
        # （移動時間の計算自体は全スポットの重心を仮の位置として行っている）
        if stop_type == "meal" and stops:
            lat, lon = stops[-1].lat, stops[-1].lon
        else:
            lat, lon = float(r["lat"]), float(r["lon"])

        stops.append(Stop(
            order=order,
            name=r["name"],
            area=r["area"],
            type=stop_type,
            lat=lat,
            lon=lon,
            arrival_clock=clock_str(hh),
            arrival_min=int(t),
            stay_min=int(r["stay_min"]),
            fee=int(r["fee"]),
            score=int(r["score"]),
            description=desc,
            photo_url=photo.get("photo_url"),
            photo_artist=photo.get("photo_artist"),
            photo_license=photo.get("photo_license"),
            photo_license_url=photo.get("photo_license_url"),
        ))

    segments = []
    for order in range(len(result) - 1):
        i, _ = result[order]
        j, _ = result[order + 1]
        raw = modes[i, j]
        mins = int(round(travel[i, j]))
        from_stop, to_stop = stops[order], stops[order + 1]
        if raw.startswith("鉄道"):
            mode, detail = "鉄道", raw.split(":", 1)[1]
            geometry = _rail_geometry(from_stop.lat, from_stop.lon, to_stop.lat, to_stop.lon, detail)
        else:
            mode, detail = "徒歩", None
            geometry = _walk_geometry(walk_geometry, from_stop.name, to_stop.name)
        segments.append(Segment(
            from_index=order, to_index=order + 1, mode=mode, detail=detail, minutes=mins,
            geometry=geometry,
        ))

    summary = Summary(
        total_score=int(total),
        visited_count=len(spots_real),
        total_fee=int(total_fee),
        stay_total_min=int(stay_total),
        lunch_min=int(lunch_min),
        move_total_min=move_total,
        end_min=int(end_min),
        end_clock=clock_str(end_hour),
    )

    excluded = compute_excluded(work, travel, result, start_hour, budget_min, max_wait, summary.end_min)
    breakdown = compute_breakdown(work, travel, modes, result, total, summary)

    needs_lunch = crosses_lunch(start_hour, budget_min)
    lunch_note = LUNCH_NOT_INCLUDED_NOTE if (needs_lunch and not lunch_visits) else None

    return RouteResponse(
        stops=stops, segments=segments, summary=summary,
        excluded=excluded, excluded_note=EXCLUDED_NOTE, breakdown=breakdown,
        lunch_note=lunch_note,
    )


def build_route_response(df, travel, modes, photos, walk_geometry, req: RouteRequest) -> RouteResponse | None:
    from optimize import solve

    # エリア選択を好みとしてスコアに反映する（app.py と同じロジック）
    work = df.copy()
    if req.areas:
        work.loc[~work["area"].isin(req.areas + ["起点"]), "score"] = 1

    budget_min = int(req.budget_hours * 60)
    result, total = solve(
        work, travel, budget_min, req.start_hour,
        search_sec=req.search_sec, max_wait=req.max_wait,
    )
    if result is None:
        return None
    return summarize_route(
        work, travel, modes, photos, walk_geometry, result, total,
        req.start_hour, budget_min, req.max_wait,
    )
