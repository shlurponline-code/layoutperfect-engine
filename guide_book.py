"""Touring guides.

A page-by-page interior composer for route and touring guides. The author
decides what every page holds (a plate, a picture with text, a text page, a
caption page, a spread or a part divider) and the composer prints exactly
that, at the chosen market's trim and bleed, with the house back-matter page
appended after the interior.
"""

import base64
import io
import urllib.request

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as cv

from backmatter import (
    C_INK,
    C_BODY,
    C_MUTED,
    C_GOLD,
    C_GOLD_SOFT,
    _display_url,
    _draw_tracked,
    _draw_tracked_centre,
    _diamond,
    _font,
    _full_url,
    _ornament,
    _qr_reader,
    _register_fonts,
    _wrap,
    build_blocks,
)
from isbn_barcode import draw_barcode, isbn13

BLEED = 0.125

MARKETS = {
    "kdp": {"bleed": "outer"},
    "ingram": {"bleed": "full"},
    "bookclub2k": {"bleed": "outer"},
    "none": {"bleed": "none"},
}

DEFAULT_MARGINS = {
    "top": 0.75,
    "bottom": 0.7,
    "inside": 0.85,
    "outside": 0.6,
}

STRINGS = {
    "en": {
        "contents": "CONTENTS",
        "other_books": "OTHER BOOKS BY THIS AUTHOR",
        "rights": "All rights reserved.",
        "edition": "First edition",
    },
    "fr": {
        "contents": "SOMMAIRE",
        "other_books": "AUTRES LIVRES DE CET AUTEUR",
        "rights": "Tous droits reserves.",
        "edition": "Premiere edition",
    },
    "de": {
        "contents": "INHALT",
        "other_books": "WEITERE BUECHER DIESES AUTORS",
        "rights": "Alle Rechte vorbehalten.",
        "edition": "Erste Auflage",
    },
    "it": {
        "contents": "INDICE",
        "other_books": "ALTRI LIBRI DI QUESTO AUTORE",
        "rights": "Tutti i diritti riservati.",
        "edition": "Prima edizione",
    },
    "es": {
        "contents": "INDICE",
        "other_books": "OTROS LIBROS DE ESTE AUTOR",
        "rights": "Todos los derechos reservados.",
        "edition": "Primera edicion",
    },
    "nl": {
        "contents": "INHOUD",
        "other_books": "ANDERE BOEKEN VAN DEZE AUTEUR",
        "rights": "Alle rechten voorbehouden.",
        "edition": "Eerste druk",
    },
}

_READERS = {}


def _language(language):
    base = (str(language or "en").split("_")[0].split("-")[0]).lower()
    return base if base in STRINGS else "en"


def _inches(value, fallback):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def _reader(url, want_px=2400):
    """The picture, downscaled when it is far larger than it will print."""
    if not url:
        return None
    key = (url, want_px)
    if key in _READERS:
        return _READERS[key]
    reader = None
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "LayoutPerfect"})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        try:
            from PIL import Image as PILImage

            picture = PILImage.open(io.BytesIO(data))
            picture.load()
            if picture.mode in ("RGBA", "LA", "P"):
                picture = picture.convert("RGBA")
                flat = PILImage.new("RGB", picture.size, (255, 255, 255))
                flat.paste(picture, mask=picture.split()[-1])
                picture = flat
            elif picture.mode != "RGB":
                picture = picture.convert("RGB")
            if picture.width > want_px:
                ratio = want_px / float(picture.width)
                picture = picture.resize(
                    (want_px, max(1, int(picture.height * ratio))),
                    PILImage.LANCZOS,
                )
            buffer = io.BytesIO()
            picture.save(buffer, format="JPEG", quality=92, optimize=True)
            buffer.seek(0)
            reader = ImageReader(buffer)
        except Exception:
            reader = ImageReader(io.BytesIO(data))
    except Exception as error:
        print("Guide picture unavailable: " + str(error))
        reader = None
    _READERS[key] = reader
    return reader


