#!/usr/bin/env python3
"""Render a source-checked event JSON report as portable, escaped HTML."""

import argparse
from datetime import date, datetime, timedelta
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

CATEGORIES = {"music": "Music", "food-drink": "Food & drink", "comedy": "Comedy", "theatre-dance": "Theatre & dance", "art": "Art", "markets": "Markets", "community": "Community", "film": "Film", "outdoors": "Outdoors", "other": "Other"}

INTERACTIVE_SCRIPT = r'''
(() => {
  const root = document.querySelector('main');
  const startInput = document.getElementById('range-start'), endInput = document.getElementById('range-end');
  const preset = document.getElementById('period'), view = document.getElementById('view');
  const entries = [...document.querySelectorAll('#bend .event, #nearby .event')].map(node => ({node: node.cloneNode(true), date: node.dataset.date, categories: node.dataset.categories.split(' '), nearby: node.dataset.nearby === 'true', booking: node.dataset.booking, cancelled: node.classList.contains('cancelled')}));
  // Date-only arithmetic uses UTC internally, never browser local time or timezone conversions.
  const date = value => new Date(value + 'T12:00:00Z');
  const iso = value => value.toISOString().slice(0, 10);
  const add = (value, days) => {const d = date(value); d.setUTCDate(d.getUTCDate() + days); return iso(d);};
  const monthStart = value => value.slice(0,7) + '-01';
  const monthEnd = value => {const d = date(monthStart(value)); d.setUTCMonth(d.getUTCMonth()+1); d.setUTCDate(0); return iso(d);};
  const heading = value => date(value).toLocaleDateString('en-US', {weekday:'long',month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
  const el = (tag, className, text) => {const n=document.createElement(tag); if(className)n.className=className; if(text)n.textContent=text; return n;};
  const controls = document.getElementById('controls');
  controls.hidden = false;
  function calendarCard(entry) {
    const card=entry.node.cloneNode(true);
    const details=el('details','event-details'), summary=el('summary','','Details');
    summary.setAttribute('aria-label','Details for '+card.querySelector('h3').textContent);
    details.append(summary);
    details.append(card.querySelector('.event-top .badge'));
    for(const node of [...card.children]) {
      if(node.matches('.details,.notes,.evidence,.booking'))details.append(node);
    }
    if(['required','recommended'].includes(entry.booking)&&!entry.cancelled)card.append(el('p','compact-booking',entry.booking==='required'?'Booking required':'Booking recommended'));
    card.append(details);
    return card;
  }
  function dates(a,b) {const result=[]; for(let current=a;current<=b;current=add(current,1)) result.push(current); return result;}
  function applyPreset() {
    const anchor = root.dataset.reportDate;
    let a = startInput.value || anchor, b;
    if(preset.value==='month') {a=monthStart(a);b=monthEnd(a);}
    else if(preset.value==='week') {a=add(anchor,-((date(anchor).getUTCDay()+6)%7));b=add(a,6);}
    else if(preset.value==='next7') {a=anchor;b=add(a,6);}
    else if(preset.value==='next30') {a=anchor;b=add(a,29);}
    else if(preset.value==='all') {a=root.dataset.start;b=root.dataset.end;}
    else {render();return;}
    startInput.value=a;endInput.value=b;render();
  }
  function render() {
    const a=startInput.value,b=endInput.value, notice=document.getElementById('range-notice');
    if(!a||!b||b<a||(date(b)-date(a))/86400000>366) {notice.textContent='Choose an ordered date range of no more than 367 days.';notice.className='warning';return;}
    const selected=new Set([...controls.querySelectorAll('[name="category"]:checked')].map(n=>n.value));
    const bookingOnly=document.getElementById('booking-only').checked;
    const filtered=entries.filter(e=>e.date>=a&&e.date<=b&&e.categories.some(c=>selected.has(c))&&(!bookingOnly||(!e.cancelled&&['required','recommended'].includes(e.booking))));
    notice.textContent=(a<root.dataset.start||b>root.dataset.end) ? 'Selected dates extend beyond collected coverage ('+root.dataset.start+' through '+root.dataset.end+'). Uncovered dates have not been researched.' : 'Showing collected events for '+a+' through '+b+'.';
    notice.className=(a<root.dataset.start||b>root.dataset.end)?'warning':'meta';
    document.getElementById('result-count').textContent=filtered.length+' matching event'+(filtered.length===1?'':'s')+'.';
    for(const [id,nearby] of [['bend',false],['nearby-results',true]]) {
      const destination=document.getElementById(id);destination.replaceChildren();
      const subset=filtered.filter(e=>e.nearby===nearby);
      if(!subset.length)destination.append(el('p','empty','No events match these filters'+(nearby?' in nearby towns':' in Bend')+'.'));
      if(view.value==='list') {
        for(const day of dates(a,b)) {
          const matches=subset.filter(e=>e.date===day);
          if(nearby&&!matches.length)continue;
          const section=el('section','day');section.append(el('h2','',heading(day)));
          matches.forEach(e=>section.append(e.node.cloneNode(true)));
          if(!matches.length)section.append(el('p','empty',day<root.dataset.start||day>root.dataset.end?'Outside collected coverage; no research recorded.':'No events match for this day.'));
          destination.append(section);
        }
      } else {
        for(let m=monthStart(a);m<=b;m=add(monthEnd(m),1)) {
          const section=el('section','calendar-month');
          section.append(el('h2','',date(m).toLocaleDateString('en-US',{month:'long',year:'numeric',timeZone:'UTC'})));
          const grid=el('div','calendar-grid');
          ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].forEach(d=>grid.append(el('div','weekday',d)));
          for(let i=0;i<date(m).getUTCDay();i++){const blank=el('div','calendar-blank');blank.setAttribute('aria-hidden','true');grid.append(blank);}
          for(const day of dates(m,monthEnd(m))) {
            const cell=el('section','calendar-day'+((day<a||day>b)?' outside-range':''));
            cell.setAttribute('aria-label',heading(day));
            cell.append(el('h3','day-number',String(date(day).getUTCDate())));
            if(day>=a&&day<=b) {
              const matches=subset.filter(e=>e.date===day);
              matches.forEach(e=>cell.append(calendarCard(e)));
              if(!matches.length)cell.append(el('p','calendar-empty',day<root.dataset.start||day>root.dataset.end?'Not researched':'No matches'));
            }
            grid.append(cell);
          }
          section.append(grid);destination.append(section);
        }
      }
    }
  }
  preset.addEventListener('change',applyPreset);
  for(const input of [startInput,endInput]) input.addEventListener('change',()=>{preset.value='custom';render();});
  view.addEventListener('change',render);
  controls.querySelectorAll('input[type="checkbox"]').forEach(input=>input.addEventListener('change',render));
  for(const [id,direction] of [['previous-month',-1],['next-month',1]]) document.getElementById(id).addEventListener('click',()=>{const d=date(monthStart(startInput.value||root.dataset.anchor));d.setUTCMonth(d.getUTCMonth()+direction);startInput.value=iso(d);preset.value='month';applyPreset();});
  document.getElementById('categories-all').addEventListener('click',()=>{controls.querySelectorAll('[name="category"]').forEach(n=>n.checked=true);render();});
  document.getElementById('categories-none').addEventListener('click',()=>{controls.querySelectorAll('[name="category"]').forEach(n=>n.checked=false);render();});
  document.getElementById('print-report').addEventListener('click',()=>window.print());
  let printDetails=[];
  window.addEventListener('beforeprint',()=>{printDetails=[...document.querySelectorAll('.event-details:not([open])')];printDetails.forEach(n=>n.open=true);});
  window.addEventListener('afterprint',()=>{printDetails.forEach(n=>n.open=false);printDetails=[];});
  applyPreset();
})();
'''


