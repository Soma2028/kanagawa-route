"""Wikimedia Commons から各スポットの画像候補とライセンス情報を取得する"""
import re
import time

import pandas as pd
import requests

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "kanagawa-route/0.1 (portfolio project)"}

# 商用利用と改変が可能なライセンスのみ採用する
# 表記ゆれ（CC BY-SA / cc-by-sa）に対応するため、区切り文字を除いて判定する
ALLOWED = ("ccby", "ccbysa", "cc0", "publicdomain", "pd")


def request_with_retry(params, max_retry=5):
    """429が返ったら待って再試行する"""
    wait = 3.0
    for _ in range(max_retry):
        res = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if res.status_code == 429:
            print(f"    制限中… {wait:.0f}秒待機")
            time.sleep(wait)
            wait *= 2                    # 待ち時間を倍にしていく
            continue
        res.raise_for_status()
        return res.json()
    raise RuntimeError("再試行の上限に達しました")


def search_images(keyword, limit=3):
    """キーワードで画像ファイルを検索し、ファイル名の一覧を返す"""
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": f"{keyword} filetype:bitmap",
        "srnamespace": 6,           # ファイル名前空間
        "srlimit": limit,
    }
    data = request_with_retry(params)
    return [r["title"] for r in data["query"]["search"]]


def get_image_info(title):
    """ファイルのURL・作者・ライセンスを取得する"""
    params = {
        "action": "query", "format": "json",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 400,          # サムネイル幅
    }
    data = request_with_retry(params)
    pages = data["query"]["pages"]
    for page in pages.values():
        info = page.get("imageinfo", [{}])[0]
        meta = info.get("extmetadata", {})
        return {
            "file": title,
            "url": info.get("thumburl"),
            "artist": strip_html(meta.get("Artist", {}).get("value", "")),
            "license": meta.get("LicenseShortName", {}).get("value", ""),
            "license_url": meta.get("LicenseUrl", {}).get("value", ""),
        }
    return None


def strip_html(text):
    """作者欄に混じるHTMLタグを除去する"""
    return re.sub(r"<[^>]+>", "", text).strip()


def is_usable(license_name):
    """利用可能なライセンスか判定する（区切り文字の差を無視する）"""
    low = license_name.lower().replace("-", "").replace(" ", "")
    return any(low.startswith(k) for k in ALLOWED)


if __name__ == "__main__":
    df = pd.read_csv("spots_master.csv")     # 全スポットを対象にする
    rows = []
    for _, r in df.iterrows():
        name = r["name"]
        print(f"\n=== {name} ===")
        try:
            titles = search_images(f"{name} 鎌倉")
        except Exception as e:
            print(f"  検索失敗: {e}")
            continue

        if not titles:
            print("  候補なし")
            continue

        for title in titles:
            try:
                info = get_image_info(title)
            except Exception as e:
                print(f"  取得失敗: {title} ({e})")
                continue

            if not info or not info["url"]:
                continue
            usable = is_usable(info["license"])
            mark = "OK " if usable else "NG "
            print(f"  {mark}{info['license']:<20} {title}")
            rows.append({"name": name, **info, "usable": usable})
            time.sleep(2.0)     # Wikimedia の制限に合わせて間隔を空ける

        time.sleep(2.0)

    out = pd.DataFrame(rows)
    out.to_csv("photo_candidates.csv", index=False)
    print(f"\n候補を保存しました: {len(out)}件 → photo_candidates.csv")
    print(f"うち利用可能: {out['usable'].sum()}件")