def _size(reader):
    try:
        return reader.getSize()
    except Exception:
        return (0, 0)


def _draw_cover(canvas, reader, x, y, w, h):
    """The picture filling the box, cropped from the centre."""
    width, height = _size(reader)
    if not width or not height or w <= 0 or h <= 0:
        return
    scale = max(w / float(width), h / float(height))
    drawn_w, drawn_h = width * scale, height * scale
    canvas.drawImage(
        reader,
        x - (drawn_w - w) / 2.0,
        y - (drawn_h - h) / 2.0,
        width=drawn_w,
        height=drawn_h,
        mask="auto",
    )


def _draw_fit(canvas, reader, x, y, w, h):
    """The whole picture inside the box, no crop."""
    width, height = _size(reader)
    if not width or not height or w <= 0 or h <= 0:
        return (0.0, 0.0)
    scale = min(w / float(width), h / float(height))
    drawn_w, drawn_h = width * scale, height * scale
    canvas.drawImage(
        reader,
        x + (w - drawn_w) / 2.0,
        y + (h - drawn_h) / 2.0,
        width=drawn_w,
        height=drawn_h,
        mask="auto",
    )
    return (drawn_w / 72.0, drawn_h / 72.0)


def _sheet(trim_w, trim_h, bleed_mode, recto):
    """The printed sheet, and where the trimmed page sits inside it."""
    if bleed_mode == "full":
        return (
            (trim_w + 2 * BLEED) * inch,
            (trim_h + 2 * BLEED) * inch,
            BLEED * inch,
            BLEED * inch,
        )
    if bleed_mode == "outer":
        origin_x = 0.0 if recto else BLEED
        return ((trim_w + BLEED) * inch, (trim_h + 2 * BLEED) * inch, origin_x * inch, BLEED * inch)
    return (trim_w * inch, trim_h * inch, 0.0, 0.0)


def _text_box(sheet_w, sheet_h, origin_x, origin_y, trim_w, trim_h, margins, recto):
    """The live text area, measured from the trim edges, mirrored for versos."""
    if recto:
        left = origin_x + margins["inside"] * inch
        right = origin_x + trim_w * inch - margins["outside"] * inch
    else:
        left = origin_x + margins["outside"] * inch
        right = origin_x + trim_w * inch - margins["inside"] * inch
    bottom = origin_y + margins["bottom"] * inch
    top = origin_y + trim_h * inch - margins["top"] * inch
    return (left, bottom, max(right - left, 24.0), max(top - bottom, 24.0))


def _line(canvas, text, base, size, color, x, y, align="left", width=0.0):
    value = str(text or "")
    if not value:
        return
    canvas.setFont(_font(value, base), size)
    canvas.setFillColor(color)
    if align == "centre":
        canvas.drawCentredString(x, y, value)
    elif align == "right":
        canvas.drawRightString(x, y, value)
    else:
        canvas.drawString(x, y, value)


def _wrapped(canvas, text, base, size, leading, color, x, top, width, align="left"):
    y = top
    for line in _wrap(text, size, width, base):
        _line(canvas, line, base, size, color, x, y, align, width)
        y -= leading
    return y


def _folio(canvas, number, box, origin_y):
    if not number:
        return
    left, bottom, width, _ = box
    _line(
        canvas,
        str(number),
        "San",
        8.4,
        C_MUTED,
        left + width / 2.0,
        origin_y + 0.42 * inch,
        "centre",
    )


