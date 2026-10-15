"""Ornament library for Layout Perfect interiors.

Every ornament is drawn procedurally with ReportLab vector primitives, so the
engine carries no font or asset dependency and ornaments scale crisply at any
trim size. Ornaments are addressed by name through :func:`draw` and are used by
chapter openers, scene breaks, running-header rules, pull quotes and callouts.

If an ``ornaments/`` directory ships beside this module containing a matching
``<name>.svg`` file *and* svglib is importable, that artwork is used instead, so
house artwork can be dropped in without touching the engine. When neither is
available the procedural drawing is used, which is always the case by default.
"""

import math
import os

try:
    from reportlab.lib.colors import HexColor
except Exception:  # pragma: no cover - reportlab is always present at runtime
    HexColor = None


SVG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ornaments')
_SVG_CACHE = {}

# ── Catalogue ────────────────────────────────────────────────────────
FLEURONS = ('leaf', 'acanthus', 'fleur_de_lis', 'vine', 'rosette',
            'arabesque', 'heart', 'star')
FLOURISHES = ('scroll', 'double_scroll', 'ribbon', 'baroque',
              'art_nouveau', 'celtic')
RULE_STYLES = ('tapered', 'double', 'dotted', 'wavy', 'dashed',
               'ornamental_centre', 'thin', 'thick')
ICONS = ('lightbulb', 'warning', 'info', 'key', 'book', 'pencil')

CATALOGUE = FLEURONS + FLOURISHES + RULE_STYLES + ICONS

# Friendly spellings authors and staff may use.
ALIASES = {
    'fleur-de-lis': 'fleur_de_lis', 'fleurdelis': 'fleur_de_lis',
    'acanthus_leaf': 'acanthus', 'simple_scroll': 'scroll',
    'double-scroll': 'double_scroll', 'artnouveau': 'art_nouveau',
    'ornamental_center': 'ornamental_centre', 'centre': 'ornamental_centre',
    'ornamental': 'ornamental_centre', 'taper': 'tapered',
    'dashes': 'dashed', 'dots': 'dotted', 'hairline': 'thin',
    'triangle': 'warning', 'warning_triangle': 'warning',
    'info_circle': 'info', 'bulb': 'lightbulb', 'pen': 'pencil',
}


def normalize(name):
    """Return the canonical catalogue name for *name* (or '' when unknown)."""
    if not name:
        return ''
    key = str(name).strip().lower().replace(' ', '_')
    key = ALIASES.get(key, key)
    return key if key in CATALOGUE else ''


def is_known(name):
    return normalize(name) != ''


# ── Shared helpers ───────────────────────────────────────────────────
def _stroke(c, color, lw):
    c.setStrokeColor(color)
    c.setLineWidth(lw)


def _fill(c, color):
    c.setFillColor(color)
    c.setStrokeColor(color)


def _arc(c, cx, cy, r, a0, a1, color, lw):
    """Stroke an arc as a polyline (portable across reportlab versions)."""
    _stroke(c, color, lw)
    p = c.beginPath()
    steps = max(8, int(abs(a1 - a0) / 6))
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    c.drawPath(p, fill=0, stroke=1)


def _spiral(c, cx, cy, r, turns, color, lw, flip=1):
    """A scroll curl: an involute spiral stroked as a polyline."""
    _stroke(c, color, lw)
    p = c.beginPath()
    steps = 48
    for i in range(steps + 1):
        t = i / steps
        ang = math.radians(360 * turns * t) * flip
        rad = r * (0.12 + 0.88 * (1 - t))
        x, y = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    c.drawPath(p, fill=0, stroke=1)


def _petal(c, cx, cy, w, h, color, angle=0):
    """A filled petal/leaf shape centred on (cx, cy), rotated by *angle*."""
    _fill(c, color)
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angle)
    p = c.beginPath()
    p.moveTo(0, 0)
    p.curveTo(w * 0.5, h * 0.65, w * 0.5, h * 1.35, 0, h)
    p.curveTo(-w * 0.5, h * 1.35, -w * 0.5, h * 0.65, 0, 0)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _dot(c, x, y, r, color):
    _fill(c, color)
    c.circle(x, y, r, fill=1, stroke=0)


def _diamond(c, cx, cy, r, color):
    _fill(c, color)
    p = c.beginPath()
    p.moveTo(cx, cy + r)
    p.lineTo(cx + r, cy)
    p.lineTo(cx, cy - r)
    p.lineTo(cx - r, cy)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


