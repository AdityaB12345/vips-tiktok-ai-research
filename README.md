# TikTok Engagement Research

Research project investigating whether a retrieval-augmented AI (RAG) agent can revise **spoken TikTok video scripts** for different engagement goals (likes, comments, shares) while preserving their meaning and important claims.

**Research question:** How do predicted-engagement gains and content-fidelity costs differ across like, comment, and share goals when TikTok text is augmented by a RAG-based agent, compared with the unchanged original and a fixed-prompt LLM rewrite?

**Status (November 6, 2026):** Research API collection, exploratory data-quality checks, and provisional **caption-based** preprocessing/splitting are complete. The next step is deciding how to acquire enough **video transcripts**. No transcript-based dataset, engagement predictors, or agent has been completed.

## Research design

1. Collect historical TikTok data and observed views, likes, comments, and shares using authorized Research API access.
2. Obtain meaningful English-language **spoken-video transcripts**, joined to video IDs and engagement metrics. The acquisition method is not yet finalized (see below).
3. Prepare cleaned, creator-disjoint resources for predictor training, validation, RAG retrieval, agent development, and held-out final evaluation.
4. Train and validate separate predictors for likes, comments, and shares; compare simple, metadata-only, and metadata-plus-transcript baselines.
5. Build a RAG-based agent that retrieves similar posts, revises scripts for each engagement goal, and logs transformations inspired by the Digital Engagement Model's SPICE framework.
6. Compare the unchanged original, fixed-prompt LLM rewrite, and RAG-agent output using **predicted engagement** and **content fidelity** (central-claim preservation, semantic similarity, contradiction/unsupported-claim checks).

The experiment concerns **model-predicted** engagement, not causally demonstrated changes in human engagement. Spoken transcripts do not describe every visual or on-screen element of a video.

## Repository layout

```text
config/
  collection.json                    API query settings
src/
  api_collection/
    pilot.py                          Initial Research API feasibility test
    tiktok_client.py                  Authentication, requests, retries
    collect_videos.py                 Multi-window paginated collection
  preprocessing/
    check_data.py                     Statistics on most recent collection CSV
    preprocess.py                     Provisional CAPTION cleaning and features
    make_splits.py                    Provisional caption-based creator splits
  transcription/
    select_video_candidates.py        Prints sample video URLs; no downloading
    transcribe_video.py               Whisper on ONE locally supplied media file

docs/
  data_dictionary.md
  pilot_notes.md
  preprocessing_report.md             Preliminary caption filtering results
  split_report.md                     Preliminary caption split results

data/                                   PRIVATE: do not commit
  raw/                                 Saved Research API responses
  processed/                           Collected CSVs, provisional caption CSV
  splits/                              Provisional caption-based split CSVs
  videos/                              Only appropriately obtained media, if any
  transcripts/                         Future transcript files
.env                                   Local research credentials (untracked)
.gitignore
requirements.txt
requirements-transcription.txt        Optional faster-whisper dependency
README.md
```

The `src/transcription/` scripts are **exploratory**, not a completed large-scale transcript acquisition solution. No automatic TikTok downloader is part of the approved workflow at present.

## Environment and collection

