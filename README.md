# TikTok Engagement Research

Research project investigating how a retrieval-augmented AI agent can augment **spoken TikTok video scripts** for three distinct engagement goals—likes, comments, and shares—while preserving the original content's meaning and important claims.

**Research question:** How do model-predicted engagement gains and content-fidelity costs differ across like, comment, and share goals when TikTok text is augmented by a RAG-based AI agent, compared with unchanged originals and fixed-prompt LLM rewrites?

**Current stage (November 2026):** Data collection and preliminary caption-data auditing completed. **Video acquisition/transcript feasibility is being tested; no transcript-based training dataset or engagement predictors have been completed.** The experiment depends on obtaining a sufficiently large, permitted, usable transcript dataset.

## Study design

1. Collect historical TikTok video metadata and observed views, likes, comments, shares, timestamps, and creator identifiers using the authorized TikTok Research API.
2. Obtain permitted video/audio or existing transcripts for matching video IDs, transcribe speech when necessary, and audit transcript coverage and accuracy.
3. Prepare transcript-based training, validation, retrieval, agent-development, and untouched final-test partitions. Keep creators separate across partitions.
4. Train and validate separate engagement predictors for likes, comments, and shares. Compare simple, context-only, and context-plus-transcript models on unseen creators. Do not treat historical correlations as causal evidence.
5. Build a RAG-based agent that retrieves relevant historical examples and rewrites spoken scripts for each engagement goal; log transformations (including SPICE-related choices).
6. Compare unchanged originals, fixed-prompt LLM rewrites, and agent revisions using **predicted engagement** and **content fidelity** (central-claim preservation, semantic similarity, contradictions, unsupported additions).

The study evaluates **model predictions**, not actual improvements in engagement following publication. Video scripts represent spoken content only; visuals, on-screen text, audio style, and creator effects remain limitations.

## Repository layout

```text
config/
  collection.json               Query fields, date windows, and pagination settings
src/
  api_collection/
    pilot.py                    Original small-scale API test
    tiktok_client.py            API authentication, tokens, requests, and retries
    collect_videos.py           Multi-window collection and JSON/CSV export
  preprocessing/
    check_data.py               Quality checks on the newest collection CSV
    preprocess.py               Provisional caption-based filtering and features
    make_splits.py              Provisional creator-disjoint caption-based splits
  transcription/
    select_video_candidates.py  Video links for manual access/speech checks (no downloads)
    transcribe_video.py         Whisper transcription of one permitted local file
docs/
  data_dictionary.md            API field definitions
  pilot_notes.md                Initial pilot observations
  preprocessing_report.md       Existing preliminary caption-data quality report
  split_report.md               Existing preliminary split report
data/                           PRIVATE; excluded from Git
  raw/                          Raw Research API JSON responses
  processed/                    API CSV exports and clean_videos.csv
  splits/                       Preliminary caption-based partition CSVs
  videos/                       Locally permitted video/audio files
  transcripts/                  Transcripts linked by video ID
.env                            Local authorized credentials (not committed)
.gitignore                      Excludes private data and credentials
requirements.txt                Core dependencies
requirements-transcription.txt  faster-whisper (optional for initial transcription test)
README.md                       Project documentation
```

`config/`, `data/`, and `docs/` remain at the **repository root**. This change reorganizes only Python code; it does not move any datasets or invalidate existing outputs. All scripts locate the project root from their own file path, so run them from the repository root using the commands below.

