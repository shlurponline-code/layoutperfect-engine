# -*- coding: utf-8 -*-
"""
Layout Perfect - Artwork intake
===============================
Turns the artwork authors actually send into the images the picture book
pipeline prints.

Illustrators export one PDF per spread (or a single PDF for the whole book),
usually with printer marks outside the trim. PDF pages are rendered at 300 DPI
from the page's crop box, so a crop-marked page arrives at exactly the trim +
bleed size instead of failing the dimension check. TIFF files - which browsers
cannot display - get a small JPEG preview so the editor can still see the
running order.
"""

import base64
import io

import fitz  # PyMuPDF
from PIL import Image

from picture_book import fetch_bytes

GOOD_DPI = 300.0
MAX_PAGE_PIXELS = 40_000_000   # ~36 MP guard: keeps a huge spread inside memory
THUMB_PX = 480

try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # Pillow < 9.1
    LANCZOS = Image.LANCZOS


def _open_pdf(url):
    return fitz.open(stream=fetch_bytes(url), filetype="pdf")


def _page_geometry(page):
    """Trim geometry of one PDF page, honouring its crop box."""
    media = page.mediabox
    crop = page.cropbox
    width_in = float(crop.width) / 72.0
    height_in = float(crop.height) / 72.0
    marks_x = (float(media.width) - float(crop.width)) / 72.0
    marks_y = (float(media.height) - float(crop.height)) / 72.0
    return {
        "width_in": round(width_in, 3),
        "height_in": round(height_in, 3),
        "crop_applied": marks_x > 0.01 or marks_y > 0.01,
        "marks_band_in": round(max(marks_x, marks_y) / 2.0, 3),
    }


def probe_pdf(url):
    """Page count and trim geometry for every page - before any rendering."""
    document = _open_pdf(url)
    try:
        pages = []
        for index in range(document.page_count):
            geometry = _page_geometry(document[index])
            geometry["index"] = index + 1
            pages.append(geometry)
        rotated = any(int(document[i].rotation or 0) % 180 == 90 for i in range(document.page_count))
        return {
            "page_count": document.page_count,
            "pages": pages,
            "rotated_pages": rotated,
            "crop_applied": any(page["crop_applied"] for page in pages),
        }
    finally:
        document.close()


def render_pdf_page(url, page_number, dpi=GOOD_DPI):
    """One PDF page as a print-resolution RGB image, cropped to its crop box."""
    document = _open_pdf(url)
    try:
        if page_number < 1 or page_number > document.page_count:
            raise ValueError(
                "Page {} is outside this PDF (it has {} pages)".format(page_number, document.page_count)
            )
        page = document[page_number - 1]
        geometry = _page_geometry(page)

        effective_dpi = float(dpi or GOOD_DPI)
        pixels = (geometry["width_in"] * effective_dpi) * (geometry["height_in"] * effective_dpi)
        while pixels > MAX_PAGE_PIXELS and effective_dpi > 150:
            effective_dpi -= 25.0
            pixels = (geometry["width_in"] * effective_dpi) * (geometry["height_in"] * effective_dpi)

        scale = effective_dpi / 72.0
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale), clip=page.cropbox, alpha=False
        )
        image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
        return {
            "image": image,
            "page": page_number,
            "page_count": document.page_count,
            "dpi": round(effective_dpi, 1),
            "crop_applied": geometry["crop_applied"],
            "marks_band_in": geometry["marks_band_in"],
        }
    finally:
        document.close()


def image_thumbnail(url, max_px=THUMB_PX, quality=86):
    """A small JPEG preview plus the true pixel size of any raster artwork."""
    raw = fetch_bytes(url)
    image = Image.open(io.BytesIO(raw))
    image.load()
    width_px, height_px = image.size
    preview = image.convert("RGB")
    if max(preview.size) > max_px:
        ratio = float(max_px) / float(max(preview.size))
        preview = preview.resize(
            (max(1, int(preview.width * ratio)), max(1, int(preview.height * ratio))), LANCZOS
        )
    buffer = io.BytesIO()
    preview.save(buffer, "JPEG", quality=quality)
    return {
        "jpeg_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
        "width_px": width_px,
        "height_px": height_px,
        "format": (image.format or "").upper(),
    }


def jpeg_base64(image, quality=92):
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=quality, dpi=(300, 300))
    return base64.b64encode(buffer.getvalue()).decode("ascii")
