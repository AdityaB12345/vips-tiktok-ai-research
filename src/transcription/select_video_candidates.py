"""Print candidate TikTok video links from the two authorized Research API CSV exports.

Run from the repository root: python src/select_video_candidates.py
This script does not download or access any TikTok videos.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    ROOT / "data/processed/videos_20261106_031209.csv",
    ROOT / "data/processed/videos_20261106_033158.csv",
]


def main():
    frames = []
    for path in SOURCES:
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}. Check your filenames.")
        frames.append(pd.read_csv(path, dtype={"id": "string", "username": "string"}))
    df = pd.concat(frames, ignore_index=True).drop_duplicates("id", keep="last")
    df["video_duration"] = pd.to_numeric(df["video_duration"], errors="coerce")
    df["view_count"] = pd.to_numeric(df["view_count"], errors="coerce")
    candidates = df.loc[
        df["id"].notna()
        & df["username"].notna()
        & df["video_duration"].between(20, 180)
        & df["view_count"].gt(0)
    ]
    if candidates.empty:
        raise SystemExit("No candidates matched the duration/view filters.")
    sample = candidates.sample(n=min(12, len(candidates)), random_state=42)
    print("Check a few candidates. Choose ONE with speech and an allowed download.\n")
    for _, row in sample.iterrows():
        handle = row["username"].strip().lstrip("@")
        vid = row["id"]
        caption = " ".join(str(row.get("video_description", "")).split())
        caption = caption[:95] + ("..." if len(caption) > 95 else "")
        print(f"{vid} | {int(row['video_duration'])} sec | {int(row['view_count'])} views")
        print(f"https://www.tiktok.com/@{handle}/video/{vid}")
        print(f"Description: {caption}\n")
    print("For a permitted download, rename the file to <video_id>.mp4 and put it in data/videos/.")


if __name__ == "__main__":
    main()
