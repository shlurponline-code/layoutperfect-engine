"""Illustrated chapter books.

Lays out a parsed script (front matter, chapters of paragraphs / scene breaks /
art slots) as a print-ready interior: half title, frontispiece, title page,
copyright, dedication, contents, illustrated chapter openers, body text with
scene breaks, art slots, and the end matter (THE END, the next-book teaser and
the colophon).

Artwork is optional. A slot with no image yet prints a measured placeholder box
with its brief, so a proof can be reviewed before the illustrator delivers.
"""

import base64
import io
import os
import re
import tempfile
import urllib.request

from pypdf import PdfReader

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame,
                                PageBreak, PageTemplate, Paragraph, Spacer)

# --------------------------------------------------------------------- colours
C_BODY = HexColor('#1F1B16')
C_MUTED = HexColor('#6B6257')
C_RULE = HexColor('#C9BCA6')
C_BOX = HexColor('#F1ECE2')
C_BOX_LINE = HexColor('#BCAF98')
C_HEAD = HexColor('#9A9184')

# ----------------------------------------------------------------------- fonts
_FONT_DIR = '/usr/share/fonts/truetype/freefont'
_FONT_FILES = {'Gar': 'FreeSerif.ttf', 'GarB': 'FreeSerifBold.ttf',
               'GarI': 'FreeSerifItalic.ttf', 'GarBI': 'FreeSerifBoldItalic.ttf'}

for _name, _file in _FONT_FILES.items():
    try:
        pdfmetrics.registerFont(TTFont(_name, os.path.join(_FONT_DIR, _file)))
    except Exception:
        pass
try:
    pdfmetrics.registerFontFamily('Gar', normal='Gar', bold='GarB',
                                  italic='GarI', boldItalic='GarBI')
except Exception:
    pass

FONT, FONT_B, FONT_I = 'Gar', 'GarB', 'GarI'

# A picture's printed size is set by its placement alone, never by the space
# left on a page. The fractions are of the text block.
PLATE_KINDS = ('frontispiece', 'full')
ART_KINDS = ('frontispiece', 'full', 'half', 'spot')
HALF_MAX_HEIGHT = 0.55
SPOT_WIDTH = 0.60
PLACEHOLDER_ASPECT = 4.0 / 3.0
MIN_DPI = 300.0
REPORT_PLACEMENT = {'frontispiece': 'frontispiece', 'full': 'full_page',
                    'half': 'half_page', 'spot': 'spot'}


# --------------------------------------------------------------------- helpers
def _wrap(text, font, size, width):
    words = [w for w in str(text or '').split() if w]
    lines, line = [], ''
    for word in words:
        trial = (line + ' ' + word).strip()
        if not line or pdfmetrics.stringWidth(trial, font, size) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _centred_block(canvas, lines, font, size, leading, cx, top):
    canvas.setFont(font, size)
    y = top
    for line in lines:
        canvas.drawCentredString(cx, y, line)
        y -= leading
    return y


def _esc(text):
    return (str(text or '').replace('&', '&amp;')
            .replace('<', '&lt;').replace('>', '&gt;'))


def _md(raw):
    """Escape for ReportLab, then honour the manuscript's *italic* / **bold**."""
    text = _esc(raw).strip()
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
    return text


def _ornament(canvas, cx, y, width=86):
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.7)
    canvas.line(cx - width / 2.0, y, cx - 13, y)
    canvas.line(cx + 13, y, cx + width / 2.0, y)
    canvas.setFillColor(C_RULE)
    path = canvas.beginPath()
    path.moveTo(cx, y + 4.2)
    path.lineTo(cx + 4.2, y)
    path.lineTo(cx, y - 4.2)
    path.lineTo(cx - 4.2, y)
    path.close()
    canvas.drawPath(path, fill=1, stroke=0)


_IMAGE_CACHE = {}
_IMAGE_BYTES = {}
_PRINT_DPI = 300
_PRINT_CACHE = {}


def _image(url):
    if not url:
        return None
    if url in _IMAGE_CACHE:
        return _IMAGE_CACHE[url]
    reader = None
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'LayoutPerfect'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        _IMAGE_BYTES[url] = data
        reader = ImageReader(io.BytesIO(data))
    except Exception as error:
        print('[illustrated] artwork unavailable: ' + str(error))
    _IMAGE_CACHE[url] = reader
    return reader


