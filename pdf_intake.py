# -*- coding: utf-8 -*-
"""
Layout Perfect - Artwork intake
===============================
Turns the artwork authors actually send into the images the picture book
pipeline prints.

Illustrators export one PDF per spread (or a single PDF for the whole book),
usually with printer marks outside the trim. PDF pages are rendered at 300 DPI
from the page's crop box, so a crop-marked page arrives at exactly the trim +
bleed size instead of failing the dimension check. A page that carries an empty
band - a landscape spread exported onto a square canvas, most often - is cut
back to its artwork, because that band would otherwise print as a white stripe.
TIFF files, which browsers cannot display, get a small JPEG preview so the
editor can still see the running order.
"""

import base64
import io

import fitz  # PyMuPDF
from PIL import Image

from picture_book import fetch_bytes

GOOD_DPI = 300.0
MAX_PAGE_PIXELS = 40_000_000   # ~36 MP guard: keeps a huge spread inside memory
THUMB_PX = 480

BLANK_LEVEL = 248          # a pixel this light, or lighter, is bare paper
BLOCK_PX = 16              # sampling grid; a block counts as printed at ~1.6% ink
FULL_SPAN_SHARE = 0.04     # blank this small means the artwork runs to that edge
MIN_BAND_SHARE = 0.15      # an empty band this wide is excess canvas, not a margin

try:
    LANCZOS = Image.Resampling.LANCZOS
    BOX = Image.Resampling.BOX
except AttributeError:  # Pillow < 9.1
    LANCZOS = Image.LANCZOS
    BOX = Image.BOX


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


def artwork_bounds(image, level=BLANK_LEVEL):
    """Where the printed artwork sits inside a page, ignoring empty canvas.

    Sampled on a coarse grid, so a speck of dust in the margin cannot count as
    artwork and keep a blank band alive.
    """
    width, height = image.size
    mask = image.convert("L").point(lambda value: 255 if value < level else 0)
    grid = mask.resize((max(1, width // BLOCK_PX), max(1, height // BLOCK_PX)), BOX)
    bounds = grid.point(lambda value: 255 if value >= 4 else 0).getbbox()
    if not bounds:
        return None
    return (
        max(0, bounds[0] * BLOCK_PX - BLOCK_PX),
        max(0, bounds[1] * BLOCK_PX - BLOCK_PX),
        min(width, bounds[2] * BLOCK_PX + BLOCK_PX),
        min(height, bounds[3] * BLOCK_PX + BLOCK_PX),
    )


def trim_excess_canvas(image, level=BLANK_LEVEL):
    """Cut away an empty band a page was exported with, keeping the artwork.

    Only acts on the giveaway shape of a padded export: the artwork runs to both
    edges of one axis, so a wide empty band across the other axis is canvas
    rather than a design margin. A page that is simply generous with white space
    is left exactly as it arrived.
    """
    width, height = image.size
    bounds = artwork_bounds(image, level)
    if not bounds:
        return image
    left, top, right, bottom = bounds
    blank_left, blank_right = left, width - right
    blank_top, blank_bottom = top, height - bottom

    cut_left = cut_top = cut_right = cut_bottom = 0
    spans_width = (
        blank_left <= FULL_SPAN_SHARE * width and blank_right <= FULL_SPAN_SHARE * width
    )
    spans_height = (
        blank_top <= FULL_SPAN_SHARE * height and blank_bottom <= FULL_SPAN_SHARE * height
    )
    if spans_width:
        if blank_top >= MIN_BAND_SHARE * height:
            cut_top = blank_top
        if blank_bottom >= MIN_BAND_SHARE * height:
            cut_bottom = blank_bottom
    elif spans_height:
        if blank_left >= MIN_BAND_SHARE * width:
            cut_left = blank_left
        if blank_right >= MIN_BAND_SHARE * width:
            cut_right = blank_right

    if not (cut_left or cut_top or cut_right or cut_bottom):
        return image
    return image.crop((cut_left, cut_top, width - cut_right, height - cut_bottom))


def render_pdf_page(url, page_number, dpi=GOOD_DPI):
    """One PDF page as a print-resolution RGB image: crop box, minus empty canvas."""
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
        image = trim_excess_canvas(image)
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