def required_text(record, key):
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a nonempty string")
    return value


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("checked_at must be a timestamp with a timezone offset")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("checked_at must include a timezone offset")


def calendar_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Dates must use YYYY-MM-DD")
    return date.fromisoformat(value)


def url(value):
    if not isinstance(value, str) or any(ord(c) < 33 for c in value):
        raise ValueError("URLs must be absolute http/https links")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URLs must be absolute http/https links without credentials")


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Report must be a JSON object")
    required_text(data, "title")
    if data.get("timezone") != "America/Los_Angeles":
        raise ValueError("timezone must be America/Los_Angeles")
    if "sample" in data and not isinstance(data["sample"], bool):
        raise ValueError("sample must be a boolean")
    start = calendar_date(required_text(data, "start_date"))
    end = calendar_date(required_text(data, "end_date"))
    if end < start or (end - start).days > 366:
        raise ValueError("Date range must be ordered and at most 367 days")
    timestamp(data.get("checked_at"))
    if not isinstance(data.get("sources"), list) or not isinstance(data.get("events"), list):
        raise ValueError("sources and events must be arrays")
    ids = set()
    for source in data["sources"]:
        if not isinstance(source, dict):
            raise ValueError("Each source must be an object")
        source_id = required_text(source, "id")
        if source_id in ids:
            raise ValueError("Source IDs must be unique")
        ids.add(source_id)
        required_text(source, "name")
        url(source.get("url"))
        if source.get("status") not in {"checked", "partial", "unavailable"}:
            raise ValueError("Invalid source status")
        timestamp(source.get("checked_at"))
        if not isinstance(source.get("notes", ""), str):
            raise ValueError("Source notes must be a string")
    for event in data["events"]:
        if not isinstance(event, dict):
            raise ValueError("Each event must be an object")
        for field in ("title", "venue", "city"):
            required_text(event, field)
        event_date = calendar_date(required_text(event, "date"))
        if not start <= event_date <= end:
            raise ValueError("Event dates must fall within the report date range")
        url(event.get("url"))
        if event.get("status") not in {"verified", "unverified", "conflict", "cancelled"}:
            raise ValueError("Invalid event status")
        for field in ("time", "doors", "end_time"):
            value = event.get(field)
            if value is not None and (not isinstance(value, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value)):
                raise ValueError(f"{field} must be null or HH:MM")
        for field in ("price", "age_restriction"):
            if event.get(field) is not None and not isinstance(event[field], str):
                raise ValueError(f"{field} must be null or a string")
        if not isinstance(event.get("notes", ""), str):
            raise ValueError("Event notes must be a string")
        refs = event.get("source_ids")
        if not isinstance(refs, list) or not all(isinstance(ref, str) and ref in ids for ref in refs):
            raise ValueError("source_ids must refer to known sources")
        if not refs:
            raise ValueError("Events must cite at least one source")
        timestamp(event.get("checked_at"))
        categories = event.get("categories", ["other"])
        if not isinstance(categories, list) or not categories or not all(isinstance(item, str) and item in CATEGORIES for item in categories) or len(set(categories)) != len(categories):
            raise ValueError("categories must be a nonempty array of unique supported category slugs")
        if event.get("booking_status", "unknown") not in {"required", "recommended", "not-required", "unknown"}:
            raise ValueError("Invalid booking_status")
        if event.get("booking_url") is not None:
            url(event["booking_url"])
        if event.get("booking_deadline") is not None:
            calendar_date(event["booking_deadline"])
        if not isinstance(event.get("booking_notes", ""), str):
            raise ValueError("booking_notes must be a string")
    return start, end


