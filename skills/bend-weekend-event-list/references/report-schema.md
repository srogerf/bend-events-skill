# Report ledger

Store a UTF-8 JSON object. Use explicit ISO dates and timestamps with UTC offsets; all event times are Pacific local wall times. Unknown details are `null` or described in `notes`, never guessed.

Root fields:

| Field | Value |
| --- | --- |
| `title` | Report title |
| `start_date`, `end_date` | Inclusive `YYYY-MM-DD` dates |
| `timezone` | `America/Los_Angeles` |
| `checked_at` | ISO timestamp with offset, when coordination completed |
| `sample` | Optional boolean; true marks fictional example data |
| `sources` | Source coverage records |
| `events` | Deduplicated event records |

Source fields: `id`, `name`, `url`, `status`, `checked_at`, `notes`. Status is `checked`, `partial`, or `unavailable`. Use `partial` for incomplete browsing, uncertain calendar completeness, or unresolved candidates; `unavailable` when the source could not be read. An empty event list from a checked source is valid. A source may be checked while an individual event has incomplete details.

Event fields:

| Field | Value |
| --- | --- |
| `title`, `venue`, `city` | Public display names |
| `date` | `YYYY-MM-DD` within the report range |
| `time`, `doors`, `end_time` | `HH:MM` or null; performance/start, doors, and end separately |
| `url` | Direct event page when possible, official calendar otherwise |
| `price`, `age_restriction` | Useful verified text or null |
| `status` | `verified`, `unverified`, `conflict`, or `cancelled` |
| `notes` | Conflicts, unchecked availability, extra source links, or useful details |
| `source_ids` | One or more IDs from the coverage records |
| `checked_at` | ISO timestamp with offset for the latest inspection; direct verification where available |
| `categories` | Array of category IDs; optional for older reports, default `other` |
| `booking_status` | `required`, `recommended`, `not-required`, or `unknown`; default `unknown` |
| `booking_url` | Direct booking/reservation URL or null |
| `booking_deadline` | Verified `YYYY-MM-DD` deadline or null; may precede report range |
| `booking_notes` | Concise evidence, cutoff time if known, or availability uncertainty |

Category IDs: `music`, `food-drink`, `comedy`, `theatre-dance`, `art`, `markets`, `community`, `film`, `outdoors`, and `other`. Assign at least one when researching new records, and use multiple categories where applicable. Category checkbox selections match any selected category.

Use booking `required` for explicit advance ticket/reservation requirements and `recommended` for a source's recommendation to book ahead. Use `not-required` only with evidence of walk-in/no-reservation access. Otherwise use `unknown`. Do not infer a deadline from the event date or claim tickets remain available without checking. Preserve known cutoff times and timezone in booking notes. Cancelled events should not be promoted as advance-booking opportunities.

Only public `http` and `https` source links belong in published reports. Do not include authentication tokens, personal browsing artifacts, or private account details. The renderer escapes display text and validates links. `verified` means the listed event details were confirmed; it does not imply ticket availability unless notes explicitly say it was checked.

Workers return `{ "sources": [...], "events": [...] }`. The coordinator adds root metadata and merges worker records. See the repository's `examples/events.sample.json` for a fictional example; do not reuse example dates as live research.