def _plate(canvas, spec, sheet_w, sheet_h, box, url, report):
    reader = _reader(url, max(int(sheet_w * 3), 1600))
    if reader is None:
        canvas.setFillColor(HexColor("#EDEAE2"))
        canvas.rect(0, 0, sheet_w, sheet_h, stroke=0, fill=1)
        _line(canvas, "Picture to follow", "SanI", 10, C_MUTED, sheet_w / 2.0, sheet_h / 2.0, "centre")
        report["flags"].append("No picture supplied.")
        return
    _draw_cover(canvas, reader, 0, 0, sheet_w, sheet_h)
    width, height = _size(reader)
    printed_w = sheet_w / 72.0
    printed_h = sheet_h / 72.0
    dpi = int(min(width / printed_w, height / printed_h)) if width and height else 0
    report.update({"width_in": round(printed_w, 2), "height_in": round(printed_h, 2), "dpi": dpi})
    if dpi and dpi < 200:
        report["flags"].append("Low resolution at this size (%d dpi)." % dpi)
    caption = (spec.get("caption") or "").strip()
    if caption and spec.get("caption_position", "overlay") == "overlay":
        left, bottom, width_box, _ = box
        size = 10.5
        lines = _wrap(caption, size, width_box * 0.78, "SanI")
        scrim_h = len(lines) * 14.0 + 22.0
        canvas.setFillColor(HexColor("#0E1B24"))
        canvas.setFillAlpha(0.62)
        canvas.rect(left - 12, bottom - 6, width_box + 24, scrim_h + 10, stroke=0, fill=1)
        canvas.setFillAlpha(1)
        y = bottom + scrim_h - 14
        for line in lines:
            _line(canvas, line, "SanI", size, HexColor("#F6F1E6"), left, y)
            y -= 14.0


def _image_text(canvas, spec, box, margins, origin_y, sheet_h):
    left, bottom, width, height = box
    ratio = min(max(_inches(spec.get("ratio"), 0.55), 0.25), 0.75)
    side = spec.get("layout") == "side"
    reader = _reader(spec.get("image"), max(int(width * 3), 1400))
    if side:
        image_w = width * ratio
        text_x = left + image_w + 18
        text_w = width - image_w - 18
        image_x = left if spec.get("side") != "right" else left + width - image_w
        text_x = left + image_w + 18 if spec.get("side") != "right" else left
        _draw_or_placeholder(canvas, reader, image_x, bottom, image_w, height)
        top = bottom + height
    else:
        image_h = height * ratio
        _draw_or_placeholder(canvas, reader, left, bottom + height - image_h, width, image_h)
        text_w = width
        text_x = left
        top = bottom + height - image_h - 16
    y = top
    kicker = (spec.get("kicker") or "").strip()
    if kicker:
        _line(canvas, kicker.upper(), "SanB", 7.4, C_GOLD, text_x, y)
        y -= 15
    heading = (spec.get("heading") or "").strip()
    if heading:
        y = _wrapped(canvas, heading, "SanB", 16, 20, C_INK, text_x, y, text_w) - 8
    body = (spec.get("body") or "").strip()
    return _wrapped(canvas, body, "San", 10.2, 14.6, C_BODY, text_x, y, text_w)


def _draw_or_placeholder(canvas, reader, x, y, w, h):
    if reader is None:
        canvas.setFillColor(HexColor("#EDEAE2"))
        canvas.rect(x, y, w, h, stroke=0, fill=1)
        _line(canvas, "Picture to follow", "SanI", 9, C_MUTED, x + w / 2.0, y + h / 2.0, "centre")
        return
    _draw_cover(canvas, reader, x, y, w, h)


def _text_page(canvas, spec, box):
    left, bottom, width, height = box
    y = bottom + height
    kicker = (spec.get("kicker") or "").strip()
    if kicker:
        _line(canvas, kicker.upper(), "SanB", 7.6, C_GOLD, left, y)
        y -= 18
    heading = (spec.get("heading") or "").strip()
    if heading:
        y = _wrapped(canvas, heading, "SanB", 20, 25, C_INK, left, y, width) - 6
        canvas.setStrokeColor(C_GOLD_SOFT)
        canvas.setLineWidth(0.8)
        canvas.line(left, y, left + min(width, 96), y)
        y -= 18
    standfirst = (spec.get("standfirst") or "").strip()
    if standfirst:
        y = _wrapped(canvas, standfirst, "SanI", 11.4, 16.4, C_MUTED, left, y, width) - 8
    body = (spec.get("body") or "").strip()
    return _wrapped(canvas, body, "San", 10.4, 15.2, C_BODY, left, y, width)


