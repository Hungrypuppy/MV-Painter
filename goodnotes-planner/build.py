#!/usr/bin/env python3
"""Atelier Soleil 2027 — GoodNotes planner sample (landscape iPad, 4:3).

Mid-century cut-paper art system: every month has its own artwork + palette,
weekdays have a shape alphabet, and real 2027 moon phases (KST) mark the calendars.
Builds planner.html; render.js -> PDF + previews; fixlinks.py -> explicit page links.
"""
import calendar
import datetime as dt
import json
from pathlib import Path

import ephem

from art import art, moon_phase_disc, TITLES

HERE = Path(__file__).parent
YEAR = 2027
W, H = 1366, 1024

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
ABBR = [m[:3].upper() for m in MONTHS]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SEASON = ["Winter", "Winter", "Spring", "Spring", "Spring", "Summer", "Summer",
          "Summer", "Autumn", "Autumn", "Autumn", "Winter"]
QUOTE = ["Begin quietly. Begin anyway.", "Soft hearts, steady hands.",
         "Everything green starts small.", "Let it rain. Let it grow.",
         "Bloom at your own pace.", "Follow the long light.",
         "Slow days, golden hours.", "Hold on to the warm evenings.",
         "Gather what you have grown.", "Let go, beautifully.",
         "Rest is part of the work.", "Close the year gently."]
MAIN = ["#26374D", "#6B3E4F", "#5F7150", "#5E86A3", "#D08068", "#2F6B6B",
        "#D9A441", "#C0562F", "#9A8A3A", "#9C4A2E", "#4B4E57", "#2F4A3A"]
LIGHT = ["#E3E8EB", "#F3E1DA", "#E5E9D7", "#E0EAF0", "#F6E2D8", "#DDEBE6",
         "#F7EBCF", "#F8E0D0", "#EFE8D0", "#F2E2D6", "#E4E3E2", "#DEE7E0"]
TABTXT = ["#F6EEDF"] * 12
TABTXT[4] = TABTXT[6] = "#2B211B"

# weekday shape alphabet
DAYSHAPE = [("circle", "#C8643B"), ("half", "#2F6B6B"), ("tri", "#D9A441"),
            ("square", "#6E7F5A"), ("arch", "#D08068"), ("flower", "#6B3E4F"), ("sun", "#26374D")]

MOON = json.loads((HERE / "moon2027.json").read_text())
PHASE_NAME = {"new": "New moon", "first": "First quarter", "full": "Full moon", "last": "Last quarter"}

cal = calendar.Calendar(firstweekday=0)
WEEK_SAMPLE = dt.date(YEAR, 1, 4)
DAY_SAMPLE = dt.date(YEAR, 1, 4)


def week_id(d):
    iso = d.isocalendar()
    return f"w{iso[0]}-{iso[1]:02d}"


def day_id(d):
    return f"d{d.isoformat()}"


EXISTING = ({"cover", "index", "year", "goals", "habits", "notes", "dots",
             week_id(WEEK_SAMPLE), day_id(DAY_SAMPLE)}
            | {f"m{i:02d}" for i in range(1, 13)} | {f"o{i:02d}" for i in range(1, 13)})


def link(target, inner, cls=""):
    if target in EXISTING:
        return f'<a href="#{target}" class="{cls}">{inner}</a>'
    return f'<span class="{cls}">{inner}</span>'


# ---------------------------------------------------------------- icons

