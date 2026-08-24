"""フェーズ1のリグレッション確認: バックエンドが app.py と同じ計算結果を返すか検証する

1. solve() を1回だけ呼び、同じ (result, total) を使って
   - app.py の元のインライン集計コード（ここに再掲）
   - backend.service.summarize_route()
   の計算結果を突き合わせる。solve() を2回呼んで比較しないのは、
   GUIDED_LOCAL_SEARCH が時間切れ判定に依存し、同じ入力でも毎回同じ解が
   返るとは限らないため（比較対象が探索結果のブレなのか実装ミスなのか
   区別できなくなる）。
2. FastAPI アプリを実際に起動し、/api/areas と /api/route の応答が
   スキーマ通り・整合的（合計スコア＝訪問スポットのスコア合計 等）かを確認する。
3. リポジトリ直下ではないカレントディレクトリから import しても
   optimize.load_data() の相対パスCSV読み込みが壊れないかをサブプロセスで確認する
   （main.py の chdir 対応が効いているかの確認）。
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

from optimize import load_data, solve  # noqa: E402

from backend.service import clock_str, summarize_route  # noqa: E402


def reference_summary(work, travel, result, total, start_hour):
    """summarize_route() が満たすべき集計式を独立に再現したもの（比較の基準）

    元は app.py:164-171 のインラインコードをそのまま再現していたが、昼食休憩
    ノードの追加に伴い、昼食の滞在時間(lunch_min)を「滞在」「訪問数」から
    除いて別枠にするよう仕様を変更したため、その新仕様に合わせて更新した
    （app.py 自体は参考用のまま残しており、この関数とは一致しなくなった）。
    """
    from optimize import LUNCH_NAME

    spots = result[1:]
    spots_real = [(i, t) for i, t in spots if work.iloc[i]["name"] != LUNCH_NAME]
    lunch_visits = [(i, t) for i, t in spots if work.iloc[i]["name"] == LUNCH_NAME]

    total_fee = sum(int(work.iloc[i]["fee"]) for i, _ in spots_real)
    last_i, last_t = result[-1]
    # summarize_route() と同じく、最後の帰路区間も int(round()) で丸める
    # （道中の区間はソルバー内部で既に整数分で積み上がっているため）
    end_min = last_t + int(work.iloc[last_i]["stay_min"]) + int(round(travel[last_i, 0]))
    end_hour = start_hour + end_min / 60
    stay_total = sum(int(work.iloc[i]["stay_min"]) for i, _ in spots_real)
    lunch_min = sum(int(work.iloc[i]["stay_min"]) for i, _ in lunch_visits)
    move_total = int(end_min - stay_total - lunch_min)
    return {
        "total_score": total,
        "visited_count": len(spots_real),
        "total_fee": total_fee,
        "stay_total_min": stay_total,
        "lunch_min": lunch_min,
        "move_total_min": move_total,
        "end_min": int(end_min),
        "end_clock": clock_str(end_hour),
    }


def check_summary_arithmetic():
    print("=== 1. 集計ロジックの突き合わせ ===")
    df, travel, modes = load_data()
    start_hour = 9.0
    result, total = solve(df, travel, 360, start_hour, search_sec=5, max_wait=60)
    assert result is not None, "解が見つかりませんでした（設定を確認してください）"

    expected = reference_summary(df, travel, result, total, start_hour)
    actual = summarize_route(df, travel, modes, {}, result, total, start_hour, 360, 60).summary.model_dump()

    mismatches = {k: (expected[k], actual[k]) for k in expected if expected[k] != actual[k]}
    if mismatches:
        raise AssertionError(f"想定した集計式と一致しません: {mismatches}")
    print(f"  OK: {expected}")


def check_lunch_skipped_when_infeasible():
    """正午をまたぐのに昼食を入れる余地が無いとき、解なしにせず昼食だけ諦めるか

    RouteRequest の入力バリデーション（budget_hours>=3.0 等）の範囲内では
    このケースを作れなかったため、solve() を直接呼んで検証する。
    """
    print("=== 1.5 昼食が入らない極端なケースの確認 ===")
    from optimize import crosses_lunch

    df, travel, modes = load_data()
    start_hour, budget_min = 11.83, 70  # 11:50開始・70分、正午をまたぐが極端に短い
    assert crosses_lunch(start_hour, budget_min), "テスト条件が正午をまたいでいません"

    result, total = solve(df, travel, budget_min, start_hour, search_sec=5, max_wait=0)
    assert result is not None, "解なしになってしまいました（昼食を諦める形で解けるはず）"

    from optimize import LUNCH_NAME
    assert all(df.iloc[i]["name"] != LUNCH_NAME for i, _ in result), "極端に短いのに昼食が入っています"

    summarized = summarize_route(df, travel, modes, {}, result, total, start_hour, budget_min, 0)
    assert summarized.summary.lunch_min == 0
    assert summarized.lunch_note, "昼食が入らなかったのにlunch_noteが空です"
    print(f"  OK: 昼食を諦めて解けました（{summarized.lunch_note}）")


def check_api_smoke():
    print("=== 2. API エンドポイントの疎通・整合性確認 ===")
    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as client:
        r = client.get("/api/areas")
        assert r.status_code == 200, r.text
        areas = r.json()["areas"]
        assert len(areas) > 0
        print(f"  /api/areas OK: {areas}")

        r = client.post("/api/route", json={
            "start_hour": 9.0, "budget_hours": 6.0, "areas": [],
            "search_sec": 5, "max_wait": 60,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        stops, segments, summary = body["stops"], body["segments"], body["summary"]

        assert len(segments) == len(stops) - 1
        visited = stops[1:]  # 起点を除く（昼食を含む場合あり）
        real_visited = [s for s in visited if s["type"] == "spot"]
        meal_visited = [s for s in visited if s["type"] == "meal"]
        assert stops[0]["type"] == "start"
        assert sum(s["score"] for s in visited) == summary["total_score"]
        assert sum(s["fee"] for s in visited) == summary["total_fee"]
        assert summary["visited_count"] == len(real_visited), "visited_countに昼食が混ざっています"
        arrival_mins = [s["arrival_min"] for s in stops]
        assert arrival_mins == sorted(arrival_mins), "到着時刻が単調増加していません"

        excluded, breakdown = body["excluded"], body["breakdown"]
        assert len(excluded) + len(real_visited) == 34, "訪問+除外の合計がスポット総数と一致しません"
        assert all(e["name"] != "昼食" for e in excluded), "昼食が「外した候補」に混入しています"
        rail_item = next(b for b in breakdown if b["type"] == "rail_usage")
        nums = [int(n) for n in re.findall(r"\d+", rail_item["message"])]
        # 「移動時間{総}分のうち、鉄道は{鉄道}分、徒歩は{徒歩}分です（鉄道利用は{件数}区間）」
        assert nums[0] == summary["move_total_min"], (
            f"breakdownの移動時間内訳がsummary.move_total_minと不一致: {rail_item['message']}"
        )
        assert nums[1] + nums[2] == nums[0], f"鉄道+徒歩が合計と一致しません: {rail_item['message']}"

        # 出発9:00・持ち時間6時間は正午をまたぐため、昼食が入っていれば
        # lunch_min>0かつlunch_noteはNone、入らなければ逆になるはず
        if meal_visited:
            assert summary["lunch_min"] == 60
            assert body["lunch_note"] is None
            print(f"  昼食 OK: {meal_visited[0]['arrival_clock']}に組み込まれました")
        else:
            assert summary["lunch_min"] == 0
            assert body["lunch_note"], "昼食が入らなかったのにlunch_noteが空です"
            print(f"  昼食 OK: 入らなかったため注記あり（{body['lunch_note']}）")

        print(f"  /api/route OK: 訪問{len(real_visited)}件 / スコア{summary['total_score']} / 帰着{summary['end_clock']}")
        print(f"  excluded {len(excluded)}件 / breakdown 移動時間内訳の整合性 OK")

        # 正午をまたがない条件（ちょうど12時開始）では昼食が一切考慮されないことを確認する
        # （start_hourのバリデーション上限が12.0のため、境界値のこのケースで検証する）
        r = client.post("/api/route", json={
            "start_hour": 12.0, "budget_hours": 3.0, "areas": [],
            "search_sec": 5, "max_wait": 60,
        })
        assert r.status_code == 200, r.text
        no_lunch_body = r.json()
        assert all(s["type"] != "meal" for s in no_lunch_body["stops"]), "正午をまたがないのに昼食が入っています"
        assert no_lunch_body["lunch_note"] is None, "正午をまたがないのにlunch_noteが出ています"
        assert no_lunch_body["summary"]["lunch_min"] == 0
        print("  昼食なし条件（12時開始/3時間） OK")

        r = client.post("/api/route", json={
            "start_hour": 9.0, "budget_hours": 0.5, "areas": [],
            "search_sec": 1, "max_wait": 0,
        })
        assert r.status_code == 422, "極端に短い持ち時間でも解なしエラーにならない"
        print("  解なし時の422応答 OK")


def check_runs_from_foreign_cwd():
    print("=== 3. リポジトリ外のカレントディレクトリからの起動確認 ===")
    script = (
        "from fastapi.testclient import TestClient\n"
        "from backend.main import app\n"
        "with TestClient(app) as c:\n"
        "    r = c.get('/api/areas')\n"
        "    assert r.status_code == 200, r.text\n"
        "    assert len(r.json()['areas']) > 0\n"
        "print('FOREIGN_CWD_OK')\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd="/tmp", env=env, capture_output=True, text=True,
    )
    if proc.returncode != 0 or "FOREIGN_CWD_OK" not in proc.stdout:
        raise AssertionError(f"cwd=/tmp からの起動に失敗:\n{proc.stdout}\n{proc.stderr}")
    print("  OK: cwd=/tmp から起動しても spots_master.csv 等を読めた")


if __name__ == "__main__":
    check_summary_arithmetic()
    check_lunch_skipped_when_infeasible()
    check_api_smoke()
    check_runs_from_foreign_cwd()
    print("\n全チェック OK")
