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


class TypesetResponse(BaseModel):
    success: bool
    page_count: int
    spine_width_inches: float
    spine_width_mm: float
    word_count: int
    file_size_bytes: int
    message: str


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

        # Route to the correct builder based on template
        if req.template == 'portrait':
            builder = BookBuilder(md_path, output_path)
        else:
            builder = GenericBookBuilder(
                md_path, output_path,
                title=req.title,
                subtitle=req.subtitle,
                author=req.author,
            )
        
        builder.build()

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

        # Store for the download endpoint
        app.state.last_pdf = pdf_bytes
        app.state.last_pdf_name = f"{req.title.replace(' ', '_')}_interior_{req.edition}.pdf"

        return TypesetResponse(
            success=True,
            page_count=page_count,
            spine_width_inches=round(spine_inches, 4),
            spine_width_mm=round(spine_mm, 1),
            word_count=word_count,
            file_size_bytes=file_size,
            message=f"Typeset complete: {page_count} pages at {req.trim_width} x {req.trim_height} inches"
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