## Installation (PowerShell, repository root)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Only if testing local video transcription:
python -m pip install -r requirements-transcription.txt
```

For approved API collection, store project-authorized credentials only in a local, untracked `.env` file:

```dotenv
TIKTOK_CLIENT_KEY=your_authorized_key
TIKTOK_CLIENT_SECRET=your_authorized_secret
```

Never publish tokens, usernames, raw API responses, video files, transcripts, or row-level records. Confirm lab and TikTok permissions before acquiring videos in bulk or processing material outside the Research API.

## Completed: data collection and initial quality audit

```powershell
python src/api_collection/collect_videos.py
python src/preprocessing/check_data.py
python src/preprocessing/preprocess.py
python src/preprocessing/make_splits.py
```

The two principal CSV exports are:

- `data/processed/videos_20261106_031209.csv` — 3,938 records
- `data/processed/videos_20261106_033158.csv` — 1,376 records

Across 12 selected one-week windows during March–August 2026, **5,314 records** were collected (5,314 distinct video IDs within the two collections). Both have complete primary engagement count fields. Approximately **76–78%** of records had nonempty descriptions, but only **1–2%** had nonempty `voice_to_text` transcripts. Views, likes, comments, and shares were heavily skewed, with many zero-comment and zero-share posts.

`src/preprocessing/preprocess.py` merges these exports, validates IDs/creators/dates/counts, removes zero-view posts, captions under five words, non-English/undetermined longer captions, and exact duplicate captions, and creates log-count and per-view features. It produced **2,394 posts** from **2,328 creators**. Of those, **880 short captions were not reliably language-classified**.

`src/preprocessing/make_splits.py` deterministically hashes creators into **caption-based** datasets:

| Dataset | Posts | Intended use |
|---|---:|---|
| `model_train.csv` | 1,431 | Training |
| `model_val.csv` | 225 | Development validation |
| `rag.csv` | 496 | Retrieval examples |
| `agent_pilot.csv` | 108 | Agent development |
| `final_test.csv` | 134 | Held-out comparison |

**Important:** These were proof-of-pipeline outputs for caption data. They are **not** the final transcript-based splits. The transcript pipeline will need different filtering, and creator-disjoint splits must be regenerated before modeling. Original API exports are preserved.

## Next: transcript feasibility test

Use existing video IDs rather than repeating collection. The Research API's `voice_to_text` field reports pre-existing subtitles only where available; the API does not provide a general video-file download endpoint. Test one permitted spoken video before designing any large-scale acquisition method.

**1. Print candidate video links (no video download):**

```powershell
python src/transcription/select_video_candidates.py
```

Open a candidate in TikTok; check that it is accessible, substantially spoken, and has a creator-enabled **Save video** option. Follow the applicable research permissions. Do not bypass blocked downloads. Put one permitted file at `data/videos/<video_id>.mp4` (create that folder if needed).

**2. Transcribe the downloaded file:**

```powershell
python -m pip install -r requirements-transcription.txt
python src/transcription/transcribe_video.py data/videos/VIDEO_ID.mp4 --video-id VIDEO_ID
```

Replace `VIDEO_ID` with the numeric TikTok ID. For this first test, `src/transcription/transcribe_video.py` uses the Whisper `base` model on CPU and writes `data/transcripts/transcripts.csv`. It does **not** download videos or contact TikTok. The model may download its weights on first use. Inspect the output against the original audio: check if it contains meaningful English speech, whether claims are accurately captured, and whether visuals/on-screen text provide essential missing context.

**3. Establish whether collection can scale legally and practically.** Check with the lab about an already-authorized media archive, transcripts, or a permitted batch access workflow. A single successful transcription proves the *technical* step, not large-scale dataset availability.

After sufficient transcripts are available: join by `id` to the existing metadata, audit speech and text quality, update preprocessing and creator-disjoint splits for transcripts, then train engagement prediction baselines.

## Validity, privacy, and limits

- Engagement is observational; predicted changes are not evidence that a script rewrite will cause more likes, comments, or shares.
- Engagement depends on many unobserved factors, particularly video visuals, creator reputation, and distribution. Validate whether **transcript features** add predictive value over nontext context features.
- The sample covers selected US-region windows, not all TikTok videos; pagination and month distributions are uneven.
- Transcription may fail on music-only, silent, multi-speaker, multilingual, or low-quality audio. Speech transcripts omit visual and on-screen content.
- Avoid train/test leakage: use creator-disjoint partitions; reserve final evaluation data; evaluate against simple baselines and disclose model failures.
- Keep downloaded media, transcripts, account identifiers, and post-level data private and within research authorization.

## Documentation

- [TikTok Research API — Query Videos](https://developers.tiktok.com/docs/en/research-api-specs-query-videos)
- [TikTok Research API Codebook](https://developers.tiktok.com/docs/en/research-api-codebook)
- [TikTok video downloads](https://support.tiktok.com/en/using-tiktok/exploring-videos/video-downloads)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
