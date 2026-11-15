"""Partner page for Layout Perfect interiors.

One printed page carrying a partner's own message - a gift plate at the front
("with the compliments of...") or a promotional page after the back matter.
Drawn as a separate single-page PDF and merged into the interior, so it works
with every template and trim size.
"""

import io
import re
import urllib.request

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as cv
from pypdf import PdfReader, PdfWriter

from backmatter import (
    _display_url,
    _draw_tracked,
    _draw_tracked_centre,
    _font,
    _full_url,
    _qr_reader,
    _wrap,
)

FONT_DIR = "/usr/share/fonts/truetype/freefont"

C_INK = HexColor("#1B1B1B")
C_BODY = HexColor("#4A4A4A")
C_MUTED = HexColor("#8C8676")
C_CREAM = HexColor("#FAF6EC")
C_PAPER = HexColor("#FFFDF8")
C_RULE = HexColor("#D8CDB2")
C_FAINT = HexColor("#A29A86")


def _register_serifs():
    for name, filename in (
        ("Gar", "FreeSerif.ttf"),
        ("GarB", "FreeSerifBold.ttf"),
        ("GarI", "FreeSerifItalic.ttf"),
        ("GarBI", "FreeSerifBoldItalic.ttf"),
    ):
        try:
            pdfmetrics.registerFont(TTFont(name, FONT_DIR + "/" + filename))
        except Exception:
            pass


def _serif(text, base="Gar"):
    try:
        return _font(text or " ", base)
    except Exception:
        return _font(text or " ", "San")


def _safe_colour(value, fallback="#1B4F72"):
    text = str(value or "").strip()
    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", text):
        text = fallback
    if not text.startswith("#"):
        text = "#" + text
    return HexColor(text)


def _shade(colour, factor):
    if factor <= 1:
        return Color(colour.red * factor, colour.green * factor, colour.blue * factor)
    step = min(factor - 1.0, 1.0)
    return Color(
        colour.red + (1 - colour.red) * step,
        colour.green + (1 - colour.green) * step,
        colour.blue + (1 - colour.blue) * step,
    )


def _mix(first, second, amount):
    return Color(
        first.red + (second.red - first.red) * amount,
        first.green + (second.green - first.green) * amount,
        first.blue + (second.blue - first.blue) * amount,
    )


def _luminance(colour):
    return 0.299 * colour.red + 0.587 * colour.green + 0.114 * colour.blue


def _on_colour(colour):
    return HexColor("#FFFFFF") if _luminance(colour) < 0.6 else HexColor("#1B1B1B")


