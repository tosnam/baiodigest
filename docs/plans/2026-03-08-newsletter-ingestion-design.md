# Newsletter Ingestion Design

**Date:** 2026-03-08

**Goal:** Add email-based newsletter ingestion for Nature and Science while keeping the existing PubMed pipeline intact, then replace the home page archive preview area with separate newsletter sections.

## Scope

- Keep the current PubMed API ingestion, filtering, summarization, and static site generation flow unchanged.
- Add a separate newsletter ingestion pipeline that reads Gmail messages for Nature and Science newsletters.
- Render newsletters as separate sections and pages, not mixed into the paper digest feed.
- Only ingest new incoming emails going forward; no historical backfill.
- Use Gmail API, not IMAP.

## Architecture

The system remains split into two independent content pipelines:

1. `PubMed pipeline`
   - Continues to fetch papers from PubMed via API.
   - Produces daily digest JSON files and existing paper digest pages.

2. `Newsletter pipeline`
   - Reads Gmail messages that were pre-labeled in Gmail.
   - Parses newsletter HTML into normalized issue data.
   - Summarizes each issue.
   - Produces newsletter JSON files and newsletter-specific static pages.

The static site generator becomes a composition layer that reads both data sets and renders them side by side while preserving their distinct UI and navigation.

## Gmail Ingestion Strategy

Recommended approach: label-based Gmail polling.

- Create Gmail labels such as:
  - `baiodigest/nature`
  - `baiodigest/science`
- Configure Gmail filters so matching incoming messages are labeled automatically.
- Poll Gmail API on schedule using those labels plus a recency or checkpoint boundary.
- Use `gmail.readonly` scope only.

This avoids brittle app-side sender/subject matching and keeps classification logic in Gmail, where it is easier to adjust without code changes.

## Data Model

Newsletter content should not be forced into the existing `Paper` or `DailyDigest` models. Add a separate model family.

### Suggested models

`NewsletterSource`
- `nature`
- `science`

`NewsletterItem`
- `title`
- `url`
- `snippet`
- `section_name`

`NewsletterSection`
- `heading`
- `items`

`NewsletterSummary`
- `overview`
- `highlights`
- `significance`

`NewsletterIssue`
- `source`
- `newsletter_name`
- `message_id`
- `thread_id`
- `received_at`
- `published_at`
- `title`
- `canonical_url`
- `html_body`
- `text_body`
- `sections`
- `summary`
- `raw_metadata`
- `schema_version`
- `generated_at`

## Storage Layout

Keep paper and newsletter storage distinct.

- Existing paper digests:
  - `data/YYYY-MM-DD.json`
- New newsletter issues:
  - `data/newsletters/nature/<message-id>.json`
  - `data/newsletters/science/<message-id>.json`

This isolates newsletter parsing changes from paper digest stability and makes debugging easier.

## Processing Flow

1. Run newsletter fetch command.
2. Query Gmail API for new messages with the configured source label.
3. Skip any message whose Gmail `message_id` is already stored.
4. Read the full payload and extract HTML or text content.
5. Route the message to a source-specific parser for Nature or Science.
6. Normalize sections, article links, and snippets into `NewsletterIssue`.
7. Send normalized content to the LLM summarizer.
8. Store the result as newsletter JSON.
9. Regenerate the static site to include updated newsletter pages and homepage sections.

## Deduplication and Checkpointing

- Primary deduplication key: Gmail `message_id`
- Secondary support fields:
  - RFC `Message-ID` header if available
  - subject
  - internal date
- Keep a small state/checkpoint file for the last processed message date or history boundary.
- Do not rely on unread/read state for correctness.

## Summarization Requirements

The summarizer must treat each newsletter as a multi-article bundle, not a single story.

Required behavior:

- Summarize all major articles included in the newsletter issue.
- Explicitly avoid dropping primary stories because of token compression or parser ordering.
- Preserve source grouping by newsletter section where possible.
- Prefer a structured output that enumerates covered stories.

Implementation implication:

- The summarization prompt must explicitly instruct the LLM to cover every main article detected in the parsed newsletter.
- The parser should extract a list of candidate main items before summarization.
- Validation should compare parsed main item count to summarized item coverage and flag likely omissions.
- If the summary appears to omit major stories, keep the normalized issue data and mark the summary for retry or manual inspection.

## Error Handling

Failure modes should be isolated and recoverable.

- Gmail auth failure:
  - Stop the newsletter fetch command with a clear configuration error.
- Gmail transient API failure:
  - Retry with backoff, then fail the run if retries are exhausted.
- Parsing failure for one message:
  - Record failure metadata and continue processing other messages.
- Summarization failure:
  - Save parsed issue without summary and mark it pending.
- Partial extraction failure:
  - Render the issue with available metadata rather than dropping it entirely.

## Site and Navigation Changes

Replace the current home page archive preview section with newsletter-focused content.

### Home page

- Keep the existing latest paper digest hero.
- Remove the `Archive preview` list from the homepage.
- Add a `Newsletter Briefings` area in its place.
- Show separate blocks for:
  - Nature
  - Science
- Each block should surface the latest issue or a short recent-issues list.

### New pages

- `newsletters.html`
- `newsletters/nature.html`
- `newsletters/science.html`
- `newsletters/<source>/<slug>.html`

### Issue page contents

- Newsletter name
- Published date
- Link to original source
- Sectioned article list
- LLM-generated summary

Do not publicly republish full newsletter bodies unless later legal review says that is acceptable. Public pages should stay summary-and-link oriented.

## Operational Constraints

- Only process future incoming messages.
- Assume a single user-owned Gmail mailbox.
- Authentication should be local and explicit.
- The pipeline can be run as a scheduled polling job; real-time push is unnecessary for this product.

## Testing Strategy

Minimum test coverage should include:

1. Model serialization tests for newsletter issue types.
2. Gmail payload parsing tests using fixture responses.
3. Nature parser tests using representative newsletter HTML fixtures.
4. Science parser tests using representative newsletter HTML fixtures.
5. Summarization prompt/coverage tests ensuring multiple main stories are represented.
6. Static site tests verifying:
   - homepage archive preview is removed
   - newsletter section is rendered
   - source pages and issue pages are generated

## Risks

- Nature and Science email HTML structures may change without warning.
- Gmail OAuth setup adds local configuration complexity.
- Summary quality may degrade if parsing misses article boundaries.
- Publicly exposing too much newsletter body content may create rights or terms issues.

## Recommendation

Proceed with:

- Gmail API
- label-based polling
- separate newsletter data models
- separate newsletter pages
- homepage replacement of archive preview with newsletter sections
- summary validation that checks for coverage of all main newsletter stories
