# TikTok Research API Pilot — Data Dictionary

**Pilot:** 20 unique videos collected on October 29, 2026 (UTC)  
**API query:** U.S. region (`region_code = US`), keyword `education`, videos dated October 1–7, 2026  
**Source:** TikTok Research API video-query response, saved as `data/processed/tiktok_pilot.csv`  
**Purpose:** Identify usable text, engagement outcomes, and context variables for the proposed engagement-prediction and RAG-agent study.

## Collected fields

| Field | Data type | Meaning / intended use | Findings from this pilot |
|---|---|---|---|
| `extracted_at_utc` | UTC timestamp (ISO 8601 string) | Date/time the API response was collected; useful because counts can change | Populated for all 20 records |
| `id` | Video ID (preserve as **string**) | Unique video identifier; deduplication and tracking | 20 unique IDs; no duplicate IDs |
| `video_description` | Text/string | Video caption/description; **candidate primary text input** for agent, RAG, and ML text features | 0% null; **100% nonempty** |
| `voice_to_text` | Text/string | Optional transcript; alternative candidate text input | 0% null but **0% nonempty** (all blank) |
| `create_time` | Unix timestamp (seconds) | Posting time; potential temporal/context feature | Populated for all 20; all dates are October 7, 2026 (UTC) |
| `region_code` | Categorical string | Region code returned by TikTok; query filter/context | Populated; 11 `US` and 9 `us` (normalize case when cleaning) |
| `username` | String | Creator identifier; useful for checking repeated creators and creator-disjoint data splits | Populated; 18 distinct usernames across 20 videos. Avoid exposing identifiers in reports |
| `view_count` | Integer count | Exposure/context variable; also denominator for descriptive engagement rates | 0% null; median **159.5**; range **0–4,777**; one zero-view video |
| `like_count` | Integer count | **Likes prediction target** | 0% null; median **4**; range **0–204**; 7 zero-like videos |
| `comment_count` | Integer count | **Comments prediction target** | 0% null; median **0.5**; range **0–18**; 10 zero-comment videos |
| `share_count` | Integer count | **Shares prediction target** | 0% null; median **0**; range **0–43**; 16 zero-share videos |
| `hashtag_names` | List of strings (stored as text in CSV) | Candidate topic/content feature or sampling-strata information | No nulls reported, but some rows have empty lists; parse lists before analysis |
| `video_duration` | Numeric, seconds | Video-length/context feature | Populated in all 20 records |

**Missingness note:** The script's missingness report uses null checks (`isna`). An empty string is *not* considered missing by that check. This is why `voice_to_text` reports 0% null values while its usable text coverage is 0%. For future data checks, evaluate both nullness and nonempty coverage for text fields.

## Possible derived fields (not yet created)

| Derived field | Definition / purpose |
|---|---|
| `description_nonempty` | Whether `video_description` contains non-whitespace text |
| `transcript_nonempty` | Whether `voice_to_text` contains non-whitespace text |
| `description_length` | Number of words or characters in the selected text field; content feature |
| `create_date_utc` | Date converted from `create_time` for date checks and time-based splits |
| `region_code_normalized` | `region_code` converted to a consistent case |
| `likes_per_1000_views`, `comments_per_1000_views`, `shares_per_1000_views` | `1000 × interaction_count / view_count` for **positive** view counts; descriptive engagement rates, not finalized model targets |

## Variables not obtained in this pilot

Creator-level measures such as `follower_count`, account popularity, and verification status were **not requested or retrieved** in this video query. Their availability through a separately authorized user-info workflow must be confirmed before using them as model controls. Likewise, the pilot did not establish whether transcripts can be obtained for other topics or time periods.

## Use and limitations

The 20 videos are only an API functionality/data-feasibility pilot, **not** a representative training dataset. The proposed project will model **predicted** likes, comments, and shares separately; observed historical counts do not establish the causal effect of rewriting content. `view_count` is an exposure/context measure, not a direct measure of content quality or attention. Follow the project's approved storage/sharing rules; captions can contain contact details and other identifying information.