def shape(kind, color, size=12, outline=False):
    paint = (f'style="fill:none;stroke:{color};stroke-width:1.1"' if outline else f'style="fill:{color}"')
    g = {
        "circle": '<circle cx="6" cy="6" r="5"/>',
        "half": '<path d="M.8 9.2A5.2 5.2 0 0 1 11.2 9.2Z"/>',
        "tri": '<path d="M6 1.2L11.1 10.4H.9Z"/>',
        "square": '<rect x="1.3" y="1.3" width="9.4" height="9.4" rx="1.4"/>',
        "arch": '<path d="M1.6 11V6.2a4.4 4.4 0 0 1 8.8 0V11Z"/>',
        "flower": ('<circle cx="6" cy="3.4" r="2.6"/><circle cx="8.6" cy="6" r="2.6"/>'
                   '<circle cx="6" cy="8.6" r="2.6"/><circle cx="3.4" cy="6" r="2.6"/>'),
        "sun": ('<circle cx="6" cy="6" r="3"/>' + "".join(
            f'<circle cx="{6 + 5.1 * __import__("math").cos(i * .785398):.2f}" '
            f'cy="{6 + 5.1 * __import__("math").sin(i * .785398):.2f}" r=".85"/>' for i in range(8))),
        "drop": '<path d="M6 .9C6 .9 1.8 6.3 1.8 8a4.2 4.2 0 0 0 8.4 0C10.2 6.3 6 .9 6 .9Z"/>',
        "line": '<rect x=".8" y="5.2" width="10.4" height="1.6" rx=".8"/>',
    }[kind]
    return f'<svg class="shp" width="{size}" height="{size}" viewBox="0 0 12 12"><g {paint}>{g}</g></svg>'


def day_shape(d, size=12, outline=False):
    k, col = DAYSHAPE[d.weekday()]
    return shape(k, col, size, outline)


def moon_icon(kind, size=12):
    dark, line = "#5A4E45", "#5A4E45"
    if kind == "new":
        g = f'<circle cx="6" cy="6" r="4.6" fill="{dark}"/>'
    elif kind == "full":
        g = '<circle cx="6" cy="6" r="4.6" fill="#EBC777" stroke="#B98A33" stroke-width=".8"/>'
    elif kind == "first":
        g = (f'<circle cx="6" cy="6" r="4.6" fill="none" stroke="{line}" stroke-width=".8"/>'
             f'<path d="M6 1.4A4.6 4.6 0 0 0 6 10.6Z" fill="{dark}"/>')
    else:
        g = (f'<circle cx="6" cy="6" r="4.6" fill="none" stroke="{line}" stroke-width=".8"/>'
             f'<path d="M6 1.4A4.6 4.6 0 0 1 6 10.6Z" fill="{dark}"/>')
    return f'<svg class="moon" width="{size}" height="{size}" viewBox="0 0 12 12">{g}</svg>'


def moon_today(d):
    """Illuminated fraction + waxing flag at local noon (KST)."""
    t = ephem.Date(dt.datetime(d.year, d.month, d.day, 3))
    k = ephem.Moon(t).phase / 100
    k2 = ephem.Moon(ephem.Date(t + 1)).phase / 100
    waxing = k2 > k
    if k < .03:
        name = "New moon"
    elif k > .97:
        name = "Full moon"
    elif abs(k - .5) < .06:
        name = "First quarter" if waxing else "Last quarter"
    else:
        name = ("Waxing " if waxing else "Waning ") + ("crescent" if k < .5 else "gibbous")
    return k, waxing, name


def next_phase(d):
    for k, v in MOON.items():
        kd = dt.date.fromisoformat(k)
        if kd > d:
            return kd, v
    return None, None


# ---------------------------------------------------------------- primitives

def lines(n, h=32, cls=""):
    return f'<div class="lines {cls}" style="--lh:{h}px">' + '<i></i>' * n + '</div>'


def checks(n, h=32, cls=""):
    return f'<div class="checks {cls}" style="--lh:{h}px">' + '<i><b></b></i>' * n + '</div>'


def dotgrid(step=24, r=1.15, pad=None):
    return f'<div class="dotfill" data-step="{step}" data-r="{r}" data-pad="{pad if pad is not None else step}"></div>'


def tabs(active=None):
    out = ['<nav class="tabs">']
    for i, a in enumerate(ABBR):
        on = " on" if active == i + 1 else ""
        out.append(f'<a href="#m{i + 1:02d}" class="tab{on}" style="--tone:{MAIN[i]};--tt:{TABTXT[i]}">'
                   f'<span>{a}</span></a>')
    out.append('</nav>')
    return "".join(out)


