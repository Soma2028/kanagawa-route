"""直線距離近似と ORS 実測値を比較して、近似の妥当性を検証する"""
import numpy as np
import pandas as pd

from travel_time import walk_min

df = pd.read_csv("spots_master.csv")
actual = pd.read_csv("walk_matrix_ors.csv", index_col=0)

n = len(df)
rows = []
for i in range(n):
    for j in range(n):
        if i >= j:                       # 対称なので片側だけ見る
            continue
        a, b = df.iloc[i], df.iloc[j]
        approx = walk_min(a["lat"], a["lon"], b["lat"], b["lon"])
        real = actual.iloc[i, j]
        if pd.isna(real):
            continue
        rows.append({
            "from": a["name"], "to": b["name"],
            "approx": round(approx, 1),
            "actual": round(real, 1),
            "diff": round(approx - real, 1),
            "ratio": round(approx / real, 2) if real > 0 else None,
        })

cmp = pd.DataFrame(rows)
cmp.to_csv("matrix_comparison.csv", index=False)

# ---- 全体傾向 ----
print(f"比較した区間数: {len(cmp)}")
print(f"近似の平均: {cmp['approx'].mean():.1f}分")
print(f"実測の平均: {cmp['actual'].mean():.1f}分")
print(f"平均誤差（近似 - 実測）: {cmp['diff'].mean():+.1f}分")
print(f"平均絶対誤差: {cmp['diff'].abs().mean():.1f}分")
print(f"相関係数: {cmp['approx'].corr(cmp['actual']):.3f}")
print()

# ---- 近似が過大だった区間 ----
print("=== 近似が過大だった区間 上位5件 ===")
print(cmp.nlargest(5, "diff")[["from", "to", "approx", "actual", "diff"]]
      .to_string(index=False))
print()

# ---- 近似が過小だった区間 ----
print("=== 近似が過小だった区間 上位5件 ===")
print(cmp.nsmallest(5, "diff")[["from", "to", "approx", "actual", "diff"]]
      .to_string(index=False))
print()

# ---- 最適な迂回係数を逆算する ----
# 現行の1.4を、実測に最も合う値に置き換えるとどうなるか
current_ratio = 1.4
best = current_ratio * cmp["actual"].sum() / cmp["approx"].sum()
print(f"現行の迂回係数: {current_ratio}")
print(f"実測に最も適合する係数: {best:.2f}")