# -*- coding: utf-8 -*-
"""
Layout Perfect - Picture Book Assembly
======================================
Image-first children's books: every page is a full-bleed image with the text
composited into the artwork by the author.

Pipeline: ingest -> sort -> mode dispatch -> pre-flight -> gutter analysis ->
spread split with gutter compensation -> bleed sheet -> front matter ->
page assembly -> print PDF + low-resolution proof PDF.

Canonical source for the engine's picture_book.py (Railway deployment).
"""

import io
import os
import tempfile
import time
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageStat
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------- constants
BLEED_IN = 0.125          # outer + top + bottom, KDP full-bleed requirement
COMP_IN = 0.125           # gutter compensation overlap per inner edge
NO_GO_IN = 1.0            # ~1" unusable zone across a spread centre
MIN_DPI = 250.0
GOOD_DPI = 300.0
SPINE_WHITE = 0.002252    # inches of spine per page
SPINE_CREAM = 0.002500
KDP_MIN_PAGES = 24
MAX_IMAGE_MB = 100.0
DEFAULT_WATERMARK = "PROOF - NOT FOR PRINT"

JOB_DIR = os.path.join(tempfile.gettempdir(), "lp-picture-books")
JOBS = {}

SUPPORTED_FORMATS = ("JPEG", "PNG", "TIFF")

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # Pillow < 9.1
    RESAMPLE = Image.LANCZOS

try:
    # Image.rotate only accepts NEAREST / BILINEAR / BICUBIC.
    ROTATE_RESAMPLE = Image.Resampling.BICUBIC
except AttributeError:
    ROTATE_RESAMPLE = Image.BICUBIC

FLIP_LR = getattr(Image, "FLIP_LEFT_RIGHT", 0)
FLIP_TB = getattr(Image, "FLIP_TOP_BOTTOM", 1)

FONT_DIRS = (
    "/usr/share/fonts/truetype/dejavu/",
    "/usr/share/fonts/truetype/liberation/",
    "/usr/share/fonts/TTF/",
)
FONT_FILES = {
    "regular": ("DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf"),
    "bold": ("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"),
    "italic": ("DejaVuSans-Oblique.ttf", "LiberationSans-Italic.ttf"),
}


# ------------------------------------------------------------------ helpers
def _trim_dims(trim_size):
    try:
        parts = str(trim_size).lower().replace('"', "").split("x")
        return float(parts[0]), float(parts[1])
    except Exception:
        return 8.25, 6.0


def _px(inches, dpi):
    return int(round(inches * dpi))


def _spine_per_page(paper_type):
    return SPINE_CREAM if str(paper_type).lower() == "cream" else SPINE_WHITE


def _hex_to_rgb(value, fallback=(74, 124, 89)):
    text = str(value or "").lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return fallback
    try:
        return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _load_font(size, style="regular"):
    size = max(6, int(size))
    for directory in FONT_DIRS:
        for name in FONT_FILES.get(style, FONT_FILES["regular"]):
            path = os.path.join(directory, name)
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