NAV = [("index", "Index", "square"), ("year", "Year", "circle"), ("goals", "Goals", "arch"),
       ("habits", "Habits", "half"), ("notes", "Notes", "line")]


def topnav(current=None):
    out = ['<nav class="topnav">']
    for t, label, k in NAV:
        on = "on" if t == current else ""
        out.append(f'<a href="#{t}" class="{on}">{shape(k, "currentColor", 8)}<span>{label}</span></a>')
    out.append('</nav>')
    return "".join(out)


def page(pid, body, cls="", active_month=None, nav=None, style=""):
    return (f'<section class="page {cls}" id="{pid}" style="{style}">{tabs(active_month)}'
            f'<div class="frame">{topnav(nav)}{body}</div></section>')


def header(kicker, title, sub="", badge="", right=""):
    return f'''
    <header class="hd">
      {badge}
      <div class="ttl">
        <div class="label">{kicker}</div>
        <h1>{title}</h1>
        {f'<div class="sub">{sub}</div>' if sub else ''}
      </div>
      <div class="hd-right">{right}</div>
    </header>'''


def art_badge(m):
    return f'<a href="#o{m:02d}" class="badge artb">{art(m)}</a>'


def arch_badge(top, num, color):
    ct = TABTXT[MAIN.index(color)] if color in MAIN else "#F6EEDF"
    return f'<div class="badge archb" style="--c:{color};--ct:{ct}"><span class="bk">{top}</span><span class="bn">{num}</span></div>'


def mini_month(m, link_days=False, cls="", moons=False):
    weeks = cal.monthdatescalendar(YEAR, m)
    while len(weeks) < 6:
        last = weeks[-1][-1]
        weeks.append([last + dt.timedelta(days=i + 1) for i in range(7)])
    head = "".join(f"<i>{d[0]}</i>" for d in DOW)
    cells = []
    for wk in weeks:
        for d in wk:
            if d.month != m:
                cells.append('<span class="out"></span>')
                continue
            c = "we" if d.weekday() >= 5 else ""
            ph = MOON.get(d.isoformat())
            if ph == "full":
                c += " fm"
            inner = str(d.day) + (moon_icon(ph, 9) if moons and ph else "")
            if link_days and day_id(d) in EXISTING:
                cells.append(f'<a href="#{day_id(d)}" class="{c} lk">{inner}</a>')
            else:
                cells.append(f'<span class="{c}">{inner}</span>')
    return f'<div class="mini {cls}"><div class="mh">{head}</div><div class="mg">{"".join(cells)}</div></div>'


def week_strip(start, current=None):
    out = ['<div class="wstrip">']
    for i in range(7):
        d = start + dt.timedelta(days=i)
        on = " on" if current == d else ""
        inner = f'{day_shape(d, 8)}<span>{d.day}</span>'
        if day_id(d) in EXISTING:
            out.append(f'<a href="#{day_id(d)}" class="wd lk{on}">{inner}</a>')
        else:
            out.append(f'<span class="wd{on}">{inner}</span>')
    out.append('</div>')
    return "".join(out)


# ---------------------------------------------------------------- pages

def cover():
    arches = "".join(
        f'<a href="#o{m:02d}" class="carch"><span class="cframe">{art(m)}</span>'
        f'<span class="clab">{m:02d}</span></a>' for m in range(1, 13))
    return f'''
    <section class="page cover" id="cover"><div class="frame">
      <div class="cv-left">
        <div class="cv-kicker">Atelier Soleil</div>
        <div class="cv-year">{YEAR}</div>
        <div class="cv-sub">Twelve months,<br><em>twelve small suns.</em></div>
        <div class="cv-rule"></div>
        <div class="cv-meta">
          <div><span>Belongs to</span><i></i></div>
          <div><span>If found</span><i></i></div>
        </div>
        <a href="#index" class="cv-enter"><span>Open the planner</span><b><svg width="20" height="10" viewBox="0 0 20 10"><path d="M1 5H18M13.5 1.2L18.4 5L13.5 8.8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg></b></a>
        <div class="cv-foot">Monday start &nbsp;&middot;&nbsp; Moon phases (KST) &nbsp;&middot;&nbsp; Hyperlinked</div>
      </div>
      <div class="cv-grid">{arches}</div>
    </div></section>'''


