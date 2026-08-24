"""主観で設定した満足度スコアを、客観指標であるWikipediaページビューと比較する

スコアは知名度と体験の質を基準に自分で設定した主観的な値（README参照）。
知名度の部分だけでもWikipediaのページビューという客観指標と相関しているか、
順位相関（Spearman）で検証し、乖離が大きいスポットを洗い出す。

半僧坊（fetch_pageviews.py で独立記事なしとして欠損扱い）は対象から除く。
"""
import matplotlib

matplotlib.rcParams["font.family"] = "Hiragino Sans"  # macOS標準の日本語フォント
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

spots = pd.read_csv("spots_master.csv")
views = pd.read_csv("pageviews.csv")

df = spots.merge(views[["name", "found", "monthly_avg"]], on="name", how="left")
missing = df[~df["found"].fillna(False)]
df = df[df["found"].fillna(False)].copy()

print(f"対象スポット数: {len(df)}件（欠損 {len(missing)}件: {', '.join(missing['name'])}）")
print()

# ---- 順位相関 ----
corr, pvalue = stats.spearmanr(df["score"], df["monthly_avg"])
print(f"Spearman順位相関: {corr:.3f}（p値 {pvalue:.3f}）")
print()

# ---- 乖離が大きいスポット ----
# パーセンタイル順位の差。正: スコアの割にページビューが少ない、負: その逆
df["score_pct"] = df["score"].rank(pct=True)
df["views_pct"] = df["monthly_avg"].rank(pct=True)
df["gap"] = df["score_pct"] - df["views_pct"]

# ---- 散布図（ページビューは値の幅が大きいため対数軸にする） ----
# 全点にラベルを付けると密集して読めなくなるため、乖離が大きい上位/下位の
# スポットだけ注記する（他の点は無地のまま）
labeled_names = set(df.nlargest(5, "gap")["name"]) | set(df.nsmallest(5, "gap")["name"])

fig, ax = plt.subplots(figsize=(9, 6.5))
ax.scatter(df["monthly_avg"], df["score"], color="#3d7a6f", alpha=0.75)
for _, row in df[df["name"].isin(labeled_names)].iterrows():
    ax.annotate(
        row["name"], (row["monthly_avg"], row["score"]),
        fontsize=8, xytext=(4, 3), textcoords="offset points",
    )
ax.set_xscale("log")
ax.set_xlabel("Wikipediaページビュー 月平均（対数軸）")
ax.set_ylabel("主観的満足度スコア（1〜10）")
ax.set_title(f"満足度スコア vs Wikipediaページビュー（Spearman相関 {corr:.2f}）")
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout()
fig.savefig("score_vs_pageviews.png", dpi=150)
print("保存しました: score_vs_pageviews.png（ラベルは乖離上位/下位5件のみ）")
print()

cols = ["name", "score", "monthly_avg", "gap"]
print("=== スコアの割に客観的関心が低いスポット（上位5件） ===")
print(df.nlargest(5, "gap")[cols].to_string(index=False))
print()

print("=== 客観的関心の割にスコアが低いスポット（上位5件） ===")
print(df.nsmallest(5, "gap")[cols].to_string(index=False))
