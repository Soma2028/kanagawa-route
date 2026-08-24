"""app.py の集計ロジックを optimize.solve() の結果から API レスポンスに組み立てる

summarize_route() は solve() の結果 (result, total) を受け取るだけの純粋な処理にし、
build_route_response() 側でだけ solve() を呼ぶ。こう分けておくことで、
solve() を再実行して探索結果が変わる（GUIDED_LOCAL_SEARCH は時間切れ判定に依存するため
同じ入力でも毎回同じ解になるとは限らない）ことの影響を受けずに、
集計ロジックだけを app.py の元の計算と突き合わせて検証できる。
"""
from .schemas import RouteRequest, RouteResponse, Segment, Stop, Summary


def clock_str(hour_float: float) -> str:
    return f"{int(hour_float):02d}:{int((hour_float % 1) * 60):02d}"


def summarize_route(work, travel, modes, photos, result, total, start_hour) -> RouteResponse:
    spots = result[1:]                      # 起点を除いたスポット
    total_fee = sum(int(work.iloc[i]["fee"]) for i, _ in spots)
    last_i, last_t = result[-1]
    end_min = last_t + int(work.iloc[last_i]["stay_min"]) + travel[last_i, 0]
    end_hour = start_hour + end_min / 60
    stay_total = sum(int(work.iloc[i]["stay_min"]) for i, _ in spots)
    move_total = int(end_min - stay_total)

    stops = []
    for order, (i, t) in enumerate(result):
        r = work.iloc[i]
        hh = start_hour + t / 60
        photo = photos.get(r["name"]) or {}
        desc = r["description"] if isinstance(r["description"], str) else ""
        stops.append(Stop(
            order=order,
            name=r["name"],
            area=r["area"],
            lat=float(r["lat"]),
            lon=float(r["lon"]),
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
        if raw.startswith("鉄道"):
            mode, detail = "鉄道", raw.split(":", 1)[1]
        else:
            mode, detail = "徒歩", None
        segments.append(Segment(
            from_index=order, to_index=order + 1, mode=mode, detail=detail, minutes=mins,
        ))

    summary = Summary(
        total_score=int(total),
        visited_count=len(spots),
        total_fee=int(total_fee),
        stay_total_min=int(stay_total),
        move_total_min=move_total,
        end_min=int(end_min),
        end_clock=clock_str(end_hour),
    )
    return RouteResponse(stops=stops, segments=segments, summary=summary)


def build_route_response(df, travel, modes, photos, req: RouteRequest) -> RouteResponse | None:
    from optimize import solve

    # エリア選択を好みとしてスコアに反映する（app.py と同じロジック）
    work = df.copy()
    if req.areas:
        work.loc[~work["area"].isin(req.areas + ["起点"]), "score"] = 1

    result, total = solve(
        work, travel, int(req.budget_hours * 60), req.start_hour,
        search_sec=req.search_sec, max_wait=req.max_wait,
    )
    if result is None:
        return None
    return summarize_route(work, travel, modes, photos, result, total, req.start_hour)