# ── Fleurons ─────────────────────────────────────────────────────────
def _leaf(c, cx, y, w, color, lw):
    h = w * 0.30
    _fill(c, color)
    p = c.beginPath()
    p.moveTo(cx - w / 2, y)
    p.curveTo(cx - w * 0.20, y + h * 1.5, cx + w * 0.20, y + h * 1.5, cx + w / 2, y)
    p.curveTo(cx + w * 0.20, y - h * 1.5, cx - w * 0.20, y - h * 1.5, cx - w / 2, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    _stroke(c, color, lw)
    c.line(cx - w * 0.40, y, cx + w * 0.36, y)


def _acanthus(c, cx, y, w, color, lw):
    """Classical acanthus spray: a stem with paired lobes and curled tips."""
    h = w * 0.26
    _stroke(c, color, lw)
    c.line(cx - w * 0.42, y, cx + w * 0.42, y)
    for i, dx in enumerate((-0.30, -0.10, 0.10, 0.30)):
        size = h * (0.55 if abs(dx) > 0.25 else 0.85)
        _petal(c, cx + w * dx, y, size * 0.7, size, color, 35 if i < 2 else -35)
    _spiral(c, cx - w * 0.46, y, h * 0.55, 0.8, color, lw, flip=-1)
    _spiral(c, cx + w * 0.46, y, h * 0.55, 0.8, color, lw, flip=1)


def _fleur_de_lis(c, cx, y, w, color, lw):
    h = w * 0.34
    _fill(c, color)
    for angle in (-38, 0, 38):
        _petal(c, cx, y - h * 0.15, w * 0.20, h * 1.15, color, angle)
    c.rect(cx - w * 0.24, y - h * 0.55, w * 0.48, h * 0.16, fill=1, stroke=0)
    _dot(c, cx, y + h * 0.62, w * 0.022, color)


def _vine(c, cx, y, w, color, lw):
    h = w * 0.22
    _stroke(c, color, lw)
    p = c.beginPath()
    steps = 40
    for i in range(steps + 1):
        t = i / steps
        px = cx - w / 2 + w * t
        py = y + math.sin(t * math.pi * 2) * h * 0.25
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    c.drawPath(p, fill=0, stroke=1)
    for i in range(5):
        t = 0.1 + i * 0.2
        px = cx - w / 2 + w * t
        up = 1 if i % 2 == 0 else -1
        _petal(c, px, y + up * h * 0.22, h * 0.34, h * 0.75, color,
               40 * up)


def _rosette(c, cx, y, w, color, lw):
    r = w * 0.22
    for i in range(8):
        _petal(c, cx, y, r * 0.42, r, color, i * 45)
    _dot(c, cx, y, r * 0.20, color)


def _arabesque(c, cx, y, w, color, lw):
    h = w * 0.24
    _stroke(c, color, lw)
    for flip in (-1, 1):
        _spiral(c, cx + flip * w * 0.34, y + h * 0.35, h * 0.55, 1.1, color, lw, flip=flip)
        _arc(c, cx + flip * w * 0.12, y - h * 0.10, h * 0.60,
             -30 if flip < 0 else 210, 150 if flip < 0 else 30, color, lw)
    _dot(c, cx, y, h * 0.14, color)


def _heart(c, cx, y, w, color, lw):
    h = w * 0.30
    _fill(c, color)
    p = c.beginPath()
    p.moveTo(cx, y - h)
    p.curveTo(cx - w * 0.55, y + h * 0.25, cx - w * 0.22, y + h * 1.25, cx, y + h * 0.45)
    p.curveTo(cx + w * 0.22, y + h * 1.25, cx + w * 0.55, y + h * 0.25, cx, y - h)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _star(c, cx, cy, r, color):
    _fill(c, color)
    p = c.beginPath()
    for i in range(5):
        a1 = math.radians(90 + i * 72)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        if i == 0:
            p.moveTo(x1, y1)
        else:
            p.lineTo(x1, y1)
        a2 = math.radians(90 + i * 72 + 36)
        p.lineTo(cx + r * 0.4 * math.cos(a2), cy + r * 0.4 * math.sin(a2))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _star_ornament(c, cx, y, w, color, lw):
    r = w * 0.24
    _star(c, cx, y, r, color)
    _stroke(c, color, lw)
    c.line(cx - w * 0.46, y, cx - r * 1.4, y)
    c.line(cx + r * 1.4, y, cx + w * 0.46, y)


# ── Flourishes ───────────────────────────────────────────────────────
def _scroll(c, cx, y, w, color, lw):
    h = w * 0.20
    _stroke(c, color, lw)
    c.line(cx - w * 0.30, y, cx + w * 0.30, y)
    _spiral(c, cx - w * 0.42, y, h, 1.0, color, lw, flip=-1)
    _spiral(c, cx + w * 0.42, y, h, 1.0, color, lw, flip=1)


def _double_scroll(c, cx, y, w, color, lw):
    h = w * 0.22
    for flip in (-1, 1):
        _spiral(c, cx + flip * w * 0.30, y + h * 0.30, h * 0.75, 1.2, color, lw, flip=flip)
        _spiral(c, cx + flip * w * 0.34, y - h * 0.30, h * 0.55, 1.0, color, lw, flip=flip)
    _stroke(c, color, lw)
    c.line(cx - w * 0.12, y, cx + w * 0.12, y)


def _ribbon(c, cx, y, w, color, lw):
    h = w * 0.16
    _stroke(c, color, lw)
    top, bottom = [], []
    steps = 36
    for i in range(steps + 1):
        t = i / steps
        px = cx - w / 2 + w * t
        off = math.sin(t * math.pi * 2) * h
        top.append((px, y + off + h * 0.55))
        bottom.append((px, y + off - h * 0.55))
    for pts in (top, bottom):
        p = c.beginPath()
        for i, (px, py) in enumerate(pts):
            p.moveTo(px, py) if i == 0 else p.lineTo(px, py)
        c.drawPath(p, fill=0, stroke=1)
    _diamond(c, cx, y - h * 1.5, h * 0.5, color)


def _baroque(c, cx, y, w, color, lw):
    h = w * 0.26
    for flip in (-1, 1):
        _spiral(c, cx + flip * w * 0.34, y + h * 0.25, h * 0.85, 1.6, color, lw, flip=flip)
        _petal(c, cx + flip * w * 0.16, y - h * 0.35, h * 0.30, h * 0.70, color,
               25 * flip)
    _diamond(c, cx, y + h * 0.55, h * 0.28, color)
    _stroke(c, color, lw)
    c.line(cx - w * 0.46, y, cx - w * 0.10, y)
    c.line(cx + w * 0.10, y, cx + w * 0.46, y)


def _art_nouveau(c, cx, y, w, color, lw):
    h = w * 0.26
    _stroke(c, color, lw)
    p = c.beginPath()
    steps = 40
    for i in range(steps + 1):
        t = i / steps
        px = cx - w / 2 + w * t
        py = y + math.sin(t * math.pi) * h * 0.55 - h * 0.20
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    c.drawPath(p, fill=0, stroke=1)
    _petal(c, cx, y + h * 0.30, h * 0.35, h * 0.85, color, 0)
    _spiral(c, cx + w * 0.44, y - h * 0.10, h * 0.45, 1.0, color, lw, flip=1)
    _spiral(c, cx - w * 0.44, y - h * 0.10, h * 0.45, 1.0, color, lw, flip=-1)


def _celtic(c, cx, y, w, color, lw):
    r = w * 0.17
    _stroke(c, color, lw * 1.4)
    for dx in (-r * 1.15, r * 1.15):
        _arc(c, cx + dx, y, r, 0, 360, color, lw * 1.4)
    _stroke(c, color, lw * 1.4)
    p = c.beginPath()
    p.moveTo(cx - w * 0.42, y)
    p.lineTo(cx - r * 1.15, y)
    p.moveTo(cx + r * 1.15, y)
    p.lineTo(cx + w * 0.42, y)
    c.drawPath(p, fill=0, stroke=1)


# ── Rules ────────────────────────────────────────────────────────────
def _rule_tapered(c, cx, y, w, color, lw):
    half = w / 2
    thick = max(lw * 4, 1.6)
    _fill(c, color)
    p = c.beginPath()
    p.moveTo(cx - half, y)
    p.lineTo(cx, y + thick / 2)
    p.lineTo(cx + half, y)
    p.lineTo(cx, y - thick / 2)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _rule_double(c, cx, y, w, color, lw):
    _stroke(c, color, lw)
    gap = max(1.6, lw * 3)
    c.line(cx - w / 2, y + gap / 2, cx + w / 2, y + gap / 2)
    c.line(cx - w / 2, y - gap / 2, cx + w / 2, y - gap / 2)


def _rule_dotted(c, cx, y, w, color, lw):
    n = max(3, int(w / 4))
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.5
        _dot(c, cx - w / 2 + w * t, y, max(0.5, lw * 1.2), color)


def _rule_dashed(c, cx, y, w, color, lw):
    _stroke(c, color, lw)
    c.setDash([2.4, 2.4])
    c.line(cx - w / 2, y, cx + w / 2, y)
    c.setDash([])


def _rule_wavy(c, cx, y, w, color, lw):
    _stroke(c, color, lw)
    p = c.beginPath()
    steps = 48
    for i in range(steps + 1):
        t = i / steps
        px = cx - w / 2 + w * t
        py = y + math.sin(t * math.pi * 4) * max(1.0, w * 0.018)
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    c.drawPath(p, fill=0, stroke=1)


def _rule_ornamental_centre(c, cx, y, w, color, lw):
    _stroke(c, color, lw)
    gap = max(6.0, w * 0.06)
    c.line(cx - w / 2, y, cx - gap, y)
    c.line(cx + gap, y, cx + w / 2, y)
    _diamond(c, cx, y, max(2.2, w * 0.022), color)


def _rule_thin(c, cx, y, w, color, lw):
    _stroke(c, color, lw)
    c.line(cx - w / 2, y, cx + w / 2, y)


def _rule_thick(c, cx, y, w, color, lw):
    _rule_thin(c, cx, y, w, color, max(lw * 4, 1.5))


# ── Icons (drawn inside a square of side *w*) ────────────────────────
def _icon_lightbulb(c, cx, y, w, color, lw):
    r = w * 0.32
    _stroke(c, color, lw)
    _arc(c, cx, y + r * 0.35, r, 0, 360, color, lw)
    c.setFillColor(color)
    c.rect(cx - r * 0.45, y - r * 0.95, r * 0.90, r * 0.45, fill=1, stroke=0)
    c.rect(cx - r * 0.30, y - r * 1.40, r * 0.60, r * 0.35, fill=1, stroke=0)


def _icon_warning(c, cx, y, w, color, lw):
    h = w * 0.46
    _fill(c, color)
    p = c.beginPath()
    p.moveTo(cx, y + h)
    p.lineTo(cx + h * 0.92, y - h * 0.75)
    p.lineTo(cx - h * 0.92, y - h * 0.75)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    ex = HexColor('#FFFFFF') if HexColor else None
    if ex is not None:
        _stroke(c, ex, lw * 1.6)
        c.line(cx, y - h * 0.35, cx, y + h * 0.30)
        _dot(c, cx, y - h * 0.58, max(0.6, lw * 0.9), ex)
    else:
        _stroke(c, color, lw)
        c.line(cx, y - h * 0.35, cx, y + h * 0.30)


def _icon_info(c, cx, y, w, color, lw):
    r = w * 0.42
    _stroke(c, color, lw)
    _arc(c, cx, y, r, 0, 360, color, lw)
    _fill(c, color)
    c.rect(cx - r * 0.10, y - r * 0.55, r * 0.20, r * 0.75, fill=1, stroke=0)
    _dot(c, cx, y + r * 0.45, r * 0.13, color)


def _icon_key(c, cx, y, w, color, lw):
    r = w * 0.22
    _stroke(c, color, lw * 1.2)
    _arc(c, cx - w * 0.22, y, r, 0, 360, color, lw * 1.2)
    c.line(cx - w * 0.22 + r, y, cx + w * 0.40, y)
    c.line(cx + w * 0.26, y, cx + w * 0.26, y - r * 0.85)
    c.line(cx + w * 0.40, y, cx + w * 0.40, y - r * 0.55)


def _icon_book(c, cx, y, w, color, lw):
    h = w * 0.40
    _stroke(c, color, lw)
    c.rect(cx - w * 0.38, y - h, w * 0.76, h * 2, fill=0, stroke=1)
    c.line(cx - w * 0.10, y - h, cx - w * 0.10, y + h)
    _fill(c, color)
    c.rect(cx - w * 0.34, y + h * 0.25, w * 0.18, h * 0.22, fill=1, stroke=0)


def _icon_pencil(c, cx, y, w, color, lw):
    h = w * 0.42
    _fill(c, color)
    p = c.beginPath()
    p.moveTo(cx - w * 0.34, y - h)
    p.lineTo(cx + w * 0.34, y + h * 0.75)
    p.lineTo(cx + w * 0.24, y + h)
    p.lineTo(cx - w * 0.46, y - h * 0.55)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


_DRAWERS = {
    'leaf': _leaf, 'acanthus': _acanthus, 'fleur_de_lis': _fleur_de_lis,
    'vine': _vine, 'rosette': _rosette, 'arabesque': _arabesque,
    'heart': _heart, 'star': _star_ornament, 'scroll': _scroll,
    'double_scroll': _double_scroll, 'ribbon': _ribbon, 'baroque': _baroque,
    'art_nouveau': _art_nouveau, 'celtic': _celtic, 'tapered': _rule_tapered,
    'double': _rule_double, 'dotted': _rule_dotted, 'wavy': _rule_wavy,
    'dashed': _rule_dashed, 'ornamental_centre': _rule_ornamental_centre,
    'thin': _rule_thin, 'thick': _rule_thick, 'lightbulb': _icon_lightbulb,
    'warning': _icon_warning, 'info': _icon_info, 'key': _icon_key,
    'book': _icon_book, 'pencil': _icon_pencil,
}


# ── Artwork overrides (optional) ─────────────────────────────────────
def _svg_drawing(name, color):
    """Return a recoloured svglib Drawing for *name*, or None.

    Dormant unless an ``ornaments/<name>.svg`` file exists and svglib is
    installed, so the engine never depends on either."""
    path = os.path.join(SVG_DIR, f'{name}.svg')
    if name in _SVG_CACHE:
        return _SVG_CACHE[name]
    if not os.path.isfile(path):
        _SVG_CACHE[name] = None
        return None
    try:
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(path)
        _recolor(drawing, color)
        _SVG_CACHE[name] = drawing
        return drawing
    except Exception:
        _SVG_CACHE[name] = None
        return None


def _recolor(obj, color):
    """Recursively replace fill/stroke colours on a reportlab Drawing."""
    if hasattr(obj, 'contents'):
        for child in obj.contents:
            _recolor(child, color)
    if hasattr(obj, 'fillColor') and getattr(obj, 'fillColor', None) is not None:
        obj.fillColor = color
    if hasattr(obj, 'strokeColor') and getattr(obj, 'strokeColor', None) is not None:
        obj.strokeColor = color


def _draw_svg(c, name, cx, y, width, color):
    drawing = _svg_drawing(name, color)
    if drawing is None:
        return False
    try:
        from reportlab.graphics import renderPDF
        scale = width / float(drawing.width or width)
        c.saveState()
        c.translate(cx - width / 2, y - (drawing.height or 0) * scale / 2)
        c.scale(scale, scale)
        renderPDF.draw(drawing, c, 0, 0)
        c.restoreState()
        return True
    except Exception:
        return False


# ── Public drawing entry points ──────────────────────────────────────
def draw(c, name, cx, y, width, color, lw=0.6, allow_svg=True):
    """Draw ornament *name* centred on (*cx*, *y*) with overall width *width*.

    Returns True when something was drawn."""
    key = normalize(name)
    if not key or width <= 0:
        return False
    if allow_svg and _draw_svg(c, key, cx, y, width, color):
        return True
    drawer = _DRAWERS.get(key)
    if drawer is None:
        return False
    c.saveState()
    try:
        drawer(c, cx, y, width, color, lw)
    finally:
        c.restoreState()
    return True


def draw_rule(c, style, cx, y, width, color, lw=0.6, allow_svg=True):
    """Draw a page rule. Unknown styles fall back to a hairline."""
    key = normalize(style) or 'thin'
    if key not in RULE_STYLES:
        key = 'thin'
    return draw(c, key, cx, y, width, color, lw, allow_svg)


def draw_triple(c, name, cx, y, width, color, lw=0.6, count=3, gap_ratio=0.24):
    """Draw *count* copies of an ornament in a row (triple ornament styles)."""
    key = normalize(name)
    if not key:
        return False
    unit = width / (count + (count - 1) * gap_ratio)
    step = unit * (1 + gap_ratio)
    start = cx - (width - unit) / 2
    drawn = False
    for i in range(count):
        drawn = draw(c, key, start + i * step, y, unit, color, lw) or drawn
    return drawn


def icon_for(kind):
    """Default icon name for a callout type."""
    return {
        'callout': '',
        'tip': 'lightbulb',
        'warning': 'warning',
        'note': 'info',
        'definition': 'book',
        'key_takeaway': 'key',
    }.get(kind, '')
