import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_report", ROOT / "skills/bend-weekend-event-list/scripts/render_report.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/events.sample.json").read_text())

    def test_escape_untrusted_text_and_attributes(self):
        self.data["title"] = '<script>alert("x")</script>'
        self.data["events"][0]["notes"] = '<img src=x onerror="alert(1)">'
        self.data["events"][0]["url"] = 'https://example.org/?x="onload"&y=2'
        output = MODULE.render(self.data)
        self.assertEqual(output.count("<script>"), 1)  # Only the trusted static interactive script.
        self.assertNotIn("<img", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertIn("x=&quot;onload&quot;&amp;y=2", output)

    def test_reject_unsafe_and_relative_urls(self):
        for unsafe in ("javascript:alert(1)", "//example.org", "data:text/html,test", "https://", "https://user:pass@example.org", "https://example.org/\nattack"):
            with self.subTest(url=unsafe):
                self.data["events"][0]["url"] = unsafe
                with self.assertRaises(ValueError):
                    MODULE.render(self.data)

    def test_date_range_validation(self):
        self.data["events"][0]["date"] = "2026-02-30"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)
        self.data["events"][0]["date"] = "2027-01-01"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)
        self.data["events"][0]["date"] = "20261016"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)

    def test_chronological_sort_unknown_time_last(self):
        earlier = copy.deepcopy(self.data["events"][1])
        earlier.update(title="Earlier market", time="08:00")
        self.data["events"].insert(0, earlier)
        output = MODULE.render(self.data)
        self.assertLess(output.index("Earlier market"), output.index("Sample makers market"))
        self.assertLess(output.index("Sample makers market"), output.index("Sample neighborhood art walk"))
        self.assertIn("Time unconfirmed", output)

    def test_nearby_events_separate_from_bend(self):
        output = MODULE.render(self.data)
        primary, nearby = output.split('<section id="nearby"', 1)
        self.assertNotIn("Sample folk concert", primary)
        self.assertIn("Sample folk concert", nearby)

    def test_empty_days_and_sample_notice_and_coverage(self):
        output = MODULE.render(self.data)
        self.assertIn("Sunday, October 18, 2026", output)
        self.assertIn("No events recorded for this day", output)
        self.assertIn("FICTIONAL SAMPLE", output)
        self.assertIn("Fictional community calendar", output)
        self.assertIn("Partial", output)
        self.assertIn("2026-10-14T14:55:00-07:00", output)

    def test_verified_event_requires_known_evidence_and_timestamp_offset(self):
        self.data["events"][0]["source_ids"] = []
        with self.assertRaises(ValueError):
            MODULE.render(self.data)
        self.data["events"][0]["source_ids"] = ["missing"]
        with self.assertRaises(ValueError):
            MODULE.render(self.data)
        self.data["events"][0]["source_ids"] = ["sample-venue"]
        self.data["events"][0]["checked_at"] = "2026-10-14T15:00:00"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)

    def test_categories_and_booking_validation(self):
        event = self.data["events"][0]
        for invalid in ([], ["invalid"], ["music", "music"], "music", [None]):
            event["categories"] = invalid
            with self.subTest(categories=invalid), self.assertRaises(ValueError):
                MODULE.render(self.data)
        event["categories"] = ["music", "community"]
        event["booking_url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)
        event["booking_url"] = "https://example.org/tickets"
        event["booking_deadline"] = "2026-02-30"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)
        event["booking_deadline"] = "20261015"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)
        event["booking_deadline"] = "2026-10-15"
        event["booking_status"] = "buy-now"
        with self.assertRaises(ValueError):
            MODULE.render(self.data)

    def test_filter_metadata_and_booking_display(self):
        event = self.data["events"][0]
        event.update(categories=["music", "community"], booking_status="required", booking_url="https://example.org/tickets", booking_deadline="2026-10-15", booking_notes="Reserve <early>")
        output = MODULE.render(self.data)
        self.assertIn('data-categories="music community"', output)
        self.assertIn('data-booking="required"', output)
        self.assertIn("Advance booking required", output)
        self.assertIn("Deadline: 2026-10-15", output)
        self.assertIn("Reserve &lt;early&gt;", output)
        self.assertIn('<option value="calendar">Calendar</option>', output)
        self.assertIn('id="booking-only"', output)
        self.assertIn("JavaScript is disabled", output)

    def test_legacy_fields_default_and_pacific_anchor(self):
        event = self.data["events"][0]
        for key in ("categories", "booking_status", "booking_url", "booking_deadline", "booking_notes"):
            event.pop(key, None)
        self.data["checked_at"] = "2026-10-17T02:00:00+00:00"
        output = MODULE.render(self.data)
        self.assertIn('data-categories="other"', output)
        self.assertIn('data-booking="unknown"', output)
        self.assertIn('data-report-date="2026-10-16"', output)

    def test_cancelled_booking_not_promoted(self):
        self.data["events"][0].update(status="cancelled", booking_status="required")
        output = MODULE.render(self.data)
        self.assertIn("Cancelled — do not book", output)
        self.assertNotIn('<p class="booking required">', output)


if __name__ == "__main__":
    unittest.main()