def clock(value):
    if value is None:
        return "Time unconfirmed"
    hour, minute = map(int, value.split(":"))
    return f"{hour % 12 or 12}:{minute:02d} {'AM' if hour < 12 else 'PM'}"


def render(data):
    start, end = validate(data)
    esc = lambda value: escape(str(value), quote=True)
    labels = {"verified": "Verified", "unverified": "Unverified", "conflict": "Conflicting details", "cancelled": "Cancelled"}
    source_names = {source["id"]: source["name"] for source in data["sources"]}
    checked_day = datetime.fromisoformat(data["checked_at"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles")).date()
    anchor = checked_day if start <= checked_day <= end else start
    category_controls = ''.join(f'<label><input type="checkbox" name="category" value="{slug}" checked> {esc(label)}</label>' for slug, label in CATEGORIES.items())

    def card(event):
        timing = clock(event.get("time"))
        if event.get("end_time"):
            timing += " – " + clock(event["end_time"])
        if event.get("doors"):
            timing += " · Doors " + clock(event["doors"])
        details = [event["venue"], event["city"]]
        details += [event[key] for key in ("price", "age_restriction") if event.get(key)]
        references = ", ".join(source_names[ref] for ref in event["source_ids"])
        categories = event.get("categories", ["other"])
        booking = event.get("booking_status", "unknown")
        booking_labels = {"required": "Advance booking required", "recommended": "Advance booking recommended", "not-required": "Advance booking not required", "unknown": "Booking requirements unconfirmed"}
        booking_style = booking if event["status"] != "cancelled" else "cancelled"
        booking_label = booking_labels[booking] if event["status"] != "cancelled" else "Cancelled — do not book; check the source for refund details"
        booking_details = f'<p class="booking {booking_style}"><strong>{booking_label}</strong>'
        if event.get("booking_url"):
            booking_details += f' · <a href="{esc(event["booking_url"])}">Booking details / tickets</a>'
        if event.get("booking_deadline"):
            booking_details += f' · Deadline: {esc(event["booking_deadline"])}'
        if event.get("booking_notes"):
            booking_details += ' · ' + esc(event["booking_notes"])
        booking_details += '</p>'
        return f'''<article class="event {event['status']}" data-date="{event['date']}" data-categories="{' '.join(categories)}" data-booking="{booking}" data-nearby="{str(event['city'].strip().casefold() != 'bend').lower()}">
<div class="event-top"><p class="time">{esc(timing)}</p><span class="badge {event['status']}">{labels[event['status']]}</span></div>
<h3><a href="{esc(event['url'])}">{esc(event['title'])}</a></h3>
<p class="details">{esc(' · '.join(details))}</p>
<p class="category-label">{esc(' · '.join(CATEGORIES[category] for category in categories))}</p>
{booking_details}
{('<p class="notes">' + esc(event['notes']) + '</p>') if event.get('notes') else ''}
<p class="evidence">Checked {esc(event['checked_at'])}{(' · Sources: ' + esc(references)) if references else ''}</p>
</article>'''

    def days(events, empty):
        sections = []
        current = start
        while current <= end:
            records = sorted((event for event in events if event["date"] == current.isoformat()), key=lambda event: (event.get("time") is None, event.get("time") or "", event["title"].casefold()))
            if records or empty:
                heading = current.strftime("%A, %B %d, %Y").replace(" 0", " ")
                content = "\n".join(card(event) for event in records) or '<p class="empty">No events recorded for this day. This does not establish that no events are taking place.</p>'
                sections.append(f'<section class="day"><h2>{heading}</h2>{content}</section>')
            current += timedelta(days=1)
        return "\n".join(sections)

    ordered_events = sorted(data["events"], key=lambda event: (event["date"], event.get("time") is None, event.get("time") or "", event["title"].casefold()))
    bend = [event for event in ordered_events if event["city"].strip().casefold() == "bend"]
    nearby = [event for event in ordered_events if event not in bend]
    source_rows = "\n".join(f'''<tr><th scope="row"><a href="{esc(source['url'])}">{esc(source['name'])}</a></th><td>{esc(source['status'].capitalize())}</td><td>{esc(source['checked_at'])}</td><td>{esc(source.get('notes', ''))}</td></tr>''' for source in data["sources"])
    sample = '<p class="sample">FICTIONAL SAMPLE · Layout demonstration only. These are not real event listings.</p>' if data.get("sample") else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data['title'])}</title><style>
