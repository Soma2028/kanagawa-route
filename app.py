"""鎌倉の周遊ルートを最適化して地図に表示するアプリ"""
import folium
import numpy as np
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html

from optimize import load_data, solve
from travel_time import rail_label

st.set_page_config(page_title="鎌倉ルート最適化", page_icon="⛩️", layout="wide")

# エリアごとの色分け
AREA_COLORS = {
    "北鎌倉": "#4a7c59",
    "八幡宮": "#b5651d",
    "金沢街道": "#6b5b95",
    "長谷": "#2b7a9e",
    "江ノ電": "#d4874a",
    "西鎌倉": "#7a9e2b",
    "大町材木座": "#9e2b5b",
    "その他": "#5a5a5a",
    "起点": "#c0392b",
}

# スポット種別のアイコン
AREA_ICONS = {
    "北鎌倉": "🍃", "八幡宮": "⛩️", "金沢街道": "🎋", "長谷": "🗿",
    "江ノ電": "🌊", "西鎌倉": "🦊", "大町材木座": "🏯", "その他": "📍",
}


# ---- スタイル ----
st.markdown("""
<style>
.summary-card {
    background: #ffffff;
    border: 1px solid #e0d9cc;
    border-radius: 12px;
    padding: 18px 20px;
    height: 100%;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.summary-label { font-size: 0.85rem; color: #6b6b6b; margin-bottom: 6px; }
.summary-value {
    font-size: 1.9rem; font-weight: 700; line-height: 1.2; color: #2c2c2c;
}
.summary-sub { font-size: 0.8rem; color: #8a8a8a; margin-top: 4px; }

.spot-card {
    background: #ffffff;
    border: 1px solid #e0d9cc;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.spot-head { display: flex; align-items: baseline; gap: 10px; }
.spot-num {
    color: #fff; border-radius: 50%;
    width: 26px; height: 26px; display: inline-flex;
    align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
}
.spot-name { font-size: 1.15rem; font-weight: 700; color: #2c2c2c; }
.spot-time { font-size: 0.9rem; color: #8a8a8a; margin-left: auto; }
.badges { margin-top: 8px; }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.78rem; margin-right: 6px; margin-bottom: 4px;
    background: #f2ede3; border: 1px solid #e0d9cc; color: #4a4a4a;
}
.badge-area { color: #fff; border: none; }
.spot-photo {
    width: 100%;
    height: 160px;
    object-fit: cover;
    border-radius: 8px;
    margin-top: 10px;
}
.photo-credit {
    font-size: 0.68rem;
    color: #a0a0a0;
    margin-top: 3px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.spot-desc {
    margin-top: 10px;
    font-size: 0.85rem;
    line-height: 1.6;
    color: #5a5a5a;
}
.move-line {
    margin: -6px 0 8px 14px;
    font-size: 0.82rem;
    color: #8a8a8a;
}

/* 右カラム（地図）をスクロールに追従させる */
[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    position: sticky;
    top: 3rem;
    align-self: flex-start;
}
</style>
""", unsafe_allow_html=True)

st.title("⛩️ 鎌倉 周遊ルート最適化")
st.caption("持ち時間と好みに合わせて、満足度が最大になる順路を提案します")

df, travel, modes = load_data()

# 画像情報を読み込んでスポット名で引けるようにする
try:
    photos = pd.read_csv("photos_selected.csv").set_index("name").to_dict("index")
except FileNotFoundError:
    photos = {}

# 計算時間・開門待ちの許容は開発者向けの調整値のため、UIには出さず固定する
SEARCH_SEC = 5
MAX_WAIT = 60


def format_clock(hour):
    """9.5 -> '09:30' のような時刻表記に変換する"""
    hh = int(hour)
    mm = int(round((hour % 1) * 60))
    return f"{hh:02d}:{mm:02d}"


def format_duration(hours):
    """6.0 -> '6時間', 6.5 -> '6時間30分' のような表記に変換する"""
    hh = int(hours)
    mm = int(round((hours % 1) * 60))
    return f"{hh}時間" if mm == 0 else f"{hh}時間{mm}分"


# ---- サイドバー: 検索条件 ----
with st.sidebar:
    st.header("検索条件")

    start_hour = st.slider("出発時刻", 7.0, 12.0, 9.0, 0.5, format="%.1f時")
    st.caption(f"→ {format_clock(start_hour)}")
    hours = st.slider("持ち時間", 3.0, 10.0, 6.0, 0.5, format="%.1f時間")
    st.caption(f"→ {format_duration(hours)}")

    run = st.button("ルートを計算", type="primary", use_container_width=True)

