---
name: bend-weekend-event-list
description: Research Bend, Oregon events for a requested date range using parallel source agents, verify venue details, and generate a standalone HTML report with nearby towns and source coverage.
---

# Bend event research

Resolve the requested dates explicitly in `America/Los_Angeles`. When no period is specified, research the current calendar month; a weekend request means the requested Friday through Sunday. Support other date ranges. Refresh event details every run; prior reports are candidates, not evidence of current availability.

## Parallel research

Read [references/sources.json](references/sources.json) for the discovery and venue sources, and [references/source-agent.md](references/source-agent.md) for the reusable worker instructions. These are source assignments, not persistent background services.

Act as coordinator. Assign one source per worker task with the same dates and timezone. Use the available agent capacity, reserving a slot for coordination, and queue remaining sources in batches. Do not assume a fixed concurrency limit. If delegation is unavailable, do the same assignments sequentially and disclose that.

Each worker returns event records and a source coverage record. Workers independently check venue calendars, including breweries; city aggregators have missed those events before. Use aggregators for discovery and direct organizers for verification. Calendar URLs are starting points: follow current official links when paths change.

Collect every assigned source's outcome, including unavailable and partial checks. Do not label an inaccessible source as checked. Retain earlier relevant discoveries when the user asks what was missed. Cover food/beer, music, comedy, theatre/dance, art, markets, and community events.

## Merge and verify

Read [references/report-schema.md](references/report-schema.md) before assembling the ledger. Deduplicate by date, venue, and normalized title, checking apparent duplicates before merging. Preserve all contributing source IDs and useful direct links in notes. Keep repeat-day performances on each date. Resolve conflicts from direct sources or mark them `conflict`; do not invent separate stages or treat missing details as confirmed.

Verify year, local times, doors versus performance, venue/city, price/fees, age restrictions and cancellation status. Categorize each event using the schema's category IDs; multiple categories are allowed. Record advance booking requirements or recommendations, direct booking links and deadlines when supported by the source. A ticket listing alone is not proof of remaining availability or urgency; free events may still require reservations. Keep booking status unknown when evidence is missing.

A snippet or ticket listing is not proof of available tickets. Use `unverified` where date or event details could not be confirmed; never substitute a guessed time. Include source coverage so readers can see the report's limits.

## Output

Produce the concise daily event list in chat and save the matching JSON ledger and standalone HTML report to the user's requested destination (otherwise a task folder under `/tmp`). Render using:

```bash
python3 <skill-directory>/scripts/render_report.py events.json report.html
```

The HTML defaults to a month calendar view with category checkboxes, other period/custom date controls, a list view, and an advance-booking filter. It shows explicit dates, local times, source links, booking details, verification notes, checked timestamps, and a separate nearby-town section. Filters operate on the researched ledger, not live searches; make its covered dates visible and flag selections outside coverage. It must work locally, on mobile, in print, and on static hosting without external assets. Open or inspect the generated report and confirm the events match the ledger. Never claim exhaustive coverage.

Creating a local report does not itself authorize publishing it to a website. Publish only when requested, and preserve any user-designated destination or privacy constraints.
