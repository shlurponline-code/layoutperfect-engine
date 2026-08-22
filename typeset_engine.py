#!/usr/bin/env python3
"""
Layout Perfect Typesetting Engine — "From These Streets" Template
=================================================================
Biographical/portrait profile layout for D&H Publishing International.
5.5 x 8.5 inch trim, mirrored margins, warm brown accents, centred folios,
fleuron ornaments, three-dot profile separators, themed chapter openers.
"""

import re, os
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# Supported image formats
SUPPORTED_IMG = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)|]+)(?:\|(\w+))?\)')
CAPTION_SZ_OFFSET = 1.5  # caption is this many pt smaller than body
C_CAPTION = HexColor('#666666')
IMG_SPACING = 0.4 * 72 / 2.54  # 0.4cm in points
CAPTION_GAP = 0.15 * 72 / 2.54  # 0.15cm in points
IMG_HEIGHT_CAP = 0.6  # max 60% of text block height

# ── Dimensions ──────────────────────────────────────────────────────
PAGE_W = 5.5 * inch
PAGE_H = 8.5 * inch
# D&H house margins: 2.54cm top/bottom, 1.54cm left, 1.6cm right, 1cm gutter
# Inside (spine) = left + gutter = 1.54 + 1.0 = 2.54cm = 1.0 inch
# Outside = right = 1.6cm = 0.630 inch
MARGIN_INSIDE  = 1.0 * inch     # 2.54cm (1.54cm + 1cm gutter)
MARGIN_OUTSIDE = 0.630 * inch   # 1.6cm
MARGIN_TOP     = 1.0 * inch     # 2.54cm
MARGIN_BOTTOM  = 1.0 * inch     # 2.54cm
HEADER_Y = PAGE_H - 0.5 * inch
FOOTER_Y = 0.5 * inch

# ── Colours ─────────────────────────────────────────────────────────
C_BODY    = HexColor('#2C2C2C')
C_BROWN   = HexColor('#8B7355')
C_GREY    = HexColor('#999999')
C_MID     = HexColor('#888888')
C_DARK    = HexColor('#4A4A4A')