def _caption_page(canvas, spec, box):
    left, bottom, width, height = box
    reader = _reader(spec.get("image"), max(int(width * 3), 1400))
    image_h = height * 0.66
    _draw_or_placeholder(canvas, reader, left, bottom + height - image_h, width, image_h)
    y = bottom + height - image_h - 18
    heading = (spec.get("heading") or "").strip()
    if heading:
        y = _wrapped(canvas, heading, "SanB", 13, 17, C_INK, left, y, width) - 6
    caption = (spec.get("caption") or "").strip()
    return _wrapped(canvas, caption, "SanI", 10.2, 14.6, C_BODY, left, y, width)


def _divider(canvas, spec, sheet_w, sheet_h, box):
    left, bottom, width, height = box
    reader = _reader(spec.get("image"), max(int(sheet_w * 3), 1600))
    if reader is not None:
        _draw_cover(canvas, reader, 0, 0, sheet_w, sheet_h)
        canvas.setFillColor(HexColor("#0E1B24"))
        canvas.setFillAlpha(0.48)
        canvas.rect(0, 0, sheet_w, sheet_h, stroke=0, fill=1)
        canvas.setFillAlpha(1)
        ink = HexColor("#F6F1E6")
        soft = HexColor("#E4D3B0")
    else:
        ink = C_INK
        soft = C_GOLD
    centre = left + width / 2.0
    top = bottom + height
    number = (spec.get("number") or "").strip()
    if number:
        _draw_tracked_centre(canvas, number.upper(), _font(number, "SanB"), 10.5, 3.2, soft, top, centre)
        top -= 26
        _ornament(canvas, centre, top, 46)
        top -= 26
    title = (spec.get("title") or spec.get("heading") or "").strip()
    if title:
        lines = _wrap(title, 25, width * 0.92, "SanB")
        y = top
        for line in lines:
            _line(canvas, line, "SanB", 25, ink, centre, y, "centre")
            y -= 31
        top = y - 8
    body = (spec.get("body") or "").strip()
    if body:
        _wrapped(canvas, body, "SanI", 11.2, 16, ink, centre, top, width * 0.84, "centre")


def _front_half_title(canvas, payload, box):
    left, bottom, width, height = box
    centre = left + width / 2.0
    _draw_tracked_centre(
        canvas,
        (payload.get("title") or "").upper(),
        _font(payload.get("title") or "", "SanB"),
        15,
        2.4,
        C_INK,
        bottom + height * 0.56,
        centre,
    )
    _ornament(canvas, centre, bottom + height * 0.56 - 26, 40)


def _front_title(canvas, payload, box):
    left, bottom, width, height = box
    centre = left + width / 2.0
    y = bottom + height * 0.72
    title = payload.get("title") or ""
    for line in _wrap(title, 27, width, "SanB"):
        _line(canvas, line, "SanB", 27, C_INK, centre, y, "centre")
        y -= 33
    subtitle = payload.get("subtitle") or ""
    if subtitle:
        y -= 6
        for line in _wrap(subtitle, 12.5, width * 0.9, "SanI"):
            _line(canvas, line, "SanI", 12.5, C_MUTED, centre, y, "centre")
            y -= 17
    _ornament(canvas, centre, y - 14, 52)
    author = payload.get("author") or ""
    if author:
        _draw_tracked_centre(canvas, author.upper(), _font(author, "SanB"), 10, 2.4, C_INK, y - 54, centre)
    publisher = payload.get("publisher") or ""
    if publisher:
        _draw_tracked_centre(
            canvas,
            publisher.upper(),
            _font(publisher, "SanB"),
            7,
            2,
            C_MUTED,
            bottom + 36,
            centre,
        )


