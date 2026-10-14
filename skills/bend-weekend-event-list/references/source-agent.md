# Source research agent

Use this reusable role once for each source ID in `sources.json`. The coordinator supplies exactly one registry entry, inclusive ISO start/end dates, `America/Los_Angeles`, and any category or geographic limits. Name the assignment after the source ID. The registry is a starting-point directory, not proof of event coverage.

## Assignment prompt

Research only the assigned source for the requested dates and timezone. Read its calendar, date filters, event pages, and official linked channels. Follow organizer, venue, or venue-authorized ticket pages to verify candidates discovered by this source. Do not take responsibility for other registry sources; return relevant candidates even if another agent may find them. Stay read-only: do not contact organizers, submit forms, purchase tickets, alter accounts, or publish anything.

Verify the year, date, city, venue, start and end time, doors versus performance time, price and fees, age restrictions, cancellation status, and booking requirements wherever stated. Cover music, food/beer festivals, comedy, theatre/dance, art/open studios, markets, and community events unless the coordinator narrows the scope. Assign categories from published event facts. Do not assume a brewery has no events because a general tourism calendar omits it.

Use source-specific notes in the registry. A search snippet is a candidate, not verification. An inaccessible calendar, unreadable image, missing year, or contradictory detail must remain explicit. Do not fabricate schedules, stages, prices, restrictions, or availability. Use `null` for unknown optional fields. A missing time is unknown, not automatically an all-day event. Copy facts into short original notes; do not reproduce event descriptions.

Return structured JSON with exactly the root keys `sources` and `events`, following the contract below. Write only an assigned source result file if the coordinator provides a path; otherwise return the JSON in your response. Do not merge other agents' records, write the final HTML, or claim the list is exhaustive. The coordinator resolves duplication and produces the report.

## Return contract

`sources` contains exactly one coverage record for the assigned source:

| Field | Value |
| --- | --- |
| `id`, `name`, `url` | Assigned registry source identity and starting URL. |
| `status` | `checked`, `partial`, or `unavailable`. |
| `checked_at` | Actual latest-inspection ISO 8601 timestamp with timezone offset, e.g. an offset of `-07:00` or `-08:00` as applicable. |
| `notes` | String describing filters/date coverage, pages inspected, verification gaps, and blocked pages. |

`checked` means the source's accessible listings for the assigned date range were reviewed, including relevant linked pages. It does not mean the source includes every event in town. Use `partial` when some listings or date filters could not be reviewed, and `unavailable` when the source could not be meaningfully inspected. Always return this record even when `events` is empty; an empty array is not evidence of no events when coverage is partial or unavailable. Never copy the registry URL-check date as a run's `checked_at`.

`events` is an array of records, one per distinct event date:

| Field | Value |
| --- | --- |
| `title` | Short event title. |
| `date` | `YYYY-MM-DD`, within the assigned inclusive date range. |
| `time`, `doors`, `end_time` | Local `HH:MM` in 24-hour form, or `null` when unknown. `time` is the event/performance start; keep doors separate. |
| `venue`, `city` | Actual venue/room and city, not the discovery site's city. |
| `url` | Best direct venue, organizer, or authorized event ticket page; keep a discovery link only when direct confirmation is unavailable. |
| `price`, `age_restriction` | Concise verified string, or `null`. State known fees and distinguish starting price from total cost. |
| `categories` | Array of one or more supported slugs: `music`, `food-drink`, `comedy`, `theatre-dance`, `art`, `markets`, `community`, `film`, `outdoors`, `other`. Multiple categories are allowed when published facts support them; use `other` when none fits. |
| `booking_status` | `required`, `recommended`, `not-required`, or `unknown`, based on direct evidence as described below. |
| `booking_url` | Direct HTTP(S) booking, reservation, registration, or authorized ticket URL, or `null` when unknown. |
| `booking_deadline` | Explicit published booking deadline as `YYYY-MM-DD`, or `null`. |
| `booking_notes` | String explaining booking evidence, fees, an exact deadline time if given, sold-out/waitlist information, or uncertainty. |
| `status` | `verified`, `unverified`, `conflict`, or `cancelled`. |
| `notes` | String containing useful details, missing information, conflicting facts and their links, unchecked ticket availability, and any next-day end time. |
| `source_ids` | Array containing the assigned registry ID. |
| `checked_at` | Actual latest-inspection ISO 8601 timestamp with timezone offset for this record, using direct verification where available. |

Use `verified` when the direct source confirms the event's identity, date/year, and venue/city; optional missing facts must still be `null` or noted. Use `unverified` for a plausible candidate lacking direct confirmation, `conflict` for materially contradictory date/time/venue claims, and `cancelled` for an explicit cancellation. Price verification does not establish remaining ticket availability. Include a repeat-day performance on each confirmed date; do not extrapolate recurrence beyond published dates. For an event running across midnight, retain its start date and note that its end time falls the next day.

For booking, default to `unknown`. Set `required` only when a direct source says booking, registration, a reservation, or advance ticket purchase is mandatory. Set `recommended` only when a direct source advises advance booking; tickets being offered for sale alone do not establish that advance booking is recommended or required. Set `not-required` only when a direct source clearly permits entry without booking, such as explicit walk-in admission. A free event can still require registration. Record a ticket-sale link when useful without inventing urgency, availability, or a requirement to book ahead.

Record only an explicit booking deadline in `booking_deadline`; do not guess a sell-out date or use the event date as a deadline. Put verified sold-out or waitlist notices in `booking_notes`. A booking deadline may precede the researched event date range: retain it for an in-range event without broadening research to events outside the assigned dates.

## Handoff check

- Confirm every event falls within the requested dates and geographic scope, including nearby-town events when permitted.
- Make every event URL and source ID traceable; include links in notes for conflicting claims.
- Record the actual inspection timestamps and source coverage status.
- Preserve uncertainty, even if it leaves the events array empty.