def _fetch_image(url):
    text = str(url or "").strip()
    if not text.lower().startswith("http"):
        return None
    try:
        request = urllib.request.Request(
            text, headers={"User-Agent": "LayoutPerfect/1.0"}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()
        return ImageReader(io.BytesIO(data)) if data else None
    except Exception as error:
        print("Partner page image skipped: " + str(error))
        return None


def _cover_image(c, reader, x, y, width, height):
    try:
        image_w, image_h = reader.getSize()
    except Exception:
        return False
    if not image_w or not image_h:
        return False
    scale = max(width / float(image_w), height / float(image_h))
    drawn_w, drawn_h = image_w * scale, image_h * scale
    c.saveState()
    clip = c.beginPath()
    clip.rect(x, y, width, height)
    c.clipPath(clip, stroke=0, fill=0)
    c.drawImage(
        reader,
        x + (width - drawn_w) / 2.0,
        y + (height - drawn_h) / 2.0,
        width=drawn_w,
        height=drawn_h,
        mask="auto",
    )
    c.restoreState()
    return True


def _contain_image(c, reader, x, y, width, height, align="left"):
    try:
        image_w, image_h = reader.getSize()
    except Exception:
        return False
    if not image_w or not image_h:
        return False
    scale = min(width / float(image_w), height / float(image_h))
    drawn_w, drawn_h = image_w * scale, image_h * scale
    left = x + (width - drawn_w) / 2.0 if align == "centre" else x
    c.drawImage(
        reader, left, y + (height - drawn_h) / 2.0, width=drawn_w, height=drawn_h,
        mask="auto",
    )
    return True


def _fit(text, font, sizes, width, max_lines):
    for size in sizes:
        lines = _wrap(text, size, width, font)
        if len(lines) <= max_lines:
            return size, lines
    last = sizes[-1]
    return last, _wrap(text, last, width, font)[:max_lines]


def _cta_block(c, cfg, page_w, margin, baseline, ink, muted, centre=True):
    """The link, with its printed QR, at the foot of the page."""
    label = str(cfg.get("cta_label") or "").strip()
    url = _display_url(cfg.get("cta_url") or "")
    qr = None
    if cfg.get("show_qr", True) and str(cfg.get("cta_url") or "").strip():
        qr = _qr_reader(_full_url(cfg.get("cta_url")))
    qr_size = 34.0 if qr is not None else 0.0
    gap = 13.0 if qr is not None else 0.0
    label_font = _serif(label or url, "GarB")
    label_size = 8.8
    url_font = _font(url or " ", "Gar")
    url_size = 7.6
    label_w = pdfmetrics.stringWidth(label, label_font, label_size) if label else 0.0
    url_w = pdfmetrics.stringWidth(url, url_font, url_size) if url else 0.0
    text_w = max(label_w, url_w)
    total = qr_size + gap + text_w
    x = (page_w - total) / 2.0 if centre else margin
    if qr is not None:
        qr_x = x if centre else page_w - margin - qr_size
        c.drawImage(qr, qr_x, baseline, width=qr_size, height=qr_size, mask="auto")
        if centre:
            x += qr_size + gap
    label_y = baseline + (qr_size * 0.46 if qr is not None else 11.0)
    url_y = baseline + (qr_size * 0.10 if qr is not None else 0.0)
    if label:
        c.setFont(label_font, label_size)
        c.setFillColor(ink)
        c.drawString(x, label_y, label)
    if url:
        c.setFont(url_font, url_size)
        c.setFillColor(muted)
        c.drawString(x, url_y, url)


def _disclosure(c, text, page_w, bottom, colour):
    lines = _wrap(str(text or ""), 5.4, page_w * 0.78, "San")
    y = bottom
    for line in lines[:2]:
        c.setFont(_font(line, "San"), 5.4)
        c.setFillColor(colour)
        c.drawCentredString(page_w / 2.0, y, line)
        y -= 6.8


def _render_gift(c, page_w, page_h, cfg, accent, logo, image):
    margin = min(0.9 * inch, page_w * 0.13)
    inner = page_w - 2 * margin
    c.setFillColor(C_CREAM)
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    image_h = page_h * 0.36
    photo = image is not None and _cover_image(
        c, image, 0, page_h - image_h, page_w, image_h
    )
    if photo:
        c.setFillColor(accent)
        c.rect(0, page_h - image_h - 3, page_w, 3, stroke=0, fill=1)
        y = page_h - image_h - 42
    else:
        y = page_h - margin - 44

    kicker = str(cfg.get("kicker") or "WITH THE COMPLIMENTS OF").strip().upper()
    _draw_tracked_centre(
        c, kicker, _serif(kicker, "SanB"), 6.6, 2.2, accent, y, page_w / 2.0
    )
    y -= 34

    name = str(cfg.get("partner_name") or "").strip()
    logo_drawn = False
    if logo is not None:
        logo_h = min(0.68 * inch, page_h * 0.085)
        logo_w = min(inner * 0.68, logo_h * 3.6)
        logo_drawn = _contain_image(
            c, logo, (page_w - logo_w) / 2.0, y - logo_h, logo_w, logo_h, "centre"
        )
    if not logo_drawn and name:
        font = _serif(name, "GarB")
        size = 15.0
        while size > 8 and pdfmetrics.stringWidth(name, font, size) > inner:
            size -= 0.5
        c.setFont(font, size)
        c.setFillColor(C_INK)
        c.drawCentredString(page_w / 2.0, y - size, name)
    y -= max(0.88 * inch, page_h * 0.105)

    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.6)
    c.line(page_w / 2.0 - 22, y, page_w / 2.0 + 22, y)
    y -= 30

    headline = str(cfg.get("headline") or "").strip()
    if headline:
        size, lines = _fit(headline, "GarB", [18.0, 17.0, 16.0, 15.0, 14.0], inner, 2)
        c.setFillColor(C_INK)
        for line in lines:
            c.setFont(_serif(line, "GarB"), size)
            c.drawCentredString(page_w / 2.0, y, line)
            y -= size * 1.3
        y -= 8

    body = str(cfg.get("body") or "").strip()
    if body:
        size, lines = _fit(body, "GarI", [9.4, 9.0, 8.6], inner * 0.94, 5)
        c.setFillColor(C_BODY)
        for line in lines:
            c.setFont(_serif(line, "GarI"), size)
            c.drawCentredString(page_w / 2.0, y, line)
            y -= size * 1.62
        y -= 12

    highlights = [
        str(line).strip() for line in (cfg.get("highlights") or []) if str(line).strip()
    ][:3]
    for line in highlights:
        text = line.upper()
        font = _serif(text, "SanB")
        size = 5.6
        while size > 4.4 and pdfmetrics.stringWidth(text, font, size) > inner * 0.9:
            size -= 0.3
        _draw_tracked_centre(c, text, font, size, 1.7, C_MUTED, y, page_w / 2.0)
        y -= 13

    cta_base = margin * 1.9
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.5)
    c.line(margin, cta_base + 48, page_w - margin, cta_base + 48)
    _cta_block(c, cfg, page_w, margin, cta_base, C_INK, C_MUTED, centre=True)
    _disclosure(c, cfg.get("disclosure"), page_w, margin * 0.55, C_FAINT)