def _print_image(url, printed_w, printed_h):
    """The picture at no more than 300 dpi for the size it prints at.

    Artwork is delivered far larger than print needs, and embedding it as sent
    makes a proof too heavy to store and to send to a printer.
    """
    reader = _image(url)
    if not reader:
        return None
    target_w = max(1, int(printed_w / inch * _PRINT_DPI))
    target_h = max(1, int(printed_h / inch * _PRINT_DPI))
    key = (url, target_w, target_h)
    if key in _PRINT_CACHE:
        return _PRINT_CACHE[key]
    try:
        raw = _IMAGE_BYTES.get(url)
        if not raw:
            return reader
        from PIL import Image as PILImage
        picture = PILImage.open(io.BytesIO(raw))
        picture.load()
        if picture.mode in ('RGBA', 'LA', 'P'):
            picture = picture.convert('RGBA')
            flat = PILImage.new('RGB', picture.size, (255, 255, 255))
            flat.paste(picture, mask=picture.split()[-1])
            picture = flat
        elif picture.mode != 'RGB':
            picture = picture.convert('RGB')
        if picture.width > target_w or picture.height > target_h:
            picture.thumbnail((target_w, target_h), PILImage.LANCZOS)
        buffer = io.BytesIO()
        picture.save(buffer, format='JPEG', quality=92, optimize=True)
        reader = ImageReader(io.BytesIO(buffer.getvalue()))
    except Exception as error:
        print('[illustrated] artwork resize failed: ' + str(error))
        reader = _image(url)
    _PRINT_CACHE[key] = reader
    return reader


# -------------------------------------------------------------------- flowables
class FrontPage(Flowable):
    """One hand-drawn page that fills the text block (front matter)."""

    def __init__(self, doc, painter, marks='front'):
        Flowable.__init__(self)
        self.doc = doc
        self.painter = painter
        self.marks = marks

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = avail_height - 2
        return self.width, self.height

    def draw(self):
        page = self.canv.getPageNumber()
        self.doc.page_marks[page] = self.marks
        self.painter(self.canv, self.width, self.height)


class Art(Flowable):
    """An illustration at the fixed printed size its placement sets.

    A picture is never shrunk to fit what is left of a page. When it does not
    fit, the text that follows fills the rest of this page and the picture is
    carried to the top of the next one.
    """

    def __init__(self, doc, slot, kind, description, url):
        Flowable.__init__(self)
        self.doc = doc
        self.slot = slot
        self.kind = kind if kind in ART_KINDS else 'half'
        self.description = description or ''
        self.url = url
        self.pixels = None
        self.dpi = 0.0
        self._measure()
        doc.arts.append(self)

    def _measure(self):
        image = _image(self.url)
        aspect = PLACEHOLDER_ASPECT
        if image:
            try:
                pixel_w, pixel_h = image.getSize()
                if pixel_w and pixel_h:
                    aspect = float(pixel_w) / float(pixel_h)
                    self.pixels = (int(pixel_w), int(pixel_h))
            except Exception:
                pass
        text_w, text_h = self.doc.width, self.doc.height
        if self.kind in PLATE_KINDS:
            box_w, box_h = text_w, text_h
        elif self.kind == 'spot':
            box_w = text_w * SPOT_WIDTH
            box_h = min(box_w / aspect, text_h)
        else:
            box_w = text_w
            box_h = min(text_w / aspect, text_h * HALF_MAX_HEIGHT)
        if self.pixels is None and self.kind in PLATE_KINDS:
            # no artwork yet: the plate proof shows the whole page it will fill
            printed_w, printed_h = box_w, box_h
        elif box_w / aspect <= box_h:
            printed_w, printed_h = box_w, box_w / aspect
        else:
            printed_w, printed_h = box_h * aspect, box_h
        self.printed_width = printed_w
        self.printed_height = printed_h
        self.width = text_w
        # a plate owns the page it sits on; everything else is exactly as tall
        # as the picture prints
        self.height = text_h if self.kind in PLATE_KINDS else printed_h
        if self.pixels and printed_w:
            self.dpi = self.pixels[0] / (printed_w / inch)

    def wrap(self, avail_width, avail_height):
        return self.width, self.height

    def draw(self):
        if self.kind in PLATE_KINDS:
            self.doc.page_marks[self.canv.getPageNumber()] = 'plate'
        self.paint(self.canv, self.width, self.height)

    def paint(self, canvas, box_w, box_h):
        image = _print_image(self.url, self.printed_width, self.printed_height)
        if image:
            try:
                left = (box_w - self.printed_width) / 2.0
                top = (box_h - self.printed_height) / 2.0
                canvas.drawImage(image, left, top, width=self.printed_width,
                                 height=self.printed_height, mask='auto')
                return
            except Exception as error:
                print('[illustrated] artwork failed to draw: ' + str(error))
        self._placeholder(canvas, box_w, box_h)

    def _placeholder(self, canvas, box_w, box_h):
        left = (box_w - self.printed_width) / 2.0
        top = (box_h - self.printed_height) / 2.0
        width, height = self.printed_width, self.printed_height
        canvas.saveState()
        canvas.setFillColor(C_BOX)
        canvas.setStrokeColor(C_BOX_LINE)
        canvas.setDash(3, 3)
        canvas.setLineWidth(0.8)
        canvas.roundRect(left, top, width, height, 6, stroke=1, fill=1)
        canvas.setDash()
        label = 'FULL-PAGE ILLUSTRATION' if self.kind in PLATE_KINDS else (self.kind.upper() + ' ILLUSTRATION')
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT, 7.6)
        canvas.drawCentredString(box_w / 2.0, top + height - 20, label)
        lines = _wrap(self.description, FONT_I, 8.6, max(60.0, width - 56))[:14]
        block_h = len(lines) * 11.4
        y = top + height / 2.0 + block_h / 2.0 - 6
        canvas.setFillColor(C_BODY)
        _centred_block(canvas, lines, FONT_I, 8.6, 11.4, box_w / 2.0, y)
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT, 7.4)
        canvas.drawCentredString(box_w / 2.0, top + 16, 'artwork to follow')
        canvas.restoreState()

