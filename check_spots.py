"""取得したスポットデータの中身を確認する"""
import pandas as pd

df = pd.read_csv("spots_kamakura.csv")

print("総件数:", len(df))
print()
print("--- tourism ---")
print(df["tourism"].value_counts(dropna=False))
print()
print("--- historic ---")
print(df["historic"].value_counts(dropna=False))
print()
print("--- amenity ---")
print(df["amenity"].value_counts(dropna=False))
print()
print("opening_hours 有り:", df["opening_hours"].notna().sum())