"""Make reproducible creator-disjoint splits for the ML models and RAG agent.

Run from project root: python src/make_splits.py
Expects data/processed/clean_videos.csv from preprocess.py.
"""

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "processed" / "clean_videos.csv"
OUT_DIR = ROOT / "data" / "splits"
REPORT = ROOT / "docs" / "split_report.md"
SEED = "vips2026_split_v1"

# Fraction of unique creators assigned to each resource.
SPLITS = [
    ("model_train", 0.60),
    ("model_val", 0.10),
    ("rag", 0.20),
    ("agent_pilot", 0.05),
    ("final_test", 0.05),
]


def assign_split(creator):
    # Hashing is deterministic and guarantees each creator stays in one split.
    digest = hashlib.sha256(f"{SEED}:{creator}".encode("utf-8")).hexdigest()
    fraction = int(digest[:12], 16) / (16**12)
    cumulative = 0.0
    for name, weight in SPLITS:
        cumulative += weight
        if fraction < cumulative:
            return name
    return SPLITS[-1][0]


def main():
    if not INPUT.exists():
        raise FileNotFoundError("Run python src/preprocess.py first.")
    df = pd.read_csv(INPUT, dtype={"id": "string", "username": "string", "creator_key": "string"})
    if df.empty:
        raise ValueError("Clean dataset is empty. Check preprocessing report.")
    df["split"] = df["creator_key"].map(assign_split)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    # Verify no creator, video ID, or identical caption appears across splits.
    for column in ["creator_key", "id", "caption_key"]:
        overlaps = df.groupby(column)["split"].nunique().gt(1).sum()
        if overlaps:
            raise RuntimeError(f"Leakage: {overlaps} {column} values appear in multiple splits")

    rows = ["# Dataset Split Report", "", "Split assignments are **creator-disjoint** and deterministic.", ""]
    rows += ["| Split | Posts | Creators | Zero comments | Zero shares |", "|---|---:|---:|---:|---:|"]
    for name, _ in SPLITS:
        part = df[df["split"] == name].copy()
        if part.empty:
            raise ValueError(f"Split {name} is empty. Collect more data or revise proportions.")
        part.drop(columns=["split"]).to_csv(OUT_DIR / f"{name}.csv", index=False, encoding="utf-8")
        zero_comments = 100 * part["comment_count"].eq(0).mean()
        zero_shares = 100 * part["share_count"].eq(0).mean()
        rows.append(f"| {name} | {len(part):,} | {part['creator_key'].nunique():,} | {zero_comments:.1f}% | {zero_shares:.1f}% |")
        print(f"{name:12s} {len(part):>5,} posts | {part['creator_key'].nunique():>5,} creators")
    rows += [
        "", "## Checks", "",
        "- No creator, video ID, or identical caption occurs across partitions.",
        "- Model training/validation and RAG reference posts are separate.",
        "- `agent_pilot` is for prompt/agent development; `final_test` remains untouched until evaluation.",
        "- Splits are creator-disjoint but **not explicitly time-ordered**; consider a time-aware sensitivity check later.",
        "- Near-duplicate captions with small wording differences are not automatically detected.",
        "- All split CSV files contain restricted row-level research data and must remain private.",
    ]
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"\nSaved files to: {OUT_DIR}\nReport: {REPORT}")


if __name__ == "__main__":
    main()