def divider(m):
    weeks = cal.monthdatescalendar(YEAR, m)
    head = "".join(f'<i>{shape(DAYSHAPE[i][0], DAYSHAPE[i][1], 8)}{DOW[i][0]}</i>' for i in range(7))
    cells = []
    for wk in weeks:
        for d in wk:
            if d.month != m:
                cells.append('<span class="out"></span>')
                continue
            ph = MOON.get(d.isoformat())
            c = "we" if d.weekday() >= 5 else ""
            inner = f'<b>{d.day}</b>{moon_icon(ph, 10) if ph else ""}'
            cells.append(link(day_id(d), inner, c + " lk") if day_id(d) in EXISTING else f'<span class="{c}">{inner}</span>')
    phases = [(k, v) for k, v in MOON.items() if k.startswith(f"{YEAR}-{m:02d}")]
    legend = "".join(f'<span>{moon_icon(v, 11)}<em>{int(k[-2:])}</em></span>' for k, v in phases)
    return f'''
    <section class="page divider" id="o{m:02d}" style="--c:{MAIN[m-1]};--l:{LIGHT[m-1]};--ct:{TABTXT[m-1]}">
      {tabs(m)}
      <div class="dv-block">
        <div class="dv-top label">N&deg; {m:02d} &nbsp;&middot;&nbsp; {SEASON[m-1]}</div>
        <a href="#m{m:02d}" class="dv-art"><span class="dv-outline"></span>{art(m)}</a>
        <div class="dv-cap"><em>&ldquo;{TITLES[m-1]}&rdquo;</em><span class="label">Cut paper &middot; {YEAR}</span></div>
      </div>
      <div class="dv-right">
        {topnav()}
        <div class="label dv-k">Month {m:02d} of 12</div>
        <h1 class="dv-name">{MONTHS[m-1]}</h1>
        <p class="dv-quote">{QUOTE[m-1]}</p>
        <div class="dv-mid">
          <div class="dv-cal"><div class="dh7">{head}</div><div class="dg7">{"".join(cells)}</div>
            <div class="dv-legend">{legend}</div></div>
          <div class="block dv-dates"><div class="label">Key dates</div>{lines(7, 30)}</div>
        </div>
        <div class="dv-prompts">
          <div class="block"><div class="label">This month I will</div>{lines(4, 34)}</div>
          <div class="dv-two">
            <div class="block"><div class="label">Looking forward to</div>{lines(3, 34)}</div>
            <div class="block"><div class="label">Letting go of</div>{lines(3, 34)}</div>
          </div>
        </div>
        <a href="#m{m:02d}" class="pill"><span>Open the calendar</span><b><svg width="20" height="10" viewBox="0 0 20 10"><path d="M1 5H18M13.5 1.2L18.4 5L13.5 8.8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg></b></a>
      </div>
    </section>'''


