from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
files = list((ROOT / "data" / "processed").glob("videos_*.csv"))
path = max(files, key=lambda p: p.stat().st_mtime)

df = pd.read_csv(path, dtype={"id": "string"})

print("File:", path.name)
print("Total videos:", len(df))
print("Unique videos:", df["id"].nunique())
print("Unique creators:", df["username"].nunique())

print("\nMissingness (%):")
print((df.isna().mean() * 100).round(2))

print("\nText coverage (%):")
for col in ["video_description", "voice_to_text"]:
    coverage = df[col].fillna("").str.strip().ne("").mean() * 100
    print(f"{col}: {coverage:.1f}%")

metrics = ["view_count", "like_count", "comment_count", "share_count"]

print("\nEngagement statistics:")
print(df[metrics].describe())

print("\nZero counts (%):")
print(((df[metrics] == 0).mean() * 100).round(2))

dates = pd.to_datetime(df["create_time"], unit="s", utc=True)
print("\nVideos by month:")
print(dates.dt.to_period("M").value_counts().sort_index())