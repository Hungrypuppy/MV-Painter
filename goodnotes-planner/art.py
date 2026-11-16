"""Cut-paper (mid-century) artworks, one per month, drawn in a 400x560 arch window."""
import math
import random
import re

CREAM = "#F6EEDF"
NAVY, NAVY_D, DUSTY, FROST = "#26374D", "#1A2738", "#9DB4C0", "#C9D6DC"
OCHRE, MUSTARD = "#D9A441", "#C99A3B"
PLUM, BLUSH, ROSE = "#6B3E4F", "#EBC3B0", "#C97B6E"
OLIVE, OLIVE_D, SAGE, PALEGREEN = "#6E7F5A", "#4B5B3E", "#A9B78E", "#DCE3C8"
TERRA, BURNT, DEEPRED, PEACH = "#C8643B", "#C0562F", "#9C3D2A", "#F3C7A3"
SKY, TEAL, TEAL_D, MINT, SEAFOAM = "#B7CCD8", "#2F6B6B", "#1F4E4F", "#CFE0D8", "#8DB8AE"
WHEAT, BROWN, RUST = "#EADFC4", "#6A3F2B", "#9C4A2E"
SLATE, SLATE_D, FOREST, FOREST_D, RED = "#4B4E57", "#34363D", "#2F4A3A", "#1F3328", "#A63D32"

ARCH = "M0 560V200A200 200 0 0 1 400 200V560Z"

TITLES = ["Winter Night", "Two Hearts", "First Green", "April Showers", "In Bloom",
          "High Tide", "Midsummer", "Long Sunset", "Harvest", "Falling Leaves",
          "Quiet Moons", "Evergreen"]


def _o(o):
    return f' opacity="{o}"' if o is not None else ""


def c(cx, cy, r, f, o=None):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{f}"{_o(o)}/>'


def ring(cx, cy, r, col, sw=1.2, o=None):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}"{_o(o)}/>'


def rect(x, y, w, h, f, rx=0, o=None):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{f}"{_o(o)}/>'


def path(d, f, o=None):
    return f'<path d="{d}" fill="{f}"{_o(o)}/>'


def stroke(d, col, sw, o=None, cap="round"):
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="{cap}"{_o(o)}/>'


def leaf(x, y, length, width, angle, fill, vein=None):
    L, w = length, width
    d = f"M0 0Q{w:.1f} {-L * .45:.1f} 0 {-L:.1f}Q{-w:.1f} {-L * .45:.1f} 0 0Z"
    v = (f'<path d="M0 -4L0 {-L * .86:.1f}" stroke="{vein}" stroke-width="1.6" '
         f'stroke-linecap="round" opacity=".55"/>') if vein else ""
    return f'<g transform="translate({x} {y}) rotate({angle})"><path d="{d}" fill="{fill}"/>{v}</g>'


def sparkle(cx, cy, r, f):
    return path(f"M{cx} {cy - r}Q{cx} {cy} {cx + r} {cy}Q{cx} {cy} {cx} {cy + r}"
                f"Q{cx} {cy} {cx - r} {cy}Q{cx} {cy} {cx} {cy - r}Z", f)


def specks(seed, n, x0, y0, x1, y1, col, rmin=1.0, rmax=2.0, omin=.45, omax=.95):
    rng = random.Random(seed)
    return "".join(c(rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(rmin, rmax), col,
                     round(rng.uniform(omin, omax), 2)) for _ in range(n))


def tri(x, base, h, w, f):
    return path(f"M{x} {base - h}L{x + w / 2} {base}L{x - w / 2} {base}Z", f)


def tree(x, base, h, w, f):
    out = ""
    for i, k in enumerate((1.0, .78, .56)):
        out += tri(x, base - h * (1 - k) * .9, h * .48, w * k, f)
    return out


def waves(y, amp, period, f, shift=0):
    d = f"M{-period + shift} {y}"
    x = -period + shift
    while x < 400 + period:
        d += f"A{period / 2} {amp} 0 0 1 {x + period} {y}"
        x += period
    d += f"L{x} 600L{-period + shift} 600Z"
    return path(d, f)


