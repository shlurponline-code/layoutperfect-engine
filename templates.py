"""Template configurations and ornament rendering for Layout Perfect.

Each template defines a visual personality through font choices, body text
parameters, chapter opening style, running headers, folio position, and
ornamental elements. All ornaments are drawn as vector graphics (lines,
circles, polygons) to avoid Unicode font dependency issues.
"""

import math
from reportlab.lib.colors import HexColor

C_BODY = HexColor('#2C2C2C')
C_BROWN = HexColor('#8B7355')
C_GREY = HexColor('#999999')
C_MID = HexColor('#888888')
C_DARK = HexColor('#4A4A4A')

# ── Template Configurations ──────────────────────────────────────────

TEMPLATES = {
    'narrative': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 12, 'leading': 18,
        'chapter_title_size': 22, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'none',
        'chapter_title_position': 'centered',
        'drop_cap': 'none',
        'ornament_below_title': 'rule',
        'header_style': 'centered',
        'header_font': 'GarI',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 0,
        'scene_break': 'dots',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 80,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'portrait': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 12, 'leading': 18,
        'chapter_title_size': 22, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'none',
        'chapter_title_position': 'centered',
        'drop_cap': 'none',
        'ornament_below_title': 'rule',
        'header_style': 'centered',
        'header_font': 'GarI',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 0,
        'scene_break': 'dots',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 80,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'fiction': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 12, 'leading': 18,
        'chapter_title_size': 22, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'none',
        'chapter_title_position': 'centered',
        'drop_cap': 'simple',
        'ornament_below_title': 'rule',
        'header_style': 'centered',
        'header_font': 'GarI',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 14,
        'paragraph_spacing': 0,
        'scene_break': 'dots',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 80,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'guide': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 12, 'leading': 18,
        'chapter_title_size': 22, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'none',
        'chapter_title_position': 'left',
        'drop_cap': 'none',
        'ornament_below_title': 'rule',
        'header_style': 'centered',
        'header_font': 'GarI',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 4,
        'scene_break': 'dots',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 80,
        'text_alignment': 'left',
        'margin_multiplier': 1.0,
    },
    'poetry': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 12, 'leading': 18,
        'chapter_title_size': 22, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'none',
        'chapter_title_position': 'centered',
        'drop_cap': 'none',
        'ornament_below_title': 'rule',
        'header_style': 'centered',
        'header_font': 'GarI',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 6,
        'scene_break': 'dots',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 80,
        'text_alignment': 'left',
        'margin_multiplier': 1.0,
    },
    'children': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 14, 'leading': 21,
        'chapter_title_size': 26, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'none',
        'chapter_title_position': 'centered',
        'drop_cap': 'simple',
        'ornament_below_title': 'rule',
        'header_style': 'centered',
        'header_font': 'GarI',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 4,
        'scene_break': 'dots',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 80,
        'text_alignment': 'left',
        'margin_multiplier': 1.0,
    },
    'custom': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 12, 'leading': 18,
        'chapter_title_size': 22, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'none',
        'chapter_title_position': 'centered',
        'drop_cap': 'none',
        'ornament_below_title': 'rule',
        'header_style': 'centered',
        'header_font': 'GarI',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 0,
        'scene_break': 'dots',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 80,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    # ── New Templates (7-16) ──
    'heritage': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 11, 'leading': 14.3,
        'chapter_title_size': 24, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'smallcaps_spaced',
        'chapter_title_position': 'centered',
        'drop_cap': 'decorative_3line',
        'ornament_below_title': 'diamond_rule',
        'header_style': 'title_left_chapter_right',
        'header_font': 'Gar',
        'folio_position': 'centered',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 18,
        'paragraph_spacing': 0,
        'scene_break': 'three_stars',
        'chapter_end_ornament': 'fleuron',
        'chapter_start_offset': 200,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'modernist': {
        'body_font': 'Gar', 'heading_font': 'SansB',
        'body_size': 11, 'leading': 14.85,
        'chapter_title_size': 48, 'chapter_title_font': 'SansB',
        'chapter_number_style': 'large_sans_topleft',
        'chapter_title_position': 'none',
        'drop_cap': 'none',
        'ornament_below_title': 'none',
        'header_style': 'none',
        'header_font': 'Sans',
        'folio_position': 'bottom_outside',
        'folio_font': 'Sans',
        'header_rule': False,
        'first_line_indent': 14,
        'paragraph_spacing': 0,
        'scene_break': 'centered_bullet',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 120,
        'text_alignment': 'justified',
        'margin_multiplier': 1.15,
    },
    'thriller': {
        'body_font': 'Gar', 'heading_font': 'SansB',
        'body_size': 11.5, 'leading': 14.375,
        'chapter_title_size': 36, 'chapter_title_font': 'SansB',
        'chapter_number_style': 'large_sans_topleft',
        'chapter_title_position': 'none',
        'drop_cap': 'none',
        'ornament_below_title': 'none',
        'header_style': 'author_left_chapter_right',
        'header_font': 'SansB',
        'folio_position': 'bottom_outside',
        'folio_font': 'SansB',
        'header_rule': False,
        'first_line_indent': 14,
        'paragraph_spacing': 0,
        'scene_break': 'three_asterisks',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 60,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'botanical': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 11, 'leading': 14.85,
        'chapter_title_size': 22, 'chapter_title_font': 'GarI',
        'chapter_number_style': 'italic_centered',
        'chapter_title_position': 'centered',
        'drop_cap': 'decorative_3line',
        'ornament_below_title': 'botanical',
        'header_style': 'title_left_chapter_right',
        'header_font': 'Gar',
        'folio_position': 'centered_with_dots',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 18,
        'paragraph_spacing': 0,
        'scene_break': 'botanical',
        'chapter_end_ornament': 'botanical',
        'chapter_start_offset': 100,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'academic': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 10.5, 'leading': 12.6,
        'chapter_title_size': 20, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'sans_medium',
        'chapter_title_position': 'left',
        'drop_cap': 'none',
        'ornament_below_title': 'thick_rule',
        'header_style': 'chapter_left_section_right',
        'header_font': 'Gar',
        'folio_position': 'bottom_outside',
        'folio_font': 'Gar',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 4,
        'scene_break': 'space',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 80,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'gothic': {
        'body_font': 'Gar', 'heading_font': 'GarB',
        'body_size': 11, 'leading': 14.3,
        'chapter_title_size': 26, 'chapter_title_font': 'GarB',
        'chapter_number_style': 'large_centered',
        'chapter_title_position': 'centered_caps_spaced',
        'drop_cap': 'decorative_3line',
        'ornament_below_title': 'gothic',
        'header_style': 'title_left_chapter_right',
        'header_font': 'Gar',
        'folio_position': 'centered',
        'folio_font': 'GarB',
        'header_rule': True,
        'first_line_indent': 18,
        'paragraph_spacing': 0,
        'scene_break': 'gothic',
        'chapter_end_ornament': 'gothic',
        'chapter_start_offset': 250,
        'text_alignment': 'justified',
        'margin_multiplier': 1.0,
    },
    'minimal': {
        'body_font': 'Sans', 'heading_font': 'SansB',
        'body_size': 11, 'leading': 15.4,
        'chapter_title_size': 36, 'chapter_title_font': 'Sans',
        'chapter_number_style': 'large_sans_topleft',
        'chapter_title_position': 'left_below',
        'drop_cap': 'none',
        'ornament_below_title': 'thin_rule',
        'header_style': 'none',
        'header_font': 'Sans',
        'folio_position': 'bottom_outside',
        'folio_font': 'Sans',
        'header_rule': False,
        'first_line_indent': 0,
        'paragraph_spacing': 6,
        'scene_break': 'short_rule',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 100,
        'text_alignment': 'left',
        'margin_multiplier': 1.1,
    },
    'journal': {
        'body_font': 'Gar', 'heading_font': 'GarI',
        'body_size': 11, 'leading': 15.4,
        'chapter_title_size': 20, 'chapter_title_font': 'GarI',
        'chapter_number_style': 'italic_centered',
        'chapter_title_position': 'left',
        'drop_cap': 'none',
        'ornament_below_title': 'thin_rule',
        'header_style': 'none',
        'header_font': 'Gar',
        'folio_position': 'bottom_outside',
        'folio_font': 'Gar',
        'header_rule': False,
        'first_line_indent': 0,
        'paragraph_spacing': 8,
        'scene_break': 'small_symbol',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 80,
        'text_alignment': 'left',
        'margin_multiplier': 1.1,
    },
    'coffee_table': {
        'body_font': 'Gar', 'heading_font': 'Sans',
        'body_size': 10.5, 'leading': 14.175,
        'chapter_title_size': 28, 'chapter_title_font': 'Sans',
        'chapter_number_style': 'none',
        'chapter_title_position': 'left',
        'drop_cap': 'none',
        'ornament_below_title': 'none',
        'header_style': 'none',
        'header_font': 'Sans',
        'folio_position': 'bottom_outside',
        'folio_font': 'Sans',
        'header_rule': False,
        'first_line_indent': 0,
        'paragraph_spacing': 6,
        'scene_break': 'space',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 120,
        'text_alignment': 'left',
        'margin_multiplier': 1.2,
    },
    'screenplay': {
        'body_font': 'Mono', 'heading_font': 'MonoB',
        'body_size': 12, 'leading': 14.4,
        'chapter_title_size': 16, 'chapter_title_font': 'MonoB',
        'chapter_number_style': 'centered_caps',
        'chapter_title_position': 'centered',
        'drop_cap': 'none',
        'ornament_below_title': 'none',
        'header_style': 'none',
        'header_font': 'Mono',
        'folio_position': 'top_outside',
        'folio_font': 'Mono',
        'header_rule': False,
        'first_line_indent': 0,
        'paragraph_spacing': 0,
        'scene_break': 'none',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 80,
        'text_alignment': 'left',
        'margin_multiplier': 1.0,
    },
}

