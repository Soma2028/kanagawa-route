"""スポットの日本語版Wikipedia記事から、直近12か月分のページビューを取得する

スポット名をそのまま記事タイトルとして使うと、同名の別対象を指してしまう
ケースが多いことが事前調査で分かった:

- 御霊神社・成就院・極楽寺・光明寺・報国寺・浄妙寺・瑞泉寺 は、
  スポット名そのままだと全国の同名寺社の曖昧さ回避ページに一致する
  （鎌倉市のものは「〇〇 (鎌倉市)」という記事名）
- 長谷寺 はスポット名そのままだと奈良県桜井市の長谷寺に一致してしまう
  （鎌倉のものは「長谷寺 (鎌倉市)」）
- 高徳院 は通称「鎌倉大仏」でも独立にページビューが計上されている
  （リダイレクト元/先の関係でも別々に集計される）ため、両方の合計を採用する
- 半僧坊 は建長寺境内の一施設で独立記事がない。記事を建長寺と共有すると
  別スポットである建長寺の数値と重複してしまうため、意図的に欠損として扱う

上記はいずれも `.../page/summary/{title}` で type（disambiguation か）と
extract 中に「鎌倉」が含まれるかを実際に確認して特定したもの。
このリストに無いスポットはスポット名をそのまま記事タイトルとして使う。
"""
import time
from datetime import date, timedelta
from urllib.parse import quote

import pandas as pd
import requests

HEADERS = {"User-Agent": "kanagawa-route/0.1 (portfolio project; oobasouma0411@gmail.com)"}
API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/ja.wikipedia/all-access/user"

# スポット名 -> Wikipedia記事タイトルのリスト（複数ある場合は合計する）。
# 値が None のスポットは独立記事がないため最初から欠損として扱う。
WIKI_TITLE_OVERRIDES = {
    "高徳院": ["高徳院", "鎌倉大仏"],
    "御霊神社": ["御霊神社 (鎌倉市)"],
    "成就院": ["成就院 (鎌倉市)"],
    "極楽寺": ["極楽寺 (鎌倉市)"],
    "光明寺": ["光明寺 (鎌倉市)"],
    "報国寺": ["報国寺 (鎌倉市)"],
    "浄妙寺": ["浄妙寺 (鎌倉市)"],
    "瑞泉寺": ["瑞泉寺 (鎌倉市)"],
    "長谷寺": ["長谷寺 (鎌倉市)"],
    "半僧坊": None,
}


def target_titles(name):
    """スポット名から問い合わせるWikipedia記事タイトルの一覧を返す"""
    if name in WIKI_TITLE_OVERRIDES:
        override = WIKI_TITLE_OVERRIDES[name]
        return list(override) if override else []
    return [name]


def last_12_full_months_range():
    """直近の完了した12か月に十分余裕を持たせた問い合わせ範囲を返す

    月初にスナップした「当月1日」を上限とし、そこから約13か月遡った月初を
    下限にする。当月分（まだ完了していない）はこの範囲でも含まれ得るが、
    呼び出し側で厳密に除外する。
    """
    end_month_first = date.today().replace(day=1)
    start_month_first = (end_month_first - timedelta(days=400)).replace(day=1)
    return start_month_first.strftime("%Y%m%d00"), end_month_first.strftime("%Y%m%d00")


def fetch_monthly_views(title, start, end, max_retry=5):
    """1記事分の月別ページビューを取得する。記事が存在しない場合は None を返す"""
    url = f"{API}/{quote(title, safe='')}/monthly/{start}/{end}"
    wait = 2.0
    for _ in range(max_retry):
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code == 404:
            return None
        if res.status_code == 429:
            print(f"    制限中… {wait:.0f}秒待機")
            time.sleep(wait)
            wait *= 2
            continue
        res.raise_for_status()
        return res.json()["items"]
    raise RuntimeError(f"再試行の上限に達しました: {title}")


if __name__ == "__main__":
    df = pd.read_csv("spots_master.csv")
    start, end = last_12_full_months_range()
    current_month = date.today().strftime("%Y%m")

    rows = []
    for name in df["name"]:
        titles = target_titles(name)
        if not titles:
            print(f"欠損: {name}（独立記事なし）")
            rows.append({
                "name": name, "wiki_titles": "", "found": False,
                "months": 0, "total_views": None, "monthly_avg": None,
            })
            continue

        monthly_totals = {}
        any_found = False
        for title in titles:
            items = fetch_monthly_views(title, start, end)
            if items is None:
                print(f"  見つからず: {name} <- {title}")
                continue
            any_found = True
            for item in items:
                month = item["timestamp"][:6]
                if month >= current_month:
                    continue  # 当月分（まだ完了していない）は除外する
                monthly_totals[month] = monthly_totals.get(month, 0) + item["views"]
            time.sleep(0.3)  # APIへの配慮

        if not any_found:
            print(f"欠損: {name}（該当記事が見つからず）")
            rows.append({
                "name": name, "wiki_titles": "|".join(titles), "found": False,
                "months": 0, "total_views": None, "monthly_avg": None,
            })
            continue

        recent_months = sorted(monthly_totals)[-12:]  # 直近12か月分に揃える
        total = sum(monthly_totals[m] for m in recent_months)
        n_months = len(recent_months)
        print(f"OK: {name} <- {'+'.join(titles)}  {n_months}ヶ月分 合計{total}")
        rows.append({
            "name": name, "wiki_titles": "|".join(titles), "found": True,
            "months": n_months, "total_views": total,
            "monthly_avg": round(total / n_months, 1) if n_months else None,
        })

    out = pd.DataFrame(rows)
    out.to_csv("pageviews.csv", index=False)
    print(f"\n保存しました: pageviews.csv（{len(out)}件中、欠損{(~out['found']).sum()}件）")