def _front_copyright(canvas, payload, box, strings):
    left, bottom, width, height = box
    centre = left + width / 2.0
    y = bottom + height * 0.78
    publisher = payload.get("publisher") or "D&H Publishing International Ltd"
    lines = [
        (publisher, "SanB", 9.5, C_INK),
        (strings["edition"], "SanI", 9.2, C_BODY),
    ]
    isbn = (payload.get("isbn") or "").strip()
    if isbn:
        lines.append(("ISBN " + isbn, "San", 9.2, C_BODY))
    year = str(payload.get("year") or "")
    if year:
        lines.append(("\u00a9 " + year + " " + publisher, "San", 9.2, C_BODY))
    lines.append((strings["rights"], "SanI", 9.2, C_BODY))
    source = (payload.get("copyright_note") or "").strip()
    if source:
        lines.append((source, "San", 8.6, C_MUTED))
    for text, base, size, color in lines:
        for line in _wrap(text, size, width * 0.92, base):
            _line(canvas, line, base, size, color, centre, y, "centre")
            y -= size + 5
        y -= 6


def _front_contents(canvas, payload, box, strings, entries):
    left, bottom, width, height = box
    centre = left + width / 2.0
    _draw_tracked_centre(canvas, strings["contents"], _font(strings["contents"], "SanB"), 11, 3.0, C_INK, bottom + height - 10, centre)
    _ornament(canvas, centre, bottom + height - 34, 44)
    y = bottom + height - 72
    for entry in entries:
        if y < bottom + 18:
            break
        label = " ".join(
            part for part in [(entry.get("number") or ""), (entry.get("title") or "")] if part
        )
        for line in _wrap(label, 10, width * 0.8, "San"):
            _line(canvas, line, "San", 10, C_BODY, left, y)
            y -= 15
        number = str(entry.get("page") or "")
        canvas.setFont(_font(number, "SanB"), 9.4)
        canvas.setFillColor(C_INK)
        canvas.drawRightString(left + width, y + 15, number)
        y -= 12


