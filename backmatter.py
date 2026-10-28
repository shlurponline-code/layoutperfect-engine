"""Back-matter links page for Layout Perfect interiors.

Renders the D&H back-matter blocks (trade and wholesale enquiries, the
AuthorCentral book page, the BookClub2K purchase link and the full catalogue)
as a single centred links page, with a framed URL panel and QR code for each
block. The page is appended after the interior is built, so it works for every
template and trim size.
"""

import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as cv
from pypdf import PdfReader, PdfWriter

FONT_DIR = "/usr/share/fonts/truetype/freefont"

C_INK = HexColor("#1F2A38")
C_BODY = HexColor("#4A4A4A")
C_MUTED = HexColor("#8A8578")
C_GOLD = HexColor("#B08D57")
C_GOLD_SOFT = HexColor("#D8CBB2")

STRINGS = {
    "en": {
        "trade": ("TRADE & WHOLESALE ENQUIRIES", "For bulk orders, retail stocking and distribution:"),
        "authorcentral": ("ABOUT THIS BOOK", "Discover more about this book and the author:"),
        "bookclub": ("BUY DIRECT", "Buy direct from the publisher:"),
        "catalogue": ("OUR CATALOGUE", "Browse our full catalogue:"),
    },
    "fr": {
        "trade": ("COMMANDES EN GROS ET DISTRIBUTION", "Pour les commandes en volume, la mise en rayon et la distribution :"),
        "authorcentral": ("A PROPOS DE CE LIVRE", "Decouvrez ce livre et son auteur :"),
        "bookclub": ("ACHAT DIRECT", "Achetez directement chez l'editeur :"),
        "catalogue": ("NOTRE CATALOGUE", "Parcourez notre catalogue complet :"),
    },
    "de": {
        "trade": ("HANDEL UND GROSSHANDEL", "Fuer Grossbestellungen, Einzelhandel und Vertrieb:"),
        "authorcentral": ("UEBER DIESES BUCH", "Mehr ueber dieses Buch und den Autor:"),
        "bookclub": ("DIREKT KAUFEN", "Direkt beim Verlag kaufen:"),
        "catalogue": ("UNSER KATALOG", "Unseren vollstaendigen Katalog ansehen:"),
    },
    "it": {
        "trade": ("ORDINI ALL'INGROSSO E DISTRIBUZIONE", "Per ordini in volume, distribuzione e vendita al dettaglio:"),
        "authorcentral": ("SU QUESTO LIBRO", "Scopri di piu su questo libro e sull'autore:"),
        "bookclub": ("ACQUISTO DIRETTO", "Acquista direttamente dall'editore:"),
        "catalogue": ("IL NOSTRO CATALOGO", "Sfoglia il nostro catalogo completo:"),
    },
    "es": {
        "trade": ("PEDIDOS AL POR MAYOR Y DISTRIBUCION", "Para pedidos en volumen, distribucion y venta al por menor:"),
        "authorcentral": ("SOBRE ESTE LIBRO", "Descubre mas sobre este libro y el autor:"),
        "bookclub": ("COMPRA DIRECTA", "Compra directamente al editor:"),
        "catalogue": ("NUESTRO CATALOGO", "Consulta nuestro catalogo completo:"),
    },
    "nl": {
        "trade": ("HANDEL EN GROOTHANDEL", "Voor bulkbestellingen, detailhandel en distributie:"),
        "authorcentral": ("OVER DIT BOEK", "Ontdek meer over dit boek en de auteur:"),
        "bookclub": ("DIRECT KOPEN", "Koop rechtstreeks bij de uitgever:"),
        "catalogue": ("ONZE CATALOGUS", "Bekijk onze volledige catalogus:"),
    },
    "ja": {
        "trade": ("\u5378\u58f2\u30fb\u53d6\u5f15\u306e\u304a\u554f\u3044\u5408\u308f\u305b", "\u5927\u91cf\u6ce8\u6587\u3001\u5c0f\u58f2\u8ca9\u58f2\u3001\u6d41\u901a\u306b\u3064\u3044\u3066\uff1a"),
        "authorcentral": ("\u3053\u306e\u672c\u306b\u3064\u3044\u3066", "\u3053\u306e\u672c\u3068\u8457\u8005\u306b\u3064\u3044\u3066\u8a73\u3057\u304f\u306f\uff1a"),
        "bookclub": ("\u76f4\u63a5\u8cfc\u5165", "\u51fa\u7248\u793e\u304b\u3089\u76f4\u63a5\u8cfc\u5165\uff1a"),
        "catalogue": ("\u30ab\u30bf\u30ed\u30b0", "\u5168\u30ab\u30bf\u30ed\u30b0\u3092\u898b\u308b\uff1a"),
    },
}


