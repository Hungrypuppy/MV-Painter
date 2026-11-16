#!/usr/bin/env python3
"""Atelier 2027 — GoodNotes planner sample (landscape iPad, 4:3).

Builds planner.html; render.js turns it into a hyperlinked PDF + PNG previews.
"""
import calendar
import datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
YEAR = 2027
W, H = 1366, 1024  # 4:3 landscape (iPad Pro 12.9" / 13" logical points)

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
ABBR = [m[:3].upper() for m in MONTHS]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# Muted seasonal palette, one hue per month (used by tabs + monthly accents)
TONE = ["#B7C0C4", "#C6BAC2", "#B9C3B0", "#D9C3B8", "#CFCBA9", "#AFC3BC",
        "#DCCBA8", "#D5AE94", "#C2AB8C", "#B09684", "#A6A497", "#9B96A6"]

cal = calendar.Calendar(firstweekday=0)

# Sample pages that exist for linking
WEEK_SAMPLE = dt.date(YEAR, 1, 4)  # ISO week 01 starts Mon Jan 4, 2027
DAY_SAMPLE = dt.date(YEAR, 1, 4)


def week_id(d):
    iso = d.isocalendar()
    return f"w{iso[0]}-{iso[1]:02d}"


def day_id(d):
    return f"d{d.isoformat()}"


EXISTING = {"cover", "index", "year", "goals", "habits", "notes", "dots",
            week_id(WEEK_SAMPLE), day_id(DAY_SAMPLE)} | {f"m{i:02d}" for i in range(1, 13)}


def link(target, inner, cls=""):
    if target in EXISTING:
        return f'<a href="#{target}" class="{cls}">{inner}</a>'
    return f'<span class="{cls}">{inner}</span>'


# ---------------------------------------------------------------- components

def lines(n, h=32, cls=""):
    return f'<div class="lines {cls}" style="--lh:{h}px">' + '<i></i>' * n + '</div>'


def checks(n, h=32, cls=""):
    return f'<div class="checks {cls}" style="--lh:{h}px">' + '<i><b></b></i>' * n + '</div>'


def dotgrid(step=24, r=1.15, pad=None):
    """Container filled at render time with an exactly-fitting, centred dot grid."""
    return f'<div class="dotfill" data-step="{step}" data-r="{r}" data-pad="{pad if pad is not None else step}"></div>'


DROP = ('<svg class="drop" width="16" height="22" viewBox="0 0 16 22">'
        '<path d="M8 1.2C8 1.2 1.6 9.6 1.6 14.2a6.4 6.4 0 0 0 12.8 0C14.4 9.6 8 1.2 8 1.2z"/></svg>')


def tabs(active=None):
    out = ['<nav class="tabs">']
    for i, a in enumerate(ABBR):
        on = " on" if active == i + 1 else ""
        out.append(f'<a href="#m{i + 1:02d}" class="tab{on}" style="--tone:{TONE[i]}"><span>{a}</span></a>')
    out.append('</nav>')
    return "".join(out)


def topnav(current=None):
    items = [("index", "Index"), ("year", "Year"), ("goals", "Goals"),
             ("habits", "Habits"), ("notes", "Notes")]
    out = ['<nav class="topnav">']
    for i, (t, label) in enumerate(items):
        on = " on" if t == current else ""
        out.append(f'<a href="#{t}" class="{on.strip()}">{label}</a>')
    out.append('</nav>')
    return "".join(out)


def page(pid, body, cls="", active_month=None, nav=None, with_tabs=True):
    t = tabs(active_month) if with_tabs else ""
    n = topnav(nav) if with_tabs else ""
    return (f'<section class="page {cls}" id="{pid}">{t}'
            f'<div class="frame">{n}{body}</div></section>')


def mini_month(m, link_days=False, highlight=None, compact=False):
    weeks = cal.monthdatescalendar(YEAR, m)
    while len(weeks) < 6:
        last = weeks[-1][-1]
        weeks.append([last + dt.timedelta(days=i + 1) for i in range(7)])
    head = "".join(f"<i>{d[0]}</i>" for d in DOW)
    cells = []
    for wk in weeks:
        for d in wk:
            c = "out" if d.month != m else ""
            if d.weekday() >= 5 and d.month == m:
                c += " we"
            if highlight and d == highlight:
                c += " hi"
            txt = str(d.day) if d.month == m else ""
            if link_days and d.month == m and day_id(d) in EXISTING:
                cells.append(f'<a href="#{day_id(d)}" class="{c}">{txt}</a>')
            else:
                cells.append(f'<span class="{c}">{txt}</span>')
    return f'<div class="mini{" compact" if compact else ""}"><div class="mh">{head}</div><div class="mg">{"".join(cells)}</div></div>'


# ---------------------------------------------------------------- pages