def _render_feature(c, page_w, page_h, cfg, accent, logo, image):
    margin = min(0.85 * inch, page_w * 0.12)
    inner = page_w - 2 * margin
    c.setFillColor(C_PAPER)
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    image_h = page_h * 0.42
    if image is not None:
        _cover_image(c, image, 0, page_h - image_h, page_w, image_h)
    else:
        c.setFillColor(_shade(accent, 1.82))
        c.rect(0, page_h - image_h, page_w, image_h, stroke=0, fill=1)
    c.setFillColor(accent)
    c.rect(0, page_h - image_h - 5, page_w, 5, stroke=0, fill=1)

    y = page_h - image_h - 34
    kicker = str(cfg.get("kicker") or "WITH THE COMPLIMENTS OF").strip().upper()
    _draw_tracked(c, kicker, _serif(kicker, "SanB"), 6.4, 2.0, accent, margin, y)

    logo_h = min(0.5 * inch, page_h * 0.06)
    logo_drawn = False
    if logo is not None:
        logo_w = min(inner * 0.34, logo_h * 3.4)
        logo_drawn = _contain_image(
            c, logo, page_w - margin - logo_w, y - logo_h + 8, logo_w, logo_h, "left"
        )
    if not logo_drawn:
        name = str(cfg.get("partner_name") or "").strip().upper()
        if name:
            font = _serif(name, "SanB")
            size = 6.2
            while size > 4.6 and pdfmetrics.stringWidth(name, font, size) > inner * 0.5:
                size -= 0.2
            width = pdfmetrics.stringWidth(name, font, size) + 1.6 * (len(name) - 1)
            _draw_tracked(
                c, name, font, size, 1.6, C_MUTED, page_w - margin - width, y
            )
    y -= 32

    headline = str(cfg.get("headline") or "").strip()
    if headline:
        size, lines = _fit(headline, "GarB", [21.0, 20.0, 18.0, 17.0, 15.0], inner, 2)
        c.setFillColor(C_INK)
        for line in lines:
            c.setFont(_serif(line, "GarB"), size)
            c.drawString(margin, y, line)
            y -= size * 1.24
        y -= 10

    body = str(cfg.get("body") or "").strip()
    if body:
        size, lines = _fit(body, "GarI", [9.6, 9.2, 8.8], inner, 5)
        c.setFillColor(C_BODY)
        for line in lines:
            c.setFont(_serif(line, "GarI"), size)
            c.drawString(margin, y, line)
            y -= size * 1.62
        y -= 14

    highlights = [
        str(line).strip() for line in (cfg.get("highlights") or []) if str(line).strip()
    ][:3]
    for line in highlights:
        c.setFillColor(accent)
        c.rect(margin, y + 2.4, 3.4, 3.4, stroke=0, fill=1)
        c.setFillColor(C_INK)
        font = _serif(line, "Gar")
        size = 8.6
        while size > 6.4 and pdfmetrics.stringWidth(line, font, size) > inner - 12:
            size -= 0.2
        c.setFont(font, size)
        c.drawString(margin + 11, y, line)
        y -= size * 1.7

    cta_base = margin * 1.95
    _cta_block(c, cfg, page_w, margin, cta_base, C_INK, accent, centre=False)
    _disclosure(c, cfg.get("disclosure"), page_w, margin * 0.55, C_FAINT)


