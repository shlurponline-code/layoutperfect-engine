"""Professional interior features for the Layout Perfect engine.

The engine's original visual vocabulary was font, margins, leading and a plain
heading hierarchy. This module adds the elements boutique formatters hand-craft:

  1. Drop caps            - raised, dropped, outline, boxed, ornamental
  2. Ornamental openers   - number / ornament / title / epigraph zones
  3. Scene break library  - fleurons, flourishes, rules, geometry
  4. Running heads & feet - recto/verso patterns, rules, folio styles
  5. Pull quotes          - five styles with attribution
  6. Callout boxes        - six types, six box styles, page-splitting

Everything is configured through the template registry: a template gains keys
and each feature reads them here. A key that is absent falls back to a value
that reproduces the engine's previous behaviour, so existing templates are
unaffected until they opt in.
"""

import re

from reportlab.lib.colors import HexColor

import ornaments
from templates import (C_BODY, C_BROWN, C_GREY, C_MID, C_DARK,
                       draw_ornament, draw_scene_break, format_chapter_number)


def _eng():
    """The engine module, imported lazily to avoid a circular import."""
    import typeset_engine
    return typeset_engine


ENGINE_FONTS = ('Gar', 'GarB', 'GarI', 'GarBI', 'Sans', 'SansB', 'SansI',
                'Mono', 'MonoB')

FONT_ALIASES = {
    'gar': 'Gar', 'garb': 'GarB', 'gari': 'GarI', 'garbi': 'GarBI',
    'sans': 'Sans', 'sansb': 'SansB', 'sansi': 'SansI', 'sansbi': 'SansB',
    'mono': 'Mono', 'monob': 'MonoB', 'monoi': 'Mono',
    'freeserif': 'Gar', 'freeserif-regular': 'Gar', 'freeserif-roman': 'Gar',
    'freeserif-bold': 'GarB', 'freeserifbold': 'GarB',
    'freeserif-italic': 'GarI', 'freeserifitalic': 'GarI',
    'freeserif-bolditalic': 'GarBI', 'serif': 'Gar', 'serif-bold': 'GarB',
    'serif-italic': 'GarI', 'times': 'Gar', 'timesnewroman': 'Gar',
    'freesans': 'Sans', 'freesans-regular': 'Sans', 'freesansbold': 'SansB',
    'freesans-bold': 'SansB', 'freesans-italic': 'SansI',
    'freesansoblique': 'SansI', 'sans-serif': 'Sans', 'sansserif': 'Sans',
    'sans-serif-bold': 'SansB', 'freemono': 'Mono', 'freemono-bold': 'MonoB',
    'monospace': 'Mono',
}


def resolve_font(name, default='Gar'):
    """Map a template font name onto a registered engine font."""
    if not name:
        return default
    raw = str(name).strip()
    if raw in ENGINE_FONTS:
        return raw
    key = raw.lower().replace(' ', '').replace('_', '-')
    if key in FONT_ALIASES:
        return FONT_ALIASES[key]
    key = raw.lower().replace(' ', '-').replace('_', '-')
    return FONT_ALIASES.get(key, default)


def _hexcolor(value, default):
    if isinstance(value, str) and value.strip().startswith('#'):
        try:
            return HexColor(value.strip())
        except Exception:
            return default
    return default


def _apply_case(text, case):
    if not text:
        return text
    case = str(case or 'as-is').lower()
    if case in ('upper', 'uppercase', 'caps'):
        return text.upper()
    if case in ('lower', 'lowercase'):
        return text.lower()
    if case == 'title':
        return text.title()
    return text