def _language(language):
    base = (language or "en").split("_")[0].split("-")[0].lower()
    return base if base in STRINGS else "en"


def _register_fonts():
    for name, filename in (
        ("San", "FreeSans.ttf"),
        ("SanB", "FreeSansBold.ttf"),
        ("SanI", "FreeSansOblique.ttf"),
    ):
        try:
            pdfmetrics.registerFont(TTFont(name, FONT_DIR + "/" + filename))
        except Exception:
            pass


def _font(text, base):
    try:
        from typeset_engine import cjk_aware_font
        return cjk_aware_font(text, base)
    except Exception:
        return base


def _display_url(url):
    text = (url or "").strip()
    lowered = text.lower()
    if lowered.startswith("https://"):
        text = text[8:]
    elif lowered.startswith("http://"):
        text = text[7:]
    return text.rstrip("/")


def _full_url(url):
    text = (url or "").strip()
    if not text:
        return ""
    if text.lower().startswith("http"):
        return text
    return "https://" + text


def _wrap(text, size, max_width, base="San"):
    text = (text or "").strip()
    if not text:
        return []
    lines = []
    current = ""
    for word in text.split():
        candidate = (current + " " + word).strip()
        if pdfmetrics.stringWidth(candidate, _font(candidate, base), size) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = ""
        if pdfmetrics.stringWidth(word, _font(word, base), size) <= max_width:
            current = word
            continue
        for character in word:
            attempt = current + character
            if pdfmetrics.stringWidth(attempt, _font(attempt, base), size) <= max_width:
                current = attempt
            else:
                if current:
                    lines.append(current)
                current = character
    if current:
        lines.append(current)
    return lines


def _qr_reader(url):
    if not url:
        return None
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#1F2A38", back_color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return ImageReader(buffer)
    except Exception:
        return None


def build_blocks(cfg, language="en_GB"):
    """The enabled blocks, in print order, in the book's language."""
    cfg = cfg or {}
    strings = STRINGS[_language(language)]
    blocks = []
    if cfg.get("show_trade", True):
        blocks.append((strings["trade"], cfg.get("trade_url") or "www.dandhpublishing.com/trade"))
    if cfg.get("show_authorcentral") and cfg.get("authorcentral_url"):
        blocks.append((strings["authorcentral"], cfg.get("authorcentral_url")))
    if cfg.get("show_bookclub") and cfg.get("bookclub_url"):
        blocks.append((strings["bookclub"], cfg.get("bookclub_url")))
    if cfg.get("show_catalogue"):
        blocks.append((strings["catalogue"], cfg.get("catalogue_url") or "bookclub2k.com/shop"))
    return blocks


def _diamond(c, cx, cy, radius, color=None):
    c.setFillColor(color or C_GOLD)
    path = c.beginPath()
    path.moveTo(cx, cy + radius)
    path.lineTo(cx + radius, cy)
    path.lineTo(cx, cy - radius)
    path.lineTo(cx - radius, cy)
    path.close()
    c.drawPath(path, stroke=0, fill=1)


def _ornament(c, cx, y, half=28):
    c.setStrokeColor(C_GOLD_SOFT)
    c.setLineWidth(0.5)
    c.line(cx - half, y, cx - 5, y)
    c.line(cx + 5, y, cx + half, y)
    _diamond(c, cx, y, 2.3)


def _tracked_width(text, font, size, track):
    if not text:
        return 0.0
    return pdfmetrics.stringWidth(text, font, size) + track * (len(text) - 1)


def _draw_tracked(c, text, font, size, track, color, x, y):
    c.setFont(font, size)
    c.setFillColor(color)
    for character in text:
        c.drawString(x, y, character)
        x += pdfmetrics.stringWidth(character, font, size) + track


def _draw_tracked_centre(c, text, font, size, track, color, y, center):
    x = center - _tracked_width(text, font, size, track) / 2.0
    _draw_tracked(c, text, font, size, track, color, x, y)