# ---- 行きたい場所を選ぶ ----
st.subheader("行きたい場所を選ぶ")
st.caption("選んだ場所は必ずルートに含めます（未選択なら34件から自動で選びます）")

area_order = [a for a in AREA_COLORS if a not in ("起点", "昼食")]
spot_names = df.loc[df["area"].isin(area_order), "name"].tolist()

tabs = st.tabs([f"{AREA_ICONS.get(a, '📍')} {a}" for a in area_order])
for tab, area in zip(tabs, area_order):
    with tab:
        area_spots = df[df["area"] == area]
        cols = st.columns(3)
        for i, (_, r) in enumerate(area_spots.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    photo = photos.get(r["name"])
                    if photo and isinstance(photo.get("photo_url"), str):
                        st.image(photo["photo_url"], width="stretch")
                    st.checkbox(r["name"], key=f"pick_{r['name']}")

picked = [name for name in spot_names if st.session_state.get(f"pick_{name}")]
if picked:
    st.caption(f"選択中（{len(picked)}件）: " + " / ".join(picked))

work = df.copy()

# ---- 実行 ----
if not run:
    st.info("行きたい場所を選び、左のサイドバーで条件を設定して「ルートを計算」を押してください")
    st.stop()

with st.spinner("最適なルートを探しています..."):
    result, _ = solve(
        work, travel, int(hours * 60), start_hour,
        search_sec=SEARCH_SEC, max_wait=MAX_WAIT,
        must_visit=set(picked),
    )

if result is None:
    st.error("条件に合うルートが見つかりませんでした。持ち時間を延ばしてみてください。")
    st.stop()

# ---- 集計 ----
spots = result[1:]                      # 起点を除いたスポット
total_fee = sum(int(work.iloc[i]["fee"]) for i, _ in spots)
last_i, last_t = result[-1]
end_min = last_t + int(work.iloc[last_i]["stay_min"]) + travel[last_i, 0]
end_hour = start_hour + end_min / 60
stay_total = sum(int(work.iloc[i]["stay_min"]) for i, _ in spots)
move_total = int(end_min - stay_total)

# ---- サマリーカード ----
visited_areas = work.iloc[[i for i, _ in spots]]["area"].nunique()
c1, c2, c3 = st.columns(3)
cards = [
    (c1, "訪問スポット数", f"{len(spots)}件", f"{visited_areas}エリアを周遊"),
    (c2, "所要時間", f"{end_min / 60:.1f}時間",
     f"移動 {move_total}分 / 滞在 {stay_total}分"),
    (c3, "拝観料合計", f"¥{total_fee:,}",
     f"帰着 {int(end_hour):02d}:{int((end_hour % 1) * 60):02d}"),
]
for col, label, value, sub in cards:
    with col:
        st.markdown(
            f'<div class="summary-card">'
            f'<div class="summary-label">{label}</div>'
            f'<div class="summary-value">{value}</div>'
            f'<div class="summary-sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.write("")

left, right = st.columns([1, 1])

# ---- 行程（タイムライン） ----
with left:
    st.subheader("行程")

    for order, (i, t) in enumerate(result):
        r = work.iloc[i]
        hh = start_hour + t / 60
        clock = f"{int(hh):02d}:{int((hh % 1) * 60):02d}"
        color = AREA_COLORS.get(r["area"], "#5a5a5a")

        if order == 0:
            st.markdown(
                f'<div class="spot-card" style="border-left:4px solid {color}">'
                f'<div class="spot-head">'
                f'<span class="spot-num" style="background:{color}">S</span>'
                f'<span class="spot-name">{r["name"]}</span>'
                f'<span class="spot-time">{clock} 出発</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        else:
            icon = AREA_ICONS.get(r["area"], "📍")
            fee = f"¥{int(r['fee'])}" if r["fee"] else "無料"
            badges = (
                f'<span class="badge badge-area" style="background:{color}">'
                f'{r["area"]}</span>'
                f'<span class="badge">滞在 {int(r["stay_min"])}分</span>'
                f'<span class="badge">{fee}</span>'
            )
            desc = r["description"] if isinstance(r["description"], str) else ""

            # 画像とクレジット（ライセンス条件を満たすため作者名を併記する）
            photo = photos.get(r["name"])
            photo_html = ""
            if photo and isinstance(photo.get("photo_url"), str):
                credit = f'{photo["photo_artist"]} / {photo["photo_license"]}'
                photo_html = (
                    f'<img src="{photo["photo_url"]}" class="spot-photo">'
                    f'<div class="photo-credit">{credit[:70]}</div>'
                )

            st.markdown(
                f'<div class="spot-card" style="border-left:4px solid {color}">'
                f'<div class="spot-head">'
                f'<span class="spot-num" style="background:{color}">{order}</span>'
                f'<span class="spot-name">{icon} {r["name"]}</span>'
                f'<span class="spot-time">{clock}</span>'
                f'</div>'
                f'<div class="badges">{badges}</div>'
                + photo_html
                + (f'<div class="spot-desc">{desc}</div>' if desc else "")
                + f'</div>',
                unsafe_allow_html=True,
            )

        # 次のスポットへの移動を区間として挟む
        if order < len(result) - 1:
            j = result[order + 1][0]
            raw = modes[i, j]
            mins = int(round(travel[i, j]))
            if raw.startswith("鉄道"):
                st_a, st_b = raw.split(":", 1)[1].split("→")
                label = f"🚃 {rail_label(st_a, st_b)} {mins}分"
            else:
                label = f"🚶 徒歩 {mins}分"
            st.markdown(
                f'<div class="move-line">↓ {label}</div>',
                unsafe_allow_html=True,
            )

# ---- 地図 ----
with right:
    st.subheader("ルートマップ")
    coords = [(work.iloc[i]["lat"], work.iloc[i]["lon"]) for i, _ in result]

    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    m = folium.Map(tiles="cartodbpositron")
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]],
                 padding=(30, 30))

    # 区間ごとに徒歩と鉄道を描き分ける（線は実際の座標で引く）
    for k in range(len(result) - 1):
        i, j = result[k][0], result[k + 1][0]
        seg = [coords[k], coords[k + 1]]
        if modes[i, j].startswith("鉄道"):
            folium.PolyLine(seg, color="#ff9800", weight=3, opacity=0.9,
                            dash_array="8, 8", tooltip="電車").add_to(m)
        else:
            folium.PolyLine(seg, color="#5a8a7a", weight=4, opacity=0.7,
                            tooltip="徒歩").add_to(m)

    # 近接するマーカーが重ならないよう、少しずつずらして描画する
    seen = []
    for order, (i, t) in enumerate(result):
        r = work.iloc[i]
        hh = start_hour + t / 60
        clock = f"{int(hh):02d}:{int((hh % 1) * 60):02d}"
        label = f"{order if order else 'S'}. {r['name']} {clock}"
        color = AREA_COLORS.get(r["area"], "#5a5a5a")

        lat, lon = r["lat"], r["lon"]
        offset = sum(
            1 for (a, b) in seen
            if abs(a - lat) < 0.004 and abs(b - lon) < 0.004
        )
        seen.append((lat, lon))
        if offset:
            angle = offset * 2.4          # ラジアン、重なるたびに回す
            lat += 0.0022 * np.cos(angle)
            lon += 0.0022 * np.sin(angle)

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(label, max_width=220),
            tooltip=label,
            icon=folium.DivIcon(
                icon_size=(26, 26),
                icon_anchor=(13, 13),
                html=(
                    f'<div style="background:{color};'
                    f'color:#fff;border-radius:50%;width:26px;height:26px;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'font-weight:700;font-size:12px;'
                    f'border:2px solid #fff;'
                    f'box-shadow:0 2px 6px rgba(0,0,0,.3);">'
                    f'{order if order else "S"}</div>'
                ),
            ),
        ).add_to(m)

    html(m._repr_html_(), height=620)

    # エリアの凡例
    legend = " ".join(
        f'<span style="display:inline-block;margin-right:10px;font-size:0.78rem">'
        f'<span style="display:inline-block;width:10px;height:10px;'
        f'border-radius:50%;background:{c};margin-right:4px"></span>{a}</span>'
        for a, c in AREA_COLORS.items() if a != "起点"
    )
    st.markdown(legend, unsafe_allow_html=True)
    st.caption("実線＝徒歩 / オレンジの破線＝電車")

# ---- 画像の出典表示 ----
used = [work.iloc[i]["name"] for i, _ in spots
        if work.iloc[i]["name"] in photos]
if used:
    with st.expander("画像の出典"):
        st.caption("画像はすべて Wikimedia Commons より。"
                   "各ライセンスの条件に従って利用しています。")
        for name in used:
            p = photos[name]
            st.markdown(
                f"- **{name}**: {p['photo_file']} / "
                f"{p['photo_artist']} / "
                f"[{p['photo_license']}]({p['photo_license_url']})"
            )