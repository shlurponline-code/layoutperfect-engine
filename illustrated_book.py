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
import urllib.request

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

KIND_RATIO = {'frontispiece': 1.0, 'full': 0.94, 'half': 0.52, 'spot': 0.30}


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
        reader = ImageReader(io.BytesIO(data))
    except Exception as error:
        print('[illustrated] artwork unavailable: ' + str(error))
    _IMAGE_CACHE[url] = reader
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
    """An illustration, or a measured placeholder when the art is still to come."""

    def __init__(self, doc, slot, kind, description, url):
        Flowable.__init__(self)
        self.doc = doc
        self.slot = slot
        self.kind = kind if kind in KIND_RATIO else 'half'
        self.description = description or ''
        self.url = url

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = max(40.0, (avail_height - 2) * KIND_RATIO.get(self.kind, 0.5))
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        if self.kind in ('frontispiece', 'full'):
            self.doc.page_marks[canvas.getPageNumber()] = 'plate'
        image = _image(self.url)
        if image:
            try:
                img_w, img_h = image.getSize()
                scale = min(self.width / float(img_w), self.height / float(img_h))
                draw_w, draw_h = img_w * scale, img_h * scale
                canvas.drawImage(image, (self.width - draw_w) / 2.0,
                                 (self.height - draw_h) / 2.0,
                                 width=draw_w, height=draw_h, mask='auto')
                return
            except Exception as error:
                print('[illustrated] artwork failed to draw: ' + str(error))
        self._placeholder(canvas)

    def _placeholder(self, canvas):
        canvas.saveState()
        canvas.setFillColor(C_BOX)
        canvas.setStrokeColor(C_BOX_LINE)
        canvas.setDash(3, 3)
        canvas.setLineWidth(0.8)
        canvas.roundRect(0, 0, self.width, self.height, 6, stroke=1, fill=1)
        canvas.setDash()
        label = 'FULL-PAGE ILLUSTRATION' if self.kind == 'full' else (self.kind.upper() + ' ILLUSTRATION')
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT, 7.6)
        canvas.drawCentredString(self.width / 2.0, self.height - 20, label)
        lines = _wrap(self.description, FONT_I, 8.6, self.width - 56)[:14]
        block_h = len(lines) * 11.4
        top = self.height / 2.0 + block_h / 2.0 - 6
        canvas.setFillColor(C_BODY)
        _centred_block(canvas, lines, FONT_I, 8.6, 11.4, self.width / 2.0, top)
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FONT, 7.4)
        canvas.drawCentredString(self.width / 2.0, 16, 'artwork to follow')
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
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id='body',
                      leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id='page', frames=[frame],
                                            onPageEnd=_decorate)])


def _decorate(canvas, doc):
    page = doc.page
    marks = doc.page_marks.get(page, 'front')
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
                          textColor=C_BODY, alignment=4, spaceAfter=0)
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
    else:
        story.append(BlankPage(doc))
    story.append(PageBreak())

    story.append(FrontPage(doc, lambda c, w, h: _title_page(c, w, h, payload)))
    story.append(PageBreak())
    story.append(FrontPage(doc, lambda c, w, h: _copyright(c, w, h, payload)))
    story.append(PageBreak())
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
                if art_kind in ('full', 'frontispiece'):
                    story.append(CondPageBreak(doc.height * 0.9))
                story.append(Art(doc, slot, art_kind,
                                 segment.get('description') or '',
                                 artwork.get(slot) or ''))
                story.append(Spacer(1, 10))
                paragraphs = 0
            elif kind == 'break':
                story.append(SceneBreak(doc))
                paragraphs = 0
            else:
                text = _esc(segment.get('text') or '').strip()
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
    return buffer.getvalue(), dict(doc.chapter_pages), doc.page


def assemble_illustrated_book(payload):
    """Build twice: the second pass carries the contents page numbers."""
    payload = payload or {}
    trim_width = float(payload.get('trim_width') or 5.5)
    trim_height = float(payload.get('trim_height') or 8.5)
    _, chapter_pages, _ = _render(payload, trim_width, trim_height, {})
    pdf_bytes, _, page_count = _render(payload, trim_width, trim_height, chapter_pages)
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
        'message': 'Illustrated interior built: %d pages at %s x %s inches'
                   % (page_count, trim_width, trim_height),
    }
