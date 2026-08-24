"""画像候補を一覧表示して、スポットごとに1枚選ぶための補助ツール"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="画像選別", layout="wide")
st.title("画像候補の選別")
st.caption("各スポットで使う1枚を選び、最後にCSVへ書き出します")

cand = pd.read_csv("photo_candidates.csv")
names = cand["name"].unique()

if "picked" not in st.session_state:
    st.session_state.picked = {}

st.write(f"選択済み: {len(st.session_state.picked)} / {len(names)}")

for name in names:
    rows = cand[cand["name"] == name].reset_index(drop=True)
    st.subheader(name)

    cols = st.columns(len(rows) + 1)
    for k, r in rows.iterrows():
        with cols[k]:
            st.image(r["url"], use_container_width=True)
            st.caption(f"{r['license']}")
            st.caption(f"{r['artist'][:40]}")
            if st.button("これにする", key=f"{name}_{k}"):
                st.session_state.picked[name] = r.to_dict()

    with cols[-1]:
        if st.button("使わない", key=f"{name}_skip"):
            st.session_state.picked[name] = None

    chosen = st.session_state.picked.get(name, "未選択")
    if chosen is None:
        st.info("この スポットは画像なし")
    elif isinstance(chosen, dict):
        st.success(f"選択中: {chosen['file']}")

    st.divider()

if st.button("選択結果をCSVに保存", type="primary"):
    rows = []
    for name, info in st.session_state.picked.items():
        if info is None:
            continue
        rows.append({
            "name": name,
            "photo_url": info["url"],
            "photo_artist": info["artist"],
            "photo_license": info["license"],
            "photo_license_url": info["license_url"],
            "photo_file": info["file"],
        })
    pd.DataFrame(rows).to_csv("photos_selected.csv", index=False)
    st.success(f"保存しました: {len(rows)}件 → photos_selected.csv")