def cover():
    body = f'''
    <div class="cover-arch">
      <div class="arch-outer"></div>
      <div class="arch">
        <div class="sun"></div>
        <div class="ground"></div>
        <div class="ripple r1"></div><div class="ripple r2"></div><div class="ripple r3"></div>
        <div class="arch-foot">
          <span class="label">Volume</span>
          <span class="arch-num">MMXXVII</span>
        </div>
      </div>
    </div>
    <div class="cover-text">
      <div class="label kicker">The Atelier Planner</div>
      <div class="cover-year">{YEAR}</div>
      <div class="cover-sub">a year, beautifully kept.</div>
      <div class="rule-gold"></div>
      <div class="cover-meta">
        <div><span class="label">Belongs to</span><i></i></div>
        <div><span class="label">If found</span><i></i></div>
      </div>
      <a href="#index" class="enter"><span class="label">Open the planner</span><span class="arrow">&#8594;</span></a>
    </div>
    <div class="cover-foot label">January &mdash; December &nbsp;&middot;&nbsp; Monday start &nbsp;&middot;&nbsp; Hyperlinked</div>
    '''
    return f'<section class="page cover" id="cover"><div class="frame">{body}</div></section>'


def header(kicker, title, sub="", numeral="", tone=None, right=""):
    num = f'<div class="numeral" style="{f"--tone:{tone}" if tone else ""}">{numeral}</div>' if numeral else ""
    return f'''
    <header class="hd">
      {num}
      <div class="ttl">
        <div class="label">{kicker}</div>
        <h1>{title}</h1>
        {f'<div class="sub">{sub}</div>' if sub else ''}
      </div>
      <div class="hd-right">{right}</div>
    </header>'''


def index_page(pages):
    def row(roman, name, target, note=""):
        return (f'<a href="#{target}" class="toc-row"><span class="roman">{roman}</span>'
                f'<span class="toc-name">{name}{f"<em>{note}</em>" if note else ""}</span>'
                f'<span class="leader"></span><span class="pg">{pages[target]:02d}</span></a>')

    toc = "".join([
        row("I", "Year at a Glance", "year"),
        row("II", "Intentions", "goals", "goals &amp; vision"),
        row("III", "January", "m01", "monthly overview"),
        row("IV", "Habit Tracker", "habits", "january"),
        row("V", "Week 01", week_id(WEEK_SAMPLE), "weekly spread"),
        row("VI", "Monday, January 4", day_id(DAY_SAMPLE), "daily page"),
        row("VII", "Notes", "notes", "lined"),
        row("VIII", "Sketch &amp; Dots", "dots", "dot grid"),
    ])
    months = "".join(
        f'<a href="#m{i + 1:02d}" class="mchip" style="--tone:{TONE[i]}"><span class="mn">{i + 1:02d}</span>'
        f'<span class="mt">{MONTHS[i]}</span></a>' for i in range(12))
    body = f'''
    <div class="index-wrap">
      <div class="index-left">
        <div class="label">Contents</div>
        <h1 class="big-italic">Index</h1>
        <p class="quote">&ldquo;Small, quiet steps,<br>taken every day.&rdquo;</p>
        <div class="rule-gold short"></div>
        <div class="howto">
          <div class="label">How to use</div>
          <p>Tap any tab, title or date to jump. The month tabs on the right edge follow you through every page.</p>
        </div>
      </div>
      <div class="index-right">
        <div class="toc">{toc}</div>
        <div class="label mlabel">Months</div>
        <div class="mchips">{months}</div>
      </div>
    </div>'''
    return page("index", body, "index", nav="index")


def year_page():
    cells = []
    for m in range(1, 13):
        cells.append(f'''
        <div class="ycell">
          <a href="#m{m:02d}" class="yhead"><span class="yn" style="color:{TONE[m-1]}">{m:02d}</span>
          <span class="ym">{MONTHS[m-1]}</span></a>
          {mini_month(m, link_days=True)}
        </div>''')
    body = header("Year at a Glance", f"{YEAR}", "Twelve months, one page.") + \
        f'<div class="ygrid">{"".join(cells)}</div>'
    return page("year", body, "year", nav="year")