class Opener(Flowable):
    """Chapter opener: label, ornament and chapter title, on a fresh page."""

    def __init__(self, doc, index, label, title):
        Flowable.__init__(self)
        self.doc = doc
        self.index = index
        self.label = label or 'CHAPTER'
        self.title = title or ''

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = 132
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        self.doc.page_marks[canvas.getPageNumber()] = 'opener'
        self.doc.chapter_pages[self.index] = canvas.getPageNumber()
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT, 9.2)
        canvas.drawCentredString(self.width / 2.0, 104, ' '.join(self.label.upper()))
        _ornament(canvas, self.width / 2.0, 84, 92)
        canvas.setFillColor(C_BODY)
        _centred_block(canvas, _wrap(self.title, FONT_B, 18, self.width - 12),
                       FONT_B, 18, 23, self.width / 2.0, 58)


class SceneBreak(Flowable):
    def __init__(self, doc):
        Flowable.__init__(self)
        self.doc = doc

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = 30
        return self.width, self.height

    def draw(self):
        self.doc.page_marks.setdefault(self.canv.getPageNumber(), 'body')
        _ornament(self.canv, self.width / 2.0, 14, 66)


class BlankPage(FrontPage):
    """A deliberately blank verso (no folio, no running head)."""

    def __init__(self, doc):
        FrontPage.__init__(self, doc, lambda canvas, width, height: None, 'front')


class Doc(BaseDocTemplate):
    def __init__(self, target, trim_width, trim_height, top, bottom, side):
        BaseDocTemplate.__init__(
            self, target, pagesize=(trim_width * inch, trim_height * inch),
            leftMargin=side, rightMargin=side,
            topMargin=top, bottomMargin=bottom,
            title='Layout Perfect illustrated book')
        self.page_marks = {}
        self.chapter_pages = {}
        self.book_title = ''
        self.arts = []
        self.held = []
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id='body',
                      leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id='page', frames=[frame],
                                            onPageEnd=_decorate)])

    def handle_flowable(self, flowables):
        page_before = self.page
        pending = flowables[0] if flowables else None
        if isinstance(pending, Art) and not self.frame._atTop:
            room = self.frame._y - self.frame._y1
            if pending.height > room + 0.5:
                # No room left: the picture keeps its printed size and the text
                # that follows it fills the rest of this page.
                flowables.pop(0)
                self.held.append(pending)
                return
        BaseDocTemplate.handle_flowable(self, flowables)
        if self.held and self.page != page_before:
            self._place_held(flowables, isinstance(pending, PageBreak))

    def _place_held(self, flowables, chapter_break):
        held = self.held
        self.held = []
        block = list(held)
        # text carries on under a picture, but a plate needs the page to itself
        if chapter_break or any(art.kind in PLATE_KINDS for art in held):
            block.append(PageBreak())
        flowables[0:0] = block