def fetch_bytes(url):
    """Download an image (or read a local path) as bytes."""
    if not url:
        raise ValueError("Missing image url")
    if url.startswith("/") or url.startswith("file:"):
        with open(url.replace("file://", ""), "rb") as handle:
            return handle.read()
    request = urllib.request.Request(
        url, headers={"User-Agent": "LayoutPerfect-Engine/1.0"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def load_image(url):
    """Return (PIL image, raw byte size, format name)."""
    raw = fetch_bytes(url)
    image = Image.open(io.BytesIO(raw))
    image.load()
    return image, len(raw), (image.format or "").upper()


def sort_key(item, fallback):
    """Sequential filenames sort numerically; an explicit order wins."""
    if item.get("order") not in (None, ""):
        try:
            return (0, float(item["order"]))
        except Exception:
            pass
    name = str(item.get("filename") or item.get("url") or "")
    digits = "".join(ch for ch in os.path.basename(name) if ch.isdigit())
    return (1, float(digits) if digits else float(fallback))


def _wrap_px(text, font, max_width):
    words = str(text or "").split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if font.getlength(candidate) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _average_colour(image):
    bands = image.getbands()
    mean = ImageStat.Stat(image).mean
    if len(bands) == 1:
        return int(mean[0])
    return tuple(int(c) for c in mean[: len(bands)])


def _strip_contrast(image):
    """How strong the outermost band is - used to pick mirror vs colour fill."""
    band = image.convert("L").crop((0, 0, min(24, image.width), image.height))
    if band.width < 2:
        return 0.0
    return ImageStat.Stat(band).stddev[0]


# ------------------------------------------------------- gutter analysis
def gutter_analysis(image, trim_w, input_mode):
    """Look for content in the ~1" no-go zone across a spread centre.

    Text and faces cannot be detected without heavy OCR dependencies, so this
    flags the two things that reliably indicate a problem: dense ink in the
    centre strip (text or fine detail) and a sharp tonal boundary running down
    the centre (an ugly seam). Warnings only - never a rejection.
    """
    findings = []
    if input_mode != "spread":
        return findings
    width, height = image.size
    strip_in = max(0.2, min(NO_GO_IN, 2 * trim_w * 0.5))
    strip_w = max(8, _px(strip_in / 2.0, GOOD_DPI))
    centre = width // 2
    strip = image.convert("L").crop(
        (max(0, centre - strip_w), 0, min(width, centre + strip_w), height)
    )
    small = strip.resize(
        (max(1, strip.width // 4), max(1, strip.height // 4)), RESAMPLE
    )

    histogram = small.histogram()
    total = sum(histogram) or 1
    dark = sum(histogram[:110]) / float(total)
    if dark > 0.10:
        findings.append(
            {
                "type": "content_in_gutter",
                "message": "Dense ink in the gutter zone - check for text or key story detail ({:.0f}% coverage)".format(
                    dark * 100
                ),
            }
        )

    columns, rows = small.width, small.height
    pixels = list(small.getdata())
    means = [
        sum(pixels[row * columns + col] for row in range(rows)) / float(rows)
        for col in range(columns)
    ]
    if len(means) > 1:
        strongest = max(
            abs(means[index] - means[index - 1]) for index in range(1, len(means))
        )
        if strongest > 55:
            findings.append(
                {
                    "type": "seam_risk",
                    "message": "Sharp tonal boundary across the gutter centre - may show a seam after binding",
                }
            )
    return findings


# ------------------------------------------------------- image processing
def split_spread(image, dpi):
    """Gutter-compensated split: each page keeps 0.125" past the centre so the
    binding absorbs the overlap instead of eating artwork."""
    width, height = image.size
    centre = width // 2
    compensation = max(1, _px(COMP_IN, dpi))
    left = image.crop((0, 0, min(width, centre + compensation), height))
    right = image.crop((max(0, centre - compensation), 0, width, height))
    return left, right


def _fill_bleed_bands(sheet, source, offset_x, offset_y):
    """Fill empty bleed bands by mirroring the adjacent strip, falling back to
    the average colour of that strip when mirroring would show artefacts."""
    band = max(4, min(24, source.width // 40))
    mirror_ok = _strip_contrast(source) < 34
    height = source.height

    def band_piece(width, height_, crop, flip):
        if width <= 0 or height_ <= 0:
            return None
        if mirror_ok:
            return source.crop(crop).transpose(flip).resize(
                (max(1, width), max(1, height_)), RESAMPLE
            )
        return Image.new(
            source.mode, (max(1, width), max(1, height_)), _average_colour(source.crop(crop))
        )

    if offset_x > 0:  # outer bleed on the left (verso)
        piece = band_piece(
            offset_x, height, (0, 0, min(band, source.width), height), FLIP_LR
        )
        if piece:
            sheet.paste(piece, (0, offset_y))
    right_start = offset_x + source.width
    if right_start < sheet.width:  # outer bleed on the right (recto)
        piece = band_piece(
            sheet.width - right_start,
            height,
            (max(0, source.width - band), 0, source.width, height),
            FLIP_LR,
        )
        if piece:
            sheet.paste(piece, (right_start, offset_y))
    if offset_y > 0:  # top bleed
        piece = band_piece(
            sheet.width, offset_y, (0, 0, source.width, min(band, height)), FLIP_TB
        )
        if piece:
            sheet.paste(piece, (0, 0))
    bottom_start = offset_y + height
    if bottom_start < sheet.height:  # bottom bleed
        piece = band_piece(
            sheet.width,
            sheet.height - bottom_start,
            (0, max(0, height - band), source.width, height),
            FLIP_TB,
        )
        if piece:
            sheet.paste(piece, (0, bottom_start))
    return sheet


def page_sheet(source, trim_w, trim_h, dpi, recto):
    """Build one print page: trim + 0.125" outer bleed, spine edge flush.

    Artwork is anchored to the spine edge, so a spread split keeps its 0.125"
    gutter overlap and loses 0.125" of the outer edge instead - the binding
    then absorbs the seam rather than cutting into the picture.
    """
    sheet_w = _px(trim_w + BLEED_IN, dpi)
    sheet_h = _px(trim_h + 2 * BLEED_IN, dpi)
    image = source.convert("RGB")

    if abs(image.height - sheet_h) > 2:
        ratio = sheet_h / float(image.height)
        image = image.resize((max(1, int(image.width * ratio)), sheet_h), RESAMPLE)

    if image.width >= sheet_w - 2:
        if recto:  # spine on the left - keep the leading portion
            return image.crop((0, 0, sheet_w, sheet_h))
        return image.crop((image.width - sheet_w, 0, image.width, sheet_h))

    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    offset_x = 0 if recto else sheet_w - image.width
    sheet.paste(image, (offset_x, 0))
    return _fill_bleed_bands(sheet, image, offset_x, 0)


# ------------------------------------------------------- front matter
def front_matter_pages(meta):
    """Which generated pages lead the book."""
    if not meta or not meta.get("generate", True):
        return []
    pages = []
    if meta.get("include_half_title"):
        pages.append("half_title")
    pages.append("title")
    pages.append("copyright")
    if meta.get("include_dedication") and str(meta.get("dedication") or "").strip():
        pages.append("dedication")
    return pages


def render_front_matter_page(kind, meta, trim_w, trim_h, dpi):
    """Draw a generated front matter page on a full sheet, sized for print."""
    sheet_w = _px(trim_w + BLEED_IN, dpi)
    sheet_h = _px(trim_h + 2 * BLEED_IN, dpi)
    accent = _hex_to_rgb(meta.get("accent_colour"))
    page = Image.new("RGB", (sheet_w, sheet_h), accent)

    luminance = (0.299 * accent[0] + 0.587 * accent[1] + 0.114 * accent[2]) / 255.0
    ink = (255, 255, 255) if luminance < 0.55 else (24, 24, 24)
    draw = ImageDraw.Draw(page)
    bleed_px = _px(BLEED_IN, dpi)
    trim_left = 0 if kind in ("half_title", "title") else bleed_px
    trim_box_width = _px(trim_w, dpi)
    margin = _px(0.75, dpi)
    usable = trim_box_width - 2 * margin
    centre_x = trim_left + (trim_box_width / 2.0)
    centre_y = sheet_h / 2.0

    title = str(meta.get("title") or meta.get("title_text") or "Untitled")
    author = str(meta.get("author") or "")
    illustrator = str(meta.get("illustrator") or "")

    def block(lines, font, leading, start_y):
        y = start_y
        for line in lines:
            draw.text((centre_x, y), line, font=font, fill=ink, anchor="mm")
            y += leading
        return y

    if kind == "half_title":
        font = _load_font(dpi * 0.34)
        lines = _wrap_px(title, font, usable)
        block(lines, font, dpi * 0.42, centre_y - leading_half(len(lines), dpi * 0.42))
    elif kind == "title":
        title_font = _load_font(dpi * 0.4)
        name_font = _load_font(dpi * 0.16, "italic")
        lines = _wrap_px(title, title_font, usable)
        start = sheet_h * 0.30
        y = block(lines, title_font, dpi * 0.5, start)
        if author:
            y = block(["by " + author], name_font, dpi * 0.24, y + dpi * 0.18)
        if illustrator and illustrator != author:
            block(["illustrated by " + illustrator], name_font, dpi * 0.24, y + dpi * 0.06)
    elif kind == "copyright":
        body = _load_font(dpi * 0.115)
        small = _load_font(dpi * 0.1)
        year = meta.get("copyright_year")
        holder = meta.get("copyright_holder") or author
        lines = []
        if year or holder:
            lines.append(
                "Copyright {} {}".format(year or "", holder or "").replace("  ", " ").strip()
            )
        if meta.get("isbn"):
            lines.append("ISBN {}".format(meta["isbn"]))
        lines.append(str(meta.get("publisher") or "D&H Publishing International Ltd"))
        lines.append("Printed and bound by our print partner")
        if meta.get("printer_statement"):
            lines.append(str(meta["printer_statement"]))
        lines.append("All rights reserved.")
        wrapped = []
        for line in lines:
            wrapped.extend(_wrap_px(line, body, usable))
        block(wrapped, body, dpi * 0.19, sheet_h * 0.44)
        block(
            _wrap_px("First edition", small, usable),
            small,
            dpi * 0.17,
            sheet_h * 0.44 + (len(wrapped) * dpi * 0.19) + dpi * 0.12,
        )
    elif kind == "dedication":
        font = _load_font(dpi * 0.19, "italic")
        lines = _wrap_px(meta.get("dedication"), font, usable)
        block(lines, font, dpi * 0.26, centre_y - leading_half(len(lines), dpi * 0.26))
    return page


def leading_half(count, leading):
    return (count - 1) * leading / 2.0


# ------------------------------------------------------- pre-flight checks
def check_image(image, size_bytes, image_format, input_mode, trim_w, trim_h, index):
    checks = []
    pages_wide = 1 if input_mode == "single" else 2
    expected_w = (trim_w * pages_wide) + BLEED_IN
    expected_h = trim_h + 2 * BLEED_IN

    if image_format not in SUPPORTED_FORMATS:
        checks.append(
            {
                "name": "format",
                "status": "fail",
                "message": "Image {}: {} is not supported (JPEG, PNG or TIFF only)".format(
                    index, image_format or "unknown format"
                ),
            }
        )
        return checks

    dpi_x = image.width / max(0.01, trim_w * pages_wide)
    dpi_y = image.height / max(0.01, trim_h)
    dpi = min(dpi_x, dpi_y)
    if dpi >= GOOD_DPI:
        checks.append(
            {"name": "resolution", "status": "pass", "message": "Image {}: {:.0f} DPI".format(index, dpi)}
        )
    elif dpi >= MIN_DPI:
        checks.append(
            {
                "name": "resolution",
                "status": "warn",
                "message": "Image {}: {:.0f} DPI (below the 300 DPI recommendation)".format(index, dpi),
            }
        )
    else:
        checks.append(
            {
                "name": "resolution",
                "status": "fail",
                "message": "Image {}: {:.0f} DPI - below the {:.0f} DPI minimum".format(index, dpi, MIN_DPI),
            }
        )

    width_in = image.width / GOOD_DPI
    height_in = image.height / GOOD_DPI

    def near(a, b):
        return abs(a - b) <= max(0.02, b * 0.01)

    # Bleed may arrive on the outer edge only, symmetrically on both, or - for
    # spreads - not on the outer edges at all, because the split creates it.
    symmetric_bleed = near(width_in, (trim_w * pages_wide) + (2 * BLEED_IN)) and near(
        height_in, trim_h + (2 * BLEED_IN)
    )
    spread_without_outer_bleed = (
        input_mode == "spread"
        and near(width_in, trim_w * pages_wide)
        and near(height_in, trim_h + (2 * BLEED_IN))
    )
    if (near(width_in, expected_w) and near(height_in, expected_h)) or symmetric_bleed:
        checks.append(
            {"name": "dimensions", "status": "pass", "message": "Image {}: matches trim + bleed".format(index)}
        )
    elif spread_without_outer_bleed:
        checks.append(
            {
                "name": "dimensions",
                "status": "pass",
                "message": "Image {}: spread at trim width with top/bottom bleed - the outer bleed is generated when the spread is split".format(index),
            }
        )
    elif near(width_in, trim_w * pages_wide) and near(height_in, trim_h):
        checks.append(
            {
                "name": "dimensions",
                "status": "warn",
                "message": "Image {}: trim size with no bleed - bleed will be generated".format(index),
            }
        )
    elif width_in >= trim_w * pages_wide * 0.98 and height_in >= trim_h * 0.98:
        checks.append(
            {
                "name": "dimensions",
                "status": "warn",
                "message": 'Image {}: {:.2f}" x {:.2f}" - partial bleed, the shortfall will be extended'.format(
                    index, width_in, height_in
                ),
            }
        )
    else:
        checks.append(
            {
                "name": "dimensions",
                "status": "fail",
                "message": 'Image {}: {:.2f}" x {:.2f}" is smaller than the {}" trim size'.format(
                    index, width_in, height_in, trim_w
                ),
            }
        )

    mode = image.mode
    if mode in ("CMYK", "L"):
        checks.append(
            {
                "name": "colour_space",
                "status": "pass",
                "message": "Image {}: {}".format(index, "CMYK" if mode == "CMYK" else "greyscale"),
            }
        )
    elif mode in ("RGB", "RGBA", "LA"):
        checks.append(
            {
                "name": "colour_space",
                "status": "warn",
                "message": "Image {}: RGB - converted for print".format(index),
            }
        )
    else:
        checks.append(
            {
                "name": "colour_space",
                "status": "fail",
                "message": "Image {}: indexed/palette colour is not supported".format(index),
            }
        )

    megabytes = size_bytes / (1024 * 1024)
    if megabytes < 50:
        checks.append(
            {"name": "file_size", "status": "pass", "message": "Image {}: {:.1f} MB".format(index, megabytes)}
        )
    elif megabytes <= MAX_IMAGE_MB:
        checks.append(
            {
                "name": "file_size",
                "status": "warn",
                "message": "Image {}: {:.1f} MB - processing will be slower".format(index, megabytes),
            }
        )
    else:
        checks.append(
            {
                "name": "file_size",
                "status": "fail",
                "message": "Image {}: {:.1f} MB exceeds the {} MB limit".format(index, megabytes, int(MAX_IMAGE_MB)),
            }
        )
    return checks


def summarise(checks):
    """Collapse the per-image checks into one colour-coded row per check."""
    grouped = {}
    for check in checks:
        row = grouped.setdefault(check["name"], {"name": check["name"], "status": "pass", "messages": []})
        if check["status"] == "fail":
            row["status"] = "fail"
        elif check["status"] == "warn" and row["status"] != "fail":
            row["status"] = "warn"
        row["messages"].append(check["message"])
    rows = []
    for row in grouped.values():
        shown = row["messages"][:4]
        row["message"] = " | ".join(shown) + (" ..." if len(row["messages"]) > 4 else "")
        row.pop("messages", None)
        rows.append(row)
    order = {
        "resolution": 0,
        "dimensions": 1,
        "colour_space": 2,
        "format": 3,
        "file_size": 4,
        "consistency": 5,
        "page_count": 6,
        "gutter_content": 7,
    }
    rows.sort(key=lambda row: order.get(row["name"], 99))
    return rows


def run_preflight(req):
    """Validate every supplied image; return the report plus gutter warnings."""
    trim_w, trim_h = _trim_dims(req.get("trim_size"))
    input_mode = req.get("input_mode") or "single"
    images = sorted(req.get("images") or [], key=lambda item: sort_key(item, 0))

    checks, gutter_warnings, sizes, errors = [], [], [], []

    if not images:
        errors.append("No images supplied")

    for index, item in enumerate(images, start=1):
        try:
            image, size_bytes, image_format = load_image(item.get("url"))
        except Exception as error:
            errors.append("Image {}: could not be read ({})".format(index, error))
            continue
        sizes.append(image.size)
        checks.extend(check_image(image, size_bytes, image_format, input_mode, trim_w, trim_h, index))
        for finding in gutter_analysis(image, trim_w, input_mode):
            gutter_warnings.append(
                {"image": index, "type": finding["type"], "message": "Image {}: {}".format(index, finding["message"])}
            )

    content_pages = len(images) * (1 if input_mode == "single" else 2)
    if content_pages % 2 == 0:
        checks.append(
            {
                "name": "page_count",
                "status": "pass",
                "message": "{} content pages (even)".format(content_pages),
            }
        )
    else:
        checks.append(
            {
                "name": "page_count",
                "status": "warn",
                "message": "{} content pages (odd) - a blank page will be added".format(content_pages),
            }
        )
    if 0 < content_pages < KDP_MIN_PAGES:
        checks.append(
            {
                "name": "page_count",
                "status": "warn",
                "message": "KDP paperbacks need at least {} pages".format(KDP_MIN_PAGES),
            }
        )

    if len(sizes) > 1:
        widths = [size[0] for size in sizes]
        heights = [size[1] for size in sizes]
        variation = max(
            (max(widths) - min(widths)) / float(max(widths)),
            (max(heights) - min(heights)) / float(max(heights)),
        )
        if variation <= 0.001:
            checks.append(
                {
                    "name": "consistency",
                    "status": "pass",
                    "message": "All {} images are the same size".format(len(sizes)),
                }
            )
        elif variation <= 0.02:
            checks.append(
                {
                    "name": "consistency",
                    "status": "warn",
                    "message": "Minor size variation across images ({:.1f}%)".format(variation * 100),
                }
            )
        else:
            checks.append(
                {
                    "name": "consistency",
                    "status": "fail",
                    "message": "Major size mismatch across images ({:.0f}%)".format(variation * 100),
                }
            )

    if input_mode == "spread":
        checks.append(
            {
                "name": "gutter_content",
                "status": "warn" if gutter_warnings else "pass",
                "message": "{} gutter warning(s)".format(len(gutter_warnings))
                if gutter_warnings
                else "Centre zone clear on all spreads",
            }
        )

    rows = summarise(checks)
    passed = not any(row["status"] == "fail" for row in rows) and not errors
    return {
        "passed": passed,
        "checks": rows,
        "gutter_warnings": gutter_warnings,
        "content_pages": content_pages,
        "errors": errors,
    }


# ------------------------------------------------------- proof preview
def _watermark(image, text):
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    size = max(16, int(min(image.size) / 22))
    font = _load_font(size, "bold")
    layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)
    draw.text(
        (image.width * 0.02, image.height * 0.5),
        text,
        font=font,
        fill=(190, 30, 40, 110),
    )
    layer = layer.rotate(45, expand=False, resample=ROTATE_RESAMPLE)
    overlay = Image.alpha_composite(overlay, layer)
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def build_preview_pages(sheets, recto_flags, trim_w, trim_h, dpi, watermark_text, page_numbers):
    """Screen-resolution pages, cropped to trim, watermarked for proofing."""
    bleed_px = _px(BLEED_IN, dpi)
    trim_px_w = _px(trim_w, dpi)
    trim_px_h = _px(trim_h, dpi)
    previews = []
    total = len(sheets)
    for index, (sheet, recto) in enumerate(zip(sheets, recto_flags)):
        left = 0 if recto else bleed_px
        trimmed = sheet.crop((left, bleed_px, left + trim_px_w, bleed_px + trim_px_h)).convert("RGB")
        marked = _watermark(trimmed, watermark_text)
        if page_numbers:
            draw = ImageDraw.Draw(marked)
            label = "Page {} of {}".format(index + 1, total)
            font = _load_font(max(10, trim_px_w // 60))
            draw.rectangle((0, marked.height - 26, marked.width, marked.height), fill=(255, 255, 255))
            draw.text((8, marked.height - 24), label, font=font, fill=(70, 70, 70))
        previews.append(marked)
    return previews


# ------------------------------------------------------- job storage
def _prune_jobs():
    now = time.time()
    for job_id, meta in list(JOBS.items()):
        if now - meta.get("created", now) > 6 * 3600:
            JOBS.pop(job_id, None)


def get_picture_book_file(job_id, kind):
    meta = JOBS.get(job_id)
    if not meta:
        return None, None
    path = meta.get("preview") if kind == "preview" else meta.get("print")
    return path, (meta.get("names") or {}).get(kind)


# ------------------------------------------------------- assembly
def assemble_picture_book(req):
    """Assemble the print PDF plus the proof preview and return both URLs."""
    trim_w, trim_h = _trim_dims(req.get("trim_size"))
    input_mode = req.get("input_mode") or "single"
    output = req.get("output") or {}
    front_meta = req.get("front_matter") or {}
    dpi = GOOD_DPI

    report = run_preflight(req)
    if not report["passed"]:
        return {
            "status": "failed",
            "project_id": req.get("project_id"),
            "preflight": report,
            "gutter_warnings": report["gutter_warnings"],
            "message": "Pre-flight found blocking issues - resolve them before assembly.",
        }

    images = sorted(req.get("images") or [], key=lambda item: sort_key(item, 0))

    # Front matter leads the book; pad so page 1 of content falls on a recto.
    front = front_matter_pages(front_meta)
    if front and len(front) % 2 == 1:
        front.append("blank")

    warnings = list(report["gutter_warnings"])
    sheets, recto_flags = [], []

    for kind in front:
        if kind == "blank":
            sheets.append(Image.new("RGB", (_px(trim_w + BLEED_IN, dpi), _px(trim_h + 2 * BLEED_IN, dpi)), (255, 255, 255)))
        else:
            sheets.append(render_front_matter_page(kind, front_meta, trim_w, trim_h, dpi))
        recto_flags.append(len(sheets) % 2 == 1)

    for item in images:
        image, _, _ = load_image(item.get("url"))
        pages = split_spread(image, dpi) if input_mode == "spread" else (image,)
        for page in pages:
            recto = (len(sheets) + 1) % 2 == 1
            sheets.append(page_sheet(page, trim_w, trim_h, dpi, recto))
            recto_flags.append(recto)

    if len(sheets) % 2 == 1:
        sheets.append(Image.new("RGB", (_px(trim_w + BLEED_IN, dpi), _px(trim_h + 2 * BLEED_IN, dpi)), (255, 255, 255)))
        recto_flags.append(False)
        warnings.append(
            {
                "image": 0,
                "type": "blank_page_added",
                "message": "An odd page count was padded with a blank page for print",
            }
        )

    if len(sheets) < KDP_MIN_PAGES:
        warnings.append(
            {
                "image": 0,
                "type": "short_book",
                "message": "Only {} pages - KDP paperbacks need at least {}".format(len(sheets), KDP_MIN_PAGES),
            }
        )

    page_w_pt = (trim_w + BLEED_IN) * 72
    page_h_pt = (trim_h + 2 * BLEED_IN) * 72
    bleed_pt = BLEED_IN * 72

    job_id = "{}-{}".format(req.get("project_id") or "pb", int(time.time()))
    directory = os.path.join(JOB_DIR, job_id)
    os.makedirs(directory, exist_ok=True)
    print_path = os.path.join(directory, "print.pdf")
    preview_path = os.path.join(directory, "preview.pdf")

    # Print PDF: one full-bleed image per page, 0.125" JPEGs, TrimBox set.
    doc = canvas.Canvas(print_path, pagesize=(page_w_pt, page_h_pt))
    doc.setTitle(str(front_meta.get("title") or front_meta.get("title_text") or "Picture Book"))
    doc.setAuthor(str(front_meta.get("author") or ""))
    doc.setCreator("Layout Perfect / D&H Publishing")
    temporary = []
    for sheet, recto in zip(sheets, recto_flags):
        handle = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        handle.close()
        sheet.save(handle.name, "JPEG", quality=92, dpi=(dpi, dpi))
        temporary.append(handle.name)
        doc.drawImage(ImageReader(handle.name), 0, 0, width=page_w_pt, height=page_h_pt, preserveAspectRatio=False)
        trim_x0 = 0 if recto else bleed_pt
        if hasattr(doc, "setTrimBox"):
            doc.setTrimBox((trim_x0, bleed_pt, trim_x0 + trim_w * 72, bleed_pt + trim_h * 72))
        doc.showPage()
    doc.save()

    # Proof preview: screen resolution, cropped to trim, watermarked.
    preview_dpi = float(output.get("preview_dpi") or 100)
    previews = build_preview_pages(
        sheets,
        recto_flags,
        trim_w,
        trim_h,
        dpi,
        output.get("watermark_text") or DEFAULT_WATERMARK,
        bool(output.get("page_numbers")),
    )
    proof = canvas.Canvas(preview_path, pagesize=(trim_w * 72, trim_h * 72))
    for page in previews:
        buffer = io.BytesIO()
        page.save(buffer, "JPEG", quality=80)
        buffer.seek(0)
        proof.drawImage(ImageReader(buffer), 0, 0, width=trim_w * 72, height=trim_h * 72, preserveAspectRatio=False)
        proof.showPage()
    proof.save()

    for path in temporary:
        try:
            os.remove(path)
        except Exception:
            pass

    page_count = len(sheets)
    names = {
        "print": "{}-interior.pdf".format(req.get("project_id") or "picture-book"),
        "preview": "{}-proof.pdf".format(req.get("project_id") or "picture-book"),
    }
    JOBS[job_id] = {"print": print_path, "preview": preview_path, "names": names, "created": time.time()}
    _prune_jobs()

    return {
        "status": "success",
        "project_id": req.get("project_id"),
        "job_id": job_id,
        "page_count": page_count,
        "content_pages": report["content_pages"],
        "front_matter_pages": len(front),
        "spine_width": round(page_count * _spine_per_page(req.get("paper_type")), 5),
        "trim_size": {"width": trim_w, "height": trim_h},
        "preflight": report,
        "gutter_warnings": warnings,
        "outputs": {
            "print_pdf": {
                "url": "/picture-book/download?job={}&kind=print".format(job_id),
                "filename": names["print"],
                "size_mb": round(os.path.getsize(print_path) / (1024 * 1024), 1),
                "pages": page_count,
            },
            "preview_pdf": {
                "url": "/picture-book/download?job={}&kind=preview".format(job_id),
                "filename": names["preview"],
                "size_mb": round(os.path.getsize(preview_path) / (1024 * 1024), 1),
                "pages": len(previews),
            },
        },
    }