_ROMAN = ((1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'),
          (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'),
          (5, 'V'), (4, 'IV'), (1, 'I'))


def to_roman(num):
    out = ''
    n = int(num)
    for value, glyph in _ROMAN:
        while n >= value:
            out += glyph
            n -= value
    return out or 'I'


ORDINALS = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
            'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen',
            'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen',
            'Twenty')


def number_word(num):
    n = int(num)
    if 1 <= n <= len(ORDINALS):
        return ORDINALS[n - 1]
    return str(n)


# ══════════════════════════════════════════════════════════════════════
#  MANUSCRIPT MARKERS  -  pull quotes and callouts in the markdown
# ══════════════════════════════════════════════════════════════════════
MARKER_NAMES = {
    'pullquote': 'pullquote', 'pull_quote': 'pullquote', 'quote': 'pullquote',
    'callout': 'callout', 'tip': 'tip', 'warning': 'warning', 'note': 'note',
    'definition': 'definition', 'key_takeaway': 'key_takeaway',
    'keytakeaway': 'key_takeaway', 'key': 'key_takeaway',
    'takeaway': 'key_takeaway', 'important': 'key_takeaway',
}
CALLABLE_KINDS = ('callout', 'tip', 'warning', 'note', 'definition',
                  'key_takeaway')

PLACEHOLDER_TMPL = '@@LPBLOCK{}@@'
PLACEHOLDER_RE = re.compile(r'^@@LPBLOCK(\d+)@@$')

_OPEN_FENCED_RE = re.compile(r'^\{\s*([A-Za-z_][A-Za-z_ ]*?)\s*(?::\s*([^}]*?))?\s*\}\s*$')
_OPEN_INLINE_RE = re.compile(
    r'^\{\s*([A-Za-z_][A-Za-z_ ]*?)\s*(?::\s*([^}]*?))?\s*\}'
    r'\s*(.*?)\s*\{\s*/\s*[A-Za-z_][A-Za-z_ ]*\s*\}\s*$')
_CLOSE_RE = re.compile(r'^\{\s*/\s*[A-Za-z_][A-Za-z_ ]*\s*\}\s*$')
_ATTRIB_RE = re.compile(r'^\{?\s*attribution[:\s]\s*(.*?)\s*\}?$', re.I)
_DASH_ATTRIB_RE = re.compile(r'^(?:--|\u2014|\u2013)\s*(.+)$')

# Whether markdown blockquote lines ("> text") are read as pull quotes. Off
# unless a template opts in, so manuscripts that use ">" for quoted matter
# keep rendering it as ordinary text.
BLOCKQUOTES = {'enabled': False}


def marker_kind(name):
    if not name:
        return None
    return MARKER_NAMES.get(str(name).strip().lower().replace(' ', '_'))


def extract_marked_blocks(lines, blockquotes=None):
    """Replace fenced marker blocks with single-line placeholders.

    Returns ``(lines, marked)``: *lines* is the manuscript with each
    ``{pullquote}``/``{callout}``/``{tip}`` block (and, when enabled, each
    ``>`` blockquote) swapped for a placeholder that survives paragraph
    joining, and *marked* is the list of parsed blocks."""
    use_bq = BLOCKQUOTES['enabled'] if blockquotes is None else bool(blockquotes)
    out, marked, i = [], [], 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        inline = _OPEN_INLINE_RE.match(stripped)
        kind = marker_kind(inline.group(1)) if inline else None
        if kind:
            body = [inline.group(3)] if inline.group(3).strip() else []
            out.extend(['', PLACEHOLDER_TMPL.format(len(marked)), ''])
            marked.append(build_marker(kind, (inline.group(2) or '').strip(), body))
            i += 1
            continue

        opened = _OPEN_FENCED_RE.match(stripped)
        kind = marker_kind(opened.group(1)) if opened else None
        if kind:
            body, i = _collect_fenced(lines, i + 1)
            out.extend(['', PLACEHOLDER_TMPL.format(len(marked)), ''])
            marked.append(build_marker(kind, (opened.group(2) or '').strip(), body))
            continue

        if use_bq and stripped.startswith('>'):
            body = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                body.append(lines[i].strip().lstrip('>').strip())
                i += 1
            out.extend(['', PLACEHOLDER_TMPL.format(len(marked)), ''])
            marked.append(build_marker('pullquote', '', body))
            continue

        out.append(raw)
        i += 1
    return out, marked


def _collect_fenced(lines, i):
    """Collect body lines up to the matching closing marker."""
    body = []
    while i < len(lines):
        if _CLOSE_RE.match(lines[i].strip()):
            return body, i + 1
        body.append(lines[i])
        i += 1
    return body, i


def build_marker(kind, heading, body_lines):
    """Turn a parsed marker into a story item the builder understands."""
    lines = [str(l).strip() for l in body_lines if str(l).strip()]
    if kind == 'pullquote':
        text, attribution = [], ''
        for idx, line in enumerate(lines):
            att = _ATTRIB_RE.match(line)
            if att:
                attribution = att.group(1)
                continue
            dash = _DASH_ATTRIB_RE.match(line)
            if dash and idx == len(lines) - 1:
                attribution = dash.group(1).strip()
                continue
            text.append(line)
        return {'type': 'pull_quote', 'text': ' '.join(text),
                'attribution': attribution}
    return {'type': 'callout', 'kind': kind, 'heading': heading,
            'lines': lines}


def apply_marked_blocks(blocks, marked):
    """Swap placeholders left by :func:`extract_marked_blocks` for real items."""
    if not marked:
        return blocks
    for blk in blocks:
        body = blk.get('body')
        if isinstance(body, list):
            for idx, item in enumerate(body):
                if item.get('type') != 'para':
                    continue
                m = PLACEHOLDER_RE.match((item.get('text') or '').strip())
                if m and int(m.group(1)) < len(marked):
                    body[idx] = dict(marked[int(m.group(1))])
        elif blk.get('type') == 'para':
            m = PLACEHOLDER_RE.match((blk.get('text') or '').strip())
            if m and int(m.group(1)) < len(marked):
                blk.update(dict(marked[int(m.group(1))]))
    return blocks


# ══════════════════════════════════════════════════════════════════════
#  RENDERER FEATURES
# ══════════════════════════════════════════════════════════════════════
class InteriorFeatures:
    """Mixin for BookRenderer; every method reads its settings from self.tpl."""

    QUOTE_CHARS = '"\'\u201c\u201d\u2018\u2019\u00ab\u00bb\u201e\u201a\u2039\u203a'

    def icfg(self, key, default=None):
        tpl = getattr(self, 'tpl', None) or {}
        return tpl.get(key, default)

    def icolor(self, key, default):
        return _hexcolor(self.icfg(key), default)

    def _top_limit(self):
        e = _eng()
        return e.PAGE_H - e.MARGIN_TOP - 10

    def _bottom_limit(self):
        return _eng().MARGIN_BOTTOM + 10

    def _fresh_page(self):
        self._finish_page()
        self._new_page()
        self.current_y = self._top_limit()

    def _hyphenate(self):
        return bool(getattr(_eng(), 'HYPHENATE', False))

    def _soft_break(self, word, font, sz, avail):
        """Break a word at a soft hyphen so it fills the available width."""
        soft = _eng().SOFT_HYPHEN
        plain = word.replace(soft, '')
        if soft not in word or avail <= 0:
            return None, plain
        parts = word.split(soft)
        fitted = ''
        for i, part in enumerate(parts):
            candidate = fitted + part
            width = self.c.stringWidth(
                candidate + '-' if i < len(parts) - 1 else candidate, font, sz)
            if width <= avail:
                fitted = candidate
            else:
                if fitted:
                    return fitted + '-', soft.join(parts[i:])
                return None, plain
        return fitted, ''

    def _wrap_widths(self, text, font, sz, narrow_w, full_w, narrow_lines):
        """Greedy wrap where the first narrow_lines lines use a narrow measure."""
        if self._hyphenate():
            text = _eng().add_soft_hyphens(text, _eng().HYPHEN_LANGUAGE)
        soft = _eng().SOFT_HYPHEN
        self.c.setFont(font, sz)
        words = [w for w in text.split() if w]
        lines, cur, i = [], '', 0
        while i < len(words):
            width = narrow_w if len(lines) < narrow_lines else full_w
            wide = words[i].replace(soft, '')
            test = f'{cur} {wide}'.strip()
            if not cur or self.c.stringWidth(test, font, sz) <= width:
                cur = test
                i += 1
                continue
            avail = width - self.c.stringWidth(cur + ' ', font, sz)
            head, tail = self._soft_break(words[i], font, sz, avail)
            if head:
                lines.append(f'{cur} {head}')
                if tail:
                    words[i] = tail
                    cur = ''
                else:
                    cur = ''
                    i += 1
            else:
                lines.append(cur)
                cur = ''
        if cur:
            lines.append(cur)
        return lines or ['']

    def _draw_fitted(self, line_text, x, y, font, sz, max_w, justify=True):
        """Draw one line, justifying only when it will not open obvious gaps."""
        c = self.c
        c.setFont(font, sz)
        words = line_text.split()
        if not justify or len(words) <= 1:
            c.drawString(x, y, line_text)
            return
        space_w = c.stringWidth(' ', font, sz)
        natural = sum(c.stringWidth(w, font, sz) for w in words) + space_w * (len(words) - 1)
        extra = max_w - natural
        if extra <= 0 or extra / (len(words) - 1) > space_w * 0.45:
            c.drawString(x, y, line_text)
            return
        gap = space_w + extra / (len(words) - 1)
        cur_x = x
        for w in words:
            c.drawString(cur_x, y, w)
            cur_x += c.stringWidth(w, font, sz) + gap

    def _draw_ornamental_frame(self, x, y, w, h, color):
        """Thin rule box with corner ticks, used by the ornamental drop cap."""
        c = self.c
        c.setStrokeColor(color)
        c.setLineWidth(0.45)
        c.rect(x, y, w, h, fill=0, stroke=1)
        tick = min(w, h) * 0.30
        c.setLineWidth(1.1)
        for (ox, oy, dx, dy) in ((x, y + h, 1, -1), (x + w, y + h, -1, -1),
                                 (x, y, 1, 1), (x + w, y, -1, 1)):
            c.line(ox, oy, ox + dx * tick, oy)
            c.line(ox, oy, ox, oy + dy * tick)

    # ══ Feature 1: drop caps ═════════════════════════════════════════
    def drop_cap_config(self):
        """Resolved drop cap settings, or None when this chapter has none."""
        enabled = self.icfg('drop_cap_enabled', None)
        legacy = self.icfg('drop_cap', 'none') or 'none'
        if enabled is None:
            if legacy in ('none', '', False):
                return None
            style = 'dropped'
            lines = 3 if legacy == 'decorative_3line' else 2
        else:
            if not enabled:
                return None
            style = str(self.icfg('drop_cap_style', 'dropped') or 'dropped').strip().lower()
            lines = int(self.icfg('drop_cap_lines', 3) or 3)
        e = _eng()
        return {
            'style': style,
            'lines': max(2, min(5, lines)),
            'font': resolve_font(self.icfg('drop_cap_font', 'GarB'), 'GarB'),
            'size': self.icfg('drop_cap_font_size'),
            'color': self.icolor('drop_cap_color', C_BODY),
            'bg': self.icolor('drop_cap_bg_color', HexColor('#F5F0E8')),
            'gap': float(self.icfg('drop_cap_gap', 4) or 4),
            'body_font': resolve_font(self.icfg('body_font', 'Gar'), 'Gar'),
            'body_size': float(self.icfg('body_size', None) or e.BODY_SZ),
            'leading': float(self.icfg('leading', None) or e.BODY_LD),
        }

    def arm_drop_cap(self):
        """Arm a drop cap for the next paragraph of this chapter."""
        self._drop_cap_cfg = self.drop_cap_config()
        self._drop_cap_used = False
        return self._drop_cap_cfg is not None

    def draw_drop_cap_paragraph(self, text):
        """Draw the chapter's opening paragraph with a drop cap.

        Returns False when the paragraph is not eligible, so the caller falls
        back to its normal paragraph rendering."""
        cfg = getattr(self, '_drop_cap_cfg', None)
        if not cfg or getattr(self, '_drop_cap_used', False):
            return False
        stripped = (text or '').strip()
        if len(stripped) < 12:
            return False
        if stripped[0] in ('-', '*', '#', '|', '!', '{', '>', '@'):
            return False
        self._drop_cap_cfg = None
        self._drop_cap_used = True

        c = self.c
        e = _eng()
        font, size, leading = cfg['body_font'], cfg['body_size'], cfg['leading']
        n_lines = cfg['lines']
        style = cfg['style']

        quote, body = '', stripped
        while body and body[0] in self.QUOTE_CHARS:
            quote += body[0]
            body = body[1:].lstrip()
        if len(body) < 6:
            return False
        letter, rest = body[0], body[1:].lstrip()

        cap_ratio = 0.70
        cap_h_body = size * cap_ratio
        if style == 'raised':
            drop_size = (n_lines * leading) / cap_ratio
        else:
            drop_size = ((n_lines - 1) * leading + cap_h_body) / cap_ratio
        if cfg.get('size'):
            drop_size = float(cfg['size'])
        drop_size = max(size * 1.6, drop_size)

        if self.current_y - ((n_lines + 1) * leading + 6) < self._bottom_limit():
            return False
        if style == 'raised' and self.current_y + drop_size * cap_ratio > self._top_limit() + leading * 0.5:
            style = 'dropped'
            drop_size = ((n_lines - 1) * leading + cap_h_body) / cap_ratio

        c.setFont(cfg['font'], drop_size)
        glyph_w = c.stringWidth(letter, cfg['font'], drop_size)
        gap = cfg['gap']
        lm, tw = self._lm(), self._tw()
        quote_w = 0.0
        if quote:
            c.setFont(font, size)
            quote_w = c.stringWidth(quote, font, size) + 1.5
        indent = quote_w + glyph_w + gap
        if indent > tw * 0.5:
            return False

        # Keep the cap inside the paragraph: a short paragraph must not leave a
        # giant letter hanging down into the paragraph below.
        if style != 'raised' and n_lines > 2:
            probe = self._wrap_widths(rest, font, size, tw - indent,
                                      tw - float(self.icfg('first_line_indent', 0) or 0),
                                      n_lines)
            if len(probe) < n_lines:
                n_lines = max(2, len(probe))
                drop_size = ((n_lines - 1) * leading + cap_h_body) / cap_ratio
                if cfg.get('size'):
                    drop_size = float(cfg['size'])
                drop_size = max(size * 1.6, drop_size)
                c.setFont(cfg['font'], drop_size)
                glyph_w = c.stringWidth(letter, cfg['font'], drop_size)
                indent = quote_w + glyph_w + gap
                if indent > tw * 0.5:
                    return False

        baseline = (self.current_y if style == 'raised'
                    else self.current_y - (n_lines - 1) * leading)

        if style == 'boxed':
            pad = drop_size * 0.10
            c.setFillColor(cfg['bg'])
            c.rect(lm + quote_w - pad, baseline - drop_size * 0.22 - pad,
                   glyph_w + pad * 2, drop_size * cap_ratio + pad * 2.4,
                   fill=1, stroke=0)
        elif style == 'ornamental':
            self._draw_ornamental_frame(lm + quote_w - 3,
                                        baseline - drop_size * 0.24 - 3,
                                        glyph_w + 6, drop_size * cap_ratio + 6,
                                        cfg['color'])

        if style == 'outline':
            c.setStrokeColor(cfg['color'])
            t = c.beginText(lm + quote_w, baseline)
            t.setFont(cfg['font'], drop_size)
            t.setTextRenderMode(1)
            t.textOut(letter)
            c.drawText(t)
        else:
            c.setFont(cfg['font'], drop_size)
            c.setFillColor(cfg['color'])
            c.drawString(lm + quote_w, baseline, letter)

        if quote:
            c.setFont(font, size)
            c.setFillColor(cfg['color'])
            c.drawString(lm, baseline + drop_size * cap_ratio * 0.80, quote)

        narrow_lines = 1 if style == 'raised' else n_lines
        narrow_w = tw - indent
        full_w = tw - float(self.icfg('first_line_indent', 0) or 0)
        lines = self._wrap_widths(rest, font, size, narrow_w, full_w, narrow_lines)
        justify = str(self.icfg('text_alignment', e.TEXT_ALIGNMENT)).lower() == 'justified'

        y = self.current_y
        for i, line_text in enumerate(lines):
            if y - leading < self._bottom_limit():
                self._fresh_page()
                y = self.current_y
            x = lm + (indent if i < narrow_lines else 0)
            avail = narrow_w if i < narrow_lines else full_w
            c.setFillColor(C_BODY)
            self._draw_fitted(line_text, x, y, font, size, avail,
                              justify and i < len(lines) - 1)
            y -= leading
        self.current_y = y - 2 - float(self.icfg('paragraph_spacing', 0) or 0)
        if style in ('ornamental', 'boxed'):
            cap_bottom = baseline - drop_size * 0.24 - 3
            self.current_y = min(self.current_y, cap_bottom - 12)
        return True


    # ══ Feature 2: ornamental chapter openers ═════════════════════════
    OPENER_KEYS = ('chapter_opener_style', 'chapter_number_format',
                   'chapter_ornament', 'chapter_ornament_name',
                   'chapter_opener_drop', 'chapter_body_same_page',
                   'epigraph_font', 'chapter_number_font',
                   'chapter_number_size')
    ORNAMENT_HEIGHTS = {
        'horizontal_rule': 14.0, 'rule': 14.0, 'line': 14.0,
        'diamond_rule': 16.0, 'rule_with_diamond': 16.0,
        'bracket_ornament': 22.0, 'brackets': 22.0,
        'flourish': 30.0, 'ornamental': 30.0, 'fleuron': 30.0,
        'triple_ornament': 26.0, 'frame': 12.0,
    }
    ORNAMENT_GAP = 16.0

    def opener_is_styled(self):
        tpl = getattr(self, 'tpl', None) or {}
        return any(k in tpl for k in self.OPENER_KEYS)

    def chapter_ornament_height(self, ornament, width):
        style = str(ornament or 'none').strip().lower()
        if style in ('none', ''):
            return 0.0
        return self.ORNAMENT_HEIGHTS.get(style, min(34.0, width * 0.35)) + self.ORNAMENT_GAP

    def _opener_number_text(self, fmt):
        n = getattr(self, 'chapter_count', 1)
        fmt = str(fmt or 'word').strip().lower()
        if fmt in ('none', '', 'off', 'false'):
            return ''
        if fmt == 'roman':
            return to_roman(n)
        if fmt == 'arabic':
            return str(n)
        if fmt == 'word':
            return number_word(n)
        return format_chapter_number(n, fmt) or ''

    def render_ornamental_chapter_opener(self, title, subtitle=''):
        """Draw the ornamental chapter opener: number, ornament, title, epigraph.

        Returns True when it rendered the opener; False so the caller keeps its
        own opener. Only templates that carry opener keys take this path."""
        if not self.opener_is_styled():
            return False
        e = _eng()
        c = self.c
        self._ensure_recto()
        self.is_front_matter = False
        self.chapter_count = getattr(self, 'chapter_count', 0) + 1
        self.current_chapter_title = title
        if self.icfg('suppress_on_chapter_opener', None):
            self._suppress_hdr_this_page = True

        tw = self._tw()
        cx = self._lm() + tw / 2
        frac = min(max(float(self.icfg('chapter_opener_drop', 0.30) or 0.30), 0.10), 0.60)
        y = e.PAGE_H - e.PAGE_H * frac
        if y > self._top_limit():
            y = self._top_limit()

        ornament = str(self.icfg('chapter_ornament', 'none') or 'none').strip().lower()
        heading_font = resolve_font(self.icfg('heading_font', 'GarB'), 'GarB')
        title_font = resolve_font(self.icfg('chapter_title_font', heading_font), heading_font)
        # CJK safety net: switch font when title contains CJK characters
        title_font = e.cjk_aware_font(title, title_font)
        title_size = float(self.icfg('chapter_title_size', None) or e.CH_TITLE_SZ)
        num_font = resolve_font(self.icfg('chapter_number_font', 'Sans'), 'Sans')
        num_size = float(self.icfg('chapter_number_size', 11) or 11)
        num_text = self._opener_number_text(self.icfg('chapter_number_format', 'word'))
        if num_text and self.icfg('chapter_number_case', None):
            num_text = _apply_case(num_text, self.icfg('chapter_number_case'))
        if num_text:
            num_font = e.cjk_aware_font(num_text, num_font)
        title_case = self.icfg('chapter_title_case', None)
        title_pos = str(self.icfg('chapter_title_position', 'centered') or 'centered').lower()
        title_lines = []
        if title and title_pos != 'none':
            title_lines = self._wrap(_apply_case(str(title), title_case) if title_case else str(title),
                                     title_font, title_size, tw * 0.92)
        orn_frac = min(max(float(self.icfg('chapter_ornament_width', 0.4) or 0.4), 0.10), 0.90)
        orn_w = max(24.0, tw * orn_frac)
        orn_h = self.chapter_ornament_height(ornament, orn_w)
        epi_font = resolve_font(self.icfg('epigraph_font', 'GarI'), 'GarI')
        if subtitle:
            epi_font = e.cjk_aware_font(str(subtitle), epi_font)
        epi_size = float(self.icfg('epigraph_size', 10) or 10)
        epi_lines = (self._wrap(str(subtitle), epi_font, epi_size, tw - 30)
                     if subtitle and self.icfg('epigraph_font', None) else [])

        # Measure the block so the optional frame can sit behind it.
        block_top = y + num_size * 0.9
        block_bottom = y - (num_size * 1.9 if num_text else 0.0)
        if ornament not in ('none', ''):
            block_bottom -= orn_h
        if title_lines:
            block_bottom -= len(title_lines) * title_size * 1.25
        if epi_lines:
            block_bottom -= 14 + len(epi_lines) * epi_size * 1.5
        if ornament == 'frame':
            self._draw_opener_frame(tw, block_top, block_bottom)

        if num_text:
            c.setFont(num_font, num_size)
            c.setFillColor(self.icolor('chapter_number_color', C_MID))
            for i, ln in enumerate(self._wrap(num_text, num_font, num_size, tw)):
                c.drawCentredString(cx, y - i * num_size * 1.35, ln)
            y -= num_size * 1.9

        if ornament not in ('none', ''):
            orn_y = y
            self.draw_chapter_ornament(orn_y, cx, ornament, orn_w)
            # Clear the ornament's own height plus the title's ascent so the
            # ornament never runs through the chapter title.
            drawn_h = float(getattr(self, '_ornament_drawn_h',
                                    max(0.0, orn_h - self.ORNAMENT_GAP)))
            clearance = drawn_h * 0.5 + max(10.0, (title_size * 0.80) if title_lines else 14.0) + 6.0
            y = orn_y - clearance

        if title_lines:
            title_color = self.icolor('chapter_title_color', C_BODY)
            left = title_pos in ('left', 'left_below', 'left_above')
            for ln in title_lines:
                c.setFont(title_font, title_size)
                c.setFillColor(title_color)
                if left:
                    c.drawString(self._lm(), y, ln)
                else:
                    c.drawCentredString(cx, y, ln)
                y -= title_size * 1.25
            y -= 6

        if epi_lines:
            epi_color = self.icolor('epigraph_color', C_GREY)
            y -= 8
            for ln in epi_lines:
                c.setFont(epi_font, epi_size)
                c.setFillColor(epi_color)
                c.drawCentredString(cx, y, ln)
                y -= epi_size * 1.5
        elif subtitle and title_pos != 'none':
            sub_font = resolve_font(self.icfg('subtitle_font', 'GarI'), 'GarI')
            sub_size = float(self.icfg('subtitle_size', 10) or 10)
            for ln in self._wrap(str(subtitle), sub_font, sub_size, tw):
                c.setFont(sub_font, sub_size)
                c.setFillColor(self.icolor('subtitle_color', C_BROWN))
                c.drawCentredString(cx, y, ln)
                y -= sub_size * 1.6

        if self.icfg('chapter_body_same_page', True) in (False, 'false', 'no'):
            self._finish_page()
            self._new_page()
            self.is_front_matter = False
            self.current_y = self._top_limit()
        else:
            self.current_y = y - float(self.icfg('chapter_opener_gap_after', 26) or 26)

        self.arm_drop_cap()
        return True

    def draw_chapter_ornament(self, y, cx, ornament, width=None, name=None):
        """Draw the ornament between the chapter number and the title."""
        style = str(ornament or 'none').strip().lower()
        if style in ('none', ''):
            return y
        c = self.c
        tw = self._tw()
        frac = min(max(float(self.icfg('chapter_ornament_width', 0.4) or 0.4), 0.10), 0.90)
        width = float(width or max(24.0, tw * frac))
        color = self.icolor('chapter_ornament_color', C_BROWN)
        lw = float(self.icfg('chapter_ornament_stroke_width', 0.6) or 0.6)
        name = name or self.icfg('chapter_ornament_name', '') or ''
        gap = self.ORNAMENT_GAP
        self._ornament_drawn_h = 6.0
        if style in ('horizontal_rule', 'rule', 'line'):
            ornaments.draw_rule(c, self.icfg('chapter_rule_style', 'thin'), cx, y, width, color, lw)
        elif style in ('diamond_rule', 'rule_with_diamond'):
            self._ornament_drawn_h = 18.0
            ornaments.draw_rule(c, 'ornamental_centre', cx, y, width, color, lw)
        elif style in ('bracket_ornament', 'brackets', 'bracket'):
            self._ornament_drawn_h = 24.0
            self._draw_bracket_ornament(cx, y, width, color, lw)
            gap = 24.0
        elif style in ('triple_ornament', 'triple'):
            self._ornament_drawn_h = 30.0
            ornaments.draw_triple(c, name or 'leaf', cx, y, min(width * 1.4, tw * 0.7), color, lw)
        elif style == 'frame':
            ornaments.draw_rule(c, 'thin', cx, y, width * 0.45, color, lw)
            gap = 10.0
        else:
            key = ornaments.normalize(name) or ornaments.normalize(style)
            if not key:
                key = 'scroll' if style in ('flourish', 'ornamental') else 'fleur_de_lis'
            if style == 'fleuron':
                draw_w = min(width * 1.6, 46.0)
            elif style in ('flourish', 'ornamental'):
                draw_w = min(width * 1.3, tw * 0.42)
            else:
                draw_w = min(width * 1.7, tw * 0.6)
            self._ornament_drawn_h = max(22.0, min(58.0, draw_w * 0.52))
            ornaments.draw(c, key, cx, y, draw_w, color, lw)
        return y - gap

    def _draw_bracket_ornament(self, cx, y, width, color, lw):
        c = self.c
        h = min(14.0, max(8.0, width * 0.20))
        c.setStrokeColor(color)
        c.setLineWidth(lw)
        for flip in (-1, 1):
            x = cx + flip * width / 2
            p = c.beginPath()
            p.moveTo(x, y + h)
            p.curveTo(x - flip * h * 0.7, y + h * 0.6,
                      x - flip * h * 0.7, y - h * 0.6, x, y - h)
            c.drawPath(p, fill=0, stroke=1)
        c.setFillColor(color)
        c.circle(cx, y, max(1.2, lw * 1.8), fill=1, stroke=0)

    def _draw_opener_frame(self, tw, top, bottom):
        """Decorative frame drawn behind the chapter opener block."""
        c = self.c
        color = self.icolor('chapter_ornament_color', C_BROWN)
        pad_x = tw * 0.10
        pad_y = 14.0
        x0 = self._lm() + pad_x
        w = tw - pad_x * 2
        y0 = bottom - pad_y
        h = max((top - bottom) + pad_y * 2, 20.0)
        c.setStrokeColor(color)
        c.setLineWidth(float(self.icfg('chapter_frame_width', 0.6) or 0.6))
        c.rect(x0, y0, w, h, fill=0, stroke=1)
        corner = self.icfg('chapter_frame_corner', 'rosette')
        for (ox, oy, dx, dy) in ((x0, y0 + h, 1, -1), (x0 + w, y0 + h, -1, -1),
                                 (x0, y0, 1, 1), (x0 + w, y0, -1, 1)):
            ornaments.draw(c, corner, ox + dx * 8, oy + dy * 8, 14, color, 0.6)

    # ══ Feature 3: scene break ornaments ═════════════════════════════
    def scene_break_style_name(self):
        return self.icfg('scene_break_style', None) or self.icfg('scene_break', 'dots')

    def render_scene_break(self, style=None):
        """Draw the configured scene break. Legacy style names keep working."""
        if style is None:
            style = self.scene_break_style_name()
        key = str(style or '').strip().lower()
        c = self.c
        cx = self._lm() + self._tw() / 2
        before = float(self.icfg('scene_break_spacing_before', 14) or 14)
        after = float(self.icfg('scene_break_spacing_after', 14) or 14)
        color = self.icolor('scene_break_color', C_MID)
        frac = min(max(float(self.icfg('scene_break_width', 0.25) or 0.25), 0.05), 1.0)
        width = max(16.0, self._tw() * frac)
        lw = float(self.icfg('scene_break_stroke_width', 0.5) or 0.5)
        name = self.icfg('scene_break_ornament', '') or ''
        self.current_y -= before
        y = self.current_y

        if key in ('blank', 'space'):
            pass
        elif key in ('asterisks', 'three_asterisks'):
            self._ctxt(y, '* * *', 'GarB', 14, color)
        elif key == 'fleuron':
            ornaments.draw(c, name or 'fleur_de_lis', cx, y, min(width * 1.8, 46.0), color, lw)
        elif key == 'triple_fleuron':
            ornaments.draw_triple(c, name or 'leaf', cx, y, min(width * 1.6, self._tw() * 0.5), color, lw)
        elif key in ('thin_rule', 'short_rule'):
            ornaments.draw_rule(c, 'thin', cx, y, width, color, lw)
        elif key == 'tapered_rule':
            ornaments.draw_rule(c, 'tapered', cx, y, width * 1.8, color, lw)
        elif key == 'diamond_rule':
            ornaments.draw_rule(c, 'ornamental_centre', cx, y, width, color, lw)
        elif key == 'flourish':
            ornaments.draw(c, name or 'scroll', cx, y, min(width * 2.6, self._tw() * 0.6), color, lw)
        elif key == 'double_rule':
            ornaments.draw_rule(c, 'double', cx, y, width, color, lw)
        elif ornaments.is_known(key):
            ornaments.draw(c, key, cx, y, min(width * 2.0, self._tw() * 0.6), color, lw)
        else:
            draw_scene_break(c, y, cx, style, color)
        self.current_y -= after


    # ══ Feature 4: running headers, rules and folios ══════════════════
    HEADER_KEYS = ('running_header_style', 'running_header_font',
                   'running_header_size', 'running_header_color',
                   'running_header_case', 'running_header_rule',
                   'running_header_rule_color', 'running_header_rule_offset',
                   'running_header_rule_width')
    PAGE_NUM_KEYS = ('page_number_style', 'page_number_position',
                     'page_number_font', 'page_number_size',
                     'page_number_color', 'running_footer_rule',
                     'suppress_on_blank_pages', 'page_number_roman_front_matter')
    LEGACY_HEADER_PATTERNS = {
        'centered': 'chapter_only',
        'title_left_chapter_right': 'title_chapter',
        'author_left_chapter_right': 'author_title',
        'chapter_left_section_right': 'title_chapter',
        'none': 'none',
    }

    def _legacy_header_pattern(self):
        style = str(self.icfg('header_style', 'centered') or 'centered').lower()
        return self.LEGACY_HEADER_PATTERNS.get(style, 'chapter_only')

    def _capture_opener_page(self):
        """Read (and clear) the 'this page starts a chapter' flag."""
        flag = bool(getattr(self, '_suppress_hdr_this_page', False))
        self._suppress_hdr_this_page = False
        self._opener_page_captured = flag
        return flag

    def _draw_header_rule(self, l, right_edge, cx):
        style = str(self.icfg('running_header_rule', 'none') or 'none').strip().lower()
        if style in ('none', '', 'off', 'false'):
            return
        color = self.icolor('running_header_rule_color', HexColor('#CCCCCC'))
        lw = float(self.icfg('running_header_rule_width', 0.5) or 0.5)
        offset = float(self.icfg('running_header_rule_offset', 6) or 6)
        e = _eng()
        width = right_edge - l
        rule_cx = l + width / 2
        y = e.HEADER_Y - offset
        if style == 'thick':
            ornaments.draw_rule(self.c, 'thick', rule_cx, y, width, color, lw)
        elif style == 'double':
            ornaments.draw_rule(self.c, 'double', rule_cx, y, width, color, lw)
        elif style in ('ornamental', 'ornament'):
            ornaments.draw_rule(self.c, 'ornamental_centre', rule_cx, y, width, color, lw)
        elif style == 'tapered':
            ornaments.draw_rule(self.c, 'tapered', rule_cx, y, width, color, lw)
        else:
            ornaments.draw_rule(self.c, 'thin', rule_cx, y, width, color, lw)

    def render_running_header(self):
        """Styled running head (recto/verso patterns + rule).

        Returns True when it handled the header, False so the engine keeps its
        original centred/left-right header drawing."""
        tpl = getattr(self, 'tpl', None) or {}
        if not any(k in tpl for k in self.HEADER_KEYS):
            return False
        opener_page = self._capture_opener_page()
        e = _eng()
        if getattr(self, 'is_front_matter', False):
            return True
        if getattr(self, 'suppress_hdr', False) and self.icfg('suppress_on_blank_pages', True):
            return True
        if opener_page and self.icfg('suppress_on_chapter_opener', False):
            return True

        pattern = str(self.icfg('running_header_style', self._legacy_header_pattern()) or 'none').lower()
        pattern = pattern.strip().replace('-', '_').replace(' ', '_')
        if pattern in ('none', 'off', '', 'false'):
            return True
        font = resolve_font(self.icfg('running_header_font', 'Gar'), 'Gar')
        size = float(self.icfg('running_header_size', 8) or 8)
        color = self.icolor('running_header_color', C_GREY)
        case = self.icfg('running_header_case', 'as-is')
        l, r = self._margins()
        right_edge = e.PAGE_W - r
        cx = l + (right_edge - l) / 2
        y = e.HEADER_Y
        recto = getattr(self, 'page_num', 1) % 2 == 1
        author = _apply_case(getattr(self, 'author_name', '') or '', case)
        title = _apply_case(getattr(self, 'header_text', '') or '', case)
        chapter = _apply_case(getattr(self, 'current_chapter_title', '') or '', case)

        c = self.c
        c.setFillColor(color)

        def _draw_hdr(method, x, text):
            """Draw header text with CJK-aware font switching."""
            hdr_font = e.cjk_aware_font(text, font)
            c.setFont(hdr_font, size)
            method(x, y, text)

        if pattern == 'author_title':
            if recto:
                _draw_hdr(c.drawRightString, right_edge, title)
            else:
                _draw_hdr(c.drawString, l, author)
        elif pattern == 'title_chapter':
            if recto:
                _draw_hdr(c.drawRightString, right_edge, chapter or title)
            else:
                _draw_hdr(c.drawString, l, title)
        elif pattern == 'chapter_only':
            _draw_hdr(c.drawCentredString, cx, chapter or title)
        elif pattern == 'author_only':
            _draw_hdr(c.drawCentredString, cx, author)
        elif pattern == 'title_only':
            _draw_hdr(c.drawCentredString, cx, title)
        elif pattern == 'chapter_author':
            if recto:
                _draw_hdr(c.drawRightString, right_edge, author)
            else:
                _draw_hdr(c.drawString, l, chapter or title)
        elif pattern == 'author_chapter':
            if recto:
                _draw_hdr(c.drawRightString, right_edge, chapter or title)
            else:
                _draw_hdr(c.drawString, l, author)

        self._draw_header_rule(l, right_edge, cx)
        return True

    def _page_number_label(self, style, label, n, front):
        """Decorate the folio text for the configured folio style."""
        if style == 'dashes':
            return '\u2013 ' + label + ' \u2013'
        if style == 'dots':
            return '. ' + label + ' .'
        if style == 'brackets':
            return '[ ' + label + ' ]'
        return label

    def _draw_ornamental_folio(self, x, y, label, font, size):
        """Folio flanked by small drawn diamonds (font independent)."""
        c = self.c
        w = c.stringWidth(label, font, size)
        c.drawString(x, y, label)
        c.setFillColor(self.icolor('page_number_color', C_GREY))
        for dx in (-1, 1):
            px = x + (w + 7) * dx + (0 if dx < 0 else 0)
            if dx < 0:
                px = x - 7
            else:
                px = x + w + 7
            p = c.beginPath()
            p.moveTo(px, y + size * 0.28)
            p.lineTo(px + 1.6, y + size * 0.28 - 1.6)
            p.lineTo(px, y + size * 0.28 - 3.2)
            p.lineTo(px - 1.6, y + size * 0.28 - 1.6)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

    def render_styled_page_number(self):
        """Styled folio: position, decoration, roman front matter, footer rule.

        Returns True when it handled the folio, False to use the engine's own
        folio drawing."""
        opener_page = getattr(self, '_opener_page_captured', None)
        if opener_page is None:
            opener_page = bool(getattr(self, '_suppress_hdr_this_page', False))
        self._opener_page_captured = None
        self._suppress_hdr_this_page = False

        tpl = getattr(self, 'tpl', None) or {}
        if not any(k in tpl for k in self.PAGE_NUM_KEYS):
            return False
        style = str(self.icfg('page_number_style', 'plain') or 'plain').strip().lower()
        if style in ('none', 'off', 'false', ''):
            return True
        if getattr(self, '_suppress_folio_this_page', False):
            self._suppress_folio_this_page = False
            return True
        front = bool(getattr(self, 'is_front_matter', False))
        roman_front = bool(self.icfg('page_number_roman_front_matter', style == 'roman'))
        if front and not (style == 'roman' and roman_front):
            return True
        if getattr(self, 'suppress_hdr', False) and self.icfg('suppress_on_blank_pages', True):
            return True
        if opener_page and self.icfg('suppress_on_chapter_opener', False):
            return True

        e = _eng()
        n = int(getattr(self, 'page_num', 1))
        label = to_roman(n).lower() if (front and roman_front) else str(n)
        font = resolve_font(self.icfg('page_number_font', 'Gar'), 'Gar')
        size = float(self.icfg('page_number_size', 9) or 9)
        color = self.icolor('page_number_color', C_GREY)
        pos = str(self.icfg('page_number_position', 'bottom_centre') or 'bottom_centre').strip().lower()
        l, r = self._margins()
        right_edge = e.PAGE_W - r
        cx = l + (right_edge - l) / 2
        c = self.c
        c.setFont(font, size)
        c.setFillColor(color)

        # Rule between text block and folio (above a bottom folio).
        rule = str(self.icfg('running_footer_rule', 'none') or 'none').strip().lower()
        if rule not in ('none', '', 'off', 'false'):
            rule_color = self.icolor('running_footer_rule_color', HexColor('#CCCCCC'))
            rule_lw = float(self.icfg('running_footer_rule_width', 0.5) or 0.5)
            rw = right_edge - l
            ry = e.FOOTER_Y + float(self.icfg('running_footer_rule_offset', 12) or 12)
            key = {'thick': 'thick', 'double': 'double', 'tapered': 'tapered',
                   'ornamental': 'ornamental_centre', 'ornament': 'ornamental_centre'}.get(rule, 'thin')
            ornaments.draw_rule(c, key, cx, ry, rw, rule_color, rule_lw)

        text = self._page_number_label(style, label, n, front)
        if pos == 'bottom_outside':
            if n % 2 == 0:
                x = l
            else:
                x = right_edge - c.stringWidth(text, font, size)
        elif pos == 'top_outside':
            hdr_none = str(self.icfg('running_header_style', self._legacy_header_pattern())).lower() == 'none'
            y = e.HEADER_Y if hdr_none else e.FOOTER_Y
            if n % 2 == 0:
                self._place_folio(text, font, size, style, x=l, y=y, centre=False)
            else:
                self._place_folio(text, font, size, style,
                                  x=right_edge - c.stringWidth(text, font, size),
                                  y=y, centre=False)
            return True
        elif pos == 'header_centre':
            self._place_folio(text, font, size, style, x=cx, y=e.HEADER_Y, centre=True)
            return True
        else:
            self._place_folio(text, font, size, style, x=cx, y=e.FOOTER_Y, centre=True)
            return True

        self._place_folio(text, font, size, style, x=x, y=e.FOOTER_Y, centre=False)
        return True

    def _place_folio(self, text, font, size, style, x, y, centre):
        c = self.c
        c.setFont(font, size)
        c.setFillColor(self.icolor('page_number_color', C_GREY))
        if style == 'ornamental':
            left = x - c.stringWidth(text, font, size) / 2 if centre else x
            self._draw_ornamental_folio(left, y, text, font, size)
            return
        if centre:
            c.drawCentredString(x, y, text)
        else:
            c.drawString(x, y, text)


    # ══ Feature 5: pull quotes ════════════════════════════════════════
    def render_pull_quote(self, text, attribution=None):
        """Draw an extracted pull quote with optional attribution."""
        text = str(text or '').strip()
        if not text:
            return
        e = _eng()
        c = self.c
        style = str(self.icfg('pull_quote_style', 'large_italic') or 'large_italic').strip().lower()
        font = resolve_font(self.icfg('pull_quote_font', 'GarI'), 'GarI')
        size = float(self.icfg('pull_quote_size', 14) or 14)
        color = self.icolor('pull_quote_color', C_BODY)
        indent = float(self.icfg('pull_quote_indent', 36) or 36)
        before = float(self.icfg('pull_quote_spacing_before', 24) or 24)
        after = float(self.icfg('pull_quote_spacing_after', 24) or 24)
        bar_w = float(self.icfg('pull_quote_bar_width', 4) or 4)
        leading = size * 1.45
        lm, tw = self._lm(), self._tw()
        pad = 10.0

        if style == 'left_bar':
            text_x = lm + indent * 0.4 + bar_w + pad
            text_w = tw - indent * 0.4 - bar_w - pad * 2
        elif style in ('indented_block', 'framed', 'decorative_marks'):
            text_x = lm + indent
            text_w = tw - indent * 2
        else:
            text_x = lm + indent
            text_w = tw - indent * 2
        text_w = max(40.0, text_w)

        lines = self._wrap(text, font, size, text_w)
        attr_font = resolve_font(self.icfg('pull_quote_attribution_font', 'Gar'), 'Gar')
        attr_size = float(self.icfg('pull_quote_attribution_size', 9) or 9)
        attr = str(attribution or '').strip()
        block_h = len(lines) * leading + pad * 2 + (attr_size * 1.8 if attr else 0.0)

        top = self.current_y - before
        if top - block_h < self._bottom_limit() and top < self._top_limit() - 20:
            self._fresh_page()
            top = self.current_y - before
        bottom = top - block_h

        if style == 'left_bar':
            c.setFillColor(self.icolor('pull_quote_bar_color', C_BROWN))
            c.rect(lm + indent * 0.4, bottom, bar_w, block_h, fill=1, stroke=0)
        elif style == 'indented_block':
            rule_color = self.icolor('pull_quote_rule_color', C_GREY)
            ornaments.draw_rule(c, 'thin', lm + tw / 2, top, tw - indent * 2, rule_color, 0.5)
            ornaments.draw_rule(c, 'thin', lm + tw / 2, bottom, tw - indent * 2, rule_color, 0.5)
        elif style == 'framed':
            c.setStrokeColor(self.icolor('pull_quote_border_color', C_GREY))
            c.setLineWidth(float(self.icfg('pull_quote_border_width', 0.75) or 0.75))
            c.rect(lm + indent * 0.5, bottom, tw - indent, block_h, fill=0, stroke=1)
        elif style == 'decorative_marks':
            mark_size = float(self.icfg('pull_quote_mark_size', 60) or 60)
            mark_font = resolve_font(self.icfg('pull_quote_mark_font', 'Gar'), 'Gar')
            c.setFont(mark_font, mark_size)
            c.setFillColor(self.icolor('pull_quote_mark_color', HexColor('#D4C5B0')))
            c.drawString(text_x - mark_size * 0.28, top - mark_size * 0.60, '\u201c')
            c.drawRightString(text_x + text_w + mark_size * 0.10,
                              bottom - mark_size * 0.25, '\u201d')

        y = top - pad - size * 0.9
        for line in lines:
            c.setFont(font, size)
            c.setFillColor(color)
            if style == 'large_italic':
                c.drawCentredString(lm + tw / 2, y, line)
            else:
                c.drawString(text_x, y, line)
            y -= leading

        if attr:
            y -= attr_size * 0.4
            c.setFont(attr_font, attr_size)
            c.setFillColor(self.icolor('pull_quote_attribution_color', C_GREY))
            c.drawRightString(text_x + text_w, y, '\u2013 ' + attr)
            y -= attr_size * 1.4

        self.current_y = min(y, bottom) - after

    # ══ Feature 6: callout and tip boxes ══════════════════════════════
    CALLOUT_TYPES = {
        'callout': ('#5B8DB8', ''),
        'tip': ('#6B8E6B', 'lightbulb'),
        'warning': ('#C4785B', 'warning'),
        'note': ('#8B7D6B', 'info'),
        'definition': ('#7B6B8E', 'book'),
        'key_takeaway': ('#B8965B', 'key'),
    }
    CALLOUT_LABELS = {
        'callout': '', 'tip': 'Tip', 'warning': 'Warning', 'note': 'Note',
        'definition': 'Definition', 'key_takeaway': 'Key Takeaway',
    }

    def _callout_accent(self, kind):
        base = _hexcolor(self.CALLOUT_TYPES.get(kind, self.CALLOUT_TYPES['callout'])[0], C_BROWN)
        overrides = self.icfg('callout_colors', None)
        if isinstance(overrides, dict):
            for key in (kind, 'default'):
                value = overrides.get(key)
                if isinstance(value, str):
                    return _hexcolor(value, base)
        return base

    def render_callout(self, kind, heading='', lines=None):
        """Draw a callout / tip / warning / note / definition / key-takeaway box."""
        body_lines = [str(l).strip() for l in (lines or []) if str(l).strip()]
        if not body_lines:
            return
        e = _eng()
        c = self.c
        kind = str(kind or 'callout').strip().lower()
        if kind not in self.CALLOUT_TYPES:
            kind = 'callout'
        accent = self._callout_accent(kind)
        style = str(self.icfg('callout_box_style', 'accent_left') or 'accent_left').strip().lower()
        pad = float(self.icfg('callout_padding', 12) or 12)
        mt = float(self.icfg('callout_margin_top', 12) or 12)
        mb = float(self.icfg('callout_margin_bottom', 12) or 12)
        body_font = resolve_font(self.icfg('callout_body_font', self.icfg('body_font', 'Gar')), 'Gar')
        body_size = float(self.icfg('callout_body_size', 9.5) or 9.5)
        head_font = resolve_font(self.icfg('callout_heading_font', 'SansB'), 'SansB')
        head_size = float(self.icfg('callout_heading_size', 10) or 10)
        accent_w = float(self.icfg('callout_accent_width', 4) or 4)
        icon_size = float(self.icfg('callout_icon_size', 14) or 14)
        radius = float(self.icfg('callout_corner_radius', 6) or 6)
        border_color = self.icolor('callout_border_color', HexColor('#CCCCCC'))
        border_w = float(self.icfg('callout_border_width', 0.75) or 0.75)
        bg_alpha = float(self.icfg('callout_bg_opacity', 0.08) or 0.08)

        icon = self.icfg('callout_icon', '') or self.CALLOUT_TYPES[kind][1]
        if style != 'icon_callout':
            icon = ''

        side = accent_w + 6.0 if style in ('accent_left', 'icon_callout') else 0.0
        inner_x = self._lm() + pad + side
        inner_w = self._tw() - pad * 2 - side
        if icon:
            inner_x += icon_size + 6.0
            inner_w -= icon_size + 6.0
        inner_w = max(60.0, inner_w)

        label = str(heading or '').strip()
        if not label and self.icfg('callout_show_default_heading', True):
            label = self.CALLOUT_LABELS.get(kind, '')

        rows = []
        if label:
            for ln in self._wrap(label, head_font, head_size, inner_w):
                rows.append((ln, head_font, head_size, 0.0, accent))
            rows.append(('', head_font, head_size * 0.45, 0.0, accent))
        for raw in body_lines:
            text, hang = raw, 0.0
            if text[:2] in ('- ', '* ') or text[:1] == '\u2022':
                text = '\u2022  ' + text[2:].strip() if text[:2] in ('- ', '* ') else text
                hang = 9.0
            for ln in self._wrap(text, body_font, body_size, inner_w - hang):
                rows.append((ln, body_font, body_size, hang, C_BODY))

        heights = [max(sz * 1.45, 1.0) for (_t, _f, sz, _o, _c) in rows]
        top = self.current_y - mt
        if top - (heights[0] + pad * 2) < self._bottom_limit() and top < self._top_limit() - 20:
            self._fresh_page()
            top = self.current_y - mt

        idx = 0
        while idx < len(rows):
            room = top - self._bottom_limit()
            used, end = pad, idx
            while end < len(rows) and used + heights[end] + pad <= room:
                used += heights[end]
                end += 1
            if end == idx:
                end = idx + 1
            box_h = used + pad
            self._draw_callout_box(top, box_h, style, accent, radius, border_color,
                                   border_w, bg_alpha, icon, icon_size, pad, accent_w)
            y = top - pad
            for j in range(idx, end):
                text, font, sz, off, color = rows[j]
                if text:
                    c.setFont(font, sz)
                    c.setFillColor(color)
                    c.drawString(inner_x + off, y - sz, text)
                y -= heights[j]
            self.current_y = top - box_h - mb
            idx = end
            if idx < len(rows):
                self._fresh_page()
                top = self.current_y - mt

    def _draw_callout_box(self, top, height, style, accent, radius, border_color,
                          border_w, bg_alpha, icon, icon_size, pad, accent_w):
        """Draw the box chrome behind the callout content."""
        c = self.c
        lm = self._lm()
        w = self._tw()
        y0 = top - height
        c.saveState()
        c.setFillColor(accent)
        try:
            c.setFillAlpha(max(0.0, min(bg_alpha, 0.35)))
        except Exception:
            pass
        if style == 'rounded':
            c.roundRect(lm, y0, w, height, radius, fill=1, stroke=0)
        else:
            c.rect(lm, y0, w, height, fill=1, stroke=0)
        c.restoreState()

        if style in ('bordered', 'rounded'):
            c.setStrokeColor(border_color)
            c.setLineWidth(border_w)
            if style == 'rounded':
                c.roundRect(lm, y0, w, height, radius, fill=0, stroke=1)
            else:
                c.rect(lm, y0, w, height, fill=0, stroke=1)
        elif style == 'accent_left':
            c.setFillColor(accent)
            c.rect(lm, y0, accent_w, height, fill=1, stroke=0)
        elif style == 'accent_top':
            c.setFillColor(accent)
            c.rect(lm, top - accent_w, w, accent_w, fill=1, stroke=0)
        elif style == 'icon_callout':
            c.setFillColor(accent)
            c.rect(lm, y0, accent_w, height, fill=1, stroke=0)
        if icon:
            ornaments.draw(c, icon, lm + pad + icon_size / 2,
                           top - pad - icon_size * 0.55, icon_size, accent, 0.8)
