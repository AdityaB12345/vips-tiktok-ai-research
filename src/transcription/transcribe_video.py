"""Transcribe one locally obtained, authorized video and save a CSV row by video ID.

Example from repository root:
  python src/transcribe_video.py data/videos/123456789.mp4 --video-id 123456789

This does not download videos or call the TikTok API. Review output for accuracy.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data/transcripts/transcripts.csv"
FIELDS = ["id", "transcript", "detected_language", "language_probability", "word_count", "model", "processed_at_utc", "media_filename"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, help="Local video/audio file, obtained with permission")
    parser.add_argument("--video-id", required=True, help="TikTok video ID from collected CSV")
    parser.add_argument("--model", default="base", help="Whisper model (base for quick test, small for improved accuracy)")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing transcript for this ID")
    args = parser.parse_args()
    media = args.media.expanduser().resolve()
    if not media.is_file():
        parser.error(f"Cannot find local media file: {media}")
    vid = str(args.video_id).strip()
    if not vid.isdecimal():
        parser.error("--video-id must be the numeric video ID from the Research API")

    if OUTPUT.is_file():
        current = pd.read_csv(OUTPUT, dtype={"id": "string"}).fillna("")
    else:
        current = pd.DataFrame(columns=FIELDS)
    if (current["id"].astype(str) == vid).any() and not args.overwrite:
        parser.error(f"ID {vid} already saved. Use --overwrite to replace it.")

    from faster_whisper import WhisperModel
    print(f"Loading Whisper model '{args.model}' on CPU (int8)...")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(media), beam_size=5, vad_filter=True)
    # Iterating is necessary: actual transcription is lazy.
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    record = {
        "id": vid,
        "transcript": transcript,
        "detected_language": info.language or "",
        "language_probability": round(float(info.language_probability), 4),
        "word_count": len(transcript.split()),
        "model": args.model,
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "media_filename": media.name,
    }
    current = current.loc[current["id"].astype(str) != vid].copy()
    updated = pd.DataFrame([record]) if current.empty else pd.concat(
        [current, pd.DataFrame([record])], ignore_index=True
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    updated[FIELDS].to_csv(OUTPUT, index=False, encoding="utf-8")
    print(f"Detected language: {record['detected_language']} (confidence {record['language_probability']})")
    print(f"Transcript ({record['word_count']} words): {transcript or '[EMPTY]'}")
    print(f"Saved: {OUTPUT}")
    print("Manually verify the audio, transcription quality, speech vs music, and meaningful claims.")
    if record["word_count"] < 20:
        print("CAUTION: Fewer than 20 words; this may not be useful as a video script.")


if __name__ == "__main__":
    main()
