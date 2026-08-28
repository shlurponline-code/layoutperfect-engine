"""
Layout Perfect Typesetting API
==============================
FastAPI wrapper around the typesetting engine.
Deploy on Railway, Render, or Fly.io.

Endpoints:
  POST /typeset     — takes manuscript + config, returns PDF + page count
  POST /epub        — takes manuscript + config, returns ePub file
  GET  /health      — health check
"""

import os
import io
import json
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(
    title="Layout Perfect Typesetting API",
    version="1.0.0",
    description="Manuscript to print-ready PDF engine"
)

# CORS — allow Base44 to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down to layoutperfect.com and base44.com in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Auth — simple API key for now
API_KEY = os.environ.get("LP_API_KEY", "lp-dev-key-change-me")


def check_auth(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── Request/Response models ──────────────────────────

class TypesetRequest(BaseModel):
    api_key: str
    manuscript: str = Field(..., description="Full markdown manuscript text")
    title: str = Field(default="Untitled")
    subtitle: str = Field(default="")
    author: str = Field(default="Unknown")
    template: str = Field(default="portrait")
    trim_width: float = Field(default=5.5)
    trim_height: float = Field(default=8.5)
    paper_type: str = Field(default="white")
    edition: str = Field(default="paperback", description="paperback or hardback")

    # TypesetConfig fields
    margin_top_cm: float = Field(default=2.54)
    margin_bottom_cm: float = Field(default=2.54)
    margin_inside_cm: float = Field(default=1.54)
    margin_outside_cm: float = Field(default=1.6)
    gutter_cm: float = Field(default=1.0)
    body_size_pt: float = Field(default=10.5)
    leading_pt: float = Field(default=14.5)
    chapter_title_size_pt: float = Field(default=22)
    chapter_end_ornament: str = Field(default="fleuron")
    section_separator: str = Field(default="dots3")
    chapter_start: str = Field(default="recto")
    include_index: bool = Field(default=False)

    # Author Central back page
    add_author_central_page: bool = Field(default=False)
    author_central_url: str = Field(default="")

    # Text alignment and hyphenation (LP-FEAT-007)
    text_alignment: str = Field(default="justified", description="justified, left, center, right")
    language: str = Field(default="en_GB", description="Hyphenation language: en_GB, en_US, fr, de, es")


class TypesetResponse(BaseModel):
    success: bool
    page_count: int
    spine_width_inches: float
    spine_width_mm: float
    word_count: int
    file_size_bytes: int
    message: str
    pdf_base64: str = Field(default="")
    filename: str = Field(default="")
    epub_base64: str = Field(default="")
    epub_filename: str = Field(default="")
    block_types: str = Field(default="")


class EpubRequest(BaseModel):
    api_key: str
    manuscript: str
    title: str = "Untitled"
    author: str = "Unknown"
    publisher: str = "D&H Publishing International"
    isbn: str = ""
    language: str = "en-GB"


# ── Endpoints ────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Layout Perfect v1.0"}


def append_author_central_page(pdf_path, trim_width, trim_height, author_central_url):
    """Append an Author Central back page (recto) with QR code to the PDF."""
    import qrcode
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as cv
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from pypdf import PdfReader, PdfWriter

    FD = "/usr/share/fonts/truetype/freefont"
    pdfmetrics.registerFont(TTFont("Gar", f"{FD}/FreeSerif.ttf"))
    pdfmetrics.registerFont(TTFont("GarB", f"{FD}/FreeSerifBold.ttf"))
    pdfmetrics.registerFont(TTFont("GarI", f"{FD}/FreeSerifItalic.ttf"))

    C_BODY = HexColor("#2C2C2C")
    C_DARK = HexColor("#4A4A4A")
    C_GREY = HexColor("#999999")

    PAGE_W = trim_width * inch
    PAGE_H = trim_height * inch
    MARGIN = 1.0 * inch

    url = author_central_url.strip()
    if not url:
        return
    full_url = url if url.startswith("http") else f"https://{url}"
    display_url = url.replace("https://", "").replace("http://", "")

    def wrap_text(text, font, size, max_width):
        words = text.split()
        lines = []
        current = []
        for word in words:
            test = " ".join(current + [word])
            if pdfmetrics.stringWidth(test, font, size) <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    # Generate QR code with high error correction (allows logo overlay)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#2C2C2C", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_reader = ImageReader(qr_buffer)

    # Create the Author Central page
    ac_path = pdf_path.replace(".pdf", "_author_central.pdf")
    c = cv.Canvas(ac_path, pagesize=(PAGE_W, PAGE_H))

    # Heading
    y = PAGE_H - MARGIN - 50
    c.setFont("GarB", 16)
    c.setFillColor(C_BODY)
    c.drawCentredString(PAGE_W / 2, y, "Discover more from this author")
    y -= 35

    # Paragraphs
    para1 = ("Every book has a story behind the story. Visit the author's page at "
             "AuthorCentral to find out more about the person who wrote the words "
             "you've just read. You'll find their complete catalogue of published works, "
             "background on how this book came to be written, and ways to get in touch "
             "directly. If you enjoyed this book, there may be bonus content waiting "
             "for you, including material that didn't make the final cut, maps, reading "
             "group discussion points, and recommendations for what to read next.")

    para2 = "Scan the QR code below or visit authorcentral.net to explore."

    text_w = PAGE_W - 2 * MARGIN
    c.setFont("Gar", 10.5)
    c.setFillColor(C_BODY)
    for line in wrap_text(para1, "Gar", 10.5, text_w):
        y -= 14.5
        c.drawString(MARGIN, y, line)
    y -= 14.5
    for line in wrap_text(para2, "Gar", 10.5, text_w):
        y -= 14.5
        c.drawString(MARGIN, y, line)

    # QR code (25mm square, centered)
    qr_size = 25 * 72 / 25.4
    qr_x = (PAGE_W - qr_size) / 2
    y -= 50
    c.drawImage(qr_reader, qr_x, y - qr_size, width=qr_size, height=qr_size)

    # URL text below QR code
    y -= qr_size + 25
    c.setFont("GarI", 10)
    c.setFillColor(C_DARK)
    c.drawCentredString(PAGE_W / 2, y, display_url)

    # Copyright at foot
    c.setFont("Gar", 9)
    c.setFillColor(C_GREY)
    c.drawCentredString(PAGE_W / 2, MARGIN + 14, "Published by D&H Publishing International Ltd")
    c.drawCentredString(PAGE_W / 2, MARGIN, "authorcentral.net")

    c.save()

    # Merge into main PDF, ensuring recto page
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    if len(writer.pages) % 2 == 1:
        writer.add_blank_page(width=PAGE_W, height=PAGE_H)

    ac_reader = PdfReader(ac_path)
    writer.add_page(ac_reader.pages[0])

    with open(pdf_path, "wb") as f:
        writer.write(f)

    os.remove(ac_path)


@app.post("/typeset", response_model=TypesetResponse)
def typeset(req: TypesetRequest):
    """Typeset a manuscript and return the PDF."""
    check_auth(req.api_key)

    if not req.manuscript.strip():
        raise HTTPException(status_code=400, detail="Manuscript is empty")

    # Write manuscript to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(req.manuscript)
        md_path = f.name

    output_path = md_path.replace('.md', '_PRINT.pdf')

    try:
        # Import the engine
        from typeset_engine import BookBuilder, GenericBookBuilder, PAGE_W, PAGE_H

        # Apply custom margins
        import typeset_engine as engine
        engine.MARGIN_INSIDE = (req.margin_inside_cm / 2.54 + req.gutter_cm / 2.54) * 72
        engine.MARGIN_OUTSIDE = (req.margin_outside_cm / 2.54) * 72
        engine.MARGIN_TOP = (req.margin_top_cm / 2.54) * 72
        engine.MARGIN_BOTTOM = (req.margin_bottom_cm / 2.54) * 72
        engine.BODY_SZ = req.body_size_pt
        engine.BODY_LD = req.leading_pt
        engine.CH_TITLE_SZ = req.chapter_title_size_pt
        engine.TEXT_ALIGNMENT = req.text_alignment
        engine.HYPHEN_LANGUAGE = req.language

        # Apply trim size from user selection (supports all KDP trim sizes)
        engine.set_trim_size(req.trim_width, req.trim_height)

        # Route to the correct builder based on template
        if req.template == 'portrait':
            builder = BookBuilder(md_path, output_path)
        else:
            builder = GenericBookBuilder(
                md_path, output_path,
                title=req.title,
                subtitle=req.subtitle,
                author=req.author,
                chapter_end_ornament=req.chapter_end_ornament,
            )
        
        block_types = ",".join(b.get('type','?') for b in builder.blocks)
        print(f"BLOCK_TYPES: {block_types}")
        
        builder.build()

        # Append Author Central back page if requested
        if req.add_author_central_page and req.author_central_url:
            append_author_central_page(output_path, req.trim_width, req.trim_height, req.author_central_url)

        # Count actual pages from the generated PDF
        from pypdf import PdfReader
        reader = PdfReader(output_path)
        page_count = len(reader.pages)

        # Calculate spine
        factor = 0.002252 if req.paper_type == "white" else 0.002347
        spine_inches = page_count * factor
        spine_mm = spine_inches * 25.4

        # Word count
        word_count = len(req.manuscript.split())

        # Read the PDF into memory
        with open(output_path, 'rb') as f:
            pdf_bytes = f.read()

        file_size = len(pdf_bytes)

        # Encode PDF as base64 for inline return
        import base64 as b64mod
        pdf_base64 = b64mod.b64encode(pdf_bytes).decode('ascii')
        filename = f"{req.title.replace(' ', '_')}_interior_{req.edition}.pdf"

        # Store for the download endpoint
        # Generate ePub
        epub_b64 = ""
        epub_filename = f"{req.title.replace(' ', '_')}.epub"
        epub_path = md_path.replace('.md', '_PRINT.epub')
        try:
            from epub_builder import build_epub
            build_epub(md_path, epub_path, title=req.title, author=req.author,
                       publisher='D&H Publishing International', isbn='',
                       language='en-GB', subtitle=req.subtitle)
            with open(epub_path, 'rb') as ef:
                epub_bytes = ef.read()
            epub_b64 = base64.b64encode(epub_bytes).decode('utf-8')
        except Exception as epub_err:
            print(f"ePub generation failed: {epub_err}")
        finally:
            if os.path.exists(epub_path):
                try:
                    os.remove(epub_path)
                except:
                    pass

        app.state.last_pdf = pdf_bytes
        app.state.last_pdf_name = filename

        return TypesetResponse(
            success=True,
            page_count=page_count,
            spine_width_inches=round(spine_inches, 4),
            spine_width_mm=round(spine_mm, 1),
            word_count=word_count,
            file_size_bytes=file_size,
            message=f"Typeset complete: {page_count} pages at {req.trim_width} x {req.trim_height} inches",
            pdf_base64=pdf_base64,
            filename=filename,
            epub_base64=epub_b64,
            epub_filename=epub_filename,
            block_types=block_types
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Typesetting failed: {str(e)}")

    finally:
        # Clean up temp files
        for path in [md_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass


@app.get("/typeset/download")
def download_pdf():
    """Download the last generated PDF."""
    if not hasattr(app.state, 'last_pdf') or not app.state.last_pdf:
        raise HTTPException(status_code=404, detail="No PDF generated yet")

    return StreamingResponse(
        io.BytesIO(app.state.last_pdf),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{app.state.last_pdf_name}"'
        }
    )


@app.post("/word-count")
def word_count(req: dict):
    """Count words in a manuscript. No estimation, no guessing."""
    text = req.get("manuscript", "")
    if not text:
        raise HTTPException(status_code=400, detail="No manuscript provided")

    words = len(text.split())
    chapters = text.count("\n## ") + text.count("\n# ")
    profiles = text.count("\n• • •")

    return {
        "word_count": words,
        "chapter_count": chapters,
        "profile_count": profiles,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
