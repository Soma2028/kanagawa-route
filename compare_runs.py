"""同一条件で複数回解いて、解のばらつきを確認する"""
import numpy as np
import pandas as pd

from optimize import load_data, solve

BUDGET_MIN = 360
START_HOUR = 9.0
N_TRIALS = 10

df, travel, modes = load_data()

for sec in (5, 15, 30):
    scores = []
    for _ in range(N_TRIALS):
        result, total = solve(df, travel, BUDGET_MIN, START_HOUR,
                              search_sec=sec, max_wait=60)
        scores.append(total if total else 0)
    s = pd.Series(scores)
    print(f"計算時間 {sec}秒 / {N_TRIALS}回試行")
    print(f"  平均 {s.mean():.1f} / 最大 {s.max()} / 最小 {s.min()} "
          f"/ 標準偏差 {s.std():.1f}")
    print(f"  全結果: {sorted(scores, reverse=True)}")
    print()