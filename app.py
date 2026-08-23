"""鎌倉の周遊ルートを最適化して地図に表示するアプリ"""
import folium
import streamlit as st
from streamlit.components.v1 import html

from optimize import load_data, solve

st.set_page_config(page_title="鎌倉ルート最適化", page_icon="⛩️", layout="wide")

# ---- スタイル ----
st.markdown("""
<style>
.summary-card {
    background: #ffffff0d;
    border: 1px solid #ffffff26;
    border-radius: 12px;
    padding: 18px 20px;
    height: 100%;
}
.summary-label { font-size: 0.85rem; opacity: 0.7; margin-bottom: 6px; }
.summary-value { font-size: 1.9rem; font-weight: 700; line-height: 1.2; }
.summary-sub { font-size: 0.8rem; opacity: 0.6; margin-top: 4px; }

.spot-card {
    background: #ffffff0d;
    border: 1px solid #ffffff26;
    border-left: 4px solid #4a9d8f;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.spot-head { display: flex; align-items: baseline; gap: 10px; }
.spot-num {
    background: #4a9d8f; color: #fff; border-radius: 50%;
    width: 26px; height: 26px; display: inline-flex;
    align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
}
.spot-name { font-size: 1.15rem; font-weight: 700; }
.spot-time { font-size: 0.9rem; opacity: 0.7; margin-left: auto; }
.badges { margin-top: 10px; }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.78rem; margin-right: 6px; margin-bottom: 4px;
    background: #ffffff1a; border: 1px solid #ffffff26;
}
.badge-move { background: #ff980026; border-color: #ff980055; }
</style>
""", unsafe_allow_html=True)

st.title("⛩️ 鎌倉 周遊ルート最適化")
st.caption("持ち時間と好みに合わせて、満足度が最大になる順路を提案します")

df, travel, modes = load_data()

# ---- サイドバー: 検索条件 ----
with st.sidebar:
    st.header("検索条件")

    start_hour = st.slider("出発時刻", 7.0, 12.0, 9.0, 0.5,
                           format="%.1f時")
    hours = st.slider("持ち時間", 3.0, 10.0, 6.0, 0.5,
                      format="%.1f時間")

    areas = sorted(df[df["area"] != "起点"]["area"].unique())
    picked = st.multiselect("行きたいエリア", areas,
                            help="未選択なら全域から選びます")

    with st.expander("詳細設定"):
        search_sec = st.selectbox("計算時間（秒）", [5, 15, 30], index=1)
        max_wait = st.slider("開門待ちの許容", 0, 90, 60, 15,
                             format="%d分")

    run = st.button("ルートを計算", type="primary", use_container_width=True)

# エリア選択を好みとしてスコアに反映する
work = df.copy()
if picked:
    work.loc[~work["area"].isin(picked + ["起点"]), "score"] = 1

# ---- 実行 ----
if not run:
    st.info("左のサイドバーで条件を設定して「ルートを計算」を押してください")
    st.stop()

with st.spinner("最適なルートを探しています..."):
    result, total = solve(
        work, travel, int(hours * 60), start_hour,
        search_sec=search_sec, max_wait=max_wait,
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
c1, c2, c3 = st.columns(3)
cards = [
    (c1, "満足度スコア", f"{total}", f"訪問 {len(spots)}件"),
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

        if order == 0:
            st.markdown(
                f'<div class="spot-card" style="border-left-color:#e74c3c">'
                f'<div class="spot-head">'
                f'<span class="spot-num" style="background:#e74c3c">S</span>'
                f'<span class="spot-name">{r["name"]}</span>'
                f'<span class="spot-time">{clock} 出発</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        else:
            fee = f"¥{int(r['fee'])}" if r["fee"] else "無料"
            badges = (
                f'<span class="badge">スコア {int(r["score"])}</span>'
                f'<span class="badge">滞在 {int(r["stay_min"])}分</span>'
                f'<span class="badge">{fee}</span>'
                f'<span class="badge">{r["area"]}</span>'
            )
            st.markdown(
                f'<div class="spot-card">'
                f'<div class="spot-head">'
                f'<span class="spot-num">{order}</span>'
                f'<span class="spot-name">{r["name"]}</span>'
                f'<span class="spot-time">{clock}</span>'
                f'</div>'
                f'<div class="badges">{badges}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # 次のスポットへの移動を区間として挟む
        if order < len(result) - 1:
            j = result[order + 1][0]
            mode = "🚃 電車" if modes[i, j] == "鉄道" else "🚶 徒歩"
            mins = int(round(travel[i, j]))
            st.markdown(
                f'<div style="margin:-6px 0 8px 14px; font-size:0.82rem; '
                f'opacity:0.65;">↓ {mode} {mins}分</div>',
                unsafe_allow_html=True,
            )

# ---- 地図 ----
with right:
    st.subheader("ルートマップ")
    coords = [(work.iloc[i]["lat"], work.iloc[i]["lon"]) for i, _ in result]

    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    m = folium.Map(tiles="cartodbpositron")
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(30, 30))

    for order, (i, t) in enumerate(result):
        r = work.iloc[i]
        hh = start_hour + t / 60
        clock = f"{int(hh):02d}:{int((hh % 1) * 60):02d}"
        label = f"{order if order else 'S'}. {r['name']} {clock}"
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(label, max_width=200),
            tooltip=label,
            icon=folium.DivIcon(html=(
                f'<div style="background:{"#e74c3c" if order == 0 else "#4a9d8f"};'
                f'color:#fff;border-radius:50%;width:28px;height:28px;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-weight:700;font-size:13px;'
                f'box-shadow:0 2px 6px rgba(0,0,0,.35);">'
                f'{order if order else "S"}</div>'
            )),
        ).add_to(m)

    # 区間ごとに徒歩と鉄道を描き分ける
    for k in range(len(result) - 1):
        i, j = result[k][0], result[k + 1][0]
        seg = [coords[k], coords[k + 1]]
        if modes[i, j] == "鉄道":
            folium.PolyLine(seg, color="#ff9800", weight=3, opacity=0.9,
                            dash_array="8, 8", tooltip="電車").add_to(m)
        else:
            folium.PolyLine(seg, color="#4a9d8f", weight=4, opacity=0.8,
                            tooltip="徒歩").add_to(m)

    html(m._repr_html_(), height=620)
    st.caption("緑の実線＝徒歩 / オレンジの破線＝電車")