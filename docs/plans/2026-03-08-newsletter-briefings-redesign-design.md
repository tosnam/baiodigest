# Newsletter Briefings Redesign Design

**Date:** 2026-03-08

**Goal:** Reframe Nature and Science newsletters as day-specific briefings, render each received newsletter issue as its own home-page card, and change the issue page from a whole-newsletter summary to per-article Korean briefings.

## Scope

- Keep the existing PubMed digest pipeline unchanged.
- Keep Gmail ingestion and newsletter parsing unchanged except where rendering or summary structure must change.
- Change the home-page newsletter section so it behaves like a daily content area rather than a source directory.
- Use sender/newsletter branding such as `Nature Briefing`, `Nature Briefing: Microbiology`, and `ScienceAdviser` as the displayed issue title.
- Replace issue-level public summary rendering with article-level Korean briefings.

## Display Model

The current home page groups newsletters by source (`nature`, `science`) and shows one latest issue per source. That model is no longer sufficient because a single day can contain multiple issues from the same source family.

The new UI should treat each newsletter email as a first-class daily issue:

- `Today's Digest` remains the paper hero.
- `Newsletter Briefings` becomes a matching headline block with the same heading scale as `Today's Digest`.
- The section renders one vertical card per received newsletter issue.
- If the same day includes both `Nature Briefing` and `Nature Briefing: Microbiology`, both must appear as separate cards.
- The card CTA is always `View`.
- `View all` is removed from the home page.

This aligns the newsletter surface with the product’s day-based digest concept while still keeping newsletters separate from papers.

## Identity and Naming

The card and issue-page title should not use the parsed newsletter email subject as the primary display label. Subjects vary too much and often foreground a lead article rather than the publication identity.

Displayed title priority should be:

1. Sender/newsletter branding from the email metadata if available
2. Parsed `newsletter_name`
3. Fallback parsed title

Examples:

- `Nature Briefing`
- `Nature Briefing: Microbiology`
- `ScienceAdviser`

This preserves distinction between multiple same-day newsletters inside the same source family.

## Summary Model

The current public issue page exposes:

- issue-level summary
- highlights
- significance
- section items with extracted newsletter snippets

That is not the right public representation for this feature. Instead, the summary output should be article-centric.

### Required public shape

Each parsed main article should have:

- English article title
- original URL
- Korean briefing in 1-2 sentences

The LLM must still cover all main articles without omission. Coverage validation should remain mandatory.

### Internal summary structure

Keep coverage metadata, but shift the generated summary payload toward:

- `overview` for lightweight home-card copy if needed
- `covered_item_titles` for validation
- `article_briefings`
  - `title`
  - `url`
  - `briefing_ko`

The legacy `highlights` and `significance` fields can remain temporarily for backward compatibility if needed, but the public templates should stop depending on them.

## Home Page Rendering

The newsletter section should be driven by a date-sorted flat issue list, not source-grouped latest pointers.

Each card should render:

- displayed newsletter name
- received/published date
- short preview copy derived from `overview` or first article briefing
- `View` link to the issue page

This means the site context needs a new property for recent newsletter issues, while `newsletter_groups` can remain for source index pages.

## Issue Page Rendering

The issue page should render:

- displayed newsletter name
- issue date
- optional original newsletter link if available
- `Top stories`
  - one block per main article
  - English article title linked to the original URL
  - Korean 1-2 sentence briefing

The existing `요약` block should be removed from the public template.

The raw newsletter snippet extracted from the email should not be the primary public text anymore unless no Korean article briefing is available.

## Error Handling

- If an issue summary exists but some article briefings are missing, keep the issue page renderable and fall back to empty briefing text for only those items.
- If branding metadata is unavailable, fall back to `newsletter_name`, then `title`.
- If multiple issues share the same publication date, preserve deterministic ordering by `received_at` and `message_id`.

## Testing Strategy

Minimum coverage:

1. Home-page rendering shows one card per issue, including multiple same-day issues from the same source family.
2. Home-page rendering uses `View`, not `View all`.
3. `Newsletter Briefings` uses the same heading level as `Today's Digest`.
4. Issue-page rendering removes the `요약` section.
5. Issue-page rendering shows article title, original link, and Korean briefing per parsed article.
6. Summary parsing validates article-level briefings against parsed main article titles.

## Recommendation

Proceed with an issue-centric render model and article-centric summary model. This is the smallest coherent change that satisfies the day-based newsletter concept without disturbing the paper digest pipeline.