From the project root (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Store project-authorized `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` in a local, ignored `.env` file. Do not commit credentials or row-level research data.

```powershell
python src/api_collection/pilot.py
python src/api_collection/collect_videos.py
python src/preprocessing/check_data.py
```

Collection is configured in `config/collection.json`. The two completed main exports are:

- `data/processed/videos_20261106_031209.csv` — **3,938** records
- `data/processed/videos_20261106_033158.csv` — **1,376** records

The data cover **12 selected seven-day windows** in March–August 2026 (days 1–7 and 15–21 of each month), filtered to **US-region accounts**. The two runs used non-random pagination, up to 100 records per page, and page limits of 10 and 5 respectively. Returned responses were saved as timestamped JSON and CSV files. These are **not** a random or representative sample of all TikTok videos.

## Data quality and exploratory preprocessing

The combined exports contain **5,314 distinct video IDs**. View, like, comment, and share fields were populated in both collections; observed engagement is highly skewed, with many zeros for comments and shares. Nonempty descriptions covered approximately **76–78%**, but `voice_to_text` covered only **1.4–1.8%** (approximately **80 transcripts** total, before evaluating language/content quality).

```powershell
python src/preprocessing/preprocess.py
python src/preprocessing/make_splits.py
```

These scripts were run **on captions**, to validate data-cleaning and leakage-control logic. They produced **2,394 posts from 2,328 creators**, then the following partitions:

| Dataset | Posts | Purpose |
|---|---:|---|
| `model_train.csv` | 1,431 | Predictor training |
| `model_val.csv` | 225 | Predictor validation |
| `rag.csv` | 496 | Retrieval references |
| `agent_pilot.csv` | 108 | Agent development |
| `final_test.csv` | 134 | Held-out evaluation |

`preprocess.py` combines CSVs, deduplicates video IDs, validates identifiers/engagement/timestamps, removes zero-view posts and captions under five words, applies a cautious language filter, deduplicates identical captions, and calculates log-count and per-view variables. **880 retained short captions were not reliably language classified.** `make_splits.py` hashes creator IDs deterministically so a creator remains in only one partition and checks for duplicate-record overlap.

**These files are not the final experiment data.** Do not train transcript-based predictors or conduct final evaluations on these caption-based splits; regenerate them after selecting a transcript source and eligibility rules. The original API datasets have not been modified.

## Transcript acquisition: unresolved method choice

TikTok Research API `voice_to_text` includes existing subtitles/voice-to-text **only for videos with that feature available**. It does not return media files for arbitrary video IDs. Two options are under review:

**A. API-only collection (preferred to investigate first).** Increase collection within the approved scope, using existing `voice_to_text` records. Conduct a small method comparison of (i) a random-order sample and (ii) targeted queries for longer, speech-oriented posts. Compare transcript-available vs unavailable videos using observed metadata such as duration, views, engagement, posting month, hashtags, and creator information. Even with checks, availability may be systematically biased; document sample restrictions and actual inclusion rates. In prior runs, `is_random=true` did not return usable pagination fields, while `is_random=false` did.

**B. Authorized video/audio acquisition plus automatic speech recognition.** If the lab and applicable platform permissions explicitly permit media retrieval, obtain permitted videos/audio, transcribe with Whisper, and join transcripts by video ID. No automatic video acquisition is implemented yet; `select_video_candidates.py` only prints links, and `transcribe_video.py` only processes a local file supplied to it. Do not use automated third-party download services without confirming authorization.

**Decision pending discussion with the instructor.** No large-scale transcription or new predictor training is scheduled until we establish a feasible and approved transcript supply. If neither option yields enough usable text, the study method and research scope will need instructor review.

## Next steps

1. Ask the instructor to confirm approved API collection volume and whether any separate automated video/audio retrieval for research is authorized.
2. If Option A is appropriate, implement a limited targeted-versus-random API sampling check and compare transcript availability; preserve raw records and record exact inclusion rules.
3. Choose the authorized source, then build transcript-specific cleaning and creator-disjoint splits.
4. Train and validate likes/comments/shares baselines, and only then build the RAG agent and final evaluation.

## Research ethics and limitations

- Keep identifiers, raw data, downloaded media, and transcripts within the project's authorized storage/sharing rules; do not publish row-level data or credentials.
- Transcript availability may select for particular topics, creators, or types of videos, and cannot be assumed missing at random.
- Transcript-only predictors omit visuals, music, delivery, and on-screen text; distinguish text contribution from view-count and metadata effects.
- Engagement labels are observational, and differences between model predictions for rewritten scripts do not establish causal effects.
- Reserve final-test data; validate predictors on unseen creators and report poor performance rather than assuming the evaluation instrument is reliable.

## Official references

- [Research API — Query Videos](https://developers.tiktok.com/docs/en/research-api-specs-query-videos)
- [Research API — Codebook](https://developers.tiktok.com/docs/en/research-api-codebook)
- [Research API — FAQs and quota](https://developers.tiktok.com/docs/en/research-api-faq)
- [faster-whisper project](https://github.com/SYSTRAN/faster-whisper)