def index_page(pages):
    def row(sh, name, target, note=""):
        k, col = sh
        return (f'<a href="#{target}" class="toc-row">{shape(k, col, 14)}'
                f'<span class="toc-name">{name}{f"<em>{note}</em>" if note else ""}</span>'
                f'<span class="leader"></span><span class="pg">{pages[target]:02d}</span></a>')
    toc = "".join([
        row(("circle", "#C8643B"), "Year at a Glance", "year"),
        row(("arch", "#D08068"), "Intentions", "goals", "goals &amp; vision"),
        row(("sun", "#26374D"), "January", "o01", "month opener"),
        row(("square", "#6E7F5A"), "January Calendar", "m01", "monthly"),
        row(("half", "#2F6B6B"), "Rituals", "habits", "habit tracker"),
        row(("tri", "#D9A441"), "Week 01", week_id(WEEK_SAMPLE), "weekly spread"),
        row(("flower", "#6B3E4F"), "Monday, January 4", day_id(DAY_SAMPLE), "daily page"),
        row(("line", "#9C4A2E"), "Notes &amp; Dots", "notes", "lined / dot grid"),
    ])
    months = "".join(
        f'<a href="#o{i:02d}" class="colm">{art(i)}<span>{ABBR[i-1]}</span></a>' for i in range(1, 13))
    body = f'''
    <div class="index-wrap">
      <div class="index-left">
        <div class="label">Contents</div>
        <h1 class="big-italic">Index</h1>
        <p class="quote">Twelve small suns &mdash;<br>one for every month<br>you are about to live.</p>
        <div class="shapes-key">
          <div class="label">Shape of the days</div>
          <div class="keyrow">{"".join(f'<span>{shape(k, c, 13)}<em>{DOW[i]}</em></span>' for i, (k, c) in enumerate(DAYSHAPE))}</div>
          <div class="label" style="margin-top:22px">Moon phases</div>
          <div class="keyrow">{"".join(f'<span>{moon_icon(k, 13)}<em>{PHASE_NAME[k].split()[0]}</em></span>' for k in ("new", "first", "full", "last"))}</div>
        </div>
      </div>
      <div class="index-right">
        <div class="toc">{toc}</div>
        <div class="label mlabel">Months &mdash; tap an arch</div>
        <div class="colonnade">{months}</div>
      </div>
    </div>'''
    return page("index", body, "index", nav="index")


def year_page():
    cells = "".join(f'''
        <div class="ycell" style="--c:{MAIN[m-1]}">
          <a href="#m{m:02d}" class="yhead"><span class="ya">{art(m)}</span>
            <span class="yt"><em>{m:02d}</em><b>{MONTHS[m-1]}</b></span></a>
          {mini_month(m, link_days=True)}
        </div>''' for m in range(1, 13))
    body = header("Year at a Glance", f"{YEAR}",
                  f'Full moons are circled &nbsp;{moon_icon("full", 11)}') + f'<div class="ygrid">{cells}</div>'
    return page("year", body, "year", nav="year")


def goals_page():
    areas = [("Body &amp; Health", ("circle", "#C8643B")), ("Work &amp; Craft", ("square", "#6E7F5A")),
             ("Love &amp; People", ("flower", "#6B3E4F")), ("Mind &amp; Rest", ("half", "#2F6B6B"))]
    boxes = "".join(f'''
      <div class="area">
        <div class="area-h">{shape(k, c, 20)}<span class="area-t">{t}</span></div>
        {lines(10, 34, "fill")}
        <div class="first"><span class="label">First step</span>{checks(1, 30)}</div>
      </div>''' for t, (k, c) in areas)
    rings = "".join(f'<circle cx="150" cy="300" r="{r}" fill="{c}"/>' for r, c in
                    ((96, "#EBC3B0"), (74, "#C8643B"), (52, "#D9A441"), (30, "#F6EEDF")))
    body = header("Intentions", "The year ahead", "What would make this year feel well spent?") + f'''
    <div class="goals">
      <div class="goals-left">
        <div class="word-arch">
          <svg class="wa-art" viewBox="0 0 300 300" preserveAspectRatio="xMidYMax slice">{rings}</svg>
          <div class="label">Word of the year</div>
          <div class="word-line"></div>
        </div>
        <div class="block"><div class="label">I want to feel</div>{lines(3, 34)}</div>
        <div class="block"><div class="label">I am letting go of</div>{lines(3, 34)}</div>
        <div class="block grow"><div class="label">Dear December me</div>{lines(6, 34, "fill")}</div>
      </div>
      <div class="areas">{boxes}</div>
    </div>'''
    return page("goals", body, "goals", nav="goals")


