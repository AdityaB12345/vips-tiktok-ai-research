# TikTok Engagement Research

Research project investigating how a retrieval-augmented AI agent can revise social media text for different engagement goals while preserving the original content's meaning and important claims.

## Project overview

The study focuses on three distinct engagement goals: **likes, comments, and shares**. A single AI agent will use historical TikTok examples retrieved from a vector database to decide how to augment a source post. Its outputs will be compared with the **unchanged original** and a **fixed-prompt, non-agent LLM rewrite**.

The evaluation will consider two outcomes separately:

- **Predicted engagement:** Three supervised models will estimate likes, comments, and shares from text features and available post/account context.
- **Content fidelity:** Measures will examine whether revisions preserve central claims, meaning, and stance/intent, and whether they introduce contradictions or unsupported factual additions.

The project studies **model-predicted engagement**, not whether the rewrites actually cause more people to interact with a published post. The initial study is limited to TikTok text, with the primary text field to be selected based on data availability.

## Research workflow

The planned workflow is:

1. **Collect and validate data** through the authorized TikTok Research API.
2. **Prepare separate datasets** for engagement-model training, RAG reference examples, development/pilot testing, and final held-out evaluation.
3. **Train and validate** separate engagement predictors for likes, comments, and shares.
4. **Build the RAG-based agent** to retrieve relevant historical examples and generate goal-specific revisions.
5. **Evaluate the outputs** against the original and non-agent LLM baseline using predicted engagement and fidelity measures.

Data access, model performance, and fidelity evaluation must be validated before drawing conclusions from the final comparison.

## Repository structure

```text
src/
  pilot.py                  TikTok Research API client and initial data checks
docs/
  data_dictionary.md        Field definitions and intended research uses
  pilot_notes.md            Pilot query, observations, and limitations
  pilot_summary.txt         Automatically generated aggregate pilot statistics
data/
  raw/                      Raw API responses (not committed)
  processed/                CSV exports (not committed)
.env                        Local credentials, if permitted (not committed)
.gitignore                  Files excluded from Git
requirements.txt            Python dependencies
README.md                   Project documentation
```

Additional scripts and components will be added as the project develops.

## Setup

Use Python 3.11+ and PowerShell from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Only use credentials authorized for the approved Research API project. If the lab permits local secret storage, create a `.env` file in the repository root:

```dotenv
TIKTOK_CLIENT_KEY=your_authorized_client_key
TIKTOK_CLIENT_SECRET=your_authorized_client_secret
```

The script requests a temporary access token automatically. Do **not** commit `.env`, tokens, credentials, or restricted TikTok data.

## Run the API pilot

Review the `FIELDS` and `QUERY` settings in `src/pilot.py` before running. Use only query parameters approved for the research project.

```powershell
python src/pilot.py
```

The script authenticates, queries video metadata, handles limited pagination and temporary errors, deduplicates by video ID, and writes:

- `data/raw/tiktok_pilot.json` — API responses and query metadata
- `data/processed/tiktok_pilot.csv` — retrieved fields with extraction timestamps
- `docs/pilot_summary.txt` — record counts, missingness, text coverage, and engagement statistics

For field descriptions, see [`docs/data_dictionary.md`](docs/data_dictionary.md). For detailed pilot observations, see [`docs/pilot_notes.md`](docs/pilot_notes.md).

## Data handling

This project uses research-access data subject to TikTok and university restrictions. Raw posts may contain usernames, contact details, or other identifying information. Do not publish or commit raw data, credentials, or access tokens. Share research data only through channels approved by the lab and the project's permissions. Confirm the query scope and obtain approval before larger-scale collection.

## Current status & next steps

**Status (October 29, 2026): Initial API pilot completed.**

- Successfully queried **20 unique TikTok videos** across two API pages using a U.S.-region, `education` keyword query for October 1–7, 2026.
- All 20 returned nonempty `video_description` values and available view, like, comment, and share counts; none returned a nonempty `voice_to_text` transcript.
- The retrieved posts were concentrated in a short interval on October 7, and engagement was often low (especially shares). These 20 records are a **feasibility test**, not a representative training sample.
- The pilot script, data dictionary, and pilot notes are complete. The larger data-collection plan has not yet been finalized or approved.

**Next steps:** Share the pilot findings and proposed API usage with Professor Yaros; confirm an approved broader sampling plan and availability of creator-level metadata; then evaluate text coverage, missingness, and engagement distributions on a larger approved sample before building the models and agent.

*Update this section as the project progresses; keep the methodology, setup, and usage instructions above as stable reference information.*

## Official documentation

- [TikTok Research Tools](https://developers.tiktok.com/products/research-api/)
- [Research API — Getting Started](https://developers.tiktok.com/docs/en/research-api-get-started)
- [Research API — Query Videos](https://developers.tiktok.com/docs/en/research-api-specs-query-videos)