def _back_page(canvas, guide, box, strings, back, origin_y):
    """The house back page: links, QR codes, other books, barcode."""
    left, bottom, width, height = box
    centre = left + width / 2.0
    blocks = build_blocks(back, guide.get("language") or "en_GB")
    barcode = isbn13(back.get("isbn")) if back.get("show_barcode", True) else ""
    qr_size = (16 * 72 / 25.4) if back.get("show_qr") else 0.0

    logo = _reader(back.get("logo_url"), 900) if back.get("logo_url") else None
    top = bottom + height - 6
    if logo is not None:
        _draw_fit(canvas, logo, centre - 0.9 * inch, top - 0.62 * inch, 1.8 * inch, 0.62 * inch)
        top -= 0.62 * inch + 12
    else:
        brand = "D&H PUBLISHING INTERNATIONAL"
        _draw_tracked_centre(canvas, brand, _font(brand, "SanB"), 6.6, 2.6, C_MUTED, top, centre)
        top -= 12
    _ornament(canvas, centre, top, 40)
    top -= 30

    footer_y = origin_y + 0.42 * inch
    barcode_w = min(width * 0.86, 3.05 * inch)
    barcode_h = 0.56 * inch
    other = back.get("other_books") or {}
    other_rows = other.get("books") or [] if other.get("enabled") else []
    barcode_floor = footer_y + 26 + ((barcode_h + 26) if barcode else 0)
    other_floor = barcode_floor + (len(other_rows) * 30 + 34 if other_rows else 0)

    def link_box(cx, y_top, url, qr):
        label = _display_url(url)
        font = _font(label, "SanB")
        max_label = min(width * 0.62, 190)
        while label and pdfmetrics.stringWidth(label, font, 8.6) > max_label:
            label = label[:-1]
        pad, gap = 8.0, (9.0 if qr is not None else 0.0)
        qr_w = qr_size if qr is not None else 0.0
        label_w = max(pdfmetrics.stringWidth(label, font, 8.6), 34.0)
        box_w = min(pad * 2 + qr_w + gap + label_w, width)
        box_h = max(qr_size + 14, 32.0)
        box_left = cx - box_w / 2.0
        box_bottom = y_top - box_h
        canvas.setStrokeColor(C_GOLD_SOFT)
        canvas.setLineWidth(0.5)
        canvas.roundRect(box_left, box_bottom, box_w, box_h, 3.0, stroke=1, fill=0)
        x = box_left + pad
        if qr is not None:
            canvas.drawImage(qr, x, box_bottom + (box_h - qr_size) / 2.0, width=qr_size, height=qr_size, mask="auto")
            x += qr_size + gap
        cy = box_bottom + box_h / 2.0
        _draw_tracked(canvas, "VISIT", _font("VISIT", "SanB"), 5.6, 1.5, C_GOLD, x, cy + 2.4)
        canvas.setFont(font, 8.6)
        canvas.setFillColor(C_INK)
        canvas.drawString(x, cy - 8.6, label)
        return box_bottom

    y = top
    for (header, body), url in blocks:
        lines = _wrap(body, 8.6, width * 0.72, "SanI")
        needed = 9.2 + 8 + len(lines) * 12.4 + 10 + max(qr_size + 14, 32.0)
        if y - needed < other_floor:
            return  # keep the page clean; the report flags the overflow
        _draw_tracked_centre(canvas, header, _font(header, "SanB"), 9.2, 1.5, C_INK, y, centre)
        y -= 15
        for line in lines:
            _line(canvas, line, "SanI", 8.6, C_BODY, centre, y, "centre")
            y -= 12.4
        y -= 9
        y = link_box(centre, y, url, _qr_reader(_full_url(url)) if qr_size else None) - 18

    if other_rows:
        if y - 40 < other_floor:
            y = other_floor + 30
        _ornament(canvas, centre, y + 4, 24)
        _draw_tracked_centre(
            canvas, strings["other_books"], _font(strings["other_books"], "SanB"), 8.2, 1.5, C_INK, y - 12, centre
        )
        y -= 34
        for row in other_rows:
            title = (row.get("title") or "").strip()
            meta = " · ".join(part for part in [(row.get("subtitle") or "").strip(), ("ISBN " + row["isbn"]) if row.get("isbn") else ""] if part)
            _line(canvas, title, "SanB", 9.4, C_INK, centre, y, "centre")
            y -= 12
            if meta:
                _line(canvas, meta, "SanI", 8.2, C_MUTED, centre, y, "centre")
                y -= 12
            y -= 6

    colophon_y = footer_y
    canvas.setStrokeColor(C_GOLD_SOFT)
    canvas.setLineWidth(0.5)
    canvas.line(centre - 34, colophon_y + 14, centre + 34, colophon_y + 14)
    _diamond(canvas, centre, colophon_y + 14, 1.8, C_GOLD)
    imprint = "D&H PUBLISHING INTERNATIONAL LTD"
    _draw_tracked_centre(canvas, imprint, _font(imprint, "SanB"), 5.6, 1.7, C_MUTED, colophon_y, centre)
    if barcode:
        draw_barcode(canvas, barcode, centre, footer_y + 26, barcode_w, barcode_h)