def month_page(m):
    weeks = cal.monthdatescalendar(YEAR, m)
    rows = []
    for wk in weeks:
        iso = wk[0].isocalendar()
        wn = link(week_id(wk[0]), f"W{iso[1]:02d}", "wk")
        cells = []
        for d in wk:
            cls = "cell" + (" out" if d.month != m else "") + (" we" if d.weekday() >= 5 else "")
            num = f'<span class="dn">{d.day}</span>'
            if d.month == m and day_id(d) in EXISTING:
                num = f'<a href="#{day_id(d)}" class="dn lk">{d.day}</a>'
            ph = MOON.get(d.isoformat()) if d.month == m else None
            mo = f'<span class="mi">{moon_icon(ph, 12)}</span>' if ph else ""
            first = f'<span class="m1">{ABBR[m-1]}</span>' if d.month == m and d.day == 1 else ""
            cells.append(f'<div class="{cls}">{num}{first}{mo}</div>')
        rows.append(f'<div class="mrow">{wn}{"".join(cells)}</div>')
    head = '<div class="mrow mhead"><span class="wk"></span>' + "".join(
        f'<span class="mh-d">{shape(DAYSHAPE[i][0], DAYSHAPE[i][1], 9)}<span class="label">{DOW[i]}</span></span>'
        for i in range(7)) + '</div>'
    nm = m % 12 + 1
    phases = [(k, v) for k, v in MOON.items() if k.startswith(f"{YEAR}-{m:02d}")]
    legend = "".join(f'<div class="ph">{moon_icon(v, 12)}<span>{PHASE_NAME[v]}</span><em>{MONTHS[m-1][:3]} {int(k[-2:])}</em></div>'
                     for k, v in phases)
    side = f'''
    <aside class="mside">
      <div class="block"><div class="label">Priorities</div>{checks(5)}</div>
      <div class="block grow"><div class="label">Notes</div>{lines(14, cls="fill")}</div>
      <div class="block moons"><div class="label">Moon</div>{legend}</div>
      <div class="block next"><div class="label">Next &middot; {MONTHS[nm-1] if nm != 1 else str(YEAR + 1)}</div>
        {mini_month(nm, cls="compact") if nm != 1 else '<div class="end-note">See you next year.</div>'}</div>
    </aside>'''
    right = f'<div class="crumbs label">{link("year", str(YEAR))} &nbsp;/&nbsp; {link(f"o{m:02d}", MONTHS[m-1] + " opener")}</div>'
    body = header(f"{SEASON[m-1]} &nbsp;&middot;&nbsp; Month {m:02d}", MONTHS[m - 1], QUOTE[m-1],
                  badge=art_badge(m), right=right) + f'''
    <div class="month">{side}<div class="mcal">{head}{"".join(rows)}</div></div>'''
    return page(f"m{m:02d}", body, "monthly", active_month=m, style=f"--c:{MAIN[m-1]};--l:{LIGHT[m-1]}")


def habits_page(m=1):
    nd = calendar.monthrange(YEAR, m)[1]
    days = [dt.date(YEAR, m, d) for d in range(1, nd + 1)]
    head = '<div class="hrow hhead"><span class="hname label">Ritual</span>' + "".join(
        f'<span class="hd-day{" we" if d.weekday() >= 5 else ""}">{day_shape(d, 7)}{d.day}</span>' for d in days) + \
        '<span class="htot label">Total</span></div>'
    rows = "".join(
        '<div class="hrow"><span class="hname"><i></i></span>' + "".join(
            f'<span class="hc{" we" if d.weekday() >= 5 else ""}"><b></b></span>' for d in days)
        + '<span class="htot"><i></i></span></div>' for _ in range(12))
    right = f'<div class="crumbs label">{link("year", str(YEAR))} &nbsp;/&nbsp; {link(f"m{m:02d}", MONTHS[m-1])}</div>'
    body = header(f"Habit Tracker &nbsp;&middot;&nbsp; {MONTHS[m-1]}", "Rituals", "Small things, done often.",
                  badge=art_badge(m), right=right) + f'''
    <div class="habits">
      <div class="hgrid">{head}{rows}</div>
      <div class="hfoot">
        <div class="block"><div class="label">What helped</div>{lines(2, 34)}</div>
        <div class="block"><div class="label">What got in the way</div>{lines(2, 34)}</div>
        <div class="block"><div class="label">Next month I&rsquo;ll try</div>{lines(2, 34)}</div>
      </div>
    </div>'''
    return page("habits", body, "habitp", active_month=m, nav="habits", style=f"--c:{MAIN[m-1]};--l:{LIGHT[m-1]}")


