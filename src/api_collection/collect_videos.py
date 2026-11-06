"""Collect a bounded TikTok video sample across configured date windows.

Run from the repository root: python src/collect_videos.py
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from api_collection.tiktok_client import TikTokClient

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "collection.json"


def load_config():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not 1 <= config["max_count"] <= 100:
        raise ValueError("max_count must be between 1 and 100")
    if not 1 <= config["max_pages_per_window"] <= 10:
        raise ValueError("max_pages_per_window must be between 1 and 10")
    if "id" not in config["fields"]:
        raise ValueError("The fields list must include id")
    if not config["date_windows"]:
        raise ValueError("At least one date window is required")
    for start, end in config["date_windows"]:
        start_day = datetime.strptime(start, "%Y%m%d").date()
        end_day = datetime.strptime(end, "%Y%m%d").date()
        if not 0 <= (end_day - start_day).days <= 30:
            raise ValueError(f"Invalid window {start}–{end}: maximum 30 days")
    return config


def build_query(config, start, end):
    conditions = [{
        "operation": "IN",
        "field_name": "region_code",
        "field_values": [config["region_code"]],
    }]
    if config.get("keyword"):
        conditions.append({
            "operation": "EQ",
            "field_name": "keyword",
            "field_values": [config["keyword"]],
        })
    return {
        "query": {"and": conditions},
        "start_date": start,
        "end_date": end,
        "max_count": config["max_count"],
        "is_random": config["is_random"],
    }


def save_csv(path, records, fields):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["extracted_at_utc", *fields])
        writer.writeheader()
        for record in records:
            row = {field: record.get(field) for field in fields}
            row["id"] = str(row["id"])  # Preserve long TikTok IDs as strings.
            for name, value in row.items():
                if isinstance(value, (list, dict)):
                    row[name] = json.dumps(value, ensure_ascii=False)
            row["extracted_at_utc"] = record["_extracted_at_utc"]
            writer.writerow(row)


def main():
    config = load_config()
    client = TikTokClient()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_dir = ROOT / "data" / "raw" / f"collection_{run_id}"
    csv_dir = ROOT / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    videos_by_id = {}
    total_rows = 0
    requests_made = 0

    for window_num, (start, end) in enumerate(config["date_windows"], 1):
        body = build_query(config, start, end)
        print(f"Window {window_num}: {start}–{end}")

        for page_num in range(1, config["max_pages_per_window"] + 1):
            response = client.query_videos(config["fields"], body)
            requests_made += 1
            collected_at = datetime.now(timezone.utc).isoformat()
            data = response.get("data") or {}
            videos = data.get("videos") or []

            # Save each complete response, including its query and timestamp.
            raw_file = raw_dir / f"window_{window_num:02d}_page_{page_num:02d}.json"
            raw_file.write_text(json.dumps({
                "extracted_at_utc": collected_at,
                "request": body,
                "response": response,
            }, indent=2, ensure_ascii=False), encoding="utf-8")

            for video in videos:
                video_id = video.get("id")
                if video_id is not None and str(video_id) not in videos_by_id:
                    videos_by_id[str(video_id)] = {
                        **video, "_extracted_at_utc": collected_at,
                    }
            total_rows += len(videos)
            print(f"  Page {page_num}: {len(videos)} videos")

            if page_num == config["max_pages_per_window"] or not data.get("has_more"):
                break
            if data.get("cursor") is None or not data.get("search_id"):
                raise RuntimeError("Cannot paginate: missing cursor or search_id")
            body = {**body, "cursor": data["cursor"], "search_id": data["search_id"]}

    csv_path = csv_dir / f"videos_{run_id}.csv"
    save_csv(csv_path, videos_by_id.values(), config["fields"])
    print(f"\nAPI requests: {requests_made}")
    print(f"Returned rows: {total_rows}")
    print(f"Unique videos: {len(videos_by_id)}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved raw responses: {raw_dir}")


if __name__ == "__main__":
    main()