def _decorate(canvas, doc):
    page = doc.page
    marks = doc.page_marks.get(page, 'body')
    if marks in ('front', 'plate', 'blank'):
        return
    canvas.saveState()
    canvas.setFillColor(C_MUTED)
    canvas.setFont(FONT, 8.4)
    canvas.drawCentredString(doc.leftMargin + doc.width / 2.0,
                             doc.bottomMargin - 26, str(page))
    if marks == 'body' and doc.book_title:
        canvas.setFont(FONT, 7.6)
        canvas.setFillColor(C_HEAD)
        label = doc.book_title.upper()
        if page % 2 == 1:
            canvas.drawRightString(doc.leftMargin + doc.width,
                                   doc.bottomMargin + doc.height + 20, label)
        else:
            canvas.drawString(doc.leftMargin,
                              doc.bottomMargin + doc.height + 20, label)
    canvas.restoreState()


# ------------------------------------------------------------------- front pages
def _half_title(canvas, width, height, title, subtitle):
    canvas.setFillColor(C_BODY)
    y = _centred_block(canvas, _wrap(title.upper(), FONT, 21, width - 24),
                       FONT, 21, 26, width / 2.0, height * 0.62)
    if subtitle:
        canvas.setFillColor(C_BODY)
        _centred_block(canvas, _wrap(subtitle, FONT_I, 12.5, width - 40),
                       FONT_I, 12.5, 17, width / 2.0, y - 12)


def _title_page(canvas, width, height, payload):
    front = payload.get('front_matter') or {}
    series = front.get('series') or ''
    if series:
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT, 9.2)
        canvas.drawCentredString(width / 2.0, height - 24, ' '.join(series.upper()))
    canvas.setFillColor(C_BODY)
    y = _centred_block(canvas, _wrap(payload.get('title') or '', FONT_B, 25,
                                     width - 20),
                       FONT_B, 25, 30, width / 2.0, height * 0.62)
    subtitle = payload.get('subtitle') or ''
    if subtitle:
        y = _centred_block(canvas, _wrap(subtitle, FONT_I, 14, width - 30),
                           FONT_I, 14, 19, width / 2.0, y - 10)
    tagline = front.get('tagline') or ''
    if tagline:
        y = _centred_block(canvas, _wrap(tagline, FONT_I, 10.5, width - 40),
                           FONT_I, 10.5, 14, width / 2.0, y - 12)
    _ornament(canvas, width / 2.0, y - 16, 110)
    author = payload.get('author') or ''
    if author:
        canvas.setFillColor(C_BODY)
        _centred_block(canvas, _wrap(author, FONT, 13, width - 40), FONT, 13, 18,
                       width / 2.0, y - 52)
    illustrator = payload.get('illustrator') or ''
    if illustrator:
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT_I, 10.5)
        canvas.drawCentredString(width / 2.0, height * 0.30,
                                 'Illustrated by ' + illustrator)
    canvas.setFillColor(C_MUTED)
    canvas.setFont(FONT, 10)
    canvas.drawCentredString(width / 2.0, height * 0.16, payload.get('publisher') or '')


def _copyright(canvas, width, height, payload):
    front = payload.get('front_matter') or {}
    lines = []
    for entry in (front.get('copyright') or []):
        lines.extend(_wrap(entry, FONT, 8.4, width - 16))
    isbn = payload.get('isbn') or front.get('isbn') or ''
    if isbn:
        lines.append('')
        lines.append('ISBN ' + str(isbn))
    imprint = front.get('imprint_url') or ''
    if imprint:
        lines.append(imprint)
    canvas.setFillColor(C_MUTED)
    _centred_block(canvas, lines, FONT, 8.4, 12, width / 2.0, height * 0.44)


def _dedication(canvas, width, height, text):
    canvas.setFillColor(C_BODY)
    _centred_block(canvas, _wrap(text, FONT_I, 12, width - 70),
                   FONT_I, 12, 17, width / 2.0, height * 0.56)