def _render_offer(c, page_w, page_h, cfg, accent, logo, image):
    margin = min(0.85 * inch, page_w * 0.12)
    inner = page_w - 2 * margin
    ink = _on_colour(accent)
    soft = _mix(ink, accent, 0.22)
    c.setFillColor(accent)
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    y = page_h - margin - 8
    if image is not None:
        band_h = page_h * 0.3
        _cover_image(c, image, 0, page_h - band_h, page_w, band_h)
        y = page_h - band_h - 34

    logo_h = min(0.58 * inch, page_h * 0.065)
    logo_drawn = False
    if logo is not None:
        logo_w = min(inner * 0.5, logo_h * 3.6)
        logo_drawn = _contain_image(
            c, logo, margin, y - logo_h, logo_w, logo_h, "left"
        )
    if not logo_drawn:
        name = str(cfg.get("partner_name") or "").strip().upper()
        if name:
            font = _serif(name, "SanB")
            size = 6.8
            while size > 4.8 and pdfmetrics.stringWidth(name, font, size) > inner * 0.6:
                size -= 0.2
            _draw_tracked(c, name, font, size, 2.2, ink, margin, y)
    y -= max(0.62 * inch, page_h * 0.07)

    headline = str(cfg.get("headline") or "").strip()
    if headline:
        size, lines = _fit(headline, "GarB", [23.0, 21.0, 19.0, 17.0], inner, 3)
        c.setFillColor(ink)
        for line in lines:
            c.setFont(_serif(line, "GarB"), size)
            c.drawString(margin, y, line)
            y -= size * 1.2
        y -= 12

    body = str(cfg.get("body") or "").strip()
    if body:
        size, lines = _fit(body, "GarI", [9.8, 9.4, 9.0], inner, 5)
        c.setFillColor(soft)
        for line in lines:
            c.setFont(_serif(line, "GarI"), size)
            c.drawString(margin, y, line)
            y -= size * 1.6
        y -= 18

    code = str(cfg.get("offer_code") or "").strip()
    if code:
        box_h = 54.0
        c.saveState()
        c.setStrokeColor(_mix(ink, accent, 0.35))
        c.setLineWidth(0.7)
        c.setDash(3, 2.4)
        c.roundRect(margin, y - box_h + 12, inner, box_h, 3.0, stroke=1, fill=0)
        c.restoreState()
        label = "QUOTE THIS CODE"
        _draw_tracked_centre(
            c, label, _serif(label, "SanB"), 5.4, 2.6, soft,
            y - 6, page_w / 2.0,
        )
        font = _serif(code, "GarB")
        size = 15.0
        while size > 9 and pdfmetrics.stringWidth(code, font, size) > inner * 0.8:
            size -= 0.5
        c.setFont(font, size)
        c.setFillColor(ink)
        c.drawCentredString(page_w / 2.0, y - 6 - size - 8, code)
        y -= box_h + 26

    cta_base = margin * 1.95
    _cta_block(c, cfg, page_w, margin, cta_base, ink, soft, centre=False)
    _disclosure(c, cfg.get("disclosure"), page_w, margin * 0.55, soft)


def _page_pdf(pdf_path, page_w, page_h, cfg):
    side_path = pdf_path.replace(".pdf", "_partner.pdf")
    c = cv.Canvas(side_path, pagesize=(page_w, page_h))
    layout = str(cfg.get("layout") or "gift").strip().lower()
    accent = _safe_colour(cfg.get("accent"))
    logo = _fetch_image(cfg.get("logo_url"))
    image = _fetch_image(cfg.get("image_url"))
    if layout == "offer":
        _render_offer(c, page_w, page_h, cfg, accent, logo, image)
    elif layout == "feature":
        _render_feature(c, page_w, page_h, cfg, accent, logo, image)
    else:
        _render_gift(c, page_w, page_h, cfg, accent, logo, image)
    c.showPage()
    c.save()
    return side_path


def apply_partner_page(pdf_path, trim_width, trim_height, cfg=None, language="en_GB"):
    """Merge the partner page: a gift plate at the front, or a promo at the back."""
    cfg = cfg or {}
    if not cfg.get("enabled"):
        return None
    _register_serifs()

    page_w = float(trim_width) * inch
    page_h = float(trim_height) * inch
    side_path = _page_pdf(pdf_path, page_w, page_h, cfg)
    placement = str(cfg.get("placement") or "front").strip().lower()

    if placement == "back":
        writer = PdfWriter(clone_from=PdfReader(pdf_path))
        if len(writer.pages) % 2 == 1:
            writer.add_blank_page(width=page_w, height=page_h)
        writer.append(PdfReader(side_path))
    else:
        # Front: the partner page, a blank verso, then the book. Two extra
        # pages keep the original recto/verso parity, so no folio changes side.
        writer = PdfWriter()
        writer.append(PdfReader(side_path))
        writer.add_blank_page(width=page_w, height=page_h)
        writer.append(PdfReader(pdf_path))

    with open(pdf_path, "wb") as handle:
        writer.write(handle)
    return side_path