# ── Ornament Drawing ─────────────────────────────────────────────────

def draw_ornament(c, y, cx, style, color=C_BROWN):
    """Draw an ornament at position y, centered at cx."""
    if style in (None, 'none', ''):
        return
    elif style in ('diamond_rule', 'fleuron'):
        _diamond_rule(c, y, cx, color)
    elif style == 'three_stars':
        _three_stars(c, y, cx, color)
    elif style == 'botanical':
        _botanical(c, y, cx, color)
    elif style == 'gothic':
        _gothic(c, y, cx, color)
    elif style == 'rule':
        _rule(c, y, cx, color, 80, 0.5)
    elif style == 'thick_rule':
        _rule(c, y, cx, color, 80, 2.0)
    elif style == 'thin_rule':
        _rule(c, y, cx, color, 40, 0.3)
    elif style == 'short_rule':
        _rule(c, y, cx, color, 20, 0.5)


def _diamond_rule(c, y, cx, color):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(0.5)
    c.line(cx - 35, y, cx - 8, y)
    c.line(cx + 8, y, cx + 35, y)
    c.saveState()
    c.translate(cx, y)
    c.rotate(45)
    c.rect(-3, -3, 6, 6, fill=1, stroke=0)
    c.restoreState()


def _star(c, cx, cy, r, color):
    c.setFillColor(color)
    p = c.beginPath()
    for i in range(5):
        a1 = math.radians(90 + i * 72)
        x1 = cx + r * math.cos(a1)
        y1 = cy + r * math.sin(a1)
        if i == 0:
            p.moveTo(x1, y1)
        else:
            p.lineTo(x1, y1)
        a2 = math.radians(90 + i * 72 + 36)
        x2 = cx + r * 0.4 * math.cos(a2)
        y2 = cy + r * 0.4 * math.sin(a2)
        p.lineTo(x2, y2)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _three_stars(c, y, cx, color):
    for dx in (-15, 0, 15):
        _star(c, cx + dx, y, 4, color)


