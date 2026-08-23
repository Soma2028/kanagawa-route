"""鎌倉の周遊ルートを最適化して地図に表示するアプリ"""
import folium
import streamlit as st
from streamlit.components.v1 import html

from optimize import load_data, solve

st.set_page_config(page_title="鎌倉ルート最適化", layout="wide")
st.title("鎌倉 周遊ルート最適化")
st.caption("持ち時間と好みに合わせて、満足度が最大になる順路を提案します")

df, travel, modes = load_data()

# ---- 入力 ----
col1, col2, col3 = st.columns(3)
with col1:
    start_hour = st.slider("出発時刻", 7.0, 12.0, 9.0, 0.5)
with col2:
    hours = st.slider("持ち時間（時間）", 3.0, 10.0, 6.0, 0.5)
with col3:
    search_sec = st.selectbox("計算時間（秒）", [5, 15, 30], index=1)

areas = sorted(df[df["area"] != "起点"]["area"].unique())
picked = st.multiselect("行きたいエリア（未選択なら全域）", areas)

if picked:
    st.info(f"選択エリアのスポットを優先します: {', '.join(picked)}")

# エリア選択を好みとしてスコアに反映する
work = df.copy()
if picked:
    work.loc[~work["area"].isin(picked + ["起点"]), "score"] = 1

# ---- 実行 ----
if st.button("ルートを計算", type="primary"):
    with st.spinner("計算中..."):
        result, total = solve(
            work, travel, int(hours * 60), start_hour,
            search_sec=search_sec, max_wait=60,
        )

    if result is None:
        st.error("条件に合うルートが見つかりませんでした。持ち時間を延ばしてみてください。")
        st.stop()

    st.success(f"訪問 {len(result) - 1}件 / 満足度合計 {total}")

    left, right = st.columns([1, 1])

    # ---- 行程表 ----
    with left:
        st.subheader("行程")
        rows = []
        total_fee = 0
        for i, t in result:
            r = work.iloc[i]
            hh = start_hour + t / 60
            rows.append({
                "時刻": f"{int(hh):02d}:{int((hh % 1) * 60):02d}",
                "スポット": r["name"],
                "滞在": f"{int(r['stay_min'])}分",
                "拝観料": f"{int(r['fee'])}円" if r["fee"] else "無料",
            })
            total_fee += int(r["fee"])
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.metric("拝観料合計", f"{total_fee:,}円")

       # ---- 地図 ----
    with right:
        st.subheader("ルート")
        coords = [(work.iloc[i]["lat"], work.iloc[i]["lon"]) for i, _ in result]
        m = folium.Map(location=coords[0], zoom_start=13)

        for order, (i, t) in enumerate(result):
            r = work.iloc[i]
            hh = start_hour + t / 60
            label = f"{order}. {r['name']} {int(hh):02d}:{int((hh % 1) * 60):02d}"
            folium.Marker(
                [r["lat"], r["lon"]],
                popup=label,
                tooltip=label,
                icon=folium.Icon(
                    color="red" if order == 0 else "blue",
                    icon="flag" if order == 0 else "info-sign",
                ),
            ).add_to(m)

        # 区間ごとに徒歩と鉄道を描き分ける
        rail_used = False
        for k in range(len(result) - 1):
            i = result[k][0]
            j = result[k + 1][0]
            seg = [coords[k], coords[k + 1]]
            if modes[i, j] == "鉄道":
                rail_used = True
                folium.PolyLine(
                    seg, color="orange", weight=3, opacity=0.8,
                    dash_array="8, 8", tooltip="電車移動",
                ).add_to(m)
            else:
                folium.PolyLine(
                    seg, color="blue", weight=3, opacity=0.7, tooltip="徒歩",
                ).add_to(m)

        html(m._repr_html_(), height=520)
        st.caption("青の実線＝徒歩 / オレンジの破線＝電車"
                   + ("" if rail_used else "（このルートは全区間徒歩）"))
else:
    st.info("条件を設定して「ルートを計算」を押してください")