#!/usr/bin/env python3
"""Render a profile card from the information on the public contributions graph."""
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen

USERNAME = "malhadeff28-gif"


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.tooltip_for = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs and "id" in attrs:
            self.cells[attrs["id"]] = attrs["data-date"]
        if tag == "tool-tip" and attrs.get("for") in self.cells:
            self.tooltip_for = attrs["for"]

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tooltip_for = None

    def handle_data(self, text):
        if self.tooltip_for:
            match = re.search(r"\b(No|[\d,]+) contributions?\b", text, re.I)
            if match:
                count = match.group(1)
                self.counts[self.cells[self.tooltip_for]] = 0 if count.lower() == "no" else int(count.replace(",", ""))


request = Request(f"https://github.com/users/{USERNAME}/contributions", headers={"User-Agent": "github-profile-activity-pulse"})
with urlopen(request, timeout=30) as response:
    parser = CalendarParser()
    parser.feed(response.read().decode("utf-8"))

today = datetime.now(timezone.utc).date()
days = [today - timedelta(days=i) for i in reversed(range(30))]
missing = [day for day in days if day.isoformat() not in parser.counts]
if missing:
    raise RuntimeError(f"GitHub contribution data is missing {len(missing)} days; keeping the previous card")
values = [parser.counts[day.isoformat()] for day in days]
total = sum(values)
active = sum(value > 0 for value in values)
peak = max(values)
peak_index = values.index(peak)
peak_date = days[peak_index].strftime("%b %d") if peak else "No activity yet"
scale = max(peak, 1)
points = []
for index, value in enumerate(values):
    x = 72 + index * (1056 / 29)
    y = 253 - (value / scale) * 88
    points.append(f"{x:.1f},{y:.1f}")
trace = " ".join(points)
average = total / 30
updated = today.strftime("%b %d, %Y")
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 420" role="img" aria-labelledby="title desc">
<title id="title">Max's activity pulse</title>
<desc id="desc">GitHub public contribution activity for the last 30 days: {total} contributions across {active} days, with a peak of {peak} in one day. Updated {updated} UTC.</desc>
<defs><linearGradient id="trace"><stop stop-color="#22c55e" stop-opacity=".45"/><stop offset=".5" stop-color="#4ade80"/><stop offset="1" stop-color="#22c55e" stop-opacity=".65"/></linearGradient></defs>
<rect width="1200" height="420" rx="4" fill="#0a1310"/>
<circle cx="76" cy="60" r="4" fill="#4ade80"/>
<text x="92" y="64" font-family="monospace" font-size="11" fill="#4ade80" letter-spacing="3">MAX / ACTIVITY PULSE</text>
<text x="1128" y="64" text-anchor="end" font-family="monospace" font-size="10" fill="#72a684" letter-spacing="2">UPDATED {updated.upper()} · UTC</text>
<text x="72" y="118" font-family="system-ui, sans-serif" font-size="28" font-weight="700" fill="#dcfce7">Building in public.</text>
<line x1="72" y1="132" x2="196" y2="132" stroke="#4ade80" stroke-width="2"/>
<text x="72" y="156" font-family="monospace" font-size="12" fill="#8db79a">Public GitHub contributions · last 30 days</text>
<line x1="72" y1="253" x2="1128" y2="253" stroke="#1a3b27"/>
<polyline points="{trace}" fill="none" stroke="url(#trace)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="1128" cy="{253-(values[-1]/scale)*88:.1f}" r="4" fill="#bbf7d0"/>
<line x1="72" y1="302" x2="1128" y2="302" stroke="#1a3b27"/>
<g font-family="monospace"><text x="72" y="330" font-size="10" fill="#79a889" letter-spacing="2">CONTRIBUTIONS</text><text x="72" y="360" font-size="22" font-weight="bold" fill="#dcfce7">{total}</text><text x="72" y="383" font-size="11" fill="#79a889">last 30 days</text>
<text x="340" y="330" font-size="10" fill="#79a889" letter-spacing="2">ACTIVE DAYS</text><text x="340" y="360" font-size="22" font-weight="bold" fill="#dcfce7">{active}</text><text x="340" y="383" font-size="11" fill="#79a889">of 30 days</text>
<text x="608" y="330" font-size="10" fill="#79a889" letter-spacing="2">PEAK DAY</text><text x="608" y="360" font-size="22" font-weight="bold" fill="#dcfce7">{peak}</text><text x="608" y="383" font-size="11" fill="#79a889">{peak_date}</text>
<text x="876" y="330" font-size="10" fill="#79a889" letter-spacing="2">DAILY AVERAGE</text><text x="876" y="360" font-size="22" font-weight="bold" fill="#dcfce7">{average:.1f}</text><text x="876" y="383" font-size="11" fill="#79a889">contributions / day</text></g>
</svg>'''
Path("activity-pulse.svg").write_text(svg, encoding="utf-8")
print(f"Rendered {total} public contributions over 30 days; updated {updated} UTC.")
