"""
Layout Perfect Typesetting API
==============================
FastAPI wrapper around the typesetting engine.
Deploy on Railway, Render, or Fly.io.

Endpoints:
  POST /typeset     — takes manuscript + config, returns PDF as base64 + page count
  POST /epub        — takes manuscript + config, returns ePub file
  GET  /health      — health check
"""

import os
import io
import json
import base64
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(
    title="Layout Perfect Typesetting API",
    version="2.0.0",
    description="Manuscript to print-ready PDF engine"
)

# CORS — allow Base44 to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Auth — Bearer token
API_KEY = os.environ.get("LP_API_KEY", "lp-dev-key-change-me")


def check_auth(request_api_key: str = None, authorization: str = None):
    key = None
    if authorization and authorization.startswith("Bearer "):
        key = authorization[7:]
    elif request_api_key:
        key = request_api_key
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# —— Request/Response models ——————————————————————

class TypesetRequest(BaseModel):
    api_key: Optional[str] = None  # kept for backwards compat; prefer Bearer header
    manuscript: str = Field(..., description="Full markdown manuscript text")
    title: str = Field(default="Untitled")
    author: str = Field(default="Unknown")
    template: str = Field(default="portrait")
    trim_width: float = Field(default=5.5)
    trim_height: float = Field(default=8.5)
    paper_type: str = Field(default="white")
    edition: str = Field(default="paperback")

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


class EpubRequest(BaseModel):
    api_key: Optional[str] = None
    manuscript: str
    title: str = "Untitled"
    author: str = "Unknown"
    publisher: str = "D&H Publishing International"
    isbn: str = ""
    language: str = "en-GB"


# —— Endpoints ——————————————————————————————————————

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Layout Perfect v2.0"}


@app.post("/typeset")
def typeset(req: TypesetRequest):
    """Typeset a manuscript. Returns JSON with page count AND the PDF as base64."""
    check_auth(request_api_key=req.api_key)

    if not req.manuscript.strip():
        raise HTTPException(status_code=400, detail="Manuscript is empty")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(req.manuscript)
        md_path = f.name

    output_path = md_path.replace('.md', '_PRINT.pdf')

    try:
        from typeset_engine import BookBuilder
        import typeset_engine as engine

        engine.MARGIN_INSIDE = (req.margin_inside_cm / 2.54 + req.gutter_cm / 2.54) * 72
        engine.MARGIN_OUTSIDE = (req.margin_outside_cm / 2.54) * 72
        engine.MARGIN_TOP = (req.margin_top_cm / 2.54) * 72
        engine.MARGIN_BOTTOM = (req.margin_bottom_cm / 2.54) * 72
        engine.BODY_SZ = req.body_size_pt
        engine.BODY_LD = req.leading_pt
        engine.CH_TITLE_SZ = req.chapter_title_size_pt

        builder = BookBuilder(md_path, output_path, title=req.title, author=req.author)
        builder.build()

        from pypdf import PdfReader
        reader = PdfReader(output_path)
        page_count = len(reader.pages)

        factor = 0.0022 if req.paper_type == "white" else 0.0025
        spine_inches = page_count * factor
        spine_mm = spine_inches * 25.4

        word_count = len(req.manuscript.split())

        with open(output_path, 'rb') as f:
            pdf_bytes = f.read()

        pdf_b64 = base64.b64encode(pdf_bytes).decode('ascii')
        filename = f"{req.title.replace(' ', '_')}_interior_{req.edition}.pdf"

        return JSONResponse({
            "success": True,
            "page_count": page_count,
            "spine_width_inches": round(spine_inches, 4),
            "spine_width_mm": round(spine_mm, 1),
            "word_count": word_count,
            "file_size_bytes": len(pdf_bytes),
            "message": f"Typeset complete: {page_count} pages at {req.trim_width} x {req.trim_height} inches",
            "pdf_base64": pdf_b64,
            "filename": filename
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Typesetting failed: {str(e)}")

    finally:
        for path in [md_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass


@app.post("/word-count")
def word_count(req: dict):
    text = req.get("manuscript", "")
    if not text:
        raise HTTPException(status_code=400, detail="No manuscript provided")
    words = len(text.split())
    chapters = text.count("\n## ") + text.count("\n# ")
    return {"word_count": words, "chapter_count": chapters}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
