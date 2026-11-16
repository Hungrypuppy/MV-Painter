"""2027 almanac (Korea): 24 solar terms, public holidays, Seoul sunrise/sunset.

All dates are local Korea time (KST, UTC+9). Computed with ephem.
"""
import datetime as dt
import math
from functools import lru_cache

import ephem

KST = dt.timedelta(hours=9)

# (sun ecliptic longitude, romanised Korean name, English gloss)
TERMS = [
    (285, "Sohan", "Lesser Cold"), (300, "Daehan", "Greater Cold"),
    (315, "Ipchun", "Start of Spring"), (330, "Usu", "Rain Water"),
    (345, "Gyeongchip", "Insects Awaken"), (0, "Chunbun", "Spring Equinox"),
    (15, "Cheongmyeong", "Clear & Bright"), (30, "Gogu", "Grain Rain"),
    (45, "Ipha", "Start of Summer"), (60, "Soman", "Grain Fills"),
    (75, "Mangjong", "Grain in Ear"), (90, "Haji", "Summer Solstice"),
    (105, "Soseo", "Lesser Heat"), (120, "Daeseo", "Greater Heat"),
    (135, "Ipchu", "Start of Autumn"), (150, "Cheoseo", "End of Heat"),
    (165, "Baengno", "White Dew"), (180, "Chubun", "Autumn Equinox"),
    (195, "Hallo", "Cold Dew"), (210, "Sanggang", "Frost Descends"),
    (225, "Ipdong", "Start of Winter"), (240, "Soseol", "Lesser Snow"),
    (255, "Daeseol", "Greater Snow"), (270, "Dongji", "Winter Solstice"),
]


def _sun_lon(t):
    s = ephem.Sun()
    s.compute(t)
    return math.degrees(ephem.Ecliptic(s, epoch=t).lon) % 360


def _crossing(target, start, end):
    """Time in (start, end) when sun longitude crosses target (bisection)."""
    def f(t):
        return ((_sun_lon(t) - target + 180) % 360) - 180
    a, b = start, end
    for _ in range(50):
        m = (a + b) / 2
        if f(a) * f(m) <= 0:
            b = m
        else:
            a = m
    return ephem.Date((a + b) / 2)


def kst_date(t):
    return (ephem.Date(t).datetime() + KST).date()


@lru_cache(None)
def solar_terms(year):
    out = {}
    t = ephem.Date(f"{year - 1}/12/15")
    end = ephem.Date(f"{year + 1}/01/10")
    while t < end:
        lon0, lon1 = _sun_lon(t), _sun_lon(t + 1)
        for deg, name, gloss in TERMS:
            d0 = (lon0 - deg) % 360
            d1 = (lon1 - deg) % 360
            if d0 > 300 and d1 < 60:
                hit = _crossing(deg, t, t + 1)
                d = kst_date(hit)
                if d.year == year:
                    out[d] = (name, gloss)
        t = ephem.Date(t + 1)
    return out


@lru_cache(None)
def new_moons(y0, y1):
    out, t = [], ephem.Date(f"{y0}/11/01")
    while True:
        t = ephem.next_new_moon(t)
        if t > ephem.Date(f"{y1}/02/01"):
            return out
        out.append(kst_date(t))
        t = ephem.Date(t + 1)


def _zhongqi(year):
    """Dates of the 12 principal terms (longitude multiple of 30) around the year."""
    dates = []
    for y in (year - 1, year, year + 1):
        for d, (name, _) in solar_terms(y).items():
            deg = next(x[0] for x in TERMS if x[1] == name)
            if deg % 30 == 0:
                dates.append(d)
    return sorted(dates)


