"""Merge two TikTok collections and create a clean, auditable caption dataset.

Run from project root: python src/preprocess.py
Requires: pandas, langdetect
Original API data and CSV files are never changed.
"""

import re
from pathlib import Path

import pandas as pd
from langdetect import DetectorFactory, LangDetectException, detect

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = [
    "videos_20261106_031209.csv",  # Original six windows
    "videos_20261106_033158.csv",  # Additional six windows
]
OUTPUT = ROOT / "data" / "processed" / "clean_videos.csv"
REPORT = ROOT / "docs" / "preprocessing_report.md"
MIN_WORDS = 5

# Make langdetect repeatable; it can be unreliable on very short captions.
DetectorFactory.seed = 0
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def normalize_text(value):
    """Normalize whitespace only; preserve hashtags, links, and punctuation."""
    return " ".join(str(value).split()) if pd.notna(value) else ""


def text_for_language_check(text):
    """Avoid using URLs and @handles as evidence for language detection."""
    without_urls = URL_RE.sub(" ", text)
    return re.sub(r"@\w+", " ", without_urls)


def language_label(text):
    text = text_for_language_check(text)
    # Very short captions are too unreliable for automatic language detection.
    if len(WORD_RE.findall(text)) < 10 or len(re.findall(r"[A-Za-z]", text)) < 40:
        return "short_unchecked"
    try:
        return detect(text)
    except LangDetectException:
        return "undetermined"


def main():
    frames = []
    for name in SOURCE_FILES:
        path = ROOT / "data" / "processed" / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing input CSV: {path}")
        frame = pd.read_csv(path, dtype={"id": "string", "username": "string"})
        frame["source_file"] = name
        frames.append(frame)
        print(f"Read {len(frame):,} rows from {name}")

    df = pd.concat(frames, ignore_index=True)
    counts = {"Total rows read": len(df)}

    # When a video was collected twice, keep its most recently extracted record.
    df["extracted_at_utc"] = pd.to_datetime(df["extracted_at_utc"], utc=True, errors="coerce")
    df = df.sort_values("extracted_at_utc").drop_duplicates("id", keep="last")
    counts["After duplicate video IDs removed"] = len(df)

    df["creator_key"] = df["username"].fillna("").str.strip().str.casefold()
    df["raw_text"] = df["video_description"].fillna("")
    df["text"] = df["raw_text"].map(normalize_text)
    df["word_count"] = df["text"].map(lambda s: len(WORD_RE.findall(text_for_language_check(s))))

    required_numbers = ["view_count", "like_count", "comment_count", "share_count", "create_time"]
    for column in required_numbers:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["created_at_utc"] = pd.to_datetime(df["create_time"], unit="s", utc=True, errors="coerce")
    valid_fields = (
        df["id"].notna() & df["id"].str.strip().ne("") & df["creator_key"].ne("")
        & df["created_at_utc"].notna()
        & df[required_numbers].notna().all(axis=1)
        & df[["view_count", "like_count", "comment_count", "share_count"]].ge(0).all(axis=1)
    )
    df = df.loc[valid_fields].copy()
    counts["After missing/invalid IDs, creators, dates, or counts removed"] = len(df)

    df = df[df["view_count"] > 0].copy()
    counts["After zero-view posts removed"] = len(df)

    df = df[df["word_count"] >= MIN_WORDS].copy()
    counts[f"After captions with fewer than {MIN_WORDS} words removed"] = len(df)

    df["language"] = df["text"].map(language_label)
    before_lang = df["language"].value_counts().to_dict()
    df = df[df["language"].isin(["en", "short_unchecked"])].copy()
    counts["After non-English/undetermined long captions removed"] = len(df)

    # Deduplicate identical captions even when posted under different video IDs.
    df["caption_key"] = df["text"].str.casefold()
    df = df.sort_values("extracted_at_utc").drop_duplicates("caption_key", keep="last")
    counts["After identical captions removed"] = len(df)

    df["region_code"] = df["region_code"].fillna("").str.upper().str.strip()
    # Numeric features for tomorrow's engagement baseline; keep zero counts.
    import numpy as np
    for field in ["view_count", "like_count", "comment_count", "share_count"]:
        df[f"log_{field}"] = np.log1p(df[field])
    for field in ["like_count", "comment_count", "share_count"]:
        df[f"{field}_per_1000_views"] = 1000 * df[field] / df["view_count"]

    df = df.sort_values(["created_at_utc", "id"]).reset_index(drop=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8")

    lines = ["# Preprocessing Report", "", "## Row counts", ""]
    lines += [f"- **{step}:** {n:,}" for step, n in counts.items()]
    lines += [
        "", "## Final dataset", "",
        f"- Unique creators: **{df['creator_key'].nunique():,}**",
        f"- English-labeled captions: **{(df['language'] == 'en').sum():,}**",
        f"- Short captions kept without reliable language classification: **{(df['language'] == 'short_unchecked').sum():,}**",
        f"- Median caption word count: **{df['word_count'].median():.0f}**" if len(df) else "- Median caption word count: N/A",
        "", "### Zero engagement (% of retained posts)", "",
    ]
    for field in ["like_count", "comment_count", "share_count"]:
        pct = 100 * df[field].eq(0).mean() if len(df) else 0
        lines.append(f"- {field}: **{pct:.1f}%**")
    lines += ["", "### Posting month", ""]
    month_counts = df["created_at_utc"].dt.strftime("%Y-%m").value_counts().sort_index()
    lines += [f"- {month}: {n:,}" for month, n in month_counts.items()]
    lines += [
        "", "## Language-detection notes", "",
        f"- Language labels before filtering: `{before_lang}`",
        "- Captions with fewer than 10 detected words or 40 ASCII letters are kept as `short_unchecked` if they meet the five-word minimum.",
        "- Automatic detection is imperfect for hashtags, mixed-language, and short captions; review a sample before making a final research claim of English-only data.",
        "", "## Limitations", "",
        "- Engagement values are historical observations, not causal effects of caption wording.",
        "- Video descriptions may include links, hashtags, and promotional text; these are preserved rather than silently stripped.",
        "- This step removes *identical* captions, not every near-duplicate or paraphrase.",
        "- Low-but-positive-view posts remain; choose any minimum-view cutoff using development data, not the final test set.",
        "- The sample is not guaranteed representative of TikTok overall.",
        "- Source posts, creator identifiers, and row-level data remain local and must not be committed to Git.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nClean posts: {len(df):,} | Creators: {df['creator_key'].nunique():,}")
    print(f"Saved: {OUTPUT}\nReport: {REPORT}")


if __name__ == "__main__":
    main()