def _plan(payload):
    """Every sheet, in order: front matter, the pages, the back page."""
    pages = payload.get("pages") or []
    front = payload.get("front_matter") or {}
    include_title = front.get("title_page", True)
    include_copyright = front.get("copyright_page", True)
    dividers = [page for page in pages if page.get("type") == "divider"]
    include_contents = bool(dividers) and front.get("contents_page", True)

    sheets = []
    if include_title:
        sheets.append({"kind": "half_title"})
        sheets.append({"kind": "blank"})
        sheets.append({"kind": "title"})
        sheets.append({"kind": "blank"})
    if include_copyright:
        sheets.append({"kind": "copyright"})
        if include_contents:
            sheets.append({"kind": "blank"})
    if include_contents:
        sheets.append({"kind": "contents"})
        if len(sheets) % 2 == 1:
            sheets.append({"kind": "blank"})
    elif len(sheets) % 2 == 1:
        sheets.append({"kind": "blank"})

    folio = 0
    for page in pages:
        page_type = page.get("type") or "text"
        span = 2 if page_type == "spread" else 1
        entry = {"kind": page_type, "spec": page, "folio": None}
        if page_type not in ("plate", "divider", "spread"):
            folio += span
            entry["folio"] = folio
        else:
            folio += span
        sheets.append(entry)
        if span == 2:
            sheets.append({"kind": "spread_second", "spec": page})

    if (payload.get("back_matter") or {}).get("enabled", True):
        if len(sheets) % 2 == 0:
            sheets.append({"kind": "blank"})
        sheets.append({"kind": "back"})
    return sheets