def append_back_matter(pdf_path, trim_width, trim_height, cfg=None, language="en_GB"):
    """Append the back-matter links page, keeping it on a recto."""
    cfg = cfg or {}
    blocks = build_blocks(cfg, language)
    if not blocks:
        return None

    _register_fonts()

    page_w = float(trim_width) * inch
    page_h = float(trim_height) * inch
    margin = min(0.95 * inch, page_w * 0.145)
    text_w = page_w - 2 * margin
    qr_size = (16 * 72 / 25.4) if cfg.get("show_qr") else 0.0

    header_size = 9.2
    body_size = 8.6
    leading = body_size + 3.8
    box_h = max(qr_size + 14, 32.0)

    side_path = pdf_path.replace(".pdf", "_backmatter.pdf")
    c = cv.Canvas(side_path, pagesize=(page_w, page_h))

    footer_y = margin * 0.5
    block_top = page_h - margin - 30
    floor_y = footer_y + 30

    def masthead():
        brand = "D&H PUBLISHING INTERNATIONAL"
        _draw_tracked_centre(c, brand, _font(brand, "SanB"), 6.6, 2.6, C_MUTED, page_h - margin, page_w / 2)
        _ornament(c, page_w / 2, page_h - margin - 10, 40)

    def colophon():
        c.setStrokeColor(C_GOLD_SOFT)
        c.setLineWidth(0.5)
        c.line(page_w / 2 - 34, footer_y + 14, page_w / 2 + 34, footer_y + 14)
        _diamond(c, page_w / 2, footer_y + 14, 1.8, C_GOLD)
        imprint = "D&H PUBLISHING INTERNATIONAL LTD"
        _draw_tracked_centre(c, imprint, _font(imprint, "SanB"), 5.6, 1.7, C_MUTED, footer_y, page_w / 2)

    def link_box(cx, top, url, qr):
        label = _display_url(url) or ""
        font = _font(label, "SanB")
        size = 8.6
        max_label = min(text_w * 0.62, 170)
        if pdfmetrics.stringWidth(label, font, size) > max_label:
            while label and pdfmetrics.stringWidth(label + "...", font, size) > max_label:
                label = label[:-1]
            label = label.rstrip() + "..."
        pad = 8.0
        gap = 9.0 if qr is not None else 0.0
        qr_w = qr_size if qr is not None else 0.0
        label_w = max(pdfmetrics.stringWidth(label, font, size), 34.0)
        width = pad * 2 + qr_w + gap + label_w
        width = min(width, text_w)
        left = cx - width / 2.0
        bottom = top - box_h
        c.setStrokeColor(C_GOLD_SOFT)
        c.setLineWidth(0.5)
        c.roundRect(left, bottom, width, box_h, 3.0, stroke=1, fill=0)
        x = left + pad
        if qr is not None:
            c.drawImage(qr, x, bottom + (box_h - qr_size) / 2.0, width=qr_size, height=qr_size, mask="auto")
            x += qr_size + gap
        cy = bottom + box_h / 2.0
        caption = "VISIT"
        _draw_tracked(c, caption, _font(caption, "SanB"), 5.6, 1.5, C_GOLD, x, cy + 2.4)
        c.setFont(font, size)
        c.setFillColor(C_INK)
        c.drawString(x, cy - 8.6, label)
        return bottom

    measured = []
    for header, body in [block[0] for block in blocks]:
        lines = _wrap(body, body_size, text_w * 0.72, "SanI")
        height = header_size + 8 + len(lines) * leading + 10 + box_h
        measured.append((height, lines))

    gap = 24.0
    total = sum(item[0] for item in measured) + gap * (len(blocks) - 1)
    available = block_top - floor_y
    slack = available - total
    start = block_top
    if slack > 0:
        gap += min(slack / max(len(blocks), 1), 44)
        start = block_top - min(slack * 0.3, 76)

    state = {"started": False}

    def start_page():
        if state["started"]:
            c.showPage()
        state["started"] = True
        masthead()
        colophon()

    start_page()

    y = start
    for index, block in enumerate(blocks):
        (header, body), url = block[0], block[1]
        height, lines = measured[index]
        qr = _qr_reader(_full_url(url)) if qr_size else None
        if index:
            if y - height < floor_y:
                start_page()
                y = block_top
            else:
                _ornament(c, page_w / 2, y + gap / 2.0 - 3, 24)
                y -= gap
        _draw_tracked_centre(c, header, _font(header, "SanB"), header_size, 1.5, C_INK, y, page_w / 2)
        y -= header_size + 6
        for line in lines:
            c.setFont(_font(line, "SanI"), body_size)
            c.setFillColor(C_BODY)
            c.drawCentredString(page_w / 2, y, line)
            y -= leading
        y -= 9
        y = link_box(page_w / 2, y, url, qr)

    c.save()

    writer = PdfWriter(clone_from=PdfReader(pdf_path))
    if len(writer.pages) % 2 == 1:
        writer.add_blank_page(width=page_w, height=page_h)
    writer.append(PdfReader(side_path))
    with open(pdf_path, "wb") as handle:
        writer.write(handle)
    return side_path
