"""
Layout Perfect Typesetting API
==============================
FastAPI wrapper around the typesetting engine.
Deploy on Railway, Render, or Fly.io.

Endpoints:
  POST /typeset     Ã¢ÂÂ takes manuscript + config, returns PDF + page count
  POST /epub        Ã¢ÂÂ takes manuscript + config, returns ePub file
  GET  /health      Ã¢ÂÂ health check
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

# CORS Ã¢ÂÂ allow Base44 to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down to layoutperfect.com and base44.com in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Auth Ã¢ÂÂ simple API key for now
API_KEY = os.environ.get("LP_API_KEY", "lp-dev-key-change-me")


def check_auth(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Ã¢ÂÂÃ¢ÂÂ Request/Response models Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

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
    body_size_pt: float = Field(default=12)
    leading_pt: float = Field(default=18)
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
    # Verso fill (LP-FEAT-008)
    verso_content: str = Field(default="none")
    verso_quotes: str = Field(default="")
    verso_quote_style: str = Field(default="italic")
    verso_quote_size: float = Field(default=14)
    verso_images: list = Field(default_factory=list)
    verso_image_captions: list = Field(default_factory=list)
    verso_image_size: str = Field(default="medium")
    verso_image_opacity: float = Field(default=100)
    # Interior feature overrides: drop caps, chapter opener ornaments, scene
    # breaks, running headers/folios, pull quotes and callouts. Keys are the
    # template-registry keys; omitted keys keep the template's own defaults.
    interior: dict = Field(default_factory=dict)
    # Back-matter links page (trade, AuthorCentral, BookClub2K, catalogue)
    back_matter: dict = Field(default_factory=dict)


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
    toc_title: str = Field(default="")


class EpubRequest(BaseModel):
    api_key: str
    manuscript: str
    title: str = "Untitled"
    author: str = "Unknown"
    publisher: str = "D&H Publishing International"
    isbn: str = ""
    language: str = "en-GB"


# Ã¢ÂÂÃ¢ÂÂ Endpoints Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Layout Perfect v1.0"}


def append_author_central_page(pdf_path, trim_width, trim_height, author_central_url, language="en_GB"):
    """Append an Author Central back page (recto) with QR code to the PDF."""
    import qrcode
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as cv
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from pypdf import PdfReader, PdfWriter
    from typeset_engine import get_front_text, cjk_aware_font, has_cjk

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
        # CJK scripts have no word spaces: break between characters instead.
        if has_cjk(text) and " " not in text.strip():
            lines = []
            current = ""
            for ch in text:
                if pdfmetrics.stringWidth(current + ch, font, size) <= max_width:
                    current += ch
                else:
                    if current:
                        lines.append(current)
                    current = ch
            if current:
                lines.append(current)
            return lines
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

    # Copy follows the manuscript's language
    heading = get_front_text(language, "ac_heading")
    para1 = get_front_text(language, "ac_body")
    para2 = get_front_text(language, "ac_scan")
    qa_msg = get_front_text(language, "ac_qa")

    cx = PAGE_W / 2

    def _ac_ornament(oy):
        c.setStrokeColor(C_DARK)
        c.setFillColor(C_DARK)
        c.setLineWidth(0.5)
        c.line(cx - 34, oy, cx - 9, oy)
        c.line(cx + 9, oy, cx + 34, oy)
        c.saveState()
        c.translate(cx, oy)
        c.rotate(45)
        c.rect(-2.6, -2.6, 5.2, 5.2, fill=1, stroke=0)
        c.restoreState()

    text_w = PAGE_W - 2 * MARGIN
    wrap_w = text_w - 24
    qr_size = 25 * 72 / 25.4
    qr_bottom = MARGIN + 72
    body_limit = qr_bottom + qr_size + 12

    # Heading, centred beneath a drawn ornament
    y = PAGE_H - MARGIN - 26
    _ac_ornament(y)
    y -= 30
    for line in wrap_text(heading, cjk_aware_font(heading, "GarB"), 16, text_w):
        c.setFont(cjk_aware_font(line, "GarB"), 16)
        c.setFillColor(C_BODY)
        c.drawCentredString(cx, y, line)
        y -= 21
    y -= 3
    c.setStrokeColor(C_DARK)
    c.setLineWidth(0.4)
    c.line(cx - 24, y, cx + 24, y)
    y -= 22

    # Body copy, centred
    for para in (para1, para2):
        pf = cjk_aware_font(para, "Gar")
        for line in wrap_text(para, pf, 9.3, wrap_w):
            if y < body_limit:
                break
            c.setFont(cjk_aware_font(line, "Gar"), 9.3)
            c.setFillColor(C_BODY)
            c.drawCentredString(cx, y, line)
            y -= 12.8
        y -= 8

    # Quality-assurance note - invites readers who spot an issue to reach
    # the publisher directly via the QR code, so genuine errors are caught
    # before they become public reviews.
    for line in wrap_text(qa_msg, cjk_aware_font(qa_msg, "GarI"), 9.3, wrap_w - 20):
        if y < body_limit:
            break
        c.setFont(cjk_aware_font(line, "GarI"), 9.3)
        c.setFillColor(C_DARK)
        c.drawCentredString(cx, y, line)
        y -= 12.8

    # QR code and link, a centred group above the imprint
    c.drawImage(qr_reader, cx - qr_size / 2, qr_bottom, width=qr_size, height=qr_size)
    c.setFont("GarI", 10)
    c.setFillColor(C_DARK)
    c.drawCentredString(cx, qr_bottom - 19, display_url)

    # Imprint at foot
    c.setStrokeColor(C_DARK)
    c.setLineWidth(0.4)
    c.line(cx - 18, MARGIN + 28, cx + 18, MARGIN + 28)
    c.setFont("GarB", 7.6)
    c.setFillColor(C_GREY)
    c.drawCentredString(cx, MARGIN + 14, "D&H PUBLISHING INTERNATIONAL LTD")
    c.save()

    # Merge into main PDF, ensuring recto page
    reader = PdfReader(pdf_path)
    # Use clone_from to preserve font embedding from the original ReportLab PDF.
    # Manually adding pages via add_page() can lose subsetted font resources.
    writer = PdfWriter(clone_from=reader)

    if len(writer.pages) % 2 == 1:
        writer.add_blank_page(width=PAGE_W, height=PAGE_H)

    ac_reader = PdfReader(ac_path)
    # Use append() instead of add_page() to properly copy font resources
    # from the Author Central PDF into the merged document.
    writer.append(ac_reader)

    with open(pdf_path, "wb") as f:
        writer.write(f)

    os.remove(ac_path)



def verify_font_embedding(pdf_path):
    """Check that all fonts in the PDF are embedded. KDP requires this."""
    from pypdf import PdfReader
    try:
        reader = PdfReader(pdf_path)
        unembedded = []
        for page in reader.pages:
            resources = page.get("/Resources")
            if not resources:
                continue
            fonts = resources.get("/Font")
            if not fonts:
                continue
            for font_name in fonts:
                font_obj = fonts[font_name]
                font = font_obj.get_object() if hasattr(font_obj, 'get_object') else font_obj
                font_desc = font.get("/FontDescriptor")
                if font_desc:
                    fd = font_desc.get_object() if hasattr(font_desc, 'get_object') else font_desc
                    if not (fd.get("/FontFile") or fd.get("/FontFile2") or fd.get("/FontFile3")):
                        unembedded.append(str(font_name))
                else:
                    unembedded.append(str(font_name))
        if unembedded:
            print(f"WARNING: Unembedded fonts detected: {unembedded}")
        else:
            print("Font embedding check: ALL FONTS EMBEDDED")
        return unembedded
    except Exception as e:
        print(f"Font embedding check failed: {e}")
        return []


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
        from typeset_engine import BookBuilder, GenericBookBuilder, PAGE_W, PAGE_H, get_toc_title

        # KDP gutter requirement varies by page count — estimate pages
        # from word count and ensure the inside margin meets the minimum.
        word_count = len(req.manuscript.split())
        est_pages = max(24, int(word_count / 280))
        if est_pages <= 150:
            kdp_min_gutter_in = 0.375
        elif est_pages <= 300:
            kdp_min_gutter_in = 0.5
        elif est_pages <= 500:
            kdp_min_gutter_in = 0.625
        elif est_pages <= 700:
            kdp_min_gutter_in = 0.75
        else:
            kdp_min_gutter_in = 0.875

        # Calculate inside margin, ensuring it meets KDP minimum gutter
        inside_margin_in = req.margin_inside_cm / 2.54 + req.gutter_cm / 2.54
        if inside_margin_in < kdp_min_gutter_in:
            inside_margin_in = kdp_min_gutter_in
            print(f'KDP gutter override: inside margin increased to {kdp_min_gutter_in}in for ~{est_pages} pages (est. from {word_count} words)')

        # Apply custom margins (all enforced to KDP minimums)
        import typeset_engine as engine
        engine.MARGIN_INSIDE = inside_margin_in * 72
        engine.MARGIN_OUTSIDE = max(req.margin_outside_cm / 2.54, 0.25) * 72
        engine.MARGIN_TOP = max(req.margin_top_cm / 2.54, 0.25) * 72
        engine.MARGIN_BOTTOM = max(req.margin_bottom_cm / 2.54, 0.25) * 72

        # Templates can trim margins further (cookbook runs tighter to make the
        # most of a small trim size). KDP minimums stay enforced.
        try:
            from templates import TEMPLATES as _TPL
            _mm = float(_TPL.get(req.template, {}).get('margin_multiplier', 1.0) or 1.0)
        except Exception:
            _mm = 1.0
        if _mm != 1.0:
            engine.MARGIN_OUTSIDE = max(engine.MARGIN_OUTSIDE * _mm, 0.25 * 72)
            engine.MARGIN_TOP = max(engine.MARGIN_TOP * _mm, 0.25 * 72)
            engine.MARGIN_BOTTOM = max(engine.MARGIN_BOTTOM * _mm, 0.25 * 72)
            print(f'Margin trim: {req.template} template scales margins by {_mm}')
        engine.BODY_SZ = req.body_size_pt
        engine.BODY_LD = req.leading_pt
        engine.CH_TITLE_SZ = req.chapter_title_size_pt
        engine.TEXT_ALIGNMENT = req.text_alignment
        engine.HYPHEN_LANGUAGE = req.language
        engine.set_language_fonts(req.language)

        # Verso fill config
        import json as _json
        engine.VERSO_CONTENT = req.verso_content
        try:
            engine.VERSO_QUOTES = _json.loads(req.verso_quotes) if req.verso_quotes else []
        except Exception:
            engine.VERSO_QUOTES = []
        engine.VERSO_QUOTE_STYLE = req.verso_quote_style
        engine.VERSO_QUOTE_SIZE = req.verso_quote_size
        engine.VERSO_IMAGES = req.verso_images or []
        engine.VERSO_IMAGE_CAPTIONS = req.verso_image_captions or []
        engine.VERSO_IMAGE_SIZE = req.verso_image_size
        engine.VERSO_IMAGE_OPACITY = req.verso_image_opacity

        # Apply trim size from user selection (supports all KDP trim sizes)
        engine.set_trim_size(req.trim_width, req.trim_height)

        # Route to the correct builder based on template
        if req.template == 'portrait':
            builder = BookBuilder(md_path, output_path, language=req.language)
        else:
            builder = GenericBookBuilder(
                md_path, output_path,
                title=req.title,
                subtitle=req.subtitle,
                author=req.author,
                chapter_end_ornament=req.chapter_end_ornament,
                language=req.language,
                template=req.template,
                interior_overrides=req.interior,
            )
        
        block_types = ",".join(b.get('type','?') for b in builder.blocks)
        print(f"BLOCK_TYPES: {block_types}")
        
        builder.build()

        # Verify font embedding for KDP compliance
        verify_font_embedding(output_path)

        # Append Author Central back page if requested
        if req.add_author_central_page and req.author_central_url:
            append_author_central_page(output_path, req.trim_width, req.trim_height, req.author_central_url, req.language)
            # Re-verify font embedding after Author Central page merge
            verify_font_embedding(output_path)

        # Back-matter links page — appended after the interior so it works for
        # every template. A failure here must never lose the typeset book.
        try:
            if req.back_matter and req.back_matter.get('enabled'):
                from backmatter import append_back_matter
                append_back_matter(output_path, req.trim_width, req.trim_height, req.back_matter, req.language)
                verify_font_embedding(output_path)
        except Exception as back_matter_error:
            print('Back-matter page skipped: ' + str(back_matter_error))

        # Count actual pages from the generated PDF
        from pypdf import PdfReader
        reader = PdfReader(output_path)
        page_count = len(reader.pages)

        # Quality pass: Gutter validation for KDP compliance
        gutter_valid = True
        gutter_msg = 'OK'
        try:
            from typeset_engine import validate_gutter
            gutter_valid, req_gutter, actual_gutter, gutter_msg = validate_gutter(page_count)
            if not gutter_valid:
                print(f'GUTTER WARNING: {gutter_msg}')
        except Exception as gutter_err:
            print(f'Gutter validation skipped: {gutter_err}')

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
                       language=req.language.replace('_', '-') if req.language else 'en-GB', subtitle=req.subtitle)
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
            message=f"Typeset complete: {page_count} pages at {req.trim_width} x {req.trim_height} inches" + (f" | WARNING: {gutter_msg}" if not gutter_valid else ""),
            pdf_base64=pdf_base64,
            filename=filename,
            epub_base64=epub_b64,
            toc_title=get_toc_title(req.language),
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
    profiles = text.count("\nÃ¢ÂÂ¢ Ã¢ÂÂ¢ Ã¢ÂÂ¢")

    return {
        "word_count": words,
        "chapter_count": chapters,
        "profile_count": profiles,
    }




# --------------------------------------------------- Picture Book Assembly
from fastapi.responses import FileResponse
from picture_book import assemble_picture_book, get_picture_book_file
from picture_book import run_preflight as picture_book_preflight


class PictureBookRequest(BaseModel):
    api_key: str
    project_id: str = Field(default="pb")
    trim_size: str = Field(default="8.25x6")
    paper_type: str = Field(default="white")
    input_mode: str = Field(default="single")
    images: list = Field(default_factory=list)
    front_matter: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)


def _picture_book_payload(req: PictureBookRequest) -> dict:
    return {
        "project_id": req.project_id,
        "trim_size": req.trim_size,
        "paper_type": req.paper_type,
        "input_mode": req.input_mode,
        "images": req.images,
        "front_matter": req.front_matter,
        "output": req.output,
    }


@app.post("/picture-book/preflight")
def picture_book_preflight_route(req: PictureBookRequest):
    """Validate artwork only - no PDF is produced."""
    check_auth(req.api_key)
    try:
        report = picture_book_preflight(_picture_book_payload(req))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Pre-flight failed: " + str(e))
    return {"status": "success", "project_id": req.project_id, "preflight": report}


@app.post("/picture-book/assemble")
def picture_book_assemble_route(req: PictureBookRequest):
    """Assemble the print-ready interior PDF and the proof preview."""
    check_auth(req.api_key)
    try:
        return assemble_picture_book(_picture_book_payload(req))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Assembly failed: " + str(e))


@app.get("/picture-book/download")
def picture_book_download(job: str, kind: str = "print"):
    path, name = get_picture_book_file(job, kind)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not available")
    return FileResponse(path, media_type="application/pdf", filename=name)

# --------------------------------------------------- Artwork intake
class ArtworkRequest(BaseModel):
    api_key: str
    source_url: str = Field(default="")
    page: int = Field(default=1)
    dpi: float = Field(default=300.0)
    max_px: int = Field(default=480)


def _pdf_intake():
    """Imported lazily so a missing PyMuPDF cannot stop the engine booting."""
    import pdf_intake
    return pdf_intake


@app.post("/picture-book/pdf-probe")
def picture_book_pdf_probe(req: ArtworkRequest):
    """Page count and trim geometry of an artwork PDF, before rendering."""
    check_auth(req.api_key)
    try:
        return _pdf_intake().probe_pdf(req.source_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not read that PDF: " + str(e))


@app.post("/picture-book/pdf-page")
def picture_book_pdf_page(req: ArtworkRequest):
    """One PDF page at print resolution, cropped to the page's crop box."""
    check_auth(req.api_key)
    try:
        result = _pdf_intake().render_pdf_page(req.source_url, req.page, req.dpi)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not extract that page: " + str(e))
    image = result["image"]
    return {
        "page": result["page"],
        "page_count": result["page_count"],
        "dpi": result["dpi"],
        "crop_applied": result["crop_applied"],
        "marks_band_in": result["marks_band_in"],
        "width_px": image.width,
        "height_px": image.height,
        "width_in": round(image.width / 300.0, 3),
        "height_in": round(image.height / 300.0, 3),
        "jpeg_base64": _pdf_intake().jpeg_base64(image),
    }


@app.post("/picture-book/thumbnail")
def picture_book_thumbnail(req: ArtworkRequest):
    """Small JPEG preview for artwork a browser cannot display (TIFF)."""
    check_auth(req.api_key)
    try:
        return _pdf_intake().image_thumbnail(req.source_url, req.max_px)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not preview that file: " + str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