def _contents(canvas, width, height, entries):
    canvas.setFillColor(C_BODY)
    canvas.setFont(FONT_B, 16)
    canvas.drawCentredString(width / 2.0, height - 30, 'Contents')
    _ornament(canvas, width / 2.0, height - 50, 90)
    y = height - 90
    for label, title, page in entries:
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT, 7.8)
        canvas.drawString(0, y, ' '.join(str(label).upper()))
        canvas.setFillColor(C_BODY)
        canvas.setFont(FONT, 11)
        canvas.drawString(0, y - 15, title)
        if page:
            canvas.setFillColor(C_MUTED)
            canvas.setFont(FONT, 9.4)
            canvas.drawRightString(width, y - 15, str(page))
        y -= 32
        if y < 20:
            break


# ------------------------------------------------------------------- assembly
def _story(doc, payload, toc_pages):
    payload = payload or {}
    front = payload.get('front_matter') or {}
    artwork = payload.get('artwork') or {}
    chapters = payload.get('chapters') or []
    doc.book_title = payload.get('title') or ''

    size = float(payload.get('body_size_pt') or 11.5)
    leading = float(payload.get('leading_pt') or 16.5)
    body = ParagraphStyle('body', fontName=FONT, fontSize=size, leading=leading,
                          textColor=C_BODY, alignment=0, spaceAfter=0)
    flush = body.clone('body-flush', firstLineIndent=0)
    indented = body.clone('body-indent', firstLineIndent=14)
    centred = ParagraphStyle('centred', parent=body, alignment=1)
    caps = ParagraphStyle('caps', parent=body, fontName=FONT, fontSize=9.4,
                          leading=14, alignment=1, textColor=C_MUTED)

    story = []
    story.append(FrontPage(doc, lambda c, w, h: _half_title(
        c, w, h, payload.get('title') or '', payload.get('subtitle') or '')))
    story.append(PageBreak())

    frontispiece = front.get('frontispiece') or {}
    if frontispiece.get('slot'):
        story.append(Art(doc, frontispiece.get('slot'), 'frontispiece',
                         frontispiece.get('description') or '',
                         artwork.get(frontispiece.get('slot')) or ''))
        story.append(PageBreak())

    story.append(FrontPage(doc, lambda c, w, h: _title_page(c, w, h, payload)))
    story.append(PageBreak())
    story.append(FrontPage(doc, lambda c, w, h: _copyright(c, w, h, payload)))
    story.append(PageBreak())
    if front.get('dedication'):
        story.append(FrontPage(doc, lambda c, w, h: _dedication(
            c, w, h, front.get('dedication') or '')))
        story.append(PageBreak())

    entries = [(chapter.get('label') or 'CHAPTER', chapter.get('title') or '',
                (toc_pages or {}).get(index))
               for index, chapter in enumerate(chapters)]
    story.append(FrontPage(doc, lambda c, w, h: _contents(c, w, h, entries)))

    for index, chapter in enumerate(chapters):
        story.append(PageBreak())
        story.append(Opener(doc, index, chapter.get('label') or 'CHAPTER',
                            chapter.get('title') or ''))
        paragraphs = 0
        for segment in (chapter.get('segments') or []):
            kind = segment.get('type')
            if kind == 'art':
                slot = segment.get('slot') or ''
                art_kind = segment.get('kind') or 'half'
                story.append(Art(doc, slot, art_kind,
                                 segment.get('description') or '',
                                 artwork.get(slot) or ''))
                story.append(Spacer(1, 10))
                paragraphs = 0
            elif kind == 'break':
                story.append(SceneBreak(doc))
                paragraphs = 0
            else:
                text = _md(segment.get('text') or '')
                if not text:
                    continue
                story.append(Paragraph(text, flush if paragraphs == 0 else indented))
                story.append(Spacer(1, 2))
                paragraphs += 1

    story.append(Spacer(1, 26))
    story.append(Paragraph(' '.join((front.get('end_text') or 'THE END').upper()), caps))

    following = front.get('next') or {}
    if following.get('title'):
        story.append(PageBreak())
        story.append(Spacer(1, doc.height * 0.22))
        story.append(Paragraph(' '.join((front.get('teaser_intro') or 'Will return in').upper()), caps))
        story.append(Spacer(1, 18))
        story.append(Paragraph(_esc(following.get('title')),
                               centred.clone('teaser-title', fontName=FONT_B,
                                             fontSize=17, leading=22)))
        if following.get('subtitle'):
            story.append(Spacer(1, 6))
            story.append(Paragraph(_esc(following.get('subtitle')),
                                   centred.clone('teaser-sub', fontName=FONT_I,
                                                 fontSize=13, leading=18)))
        story.append(Spacer(1, 20))
        for line in (following.get('lines') or []):
            story.append(Paragraph(_esc(line),
                                   centred.clone('teaser-line', fontSize=10.6,
                                                 leading=16)))
            story.append(Spacer(1, 7))

    story.append(PageBreak())
    story.append(Spacer(1, doc.height * 0.34))
    story.append(Paragraph(_esc(payload.get('publisher') or ''), caps))
    if front.get('imprint_url'):
        story.append(Spacer(1, 8))
        story.append(Paragraph(_esc(front.get('imprint_url')), caps))
    return story