def week_page(start):
    iso = start.isocalendar()
    end = start + dt.timedelta(days=6)
    m = start.month
    days = []
    for i in range(7):
        d = start + dt.timedelta(days=i)
        ph = MOON.get(d.isoformat())
        title = (f'<span class="dl">{day_shape(d, 11)}<span class="label">{DOW[i]}</span>'
                 f'{moon_icon(ph, 11) if ph else ""}</span><span class="dnum">{d.day:02d}</span>')
        title = link(day_id(d), title, "dh lk") if day_id(d) in EXISTING else f'<span class="dh">{title}</span>'
        days.append(f'<div class="day{" we" if d.weekday() >= 5 else ""}">{title}{lines(14, 32, "fill")}</div>')
    days.append(f'<div class="day notebox"><span class="dh"><span class="dl">{shape("line", "#9C4A2E", 11)}'
                f'<span class="label">Notes</span></span><span class="dnum amp">&amp;</span></span>'
                f'<div class="dotwrap">{dotgrid(22)}</div></div>')
    hab = "".join('<div class="mh-row"><i></i>' + "<b></b>" * 7 + '</div>' for _ in range(4))
    side = f'''
    <aside class="wside">
      <div class="block"><div class="label">This week&rsquo;s focus</div>{lines(3)}</div>
      <div class="block"><div class="label">To do</div>{checks(8)}</div>
      <div class="block">
        <div class="label">Habits</div>
        <div class="mhabit"><div class="mh-row mh-head"><i></i>{"".join(f"<b>{shape(k, c, 8)}</b>" for k, c in DAYSHAPE)}</div>{hab}</div>
      </div>
      <div class="block grow"><div class="label">Looking ahead</div>{lines(10, cls="fill")}</div>
    </aside>'''
    sub = f"{MONTHS[start.month-1]} {start.day} &ndash; {MONTHS[end.month-1] + ' ' if end.month != start.month else ''}{end.day}, {YEAR}"
    right = (f'<div class="crumbs label">{link("year", str(YEAR))} &nbsp;/&nbsp; {link(f"m{m:02d}", MONTHS[m-1])}</div>'
             + week_strip(start))
    body = header("Weekly", f"Week {iso[1]:02d}", sub, badge=arch_badge("Week", f"{iso[1]:02d}", MAIN[m-1]),
                  right=right) + f'<div class="week">{side}<div class="wgrid">{"".join(days)}</div></div>'
    return page(week_id(start), body, "weekly", active_month=m, style=f"--c:{MAIN[m-1]};--l:{LIGHT[m-1]}")