def _botanical(c, y, cx, color):
    """Draw a simple botanical spray - stem with leaves."""
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(0.8)
    c.line(cx, y - 8, cx, y + 8)
    for dy in (-5, 0, 5):
        c.saveState()
        c.translate(cx - 2, y + dy)
        c.rotate(-30)
        c.ellipse(-8, -1.5, 0, 1.5, fill=1, stroke=0)
        c.restoreState()
        c.saveState()
        c.translate(cx + 2, y + dy)
        c.rotate(30)
        c.ellipse(0, -1.5, 8, 1.5, fill=1, stroke=0)
        c.restoreState()


def _gothic(c, y, cx, color):
    """Draw a gothic-style ornament - iron scroll with cross."""
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.0)
    c.line(cx - 20, y, cx + 20, y)
    c.line(cx, y - 8, cx, y + 8)
    for dx in (-20, 20):
        c.circle(cx + dx, y, 2, fill=1, stroke=0)
    c.saveState()
    c.translate(cx, y)
    c.rotate(45)
    c.rect(-3, -3, 6, 6, fill=1, stroke=0)
    c.restoreState()


def _rule(c, y, cx, color, width=80, lw=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(cx - width, y, cx + width, y)


# ── Scene Break Drawing ──────────────────────────────────────────────

def draw_scene_break(c, y, cx, style, color=C_MID):
    """Draw a scene break separator at position y, centered at cx."""
    if style in (None, 'none', '', 'space'):
        return
    elif style == 'dots':
        c.setFillColor(color)
        for dx in (-12, 0, 12):
            c.circle(cx + dx, y, 1.5, fill=1, stroke=0)
    elif style == 'three_stars':
        _three_stars(c, y, cx, color)
    elif style == 'three_asterisks':
        c.setFillColor(color)
        c.setFont('GarB', 14)
        c.drawCentredString(cx, y, '* * *')
    elif style == 'centered_bullet':
        c.setFillColor(color)
        c.circle(cx, y, 2, fill=1, stroke=0)
    elif style == 'short_rule':
        _rule(c, y, cx, color, 20, 0.5)
    elif style == 'botanical':
        _botanical(c, y, cx, color)
    elif style == 'gothic':
        _gothic(c, y, cx, color)
    elif style == 'small_symbol':
        c.setFillColor(color)
        c.circle(cx, y, 2, fill=1, stroke=0)


# ── Chapter Number Formatting ────────────────────────────────────────

_ORDINALS = ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven',
             'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen',
             'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen',
             'Nineteen', 'Twenty']


def format_chapter_number(num, style):
    """Return formatted chapter number text, or None if no number."""
    if style in ('none', None, ''):
        return None
    ordinal = _ORDINALS[num - 1] if 1 <= num <= 20 else str(num)
    if style == 'smallcaps_spaced':
        return ' '.join(ordinal.upper())
    elif style == 'large_sans_topleft':
        return str(num)
    elif style == 'italic_centered':
        return ordinal
    elif style == 'sans_medium':
        return 'Chapter ' + str(num)
    elif style == 'large_centered':
        return ordinal.upper()
    elif style == 'centered_caps':
        return 'ACT ' + _roman(num)
    return None


def _roman(num):
    vals = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    result = ''
    for v, s in vals:
        while num >= v:
            result += s
            num -= v
    return result
