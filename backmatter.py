"""Back-matter links page for Layout Perfect interiors.

Renders the standard D&H back-matter blocks (trade and wholesale enquiries,
the AuthorCentral book page, the BookClub2K purchase link and the full
catalogue) as one or more appended pages, with an optional QR code beside
each URL. The page is appended after the interior is built, so it works for
every template.
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

C_BODY = HexColor("#2C2C2C")
C_DARK = HexColor("#4A4A4A")
C_RULE = HexColor("#C9C1AE")
C_GREY = HexColor("#999999")

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
    for name, filename in (("San", "FreeSans.ttf"), ("SanB", "FreeSansBold.ttf")):
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


def _wrap(text, size, max_width):
    text = (text or "").strip()
    if not text:
        return []
    lines = []
    current = ""
    for word in text.split():
        candidate = (current + " " + word).strip()
        if pdfmetrics.stringWidth(candidate, _font(candidate, "San"), size) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = ""
        if pdfmetrics.stringWidth(word, _font(word, "San"), size) <= max_width:
            current = word
            continue
        for character in word:
            attempt = current + character
            if pdfmetrics.stringWidth(attempt, _font(attempt, "San"), size) <= max_width:
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
        image = qr.make_image(fill_color="#2C2C2C", back_color="white")
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
        blocks.append((strings["catalogue"], cfg.get("catalogue_url") or "www.dandhpublishing.com/books"))
    return blocks


def append_back_matter(pdf_path, trim_width, trim_height, cfg=None, language="en_GB"):
    """Append the back-matter links page, keeping it on a recto."""
    blocks = build_blocks(cfg, language)
    if not blocks:
        return None

    _register_fonts()

    page_w = float(trim_width) * inch
    page_h = float(trim_height) * inch
    margin = min(1.0 * inch, page_w * 0.16)
    text_w = page_w - 2 * margin
    qr_size = (20 * 72 / 25.4) if cfg.get("show_qr") else 0

    side_path = pdf_path.replace(".pdf", "_backmatter.pdf")
    c = cv.Canvas(side_path, pagesize=(page_w, page_h))
    bottom_limit = margin + 46

    state = {"y": page_h - margin, "started": False}

    def new_page():
        if state["started"]:
            c.showPage()
        state["started"] = True
        state["y"] = page_h - margin

    new_page()

    for block in blocks:
        header, body = block[0]
        url = block[1]
        qr = _qr_reader(_full_url(url)) if qr_size else None
        wrap_w = text_w - (qr_size + 14 if qr_size else 0)
        body_lines = _wrap(body, 9, wrap_w)
        needed = 15 + len(body_lines) * 12.4 + (qr_size + 10 if qr_size else 16) + 18
        if state["y"] - needed < bottom_limit:
            new_page()

        y = state["y"]
        top = y

        c.setFont(_font(header, "SanB"), 9.5)
        c.setFillColor(C_BODY)
        c.drawString(margin, y, header)
        y -= 15

        for line in body_lines:
            c.setFont(_font(line, "San"), 9)
            c.setFillColor(C_DARK)
            c.drawString(margin, y, line)
            y -= 12.4

        y -= 4
        label = _display_url(url)
        c.setFont(_font(label, "SanB"), 9)
        c.setFillColor(C_BODY)
        c.drawString(margin, y, label)

        if qr is not None:
            c.drawImage(qr, margin + text_w - qr_size, top - qr_size, width=qr_size, height=qr_size, mask="auto")
            y = min(y - 8, top - qr_size - 8)
        else:
            y -= 12

        c.setStrokeColor(C_RULE)
        c.setLineWidth(0.4)
        c.line(margin, y, margin + text_w, y)
        state["y"] = y - 18

    c.setFont("SanB", 7.4)
    c.setFillColor(C_GREY)
    c.drawCentredString(page_w / 2, margin * 0.62, "D&H PUBLISHING INTERNATIONAL LTD")
    c.save()

    writer = PdfWriter(clone_from=PdfReader(pdf_path))
    if len(writer.pages) % 2 == 1:
        writer.add_blank_page(width=page_w, height=page_h)
    writer.append(PdfReader(side_path))
    with open(pdf_path, "wb") as handle:
        writer.write(handle)
    return side_path