def day_page(d):
    m = d.month
    hours = "".join(
        f'<div class="hr"><span class="t">{h if h <= 12 else h - 12}<em>{"am" if h < 12 else "pm"}</em></span><i></i></div>'
        for h in range(6, 23))
    doy = d.timetuple().tm_yday
    total = 366 if calendar.isleap(YEAR) else 365
    mon = d - dt.timedelta(days=d.weekday())
    k, waxing, pname = moon_today(d)
    nd, nv = next_phase(d)
    disc = (f'<svg width="30" height="30" viewBox="0 0 30 30">'
            f'{moon_phase_disc(15, 15, 13, k, waxing, "#E5B95C", "#3E3530")}'
            f'<circle cx="15" cy="15" r="13" fill="none" stroke="#3E3530" stroke-width=".8"/></svg>')
    moonw = (f'<div class="moonw">{disc}<div><b>{pname}</b>'
             f'<span>{PHASE_NAME[nv]} &middot; {MONTHS[nd.month-1][:3]} {nd.day}</span></div></div>')
    water = shape("drop", "var(--c)", 20, outline=True) * 8
    moods = "".join(f'<span class="mood">{shape(k_, "#BFAF99", 20, outline=True)}<em>{w}</em></span>'
                    for k_, w in (("drop", "low"), ("half", "meh"), ("circle", "okay"),
                                  ("flower", "good"), ("sun", "glow")))
    t3 = "".join(f'<div class="t3"><span style="background:{c}">{i}</span><i></i></div>'
                 for i, c in ((1, "#C8643B"), (2, "#D9A441"), (3, "#2F6B6B")))
    right = (f'<div class="hd-row">{moonw}{week_strip(mon, current=d)}</div>'
             f'<div class="crumbs label">{link(f"m{m:02d}", MONTHS[m-1])} &nbsp;/&nbsp; '
             f'{link(week_id(d), "Week " + f"{d.isocalendar()[1]:02d}")}</div>')
    body = header(f"Day {doy:03d} of {total}",
                  f'{calendar.day_name[d.weekday()]}', f"{MONTHS[m-1]} {d.day}, {YEAR}",
                  badge=arch_badge(DOW[d.weekday()], f"{d.day:02d}", MAIN[m-1]), right=right) + f'''
    <div class="daily">
      <div class="col sched"><div class="label">Schedule</div><div class="hours">{hours}</div></div>
      <div class="col mid">
        <div class="block top3"><div class="label">Top three</div>{t3}</div>
        <div class="block grow"><div class="label">To do</div>{checks(24, cls="fill")}</div>
      </div>
      <div class="col right">
        <div class="block grow"><div class="label">Notes</div><div class="dotwrap boxed">{dotgrid(24)}</div></div>
        <div class="block"><div class="label">Grateful for</div>{lines(3, 32)}</div>
        <div class="trackers">
          <div class="block"><div class="label">Water</div><div class="water">{water}</div></div>
          <div class="block"><div class="label">Mood</div><div class="moods">{moods}</div></div>
        </div>
      </div>
    </div>'''
    return page(day_id(d), body, "dailyp", active_month=m, style=f"--c:{MAIN[m-1]};--l:{LIGHT[m-1]}")


def notes_page():
    body = header("Notes", "Notes", "Date &nbsp;<i class='blank'></i>") + \
        f'<div class="notes-area">{lines(22, 34, "fill")}</div>'
    return page("notes", body, "notesp", nav="notes")


def dots_page():
    body = header("Sketch", "Dots &amp; drafts", "Date &nbsp;<i class='blank'></i>") + \
        f'<div class="dots-area">{dotgrid(26, 1.25, 4)}</div>'
    return page("dots", body, "dotsp", nav="notes")


# ---------------------------------------------------------------- assemble

def build():
    order = ["cover", "index", "year", "goals",
             "o01", "m01", "habits", week_id(WEEK_SAMPLE), day_id(DAY_SAMPLE)]
    for i in range(2, 13):
        order += [f"o{i:02d}", f"m{i:02d}"]
    order += ["notes", "dots"]
    pages = {pid: i + 1 for i, pid in enumerate(order)}
    render = {
        "cover": cover, "index": lambda: index_page(pages), "year": year_page,
        "goals": goals_page, "habits": habits_page, "notes": notes_page, "dots": dots_page,
        week_id(WEEK_SAMPLE): lambda: week_page(WEEK_SAMPLE),
        day_id(DAY_SAMPLE): lambda: day_page(DAY_SAMPLE),
    }
    for i in range(1, 13):
        render[f"m{i:02d}"] = (lambda i=i: month_page(i))
        render[f"o{i:02d}"] = (lambda i=i: divider(i))
    html_pages = "\n".join(render[p]() for p in order)
    fonts = (HERE / "fonts" / "local.css").read_text()
    css = (HERE / "style.css").read_text()
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Atelier Soleil {YEAR}</title>
<style>{fonts}
@page {{ size: {W}px {H}px; margin: 0; }}
{css}</style></head>
<body>{html_pages}
<script>{(HERE / "fill.js").read_text()}</script></body></html>'''
    (HERE / "planner.html").write_text(html)
    print(f"wrote planner.html with {len(order)} pages")


if __name__ == "__main__":
    build()