@lru_cache(None)
def lunar_months(year):
    """List of (month_number, is_leap, start_date) covering the lunar year."""
    nms = new_moons(year - 1, year + 1)
    zq = _zhongqi(year)
    sol_prev = next(d for d in zq if d.year == year - 1 and d.month == 12 and d.day > 15)
    sol_this = next(d for d in zq if d.year == year and d.month == 12 and d.day > 15)
    m11a = max(n for n in nms if n <= sol_prev)
    m11b = max(n for n in nms if n <= sol_this)
    span = [n for n in nms if m11a <= n <= m11b]
    leap_needed = len(span) - 1 == 13
    months, num, leap_used = [], 11, False
    for i, start in enumerate(span[:-1]):
        nxt = span[i + 1]
        has_zq = any(start <= z < nxt for z in zq)
        if i > 0:
            if leap_needed and not leap_used and not has_zq:
                months.append((num, True, start))
                leap_used = True
                continue
            num = num % 12 + 1
        months.append((num, False, start))
    return months


def lunar_to_solar(year, month, day):
    for i, (num, leap, start) in enumerate(lunar_months(year)):
        if num == month and not leap and start.year >= year - 0 and (month < 11 or start.year == year):
            return start + dt.timedelta(days=day - 1)
    raise ValueError


@lru_cache(None)
def kr_holidays(year):
    """Korean public holidays incl. substitute holidays (current rules)."""
    D = dt.date
    hol = {}

    def add(d, name):
        hol.setdefault(d, name)

    add(D(year, 1, 1), "New Year")
    seollal = lunar_to_solar(year, 1, 1)
    seol = [seollal - dt.timedelta(days=1), seollal, seollal + dt.timedelta(days=1)]
    for d in seol:
        add(d, "Seollal")
    add(D(year, 3, 1), "Samiljeol")
    add(D(year, 5, 5), "Children's Day")
    buddha = lunar_to_solar(year, 4, 8)
    add(buddha, "Buddha's Day")
    add(D(year, 6, 6), "Memorial Day")
    add(D(year, 8, 15), "Liberation Day")
    chuseok = lunar_to_solar(year, 8, 15)
    chu = [chuseok - dt.timedelta(days=1), chuseok, chuseok + dt.timedelta(days=1)]
    for d in chu:
        add(d, "Chuseok")
    add(D(year, 10, 3), "Foundation Day")
    add(D(year, 10, 9), "Hangeul Day")
    add(D(year, 12, 25), "Christmas")

    def next_free(d):
        d = d + dt.timedelta(days=1)
        while d.weekday() >= 5 or d in hol:
            d += dt.timedelta(days=1)
        return d

    subs = []
    # Seollal / Chuseok: a day falling on Sunday (or on another holiday) -> one substitute
    for block in (seol, chu):
        if any(d.weekday() == 6 for d in block):
            subs.append(next_free(block[-1]))
    # Weekend-sensitive days (Sat or Sun)
    for d in [D(year, 3, 1), D(year, 5, 5), buddha, D(year, 8, 15), D(year, 10, 3),
              D(year, 10, 9), D(year, 12, 25)]:
        if d.weekday() >= 5:
            subs.append(next_free(d))
    for s in subs:
        hol[s] = "Substitute"
    return dict(sorted(hol.items()))


SEOUL = ("37.5665", "126.9780")


@lru_cache(None)
def sun_times(d):
    """(sunrise, sunset, daylight minutes) in Seoul, KST."""
    o = ephem.Observer()
    o.lat, o.lon = SEOUL
    o.pressure = 0
    o.horizon = "-0:34"  # refraction; ephem adds the solar radius itself
    o.date = ephem.Date(dt.datetime(d.year, d.month, d.day) - KST)
    sun = ephem.Sun()
    rise = ephem.Date(o.next_rising(sun)).datetime() + KST
    sset = ephem.Date(o.next_setting(sun)).datetime() + KST
    return rise, sset, round((sset - rise).total_seconds() / 60)


if __name__ == "__main__":
    print("lunar months:", [(m, l, s.isoformat()) for m, l, s in lunar_months(2027)])
    print("holidays:")
    for d, n in kr_holidays(2027).items():
        print("  ", d, d.strftime("%a"), n)
    print("terms:", [(d.isoformat(), n) for d, (n, g) in solar_terms(2027).items()])
    r, s, mins = sun_times(dt.date(2027, 1, 4))
    print("Seoul Jan 4:", r.strftime("%H:%M"), s.strftime("%H:%M"), mins)