def _render(payload, trim_width, trim_height, toc_pages):
    buffer = io.BytesIO()
    doc = Doc(buffer, trim_width, trim_height, 0.75 * inch, 0.72 * inch, 0.88 * inch)
    doc.build(_story(doc, payload, toc_pages))
    return buffer.getvalue(), dict(doc.chapter_pages), doc.page, doc


def _image_report(doc):
    """Every picture, its placement, printed width and printed resolution."""
    rows = []
    for art in doc.arts:
        row = {
            'slot': art.slot,
            'placement': REPORT_PLACEMENT.get(art.kind, art.kind),
            'width_inches': round(art.printed_width / inch, 2),
            'height_inches': round(art.printed_height / inch, 2),
            'pixels': ('%d x %d' % art.pixels) if art.pixels else '',
            'dpi': int(round(art.dpi)) if art.dpi else 0,
            'flags': [],
        }
        if not art.pixels:
            row['flags'].append('Artwork to follow: no image supplied yet.')
        else:
            if art.dpi and art.dpi < MIN_DPI:
                row['flags'].append('Below %d DPI at its printed size (%d DPI).'
                                    % (int(MIN_DPI), row['dpi']))
            if art.kind == 'half' and art.printed_width < art.doc.width - 0.5:
                row['flags'].append('Printed %.2f in wide, under the full text width its placement allows (%.2f in).'
                                    % (row['width_inches'], art.doc.width / inch))
            elif art.kind == 'spot':
                minimum = art.doc.width * SPOT_WIDTH
                if art.printed_width < minimum - 0.5:
                    row['flags'].append('Printed %.2f in wide, under the 60%% of the text width its placement allows (%.2f in).'
                                        % (row['width_inches'], minimum / inch))
        rows.append(row)
    return rows


def assemble_illustrated_book(payload):
    """Build twice: the second pass carries the contents page numbers."""
    payload = payload or {}
    trim_width = float(payload.get('trim_width') or 5.5)
    trim_height = float(payload.get('trim_height') or 8.5)
    _, chapter_pages, _, _ = _render(payload, trim_width, trim_height, {})
    pdf_bytes, _, page_count, doc = _render(payload, trim_width, trim_height, chapter_pages)

    # The final page: the ISBN barcode and the trade / buy-direct links, when the
    # project asks for them. Added after the interior so it lands on a recto.
    back_matter = payload.get('back_matter') or {}
    if back_matter.get('enabled'):
        try:
            from backmatter import append_back_matter
            cfg = dict(back_matter)
            if not cfg.get('isbn'):
                cfg['isbn'] = payload.get('isbn') or ''
            handle, temp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(handle)
            with open(temp_path, 'wb') as out:
                out.write(pdf_bytes)
            try:
                append_back_matter(temp_path, trim_width, trim_height, cfg,
                                   payload.get('language') or 'en_GB')
                with open(temp_path, 'rb') as back_in:
                    pdf_bytes = back_in.read()
                page_count = len(PdfReader(io.BytesIO(pdf_bytes)).pages)
            finally:
                os.remove(temp_path)
        except Exception as back_matter_error:
            print('Back-matter page skipped: ' + str(back_matter_error))

    spine = page_count * float(payload.get('spine_per_page') or 0.002252)
    words = sum(len((segment.get('text') or '').split())
                for chapter in (payload.get('chapters') or [])
                for segment in (chapter.get('segments') or []))
    filename = (payload.get('title') or 'illustrated-book').replace(' ', '_') + '.pdf'
    return {
        'success': True,
        'page_count': page_count,
        'spine_width_inches': round(spine, 4),
        'spine_width_mm': round(spine * 25.4, 1),
        'word_count': words,
        'filename': filename,
        'pdf_base64': base64.b64encode(pdf_bytes).decode('utf-8'),
        'image_report': _image_report(doc),
        'message': 'Illustrated interior built: %d pages at %s x %s inches'
                   % (page_count, trim_width, trim_height),
    }
