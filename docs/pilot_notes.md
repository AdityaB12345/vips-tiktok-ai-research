# TikTok Research API Pilot — Notes and Findings

**Date collected:** October 29, 2026 (UTC)  
**Purpose:** Test the TikTok Research API and assess whether the returned fields can support the text-based engagement-prediction and RAG-agent project.

## 1. Query and output

- **Endpoint:** TikTok Research API video query
- **Filter:** `region_code IN ["US"]` and `keyword EQ "education"`
- **Requested date range:** October 1–7, 2026 (`20261001`–`20261007`)
- **Page size:** 10 videos; **pages queried:** 2
- **Retrieved:** **20** rows, **20** unique video IDs; **0** duplicate IDs removed
- **Outputs created by script:** `data/raw/tiktok_pilot.json`, `data/processed/tiktok_pilot.csv`, and `docs/pilot_summary.txt`
- **API result:** Authentication, video retrieval, and a second page of results worked. No API error was shown in the supplied output.

## 2. Main results

| Check | Pilot result | What it suggests |
|---|---|---|
| Video descriptions | **20/20 nonempty (100%)** | Good candidate for the project's primary text representation |
| Voice-to-text transcripts | **0/20 nonempty (0%)** | Not usable in this particular pilot, despite 0% null values |
| `view_count`, `like_count`, `comment_count`, `share_count` | **20/20 populated for each** | The four core engagement/exposure measures are available in the test query |
| Creator identifiers | **18 distinct usernames across 20 videos** | Creator-disjoint splitting will matter for a larger dataset |
| Video IDs | **20 distinct IDs** | No duplicate IDs in the pilot |
| Region code | **11 `US`, 9 `us`** | Standardize capitalization in preprocessing |
| Duplicate caption text | **19 distinct descriptions across 20 videos** | Different video IDs may contain identical text; consider duplicate-text checks |

**Engagement distributions:**

| Measure | Mean | Median | Minimum | Maximum | Number equal to zero |
|---|---:|---:|---:|---:|---:|
| Views | 665.4 | 159.5 | 0 | 4,777 | 1 |
| Likes | 26.35 | 4 | 0 | 204 | 7 |
| Comments | 2.45 | 0.5 | 0 | 18 | 10 |
| Shares | 2.70 | 0 | 0 | 43 | 16 |

## 3. Manual inspection / data-quality observations

1. **All 20 posts are from October 7, 2026**, even though the requested window was October 1–7. Their `create_time` values fall between **23:57:51 and 23:59:53 UTC** (about two minutes). A few returned API pages therefore do not represent all days in a requested window; the actual collection strategy needs broader date coverage.
2. **Descriptions are available, but not always clean research text.** The sample includes lengthy captions, hashtags, promotional text, external links, and contact information. Future preprocessing should decide how to handle these while preserving meaning and avoiding unauthorized sharing of identifiers.
3. **The `education` keyword covers a wide range of topics.** It returned educational material as well as business promotions and other unrelated content. A later sampling plan should specify how topics will be represented rather than assuming the keyword creates one homogeneous category.
4. **Engagement is low and uneven in this pilot.** The median video has 159.5 views, and 16 of 20 videos have zero shares. This could make share prediction challenging, but the sample is far too small to judge model feasibility.
5. **One post has zero views.** View-normalized rates are undefined for such posts, so zero-/low-view handling must be specified before modeling.
6. **Field missingness requires two checks.** The printed missingness table shows 0% nulls for every field, but every `voice_to_text` entry is blank. Evaluate text availability using nonempty coverage as well as null percentages.
7. **Creator-level controls are not established.** The current query returned usernames, but it did not retrieve follower counts or other account-level measures. Their availability must be confirmed separately before using them in the engagement predictors.

## 4. Conclusions for the project

- **API feasibility:** A working Research API query and pagination test have been demonstrated.
- **Text input:** `video_description` looks more practical than `voice_to_text` for the initial text-only study, **provisionally**; verify with a larger, more varied approved sample.
- **Engagement outcomes:** All three intended targets (likes, comments, shares) and the exposure variable (views) were returned.
- **Model feasibility:** Not yet established. Twenty videos are insufficient for meaningful training/validation, and this pilot was concentrated in a very narrow posting period.

## 5. Proposed next steps (after professor's approval)

1. Share the API test results, code, data dictionary, and pilot summary through an approved channel, and confirm the allowed query scope before larger collection.
2. Plan sampling across multiple dates/topics and a range of account/exposure levels; avoid relying on the first two pages of a single query.
3. Confirm whether approved access permits retrieving creator-level context (especially follower counts).
4. Run a larger **approved** data-quality pilot to quantify caption length/coverage, transcript coverage, missingness, zero-view posts, and engagement distributions.
5. Decide the primary text field and finalize cleaning, train/RAG/test separation, and target definitions before training models or building the agent.

**Data handling:** These notes deliberately omit the raw video descriptions, usernames, and contact information found in posts. Retain raw records only in the approved research environment and do not commit restricted data or credentials to Git.
