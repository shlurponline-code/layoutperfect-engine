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
        'chapter_start_offset': 54,
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
        'chapter_start_offset': 54,
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
        'chapter_start_offset': 54,
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
        'body_size': 11, 'leading': 15.4,
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
        'chapter_start_offset': 216,
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
        'chapter_start_offset': 81,
        'text_alignment': 'justified',
        'margin_multiplier': 1.25,
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
        'chapter_start_offset': 108,
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
        'chapter_start_offset': 189,
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
        'chapter_start_offset': 243,
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
        'chapter_start_offset': 54,
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
        'chapter_start_offset': 81,
        'text_alignment': 'left',
        'margin_multiplier': 1.5,
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
    'cookbook': {
        'body_font': 'Sans', 'heading_font': 'SansB',
        'body_size': 10, 'leading': 14,
        'chapter_title_size': 16, 'chapter_title_font': 'SansB',
        'chapter_title_position': 'left',
        'chapter_number_style': 'none',
        'chapter_subtitles': False,
        'drop_cap': 'none',
        'ornament_below_title': 'none',
        'ornament_above_title': 'hairline',
        'ornament_above_gap': 12,
        'header_style': 'centered',
        'header_font': 'Sans',
        'folio_position': 'centered',
        'folio_font': 'Sans',
        'header_rule': True,
        'first_line_indent': 0,
        'paragraph_spacing': 4,
        'scene_break': 'none',
        'chapter_end_ornament': 'none',
        'chapter_start_offset': 30,
        'text_alignment': 'left',
        'margin_multiplier': 0.78,
        'accent_color': '#7A6B5D',
        # Recipe titles: left-aligned bold sans, hairline rule above.
        'subhead_font': 'SansB', 'subhead_size': 16, 'subhead_align': 'left',
        'subhead_rule_above': 'hairline', 'rule_gap': 7,
        'subhead_break_need': 46, 'subhead_space_before': 16, 'subhead_space_after': 6,
        # Translation line under the recipe title.
        'subhead2_font': 'SansI', 'subhead2_size': 10, 'subhead2_align': 'left',
        'subhead2_color': '#7A6B5D',
        'subhead2_break_need': 24, 'subhead2_space_before': 2, 'subhead2_space_after': 4,
        'subtitle_font': 'SansI', 'subtitle_size': 10, 'subtitle_color': '#7A6B5D',
        'subtitle_align': 'left', 'subtitle_gap_after': 12,
        # Sub-labels: Ingredients, Method, Butcher's Tip.
        'sublabel_font': 'SansB', 'sublabel_size': 10,
        'sublabel_break_need': 22, 'sublabel_space_before': 8, 'sublabel_space_after': 5,
        # Ingredient lists: compact, indented, dashed.
        'list_font': 'Sans', 'list_size': 9, 'list_leading': 12,
        'list_indent': 12, 'list_marker': '\u2013',
        # Metadata block: **Cut:** Beef cheek (joue de boeuf).
        'meta_font': 'Sans', 'meta_label_font': 'SansB', 'meta_size': 9, 'meta_leading': 11.5,
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
    else:
        _delegate_ornament(c, y, cx, style, color, 40.0)


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
    else:
        _delegate_ornament(c, y, cx, style, color, 30.0)


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


# ══════════════════════════════════════════════════════════════════════
#  ORNAMENTAL INTERIOR DEFAULTS
#  Showcase settings for the drop cap, chapter opener, scene break,
#  running header, folio, pull quote and callout features. Templates not
#  listed here keep their classic layout.
# ══════════════════════════════════════════════════════════════════════

def _delegate_ornament(c, y, cx, style, color, width=40.0):
    """Draw a catalogue ornament by name.

    Lets templates name any ornament in ornaments.CATALOGUE (fleurons,
    flourishes, rules, icons) wherever an ornament style is expected."""
    import ornaments
    key = ornaments.normalize(style)
    if not key:
        return False
    ornaments.draw(c, key, cx, y, width, color, 0.5)
    return True


ORN_TEMPLATE_DEFAULTS = {
    'narrative': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.24,
        'chapter_number_format': 'arabic',
        'chapter_number_size': 10,
        'chapter_number_color': '#8B7355',
        'chapter_ornament': 'horizontal_rule',
        'chapter_ornament_width': 0.20,
        'chapter_ornament_color': '#B8A88A',
        'scene_break_style': 'diamond_rule',
        'scene_break_width': 0.18,
        'scene_break_color': '#A08E6E',
        'running_header_style': 'title_chapter',
        'running_header_rule': 'thin',
        'running_header_rule_color': '#D0C8B8',
        'running_header_size': 8,
        'running_header_color': '#8B7D6B',
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'page_number_size': 9,
        'pull_quote_style': 'framed',
        'pull_quote_size': 13,
        'callout_box_style': 'accent_left',
    },
    'fiction': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.28,
        'chapter_number_format': 'arabic',
        'chapter_number_size': 11,
        'chapter_number_color': '#8B7355',
        'chapter_ornament': 'flourish',
        'chapter_ornament_name': 'scroll',
        'chapter_ornament_width': 0.30,
        'chapter_title_position': 'centered',
        'drop_cap_enabled': True,
        'drop_cap_style': 'dropped',
        'drop_cap_lines': 3,
        'drop_cap_font': 'GarB',
        'drop_cap_color': '#5B4A34',
        'drop_cap_gap': 6,
        'scene_break_style': 'fleuron',
        'scene_break_ornament': 'fleur_de_lis',
        'scene_break_spacing_before': 16,
        'scene_break_spacing_after': 16,
        'scene_break_width': 0.20,
        'running_header_style': 'title_chapter',
        'running_header_rule': 'none',
        'running_header_size': 8,
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'pull_quote_style': 'large_italic',
        'pull_quote_size': 14,
        'callout_box_style': 'accent_left',
    },
    'heritage': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.26,
        'chapter_number_format': 'roman',
        'chapter_number_case': 'upper',
        'chapter_number_size': 12,
        'chapter_number_color': '#7A6240',
        'chapter_ornament': 'triple_ornament',
        'chapter_ornament_name': 'acanthus',
        'chapter_ornament_width': 0.36,
        'chapter_ornament_color': '#8B6F47',
        'chapter_frame_corner': 'rosette',
        'drop_cap_enabled': True,
        'drop_cap_style': 'ornamental',
        'drop_cap_lines': 3,
        'drop_cap_font': 'GarB',
        'drop_cap_color': '#5B4A34',
        'scene_break_style': 'triple_fleuron',
        'scene_break_ornament': 'acanthus',
        'scene_break_color': '#8B6F47',
        'running_header_style': 'chapter_only',
        'running_header_rule': 'ornamental',
        'running_header_rule_color': '#B8A88A',
        'running_header_case': 'title',
        'page_number_style': 'dots',
        'page_number_position': 'bottom_centre',
        'page_number_roman_front_matter': True,
        'pull_quote_style': 'indented_block',
        'pull_quote_rule_color': '#B8A88A',
        'pull_quote_mark_font': 'Gar',
        'callout_box_style': 'bordered',
        'callout_border_color': '#B8A88A',
    },
    'gothic': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.26,
        'chapter_number_format': 'roman',
        'chapter_number_size': 12,
        'chapter_number_color': '#5C5C70',
        'chapter_ornament': 'flourish',
        'chapter_ornament_name': 'fleur_de_lis',
        'chapter_ornament_color': '#2B2B33',
        'chapter_title_size': 26,
        'chapter_body_same_page': True,
        'drop_cap_enabled': True,
        'drop_cap_style': 'dropped',
        'drop_cap_lines': 3,
        'drop_cap_color': '#2B2B33',
        'drop_cap_font': 'GarB',
        'scene_break_style': 'triple_fleuron',
        'scene_break_ornament': 'fleur_de_lis',
        'scene_break_color': '#5C5C70',
        'scene_break_spacing_before': 18,
        'scene_break_spacing_after': 18,
        'running_header_style': 'chapter_only',
        'running_header_rule': 'double',
        'running_header_rule_color': '#3A3A48',
        'running_header_color': '#3A3A48',
        'running_header_case': 'upper',
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'page_number_color': '#3A3A48',
        'pull_quote_style': 'framed',
        'pull_quote_border_color': '#3A3A48',
        'pull_quote_font': 'GarI',
        'callout_box_style': 'accent_left',
    },
    'botanical': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.26,
        'chapter_number_format': 'word',
        'chapter_number_size': 11,
        'chapter_number_color': '#6B7A52',
        'chapter_ornament': 'triple_ornament',
        'chapter_ornament_name': 'leaf',
        'chapter_ornament_width': 0.34,
        'chapter_ornament_color': '#6B7A52',
        'drop_cap_enabled': True,
        'drop_cap_style': 'boxed',
        'drop_cap_lines': 3,
        'drop_cap_font': 'GarB',
        'drop_cap_color': '#4E5A3A',
        'drop_cap_bg_color': '#F1F4EA',
        'scene_break_style': 'fleuron',
        'scene_break_ornament': 'vine',
        'scene_break_color': '#6B7A52',
        'running_header_style': 'title_chapter',
        'running_header_rule': 'thin',
        'running_header_rule_color': '#C9D2BC',
        'running_header_color': '#5E6A48',
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'pull_quote_style': 'left_bar',
        'pull_quote_bar_color': '#6B7A52',
        'pull_quote_size': 12,
        'callout_box_style': 'rounded',
        'callout_border_color': '#C9D2BC',
        'callout_corner_radius': 6,
        'callout_icon': 'lightbulb',
        'callout_colors': {'tip': '#6B8E6B', 'note': '#8B7D6B'},
    },
    'minimal': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.30,
        'chapter_number_format': 'none',
        'chapter_ornament': 'horizontal_rule',
        'chapter_ornament_width': 0.14,
        'chapter_ornament_color': '#9A9A9A',
        'chapter_title_position': 'left',
        'drop_cap_enabled': True,
        'drop_cap_style': 'raised',
        'drop_cap_lines': 2,
        'drop_cap_font': 'SansL',
        'drop_cap_color': '#111111',
        'scene_break_style': 'thin_rule',
        'scene_break_width': 0.10,
        'scene_break_color': '#BBBBBB',
        'scene_break_spacing_before': 12,
        'scene_break_spacing_after': 12,
        'running_header_style': 'title_chapter',
        'running_header_rule': 'thin',
        'running_header_rule_color': '#DDDDDD',
        'running_header_size': 8,
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'page_number_size': 8,
        'pull_quote_style': 'large_italic',
        'callout_box_style': 'accent_top',
    },
    'guide': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.24,
        'chapter_number_format': 'arabic',
        'chapter_number_size': 11,
        'chapter_number_color': '#2C5F7A',
        'chapter_ornament': 'horizontal_rule',
        'chapter_ornament_width': 0.22,
        'chapter_ornament_color': '#7FA8BF',
        'drop_cap_enabled': True,
        'drop_cap_style': 'dropped',
        'drop_cap_lines': 2,
        'drop_cap_font': 'SansB',
        'drop_cap_color': '#1F4A5F',
        'scene_break_style': 'diamond_rule',
        'scene_break_width': 0.16,
        'scene_break_color': '#7FA8BF',
        'running_header_style': 'title_chapter',
        'running_header_rule': 'thin',
        'running_header_rule_color': '#BBD1DE',
        'running_header_color': '#2C5F7A',
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'pull_quote_style': 'framed',
        'pull_quote_border_color': '#BBD1DE',
        'callout_box_style': 'accent_left',
        'callout_colors': {'tip': '#4E8A6B', 'warning': '#B4683F',
                           'note': '#2C5F7A', 'key_takeaway': '#B8965B'},
        'callout_accent_width': 5,
    },
    'academic': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.22,
        'chapter_number_format': 'arabic',
        'chapter_number_size': 10,
        'chapter_number_color': '#6B6B6B',
        'chapter_title_position': 'left',
        'chapter_ornament': 'horizontal_rule',
        'chapter_ornament_width': 0.18,
        'chapter_ornament_color': '#9A9A9A',
        'scene_break_style': 'thin_rule',
        'scene_break_width': 0.14,
        'scene_break_color': '#A8A8A8',
        'running_header_style': 'title_only',
        'running_header_rule': 'thin',
        'running_header_rule_color': '#CCCCCC',
        'running_header_size': 8,
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'pull_quote_style': 'indented_block',
        'pull_quote_size': 11,
        'callout_box_style': 'bordered',
        'callout_show_default_heading': False,
    },
    'journal': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.30,
        'chapter_number_format': 'none',
        'chapter_ornament': 'horizontal_rule',
        'chapter_ornament_width': 0.18,
        'chapter_ornament_color': '#C0B49A',
        'drop_cap_enabled': True,
        'drop_cap_style': 'outline',
        'drop_cap_lines': 2,
        'drop_cap_font': 'GarB',
        'drop_cap_color': '#8C7E62',
        'scene_break_style': 'asterisks',
        'running_header_style': 'title_chapter',
        'running_header_rule': 'none',
        'running_header_size': 8,
        'page_number_style': 'ornamental',
        'page_number_position': 'bottom_centre',
        'pull_quote_style': 'decorative_marks',
        'pull_quote_mark_color': '#DCD2BE',
        'pull_quote_size': 13,
        'callout_box_style': 'bordered',
        'callout_border_color': '#DCD2BE',
    },
    'cookbook': {
        'chapter_opener_style': 'ornamental',
        'chapter_opener_drop': 0.22,
        'chapter_number_format': 'none',
        'chapter_ornament': 'horizontal_rule',
        'chapter_ornament_width': 0.30,
        'chapter_ornament_color': '#B4884E',
        'running_header_style': 'chapter_only',
        'running_header_rule': 'thin',
        'running_header_rule_color': '#E0D6C4',
        'running_header_color': '#8A6A3E',
        'page_number_style': 'plain',
        'page_number_position': 'bottom_outside',
        'pull_quote_style': 'left_bar',
        'pull_quote_bar_color': '#B4884E',
        'pull_quote_size': 11,
        'callout_box_style': 'accent_left',
        'callout_colors': {'tip': '#6B8E6B', 'warning': '#C4785B'},
        'callout_icon_size': 13,
    },
}

for _name, _defaults in ORN_TEMPLATE_DEFAULTS.items():
    if _name in TEMPLATES:
        TEMPLATES[_name].update(_defaults)