def rays(cx, cy, n, r0, r1, half_deg, cols, rot=0, o=None):
    out = ""
    for i in range(n):
        a = math.radians(rot + i * 360 / n)
        h = math.radians(half_deg)
        p = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
             (cx + r1 * math.cos(a - h), cy + r1 * math.sin(a - h)),
             (cx + r1 * math.cos(a + h), cy + r1 * math.sin(a + h))]
        out += path("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in p) + "Z", cols[i % len(cols)], o)
    return out


def flower(cx, cy, r, petal, center, n=6, rot=0):
    out = ""
    for i in range(n):
        a = math.radians(rot + i * 360 / n)
        out += c(cx + r * .62 * math.cos(a), cy + r * .62 * math.sin(a), r * .48, petal)
    return out + c(cx, cy, r * .42, center)


def grain_stalk(x0, y0, x1, y1, col, grain):
    out = stroke(f"M{x0} {y0}Q{x0 + (x1 - x0) * .2} {(y0 + y1) / 2} {x1} {y1}", col, 3)
    for i in range(6):
        t = i / 6
        gx, gy = x1 + (x0 - x1) * t * .02, y1 + 14 + i * 15
        out += (f'<ellipse cx="{gx - 8:.1f}" cy="{gy:.1f}" rx="5" ry="10" fill="{grain}" transform="rotate(-32 {gx - 8:.1f} {gy:.1f})"/>'
                f'<ellipse cx="{gx + 8:.1f}" cy="{gy:.1f}" rx="5" ry="10" fill="{grain}" transform="rotate(32 {gx + 8:.1f} {gy:.1f})"/>')
    return out + f'<ellipse cx="{x1}" cy="{y1 + 2}" rx="5" ry="11" fill="{grain}"/>'


def moon_phase_disc(cx, cy, r, k, waxing, lit, dark):
    """k = illuminated fraction (0..1)."""
    if k <= .02:
        return c(cx, cy, r, dark)
    if k >= .98:
        return c(cx, cy, r, lit)
    rx = abs(1 - 2 * k) * r
    if waxing:
        d = (f"M{cx} {cy - r}A{r} {r} 0 0 1 {cx} {cy + r}"
             f"A{rx:.1f} {r} 0 0 {0 if k < .5 else 1} {cx} {cy - r}Z")
    else:
        d = (f"M{cx} {cy - r}A{r} {r} 0 0 0 {cx} {cy + r}"
             f"A{rx:.1f} {r} 0 0 {1 if k < .5 else 0} {cx} {cy - r}Z")
    return c(cx, cy, r, dark) + path(d, lit)


# ---------------------------------------------------------------- paper layers

SHADOW = "#1E140E"


def P(markup, o=.15):
    """Cut-paper layer: the markup plus a soft two-step drop shadow underneath."""
    sh = re.sub(r'fill="(?!none)[^"]+"', f'fill="{SHADOW}"', markup)
    sh = re.sub(r'stroke="[^"]+"', f'stroke="{SHADOW}"', sh)
    sh = re.sub(r' opacity="[^"]+"', "", sh)
    return (f'<g transform="translate(3 5)" opacity="{o * .45:.3f}">{sh}</g>'
            f'<g transform="translate(1.4 2.4)" opacity="{o:.3f}">{sh}</g>{markup}')


def crescent(ax, ay, ar, bx, by, br, f):
    """Part of circle A not covered by circle B, as one cut shape."""
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    a = (ar * ar - br * br + d * d) / (2 * d)
    h = math.sqrt(ar * ar - a * a)
    px, py = ax + a * ux, ay + a * uy
    p1 = (px - h * uy, py + h * ux)
    p2 = (px + h * uy, py - h * ux)
    return path(f"M{p1[0]:.2f} {p1[1]:.2f}A{ar} {ar} 0 1 1 {p2[0]:.2f} {p2[1]:.2f}"
                f"A{br} {br} 0 0 0 {p1[0]:.2f} {p1[1]:.2f}Z", f)


# ---------------------------------------------------------------- compositions

def jan(u):
    return (rect(0, 0, 400, 560, NAVY)
            + specks(1, 46, 10, 20, 390, 360, CREAM, .8, 1.8)
            + ring(255, 175, 96, CREAM, 1, .22) + ring(255, 175, 128, CREAM, 1, .1)
            + P(crescent(255, 175, 62, 283, 154, 55, CREAM), .3)
            + P(sparkle(112, 150, 15, OCHRE), .3) + sparkle(168, 92, 8, OCHRE)
            + sparkle(330, 300, 9, CREAM) + sparkle(76, 290, 6, CREAM)
            + P(c(-60, 720, 330, DUSTY), .3) + P(c(470, 770, 330, FROST), .3)
            + P(tree(64, 418, 70, 34, NAVY_D) + tree(106, 404, 92, 44, NAVY_D)
                + tree(150, 420, 58, 30, NAVY_D), .25) + P(tree(318, 458, 64, 32, "#7F9AA8"))
            + P(c(200, 1010, 540, CREAM), .22)
            + specks(11, 18, 30, 480, 370, 556, "#D9E2E6", 1.2, 2.4, .7, 1))


def feb(u):
    clip = f'<clipPath id="{u}o"><circle cx="160" cy="300" r="122"/></clipPath>'
    stripes = "".join(rect(28 + i * 15, 0, 5, 250, ROSE, o=.5) for i in range(8))
    return (f"<defs>{clip}</defs>" + rect(0, 0, 400, 560, BLUSH) + stripes
            + P(c(160, 300, 122, ROSE)) + P(c(258, 244, 108, PLUM))
            + f'<g clip-path="url(#{u}o)">{c(258, 244, 108, "#8E4A55")}</g>'
            + P(c(312, 118, 20, CREAM)) + c(96, 160, 9, PLUM) + P(c(332, 380, 12, CREAM))
            + P(c(200, 880, 380, "#F7E6DA"))
            + "".join(c(90 + i * 44, 520, 5, PLUM, .75) for i in range(6))
            + specks(2, 24, 20, 330, 380, 470, CREAM, 1.2, 2.2, .6, .95))


def mar(u):
    return (rect(0, 0, 400, 560, PALEGREEN)
            + ring(288, 150, 62, TERRA, 1.2, .35) + ring(288, 150, 86, TERRA, 1, .18)
            + P(c(288, 150, 38, TERRA))
            + specks(3, 26, 20, 60, 380, 300, OLIVE, 1, 2, .35, .7)
            + P(c(200, 900, 420, OLIVE_D))
            + P(leaf(200, 520, 330, 62, -28, OLIVE, CREAM))
            + P(leaf(200, 520, 392, 66, 4, "#879772", CREAM))
            + P(leaf(200, 520, 300, 58, 33, OLIVE_D, CREAM))
            + P(leaf(118, 530, 150, 30, -52, SAGE)) + P(leaf(292, 530, 160, 30, 50, SAGE)))


def apr(u):
    rain = ""
    rng = random.Random(4)
    for row in range(4):
        for i in range(7):
            x = 104 + i * 32 + (row % 2) * 16 + rng.uniform(-3, 3)
            y = 236 + row * 30 + rng.uniform(-4, 4)
            rain += rect(x, y, 3.2, 18, NAVY, 1.6, .78)
    cloud = (c(148, 176, 46, CREAM) + c(202, 152, 60, CREAM) + c(258, 178, 44, CREAM)
             + c(106, 200, 30, CREAM) + rect(100, 180, 200, 50, CREAM, 25))
    return (rect(0, 0, 400, 560, SKY)
            + specks(5, 14, 30, 60, 370, 140, CREAM, 1, 2, .5, .9)
            + P(c(200, 560, 214, BLUSH)) + P(c(200, 560, 174, TERRA)) + P(c(200, 560, 134, OCHRE))
            + P(c(200, 560, 94, CREAM)) + P(c(200, 560, 54, SKY))
            + rain + P(cloud, .18))


def may(u):
    return (rect(0, 0, 400, 560, "#F4DCCD")
            + specks(6, 22, 20, 40, 380, 200, TERRA, 1, 2, .3, .6)
            + P(c(200, 880, 400, OLIVE))
            + P(stroke("M200 560Q192 420 200 250", OLIVE_D, 4.5)
                + stroke("M128 560Q112 450 120 330", OLIVE_D, 4)
                + stroke("M284 560Q300 430 290 302", OLIVE_D, 4))
            + P(leaf(198, 410, 80, 22, -58, SAGE) + leaf(204, 455, 78, 22, 56, SAGE)
                + leaf(118, 430, 64, 18, -50, SAGE) + leaf(294, 420, 68, 18, 52, SAGE))
            + P(flower(200, 240, 50, TERRA, OCHRE))
            + P(flower(120, 330, 38, "#E9A58F", TERRA, 5, 18))
            + P(flower(290, 300, 42, CREAM, TERRA, 8)))


def jun(u):
    return (rect(0, 0, 400, 560, MINT)
            + specks(7, 14, 30, 60, 370, 300, CREAM, 1, 2.2, .6, 1)
            + ring(200, 196, 92, OCHRE, 1.4, .4) + ring(200, 196, 120, OCHRE, 1, .2)
            + P(c(200, 196, 64, OCHRE))
            + P(waves(330, 24, 84, SEAFOAM, 10)) + P(waves(378, 22, 72, "#4F8F8A", -20))
            + P(waves(428, 20, 92, TEAL, 30), .2) + P(waves(480, 16, 64, TEAL_D, 0), .25)
            + "".join(rect(60 + i * 64, 520, 22, 3, CREAM, 1.5, .55) for i in range(5)))


def jul(u):
    return (rect(0, 0, 400, 560, "#F6E3BF")
            + P(rays(200, 286, 20, 116, 460, 4.2, [TERRA, OCHRE], -90, .85), .1)
            + P(c(200, 286, 104, OCHRE)) + P(c(200, 286, 74, "#E7B356")) + P(c(200, 286, 44, "#F2CC7A"))
            + P(c(-20, 770, 270, "#A94F2E")) + P(c(200, 910, 420, TERRA))
            + specks(8, 16, 30, 500, 370, 556, "#F6E3BF", 1.2, 2.2, .5, .9))


def aug(u):
    refl = "".join(rect(200 - w / 2, 412 + i * 19, w, 3.2, "#F6DDB8", 1.6, .7)
                   for i, w in enumerate((150, 104, 64, 30)))
    return (rect(0, 0, 400, 560, PEACH)
            + specks(9, 20, 20, 40, 380, 190, CREAM, 1, 2, .55, .95)
            + P(c(200, 392, 206, DEEPRED)) + P(c(200, 392, 166, BURNT)) + P(c(200, 392, 126, OCHRE))
            + P(c(200, 392, 86, "#F6DDB8")) + P(c(200, 392, 48, TERRA))
            + P(rect(0, 392, 400, 170, "#7E2F22"), .25) + refl
            + rect(0, 391, 400, 1.5, "#F6DDB8", o=.5))


def sep(u):
    return (rect(0, 0, 400, 560, WHEAT)
            + ring(272, 168, 76, MUSTARD, 1.2, .4) + P(c(272, 168, 54, MUSTARD))
            + P(c(-40, 720, 320, OLIVE)) + P(c(440, 770, 320, "#8A6A3E"))
            + P(c(200, 930, 430, MUSTARD))
            + "".join(stroke(f"M{40 + i * 46} 556Q{60 + i * 46} 530 {54 + i * 46} 512", "#A88035", 2, .6)
                      for i in range(8))
            + P(grain_stalk(112, 560, 120, 262, BROWN, OCHRE))
            + P(grain_stalk(176, 560, 184, 232, BROWN, "#E5B85C"))
            + P(grain_stalk(300, 560, 292, 300, BROWN, OCHRE)))


def oct_(u):
    return (rect(0, 0, 400, 560, "#F1E2D0")
            + P(c(200, 250, 150, "#E8C3A0"), .1)
            + P(stroke("M-10 128Q150 150 312 210", BROWN, 5) + stroke("M170 160Q190 120 230 106", BROWN, 3.5))
            + P(c(200, 950, 430, "#C9A27E"))
            + specks(10, 18, 20, 520, 380, 556, RUST, 1.2, 2.4, .5, .9)
            + P(leaf(250, 196, 172, 52, 188, RUST, CREAM))
            + P(leaf(84, 452, 128, 40, 38, OCHRE, CREAM))
            + P(leaf(302, 506, 116, 36, 14, BROWN, CREAM))
            + P(leaf(112, 246, 94, 30, -22, TERRA, CREAM))
            + P(leaf(232, 106, 70, 22, 210, OCHRE))
            + P(leaf(330, 300, 70, 22, 130, TERRA)))


def nov(u):
    phases = ""
    for i, (k, wax) in enumerate(((.15, True), (.5, True), (1, True), (.5, False), (.15, False))):
        x = 80 + i * 60
        y = 352 + ((x - 200) / 120) ** 2 * 22
        phases += P(moon_phase_disc(x, y, 17, k, wax, "#EDE4D3", "#6A6D77"), .3)
    return (rect(0, 0, 400, 560, SLATE)
            + specks(12, 40, 10, 20, 390, 320, CREAM, .8, 1.6)
            + ring(200, 186, 104, CREAM, 1, .18)
            + P(c(200, 186, 80, "#EDE4D3"), .3) + c(176, 166, 13, "#DED3BF")
            + c(226, 212, 9, "#DED3BF") + c(214, 156, 6, "#DED3BF") + c(166, 214, 5, "#DED3BF")
            + phases
            + P(c(200, 900, 420, SLATE_D), .3)
            + "".join(rect(60 + i * 10, 520 - i * 8, 280 - i * 20, 1.2, CREAM, o=.16) for i in range(4)))


def dec(u):
    return (rect(0, 0, 400, 560, FOREST)
            + specks(13, 34, 10, 20, 390, 330, CREAM, .8, 1.8)
            + P(c(200, 226, 102, RED), .25)
            + P(sparkle(92, 112, 13, OCHRE), .3) + sparkle(322, 92, 9, OCHRE)
            + sparkle(318, 318, 7, CREAM) + sparkle(64, 320, 6, CREAM)
            + P(tree(70, 524, 150, 82, "#4E6B55"), .3) + P(tree(334, 524, 128, 70, FOREST_D), .3)
            + P(tree(150, 516, 240, 128, FOREST_D), .3) + P(tree(262, 518, 196, 104, "#6E8B6E"), .3)
            + P(c(200, 970, 456, CREAM), .3)
            + specks(14, 16, 30, 520, 370, 556, "#E6EDE6", 1.2, 2.4, .7, 1))


# ---------------------------------------------------------------- small marks

def glyph(m, size=10):
    """Tiny single-colour month mark (currentColor) for tabs and labels."""
    g = [
        crescent(6, 6, 5, 8.3, 4.3, 4.3, "currentColor"),
        '<circle cx="4.4" cy="6.8" r="3.4"/><circle cx="7.6" cy="5.2" r="3.4" opacity=".55"/>',
        '<path d="M6 11.4Q11.2 6 6 .6Q.8 6 6 11.4Z"/>',
        '<path d="M6 .8C6 .8 1.9 6.2 1.9 8a4.1 4.1 0 0 0 8.2 0C10.1 6.2 6 .8 6 .8Z"/>',
        "".join(f'<circle cx="{6 + 3 * math.cos(i * 1.2566 - 1.5708):.2f}" cy="{6 + 3 * math.sin(i * 1.2566 - 1.5708):.2f}" r="2.1"/>' for i in range(5)) + '<circle cx="6" cy="6" r="1.4" opacity=".5"/>',
        '<path d="M.6 4.6q1.35-1.8 2.7 0t2.7 0 2.7 0 2.7 0M.6 8.6q1.35-1.8 2.7 0t2.7 0 2.7 0 2.7 0" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>',
        '<circle cx="6" cy="6" r="2.7"/>' + "".join(
            f'<rect x="5.45" y=".4" width="1.1" height="2.2" rx=".55" transform="rotate({i * 45} 6 6)"/>' for i in range(8)),
        '<path d="M1.4 8.4A4.6 4.6 0 0 1 10.6 8.4Z"/><rect x=".4" y="9.6" width="11.2" height="1.1" rx=".55"/>',
        '<rect x="5.45" y="4" width="1.1" height="7.6" rx=".55"/>' + "".join(
            f'<ellipse cx="{6 + sx * 1.7}" cy="{2.4 + j * 2.2}" rx="1.1" ry="1.9" transform="rotate({sx * 32} {6 + sx * 1.7} {2.4 + j * 2.2})"/>'
            for j in range(3) for sx in (-1, 1)),
        '<g transform="rotate(38 6 6)"><path d="M6 10.6Q10.6 5.6 6 .6Q1.4 5.6 6 10.6Z"/><rect x="5.5" y="9.6" width="1" height="2.4" rx=".5"/></g>',
        '<circle cx="6" cy="6" r="4.4"/><circle cx="6" cy="6" r="5.6" fill="none" stroke="currentColor" stroke-width=".7" opacity=".6"/>',
        '<path d="M6 .6L9.4 5.2H7.6L10.6 9.4H1.4L4.4 5.2H2.6Z"/><rect x="5.4" y="9.2" width="1.2" height="2.4"/>',
    ][m - 1]
    return f'<svg class="glyph" width="{size}" height="{size}" viewBox="0 0 12 12"><g fill="currentColor">{g}</g></svg>'


def seal(size=132, uid="s1", text="ATELIER SOLEIL \u00b7 EDITION MMXXVII \u00b7 ",
         ink="#F3EADB", gold="#D9A441"):
    sun = '<circle cx="66" cy="66" r="15" fill="%s"/>' % gold + "".join(
        f'<rect x="64.9" y="38" width="2.2" height="8" rx="1.1" fill="{gold}" transform="rotate({i * 30} 66 66)"/>'
        for i in range(12))
    return (f'<svg class="seal" width="{size}" height="{size}" viewBox="0 0 132 132">'
            f'<defs><path id="sealp{uid}" d="M66 66m-50 0a50 50 0 1 1 100 0a50 50 0 1 1-100 0"/></defs>'
            f'<circle cx="66" cy="66" r="64" fill="none" stroke="{gold}" stroke-width=".9" opacity=".7"/>'
            f'<circle cx="66" cy="66" r="38" fill="none" stroke="{gold}" stroke-width=".7" opacity=".55"/>'
            f'<text font-family="Jost" font-size="8.6" font-weight="500" fill="{ink}" opacity=".78">'
            f'<textPath href="#sealp{uid}" textLength="306" lengthAdjust="spacing">{text}</textPath></text>{sun}</svg>')


def stamp(m, paper="#F5EFE5", light="#F2E2D6"):
    """Perforated postage stamp with the month artwork, plus a postmark."""
    perf = "".join(f'<circle cx="{x}" cy="{y}" r="2.6" fill="{paper}"/>'
                   for x in range(4, 88, 7) for y in (0, 108)) + "".join(
        f'<circle cx="{x}" cy="{y}" r="2.6" fill="{paper}"/>' for y in range(4, 108, 7) for x in (0, 88))
    pm = ''.join(f'<path d="M-46 {44 + i * 7}q6-4 12 0t12 0 12 0 12 0" fill="none" stroke="#6E6158" stroke-width=".9" opacity=".5"/>' for i in range(4))
    return (f'<svg class="stamp" width="150" height="116" viewBox="-60 -4 152 116">'
            f'<g transform="translate(1.6 2.4)" opacity=".12"><rect width="88" height="108" fill="{SHADOW}"/></g>'
            f'<rect width="88" height="108" fill="#FBF8F2"/>{perf}'
            f'<rect x="8" y="8" width="72" height="80" fill="{light}"/>'
            f'<svg x="16" y="12" width="56" height="74" viewBox="0 0 400 560">{COMPOSE[m - 1]("st" + str(m))}</svg>'
            f'<text x="44" y="100" text-anchor="middle" font-family="Fraunces Text" font-style="italic" font-size="8.5" fill="#6E6158">Soleil \u00b7 2027</text>'
            f'<g opacity=".9">{pm}<circle cx="-14" cy="54" r="20" fill="none" stroke="#6E6158" stroke-width=".9" opacity=".5"/>'
            f'<text x="-14" y="57" text-anchor="middle" font-family="Jost" font-size="6.5" letter-spacing="1" fill="#6E6158" opacity=".7">2027</text></g>'
            f'</svg>')


COMPOSE = [jan, feb, mar, apr, may, jun, jul, aug, sep, oct_, nov, dec]
_uid = [0]


def art(m, cls="art"):
    """Return an inline SVG of month m (1..12) inside an arch window."""
    _uid[0] += 1
    u = f"ar{m}x{_uid[0]}"
    body = COMPOSE[m - 1](u)
    return (f'<svg class="{cls}" viewBox="0 0 400 560" preserveAspectRatio="xMidYMid meet">'
            f'<defs><clipPath id="{u}"><path d="{ARCH}"/></clipPath></defs>'
            f'<g clip-path="url(#{u})">{body}</g></svg>')
