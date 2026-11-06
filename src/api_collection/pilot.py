import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
key = os.getenv('TIKTOK_CLIENT_KEY')
secret = os.getenv('TIKTOK_CLIENT_SECRET')
if not key or not secret:
    raise SystemExit('Missing TIKTOK_CLIENT_KEY or TIKTOK_CLIENT_SECRET in .env')

FIELDS = [
    'id', 'video_description', 'voice_to_text', 'create_time',
    'region_code', 'username', 'view_count', 'like_count',
    'comment_count', 'share_count', 'hashtag_names', 'video_duration',
]
QUERY = {
    'query': {'and': [
        {'operation': 'IN', 'field_name': 'region_code', 'field_values': ['US']},
        {'operation': 'EQ', 'field_name': 'keyword', 'field_values': ['education']},
    ]},
    'start_date': '20261001',
    'end_date': '20261007',
    'max_count': 10,
}

session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=Retry(
    total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(['POST']), respect_retry_after_header=True,
)))

response = session.post(
    'https://open.tiktokapis.com/v2/oauth/token/',
    data={'client_key': key, 'client_secret': secret, 'grant_type': 'client_credentials'},
    timeout=30,
)
response.raise_for_status()
token = response.json().get('access_token')
if not token:
    raise RuntimeError('Token request failed; inspect error code without exposing credentials')
print('Token acquired (not displayed).')

pages = []
all_videos = []
body = QUERY.copy()
for page_num in range(2):  # Small pilot: at most 20 returned videos
    response = session.post(
        'https://open.tiktokapis.com/v2/research/video/query/',
        params={'fields': ','.join(FIELDS)},
        headers={'Authorization': f'Bearer {token}'},
        json=body,
        timeout=30,
    )
    response.raise_for_status()
    page = response.json()
    error = page.get('error') or {}
    if error.get('code') not in (None, 'ok', 0):
        raise RuntimeError(f"TikTok API error: {error.get('code')}: {error.get('message')}")
    pages.append(page)
    data = page.get('data') or {}
    videos = data.get('videos') or []
    all_videos.extend(videos)
    print(f'Page {page_num + 1}: {len(videos)} videos')
    if not data.get('has_more'):
        break
    if data.get('cursor') is None or not data.get('search_id'):
        raise RuntimeError('Pagination indicated more results but cursor/search_id was missing')
    body = {**QUERY, 'cursor': data['cursor'], 'search_id': data['search_id']}

raw_dir = ROOT / 'data' / 'raw'
out_dir = ROOT / 'data' / 'processed'
docs_dir = ROOT / 'docs'
for folder in (raw_dir, out_dir, docs_dir):
    folder.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc).isoformat()
(raw_dir / 'tiktok_pilot.json').write_text(
    json.dumps({'extracted_at_utc': now, 'query': QUERY, 'pages': pages}, indent=2),
    encoding='utf-8',
)

df = pd.DataFrame(all_videos)
for field in FIELDS:
    if field not in df:
        df[field] = None
num_before = len(df)
df = df.drop_duplicates(subset='id')
df.insert(0, 'extracted_at_utc', now)
df[['extracted_at_utc', *FIELDS]].to_csv(out_dir / 'tiktok_pilot.csv', index=False)

metrics = ['view_count', 'like_count', 'comment_count', 'share_count']
report = [f'Queried: {QUERY}', f'Pages: {len(pages)}',
          f'Rows returned: {num_before}', f'Unique videos: {len(df)}',
          f'Duplicates removed: {num_before - len(df)}',
          '', 'Missingness (%)',
          df[FIELDS].isna().mean().mul(100).round(1).to_string(),
          '', 'Text coverage (%)']
for field in ('video_description', 'voice_to_text'):
    nonempty = df[field].fillna('').astype(str).str.strip().ne('').mean() * 100 if len(df) else 0
    report.append(f'{field}: {nonempty:.1f}%')
report += ['', 'Engagement summary',
           df[metrics].apply(pd.to_numeric, errors='coerce').describe().to_string()]
(docs_dir / 'pilot_summary.txt').write_text('\n'.join(report), encoding='utf-8')
print('\n'.join(report))
print('\nSaved JSON, CSV, and report.')