# ── Fonts ───────────────────────────────────────────────────────────
FD = '/usr/share/fonts/truetype/freefont'
pdfmetrics.registerFont(TTFont('Gar',   f'{FD}/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('GarB',  f'{FD}/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('GarI',  f'{FD}/FreeSerifItalic.ttf'))
pdfmetrics.registerFont(TTFont('GarBI', f'{FD}/FreeSerifBoldItalic.ttf'))
pdfmetrics.registerFontFamily('Gar', normal='Gar', bold='GarB',
                              italic='GarI', boldItalic='GarBI')

BODY_SZ = 10.5
BODY_LD = 14.5
PROF_NAME_SZ = 12.5
PROF_TAG_SZ  = 9.5
CH_TITLE_SZ  = 22
CH_SUB_SZ    = 13
HDR_SZ = 8
FTR_SZ = 9


# ═══════════════════════════════════════════════════════════════════
# PARAGRAPH JOINER — key fix for hard-wrapped markdown
# ═══════════════════════════════════════════════════════════════════

def join_paragraphs(lines):
    """Join hard-wrapped markdown lines into proper paragraphs.
    Paragraphs are separated by blank lines. Special lines (headings,
    separators, ornaments) are kept separate."""
    paragraphs = []
    current = []
    
    for line in lines:
        stripped = line.strip()
        
        # Blank line = paragraph break
        if not stripped:
            if current:
                paragraphs.append(' '.join(current))
                current = []
            continue
        
        # Image references — always their own block
        if IMAGE_PATTERN.match(stripped):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Special markers — always their own block
        if stripped in ('• • •', '❦') or stripped.startswith('--- '):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Headings
        if stripped.startswith('#'):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Bold name lines (profile names like **William Crabtree**)
        if (stripped.startswith('**') and stripped.endswith('**') 
            and len(stripped) < 80 and '\n' not in stripped
            and not stripped.startswith('**FROM')):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Tagline lines (italic dates like *1610--1644 · Broughton · Astronomer*)
        if (stripped.startswith('*') and stripped.endswith('*') 
            and not stripped.startswith('**')
            and '·' in stripped and len(stripped) < 100):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Normal text — accumulate
        current.append(stripped)
    
    if current:
        paragraphs.append(' '.join(current))
    
    return paragraphs


# ═══════════════════════════════════════════════════════════════════
# MANUSCRIPT PARSER
# ═══════════════════════════════════════════════════════════════════

def parse_manuscript(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.read().split('\n')
    
    blocks = []
    
    # ── Locate key sections by line number ──
    # Title page: lines 1-16 (before first ❦)
    blocks.append({'type': 'title_page'})
    
    # Copyright: between second "FROM THESE STREETS" and next ❦
    cp_lines = []
    found_second_title = False
    for j, line in enumerate(raw_lines):
        if j > 15 and '**FROM THESE STREETS**' in line and not found_second_title:
            found_second_title = True
            continue
        if found_second_title:
            if line.strip() == '❦':
                break
            cp_lines.append(line)
    blocks.append({'type': 'copyright_page', 'lines': cp_lines})
    
    # Dedication
    blocks.append({'type': 'dedication_page'})
    
    # Note on Inclusion
    note_lines = []
    in_note = False
    for j, line in enumerate(raw_lines):
        if line.strip() == '**A Note on Inclusion**':
            in_note = True
            continue
        if in_note:
            if line.strip() == '**Contents**':
                break
            note_lines.append(line)
    note_paras = join_paragraphs(note_lines)
    blocks.append({'type': 'note_on_inclusion', 'paras': [p for p in note_paras if p.strip()]})
    
    # TOC placeholder
    blocks.append({'type': 'toc'})
    
    # ── Find Introduction ──
    intro_start = None
    for j, line in enumerate(raw_lines):
        if line.strip() == '# Introduction':
            intro_start = j
            break
    
    if intro_start is None:
        return blocks
    
    # Collect everything from Introduction to end, then parse
    # into chapters, profiles, afterword
    content_lines = raw_lines[intro_start:]
    
    # First join into paragraphs
    paras = join_paragraphs(content_lines)
    
    # Now parse the paragraph stream
    i = 0
    while i < len(paras):
        p = paras[i].strip()
        
        # Chapter heading: # or ##
        if p.startswith('# ') or p.startswith('## '):
            title = p.lstrip('#').strip()
            if title in ('Supplementary Material', 'Further Reading'):
                i += 1
                continue
            
            is_afterword = 'Afterword' in title
            subtitle = ''
            intro = []
            i += 1
            
            # Look for subtitle (italic line with no bold)
            if i < len(paras):
                candidate = paras[i].strip()
                if (candidate.startswith('*') and candidate.endswith('*')
                    and not candidate.startswith('**')):
                    subtitle = candidate.strip('*').strip('\\')
                    i += 1
            
            # Collect intro/body paragraphs
            # For Afterword, collect everything until end markers
            while i < len(paras):
                pp = paras[i].strip()
                if pp.startswith('--- ') or pp == '❦':
                    break
                if not is_afterword:
                    # Normal chapter: stop at first profile marker
                    if (pp == '• • •'
                        or (pp.startswith('**') and pp.endswith('**') and len(pp) < 80
                            and '(' not in pp)):
                        break
                    if pp.startswith('*') and pp.endswith('*') and '·' in pp:
                        break
                else:
                    # Afterword: skip separators but include everything else
                    if pp == '• • •':
                        i += 1
                        continue
                    if pp.startswith('## ') or pp.startswith('# '):
                        break
                intro.append(pp)
                i += 1
            
            blocks.append({
                'type': 'chapter' if not is_afterword else 'afterword',
                'title': title,
                'subtitle': subtitle,
                'intro': intro,
            })
            continue
        
        # Bold section header (chapter-level for later sections)
        if (p.startswith('**The ') and p.endswith('**') and len(p) < 80):
            title = p.strip('*')
            subtitle = ''
            intro = []
            i += 1
            
            if i < len(paras):
                candidate = paras[i].strip()
                if (candidate.startswith('*') and candidate.endswith('*')
                    and not candidate.startswith('**') and '·' not in candidate):
                    subtitle = candidate.strip('*').strip('\\')
                    i += 1
            
            while i < len(paras):
                pp = paras[i].strip()
                if (pp == '• • •' or pp.startswith('--- ') or pp == '❦'
                    or (pp.startswith('**') and pp.endswith('**') and len(pp) < 80)):
                    break
                if pp.startswith('*') and pp.endswith('*') and '·' in pp:
                    break
                intro.append(pp)
                i += 1
            
            blocks.append({
                'type': 'chapter',
                'title': title,
                'subtitle': subtitle,
                'intro': intro,
            })
            continue
        
        # Profile separator
        if p == '• • •':
            i += 1
            continue
        
        # Profile name — but NOT inline bold names in Afterword body,
        # and NOT the back page URL or other non-profile bold text
        if (p.startswith('**') and p.endswith('**') and len(p) < 80
            and not p.startswith('**FROM') and not p.startswith('**A Note')
            and not p.startswith('**Contents')
            and not p.startswith('**www.')
            and '(' not in p):  # Afterword inline profiles have (dates) after
            name = p.strip('*')
            tagline = ''
            body = []
            i += 1
            
            # Tagline
            if i < len(paras):
                candidate = paras[i].strip()
                if (candidate.startswith('*') and candidate.endswith('*')
                    and not candidate.startswith('**') and '·' in candidate):
                    tagline = candidate.strip('*').strip('\\')
                    i += 1
            
            # Body paragraphs
            while i < len(paras):
                pp = paras[i].strip()
                if (pp == '• • •' or pp.startswith('--- ') or pp == '❦'
                    or (pp.startswith('**') and pp.endswith('**') and len(pp) < 80)
                    or pp.startswith('# ') or pp.startswith('## ')):
                    break
                body.append(pp)
                i += 1
            
            blocks.append({
                'type': 'profile',
                'name': name,
                'tagline': tagline,
                'body': body,
            })
            continue
        
        # End markers — skip
        if p.startswith('--- ') or p == '❦':
            i += 1
            continue
        
        # Stray text (e.g. appendix placeholders, back page)
        i += 1
    
    return blocks


def parse_manuscript_generic(filepath):
    """Generic parser for novels, non-fiction, and any standard markdown manuscript.
    Handles: # Part, # Chapter, ## Subtitle, body text, scene breaks (*** ---),
    and back matter (Author's Note, Acknowledgements, About, etc.)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.read().split('\n')
    
    paras = join_paragraphs(raw_lines)
    blocks = []
    i = 0
    
    while i < len(paras):
        p = paras[i].strip()
        if not p:
            i += 1
            continue
        
        # # Heading (Part, Chapter, Prologue, Epilogue, back matter)
        if p.startswith('# '):
            title = p[2:].strip()
            subtitle = ''
            body = []
            i += 1
            
            # Check for ## subtitle
            if i < len(paras) and paras[i].strip().startswith('## '):
                subtitle = paras[i].strip()[3:].strip()
                i += 1
            
            # Collect body until next # heading
            while i < len(paras):
                pp = paras[i].strip()
                if pp.startswith('# '):
                    break
                if pp in ('***', '* * *') or (len(pp) >= 3 and all(c == '-' for c in pp)):
                    body.append({'type': 'scene_break'})
                    i += 1
                    continue
                if IMAGE_PATTERN.match(pp):
                    body.append({'type': 'image', 'text': pp})
                    i += 1
                    continue
                body.append({'type': 'para', 'text': pp})
                i += 1
            
            # Part headings typically have no body (just a title page)
            is_part = (title.lower().startswith('part ') and len(body) == 0)
            
            blocks.append({
                'type': 'part' if is_part else 'chapter',
                'title': title,
                'subtitle': subtitle,
                'body': body,
            })
            continue
        
        # ## Heading without parent #
        if p.startswith('## '):
            title = p[3:].strip()
            body = []
            i += 1
            while i < len(paras):
                pp = paras[i].strip()
                if pp.startswith('# ') or pp.startswith('## '):
                    break
                if pp in ('***', '* * *') or (len(pp) >= 3 and all(c == '-' for c in pp)):
                    body.append({'type': 'scene_break'})
                    i += 1
                    continue
                if IMAGE_PATTERN.match(pp):
                    body.append({'type': 'image', 'text': pp})
                    i += 1
                    continue
                body.append({'type': 'para', 'text': pp})
                i += 1
            blocks.append({
                'type': 'chapter', 'title': title,
                'subtitle': '', 'body': body,
            })
            continue
        
        i += 1
    
    return blocks


# ═══════════════════════════════════════════════════════════════════
# GENERIC BOOK BUILDER — works with any manuscript structure
# ═══════════════════════════════════════════════════════════════════

class GenericBookBuilder:
    """Builds print-ready PDFs from any markdown manuscript.
    Uses parse_manuscript_generic for structure detection."""
    
    def __init__(self, md_path, output_path, title='Untitled', author='Unknown',
                 subtitle='', publisher='D&H Publishing International',
                 publisher_url='www.dandhpublishing.com'):
        self.md_path = md_path
        self.output_path = output_path
        self.title = title
        self.subtitle = subtitle
        self.author = author
        self.publisher = publisher
        self.publisher_url = publisher_url
        self.blocks = parse_manuscript_generic(md_path)
        self.image_base_dir = os.path.dirname(os.path.abspath(md_path))
    
    def _render(self, path, toc_entries=None):
        r = BookRenderer(path)
        r.image_base_dir = self.image_base_dir
        r.header_text = self.title
        
        # ── Front matter (generic, driven by title/author) ──
        # Title page
        r._new_page(suppress=True)
        y = PAGE_H - 2.2 * inch
        
        # Auto-size title to fit within page margins
        # Start at 42pt, reduce until it fits (single or multi-line)
        tw = r._tw()
        title_sz = 42
        title_lines = [self.title]
        
        while title_sz >= 18:
            r.c.setFont('GarB', title_sz)
            single_w = r.c.stringWidth(self.title, 'GarB', title_sz)
            
            if single_w <= tw:
                # Fits on one line
                title_lines = [self.title]
                break
            
            # Try splitting into two lines
            words = self.title.split()
            best_split = None
            best_max_w = single_w
            for split_at in range(1, len(words)):
                line1 = ' '.join(words[:split_at])
                line2 = ' '.join(words[split_at:])
                w1 = r.c.stringWidth(line1, 'GarB', title_sz)
                w2 = r.c.stringWidth(line2, 'GarB', title_sz)
                max_w = max(w1, w2)
                if max_w < best_max_w:
                    best_max_w = max_w
                    best_split = (line1, line2)
            
            if best_split and best_max_w <= tw:
                title_lines = [best_split[0], best_split[1]]
                break
            
            title_sz -= 2
        
        # Render title lines
        for tl in title_lines:
            r._ctxt(y, tl, 'GarB', title_sz, C_BODY)
            y -= title_sz + 8
        
        y -= 8
        
        # Subtitle (if provided)
        if self.subtitle:
            # Auto-size subtitle too
            sub_sz = 16
            while sub_sz >= 10:
                if r.c.stringWidth(self.subtitle, 'GarI', sub_sz) <= tw:
                    break
                sub_sz -= 1
            r._ctxt(y, self.subtitle, 'GarI', sub_sz, C_BROWN)
            y -= sub_sz + 14
        
        r._divider(y, 'star'); y -= 35
        r._ctxt(y, self.author, 'GarI', 14, C_DARK); y -= 35
        r._divider(y, 'star'); y -= 50
        r._ctxt(y, 'published by:', 'Gar', 9, C_DARK); y -= 18
        r._ctxt(y, self.publisher, 'Gar', 11, C_BODY); y -= 35
        r._ornament(y)
        r._finish_page()
        
        # Blank verso
        r._new_page(suppress=True)
        r._finish_page()
        
        # Copyright page
        r._new_page(suppress=True)
        y = PAGE_H - 2.0 * inch
        r._ctxt(y, self.title, 'GarB', 14, C_BODY); y -= 20
        r._ctxt(y, self.author, 'GarI', 11, C_BROWN); y -= 30
        lm = r._lm()
        for line in [
            f'First published in 2026 by {self.publisher}.',
            f'\u00a9 2026 {self.author}. All rights reserved.',
            '',
            'No part of this publication may be reproduced, distributed, or transmitted '
            'in any form or by any means, including photocopying, recording, or other '
            'electronic or mechanical methods, without the prior written permission of '
            'the publisher, except in the case of brief quotations embodied in critical '
            'reviews and certain other non-commercial uses permitted by copyright law.',
            '',
            f'{self.publisher_url}',
        ]:
            if not line:
                y -= 8
                continue
            wrapped = r._wrap(line, 'Gar', 9.5, r._tw())
            for wl in wrapped:
                if y < MARGIN_BOTTOM + 30:
                    break
                r.c.setFont('Gar', 9.5)
                r.c.setFillColor(C_BODY)
                if line == self.publisher_url:
                    r.c.drawCentredString(PAGE_W / 2, y, wl)
                else:
                    r.c.drawString(lm, y, wl)
                y -= 13
            y -= 3
        y -= 10
        r._ornament(y)
        r._finish_page()
        
        # TOC placeholder or real TOC
        if toc_entries:
            r.render_toc(toc_entries)
        else:
            r._ensure_recto()
            r._ctxt(PAGE_H - MARGIN_TOP - 30, 'Contents', 'GarB', 22, C_BODY)
            r._finish_page()
            r._new_page(suppress=True)
            r._finish_page()
        
        # ── Body content ──
        for i, blk in enumerate(self.blocks):
            t = blk['type']
            
            if t == 'part':
                # Part title page — centred, recto, no body text
                r._ensure_recto()
                r.is_front_matter = False
                r.toc_entries.append((blk['title'], r.page_num, 0))
                y = PAGE_H / 2 + 30
                r._ctxt(y, blk['title'].upper(), 'GarB', 24, C_BODY)
                if blk.get('subtitle'):
                    y -= 28
                    r._ctxt(y, blk['subtitle'], 'GarI', 14, C_BROWN)
                r._finish_page()
            
            elif t == 'chapter':
                # Build TOC entry with subtitle if available
                toc_title = blk['title']
                if blk.get('subtitle'):
                    toc_title = f"{blk['title']}: {blk['subtitle']}"
                r.toc_entries.append((toc_title, r.page_num + 1, 1 if any(
                    b['type'] == 'part' for b in self.blocks[:i]) else 0))
                r.render_chapter_opener(blk['title'], blk.get('subtitle', ''))
                
                # Render body content
                for item in blk.get('body', []):
                    if item['type'] == 'para':
                        r._draw_content(item['text'])
                    elif item['type'] == 'scene_break':
                        r._check_page(40)
                        r.current_y -= 12
                        r._ctxt(r.current_y, '•   •   •', 'Gar', 10, C_MID)
                        r.current_y -= 20
                    elif item['type'] == 'image':
                        r._draw_content(item['text'])
                
                # Chapter end divider if next block is a part or it's the last
                if i + 1 < len(self.blocks):
                    nt = self.blocks[i + 1]['type']
                    if nt == 'part':
                        r.render_chapter_end()
                if i == len(self.blocks) - 1:
                    r.render_chapter_end()
        
        # ── Back page ──
        r._ensure_recto()
        y = PAGE_H / 2 + 20
        r._ctxt(y, self.publisher_url, 'GarB', 13, C_BODY); y -= 22
        r._ctxt(y, self.title, 'GarI', 11, C_DARK); y -= 30
        r._divider(y, 'star'); y -= 25
        r._ctxt(y, self.publisher, 'Gar', 10, C_DARK); y -= 18
        r.c.setFont('Gar', 8.5)
        r.c.setFillColor(C_GREY)
        r.c.drawCentredString(PAGE_W / 2, y,
                             f'\u00a9 2026 {self.author}. All rights reserved.')
        r._finish_page()
        
        r.c.save()
        self._last_image_log = r.image_log
        return r.toc_entries
    
    def build(self):
        print(f"Building: {self.title} by {self.author}")
        print("Pass 1: Collecting page numbers...")
        tmp = self.output_path.replace('.pdf', '_p1.pdf')
        toc = self._render(tmp)
        print(f"  {len(toc)} TOC entries")
        
        print("Pass 2: Final render with TOC...")
        self._render(self.output_path, toc)
        if os.path.exists(tmp):
            os.remove(tmp)
        
        self._set_trimbox()
        
        if self._last_image_log:
            print(f"\nIMAGES")
            print(f"------")
            placed = warnings = errors = 0
            for fname, page, hint, dpi, status in self._last_image_log:
                if status == 'OK':
                    print(f"  {fname:40s} placed p.{page} ({hint}, {dpi} DPI) \u2713")
                    placed += 1
                elif status == 'LOW RES':
                    print(f"  {fname:40s} placed p.{page} ({hint}, {dpi} DPI) \u26a0 LOW RES")
                    placed += 1; warnings += 1
                else:
                    print(f"  {fname:40s} {status} \u2717")
                    errors += 1
            print(f"\n  Total: {len(self._last_image_log)}, Placed: {placed}, Warnings: {warnings}, Errors: {errors}")
        
        print(f"Done: {self.output_path}")
        return self.output_path
    
    def _set_trimbox(self):
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, FloatObject, NameObject
        reader = PdfReader(self.output_path)
        writer = PdfWriter()
        for page in reader.pages:
            page[NameObject('/TrimBox')] = ArrayObject([
                FloatObject(0), FloatObject(0),
                FloatObject(PAGE_W), FloatObject(PAGE_H),
            ])
            writer.add_page(page)
        writer.add_metadata({
            '/Title': self.title,
            '/Author': self.author,
            '/Creator': 'Layout Perfect Typesetting Engine',
            '/Producer': 'ReportLab + pypdf',
        })
        with open(self.output_path, 'wb') as f:
            writer.write(f)

class BookRenderer:
    def __init__(self, output_path):
        self.c = canvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))
        self.c.setTitle("From These Streets")
        self.c.setAuthor("David Oldham")
        self.page_num = 0
        self.toc_entries = []
        self.suppress_hdr = False
        self.is_front_matter = True  # suppress folios in front matter
        self.current_y = PAGE_H - MARGIN_TOP - 10
        self.output_path = output_path
        self.image_base_dir = ''  # set by BookBuilder
        self.image_log = []  # [(filename, page, size_hint, dpi, status)]
        self.header_text = ''  # set by builder — used in running header
        
    def _margins(self):
        if self.page_num % 2 == 1:  # Recto: gutter left
            return MARGIN_INSIDE, MARGIN_OUTSIDE
        return MARGIN_OUTSIDE, MARGIN_INSIDE
    
    def _tw(self):
        l, r = self._margins()
        return PAGE_W - l - r
    
    def _lm(self):
        return self._margins()[0]
    
    def _draw_header(self):
        if self.suppress_hdr or self.is_front_matter:
            return
        txt = self.header_text or 'Layout Perfect'
        self.c.setFont('GarI', HDR_SZ)
        self.c.setFillColor(C_GREY)
        self.c.drawCentredString(PAGE_W/2, HEADER_Y, txt)
        self.c.setStrokeColor(HexColor('#D0C8B8'))
        self.c.setLineWidth(0.3)
        l, r = self._margins()
        self.c.line(l, HEADER_Y - 6, PAGE_W - r, HEADER_Y - 6)
    
    def _draw_folio(self):
        if self.is_front_matter:
            return
        if getattr(self, '_suppress_folio_this_page', False):
            self._suppress_folio_this_page = False
            return
        self.c.setFont('Gar', FTR_SZ)
        self.c.setFillColor(C_GREY)
        self.c.drawCentredString(PAGE_W/2, FOOTER_Y, str(self.page_num))
    
    def _new_page(self, suppress=False):
        if self.page_num > 0:
            self.c.showPage()
        self.page_num += 1
        self.suppress_hdr = suppress
        self.current_y = PAGE_H - MARGIN_TOP - 10
    
    def _finish_page(self):
        self._draw_header()
        self._draw_folio()
    
    def _ensure_recto(self):
        """Finish current page and ensure next is recto (odd)."""
        self._finish_page()
        if self.page_num % 2 == 0:  # on verso, add blank recto? No — need blank verso
            # Actually: if on even page (verso), next page is odd (recto) — good
            pass
        else:
            # On odd (recto), need to add a blank verso first
            self._new_page(suppress=True)
            self._draw_folio()
            self._finish_page()
        self._new_page(suppress=True)
    
    def _ctxt(self, y, text, font, sz, color=C_BODY):
        self.c.setFont(font, sz)
        self.c.setFillColor(color)
        self.c.drawCentredString(PAGE_W/2, y, text)
    
    def _ornament(self, y, ch='❦', sz=18, color=C_BROWN):
        self._ctxt(y, ch, 'Gar', sz, color)
    
    def _divider(self, y, style='end'):
        ch = '✻' if style == 'star' else '❧'
        self._ctxt(y, f'— {ch} —', 'Gar', 16, C_BROWN)
    
    def _dot_sep(self, y):
        self._ctxt(y, '•   •   •', 'Gar', 10, C_MID)
        return y - 8
    
    def _wrap(self, text, font, sz, max_w):
        self.c.setFont(font, sz)
        words = text.split()
        lines = []
        cur = ''
        for w in words:
            test = f'{cur} {w}'.strip()
            if self.c.stringWidth(test, font, sz) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines or ['']
    
    def _check_page(self, needed=20):
        """If not enough room, finish page and start new one."""
        if self.current_y < MARGIN_BOTTOM + needed:
            self._finish_page()
            self._new_page()
            self.current_y = PAGE_H - MARGIN_TOP - 10
    
    def _draw_para(self, text, centered=False, font='Gar', sz=BODY_SZ, 
                   leading=BODY_LD, color=C_BODY, indent=0):
        """Draw a wrapped paragraph. Updates self.current_y."""
        # Strip remaining markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # italic
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # links
        text = text.replace('\\"', '"').replace("\\'", "'")
        
        # Word-wrap using the NARROWER margin to be safe across page breaks
        # (inside margin is wider than outside, giving a narrower text width)
        min_tw = PAGE_W - MARGIN_INSIDE - MARGIN_OUTSIDE  # narrowest possible
        lines = self._wrap(text, font, sz, min_tw - indent)
        
        for line_text in lines:
            self._check_page()
            # Recalculate margins fresh for CURRENT page after any page break
            lm = self._lm() + indent
            self.c.setFont(font, sz)
            self.c.setFillColor(color)
            if centered:
                self.c.drawCentredString(PAGE_W/2, self.current_y, line_text)
            else:
                self.c.drawString(lm, self.current_y, line_text)
            self.current_y -= leading
        
        self.current_y -= 2  # paragraph gap
    
    def _draw_image(self, caption, img_path, size_hint='full'):
        """Render an image with caption. Supports six placement modes:
        full    — spans text width, inline in flow (default)
        half    — half text width, centred, inline
        quarter — quarter text width, centred, inline
        page    — full page, no header/folio, caption overlaid at bottom
        bleed   — edge-to-edge, no margins/header/folio
        facing  — full page on next recto/verso to face the text
        """
        # Resolve path
        full_path = os.path.join(self.image_base_dir, img_path) if self.image_base_dir else img_path
        
        # Check file exists
        if not os.path.exists(full_path):
            self._check_page(30)
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(HexColor('#CC0000'))
            self.c.drawString(lm, self.current_y, f'[IMAGE NOT FOUND: {img_path}]')
            self.current_y -= BODY_LD
            self.image_log.append((img_path, self.page_num, size_hint, 0, 'NOT FOUND'))
            return
        
        # Check format
        ext = os.path.splitext(full_path)[1].lower()
        if ext not in SUPPORTED_IMG:
            self._check_page(30)
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(HexColor('#CC0000'))
            self.c.drawString(lm, self.current_y, f'[UNSUPPORTED FORMAT: {img_path} — use JPG, PNG or TIFF]')
            self.current_y -= BODY_LD
            self.image_log.append((img_path, self.page_num, size_hint, 0, 'UNSUPPORTED'))
            return
        
        # Read image dimensions
        try:
            img_reader = ImageReader(full_path)
            native_w, native_h = img_reader.getSize()
        except Exception as e:
            self._check_page(30)
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(HexColor('#CC0000'))
            self.c.drawString(lm, self.current_y, f'[IMAGE ERROR: {img_path} — {str(e)}]')
            self.current_y -= BODY_LD
            self.image_log.append((img_path, self.page_num, size_hint, 0, 'ERROR'))
            return
        
        # ── FULL PAGE mode ──
        if size_hint == 'page':
            self._draw_image_page(full_path, caption, native_w, native_h, bleed=False)
            return
        
        # ── BLEED mode (edge to edge, no margins) ──
        if size_hint == 'bleed':
            self._draw_image_page(full_path, caption, native_w, native_h, bleed=True)
            return
        
        # ── FACING mode (full page on facing page) ──
        if size_hint == 'facing':
            self._draw_image_facing(full_path, caption, native_w, native_h)
            return
        
        # ── INLINE modes (full, half, quarter) ──
        tw = self._tw()
        text_height = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
        
        if size_hint == 'half':
            target_w = tw / 2
        elif size_hint == 'quarter':
            target_w = tw / 4
        else:  # full
            target_w = tw
        
        # Scale maintaining aspect ratio
        scale = target_w / native_w
        render_w = target_w
        render_h = native_h * scale
        
        # Height cap at 60% of text block
        max_h = text_height * IMG_HEIGHT_CAP
        if render_h > max_h:
            render_h = max_h
            render_w = native_w * (max_h / native_h)
        
        # DPI check
        render_w_inches = render_w / 72
        effective_dpi = native_w / render_w_inches if render_w_inches > 0 else 0
        dpi_status = 'OK'
        if effective_dpi < 200:
            dpi_status = 'LOW RES'
            print(f"WARNING: {img_path} will print at {effective_dpi:.0f} DPI — minimum recommended is 300 DPI")
        
        # Calculate caption height
        caption_sz = BODY_SZ - CAPTION_SZ_OFFSET
        caption_lines = self._wrap(caption, 'GarI', caption_sz, render_w) if caption else []
        caption_height = len(caption_lines) * (caption_sz + 2) + CAPTION_GAP if caption_lines else 0
        
        # Total space needed
        total_needed = IMG_SPACING + render_h + caption_height + IMG_SPACING
        
        # Check if it fits on current page
        if self.current_y - total_needed < MARGIN_BOTTOM:
            self._finish_page()
            self._new_page()
            self.current_y = PAGE_H - MARGIN_TOP - 10
        
        # Top spacing
        self.current_y -= IMG_SPACING
        
        # Draw image centred
        lm = self._lm()
        img_x = lm + (tw - render_w) / 2
        img_y = self.current_y - render_h
        
        self.c.drawImage(full_path, img_x, img_y, render_w, render_h,
                        preserveAspectRatio=True, anchor='c')
        self.current_y = img_y
        
        # Draw caption
        if caption_lines:
            self.current_y -= CAPTION_GAP
            self.c.setFont('GarI', caption_sz)
            self.c.setFillColor(C_CAPTION)
            cap_x = lm + (tw - render_w) / 2 + render_w / 2
            for cap_line in caption_lines:
                self.c.drawCentredString(cap_x, self.current_y, cap_line)
                self.current_y -= (caption_sz + 2)
        
        # Bottom spacing
        self.current_y -= IMG_SPACING
        
        self.image_log.append((img_path, self.page_num, size_hint,
                              round(effective_dpi), dpi_status))
    
    def _draw_image_page(self, full_path, caption, native_w, native_h, bleed=False):
        """Render a full-page image. No running header, no folio.
        If bleed=True, image extends to page edges (trimmed at TrimBox).
        If bleed=False, image fills within margins."""
        
        # Finish current page if we have content on it
        if self.current_y < PAGE_H - MARGIN_TOP - 20:
            self._finish_page()
        else:
            # We're at the top of a fresh page already — just need to
            # suppress the header that _finish_page would draw
            pass
        
        # Start a dedicated image page — suppress header and folio
        self._new_page(suppress=True)
        self._suppress_folio_this_page = True
        
        if bleed:
            # Edge to edge — fill entire page
            target_w = PAGE_W
            target_h = PAGE_H
        else:
            # Within margins
            target_w = self._tw()
            target_h = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
        
        # Scale to cover the target area (cover fit, may crop)
        scale_w = target_w / native_w
        scale_h = target_h / native_h
        scale = max(scale_w, scale_h)  # cover fit
        render_w = native_w * scale
        render_h = native_h * scale
        
        # Centre the image
        if bleed:
            img_x = (PAGE_W - render_w) / 2
            img_y = (PAGE_H - render_h) / 2
        else:
            lm = self._lm()
            tw = self._tw()
            img_x = lm + (tw - render_w) / 2
            img_y = MARGIN_BOTTOM + (target_h - render_h) / 2
        
        # Clip to target area and draw image
        self.c.saveState()
        if bleed:
            p = self.c.beginPath()
            p.rect(0, 0, PAGE_W, PAGE_H)
            self.c.clipPath(p, stroke=0, fill=0)
        else:
            lm = self._lm()
            p = self.c.beginPath()
            p.rect(lm, MARGIN_BOTTOM, self._tw(), target_h)
            self.c.clipPath(p, stroke=0, fill=0)
        
        self.c.drawImage(full_path, img_x, img_y, render_w, render_h,
                        preserveAspectRatio=False)
        self.c.restoreState()
        
        # Caption overlay at bottom (semi-transparent background)
        if caption:
            caption_sz = BODY_SZ - CAPTION_SZ_OFFSET
            cap_lines = self._wrap(caption, 'GarI', caption_sz, self._tw() * 0.8)
            if cap_lines:
                cap_h = len(cap_lines) * (caption_sz + 3) + 12
                cap_y_start = MARGIN_BOTTOM + 15 if not bleed else 20
                
                # Semi-transparent background for readability
                self.c.setFillColor(HexColor('#00000080'))
                bg_x = PAGE_W / 2 - self._tw() * 0.42
                self.c.rect(bg_x, cap_y_start - 4, self._tw() * 0.84, cap_h,
                           stroke=0, fill=1)
                
                self.c.setFont('GarI', caption_sz)
                self.c.setFillColor(HexColor('#FFFFFF'))
                cy = cap_y_start + cap_h - (caption_sz + 3) - 4
                for cap_line in cap_lines:
                    self.c.drawCentredString(PAGE_W / 2, cy, cap_line)
                    cy -= (caption_sz + 3)
        
        # DPI check
        render_w_inches = render_w / 72
        effective_dpi = native_w / render_w_inches if render_w_inches > 0 else 0
        dpi_status = 'OK'
        if effective_dpi < 200:
            dpi_status = 'LOW RES'
            print(f"WARNING: {os.path.basename(full_path)} will print at {effective_dpi:.0f} DPI")
        
        mode_str = 'bleed' if bleed else 'page'
        self.image_log.append((os.path.basename(full_path), self.page_num,
                              mode_str, round(effective_dpi), dpi_status))
        
        # This image page is complete — start a fresh page for following text
        # (no header/folio on the image page since suppress_hdr is True
        # and _suppress_folio_this_page is True)
        self._finish_page()
        self._new_page()
        self.current_y = PAGE_H - MARGIN_TOP - 10
    
    def _draw_image_facing(self, full_path, caption, native_w, native_h):
        """Place a full-page image on the next page so it faces the current text.
        The image goes on the next verso (left page) if we're on a recto,
        or next recto (right page) if we're on a verso, so it faces the text."""
        
        # Finish the current text page
        self._finish_page()
        
        # If we're on a recto (odd), the facing page is the next verso (even)
        # If we're on a verso (even), we need to add a blank recto first,
        # then the image goes on the following verso
        if self.page_num % 2 == 0:
            # Currently on verso — add blank recto, then image on next verso
            self._new_page(suppress=True)
            self._draw_folio()
            self._finish_page()
        
        # Now render the image as a full page
        self._draw_image_page(full_path, caption, native_w, native_h, bleed=False)
    
    def _draw_drop_cap(self, text, cap_lines=3):
        """Render the first letter of text as a drop cap spanning cap_lines lines.
        Used for children's book and novel chapter openers."""
        if not text or len(text) < 2:
            self._draw_para(text)
            return
        
        # Strip markdown
        clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        clean = re.sub(r'\*([^*]+)\*', r'\1', clean)
        clean = clean.replace('\\"', '"').replace("\\'", "'")
        
        if not clean:
            return
        
        self._check_page(60)
        
        first_char = clean[0]
        rest_text = clean[1:].strip()
        
        lm = self._lm()
        tw = self._tw()
        
        # Drop cap sizing: spans cap_lines of body text
        drop_sz = BODY_SZ * cap_lines * 0.85
        drop_leading = BODY_LD * cap_lines
        
        # Measure the drop cap width
        self.c.setFont('GarB', drop_sz)
        drop_w = self.c.stringWidth(first_char, 'GarB', drop_sz) + 4  # 4pt gap
        
        # Draw the drop cap
        drop_y = self.current_y - (drop_sz * 0.72)  # baseline offset
        self.c.setFillColor(C_BROWN)
        self.c.drawString(lm, drop_y, first_char)
        
        # Draw the first few lines of text indented around the drop cap
        indent_tw = tw - drop_w
        indent_lm = lm + drop_w
        
        # Wrap text for the indented region
        min_tw_safe = PAGE_W - MARGIN_INSIDE - MARGIN_OUTSIDE
        indent_lines = self._wrap(rest_text, 'Gar', BODY_SZ, 
                                  min(indent_tw, min_tw_safe - drop_w))
        
        # Draw lines next to the drop cap
        lines_beside = min(cap_lines, len(indent_lines))
        for j in range(lines_beside):
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(C_BODY)
            self.c.drawString(indent_lm, self.current_y, indent_lines[j])
            self.current_y -= BODY_LD
        
        # Remaining lines at full width
        for j in range(lines_beside, len(indent_lines)):
            self._check_page()
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(C_BODY)
            self.c.drawString(lm, self.current_y, indent_lines[j])
            self.current_y -= BODY_LD
        
        self.current_y -= 2
    
    def _draw_content(self, text):
        """Route content: render as image if it's an image reference, otherwise as paragraph."""
        m = IMAGE_PATTERN.match(text.strip())
        if m:
            caption = m.group(1)
            img_path = m.group(2)
            size_hint = m.group(3) or 'full'
            self._draw_image(caption, img_path, size_hint)
        else:
            self._draw_para(text)
    
    # ═══════════════════════════════════════════════════════════════
    # PAGE TYPES
    # ═══════════════════════════════════════════════════════════════
    
    def render_title(self):
        self._new_page(suppress=True)
        y = PAGE_H - 2.2*inch
        self._ctxt(y, 'FROM THESE', 'GarB', 42, C_BODY); y -= 50
        self._ctxt(y, 'STREETS', 'GarB', 42, C_BODY); y -= 40
        self._divider(y, 'star'); y -= 30
        self._ctxt(y, 'Salfordians who Changed the World', 'GarI', 14, C_BROWN); y -= 30
        self._divider(y, 'star'); y -= 50
        self._ctxt(y, 'David Oldham', 'GarI', 12, C_DARK); y -= 40
        self._ctxt(y, 'published by:', 'Gar', 9, C_DARK); y -= 18
        self._ctxt(y, 'D&H Publishing International', 'Gar', 11, C_BODY); y -= 35
        self._ornament(y)
        self._finish_page()
    
    def render_copyright(self, lines):
        self._new_page(suppress=True)
        y = PAGE_H - 2.0*inch
        self._ctxt(y, 'FROM THESE STREETS', 'GarB', 14, C_BODY); y -= 20
        self._ctxt(y, 'Salfordians who Changed the World', 'GarI', 11, C_BROWN); y -= 30
        
        # Join the copyright lines into paragraphs
        paras = join_paragraphs(lines)
        lm = self._lm()
        tw = self._tw()
        
        for para in paras:
            para = para.strip()
            if not para:
                continue
            # Clean markdown artifacts
            para = re.sub(r'\*([^*]+)\*', r'\1', para)
            para = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', para)
            
            centered_markers = ['Paperback', 'www.']
            is_centered = any(m in para for m in centered_markers)
            
            wrapped = self._wrap(para, 'Gar', 9.5, tw)
            for wl in wrapped:
                if y < MARGIN_BOTTOM + 30:
                    break
                self.c.setFont('Gar', 9.5)
                self.c.setFillColor(C_BODY)
                if is_centered:
                    self.c.drawCentredString(PAGE_W/2, y, wl)
                else:
                    self.c.drawString(lm, y, wl)
                y -= 13
            y -= 5
        
        y -= 10
        self._ornament(y)
        self._finish_page()
    
    def render_dedication(self):
        self._ensure_recto()
        y = PAGE_H/2 + 30
        self.c.setFont('GarI', 12)
        self.c.setFillColor(C_DARK)
        self.c.drawCentredString(PAGE_W/2, y, '"For anyone who\'s ever said:')
        y -= 18
        self.c.drawCentredString(PAGE_W/2, y, 'I\'m not from Manchester, I\'m from Salford."')
        self._finish_page()
    
    def render_note(self, paras):
        self._ensure_recto()
        self.current_y = PAGE_H - MARGIN_TOP - 40
        self._ctxt(self.current_y, 'A Note on Inclusion', 'GarB', 14, C_BODY)
        self.current_y -= 28
        for para in paras:
            self._draw_para(para)
        self._finish_page()
    
    def render_toc(self, entries):
        self._ensure_recto()
        self.current_y = PAGE_H - MARGIN_TOP - 30
        self._ctxt(self.current_y, 'Contents', 'GarB', 22, C_BODY)
        self.current_y -= 40

        lm = self._lm()
        tw = self._tw()

        # Reserve space for page number on the right (e.g. "210" max width)
        pg_num_reserve = 28  # points — enough for a 3-digit page number
        title_max_w = tw - pg_num_reserve - 12  # 12pt gap between title and leaders

        for title, page, level in entries:
            if level == 0:
                font, sz = 'GarB', 11
                indent = 0
                line_h = 16
                pre_gap = 6
            else:
                font, sz = 'Gar', 10
                indent = 18
                line_h = 14
                pre_gap = 0

            self.c.setFont(font, sz)

            pg_str = str(page)
            x_start = lm + indent
            x_end = lm + tw

            # Wrap title into lines that fit within title_max_w
            max_title_w = title_max_w - indent
            words = title.split()
            wrapped_lines = []
            current_line = ''
            for word in words:
                test = (current_line + ' ' + word).strip()
                if self.c.stringWidth(test, font, sz) <= max_title_w:
                    current_line = test
                else:
                    if current_line:
                        wrapped_lines.append(current_line)
                    current_line = word
            if current_line:
                wrapped_lines.append(current_line)
            if not wrapped_lines:
                wrapped_lines = [title]

            total_h = len(wrapped_lines) * line_h + pre_gap + 2
            self._check_page(total_h + 10)

            self.current_y -= pre_gap
            self.c.setFillColor(C_BODY)

            # Draw all lines except the last
            for line in wrapped_lines[:-1]:
                self.c.drawString(x_start, self.current_y, line)
                self.current_y -= line_h

            # Last line: draw title text, dot leaders, and page number on same baseline
            last_line = wrapped_lines[-1]
            self.c.setFont(font, sz)
            self.c.setFillColor(C_BODY)
            self.c.drawString(x_start, self.current_y, last_line)
            self.c.drawRightString(x_end, self.current_y, pg_str)

            # Dot leaders on last line
            last_w = self.c.stringWidth(last_line, font, sz)
            pg_w = self.c.stringWidth(pg_str, font, sz)
            dot_s = x_start + last_w + 6
            dot_e = x_end - pg_w - 6
            if dot_e > dot_s + 10:
                self.c.setFont('Gar', sz)
                self.c.setFillColor(C_GREY)
                dot_w = self.c.stringWidth('.', 'Gar', sz) + 1
                x = dot_s
                while x + dot_w <= dot_e:
                    self.c.drawString(x, self.current_y, '.')
                    x += dot_w

            self.current_y -= line_h + 2

        self.current_y -= 20
        self._ornament(self.current_y)
        self._finish_page()
    
    def render_chapter_opener(self, title, subtitle=''):
        """Start chapter on recto page, return with current_y set."""
        self._ensure_recto()
        self.is_front_matter = False  # chapters start body numbering
        
        self.current_y = PAGE_H - MARGIN_TOP - 80
        
        # Title
        tw = self._tw()
        self.c.setFont('GarB', CH_TITLE_SZ)
        title_w = self.c.stringWidth(title, 'GarB', CH_TITLE_SZ)
        
        if title_w > tw:
            words = title.split()
            mid = len(words) // 2
            l1 = ' '.join(words[:mid])
            l2 = ' '.join(words[mid:])
            self._ctxt(self.current_y, l1, 'GarB', CH_TITLE_SZ, C_BODY)
            self.current_y -= 28
            self._ctxt(self.current_y, l2, 'GarB', CH_TITLE_SZ, C_BODY)
        else:
            self._ctxt(self.current_y, title, 'GarB', CH_TITLE_SZ, C_BODY)
        
        self.current_y -= 25
        
        if subtitle:
            # Wrap long subtitles
            sub_w = self.c.stringWidth(subtitle, 'GarI', CH_SUB_SZ)
            if sub_w > tw:
                sub_lines = self._wrap(subtitle, 'GarI', CH_SUB_SZ, tw)
                for sl in sub_lines:
                    self._ctxt(self.current_y, sl, 'GarI', CH_SUB_SZ, C_BROWN)
                    self.current_y -= 18
                self.current_y -= 12
            else:
                self._ctxt(self.current_y, subtitle, 'GarI', CH_SUB_SZ, C_BROWN)
                self.current_y -= 30
        else:
            self.current_y -= 10
        
        # Decorative rule
        cx = PAGE_W / 2
        self.c.setStrokeColor(C_BROWN)
        self.c.setLineWidth(0.5)
        self.c.line(cx - 80, self.current_y, cx + 80, self.current_y)
        self.current_y -= 30
    
    def render_chapter_end(self):
        self._check_page(50)
        self.current_y -= 15
        self._divider(self.current_y, 'end')
        self._finish_page()
    
    def render_profile(self, name, tagline, body, is_first=False):
        if not is_first:
            self._check_page(80)
            self._dot_sep(self.current_y)
            self.current_y -= 22
        
        self._check_page(60)
        
        # Name
        lm = self._lm()
        self.c.setFont('GarB', PROF_NAME_SZ)
        self.c.setFillColor(C_BODY)
        self.c.drawString(lm, self.current_y, name)
        self.current_y -= 18
        
        # Tagline
        if tagline:
            tag = tagline.replace('--', '\u2013')
            self.c.setFont('GarI', PROF_TAG_SZ)
            self.c.setFillColor(C_MID)
            self.c.drawString(lm, self.current_y, tag)
            self.current_y -= 20
        else:
            self.current_y -= 6
        
        # Body
        for para in body:
            self._draw_content(para)
    
    def render_also_available(self):
        """Also available page — nod to Not Manchester."""
        self._ensure_recto()
        y = PAGE_H / 2 + 80
        
        self._ctxt(y, 'Also available from', 'Gar', 10, C_DARK)
        y -= 16
        self._ctxt(y, 'D&H Publishing International', 'GarI', 11, C_DARK)
        y -= 35
        
        # Decorative rule above title
        cx = PAGE_W / 2
        self.c.setStrokeColor(C_BROWN)
        self.c.setLineWidth(0.5)
        self.c.line(cx - 60, y, cx + 60, y)
        y -= 30
        
        self._ctxt(y, 'NOT MANCHESTER', 'GarB', 20, C_BODY)
        y -= 26
        self._ctxt(y, 'The Proud Story of Salford', 'GarI', 13, C_BROWN)
        y -= 30
        
        # Rule below
        self.c.setStrokeColor(C_BROWN)
        self.c.setLineWidth(0.5)
        self.c.line(cx - 60, y, cx + 60, y)
        y -= 28
        
        self._ctxt(y, 'David Oldham', 'GarI', 11, C_DARK)
        y -= 35
        
        self._ctxt(y, 'www.dandhpublishing.com', 'Gar', 9.5, C_GREY)
        y -= 30
        
        self._ornament(y)
        self._finish_page()
    
    def render_back_page(self):
        self._ensure_recto()
        y = PAGE_H/2 + 20
        self._ctxt(y, 'www.dandhpublishing.com', 'GarB', 13, C_BODY); y -= 22
        self._ctxt(y, 'Salfordians who Changed the World', 'GarI', 11, C_DARK); y -= 30
        self._divider(y, 'star'); y -= 25
        self._ctxt(y, 'D&H Publishing International', 'Gar', 10, C_DARK); y -= 18
        self.c.setFont('Gar', 8.5)
        self.c.setFillColor(C_GREY)
        self.c.drawCentredString(PAGE_W/2, y, '\u00a9 2026 David Oldham. All rights reserved.')
        self._finish_page()


# ═══════════════════════════════════════════════════════════════════
# TWO-PASS BUILDER
# ═══════════════════════════════════════════════════════════════════

class BookBuilder:
    def __init__(self, md_path, output_path):
        self.md_path = md_path
        self.output_path = output_path
        self.blocks = parse_manuscript(md_path)
        # Image base directory: same folder as the manuscript
        self.image_base_dir = os.path.dirname(os.path.abspath(md_path))
    
    def _render(self, path, toc_entries=None):
        r = BookRenderer(path)
        r.image_base_dir = self.image_base_dir
        r.header_text = 'FROM THESE STREETS \u2013 Salfordians who Changed the World'
        first_in_ch = True
        
        for i, blk in enumerate(self.blocks):
            t = blk['type']
            
            if t == 'title_page':
                r.render_title()
            elif t == 'copyright_page':
                # blank verso
                r._new_page(suppress=True)
                r._finish_page()
                r.render_copyright(blk['lines'])
            elif t == 'dedication_page':
                r.render_dedication()
            elif t == 'note_on_inclusion':
                r.render_note(blk['paras'])
            elif t == 'toc':
                if toc_entries:
                    r.render_toc(toc_entries)
                else:
                    # Placeholder pages
                    r._ensure_recto()
                    r._ctxt(PAGE_H - MARGIN_TOP - 30, 'Contents', 'GarB', 22, C_BODY)
                    r._finish_page()
                    r._new_page(suppress=True)
                    r._finish_page()
            elif t in ('chapter', 'afterword'):
                r.toc_entries.append((blk['title'], r.page_num + 1, 0))
                r.render_chapter_opener(blk['title'], blk.get('subtitle', ''))
                first_in_ch = True
                for para in blk.get('intro', []):
                    r._draw_content(para)
                if t == 'afterword':
                    r.render_chapter_end()
            elif t == 'profile':
                r.toc_entries.append((blk['name'], r.page_num, 1))
                r.render_profile(blk['name'], blk.get('tagline',''),
                                blk.get('body',[]), is_first=first_in_ch)
                first_in_ch = False
                
                # Check if next block starts a new chapter or afterword
                if i+1 < len(self.blocks):
                    nt = self.blocks[i+1]['type']
                    if nt in ('chapter', 'afterword'):
                        r.render_chapter_end()
                elif i == len(self.blocks) - 1:
                    r.render_chapter_end()
        
        r.render_also_available()
        r.render_back_page()
        r.c.save()
        self._last_image_log = r.image_log
        return r.toc_entries
    
    def build(self):
        print("Pass 1: Collecting page numbers...")
        tmp = self.output_path.replace('.pdf', '_p1.pdf')
        toc = self._render(tmp)
        print(f"  {len(toc)} TOC entries, last page ~{toc[-1][1] if toc else '?'}")
        
        print("Pass 2: Final render with TOC...")
        self._render(self.output_path, toc)
        if os.path.exists(tmp):
            os.remove(tmp)
        
        # Set TrimBox
        self._set_trimbox()
        
        # Print image log
        if self._last_image_log:
            print(f"\nIMAGES")
            print(f"------")
            placed = 0
            warnings = 0
            errors = 0
            for fname, page, hint, dpi, status in self._last_image_log:
                if status == 'OK':
                    print(f"  {fname:40s} placed p.{page} ({hint} width, {dpi} DPI) ✓")
                    placed += 1
                elif status == 'LOW RES':
                    print(f"  {fname:40s} placed p.{page} ({hint} width, {dpi} DPI) ⚠ LOW RES")
                    placed += 1
                    warnings += 1
                else:
                    print(f"  {fname:40s} {status} ✗")
                    errors += 1
            print(f"\n  Total images: {len(self._last_image_log)}")
            print(f"  Placed: {placed}")
            if warnings:
                print(f"  Warnings: {warnings} (low resolution)")
            if errors:
                print(f"  Errors: {errors}")
        
        print(f"\nDone: {self.output_path}")
    
    def _set_trimbox(self):
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, FloatObject, NameObject
        
        reader = PdfReader(self.output_path)
        writer = PdfWriter()
        for page in reader.pages:
            page[NameObject('/TrimBox')] = ArrayObject([
                FloatObject(0), FloatObject(0),
                FloatObject(PAGE_W), FloatObject(PAGE_H),
            ])
            writer.add_page(page)
        writer.add_metadata({
            '/Title': 'From These Streets \u2014 Salfordians who Changed the World',
            '/Author': 'David Oldham',
            '/Creator': 'Layout Perfect Typesetting Engine',
            '/Producer': 'ReportLab + pypdf',
        })
        with open(self.output_path, 'wb') as f:
            writer.write(f)


if __name__ == '__main__':
    builder = BookBuilder(
        '/mnt/user-data/uploads/From_These_Streets_-_Revised_Manuscript.md',
        '/mnt/user-data/outputs/From_These_Streets_PRINT.pdf'
    )
    builder.build()