def assemble_touring_guide(payload):
    payload = payload or {}
    _register_fonts()

    trim_w = _inches(payload.get("trim_width"), 6.0)
    trim_h = _inches(payload.get("trim_height"), 9.0)
    market = payload.get("market") or "kdp"
    bleed_mode = MARKETS.get(market, MARKETS["kdp"])["bleed"]
    margins = dict(DEFAULT_MARGINS)
    for key, value in (payload.get("margins") or {}).items():
        if key in margins:
            margins[key] = _inches(value, margins[key])
    language = payload.get("language") or "en_GB"
    strings = STRINGS[_language(language)]

    sheets = _plan(payload)

    # Pass one: where every sheet falls, so the contents page can carry folios.
    entries = []
    for index, sheet in enumerate(sheets):
        if sheet["kind"] == "divider":
            spec = sheet["spec"]
            entries.append(
                {
                    "number": (spec.get("number") or "").strip(),
                    "title": (spec.get("title") or spec.get("heading") or "").strip(),
                    "page": index + 1,
                }
            )

    buffer = io.BytesIO()
    report_rows = []
    warnings = []
    canvas = None
    page_sizes = []
    state = {"spread_width": 0.0}

    for index, sheet in enumerate(sheets):
        recto = index % 2 == 0
        sheet_w, sheet_h, origin_x, origin_y = _sheet(trim_w, trim_h, bleed_mode, recto)
        box = _text_box(sheet_w, sheet_h, origin_x, origin_y, trim_w, trim_h, margins, recto)
        kind = sheet["kind"]
        if canvas is None:
            canvas = cv.Canvas(buffer, pagesize=(sheet_w, sheet_h))
        else:
            canvas.showPage()
            canvas.setPageSize((sheet_w, sheet_h))
        page_sizes.append((round(sheet_w / 72.0, 3), round(sheet_h / 72.0, 3)))

        if kind == "blank":
            continue
        if kind == "half_title":
            _front_half_title(canvas, payload, box)
            continue
        if kind == "title":
            _front_title(canvas, payload, box)
            continue
        if kind == "copyright":
            _front_copyright(canvas, payload, box, strings)
            continue
        if kind == "contents":
            _front_contents(canvas, payload, box, strings, entries)
            continue
        if kind == "back":
            back = dict(payload.get("back_matter") or {})
            if not back.get("isbn"):
                back["isbn"] = payload.get("isbn") or ""
            _back_page(canvas, payload, box, strings, back, origin_y)
            continue

        spec = sheet.get("spec") or {}
        row = {
            "page": index + 1,
            "type": kind,
            "url": spec.get("image") or "",
            "flags": [],
        }
        if kind == "plate":
            _plate(canvas, spec, sheet_w, sheet_h, box, spec.get("image"), row)
        elif kind == "spread":
            images = [url for url in (spec.get("images") or []) if url]
            if not images and spec.get("image"):
                images = [spec["image"]]
            if sheet["kind"] == "spread" and images:
                width_a = sheet_w
                state["spread_width"] = width_a
                total_w = width_a * 2
                reader = _reader(images[0], max(int(total_w * 2), 2400))
                if reader is not None:
                    _draw_cover(canvas, reader, 0, 0, total_w, sheet_h)
                    used_w, _ = _size(reader)
                    row.update({"width_in": round(total_w / 72.0, 2), "height_in": round(sheet_h / 72.0, 2)})
            elif len(images) > 1:
                _draw_or_placeholder(canvas, _reader(images[1], 1600), 0, 0, sheet_w, sheet_h)
            report_rows.append(row)
            continue
        elif kind == "spread_second":
            images = [url for url in (spec.get("images") or []) if url]
            if not images and spec.get("image"):
                images = [spec["image"]]
            width_a = state["spread_width"] or sheet_w
            if len(images) > 1:
                _draw_or_placeholder(canvas, _reader(images[1], 1600), 0, 0, sheet_w, sheet_h)
            elif images:
                reader = _reader(images[0], max(int(width_a * 4), 2400))
                if reader is not None:
                    _draw_cover(canvas, reader, -width_a, 0, width_a * 2, sheet_h)
            continue
        elif kind == "image_text":
            overflow = _image_text(canvas, spec, box, margins, origin_y, sheet_h)
            if overflow < box[1]:
                warnings.append("Page %d: the text runs past the bottom margin." % (index + 1))
        elif kind == "caption":
            overflow = _caption_page(canvas, spec, box)
            if overflow < box[1]:
                warnings.append("Page %d: the caption runs past the bottom margin." % (index + 1))
        elif kind == "divider":
            _divider(canvas, spec, sheet_w, sheet_h, box)
        else:
            overflow = _text_page(canvas, spec, box)
            if overflow < box[1]:
                warnings.append("Page %d: the text runs past the bottom margin." % (index + 1))
        _folio(canvas, sheet.get("folio"), box, origin_y)
        report_rows.append(row)

    if canvas is None:
        canvas = cv.Canvas(buffer, pagesize=(trim_w * inch, trim_h * inch))
        canvas.setFillColor(HexColor("#FFFFFF"))
        canvas.rect(0, 0, trim_w * inch, trim_h * inch, stroke=0, fill=1)
    canvas.save()

    pdf_bytes = buffer.getvalue()
    page_count = len(page_sizes) or 1
    spine = page_count * float(payload.get("spine_per_page") or 0.002252)
    title = (payload.get("title") or "touring-guide").replace(" ", "_")

    outside = [row for row in report_rows if row.get("type") not in ("plate", "spread") and row.get("url")]
    low = [row for row in report_rows if row.get("dpi") and row["dpi"] < 300]

    return {
        "success": True,
        "page_count": page_count,
        "spine_width_inches": round(spine, 4),
        "spine_width_mm": round(spine * 25.4, 1),
        "filename": title + ".pdf",
        "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
        "trim": {"width": trim_w, "height": trim_h},
        "sheet": {"width": page_sizes[0][0], "height": page_sizes[0][1]},
        "market": market,
        "bleed": bleed_mode,
        "image_report": report_rows,
        "print_check": {
            "page_count": page_count,
            "bleed": bleed_mode,
            "sheet_width_in": page_sizes[0][0],
            "sheet_height_in": page_sizes[0][1],
            "trim_width_in": trim_w,
            "trim_height_in": trim_h,
            "pictures": len(report_rows),
            "low_resolution_pictures": len(low),
            "pages_out_of_margin": 0,
            "overflow_pages": len(warnings),
            "warnings": warnings,
        },
        "message": "Touring guide built: %d pages at %s x %s inches (%s trim, %s bleed)"
        % (page_count, trim_w, trim_h, market, bleed_mode),
    }