:root{{color-scheme:light;--ink:#18332e;--muted:#596961;--line:#d9e1d9;--paper:#f5f6ef;--accent:#236f5b}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,-apple-system,sans-serif}}main{{max-width:960px;margin:auto;padding:48px 24px 36px}}header{{border-bottom:2px solid var(--ink);padding-bottom:24px;margin-bottom:32px}}.eyebrow{{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:var(--accent)}}h1{{font-size:clamp(2rem,5vw,3.5rem);line-height:1.1;margin:12px 0 18px;letter-spacing:-.035em}}h2{{font-size:1.35rem;margin:28px 0 14px}}h3{{margin:4px 0 8px;font-size:1.2rem}}p{{margin:6px 0}}a{{color:var(--accent);text-underline-offset:3px}}nav{{display:flex;gap:20px;flex-wrap:wrap;margin-top:18px}}.meta,.evidence,.empty{{color:var(--muted)}}.meta{{font-size:.9rem}}.event{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px;margin:12px 0;break-inside:avoid}}.event-top{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}}.time{{font-weight:650;font-size:.95rem}}.badge{{font-size:.75rem;font-weight:650;border-radius:30px;padding:3px 10px;background:#eef1ed}}.badge.verified{{color:#17573f;background:#e6f3e9}}.badge.conflict,.badge.unverified{{color:#704a10;background:#fff2d5}}.badge.cancelled{{color:#8c3030;background:#fbe9e7}}.cancelled h3{{text-decoration:line-through}}.notes{{margin-top:10px}}.evidence{{font-size:.75rem;margin-top:12px}}.nearby{{margin-top:40px;padding-top:18px;border-top:2px solid var(--line)}}.nearby>h2,.coverage>h2{{font-size:1.7rem}}.sample{{padding:14px 18px;background:#fff2d5;border:1px solid #d8bd79;border-radius:8px;font-weight:650;margin-bottom:24px}}.coverage{{margin-top:40px;border-top:2px solid var(--line);padding-top:18px}}.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:.85rem;text-align:left}}th,td{{padding:12px 8px;border-bottom:1px solid var(--line);vertical-align:top}}thead th{{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em}}footer{{color:var(--muted);font-size:.85rem;margin-top:28px}}@media(max-width:540px){{main{{padding:28px 16px}}.event{{padding:16px}}}}@media print{{body{{background:white;font-size:10pt}}main{{max-width:none;padding:0}}nav{{display:none}}.event{{border-radius:0;padding:12px}}a{{color:inherit}}h2{{break-after:avoid}}.table-wrap{{overflow:visible}}th,td{{padding:6px}}footer{{font-size:9pt}}}}
.controls{{background:white;border:1px solid var(--line);border-radius:12px;padding:18px;margin:24px 0}}.toolbar{{display:flex;gap:12px;flex-wrap:wrap;align-items:end}}.toolbar label{{display:grid;gap:4px;font-size:.85rem}}button,select,input[type="date"]{{font:inherit;border:1px solid #abbcaf;border-radius:5px;background:white;color:var(--ink);padding:7px 10px}}button{{cursor:pointer}}button:hover{{background:#edf3eb}}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{{outline:3px solid #378873;outline-offset:3px}}fieldset{{border:0;margin:16px 0;padding:0}}legend{{font-weight:650}}.category-options{{display:flex;flex-wrap:wrap;gap:8px 18px}}.category-options label{{font-size:.9rem}}input[type="checkbox"]{{accent-color:var(--accent)}}.category-actions{{margin-top:10px;display:flex;gap:8px}}.warning{{background:#fff2d5;padding:12px;border-radius:6px}}.category-label{{font-size:.75rem;font-weight:600;color:var(--accent)}}.booking{{font-size:.82rem;color:var(--muted);margin-top:10px}}.booking.required,.booking.recommended{{background:#fff2d5;color:#704a10;padding:7px 10px;border-radius:5px}}.calendar-grid{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px}}.weekday{{font-size:.75rem;text-align:center;font-weight:700;padding:7px}}.calendar-day{{background:#fff;border:1px solid var(--line);border-radius:6px;min-height:100px;padding:6px;overflow-wrap:anywhere}}.day-number{{margin:0;font-size:.9rem}}.calendar-grid .event{{padding:7px;margin:8px 0;font-size:.8rem;border-radius:4px}}.calendar-grid .event h3{{font-size:.9rem;line-height:1.35}}.calendar-grid .event-top{{gap:4px}}.calendar-grid .event-top .badge{{display:none}}.event-details{{margin-top:7px}}.event-details summary{{cursor:pointer;color:var(--accent);font-size:.75rem;min-height:24px}}.compact-booking{{font-size:.67rem;line-height:1.4;background:#fff2d5;color:#704a10;border-radius:4px;padding:3px 5px}}.calendar-grid .category-label{{font-size:.65rem;line-height:1.35}}.calendar-grid .time{{font-size:.72rem}}.calendar-grid .badge{{font-size:.65rem;padding:2px 5px}}.calendar-grid .evidence{{font-size:.65rem}}.calendar-grid .booking{{font-size:.72rem;padding:4px}}.calendar-empty{{font-size:.65rem;color:var(--muted)}}.outside-range{{background:#ecefe8;min-height:70px}}.calendar-blank{{background:transparent}}[hidden]{{display:none!important}}@media(min-width:900px){{main{{max-width:1280px}}}}@media(max-width:760px){{.calendar-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.weekday,.calendar-blank,.outside-range{{display:none}}.calendar-day{{min-height:100px}}.calendar-grid .event h3{{font-size:1rem}}}}@media(max-width:420px){{.calendar-grid{{grid-template-columns:1fr}}}}@media print{{.controls{{display:none}}.calendar-grid{{display:block}}.weekday,.calendar-blank,.outside-range,.calendar-day:not(:has(.event)){{display:none}}.calendar-day{{border:0;break-inside:avoid;margin-bottom:12px}}.event-details summary{{display:none}}.compact-booking{{display:none}}.calendar-grid .event{{font-size:10pt}}.calendar-grid .event h3{{font-size:11pt}}.calendar-grid .evidence{{font-size:8pt}}}}
</style></head><body><main data-start="{start.isoformat()}" data-end="{end.isoformat()}" data-anchor="{anchor.isoformat()}" data-report-date="{checked_day.isoformat()}">{sample}<header><p class="eyebrow">Bend &amp; Central Oregon</p><h1>{esc(data['title'])}</h1>
<p>Collected coverage: {esc(start.isoformat())} through {esc(end.isoformat())}</p><p class="meta">All event times are local: America/Los_Angeles. Report checked {esc(data['checked_at'])}.</p>
<nav aria-label="Report sections"><a href="#bend">Bend events</a><a href="#nearby">Nearby towns</a><a href="#coverage">Source coverage</a></nav></header>
<section id="controls" class="controls" aria-label="Event display and filters" hidden>
<div class="toolbar"><label>Period<select id="period"><option value="month">Month</option><option value="week">Week (Monday–Sunday)</option><option value="next7">Next 7 days from report date</option><option value="next30">Next 30 days from report date</option><option value="all">All collected dates</option><option value="custom">Custom dates</option></select></label>
<label>Start<input id="range-start" type="date" value="{anchor.isoformat()}"></label><label>End<input id="range-end" type="date" value="{end.isoformat()}"></label>
<label>View<select id="view"><option value="calendar">Calendar</option><option value="list">List</option></select></label>
<button id="previous-month" type="button" aria-label="Previous month">← Month</button><button id="next-month" type="button" aria-label="Next month">Month →</button><button id="print-report" type="button">Print / Save PDF</button></div>
<fieldset><legend>Show categories</legend><div class="category-options">{category_controls}</div><div class="category-actions"><button id="categories-all" type="button">Select all</button><button id="categories-none" type="button">Clear all</button></div></fieldset>
<label><input id="booking-only" type="checkbox"> Only events with advance booking required or recommended</label>
<p id="range-notice" role="status"></p><p id="result-count" class="meta" aria-live="polite"></p></section>
<noscript><p class="meta">JavaScript is disabled. All collected events appear below in date order; interactive filters and calendar view require JavaScript.</p></noscript>
<div id="bend">{days(bend, True)}</div>
<section id="nearby" class="nearby"><h2>Nearby towns</h2><div id="nearby-results">{days(nearby, False) or '<p class="empty">No nearby events recorded.</p>'}</div></section>
<section id="coverage" class="coverage"><h2>Source coverage</h2><p class="meta">Checked means the source was reviewed; availability and details can still change. Partial and unavailable sources leave gaps.</p>
<div class="table-wrap"><table><thead><tr><th scope="col">Source</th><th scope="col">Review status</th><th scope="col">Last checked</th><th scope="col">Notes</th></tr></thead><tbody>{source_rows}</tbody></table></div></section>
<footer>This report is not exhaustive. Follow the event link to confirm details and ticket availability before making plans.</footer></main><script>{INTERACTIVE_SCRIPT}</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source-checked event JSON")
    parser.add_argument("output", type=Path, help="Standalone HTML destination")
    args = parser.parse_args()
    try:
        result = render(json.loads(args.input.read_text(encoding="utf-8")))
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"Invalid report: {exc}\n")
    args.output.write_text(result, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