def goals_page():
    areas = [("Body &amp; Health", "i"), ("Work &amp; Craft", "ii"),
             ("Love &amp; People", "iii"), ("Mind &amp; Rest", "iv")]
    boxes = "".join(f'''
      <div class="area">
        <div class="area-h"><span class="roman">{r}</span><span class="area-t">{t}</span></div>
        {lines(10, 34, "fill")}
        <div class="first"><span class="label">First step</span>{checks(1, 30)}</div>
      </div>''' for t, r in areas)
    body = header("Intentions", "The year ahead", "What would make this year feel well spent?") + f'''
    <div class="goals">
      <div class="goals-left">
        <div class="word-arch">
          <div class="label">Word of the year</div>
          <div class="word-line"></div>
        </div>
        <div class="block">
          <div class="label">I want to feel</div>
          {lines(3, 34)}
        </div>
        <div class="block">
          <div class="label">I am letting go of</div>
          {lines(3, 34)}
        </div>
        <div class="block grow">
          <div class="label">Dear December me</div>
          {lines(6, 34, "fill")}
        </div>
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
            cls = "cell"
            if d.month != m:
                cls += " out"
            if d.weekday() >= 5:
                cls += " we"
            num = f'<span class="dn">{d.day}</span>'
            if d.month == m and day_id(d) in EXISTING:
                num = f'<a href="#{day_id(d)}" class="dn">{d.day}</a>'
            cells.append(f'<div class="{cls}">{num}</div>')
        rows.append(f'<div class="mrow">{wn}{"".join(cells)}</div>')
    head = '<div class="mrow mhead"><span class="wk"></span>' + \
        "".join(f'<span class="label">{d}</span>' for d in DOW) + '</div>'

    nm = m % 12 + 1
    next_mini = f'''
      <div class="block next">
        <div class="label">Next &middot; {MONTHS[nm-1]}</div>
        {mini_month(nm, compact=True) if nm != 1 else '<div class="end-note">See you in ' + str(YEAR + 1) + '.</div>'}
      </div>'''
    side = f'''
    <aside class="mside">
      <div class="block"><div class="label">Monthly focus</div>{lines(3)}</div>
      <div class="block"><div class="label">Priorities</div>{checks(5)}</div>
      <div class="block grow"><div class="label">Notes</div>{lines(12, cls="fill")}</div>
      {next_mini}
    </aside>'''
    right = f'<div class="crumbs label">{YEAR} &nbsp;/&nbsp; {link("year", "Year")}</div>'
    body = header(f"Month {m:02d} of 12", MONTHS[m - 1], f"{YEAR}",
                  numeral=f"{m:02d}", tone=TONE[m - 1], right=right) + f'''
    <div class="month">
      {side}
      <div class="mcal" style="--rows:{len(weeks)}">{head}{"".join(rows)}</div>
    </div>'''
    return page(f"m{m:02d}", body, "monthly", active_month=m)


def habits_page(m=1):
    ndays = calendar.monthrange(YEAR, m)[1]
    head = '<div class="hrow hhead"><span class="hname label">Habit</span>' + "".join(
        f'<span class="hd-day{" we" if dt.date(YEAR, m, d).weekday() >= 5 else ""}">'
        f'<em>{DOW[dt.date(YEAR, m, d).weekday()][0]}</em>{d}</span>' for d in range(1, ndays + 1)) + \
        '<span class="htot label">Total</span></div>'
    rows = "".join(
        '<div class="hrow"><span class="hname"><i></i></span>' + "".join(
            f'<span class="hc{" we" if dt.date(YEAR, m, d).weekday() >= 5 else ""}"><b></b></span>'
            for d in range(1, ndays + 1)) + '<span class="htot"><i></i></span></div>'
        for _ in range(12))
    right = f'<div class="crumbs label">{YEAR} &nbsp;/&nbsp; {link(f"m{m:02d}", MONTHS[m-1])}</div>'
    body = header("Habit Tracker", "Rituals", f"{MONTHS[m-1]} {YEAR}", right=right) + f'''
    <div class="habits">
      <div class="hgrid">{head}{rows}</div>
      <div class="hfoot">
        <div class="block"><div class="label">What helped</div>{lines(2, 34)}</div>
        <div class="block"><div class="label">What got in the way</div>{lines(2, 34)}</div>
        <div class="block"><div class="label">Next month I&rsquo;ll try</div>{lines(2, 34)}</div>
      </div>
    </div>'''
    return page("habits", body, "habitp", active_month=m, nav="habits")


def week_strip(start, current=None, link_days=True):
    out = ['<div class="wstrip">']
    for i in range(7):
        d = start + dt.timedelta(days=i)
        on = " on" if current == d else ""
        inner = f'<em>{DOW[d.weekday()][0]}</em><span>{d.day}</span>'
        if link_days and day_id(d) in EXISTING:
            out.append(f'<a href="#{day_id(d)}" class="wd{on}">{inner}</a>')
        else:
            out.append(f'<span class="wd{on}">{inner}</span>')
    out.append('</div>')
    return "".join(out)


def week_page(start):
    iso = start.isocalendar()
    end = start + dt.timedelta(days=6)
    days = []
    for i in range(7):
        d = start + dt.timedelta(days=i)
        title = (f'<span class="label">{DOW[d.weekday()]}</span>'
                 f'<span class="dnum">{d.day:02d}</span>')
        title = link(day_id(d), title, "dh") if day_id(d) in EXISTING else f'<span class="dh">{title}</span>'
        days.append(f'<div class="day{" we" if d.weekday() >= 5 else ""}">{title}{lines(14, 32, "fill")}</div>')
    days.append(f'<div class="day notebox"><span class="dh"><span class="label">Notes</span>'
                f'<span class="dnum ital">&amp;</span></span>'
                f'<div class="dotwrap">{dotgrid(22)}</div></div>')
    hab = "".join('<div class="mh-row"><i></i>' + "<b></b>" * 7 + '</div>' for _ in range(4))
    side = f'''
    <aside class="wside">
      <div class="block"><div class="label">This week&rsquo;s focus</div>{lines(3)}</div>
      <div class="block"><div class="label">To do</div>{checks(8)}</div>
      <div class="block">
        <div class="label">Habits</div>
        <div class="mhabit"><div class="mh-row mh-head"><i></i>{"".join(f"<b>{d[0]}</b>" for d in DOW)}</div>{hab}</div>
      </div>
      <div class="block grow"><div class="label">Looking ahead</div>{lines(10, cls="fill")}</div>
    </aside>'''
    sub = f"{MONTHS[start.month-1]} {start.day} &mdash; {MONTHS[end.month-1] if end.month != start.month else ''}{end.day}, {YEAR}"
    right = (f'<div class="crumbs label">{YEAR} &nbsp;/&nbsp; {link(f"m{start.month:02d}", MONTHS[start.month-1])}</div>'
             + week_strip(start))
    body = header("Weekly", f"Week {iso[1]:02d}", sub, right=right) + f'''
    <div class="week">{side}<div class="wgrid">{"".join(days)}</div></div>'''
    return page(week_id(start), body, "weekly", active_month=start.month)


def day_page(d):
    hours = []
    for h in range(6, 23):
        lab = f"{h if h <= 12 else h - 12}"
        ap = "am" if h < 12 else "pm"
        hours.append(f'<div class="hr"><span class="t">{lab}<em>{ap}</em></span><i></i></div>')
    doy = d.timetuple().tm_yday
    total = 366 if calendar.isleap(YEAR) else 365
    mon = d - dt.timedelta(days=d.weekday())
    water = DROP * 8
    moods = "".join(f'<span class="mood"><b></b><em>{w}</em></span>'
                    for w in ["low", "meh", "okay", "good", "glow"])
    right = (f'<div class="crumbs label">{YEAR} &nbsp;/&nbsp; {link(f"m{d.month:02d}", MONTHS[d.month-1])}'
             f' &nbsp;/&nbsp; {link(week_id(d), "Week " + f"{d.isocalendar()[1]:02d}")}</div>'
             + week_strip(mon, current=d))
    body = header(f"Day {doy:03d} of {total}", calendar.day_name[d.weekday()],
                  f"{MONTHS[d.month-1]} {d.day}, {YEAR}", right=right) + f'''
    <div class="daily">
      <div class="col sched">
        <div class="label">Schedule</div>
        <div class="hours">{"".join(hours)}</div>
      </div>
      <div class="col mid">
        <div class="block top3">
          <div class="label">Top three</div>
          <div class="t3"><span>1</span><i></i></div>
          <div class="t3"><span>2</span><i></i></div>
          <div class="t3"><span>3</span><i></i></div>
        </div>
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
    return page(day_id(d), body, "dailyp", active_month=d.month)


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
    order = ["cover", "index", "year", "goals", "m01", "habits", week_id(WEEK_SAMPLE),
             day_id(DAY_SAMPLE)] + [f"m{i:02d}" for i in range(2, 13)] + ["notes", "dots"]
    pages = {pid: i + 1 for i, pid in enumerate(order)}
    render = {
        "cover": cover, "index": lambda: index_page(pages), "year": year_page,
        "goals": goals_page, "habits": habits_page, "notes": notes_page, "dots": dots_page,
        week_id(WEEK_SAMPLE): lambda: week_page(WEEK_SAMPLE),
        day_id(DAY_SAMPLE): lambda: day_page(DAY_SAMPLE),
    }
    for i in range(1, 13):
        render[f"m{i:02d}"] = (lambda i=i: month_page(i))
    html_pages = "\n".join(render[p]() for p in order)
    fonts = (HERE / "fonts" / "local.css").read_text()
    css = (HERE / "style.css").read_text()
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Atelier Planner {YEAR}</title>
<style>{fonts}
@page {{ size: {W}px {H}px; margin: 0; }}
{css}</style></head>
<body>{html_pages}
<script>{(HERE / "fill.js").read_text()}</script></body></html>'''
    (HERE / "planner.html").write_text(html)
    print(f"wrote planner.html with {len(order)} pages")


if __name__ == "__main__":
    build()
